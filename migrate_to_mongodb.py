"""Migrate data from SQLite to MongoDB"""
import sqlite3
from pymongo import MongoClient
from datetime import datetime

SQLITE_PATH = "data/bot_database.db"
MONGODB_URI = "mongodb+srv://fivdjgwjcujj_db_user:oMeCIHgUbClBaYXY@cluster0.4csmirr.mongodb.net/?appName=Cluster0"

def migrate():
    # Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    mongo_client = MongoClient(MONGODB_URI)
    mongo_db = mongo_client.robloxcheatz
    
    # Migrate users
    print("Migrating users...")
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT * FROM email_links")
    users = cursor.fetchall()
    
    for user in users:
        user_dict = dict(user)
        mongo_db.users.update_one(
            {"discord_id": user_dict["discord_id"]},
            {"$set": {
                "discord_id": user_dict["discord_id"],
                "email": user_dict["email"],
                "total_spent": user_dict.get("total_spent", 0),
                "purchase_count": user_dict.get("purchase_count", 0),
                "level": user_dict.get("level", 0),
                "verified_at": datetime.now(),
                "last_updated": datetime.now()
            }},
            upsert=True
        )
        print(f"  Migrated user {user_dict['discord_id']} - {user_dict['email']}")
    
    # Migrate loyalty keys
    print("\nMigrating loyalty keys...")
    cursor.execute("SELECT * FROM loyalty_keys")
    keys = cursor.fetchall()
    
    for key in keys:
        key_dict = dict(key)
        mongo_db.loyalty_keys.update_one(
            {"discord_id": key_dict["discord_id"]},
            {"$set": {
                "discord_id": key_dict["discord_id"],
                "keys_balance": key_dict.get("keys_balance", 0),
                "total_keys_earned": key_dict.get("total_keys_earned", 0),
                "total_keys_used": key_dict.get("total_keys_used", 0)
            }},
            upsert=True
        )
        print(f"  Migrated keys for {key_dict['discord_id']}")
    
    # Migrate purchase history
    print("\nMigrating purchase history...")
    cursor.execute("SELECT * FROM purchase_history")
    purchases = cursor.fetchall()
    
    for purchase in purchases:
        p_dict = dict(purchase)
        mongo_db.purchase_history.update_one(
            {"order_id": p_dict["order_id"]},
            {"$set": {
                "discord_id": p_dict["discord_id"],
                "order_id": p_dict["order_id"],
                "product_name": p_dict.get("product_name"),
                "product_category": p_dict.get("product_category"),
                "amount": p_dict.get("amount", 0),
                "synced_at": datetime.now()
            }},
            upsert=True
        )
        print(f"  Migrated purchase {p_dict['order_id']}")
    
    print("\n[OK] Migration complete!")
    
    # Verify
    print("\n=== Verification ===")
    print(f"Users in MongoDB: {mongo_db.users.count_documents({})}")
    print(f"Keys in MongoDB: {mongo_db.loyalty_keys.count_documents({})}")
    print(f"Purchases in MongoDB: {mongo_db.purchase_history.count_documents({})}")
    
    for user in mongo_db.users.find():
        print(f"\nUser: {user}")


if __name__ == "__main__":
    migrate()
