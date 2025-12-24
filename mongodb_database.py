"""
MongoDB Database module - replaces SQLite for cloud deployment
Stores email links, purchases, loyalty keys, rewards in MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
from typing import Optional, Dict, List, Any
import os
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
        _client = MongoClient(MONGODB_URI)
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
    """Calculate user level based on total spent"""
    if total_spent >= 200:
        return 5
    elif total_spent >= 100:
        return 4
    elif total_spent >= 70:
        return 3
    elif total_spent >= 30:
        return 2
    elif total_spent >= 10:
        return 1
    return 0


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
                    "last_updated": datetime.now()
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
