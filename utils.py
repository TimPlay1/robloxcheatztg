"""
Utility functions for the bot
"""

import re
import random
import string
from datetime import datetime
import config


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def mask_email(email: str) -> str:
    """Mask email for privacy (show first 2 and last 2 chars before @)"""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 4:
        masked = local[0] + '*' * (len(local) - 1)
    else:
        masked = local[:2] + '*' * (len(local) - 4) + local[-2:]
    
    return f"{masked}@{domain}"


def generate_coupon_code(prefix: str, user_id: int) -> str:
    """Generate a unique coupon code"""
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{random_part}"


def get_discount_for_level(level: int) -> dict:
    """Get discount info for a level"""
    if level in config.DISCOUNT_BY_LEVEL:
        return config.DISCOUNT_BY_LEVEL[level]
    return {"discount": 0, "code_prefix": ""}


def get_level_name(level: int) -> str:
    """Get readable name for level"""
    level_names = {
        0: "Not Verified",
        1: "Bronze",
        2: "Silver",
        3: "Gold",
        4: "Platinum",
        5: "Diamond",
        6: "Master",
        7: "VIP",
        8: "VIP+",
        9: "Elite",
        10: "Legend"
    }
    return level_names.get(level, "Unknown")


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"


def get_level_progress(total_spent: float) -> dict:
    """Calculate progress to next level"""
    current_level = min(int(total_spent // 10), 10)
    
    if current_level >= 10:
        return {
            "current_level": 10,
            "next_level": None,
            "progress": 100.0,
            "needed_for_next": 0
        }
    
    current_threshold = current_level * 10
    next_threshold = (current_level + 1) * 10
    progress_in_level = total_spent - current_threshold
    level_range = next_threshold - current_threshold
    progress_percent = (progress_in_level / level_range) * 100
    
    return {
        "current_level": current_level,
        "next_level": current_level + 1,
        "progress": min(progress_percent, 100),
        "needed_for_next": next_threshold - total_spent
    }


def create_progress_bar(progress: float, length: int = 10) -> str:
    """Create a text progress bar"""
    filled = int(progress / 100 * length)
    empty = length - filled
    return f"[{'#' * filled}{'-' * empty}]"


def get_embed_color(level: int) -> int:
    """Get embed color for level"""
    return config.LEVEL_COLORS.get(level, config.COLORS["primary"])


def roll_reward() -> tuple:
    """Roll for a random reward based on chances"""
    roll = random.randint(1, 100)
    cumulative = 0
    
    for reward_type, value, chance, description in config.REWARDS:
        cumulative += chance
        if roll <= cumulative:
            return (reward_type, value, description)
    
    # Fallback to first reward
    return (config.REWARDS[0][0], config.REWARDS[0][1], config.REWARDS[0][3])


def calculate_keys_earned(purchase_count: int, previous_count: int) -> int:
    """Calculate how many new keys were earned"""
    purchases_per_key = config.LOYALTY_SETTINGS["purchases_per_key"]
    
    keys_before = previous_count // purchases_per_key
    keys_after = purchase_count // purchases_per_key
    
    return max(0, keys_after - keys_before)


def format_reward_description(reward_type: str, value: int, description: str) -> str:
    """Format reward description for display"""
    if reward_type == "discount_key":
        return f"{description}"
    elif reward_type == "roblox_alt":
        return f"{description}"
    elif reward_type == "free_product":
        return f"{description}"
    return description


def get_reward_emoji_replacement(reward_type: str) -> str:
    """Get icon for reward type (no emojis)"""
    icons = {
        "discount_key": "[KEY]",
        "roblox_alt": "[ALT]",
        "free_product": "[GIFT]",
    }
    return icons.get(reward_type, "[?]")
