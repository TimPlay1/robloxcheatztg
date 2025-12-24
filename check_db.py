"""Check MongoDB database contents"""
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://fivdjgwjcujj_db_user:oMeCIHgUbClBaYXY@cluster0.4csmirr.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Force connection
    client.admin.command('ping')
    print("[OK] MongoDB connected!")
    
    db = client.robloxcheatz
    
    print("\n=== COLLECTIONS ===")
    collections = db.list_collection_names()
    print(collections if collections else "No collections found")
    
    print("\n=== TICKETS ===")
    tickets = list(db.tickets.find())
    print(f"Count: {len(tickets)}")
    for t in tickets[:5]:
        print(t)
    
    print("\n=== TELEGRAM AUTHORIZED ===")
    auth = list(db.telegram_authorized.find())
    print(f"Count: {len(auth)}")
    for u in auth:
        print(u)
    
    print("\n=== USERS (verified) ===")
    users = list(db.users.find())
    print(f"Count: {len(users)}")
    for u in users[:5]:
        print(u)
        
except Exception as e:
    print(f"[ERROR] {e}")
