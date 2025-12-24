"""
Ticket API Backend with MongoDB
REST API for managing VIP tickets
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
import json
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for WebApp

# MongoDB connection
# Free MongoDB Atlas: https://cloud.mongodb.com
# Create a free cluster and get connection string
# Format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/robloxcheatz")
client = None
db = None
tickets_collection = None

def init_db():
    """Initialize MongoDB connection"""
    global client, db, tickets_collection
    try:
        # Use certifi CA bundle for proper SSL
        client = MongoClient(
            MONGODB_URI,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        db = client.robloxcheatz
        tickets_collection = db.tickets
        # Create indexes
        tickets_collection.create_index("channel_id", unique=True)
        tickets_collection.create_index("discord_user_id")
        tickets_collection.create_index("status")
        print("[OK] MongoDB connected successfully")
        return True
    except Exception as e:
        print(f"[!] MongoDB connection error: {e}")
        return False


# ============= TELEGRAM AUTHORIZED USERS (MongoDB) =============

def sync_get_authorized_users() -> set:
    """Get all authorized Telegram user IDs from MongoDB"""
    try:
        auth_collection = db.telegram_authorized
        users = auth_collection.find({})
        return set(u["telegram_user_id"] for u in users)
    except Exception as e:
        print(f"[!] Error loading authorized users: {e}")
        return set()


def sync_add_authorized_user(telegram_user_id: int):
    """Add authorized Telegram user to MongoDB"""
    try:
        auth_collection = db.telegram_authorized
        auth_collection.update_one(
            {"telegram_user_id": telegram_user_id},
            {"$set": {"telegram_user_id": telegram_user_id, "authorized_at": datetime.now()}},
            upsert=True
        )
        print(f"[OK] Authorized user {telegram_user_id} saved to MongoDB")
    except Exception as e:
        print(f"[!] Error saving authorized user: {e}")


def sync_remove_authorized_user(telegram_user_id: int):
    """Remove authorized Telegram user from MongoDB"""
    try:
        auth_collection = db.telegram_authorized
        auth_collection.delete_one({"telegram_user_id": telegram_user_id})
    except Exception as e:
        print(f"[!] Error removing authorized user: {e}")


def serialize_ticket(ticket):
    """Serialize ticket for JSON response"""
    if ticket:
        ticket = dict(ticket)  # Create a copy
        ticket["_id"] = str(ticket["_id"])
        # Convert datetime objects to ISO strings
        for key, value in ticket.items():
            if isinstance(value, datetime):
                ticket[key] = value.isoformat()
    return ticket


# ============= API ENDPOINTS =============

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/api/tickets", methods=["GET"])
def get_all_tickets():
    """Get all active tickets"""
    try:
        tickets = list(tickets_collection.find({"status": "active"}))
        return jsonify({
            "success": True,
            "tickets": [serialize_ticket(t) for t in tickets],
            "count": len(tickets)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/<int:channel_id>", methods=["GET"])
def get_ticket(channel_id):
    """Get specific ticket by channel ID"""
    try:
        ticket = tickets_collection.find_one({"channel_id": channel_id})
        if ticket:
            return jsonify({"success": True, "ticket": serialize_ticket(ticket)})
        return jsonify({"success": False, "error": "Ticket not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/user/<int:discord_user_id>", methods=["GET"])
def get_user_ticket(discord_user_id):
    """Get active ticket for a specific Discord user"""
    try:
        ticket = tickets_collection.find_one({
            "discord_user_id": discord_user_id,
            "status": "active"
        })
        if ticket:
            return jsonify({"success": True, "ticket": serialize_ticket(ticket), "has_ticket": True})
        return jsonify({"success": True, "ticket": None, "has_ticket": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets", methods=["POST"])
def create_ticket():
    """Create a new ticket"""
    try:
        data = request.json
        
        # Check required fields
        required = ["channel_id", "discord_user_id", "discord_username"]
        for field in required:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        # Check if user already has active ticket
        existing = tickets_collection.find_one({
            "discord_user_id": data["discord_user_id"],
            "status": "active"
        })
        if existing:
            return jsonify({
                "success": False, 
                "error": "User already has an active ticket",
                "existing_channel_id": existing["channel_id"]
            }), 409
        
        # Create ticket document
        ticket = {
            "channel_id": data["channel_id"],
            "discord_user_id": data["discord_user_id"],
            "discord_username": data["discord_username"],
            "email": data.get("email", "N/A"),
            "total_spent": data.get("total_spent", 0),
            "purchase_count": data.get("purchase_count", 0),
            "level": data.get("level", 1),
            "telegram_chat_id": data.get("telegram_chat_id"),
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": []
        }
        
        result = tickets_collection.insert_one(ticket)
        ticket["_id"] = str(result.inserted_id)
        
        return jsonify({"success": True, "ticket": ticket}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/<int:channel_id>", methods=["DELETE"])
def delete_ticket(channel_id):
    """Delete/close a ticket"""
    try:
        result = tickets_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"status": "closed", "closed_at": datetime.now(), "updated_at": datetime.now()}}
        )
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Ticket closed"})
        return jsonify({"success": False, "error": "Ticket not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/<int:channel_id>/hard-delete", methods=["DELETE"])
def hard_delete_ticket(channel_id):
    """Permanently delete a ticket"""
    try:
        result = tickets_collection.delete_one({"channel_id": channel_id})
        if result.deleted_count > 0:
            return jsonify({"success": True, "message": "Ticket permanently deleted"})
        return jsonify({"success": False, "error": "Ticket not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/user/<int:discord_user_id>", methods=["DELETE"])
def delete_user_ticket(discord_user_id):
    """Delete active ticket for a specific Discord user"""
    try:
        result = tickets_collection.update_one(
            {"discord_user_id": discord_user_id, "status": "active"},
            {"$set": {"status": "closed", "closed_at": datetime.now(), "updated_at": datetime.now()}}
        )
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "User ticket closed"})
        return jsonify({"success": False, "error": "No active ticket found for user"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/<int:channel_id>/messages", methods=["POST"])
def add_message(channel_id):
    """Add a message to ticket"""
    try:
        data = request.json
        message = {
            "id": str(ObjectId()),
            "sender": data.get("sender", "unknown"),
            "sender_type": data.get("sender_type", "discord"),  # discord, telegram, webapp
            "content": data.get("content", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        result = tickets_collection.update_one(
            {"channel_id": channel_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True, "message": message})
        return jsonify({"success": False, "error": "Ticket not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tickets/<int:channel_id>/messages", methods=["GET"])
def get_messages(channel_id):
    """Get all messages for a ticket"""
    try:
        ticket = tickets_collection.find_one({"channel_id": channel_id})
        if ticket:
            return jsonify({
                "success": True, 
                "messages": ticket.get("messages", []),
                "count": len(ticket.get("messages", []))
            })
        return jsonify({"success": False, "error": "Ticket not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============= SYNC FUNCTIONS (for bot integration) =============

def sync_create_ticket(channel_id: int, discord_user_id: int, discord_username: str, 
                       email: str = "N/A", total_spent: float = 0, 
                       purchase_count: int = 0, level: int = 1,
                       telegram_chat_id: int = None) -> dict:
    """Synchronously create a ticket (called from Discord bot)"""
    try:
        # Check if user already has active ticket
        existing = tickets_collection.find_one({
            "discord_user_id": discord_user_id,
            "status": "active"
        })
        if existing:
            return {"success": False, "error": "User already has an active ticket", 
                   "existing_channel_id": existing["channel_id"]}
        
        ticket = {
            "channel_id": channel_id,
            "discord_user_id": discord_user_id,
            "discord_username": discord_username,
            "email": email,
            "total_spent": total_spent,
            "purchase_count": purchase_count,
            "level": level,
            "telegram_chat_id": telegram_chat_id,
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": []
        }
        
        result = tickets_collection.insert_one(ticket)
        return {"success": True, "ticket_id": str(result.inserted_id)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sync_delete_ticket(channel_id: int) -> dict:
    """Synchronously delete/close a ticket"""
    try:
        result = tickets_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"status": "closed", "closed_at": datetime.now(), "updated_at": datetime.now()}}
        )
        return {"success": result.modified_count > 0}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sync_get_user_active_ticket(discord_user_id: int) -> dict:
    """Check if user has active ticket"""
    try:
        ticket = tickets_collection.find_one({
            "discord_user_id": discord_user_id,
            "status": "active"
        })
        if ticket:
            return {"has_ticket": True, "channel_id": ticket["channel_id"]}
        return {"has_ticket": False}
    except Exception as e:
        return {"has_ticket": False, "error": str(e)}


def sync_get_all_active_tickets() -> list:
    """Get all active tickets"""
    try:
        tickets = list(tickets_collection.find({"status": "active"}))
        return [serialize_ticket(t) for t in tickets]
    except Exception as e:
        print(f"[!] Error getting tickets: {e}")
        return []


def sync_update_telegram_chat_id(channel_id: int, telegram_chat_id: int):
    """Update telegram chat ID for ticket"""
    try:
        tickets_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"telegram_chat_id": telegram_chat_id, "updated_at": datetime.now()}}
        )
    except Exception as e:
        print(f"[!] Error updating telegram chat ID: {e}")


def sync_add_message(channel_id: int, sender: str, sender_type: str, content: str) -> bool:
    """Add a message to ticket history
    
    Args:
        channel_id: Discord channel ID of the ticket
        sender: Name of the sender (username)
        sender_type: 'discord', 'telegram', or 'webapp'
        content: Message content
    
    Returns:
        True if message was added, False otherwise
    """
    try:
        message = {
            "id": str(ObjectId()),
            "sender": sender,
            "sender_type": sender_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        result = tickets_collection.update_one(
            {"channel_id": channel_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now()}
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"[!] Error adding message to ticket: {e}")
        return False


def sync_get_ticket_by_channel(channel_id: int) -> dict:
    """Get ticket by channel ID"""
    try:
        ticket = tickets_collection.find_one({"channel_id": channel_id})
        return serialize_ticket(ticket) if ticket else None
    except Exception as e:
        print(f"[!] Error getting ticket by channel: {e}")
        return None


# Initialize database on import
init_db()


if __name__ == "__main__":
    # Run Flask app (for local testing)
    app.run(host="0.0.0.0", port=5000, debug=True)
