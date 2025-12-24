# ===============================================
# DISCORD BOT CONFIGURATION
# RobloxCheatz Verification & Loyalty System
# Purple Theme | No Emojis | English Only
# ===============================================

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Bot Token (required - set via environment variable)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Discord Server ID
GUILD_ID = int(os.environ.get("GUILD_ID", "1453346027003183147"))

# Emoji Server IDs (отдельные серверы для хранения эмодзи)
# Бот будет загружать эмодзи с этих серверов и создавать недостающие там
EMOJI_SERVER_IDS = [
    1453406267992313921,  # Эмодзи сервер 1
    1453406520220848241,  # Эмодзи сервер 2
]

# Komerza API Settings (required - set via environment variables)
KOMERZA_API_TOKEN = os.environ.get("KOMERZA_API_TOKEN")
KOMERZA_API_BASE = "https://api.komerza.com"
STORE_ID = os.environ.get("STORE_ID", "d1550f0a-b430-49a9-807a-21f33df2d603")

# ===============================================
# PURPLE THEME COLORS
# ===============================================
COLORS = {
    "primary": 0x9B59B6,      # Main purple
    "secondary": 0x8E44AD,    # Dark purple
    "accent": 0xAF7AC5,       # Light purple
    "success": 0x6C3483,      # Success purple
    "error": 0xC0392B,        # Red for errors
    "warning": 0xF39C12,      # Orange for warnings
    "gold": 0xD4AC0D,         # Gold for VIP
    "platinum": 0xBDC3C7,     # Platinum tier
}

# Level colors (purple gradient)
LEVEL_COLORS = {
    1: 0xD7BDE2,   # Very light purple
    2: 0xC39BD3,   # Light purple
    3: 0xAF7AC5,   # Medium light
    4: 0x9B59B6,   # Medium purple
    5: 0x8E44AD,   # Dark purple
    6: 0x7D3C98,   # Darker purple
    7: 0x6C3483,   # Very dark
    8: 0x5B2C6F,   # Deep purple
    9: 0x4A235A,   # Deeper purple
    10: 0xD4AC0D,  # Gold (legend)
}

# ===============================================
# PURCHASE ROLES (levels by amount)
# Format: min_amount: (role_name, color_hex)
# ===============================================
PURCHASE_ROLES = {
    10: ("$10 Buyer", 0xD7BDE2),      # Level 1
    20: ("$20 Buyer", 0xC39BD3),      # Level 2
    30: ("$30 Buyer", 0xAF7AC5),      # Level 3
    40: ("$40 Buyer", 0x9B59B6),      # Level 4
    50: ("$50 Buyer", 0x8E44AD),      # Level 5
    60: ("$60 Buyer", 0x7D3C98),      # Level 6
    70: ("$70 VIP", 0x6C3483),        # Level 7 - Priority Support
    80: ("$80 VIP", 0x5B2C6F),        # Level 8
    90: ("$90 Elite", 0x4A235A),      # Level 9
    100: ("$100 Legend", 0xD4AC0D),   # Level 10 - Gold
}

# ===============================================
# SPECIAL ROLES
# ===============================================
SPECIAL_ROLES = {
    "priority_support": ("Priority Support", 0x6C3483, 70),   # Min $70
    "verified_buyer": ("Verified Buyer", 0x9B59B6, 10),       # Any purchase
}

# ===============================================
# PRODUCT ROLES - Roles by purchased products
# Format: product_id: (role_name, color_hex)
# ===============================================
PRODUCT_ROLES = {
    # Main Products
    "wave": ("Wave Buyer", 0x3b82f6),
    "seliware": ("Seliware Buyer", 0xec4899),
    "matcha": ("Matcha Buyer", 0x84cc16),
    # Other Products
    "potassium": ("Potassium Buyer", 0xff0ae2),
    "bunni": ("Bunni Buyer", 0xff0ae2),
    "volt": ("Volt Buyer", 0xff0ae2),
    "volcano": ("Volcano Buyer", 0xff0ae2),
    # External Products
    "serotonin": ("Serotonin Buyer", 0x3b82f6),
    "isabelle": ("Isabelle Buyer", 0x3b82f6),
    "ronin": ("Ronin Buyer", 0x3b82f6),
    "yerba": ("Yerba Buyer", 0x3b82f6),
    # Android Products
    "codex": ("Codex Buyer", 0x22c55e),
    "arceus": ("Arceus Buyer", 0x22c55e),
}

# ===============================================
# LOYALTY PROGRAM SETTINGS
# Keys earned per purchase count
# ===============================================
LOYALTY_SETTINGS = {
    "purchases_per_key": 5,  # Every 5 purchases = 1 loyalty key
}

# ===============================================
# REWARD CHANCES (total = 100%)
# Format: (reward_type, value, chance_percent, description)
# ===============================================
REWARDS = [
    ("discount_key", 1, 40, "1-Day Discount Key (10% off)"),       # 40%
    ("roblox_alt", 5, 50, "Roblox Alt Account x5"),                # 50%
    ("discount_key", 3, 5, "3-Day Discount Key (15% off)"),        # 5%
    ("discount_key", 7, 2, "7-Day Discount Key (20% off)"),        # 2%
    ("discount_key", 30, 1, "30-Day Discount Key (25% off)"),      # 1%
    ("free_product", 1, 2, "Mystery Box (Random Product)"),        # 2%
]

# ===============================================
# CHANNEL IDs (auto-filled on startup)
# ===============================================
CHANNELS = {
    "verify": None,
    "support": None,
    "buyers_chat": None,
    "buyers_news": None,
    "vip_chat": None,
    "vip_support": None,
    "rewards": None,
    "logs": None,
}

# ===============================================
# CATEGORY IDs (auto-filled on startup)
# ===============================================
CATEGORIES = {
    "info": None,
    "buyers": None,
    "vip": None,
    "tickets": None,
}

# ===============================================
# DISCOUNT COUPONS BY LEVEL
# ===============================================
DISCOUNT_BY_LEVEL = {
    1: {"discount": 5, "code_prefix": "BUYER5"},
    2: {"discount": 5, "code_prefix": "BUYER5"},
    3: {"discount": 5, "code_prefix": "BUYER5"},
    4: {"discount": 5, "code_prefix": "BUYER5"},
    5: {"discount": 5, "code_prefix": "BUYER5"},
    6: {"discount": 5, "code_prefix": "BUYER5"},
    7: {"discount": 7, "code_prefix": "VIP7"},
    8: {"discount": 7, "code_prefix": "VIP7"},
    9: {"discount": 7, "code_prefix": "VIP7"},
    10: {"discount": 10, "code_prefix": "LEGEND10"},
}
