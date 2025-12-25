"""
MongoDB Database module - replaces SQLite for cloud deployment
Stores email links, purchases, loyalty keys, rewards in MongoDB
"""

from pymongo import MongoClient, ReturnDocument
from datetime import datetime
from typing import Optional, Dict, List, Any
import os
import ssl
import certifi
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/robloxcheatz")

# Global MongoDB client
_client = None
_db = None


def get_db():
    """Get MongoDB database connection"""
    global _client, _db
    if _db is None:
        # Use certifi CA bundle for proper SSL
        _client = MongoClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        _db = _client.robloxcheatz
        # Create indexes
        _db.users.create_index("discord_id", unique=True)
        _db.users.create_index("email", unique=True)
        _db.purchase_history.create_index("discord_id")
        _db.purchase_history.create_index("order_id", unique=True)
        _db.loyalty_keys.create_index("discord_id", unique=True)
        print("[OK] MongoDB users database initialized")
    return _db


def calculate_level(total_spent: float) -> int:
    """Calculate user level based on total spent (10 levels, every $10 = +1 level)"""
    level = int(total_spent // 10)
    return min(level, 10)  # Max level is 10


# ============= USER FUNCTIONS =============

async def get_user_by_discord_id(discord_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by Discord ID"""
    import asyncio
    return await asyncio.to_thread(_sync_get_user_by_discord_id, discord_id)


def _sync_get_user_by_discord_id(discord_id: int) -> Optional[Dict[str, Any]]:
    """Sync version of get_user_by_discord_id"""
    db = get_db()
    user = db.users.find_one({"discord_id": discord_id})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user data by email"""
    import asyncio
    return await asyncio.to_thread(_sync_get_user_by_email, email)


def _sync_get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Sync version of get_user_by_email"""
    db = get_db()
    user = db.users.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def link_email_to_discord(discord_id: int, email: str, total_spent: float = 0, purchase_count: int = 0) -> bool:
    """Link email to Discord account"""
    import asyncio
    return await asyncio.to_thread(_sync_link_email_to_discord, discord_id, email, total_spent, purchase_count)


def _sync_link_email_to_discord(discord_id: int, email: str, total_spent: float = 0, purchase_count: int = 0) -> bool:
    """Sync version of link_email_to_discord"""
    db = get_db()
    level = calculate_level(total_spent)
    
    try:
        # Check if this email was previously linked (to preserve keys_already_claimed)
        existing_email_record = db.email_keys_tracking.find_one({"email": email.lower()})
        keys_already_claimed = existing_email_record.get("keys_claimed", 0) if existing_email_record else 0
        
        db.users.update_one(
            {"discord_id": discord_id},
            {
                "$set": {
                    "discord_id": discord_id,
                    "email": email.lower(),
                    "total_spent": total_spent,
                    "purchase_count": purchase_count,
                    "level": level,
                    "verified_at": datetime.now(),
                    "last_updated": datetime.now(),
                    "keys_already_claimed": keys_already_claimed  # Track keys from previous verifications
                }
            },
            upsert=True
        )
        
        # Create loyalty keys entry
        db.loyalty_keys.update_one(
            {"discord_id": discord_id},
            {
                "$setOnInsert": {
                    "discord_id": discord_id,
                    "keys_balance": 0,
                    "total_keys_earned": 0,
                    "total_keys_used": 0
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[!] Error linking email: {e}")
        return False


async def update_user_stats(discord_id: int, total_spent: float, purchase_count: int):
    """Update user's purchase stats"""
    import asyncio
    return await asyncio.to_thread(_sync_update_user_stats, discord_id, total_spent, purchase_count)


def _sync_update_user_stats(discord_id: int, total_spent: float, purchase_count: int):
    """Sync version of update_user_stats"""
    db = get_db()
    level = calculate_level(total_spent)
    
    db.users.update_one(
        {"discord_id": discord_id},
        {
            "$set": {
                "total_spent": total_spent,
                "purchase_count": purchase_count,
                "level": level,
                "last_updated": datetime.now()
            }
        }
    )


async def unlink_email(discord_id: int) -> bool:
    """Unlink email from Discord account"""
    import asyncio
    return await asyncio.to_thread(_sync_unlink_email, discord_id)


def _sync_unlink_email(discord_id: int) -> bool:
    """Sync version of unlink_email"""
    db = get_db()
    
    # Get user data before deleting to track keys
    user_data = db.users.find_one({"discord_id": discord_id})
    keys_data = db.loyalty_keys.find_one({"discord_id": discord_id})
    
    if user_data and keys_data:
        email = user_data.get("email", "").lower()
        total_keys_earned = keys_data.get("total_keys_earned", 0)
        previous_claimed = user_data.get("keys_already_claimed", 0)
        
        # Save total keys ever claimed for this email
        if email:
            db.email_keys_tracking.update_one(
                {"email": email},
                {
                    "$set": {
                        "email": email,
                        "keys_claimed": total_keys_earned + previous_claimed,
                        "last_updated": datetime.now()
                    }
                },
                upsert=True
            )
    
    result = db.users.delete_one({"discord_id": discord_id})
    db.loyalty_keys.delete_one({"discord_id": discord_id})
    db.purchase_history.delete_many({"discord_id": discord_id})
    return result.deleted_count > 0


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all verified users"""
    import asyncio
    return await asyncio.to_thread(_sync_get_all_users)


def _sync_get_all_users() -> List[Dict[str, Any]]:
    """Sync version of get_all_users"""
    db = get_db()
    users = list(db.users.find())
    for user in users:
        user["_id"] = str(user["_id"])
    return users


# ============= PURCHASE HISTORY =============

async def add_purchase(discord_id: int, order_id: str, product_name: str, 
                       product_category: str, amount: float, purchased_at: datetime) -> bool:
    """Add purchase to history"""
    import asyncio
    return await asyncio.to_thread(
        _sync_add_purchase, discord_id, order_id, product_name, product_category, amount, purchased_at
    )


def _sync_add_purchase(discord_id: int, order_id: str, product_name: str,
                       product_category: str, amount: float, purchased_at: datetime) -> bool:
    """Sync version of add_purchase"""
    db = get_db()
    try:
        db.purchase_history.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "discord_id": discord_id,
                    "order_id": order_id,
                    "product_name": product_name,
                    "product_category": product_category,
                    "amount": amount,
                    "purchased_at": purchased_at,
                    "synced_at": datetime.now()
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[!] Error adding purchase: {e}")
        return False


async def get_user_purchases(discord_id: int) -> List[Dict[str, Any]]:
    """Get purchase history for user"""
    import asyncio
    return await asyncio.to_thread(_sync_get_user_purchases, discord_id)


def _sync_get_user_purchases(discord_id: int) -> List[Dict[str, Any]]:
    """Sync version of get_user_purchases"""
    db = get_db()
    purchases = list(db.purchase_history.find(
        {"discord_id": discord_id}
    ).sort("purchased_at", -1))
    for p in purchases:
        p["_id"] = str(p["_id"])
    return purchases


# ============= LOYALTY KEYS =============

async def get_user_keys(discord_id: int) -> Dict[str, Any]:
    """Get user's loyalty keys balance"""
    import asyncio
    return await asyncio.to_thread(_sync_get_user_keys, discord_id)


def _sync_get_user_keys(discord_id: int) -> Dict[str, Any]:
    """Sync version of get_user_keys"""
    db = get_db()
    keys = db.loyalty_keys.find_one({"discord_id": discord_id})
    if keys:
        keys["_id"] = str(keys["_id"])
        return keys
    return {"discord_id": discord_id, "keys_balance": 0, "total_keys_earned": 0, "total_keys_used": 0}


async def add_loyalty_key(discord_id: int, count: int = 1) -> bool:
    """Add loyalty key(s) to user"""
    import asyncio
    return await asyncio.to_thread(_sync_add_loyalty_key, discord_id, count)


def _sync_add_loyalty_key(discord_id: int, count: int = 1) -> bool:
    """Sync version of add_loyalty_key"""
    db = get_db()
    try:
        db.loyalty_keys.update_one(
            {"discord_id": discord_id},
            {
                "$inc": {"keys_balance": count, "total_keys_earned": count},
                "$set": {"last_key_earned": datetime.now()}
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[!] Error adding key: {e}")
        return False


async def use_loyalty_key(discord_id: int) -> bool:
    """Use one loyalty key"""
    import asyncio
    return await asyncio.to_thread(_sync_use_loyalty_key, discord_id)


def _sync_use_loyalty_key(discord_id: int) -> bool:
    """Sync version of use_loyalty_key"""
    db = get_db()
    keys = db.loyalty_keys.find_one({"discord_id": discord_id})
    if not keys or keys.get("keys_balance", 0) < 1:
        return False
    
    db.loyalty_keys.update_one(
        {"discord_id": discord_id},
        {"$inc": {"keys_balance": -1, "total_keys_used": 1}}
    )
    return True


# ============= REWARDS =============

async def add_reward(discord_id: int, reward_type: str, reward_value: str, 
                     reward_description: str, expires_at: datetime = None) -> bool:
    """Add reward to user"""
    import asyncio
    return await asyncio.to_thread(
        _sync_add_reward, discord_id, reward_type, reward_value, reward_description, expires_at
    )


def _sync_add_reward(discord_id: int, reward_type: str, reward_value: str,
                     reward_description: str, expires_at: datetime = None) -> bool:
    """Sync version of add_reward"""
    db = get_db()
    try:
        db.rewards_history.insert_one({
            "discord_id": discord_id,
            "reward_type": reward_type,
            "reward_value": reward_value,
            "reward_description": reward_description,
            "claimed_at": datetime.now(),
            "expires_at": expires_at,
            "used": False
        })
        return True
    except Exception as e:
        print(f"[!] Error adding reward: {e}")
        return False


async def get_user_rewards(discord_id: int) -> List[Dict[str, Any]]:
    """Get user's rewards"""
    import asyncio
    return await asyncio.to_thread(_sync_get_user_rewards, discord_id)


def _sync_get_user_rewards(discord_id: int) -> List[Dict[str, Any]]:
    """Sync version of get_user_rewards"""
    db = get_db()
    rewards = list(db.rewards_history.find({"discord_id": discord_id}).sort("claimed_at", -1))
    for r in rewards:
        r["_id"] = str(r["_id"])
    return rewards


# ============= COUPONS =============

async def add_issued_coupon(discord_id: int, coupon_code: str, discount_percent: int, level: int) -> bool:
    """Record issued coupon"""
    import asyncio
    return await asyncio.to_thread(_sync_add_issued_coupon, discord_id, coupon_code, discount_percent, level)


def _sync_add_issued_coupon(discord_id: int, coupon_code: str, discount_percent: int, level: int) -> bool:
    """Sync version of add_issued_coupon"""
    db = get_db()
    try:
        db.issued_coupons.insert_one({
            "discord_id": discord_id,
            "coupon_code": coupon_code,
            "discount_percent": discount_percent,
            "level": level,
            "issued_at": datetime.now(),
            "used": False
        })
        return True
    except Exception as e:
        print(f"[!] Error adding coupon: {e}")
        return False


async def get_user_coupons(discord_id: int) -> List[Dict[str, Any]]:
    """Get user's issued coupons"""
    import asyncio
    return await asyncio.to_thread(_sync_get_user_coupons, discord_id)


def _sync_get_user_coupons(discord_id: int) -> List[Dict[str, Any]]:
    """Sync version of get_user_coupons"""
    db = get_db()
    coupons = list(db.issued_coupons.find({"discord_id": discord_id}).sort("issued_at", -1))
    for c in coupons:
        c["_id"] = str(c["_id"])
    return coupons


async def check_existing_coupon_for_level(discord_id: int, level: int) -> bool:
    """Check if user already has coupon for specific level"""
    import asyncio
    return await asyncio.to_thread(_sync_check_existing_coupon_for_level, discord_id, level)


def _sync_check_existing_coupon_for_level(discord_id: int, level: int) -> bool:
    """Sync version of check_existing_coupon_for_level"""
    db = get_db()
    coupon = db.issued_coupons.find_one({"discord_id": discord_id, "level": level})
    return coupon is not None


# ============= VERIFICATION LOGS =============

async def log_verification(discord_id: int, discord_username: str, email: str,
                           action: str, success: bool, details: str = None):
    """Log verification attempt"""
    import asyncio
    return await asyncio.to_thread(
        _sync_log_verification, discord_id, discord_username, email, action, success, details
    )


def _sync_log_verification(discord_id: int, discord_username: str, email: str,
                           action: str, success: bool, details: str = None):
    """Sync version of log_verification"""
    db = get_db()
    db.verification_logs.insert_one({
        "discord_id": discord_id,
        "discord_username": discord_username,
        "email": email,
        "action": action,
        "success": success,
        "details": details,
        "created_at": datetime.now()
    })


# ============= DATABASE INIT =============

async def init_database():
    """Initialize MongoDB database"""
    import asyncio
    await asyncio.to_thread(get_db)
    print("[OK] MongoDB database initialized")


# ============= COMPATIBILITY ALIASES =============

async def get_all_verified_users() -> List[Dict[str, Any]]:
    """Alias for get_all_users (compatibility with old code)"""
    return await get_all_users()


async def add_loyalty_keys(discord_id: int, keys_to_add: int) -> int:
    """Add multiple loyalty keys and return new balance"""
    import asyncio
    return await asyncio.to_thread(_sync_add_loyalty_keys, discord_id, keys_to_add)


def _sync_add_loyalty_keys(discord_id: int, keys_to_add: int) -> int:
    """Sync version of add_loyalty_keys"""
    db = get_db()
    result = db.loyalty_keys.find_one_and_update(
        {"discord_id": discord_id},
        {
            "$inc": {"keys_balance": keys_to_add, "total_keys_earned": keys_to_add},
            "$set": {"last_key_earned": datetime.now()}
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return result.get("keys_balance", 0) if result else keys_to_add


async def issue_coupon(discord_id: int, coupon_code: str, discount_percent: int, level: int) -> bool:
    """Alias for add_issued_coupon (compatibility with old code)"""
    return await add_issued_coupon(discord_id, coupon_code, discount_percent, level)


async def unlink_email_by_email(email: str) -> bool:
    """Unlink user by email address"""
    import asyncio
    return await asyncio.to_thread(_sync_unlink_email_by_email, email)


def _sync_unlink_email_by_email(email: str) -> bool:
    """Sync version of unlink_email_by_email"""
    db = get_db()
    user = db.users.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
    if not user:
        return False
    
    discord_id = user.get("discord_id")
    db.users.delete_one({"discord_id": discord_id})
    db.loyalty_keys.delete_one({"discord_id": discord_id})
    db.purchase_history.delete_many({"discord_id": discord_id})
    return True


async def use_loyalty_key(discord_id: int) -> bool:
    """Use one loyalty key"""
    import asyncio
    return await asyncio.to_thread(_sync_use_loyalty_key, discord_id)


def _sync_use_loyalty_key(discord_id: int) -> bool:
    """Sync version of use_loyalty_key"""
    db = get_db()
    keys = db.loyalty_keys.find_one({"discord_id": discord_id})
    if not keys or keys.get("keys_balance", 0) < 1:
        return False
    
    db.loyalty_keys.update_one(
        {"discord_id": discord_id},
        {"$inc": {"keys_balance": -1, "total_keys_used": 1}}
    )
    return True


def generate_reward_code() -> str:
    """Generate unique reward code"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return 'RW-' + ''.join(random.choices(chars, k=8))


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all verified users"""
    import asyncio
    return await asyncio.to_thread(_sync_get_all_users)


def _sync_get_all_users() -> List[Dict[str, Any]]:
    """Sync version of get_all_users"""
    db = get_db()
    users = list(db.users.find())
    for user in users:
        user["_id"] = str(user["_id"])
    return users


# ============= VERIFICATION CODE FUNCTIONS =============

async def save_verification_code(discord_id: int, email: str, code: str, expires_at: datetime) -> bool:
    """Save email verification code"""
    import asyncio
    return await asyncio.to_thread(_sync_save_verification_code, discord_id, email, code, expires_at)


def _sync_save_verification_code(discord_id: int, email: str, code: str, expires_at: datetime) -> bool:
    """Sync version of save_verification_code"""
    db = get_db()
    try:
        db.verification_codes.update_one(
            {"discord_id": discord_id},
            {
                "$set": {
                    "discord_id": discord_id,
                    "email": email.lower(),
                    "code": code,
                    "expires_at": expires_at,
                    "verified": False,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[!] Error saving verification code: {e}")
        return False


async def get_verification_code(discord_id: int) -> Optional[Dict[str, Any]]:
    """Get pending verification code for discord user"""
    import asyncio
    return await asyncio.to_thread(_sync_get_verification_code, discord_id)


def _sync_get_verification_code(discord_id: int) -> Optional[Dict[str, Any]]:
    """Sync version of get_verification_code"""
    db = get_db()
    code_data = db.verification_codes.find_one({"discord_id": discord_id})
    if code_data:
        code_data["_id"] = str(code_data["_id"])
    return code_data


async def verify_code(discord_id: int, entered_code: str) -> dict:
    """Verify the entered code - returns {success: bool, error: str|None, email: str|None}"""
    import asyncio
    return await asyncio.to_thread(_sync_verify_code, discord_id, entered_code)


def _sync_verify_code(discord_id: int, entered_code: str) -> dict:
    """Sync version of verify_code"""
    db = get_db()
    code_data = db.verification_codes.find_one({"discord_id": discord_id})
    
    if not code_data:
        return {"success": False, "error": "No pending verification. Please enter your email first.", "email": None}
    
    if code_data.get("verified"):
        return {"success": False, "error": "Code already used.", "email": None}
    
    if datetime.utcnow() > code_data.get("expires_at", datetime.utcnow()):
        return {"success": False, "error": "Code expired. Please request a new code.", "email": None}
    
    if code_data.get("code") != entered_code:
        return {"success": False, "error": "Invalid code. Please check and try again.", "email": None}
    
    # Mark as verified
    db.verification_codes.update_one(
        {"discord_id": discord_id},
        {"$set": {"verified": True}}
    )
    
    return {"success": True, "error": None, "email": code_data.get("email")}


async def delete_verification_code(discord_id: int) -> bool:
    """Delete verification code after successful verification"""
    import asyncio
    return await asyncio.to_thread(_sync_delete_verification_code, discord_id)


def _sync_delete_verification_code(discord_id: int) -> bool:
    """Sync version of delete_verification_code"""
    db = get_db()
    result = db.verification_codes.delete_one({"discord_id": discord_id})
    return result.deleted_count > 0

