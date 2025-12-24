"""
Database module for SQLite operations
Stores email links, purchases, loyalty keys, rewards
"""

import aiosqlite
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import random
import string

DATABASE_PATH = "data/bot_database.db"


async def init_database():
    """Initialize database and create tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Email links table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS email_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                total_spent REAL DEFAULT 0,
                purchase_count INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add purchase_count column if missing (for existing databases)
        try:
            await db.execute('ALTER TABLE email_links ADD COLUMN purchase_count INTEGER DEFAULT 0')
        except:
            pass  # Column already exists
        
        # Purchase history table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS purchase_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                order_id TEXT UNIQUE NOT NULL,
                product_name TEXT,
                product_category TEXT,
                amount REAL NOT NULL,
                purchased_at TIMESTAMP,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES email_links(discord_id)
            )
        ''')
        
        # Loyalty keys table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS loyalty_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                keys_balance INTEGER DEFAULT 0,
                total_keys_earned INTEGER DEFAULT 0,
                total_keys_used INTEGER DEFAULT 0,
                last_key_earned TIMESTAMP,
                FOREIGN KEY (discord_id) REFERENCES email_links(discord_id)
            )
        ''')
        
        # Rewards history table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS rewards_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                reward_type TEXT NOT NULL,
                reward_value TEXT NOT NULL,
                reward_description TEXT,
                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                used BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (discord_id) REFERENCES email_links(discord_id)
            )
        ''')
        
        # Issued coupons table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS issued_coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                coupon_code TEXT NOT NULL,
                discount_percent INTEGER NOT NULL,
                level INTEGER NOT NULL,
                issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (discord_id) REFERENCES email_links(discord_id)
            )
        ''')
        
        # Verification logs table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER NOT NULL,
                discord_username TEXT,
                email TEXT NOT NULL,
                action TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        await db.execute('CREATE INDEX IF NOT EXISTS idx_email_links_discord ON email_links(discord_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_email_links_email ON email_links(email)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_purchase_history_discord ON purchase_history(discord_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_loyalty_keys_discord ON loyalty_keys(discord_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_rewards_discord ON rewards_history(discord_id)')
        
        await db.commit()
        print("[OK] Database initialized")


# ============= USER FUNCTIONS =============

async def get_user_by_discord_id(discord_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by Discord ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM email_links WHERE discord_id = ?',
            (discord_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user data by email"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM email_links WHERE LOWER(email) = LOWER(?)',
            (email,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def link_email_to_discord(discord_id: int, email: str, total_spent: float = 0, purchase_count: int = 0) -> bool:
    """Link email to Discord account"""
    level = calculate_level(total_spent)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute('''
                INSERT INTO email_links (discord_id, email, total_spent, purchase_count, level)
                VALUES (?, ?, ?, ?, ?)
            ''', (discord_id, email.lower(), total_spent, purchase_count, level))
            
            # Create loyalty keys entry
            await db.execute('''
                INSERT INTO loyalty_keys (discord_id, keys_balance, total_keys_earned)
                VALUES (?, 0, 0)
            ''', (discord_id,))
            
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def update_user_stats(discord_id: int, total_spent: float, purchase_count: int):
    """Update user's purchase stats"""
    level = calculate_level(total_spent)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE email_links 
            SET total_spent = ?, purchase_count = ?, level = ?, last_updated = CURRENT_TIMESTAMP
            WHERE discord_id = ?
        ''', (total_spent, purchase_count, level, discord_id))
        await db.commit()


async def get_all_verified_users() -> List[Dict[str, Any]]:
    """Get all verified users"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('SELECT * FROM email_links')
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def unlink_email(discord_id: int) -> bool:
    """Unlink email from Discord account"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            'DELETE FROM email_links WHERE discord_id = ?',
            (discord_id,)
        )
        # Also delete loyalty keys
        await db.execute('DELETE FROM loyalty_keys WHERE discord_id = ?', (discord_id,))
        await db.commit()
        return cursor.rowcount > 0


async def unlink_email_by_email(email: str) -> bool:
    """Unlink by email address"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get discord_id first
        cursor = await db.execute(
            'SELECT discord_id FROM email_links WHERE LOWER(email) = LOWER(?)',
            (email,)
        )
        row = await cursor.fetchone()
        if row:
            discord_id = row[0]
            await db.execute('DELETE FROM email_links WHERE discord_id = ?', (discord_id,))
            await db.execute('DELETE FROM loyalty_keys WHERE discord_id = ?', (discord_id,))
            await db.commit()
            return True
        return False


# ============= LOYALTY KEYS FUNCTIONS =============

async def get_user_keys(discord_id: int) -> Dict[str, Any]:
    """Get user's loyalty keys balance"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM loyalty_keys WHERE discord_id = ?',
            (discord_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {"keys_balance": 0, "total_keys_earned": 0, "total_keys_used": 0}


async def add_loyalty_keys(discord_id: int, keys_to_add: int) -> int:
    """Add loyalty keys to user's balance"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if entry exists
        cursor = await db.execute(
            'SELECT keys_balance FROM loyalty_keys WHERE discord_id = ?',
            (discord_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            new_balance = row[0] + keys_to_add
            await db.execute('''
                UPDATE loyalty_keys 
                SET keys_balance = keys_balance + ?, 
                    total_keys_earned = total_keys_earned + ?,
                    last_key_earned = CURRENT_TIMESTAMP
                WHERE discord_id = ?
            ''', (keys_to_add, keys_to_add, discord_id))
        else:
            new_balance = keys_to_add
            await db.execute('''
                INSERT INTO loyalty_keys (discord_id, keys_balance, total_keys_earned, last_key_earned)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (discord_id, keys_to_add, keys_to_add))
        
        await db.commit()
        return new_balance


async def use_loyalty_key(discord_id: int) -> bool:
    """Use one loyalty key"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            'SELECT keys_balance FROM loyalty_keys WHERE discord_id = ?',
            (discord_id,)
        )
        row = await cursor.fetchone()
        
        if row and row[0] > 0:
            await db.execute('''
                UPDATE loyalty_keys 
                SET keys_balance = keys_balance - 1,
                    total_keys_used = total_keys_used + 1
                WHERE discord_id = ?
            ''', (discord_id,))
            await db.commit()
            return True
        return False


# ============= REWARDS FUNCTIONS =============

async def add_reward(discord_id: int, reward_type: str, reward_value: str, 
                     description: str, expires_days: int = None) -> int:
    """Add a reward to user's account"""
    expires_at = None
    if expires_days:
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO rewards_history 
            (discord_id, reward_type, reward_value, reward_description, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (discord_id, reward_type, reward_value, description, expires_at))
        await db.commit()
        return cursor.lastrowid


async def get_user_rewards(discord_id: int, unused_only: bool = False) -> List[Dict[str, Any]]:
    """Get user's rewards"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        if unused_only:
            cursor = await db.execute(
                'SELECT * FROM rewards_history WHERE discord_id = ? AND used = FALSE ORDER BY claimed_at DESC',
                (discord_id,)
            )
        else:
            cursor = await db.execute(
                'SELECT * FROM rewards_history WHERE discord_id = ? ORDER BY claimed_at DESC',
                (discord_id,)
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def mark_reward_used(reward_id: int) -> bool:
    """Mark a reward as used"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'UPDATE rewards_history SET used = TRUE WHERE id = ?',
            (reward_id,)
        )
        await db.commit()
        return True


# ============= COUPON FUNCTIONS =============

async def issue_coupon(discord_id: int, coupon_code: str, discount_percent: int, level: int) -> bool:
    """Issue a coupon to user"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO issued_coupons (discord_id, coupon_code, discount_percent, level)
            VALUES (?, ?, ?, ?)
        ''', (discord_id, coupon_code, discount_percent, level))
        await db.commit()
        return True


async def get_user_coupons(discord_id: int) -> List[Dict[str, Any]]:
    """Get user's coupons"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM issued_coupons WHERE discord_id = ? ORDER BY issued_at DESC',
            (discord_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ============= LOGGING FUNCTIONS =============

async def log_verification(discord_id: int, discord_username: str, email: str,
                           action: str, success: bool, details: str = None):
    """Log verification action"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO verification_logs 
            (discord_id, discord_username, email, action, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (discord_id, discord_username, email, action, success, details))
        await db.commit()


# ============= HELPER FUNCTIONS =============

def calculate_level(total_spent: float) -> int:
    """Calculate level from total spent (every $10 = 1 level, max 10)"""
    return min(int(total_spent // 10), 10)


def generate_reward_code() -> str:
    """Generate a random reward code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
