"""
RobloxCheatz Discord Bot
Verification & Loyalty System
Purple Theme | English Only | No Emojis
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import aiohttp
import os
from datetime import datetime
from typing import Optional, Dict, List

import config
import mongodb_database as database  # Use MongoDB for cloud deployment
from komerza_api import api as komerza_api
from roles import RoleManager, setup_channels_permissions
from utils import (
    generate_coupon_code, get_discount_for_level, get_level_name,
    format_currency, get_level_progress, create_progress_bar,
    validate_email, mask_email, get_embed_color, roll_reward,
    calculate_keys_earned, format_reward_description
)
import telegram_bot
import ticket_api


# ============= CONSTANTS =============

# GitHub raw for icons
WEBSITE_BASE = "https://raw.githubusercontent.com/TimPlay1/robloxcheatz/main/public"
WEAO_API = "https://weao.gg/api/status/exploits"

# Тематические иконки для thumbnails (из интернета)
# Белые минималистичные UI иконки (Icons8 iOS Filled White)
# Используются как источник для создания кастомных эмодзи
UI_ICONS = {
    # Категории статуса
    "star": "https://img.icons8.com/ios-filled/100/FFFFFF/star--v1.png",  # Main Products
    "wrench": "https://img.icons8.com/ios-filled/100/FFFFFF/wrench.png",  # Other Products
    "globe": "https://img.icons8.com/ios-filled/100/FFFFFF/globe--v1.png",  # External
    "android": "https://img.icons8.com/ios-filled/100/FFFFFF/android-os.png",  # Android
    # Инфраструктура
    "shield": "https://img.icons8.com/ios-filled/100/FFFFFF/verified-account.png",  # Verify
    "headset": "https://img.icons8.com/ios-filled/100/FFFFFF/headset.png",  # Support
    "gift": "https://img.icons8.com/ios-filled/100/FFFFFF/gift.png",  # Rewards
    "crown": "https://img.icons8.com/ios-filled/100/FFFFFF/crown.png",  # VIP
    # UI элементы
    "check": "https://img.icons8.com/ios-filled/100/FFFFFF/checkmark--v1.png",  # Галочка
    "cross": "https://img.icons8.com/ios-filled/100/FFFFFF/multiply.png",  # Крестик
    "warning": "https://img.icons8.com/ios-filled/100/FFFFFF/error--v1.png",  # Внимание
    "info": "https://img.icons8.com/ios-filled/100/FFFFFF/info.png",  # Инфо
    "user": "https://img.icons8.com/ios-filled/100/FFFFFF/user.png",  # Пользователь
    "key": "https://img.icons8.com/ios-filled/100/FFFFFF/key.png",  # Ключ
    "ticket": "https://img.icons8.com/ios-filled/100/FFFFFF/ticket.png",  # Тикет
    "dollar": "https://img.icons8.com/ios-filled/100/FFFFFF/us-dollar-circled--v1.png",  # Деньги
    "chart": "https://img.icons8.com/ios-filled/100/FFFFFF/combo-chart.png",  # Статистика
    "lock": "https://img.icons8.com/ios-filled/100/FFFFFF/lock.png",  # Замок
    "unlock": "https://img.icons8.com/ios-filled/100/FFFFFF/unlock.png",  # Открытый замок
    "link": "https://img.icons8.com/ios-filled/100/FFFFFF/link--v1.png",  # Ссылка
    "email": "https://img.icons8.com/ios-filled/100/FFFFFF/new-post.png",  # Email
    "time": "https://img.icons8.com/ios-filled/100/FFFFFF/time.png",  # Время
    "refresh": "https://img.icons8.com/ios-filled/100/FFFFFF/refresh--v1.png",  # Обновить
    "settings": "https://img.icons8.com/ios-filled/100/FFFFFF/settings.png",  # Настройки
    "search": "https://img.icons8.com/ios-filled/100/FFFFFF/search--v1.png",  # Поиск
    "cart": "https://img.icons8.com/ios-filled/100/FFFFFF/shopping-cart.png",  # Корзина
    "list": "https://img.icons8.com/ios-filled/100/FFFFFF/list.png",  # Список
    "arrow_right": "https://img.icons8.com/ios-filled/100/FFFFFF/arrow--v1.png",  # Стрелка
    "controller": "https://img.icons8.com/ios-filled/100/FFFFFF/controller.png",  # Геймпад (лого)
    # Дополнительные иконки для кнопок и действий
    "close": "https://img.icons8.com/ios-filled/100/FFFFFF/close-window.png",  # Закрыть
    "plus": "https://img.icons8.com/ios-filled/100/FFFFFF/plus-math.png",  # Плюс
    "minus": "https://img.icons8.com/ios-filled/100/FFFFFF/minus-math.png",  # Минус  
    "edit": "https://img.icons8.com/ios-filled/100/FFFFFF/edit--v1.png",  # Редактировать
    "trash": "https://img.icons8.com/ios-filled/100/FFFFFF/trash.png",  # Удалить
    "send": "https://img.icons8.com/ios-filled/100/FFFFFF/sent.png",  # Отправить
    "success": "https://img.icons8.com/ios-filled/100/FFFFFF/ok--v1.png",  # Успех (круг с галочкой)
    "bag": "https://img.icons8.com/ios-filled/100/FFFFFF/shopping-bag.png",  # Сумка покупок
    "coupon": "https://img.icons8.com/ios-filled/100/FFFFFF/discount.png",  # Купон/скидка
    "level": "https://img.icons8.com/ios-filled/100/FFFFFF/prize.png",  # Уровень/награда
    "chat": "https://img.icons8.com/ios-filled/100/FFFFFF/chat.png",  # Чат
    "bell": "https://img.icons8.com/ios-filled/100/FFFFFF/appointment-reminders.png",  # Уведомление
    "fire": "https://img.icons8.com/ios-filled/100/FFFFFF/fire-element.png",  # Огонь/hot
    "lightning": "https://img.icons8.com/ios-filled/100/FFFFFF/lightning-bolt.png",  # Молния/быстро
}

# Кэш UI эмодзи (name -> emoji string "<:name:id>")
UI_EMOJIS = {}

# Кэш загруженных эмодзи продуктов (id -> emoji string)
PRODUCT_EMOJIS = {}

# Products data with buy links (from robloxcheatz products.json)
PRODUCTS = {
    "mainProducts": [
        {"id": "wave", "name": "Wave", "apiName": "wave", "icon": "/wave.png", "color": 0x3b82f6,
         "buyLink": "https://robloxcheatz.com/product?id=6d1f91b5-4599-467a-b9ba-eadef98c63fe&ref=robloxcheatzonline"},
        {"id": "seliware", "name": "Seliware", "apiName": "seliware", "icon": "/seliware.png", "color": 0xec4899,
         "buyLink": "https://robloxcheatz.com/product?id=51c9587f-4794-46ef-b6bf-2bd9f13c17d2&ref=robloxcheatzonline"},
        {"id": "matcha", "name": "Matcha", "apiName": "matcha", "icon": "/matcha.png", "color": 0x84cc16,
         "buyLink": "https://robloxcheatz.com/product?id=matcha&ref=robloxcheatzonline"},
    ],
    "otherProducts": [
        {"id": "potassium", "name": "Potassium", "apiName": "potassium", "icon": "/potassium.png", "color": 0xff0ae2,
         "buyLink": "https://robloxcheatz.com/product?id=potassium&ref=robloxcheatzonline"},
        {"id": "bunni", "name": "Bunni", "apiName": "bunni.lol", "icon": "/bunni.png", "color": 0xff0ae2,
         "buyLink": "https://robloxcheatz.com/product?id=178fa9f7-f297-41d2-b654-274ed11d3b54&ref=robloxcheatzonline"},
        {"id": "volt", "name": "Volt", "apiName": "volt", "icon": "/volt.png", "color": 0xff0ae2,
         "buyLink": "https://robloxcheatz.com/product?id=volt&ref=robloxcheatzonline"},
        {"id": "volcano", "name": "Volcano", "apiName": "volcano", "icon": "/volcano.png", "color": 0xff0ae2,
         "buyLink": "https://robloxcheatz.com/product?id=volcano"},
    ],
    "externalProducts": [
        {"id": "serotonin", "name": "Serotonin", "apiName": "serotonin", "icon": "/serotonin.png", "color": 0x3b82f6,
         "buyLink": "https://robloxcheatz.com/product?id=serotonin&ref=robloxcheatzonline"},
        {"id": "isabelle", "name": "Isabelle", "apiName": "isabelle", "icon": "/isabelle.png", "color": 0x3b82f6,
         "buyLink": "https://robloxcheatz.com/product?id=isabelle&ref=robloxcheatzonline"},
        {"id": "ronin", "name": "Ronin", "apiName": "ronin", "icon": "/ronin.png", "color": 0x3b82f6,
         "buyLink": "https://robloxcheatz.com/product?id=d85e5584-8469-4bd3-be6a-1f616f2959dd&ref=robloxcheatzonline"},
        {"id": "yerba", "name": "Yerba", "apiName": "yerba", "icon": "/yerba.png", "color": 0x3b82f6,
         "buyLink": "https://robloxcheatz.com/product?id=yerba&ref=robloxcheatzonline"},
    ],
    "androidProducts": [
        {"id": "codex", "name": "Codex", "apiName": "codex", "icon": "/codex.png", "color": 0x22c55e,
         "buyLink": "https://robloxcheatz.com/product?id=17ca258e-251f-44c6-b89d-601c335d1b9e&ref=robloxcheatzonline"},
        {"id": "arceus", "name": "Arceus X V5", "apiName": "arceus x v5", "icon": "/arcues.png", "color": 0x22c55e,
         "buyLink": "https://robloxcheatz.com/product?id=arceusxv5&ref=robloxcheatzonline"},
    ]
}


# ============= EMOJI MANAGEMENT =============

def get_all_emoji_servers(bot):
    """Получить список всех эмодзи-серверов"""
    servers = []
    for server_id in getattr(config, 'EMOJI_SERVER_IDS', []):
        guild = bot.get_guild(server_id)
        if guild:
            servers.append(guild)
    return servers


async def setup_ui_emojis(bot, guild: discord.Guild):
    """Загрузить UI эмодзи с эмодзи-серверов"""
    global UI_EMOJIS
    
    print("[...] Загрузка UI эмодзи...")
    
    # Собираем эмодзи со всех эмодзи-серверов
    all_emojis = {}
    
    for emoji_guild in get_all_emoji_servers(bot):
        for emoji in emoji_guild.emojis:
            if emoji.name not in all_emojis:
                all_emojis[emoji.name] = emoji
        print(f"  [+] Сервер {emoji_guild.name}: {len(emoji_guild.emojis)} эмодзи")
    
    # Заполняем UI_EMOJIS
    for icon_name in UI_ICONS.keys():
        emoji_name = f"ui_{icon_name}"
        if emoji_name in all_emojis:
            emoji = all_emojis[emoji_name]
            UI_EMOJIS[icon_name] = f"<:{emoji.name}:{emoji.id}>"
    
    print(f"[OK] Загружено {len(UI_EMOJIS)} UI эмодзи")


async def setup_product_emojis(bot, guild: discord.Guild):
    """Загрузить эмодзи продуктов с эмодзи-серверов"""
    global PRODUCT_EMOJIS
    
    print("[...] Загрузка эмодзи продуктов...")
    
    # Собираем эмодзи со всех эмодзи-серверов
    all_emojis = {}
    
    for emoji_guild in get_all_emoji_servers(bot):
        for emoji in emoji_guild.emojis:
            if emoji.name not in all_emojis:
                all_emojis[emoji.name] = emoji
    
    # Собираем все продукты
    all_products = []
    for category in PRODUCTS.values():
        all_products.extend(category)
    
    for product in all_products:
        emoji_name = f"rc_{product['id']}"
        if emoji_name in all_emojis:
            emoji = all_emojis[emoji_name]
            PRODUCT_EMOJIS[product['id']] = f"<:{emoji.name}:{emoji.id}>"
    
    print(f"[OK] Загружено {len(PRODUCT_EMOJIS)} эмодзи продуктов")


async def create_missing_emojis(bot, guild: discord.Guild):
    """Создать недостающие эмодзи на эмодзи-серверах"""
    emoji_servers = get_all_emoji_servers(bot)
    if not emoji_servers:
        print("[!] Эмодзи-серверы не найдены")
        return
    
    # Собираем все существующие эмодзи со всех серверов
    existing_emojis = set()
    for emoji_guild in emoji_servers:
        for emoji in emoji_guild.emojis:
            existing_emojis.add(emoji.name)
    
    # Выбираем сервер для создания новых эмодзи (первый с свободными слотами)
    def get_server_with_space():
        for emoji_guild in emoji_servers:
            if len(emoji_guild.emojis) < 50:  # Лимит для сервера без буста
                return emoji_guild
        return None
    
    created = 0
    
    async with aiohttp.ClientSession() as session:
        # Создаём недостающие UI эмодзи
        for icon_name, icon_url in UI_ICONS.items():
            emoji_name = f"ui_{icon_name}"
            if emoji_name not in existing_emojis and icon_name not in UI_EMOJIS:
                target_guild = get_server_with_space()
                if not target_guild:
                    print(f"  [!] Нет места на эмодзи-серверах")
                    break
                    
                try:
                    async with session.get(icon_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            emoji = await target_guild.create_custom_emoji(
                                name=emoji_name,
                                image=image_data,
                                reason="RobloxCheatz UI icon"
                            )
                            UI_EMOJIS[icon_name] = f"<:{emoji.name}:{emoji.id}>"
                            existing_emojis.add(emoji_name)
                            created += 1
                            print(f"  [+] UI эмодзи: {emoji_name} -> {target_guild.name}")
                except discord.HTTPException as e:
                    if e.code == 30008:
                        print(f"  [!] Лимит на {target_guild.name}")
                    else:
                        print(f"  [!] Ошибка: {e}")
                except Exception as e:
                    print(f"  [!] Ошибка {emoji_name}: {e}")
        
        # Создаём недостающие эмодзи продуктов
        all_products = []
        for category in PRODUCTS.values():
            all_products.extend(category)
        
        for product in all_products:
            emoji_name = f"rc_{product['id']}"
            if emoji_name not in existing_emojis and product['id'] not in PRODUCT_EMOJIS:
                target_guild = get_server_with_space()
                if not target_guild:
                    print(f"  [!] Нет места на эмодзи-серверах")
                    break
                    
                icon_url = f"{WEBSITE_BASE}{product['icon']}"
                try:
                    async with session.get(icon_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            emoji = await target_guild.create_custom_emoji(
                                name=emoji_name,
                                image=image_data,
                                reason="RobloxCheatz product icon"
                            )
                            PRODUCT_EMOJIS[product['id']] = f"<:{emoji.name}:{emoji.id}>"
                            existing_emojis.add(emoji_name)
                            created += 1
                            print(f"  [+] Продукт: {emoji_name} -> {target_guild.name}")
                except discord.HTTPException as e:
                    if e.code == 30008:
                        print(f"  [!] Лимит на {target_guild.name}")
                except Exception as e:
                    print(f"  [!] Ошибка {emoji_name}: {e}")
    
    if created > 0:
        print(f"[OK] Создано {created} новых эмодзи")


async def clear_main_server_emojis(guild: discord.Guild):
    """Удалить все кастомные эмодзи с основного сервера"""
    deleted = 0
    for emoji in guild.emojis:
        if emoji.name.startswith("ui_") or emoji.name.startswith("rc_"):
            try:
                await emoji.delete(reason="Перенос на эмодзи-сервер")
                deleted += 1
                print(f"  [-] Удалён: {emoji.name}")
            except Exception as e:
                print(f"  [!] Ошибка удаления {emoji.name}: {e}")
    return deleted


def ui(name: str) -> str:
    """Получить UI эмодзи по имени или fallback"""
    fallbacks = {
        "star": "⭐", "wrench": "🔧", "globe": "🌐", "android": "🤖",
        "shield": "🛡️", "headset": "🎧", "gift": "🎁", "crown": "👑",
        "check": "✅", "cross": "❌", "warning": "⚠️", "info": "ℹ️",
        "user": "👤", "key": "🔑", "ticket": "🎫", "dollar": "💰",
        "chart": "📊", "lock": "🔒", "unlock": "🔓", "link": "🔗",
        "email": "📧", "time": "⏰", "refresh": "🔄", "settings": "⚙️",
        "search": "🔍", "cart": "🛒", "list": "📋", "arrow_right": "➡️",
        "controller": "🎮", "close": "✖️", "plus": "➕", "minus": "➖",
        "edit": "✏️", "trash": "🗑️", "send": "📤", "success": "✔️",
        "bag": "🛍️", "coupon": "🏷️", "level": "🏆", "chat": "💬",
        "bell": "🔔", "fire": "🔥", "lightning": "⚡",
    }
    return UI_EMOJIS.get(name, fallbacks.get(name, ""))


def get_product_emoji(product_id: str) -> str:
    """Получить эмодзи продукта или пустую строку"""
    return PRODUCT_EMOJIS.get(product_id, "")


# ============= CHECK STATUS BUTTON VIEW =============

class CheckStatusView(discord.ui.View):
    """Persistent view with Check Status button"""
    
    def __init__(self):
        super().__init__(timeout=None)
        # Add link button (doesn't need custom_id since it's a link button)
        self.add_item(discord.ui.Button(
            label="Check Status",
            style=discord.ButtonStyle.link,
            url="https://robloxcheatz.online",
            emoji="🔍"
        ))


# ============= HELPER FUNCTIONS =============

async def delete_after(message, delay: int = 15):
    """Delete a message after delay seconds (for non-ephemeral)"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass


async def fetch_exploits_status() -> List:
    """Fetch current exploit status from WEAO API"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'WEAO-3PService',
                'Accept': 'application/json'
            }
            async with session.get(WEAO_API, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
    except Exception as e:
        print(f"[!] Error fetching WEAO status: {e}")
    return []


def get_status_indicator(update_status: bool) -> str:
    """Get status emoji indicator"""
    if update_status:
        return "🟢"  # Green circle for online
    else:
        return "🔴"  # Red circle for offline


def get_unknown_indicator() -> str:
    """Get unknown status indicator"""
    return "🟡"  # Yellow circle for unknown


def find_exploit_in_weao(exploits: List, api_name: str) -> dict:
    """Find exploit in WEAO data by apiName"""
    if not exploits:
        return None
    
    api_name_lower = api_name.lower().replace(" ", "").replace(".", "")
    
    # Exact match by title
    for exploit in exploits:
        if exploit.get("title", "").lower() == api_name.lower():
            return exploit
    
    # Normalized match
    for exploit in exploits:
        title_norm = exploit.get("title", "").lower().replace(" ", "").replace(".", "")
        if title_norm == api_name_lower:
            return exploit
    
    # Partial match
    for exploit in exploits:
        title_norm = exploit.get("title", "").lower().replace(" ", "").replace(".", "")
        if api_name_lower in title_norm or title_norm in api_name_lower:
            return exploit
    
    return None


async def update_status_embed(channel: discord.TextChannel, bot):
    """Update or create status embed in the status channel"""
    # Fetch status from WEAO API
    exploits_data = await fetch_exploits_status()
    
    embeds = []
    
    # Main header embed
    header_embed = discord.Embed(
        title=f"{ui('chart')} Software Status",
        description=f"Real-time status of all software products.\nUpdated every 10 minutes.\n\n"
                   f"🟢 Online/Updated | 🔴 Down/Offline | 🟡 Unknown\n\n"
                   f"{ui('cart')} Click on product name to purchase!",
        color=config.COLORS["primary"],
        timestamp=datetime.now()
    )
    header_embed.set_thumbnail(url=UI_ICONS["controller"])
    header_embed.set_footer(text="RobloxCheatz | Status Monitor")
    embeds.append(header_embed)
    
    # Main Products embed
    main_embed = discord.Embed(
        title=f"{ui('star')} Main Products",
        color=0x3b82f6  # Blue
    )
    main_lines = []
    for product in PRODUCTS["mainProducts"]:
        exploit = find_exploit_in_weao(exploits_data, product["apiName"])
        if exploit:
            indicator = get_status_indicator(exploit.get("updateStatus", False))
            version = exploit.get("version", "N/A")
        else:
            indicator = get_unknown_indicator()
            version = "N/A"
        buy_link = product.get("buyLink", "https://robloxcheatz.online")
        emoji = get_product_emoji(product['id'])
        emoji_prefix = f"{emoji} " if emoji else ""
        main_lines.append(f"{indicator} {emoji_prefix}**[{product['name']}]({buy_link})** • v{version}")
    
    main_embed.description = "\n\n".join(main_lines)
    embeds.append(main_embed)
    
    # Other Products embed
    other_embed = discord.Embed(
        title=f"{ui('wrench')} Other Products",
        color=0xff0ae2  # Pink
    )
    other_lines = []
    for product in PRODUCTS["otherProducts"]:
        exploit = find_exploit_in_weao(exploits_data, product["apiName"])
        if exploit:
            indicator = get_status_indicator(exploit.get("updateStatus", False))
            version = exploit.get("version", "N/A")
        else:
            indicator = get_unknown_indicator()
            version = "N/A"
        buy_link = product.get("buyLink", "https://robloxcheatz.online")
        emoji = get_product_emoji(product['id'])
        emoji_prefix = f"{emoji} " if emoji else ""
        other_lines.append(f"{indicator} {emoji_prefix}**[{product['name']}]({buy_link})** • v{version}")
    
    other_embed.description = "\n\n".join(other_lines)
    embeds.append(other_embed)
    
    # External Products embed
    external_embed = discord.Embed(
        title=f"{ui('globe')} External Products",
        color=0x3b82f6  # Blue
    )
    external_lines = []
    for product in PRODUCTS["externalProducts"]:
        exploit = find_exploit_in_weao(exploits_data, product["apiName"])
        if exploit:
            indicator = get_status_indicator(exploit.get("updateStatus", False))
            version = exploit.get("version", "N/A")
        else:
            indicator = get_unknown_indicator()
            version = "N/A"
        buy_link = product.get("buyLink", "https://robloxcheatz.online")
        emoji = get_product_emoji(product['id'])
        emoji_prefix = f"{emoji} " if emoji else ""
        external_lines.append(f"{indicator} {emoji_prefix}**[{product['name']}]({buy_link})** • v{version}")
    
    external_embed.description = "\n\n".join(external_lines)
    embeds.append(external_embed)
    
    # Android Products embed
    android_embed = discord.Embed(
        title=f"{ui('android')} Android Products",
        color=0x22c55e  # Green
    )
    android_lines = []
    for product in PRODUCTS["androidProducts"]:
        exploit = find_exploit_in_weao(exploits_data, product["apiName"])
        if exploit:
            indicator = get_status_indicator(exploit.get("updateStatus", False))
            version = exploit.get("version", "N/A")
        else:
            indicator = get_unknown_indicator()
            version = "N/A"
        buy_link = product.get("buyLink", "https://robloxcheatz.online")
        emoji = get_product_emoji(product['id'])
        emoji_prefix = f"{emoji} " if emoji else ""
        android_lines.append(f"{indicator} {emoji_prefix}**[{product['name']}]({buy_link})** • v{version}")
    
    android_embed.description = "\n\n".join(android_lines)
    embeds.append(android_embed)
    
    # Try to find and delete old status messages, then send new ones
    try:
        async for msg in channel.history(limit=20):
            if msg.author == channel.guild.me:
                await msg.delete()
                await asyncio.sleep(0.5)
    except:
        pass
    
    # Send all embeds with Check Status button
    await channel.send(embeds=embeds, view=CheckStatusView())


# ============= MAIN BOT CLASS =============

class VerificationBot(commands.Bot):
    """Main bot class"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            description="RobloxCheatz Verification Bot"
        )
        
        self.role_manager: Optional[RoleManager] = None
        self.status_message_id: Optional[int] = None
    
    async def setup_hook(self):
        """Setup on bot start"""
        # Initialize database
        await database.init_database()
        
        # Add command cogs (admin only)
        await self.add_cog(AdminCog(self))
        
        # Sync slash commands
        guild = discord.Object(id=config.GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("[OK] Slash commands synced")
    
    async def on_ready(self):
        """Event when bot is ready"""
        print(f"{'='*50}")
        print(f"[BOT] Logged in as {self.user}")
        print(f"[BOT] Servers: {len(self.guilds)}")
        print(f"{'='*50}")
        
        # Get main guild
        guild = self.get_guild(config.GUILD_ID)
        if guild:
            self.role_manager = RoleManager(guild)
            await self.role_manager.ensure_roles_exist()
            await setup_channels_permissions(guild, self.role_manager)
        
        # Set bot status - custom gaming status
        await self.change_presence(
            activity=discord.Game(
                name="🎮 Dominating Roblox | robloxcheatz.com"
            ),
            status=discord.Status.online
        )
        
        # Load customer cache
        await komerza_api.load_all_customers()
        
        # Setup custom emojis (загружаем с основного сервера и эмодзи-сервера)
        if guild:
            await setup_ui_emojis(self, guild)  # UI эмодзи (белые иконки)
            await setup_product_emojis(self, guild)  # Эмодзи продуктов
            await create_missing_emojis(self, guild)  # Создаём недостающие на эмодзи-сервере
        
        # Setup infrastructure (auto-create channels)
        await setup_infrastructure(guild, self)
        
        # Register persistent views (buttons work after restart)
        self.add_view(VerifyButtonView())
        self.add_view(TicketView())
        self.add_view(CloseTicketView())
        self.add_view(PriorityTicketView())
        self.add_view(ClaimRewardView())
        
        # Start background tasks
        if not self.sync_purchases.is_running():
            self.sync_purchases.start()
        
        if not self.refresh_customers_cache.is_running():
            self.refresh_customers_cache.start()
        
        if not self.update_status_channel.is_running():
            self.update_status_channel.start()
        
        # Start Telegram bot for VIP ticket notifications
        try:
            await telegram_bot.start_telegram_bot(self)
        except Exception as e:
            print(f"[!] Failed to start Telegram bot: {e}")
    
    async def on_message(self, message: discord.Message):
        """Handle messages - forward ticket messages to Telegram"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if message is in a ticket channel
        if message.channel.name.startswith("ticket-"):
            # Check if it's a VIP ticket (has [VIP] in topic)
            if message.channel.topic and "[VIP]" in message.channel.topic:
                # Forward to Telegram
                try:
                    await telegram_bot.notify_ticket_message(
                        channel_id=message.channel.id,
                        username=message.author.display_name,
                        message=message.content
                    )
                except Exception as e:
                    print(f"[!] Failed to forward message to Telegram: {e}")
        
        await self.process_commands(message)
    
    @tasks.loop(minutes=10)
    async def refresh_customers_cache(self):
        """Refresh customer cache every 10 minutes"""
        await komerza_api.refresh_customers_cache()
    
    @tasks.loop(minutes=10)
    async def update_status_channel(self):
        """Update status channel every 10 minutes"""
        guild = self.get_guild(config.GUILD_ID)
        if not guild:
            return
        
        status_channel = discord.utils.get(guild.text_channels, name="status")
        if not status_channel:
            return
        
        await update_status_embed(status_channel, self)
    
    @update_status_channel.before_loop
    async def before_status_update(self):
        await self.wait_until_ready()
    
    @tasks.loop(minutes=10)
    async def sync_purchases(self):
        """Periodic purchase sync - check for new purchases of verified users every 10 minutes"""
        print("[...] Syncing purchases...")
        guild = self.get_guild(config.GUILD_ID)
        if not guild or not self.role_manager:
            return
        
        verified_users = await database.get_all_verified_users()
        
        for user_data in verified_users:
            try:
                email = user_data["email"]
                discord_id = user_data["discord_id"]
                old_count = user_data.get("purchase_count", 0)
                
                # Get updated data
                total_spent = await komerza_api.get_customer_total_spent(email)
                purchase_count = await komerza_api.get_customer_purchase_count(email)
                old_total = user_data.get("total_spent", 0)
                
                # Update if changed
                if total_spent != old_total or purchase_count != old_count:
                    await database.update_user_stats(discord_id, total_spent, purchase_count)
                    
                    # Check for new loyalty keys
                    new_keys = calculate_keys_earned(purchase_count, old_count)
                    if new_keys > 0:
                        await database.add_loyalty_keys(discord_id, new_keys)
                        
                        # Notify user about new keys
                        member = guild.get_member(discord_id)
                        if member:
                            try:
                                embed = discord.Embed(
                                    title=f"{ui('key')} New Loyalty Keys!",
                                    description=f"You earned **{new_keys}** loyalty key(s)!\n\n"
                                               f"{ui('gift')} Use them in the rewards channel to claim prizes.",
                                    color=config.COLORS["primary"]
                                )
                                embed.set_thumbnail(url=UI_ICONS["key"])
                                await member.send(embed=embed)
                            except:
                                pass
                    
                    # Update roles (purchase level + product roles)
                    member = guild.get_member(discord_id)
                    if member:
                        await self.role_manager.assign_purchase_roles(member, total_spent)
                        # Assign product-specific roles
                        await self.role_manager.assign_product_roles(member, email)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"[!] Sync error for {user_data.get('email')}: {e}")
        
        print("[OK] Sync completed")
    
    @sync_purchases.before_loop
    async def before_sync(self):
        await self.wait_until_ready()


# ============= BUTTON VIEWS =============

class VerifyButtonView(discord.ui.View):
    """Verification button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Verify Account",
        style=discord.ButtonStyle.primary,
        custom_id="verify_button",
        emoji="🛡️"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show verification modal"""
        await interaction.response.send_modal(VerifyModal())


class VerifyModal(discord.ui.Modal, title="Account Verification"):
    """Modal for email input"""
    
    email = discord.ui.TextInput(
        label="Purchase Email",
        placeholder="Enter the email used for your purchase",
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        email = str(self.email.value).strip().lower()
        
        # Validate email format
        if not validate_email(email):
            embed = discord.Embed(
                title=f"{ui('cross')} Invalid Email Format",
                description=f"{ui('email')} Please enter a valid email address.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Check if already verified
        existing_user = await database.get_user_by_discord_id(interaction.user.id)
        if existing_user:
            embed = discord.Embed(
                title=f"{ui('warning')} Already Verified",
                description=f"{ui('email')} Your Discord account is already linked to: `{mask_email(existing_user['email'])}`\n\n"
                           f"{ui('headset')} Contact an administrator if you need to change this.",
                color=config.COLORS["warning"]
            )
            embed.set_thumbnail(url=UI_ICONS["warning"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Check if email already linked
        email_user = await database.get_user_by_email(email)
        if email_user:
            embed = discord.Embed(
                title=f"{ui('warning')} Email Already Linked",
                description=f"{ui('link')} This email is already linked to another Discord account.\n\n"
                           f"{ui('headset')} Contact an administrator if this is your email.",
                color=config.COLORS["warning"]
            )
            embed.set_thumbnail(url=UI_ICONS["warning"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Check email in API
        try:
            email_exists = await asyncio.wait_for(
                komerza_api.verify_email_exists(email),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            email_exists = False
        
        if not email_exists:
            embed = discord.Embed(
                title=f"{ui('cross')} Email Not Found",
                description=f"{ui('search')} This email was not found in our purchase database.\n\n"
                           f"{ui('info')} Make sure you're using the email from your purchase.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["search"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Get purchase data
        try:
            total_spent = await asyncio.wait_for(
                komerza_api.get_customer_total_spent(email),
                timeout=10.0
            )
            purchase_count = await asyncio.wait_for(
                komerza_api.get_customer_purchase_count(email),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            total_spent = 0
            purchase_count = 0
        
        # Check minimum purchase
        if total_spent < 10:
            embed = discord.Embed(
                title=f"{ui('cross')} Insufficient Purchases",
                description=f"{ui('dollar')} Minimum $10 in purchases required for verification.\n\n"
                           f"{ui('cart')} Your current total: {format_currency(total_spent)}",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["dollar"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Link email
        success = await database.link_email_to_discord(
            interaction.user.id, email, total_spent, purchase_count
        )
        
        if not success:
            embed = discord.Embed(
                title=f"{ui('cross')} Verification Error",
                description=f"{ui('warning')} An error occurred. Please try again later.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Assign roles
        level = database.calculate_level(total_spent)
        bot = interaction.client
        
        if bot.role_manager:
            await bot.role_manager.assign_purchase_roles(interaction.user, total_spent)
            # Also assign product-specific roles
            product_roles = await bot.role_manager.assign_product_roles(interaction.user, email)
        
        # Calculate initial loyalty keys
        initial_keys = purchase_count // config.LOYALTY_SETTINGS["purchases_per_key"]
        if initial_keys > 0:
            await database.add_loyalty_keys(interaction.user.id, initial_keys)
        
        # Generate coupon
        discount_info = get_discount_for_level(level)
        coupon_code = None
        
        if discount_info["discount"] > 0:
            coupon_code = generate_coupon_code(discount_info["code_prefix"], interaction.user.id)
            await database.issue_coupon(
                interaction.user.id, coupon_code,
                discount_info["discount"], level
            )
        
        # Create success embed
        embed = discord.Embed(
            title=f"{ui('success')} Verification Successful!",
            color=get_embed_color(level)
        )
        embed.set_thumbnail(url=UI_ICONS["success"])
        
        embed.add_field(
            name=f"{ui('dollar')} Total Purchases",
            value=format_currency(total_spent),
            inline=True
        )
        
        embed.add_field(
            name=f"{ui('level')} Level",
            value=f"{level} ({get_level_name(level)})",
            inline=True
        )
        
        embed.add_field(
            name=f"{ui('cart')} Purchase Count",
            value=str(purchase_count),
            inline=True
        )
        
        if discount_info["discount"] > 0:
            embed.add_field(
                name=f"{ui('coupon')} Your Discount",
                value=f"{discount_info['discount']}%",
                inline=True
            )
        
        if initial_keys > 0:
            embed.add_field(
                name=f"{ui('key')} Loyalty Keys",
                value=f"{initial_keys} key(s) added!",
                inline=True
            )
        
        # Progress to next level
        progress = get_level_progress(total_spent)
        if progress["next_level"]:
            progress_bar = create_progress_bar(progress["progress"])
            embed.add_field(
                name=f"{ui('chart')} Progress to Level {progress['next_level']}",
                value=f"{progress_bar} {progress['progress']:.1f}%\n"
                      f"{ui('dollar')} Remaining: {format_currency(progress['needed_for_next'])}",
                inline=False
            )
        
        if coupon_code:
            embed.add_field(
                name=f"{ui('coupon')} Your Discount Coupon",
                value=f"`{coupon_code}`",
                inline=False
            )
        
        embed.set_footer(text="Welcome to the RobloxCheatz community! Check your DMs for details.")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        
        # Send permanent copy to DM
        try:
            dm_embed = discord.Embed(
                title="Verification Successful!",
                description="Here is your permanent verification record:",
                color=get_embed_color(level)
            )
            dm_embed.add_field(name="Total Purchases", value=format_currency(total_spent), inline=True)
            dm_embed.add_field(name="Level", value=f"{level} ({get_level_name(level)})", inline=True)
            dm_embed.add_field(name="Purchase Count", value=str(purchase_count), inline=True)
            if discount_info["discount"] > 0:
                dm_embed.add_field(name="Your Discount", value=f"{discount_info['discount']}%", inline=True)
            if initial_keys > 0:
                dm_embed.add_field(name="Loyalty Keys", value=f"{initial_keys} key(s)", inline=True)
            if coupon_code:
                dm_embed.add_field(name="Your Discount Coupon", value=f"`{coupon_code}`", inline=False)
            dm_embed.set_footer(text="RobloxCheatz | Keep this for your records")
            dm_embed.timestamp = datetime.now()
            await interaction.user.send(embed=dm_embed)
        except:
            pass
        
        # Log verification
        await database.log_verification(
            interaction.user.id, str(interaction.user), email,
            "verify", True, f"total_spent={total_spent}, level={level}"
        )
        
        # Send to logs
        if config.CHANNELS.get("logs"):
            log_channel = interaction.guild.get_channel(config.CHANNELS["logs"])
            if log_channel:
                log_embed = discord.Embed(
                    title=f"{ui('success')} New Verification",
                    color=config.COLORS["success"]
                )
                log_embed.set_thumbnail(url=UI_ICONS["check"])
                log_embed.add_field(name=f"{ui('user')} User", value=interaction.user.mention, inline=True)
                log_embed.add_field(name=f"{ui('email')} Email", value=mask_email(email), inline=True)
                log_embed.add_field(name=f"{ui('dollar')} Total", value=format_currency(total_spent), inline=True)
                log_embed.add_field(name=f"{ui('level')} Level", value=str(level), inline=True)
                log_embed.timestamp = datetime.now()
                
                await log_channel.send(embed=log_embed)


class TicketView(discord.ui.View):
    """Ticket creation button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket",
        emoji="🎫"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Check verification
        user_data = await database.get_user_by_discord_id(interaction.user.id)
        if not user_data:
            embed = discord.Embed(
                title=f"{ui('cross')} Access Denied",
                description=f"{ui('lock')} Only verified buyers can create tickets.\n\n"
                           f"{ui('arrow_right')} Use the verification channel to verify your account.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["lock"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        is_priority = user_data.get("total_spent", 0) >= 70
        await create_ticket_for_user(interaction, user_data, is_priority)


class CloseTicketView(discord.ui.View):
    """Close ticket button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket",
        emoji="✖️"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        is_owner = channel.name.endswith(interaction.user.name.lower())
        is_admin = interaction.user.guild_permissions.administrator
        
        if not is_owner and not is_admin:
            await interaction.response.send_message(
                f"{ui('cross')} Only ticket owner or admin can close this.",
                ephemeral=True
            )
            return
        
        # Notify Telegram about ticket closure (for VIP tickets)
        if channel.topic and "[VIP]" in channel.topic:
            try:
                await telegram_bot.notify_ticket_closed(channel.id)
            except Exception as e:
                print(f"[!] Failed to notify Telegram about ticket closure: {e}")
        
        # Delete ticket from MongoDB
        ticket_api.sync_delete_ticket(channel.id)
        
        await interaction.response.send_message(f"{ui('time')} Ticket closing in 5 seconds...")
        await asyncio.sleep(5)
        await channel.delete()


class PriorityTicketView(discord.ui.View):
    """Priority ticket button for VIP"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Priority Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="priority_ticket",
        emoji="⚡"
    )
    async def priority_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        user_data = await database.get_user_by_discord_id(interaction.user.id)
        if not user_data or user_data.get("total_spent", 0) < 70:
            embed = discord.Embed(
                title=f"{ui('cross')} Access Denied",
                description=f"{ui('crown')} Priority support is only for $70+ customers.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["crown"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        await create_ticket_for_user(interaction, user_data, is_priority=True)


class ClaimRewardView(discord.ui.View):
    """Claim reward button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Claim Reward",
        style=discord.ButtonStyle.success,
        custom_id="claim_reward",
        emoji="🎁"
    )
    async def claim_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Check verification
        user_data = await database.get_user_by_discord_id(interaction.user.id)
        if not user_data:
            embed = discord.Embed(
                title=f"{ui('cross')} Access Denied",
                description=f"{ui('lock')} Only verified buyers can claim rewards.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["lock"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Check keys balance
        keys_data = await database.get_user_keys(interaction.user.id)
        if keys_data["keys_balance"] < 1:
            embed = discord.Embed(
                title=f"{ui('cross')} No Loyalty Keys",
                description=f"{ui('info')} You don't have any loyalty keys.\n\n"
                           f"{ui('cart')} Earn keys by making purchases:\n"
                           f"{ui('key')} Every {config.LOYALTY_SETTINGS['purchases_per_key']} purchases = 1 key\n\n"
                           f"**{ui('chart')} Your Stats:**\n"
                           f"{ui('key')} Keys Balance: {keys_data['keys_balance']}\n"
                           f"{ui('check')} Total Earned: {keys_data['total_keys_earned']}\n"
                           f"{ui('gift')} Total Used: {keys_data['total_keys_used']}",
                color=config.COLORS["warning"]
            )
            embed.set_thumbnail(url=UI_ICONS["key"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Use a key
        success = await database.use_loyalty_key(interaction.user.id)
        if not success:
            embed = discord.Embed(
                title=f"{ui('cross')} Error",
                description=f"{ui('warning')} Failed to use key. Try again.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
            msg = await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        
        # Roll for reward
        reward_type, reward_value, reward_desc = roll_reward()
        
        # Add reward to database
        expires_days = reward_value if reward_type == "discount_key" else None
        reward_id = await database.add_reward(
            interaction.user.id,
            reward_type,
            str(reward_value),
            reward_desc,
            expires_days
        )
        
        # Generate reward code
        reward_code = database.generate_reward_code()
        
        # Create reward embed
        embed = discord.Embed(
            title=f"{ui('gift')} Reward Claimed!",
            description=f"{ui('key')} You used 1 loyalty key and won:\n\n"
                       f"{ui('star')} **{reward_desc}**\n\n"
                       f"{ui('coupon')} Reward Code: `{reward_code}`",
            color=config.COLORS["gold"]
        )
        embed.set_thumbnail(url=UI_ICONS["gift"])
        
        # Get updated keys balance
        new_keys_data = await database.get_user_keys(interaction.user.id)
        embed.add_field(
            name=f"{ui('key')} Keys Remaining",
            value=str(new_keys_data["keys_balance"]),
            inline=True
        )
        
        # Add reward-specific instructions
        if reward_type == "discount_key":
            embed.add_field(
                name=f"{ui('info')} How to Use",
                value=f"{ui('arrow_right')} Use code `{reward_code}` at checkout within {reward_value} day(s).",
                inline=False
            )
        elif reward_type == "roblox_alt":
            embed.add_field(
                name=f"{ui('info')} How to Claim",
                value=f"{ui('ticket')} Create a ticket to receive your Roblox alt accounts.",
                inline=False
            )
        elif reward_type == "free_product":
            embed.add_field(
                name=f"{ui('info')} How to Claim",
                value=f"{ui('ticket')} Create a ticket to claim your mystery prize!",
                inline=False
            )
        
        embed.set_footer(text="Thank you for your loyalty! Check your DMs for a copy.")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        
        # Send reward to DM as well (permanent copy)
        try:
            dm_embed = discord.Embed(
                title=f"{ui('gift')} Reward Claimed!",
                description=f"{ui('info')} Here is your permanent reward record:\n\n"
                           f"{ui('star')} **{reward_desc}**\n\n"
                           f"{ui('coupon')} Reward Code: `{reward_code}`",
                color=config.COLORS["gold"]
            )
            dm_embed.set_thumbnail(url=UI_ICONS["gift"])
            dm_embed.add_field(
                name=f"{ui('key')} Keys Remaining",
                value=str(new_keys_data["keys_balance"]),
                inline=True
            )
            if reward_type == "discount_key":
                dm_embed.add_field(
                    name=f"{ui('info')} How to Use",
                    value=f"{ui('arrow_right')} Use code `{reward_code}` at checkout within {reward_value} day(s).",
                    inline=False
                )
            elif reward_type == "roblox_alt":
                dm_embed.add_field(
                    name=f"{ui('info')} How to Claim",
                    value=f"{ui('ticket')} Create a ticket in the Discord server to receive your Roblox alt accounts.",
                    inline=False
                )
            elif reward_type == "free_product":
                dm_embed.add_field(
                    name=f"{ui('info')} How to Claim",
                    value=f"{ui('ticket')} Create a ticket in the Discord server to claim your mystery prize!",
                    inline=False
                )
            dm_embed.set_footer(text="RobloxCheatz | Keep this for your records")
            dm_embed.timestamp = datetime.now()
            await interaction.user.send(embed=dm_embed)
        except:
            pass
        
        # Log to channel
        if config.CHANNELS.get("logs"):
            log_channel = interaction.guild.get_channel(config.CHANNELS["logs"])
            if log_channel:
                log_embed = discord.Embed(
                    title=f"{ui('gift')} Reward Claimed",
                    color=config.COLORS["gold"]
                )
                log_embed.set_thumbnail(url=UI_ICONS["gift"])
                log_embed.add_field(name=f"{ui('user')} User", value=interaction.user.mention, inline=True)
                log_embed.add_field(name=f"{ui('star')} Reward", value=reward_desc, inline=True)
                log_embed.add_field(name=f"{ui('coupon')} Code", value=f"`{reward_code}`", inline=True)
                log_embed.timestamp = datetime.now()
                
                await log_channel.send(embed=log_embed)


# ============= TICKET HELPER =============

async def create_ticket_for_user(interaction: discord.Interaction, user_data: dict, is_priority: bool = False):
    """Create a ticket for user"""
    guild = interaction.guild
    user = interaction.user
    
    # Check for existing ticket in MongoDB
    existing_check = ticket_api.sync_get_user_active_ticket(user.id)
    if existing_check.get("has_ticket"):
        existing_channel = guild.get_channel(existing_check["channel_id"])
        if existing_channel:
            embed = discord.Embed(
                title=f"{ui('warning')} Ticket Exists",
                description=f"{ui('ticket')} You already have an open ticket: {existing_channel.mention}",
                color=config.COLORS["warning"]
            )
            embed.set_thumbnail(url=UI_ICONS["ticket"])
            await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
            return
        else:
            # Channel deleted but ticket exists in DB - clean up
            ticket_api.sync_delete_ticket(existing_check["channel_id"])
    
    # Also check by channel name (backup)
    existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
    if existing:
        embed = discord.Embed(
            title=f"{ui('warning')} Ticket Exists",
            description=f"{ui('ticket')} You already have an open ticket: {existing.mention}",
            color=config.COLORS["warning"]
        )
        embed.set_thumbnail(url=UI_ICONS["ticket"])
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        return
    
    # Find tickets category
    category = discord.utils.get(guild.categories, name="Tickets")
    if not category:
        category = await guild.create_category("Tickets")
    
    total_spent = user_data.get("total_spent", 0)
    
    # Create channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    
    for role in guild.roles:
        if role.permissions.administrator:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    priority_mark = "[VIP] " if is_priority else ""
    ticket_channel = await guild.create_text_channel(
        name=f"ticket-{user.name.lower()}",
        category=category,
        overwrites=overwrites,
        topic=f"{priority_mark}Ticket from {user} | Email: {mask_email(user_data['email'])} | Spent: ${total_spent:.2f}"
    )
    
    # Save ticket to MongoDB
    ticket_result = ticket_api.sync_create_ticket(
        channel_id=ticket_channel.id,
        discord_user_id=user.id,
        discord_username=user.display_name,
        email=user_data.get("email", "N/A"),
        total_spent=total_spent,
        purchase_count=user_data.get("purchase_count", 0),
        level=user_data.get("level", 1)
    )
    
    if not ticket_result.get("success"):
        # If failed to create in DB, delete channel
        await ticket_channel.delete()
        embed = discord.Embed(
            title=f"{ui('cross')} Error",
            description=f"{ui('warning')} Failed to create ticket. Please try again.",
            color=config.COLORS["error"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        return
    
    # Send welcome message
    priority_text = f"{ui('crown')} **[VIP] PRIORITY TICKET** - $70+ Customer\n\n" if is_priority else ""
    
    embed = discord.Embed(
        title=f"{ui('crown') if is_priority else ui('ticket')} {'[VIP] ' if is_priority else ''}Ticket Created",
        description=f"{priority_text}{ui('user')} Hello {user.mention}!\n\n"
                   f"{ui('info')} Please describe your issue and an administrator will respond shortly.\n\n"
                   f"**{ui('chart')} Your Profile:**\n"
                   f"{ui('dollar')} Total Spent: ${total_spent:.2f}\n"
                   f"{ui('level')} Level: {user_data.get('level', 1)} ({get_level_name(user_data.get('level', 1))})",
        color=config.COLORS["gold"] if is_priority else config.COLORS["primary"]
    )
    embed.set_thumbnail(url=UI_ICONS["crown"] if is_priority else UI_ICONS["ticket"])
    embed.set_footer(text="Click the button below to close this ticket")
    
    await ticket_channel.send(content=user.mention, embed=embed, view=CloseTicketView())
    
    # Notify user
    success_embed = discord.Embed(
        title=f"{ui('success')} Ticket Created",
        description=f"{ui('ticket')} Your ticket: {ticket_channel.mention}",
        color=config.COLORS["success"]
    )
    success_embed.set_thumbnail(url=UI_ICONS["ticket"])
    await interaction.followup.send(embed=success_embed, ephemeral=True, delete_after=15)
    
    # Send Telegram notification for VIP tickets
    if is_priority:
        try:
            await telegram_bot.notify_new_vip_ticket(
                channel_id=ticket_channel.id,
                discord_user_id=user.id,
                discord_username=user.display_name,
                email=user_data.get("email", "N/A"),
                total_spent=total_spent,
                purchase_count=user_data.get("purchase_count", 0),
                level=user_data.get("level", 1)
            )
        except Exception as e:
            print(f"[!] Failed to send Telegram notification: {e}")


# ============= ADMIN COG =============

class AdminCog(commands.Cog):
    """Admin commands"""
    
    def __init__(self, bot: VerificationBot):
        self.bot = bot
    
    async def is_admin(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    
    @app_commands.command(name="admin_unlink", description="[ADMIN] Unlink email from Discord account")
    @app_commands.describe(
        user="Discord user",
        email="Email to unlink (if user not specified)"
    )
    async def admin_unlink(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        email: Optional[str] = None
    ):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        if not user and not email:
            await interaction.followup.send(f"{ui('cross')} Specify a user or email", ephemeral=True, delete_after=15)
            return
        
        success = False
        target_info = ""
        
        if user:
            user_data = await database.get_user_by_discord_id(user.id)
            if user_data:
                success = await database.unlink_email(user.id)
                target_info = f"user {user.mention}"
                
                if success and self.bot.role_manager:
                    await self.bot.role_manager.remove_all_buyer_roles(user)
        elif email:
            user_data = await database.get_user_by_email(email)
            if user_data:
                success = await database.unlink_email_by_email(email)
                target_info = f"email `{mask_email(email)}`"
                
                if success and self.bot.role_manager:
                    member = interaction.guild.get_member(user_data["discord_id"])
                    if member:
                        await self.bot.role_manager.remove_all_buyer_roles(member)
        
        if success:
            embed = discord.Embed(
                title=f"{ui('success')} Unlinked",
                description=f"{ui('check')} Successfully unlinked {target_info}",
                color=config.COLORS["success"]
            )
            embed.set_thumbnail(url=UI_ICONS["success"])
        else:
            embed = discord.Embed(
                title=f"{ui('cross')} Not Found",
                description=f"{ui('warning')} User or email not linked.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
    
    @app_commands.command(name="admin_lookup", description="[ADMIN] View user information")
    @app_commands.describe(
        user="Discord user",
        email="Email to search"
    )
    async def admin_lookup(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        email: Optional[str] = None
    ):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        user_data = None
        if user:
            user_data = await database.get_user_by_discord_id(user.id)
        elif email:
            user_data = await database.get_user_by_email(email)
        
        if not user_data:
            await interaction.followup.send(f"{ui('cross')} User not found", ephemeral=True, delete_after=15)
            return
        
        keys_data = await database.get_user_keys(user_data["discord_id"])
        
        embed = discord.Embed(
            title=f"{ui('user')} User Information",
            color=get_embed_color(user_data["level"])
        )
        embed.set_thumbnail(url=UI_ICONS["user"])
        
        member = interaction.guild.get_member(user_data["discord_id"])
        
        embed.add_field(name=f"{ui('info')} Discord ID", value=str(user_data["discord_id"]), inline=True)
        embed.add_field(name=f"{ui('user')} Discord", value=member.mention if member else "Not in server", inline=True)
        embed.add_field(name=f"{ui('email')} Email", value=user_data["email"], inline=True)
        embed.add_field(name=f"{ui('dollar')} Total Spent", value=format_currency(user_data["total_spent"]), inline=True)
        embed.add_field(name=f"{ui('cart')} Purchase Count", value=str(user_data.get("purchase_count", 0)), inline=True)
        embed.add_field(name=f"{ui('level')} Level", value=str(user_data["level"]), inline=True)
        embed.add_field(name=f"{ui('key')} Loyalty Keys", value=str(keys_data["keys_balance"]), inline=True)
        embed.add_field(name=f"{ui('time')} Verified At", value=user_data["verified_at"], inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
    
    @app_commands.command(name="admin_sync", description="[ADMIN] Sync all users")
    async def admin_sync(self, interaction: discord.Interaction):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title=f"{ui('refresh')} Syncing",
            description=f"{ui('time')} Syncing all users... This may take a few minutes.",
            color=config.COLORS["primary"]
        )
        embed.set_thumbnail(url=UI_ICONS["refresh"])
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        
        komerza_api.clear_cache()
        await self.bot.sync_purchases()
        
        embed = discord.Embed(
            title=f"{ui('success')} Sync Complete",
            description=f"{ui('check')} All users have been synced.",
            color=config.COLORS["success"]
        )
        embed.set_thumbnail(url=UI_ICONS["success"])
        await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="admin_give_keys", description="[ADMIN] Give loyalty keys to user")
    @app_commands.describe(
        user="Discord user",
        amount="Number of keys to give"
    )
    async def admin_give_keys(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int
    ):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        user_data = await database.get_user_by_discord_id(user.id)
        if not user_data:
            await interaction.followup.send(f"{ui('cross')} User is not verified", ephemeral=True, delete_after=15)
            return
        
        new_balance = await database.add_loyalty_keys(user.id, amount)
        
        embed = discord.Embed(
            title=f"{ui('success')} Keys Added",
            description=f"{ui('key')} Added {amount} keys to {user.mention}\n\n"
                       f"{ui('info')} New balance: {new_balance} keys",
            color=config.COLORS["success"]
        )
        embed.set_thumbnail(url=UI_ICONS["key"])
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        
        # Notify user
        try:
            notify_embed = discord.Embed(
                title=f"{ui('gift')} Loyalty Keys Received!",
                description=f"{ui('star')} An administrator gave you **{amount}** loyalty key(s)!\n\n"
                           f"{ui('arrow_right')} Use them in the rewards channel.",
                color=config.COLORS["gold"]
            )
            notify_embed.set_thumbnail(url=UI_ICONS["key"])
            await user.send(embed=notify_embed)
        except:
            pass
    
    @app_commands.command(name="admin_setup", description="[ADMIN] Full setup - channels, roles, infrastructure")
    async def admin_setup(self, interaction: discord.Interaction):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            report = await setup_infrastructure(interaction.guild, self.bot)
            
            lines = ["**Setup completed successfully!**\n"]
            
            if report.get("created"):
                lines.append("**✅ Created:**")
                for item in report["created"]:
                    lines.append(f"• {item}")
                lines.append("")
            
            if report.get("existing"):
                lines.append("**📋 Already exists:**")
                for item in report["existing"][:15]:
                    lines.append(f"• {item}")
                if len(report["existing"]) > 15:
                    lines.append(f"... +{len(report['existing']) - 15} more")
                lines.append("")
            
            if report.get("errors"):
                lines.append("**❌ Errors:**")
                for item in report["errors"]:
                    lines.append(f"• {item}")
            
            # Summary
            lines.append(f"\n**Summary:**")
            lines.append(f"• Categories: {report.get('categories', 0)}")
            lines.append(f"• Channels: {report.get('channels', 0)}")
            lines.append(f"• Roles: {report.get('roles', 0)}")
            
            embed = discord.Embed(
                title=f"{ui('success')} Setup Complete",
                description="\n".join(lines),
                color=config.COLORS["success"]
            )
            embed.set_thumbnail(url=UI_ICONS["success"])
        except Exception as e:
            embed = discord.Embed(
                title=f"{ui('cross')} Error",
                description=f"{ui('warning')} Setup error: {e}",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
    
    @app_commands.command(name="admin_update_status", description="[ADMIN] Force update status channel")
    async def admin_update_status(self, interaction: discord.Interaction):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        status_channel = discord.utils.get(interaction.guild.text_channels, name="status")
        if status_channel:
            await update_status_embed(status_channel, self.bot)
            embed = discord.Embed(
                title=f"{ui('success')} Status Updated",
                description=f"{ui('check')} Status channel has been updated with latest WEAO data.",
                color=config.COLORS["success"]
            )
            embed.set_thumbnail(url=UI_ICONS["success"])
        else:
            embed = discord.Embed(
                title=f"{ui('cross')} Error",
                description=f"{ui('warning')} Status channel not found. Run /admin_setup first.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)

    @app_commands.command(name="admin_refresh_embeds", description="[ADMIN] Refresh all infrastructure embeds with new thumbnails")
    async def admin_refresh_embeds(self, interaction: discord.Interaction):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        refreshed = []
        errors = []
        
        # Refresh verify channel
        verify_channel = discord.utils.get(guild.text_channels, name="verify")
        if verify_channel:
            try:
                await verify_channel.purge(limit=10)
                embed = discord.Embed(
                    title=f"{ui('shield')} Account Verification",
                    description=(
                        f"**Welcome to RobloxCheatz!**\n\n"
                        f"Verify your purchase to unlock:\n\n"
                        f"{ui('check')} Buyer role based on total spent\n"
                        f"{ui('unlock')} Access to private channels\n"
                        f"{ui('dollar')} Discount coupons (up to 10%)\n"
                        f"{ui('crown')} Priority support ($70+)\n"
                        f"{ui('gift')} Loyalty rewards program\n\n"
                        f"{ui('arrow_right')} Click the button below to verify:"
                    ),
                    color=config.COLORS["primary"]
                )
                embed.set_thumbnail(url=UI_ICONS["shield"])
                embed.set_footer(text="RobloxCheatz | Verification System")
                await verify_channel.send(embed=embed, view=VerifyButtonView())
                refreshed.append("verify")
            except Exception as e:
                errors.append(f"verify: {e}")
        
        # Refresh support channel
        support_channel = discord.utils.get(guild.text_channels, name="support")
        if support_channel:
            try:
                await support_channel.purge(limit=10)
                embed = discord.Embed(
                    title=f"{ui('headset')} Customer Support",
                    description=(
                        f"Need help? Create a ticket!\n\n"
                        f"**What we can help with:**\n"
                        f"{ui('wrench')} Product issues\n"
                        f"{ui('cart')} Order questions\n"
                        f"{ui('dollar')} Refund requests\n"
                        f"{ui('settings')} Technical problems\n\n"
                        f"**Response Times:**\n"
                        f"{ui('crown')} VIP Customers ($70+): Up to 1 hour\n"
                        f"{ui('time')} Standard Tickets: Up to 24 hours\n\n"
                        f"{ui('arrow_right')} Click the button below to create a ticket:"
                    ),
                    color=config.COLORS["primary"]
                )
                embed.set_thumbnail(url=UI_ICONS["headset"])
                embed.set_footer(text="RobloxCheatz | Support")
                await support_channel.send(embed=embed, view=TicketView())
                refreshed.append("support")
            except Exception as e:
                errors.append(f"support: {e}")
        
        # Refresh rewards channel
        rewards_channel = discord.utils.get(guild.text_channels, name="rewards")
        if rewards_channel:
            try:
                await rewards_channel.purge(limit=10)
                rewards_text = ""
                for reward_type, value, chance, desc in config.REWARDS:
                    rewards_text += f"{ui('gift')} {desc} - {chance}%\n"
                embed = discord.Embed(
                    title=f"{ui('gift')} Loyalty Rewards",
                    description=(
                        f"**Earn keys through purchases!**\n\n"
                        f"{ui('key')} Every **{config.LOYALTY_SETTINGS['purchases_per_key']} purchases** = 1 Loyalty Key\n\n"
                        f"**Available Rewards:**\n"
                        f"{rewards_text}\n"
                        f"{ui('arrow_right')} Click the button below to use a key and claim a random reward:"
                    ),
                    color=config.COLORS["gold"]
                )
                embed.set_thumbnail(url=UI_ICONS["gift"])
                embed.set_footer(text="RobloxCheatz | Loyalty Program")
                await rewards_channel.send(embed=embed, view=ClaimRewardView())
                refreshed.append("rewards")
            except Exception as e:
                errors.append(f"rewards: {e}")
        
        # Refresh VIP support channel
        vip_support = discord.utils.get(guild.text_channels, name="vip-support")
        if vip_support:
            try:
                await vip_support.purge(limit=10)
                embed = discord.Embed(
                    title=f"{ui('crown')} VIP Priority Support",
                    description=(
                        f"**Thank you for your purchases!**\n\n"
                        f"As a VIP customer ($70+) you get:\n\n"
                        f"{ui('time')} Priority response time (up to 1 hour)\n"
                        f"{ui('dollar')} Exclusive discounts\n"
                        f"{ui('user')} VIP chat access\n"
                        f"{ui('headset')} Direct admin support\n\n"
                        f"{ui('arrow_right')} Create a priority ticket for fast assistance:"
                    ),
                    color=config.COLORS["gold"]
                )
                embed.set_thumbnail(url=UI_ICONS["crown"])
                embed.set_footer(text="RobloxCheatz | VIP Support")
                await vip_support.send(embed=embed, view=PriorityTicketView())
                refreshed.append("vip-support")
            except Exception as e:
                errors.append(f"vip-support: {e}")
        
        # Refresh status channel
        status_channel = discord.utils.get(guild.text_channels, name="status")
        if status_channel:
            try:
                await update_status_embed(status_channel, self.bot)
                refreshed.append("status")
            except Exception as e:
                errors.append(f"status: {e}")
        
        # Build result embed
        if refreshed:
            description = f"{ui('info')} **Refreshed channels:**\n" + "\n".join([f"{ui('check')} #{ch}" for ch in refreshed])
            if errors:
                description += f"\n\n{ui('warning')} **Errors:**\n" + "\n".join([f"{ui('cross')} {e}" for e in errors])
            embed = discord.Embed(
                title=f"{ui('success')} Embeds Refreshed",
                description=description,
                color=config.COLORS["success"]
            )
            embed.set_thumbnail(url=UI_ICONS["success"])
        else:
            embed = discord.Embed(
                title=f"{ui('cross')} Error",
                description=f"{ui('warning')} No channels were refreshed.\n\n" + "\n".join(errors) if errors else f"{ui('info')} No channels found.",
                color=config.COLORS["error"]
            )
            embed.set_thumbnail(url=UI_ICONS["cross"])
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)

    @app_commands.command(name="admin_clear_emojis", description="[ADMIN] Clear all bot emojis from main server")
    async def admin_clear_emojis(self, interaction: discord.Interaction):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title=f"{ui('refresh')} Clearing Emojis...",
            description=f"{ui('time')} Removing bot emojis from main server...",
            color=config.COLORS["primary"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        
        deleted = await clear_main_server_emojis(interaction.guild)
        
        embed = discord.Embed(
            title=f"{ui('success')} Emojis Cleared",
            description=f"{ui('check')} Deleted **{deleted}** emojis from main server.\n\n"
                       f"{ui('info')} Emojis are now stored on emoji servers.",
            color=config.COLORS["success"]
        )
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="admin_setup_emojis", description="[ADMIN] Setup all emojis on emoji servers")
    async def admin_setup_emojis(self, interaction: discord.Interaction):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title=f"{ui('refresh')} Setting up Emojis...",
            description=f"{ui('time')} Creating emojis on emoji servers...",
            color=config.COLORS["primary"]
        )
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)
        
        # Create missing emojis
        await create_missing_emojis(self.bot, interaction.guild)
        
        # Reload emojis
        await setup_ui_emojis(self.bot, interaction.guild)
        await setup_product_emojis(self.bot, interaction.guild)
        
        embed = discord.Embed(
            title=f"{ui('success')} Emojis Setup Complete",
            description=f"{ui('check')} **{len(UI_EMOJIS)}** UI emojis loaded\n"
                       f"{ui('check')} **{len(PRODUCT_EMOJIS)}** product emojis loaded",
            color=config.COLORS["success"]
        )
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="admin_check_products", description="[ADMIN] Check & fix products/roles for email")
    @app_commands.describe(email="Email to check", fix_roles="Automatically assign missing roles")
    async def admin_check_products(self, interaction: discord.Interaction, email: str, fix_roles: bool = True):
        if not await self.is_admin(interaction):
            await interaction.response.send_message(f"{ui('cross')} Insufficient permissions", ephemeral=True, delete_after=15)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Get customer info
        customer = await komerza_api.get_customer_by_email(email)
        
        if not customer:
            await interaction.followup.send(f"{ui('cross')} Customer not found: `{email}`", ephemeral=True, delete_after=15)
            return
        
        # Find linked Discord user
        user_data = await database.get_user_by_email(email)
        member = None
        if user_data:
            member = interaction.guild.get_member(user_data["discord_id"])
        
        # Get orders and products
        orders = await komerza_api.get_orders_by_email(email)
        products = await komerza_api.get_customer_products(email)
        total_spent = customer.get('totalSpend', 0)
        
        # Get unique product names
        unique_names = set()
        for p in products:
            name = p.get('name', '').lower()
            if name:
                unique_names.add(name)
        
        # Check which products would be matched
        product_name_map = {
            "wave": ["wave"],
            "seliware": ["seliware"],
            "matcha": ["matcha"],
            "potassium": ["potassium"],
            "bunni": ["bunni", "bunni.lol"],
            "volt": ["volt"],
            "volcano": ["volcano"],
            "serotonin": ["serotonin"],
            "isabelle": ["isabelle"],
            "ronin": ["ronin"],
            "yerba": ["yerba"],
            "codex": ["codex"],
            "arceus": ["arceus", "arceus x", "arceus x v5", "arceusxv5"],
        }
        
        matched_products = set()
        for product_name in unique_names:
            for product_id, aliases in product_name_map.items():
                for alias in aliases:
                    if alias in product_name:
                        matched_products.add(product_id)
                        break
        
        # Build response
        lines = [
            f"**Email:** `{email}`",
            f"**Discord:** {member.mention if member else '❌ Not linked / Not in server'}",
            f"**Status:** {customer.get('status', 'N/A')}",
            f"**Total Spend:** ${total_spent:.2f}",
            f"**Orders:** {len(orders)} paid",
            ""
        ]
        
        # Products from API
        if unique_names:
            lines.append(f"**Products from API ({len(unique_names)}):**")
            for name in list(unique_names)[:10]:
                lines.append(f"• `{name}`")
            if len(unique_names) > 10:
                lines.append(f"... +{len(unique_names) - 10} more")
        else:
            lines.append("**Products:** None found")
        
        lines.append("")
        lines.append(f"**Matched Products:** {', '.join(matched_products) if matched_products else 'None'}")
        
        # Roles status
        lines.append("")
        lines.append("**Roles:**")
        
        roles_assigned = []
        roles_already_had = []
        roles_missing_no_member = []
        
        for pid in matched_products:
            role_info = config.PRODUCT_ROLES.get(pid)
            if role_info:
                role = discord.utils.get(interaction.guild.roles, name=role_info[0])
                if not role:
                    lines.append(f"• {role_info[0]} - ❌ Role doesn't exist!")
                elif not member:
                    roles_missing_no_member.append(role_info[0])
                elif role in member.roles:
                    roles_already_had.append(role_info[0])
                else:
                    if fix_roles and self.bot.role_manager:
                        try:
                            await member.add_roles(role)
                            roles_assigned.append(role_info[0])
                        except Exception as e:
                            lines.append(f"• {role_info[0]} - ❌ Error: {e}")
                    else:
                        lines.append(f"• {role_info[0]} - ⚠️ Missing (fix_roles=False)")
        
        # Also check purchase level roles if fixing
        if fix_roles and member and self.bot.role_manager:
            purchase_roles = await self.bot.role_manager.assign_purchase_roles(member, total_spent)
            for r in purchase_roles:
                roles_assigned.append(r.name)
        
        if roles_already_had:
            lines.append(f"✅ Already has: {', '.join(roles_already_had)}")
        if roles_assigned:
            lines.append(f"🔧 Assigned: {', '.join(roles_assigned)}")
        if roles_missing_no_member:
            lines.append(f"⚠️ Can't assign (no member): {', '.join(roles_missing_no_member)}")
        if not roles_already_had and not roles_assigned and not roles_missing_no_member and matched_products:
            lines.append("✅ All roles OK")
        
        # Truncate if too long
        description = "\n".join(lines)
        if len(description) > 4000:
            description = description[:3950] + "\n\n... (truncated)"
        
        embed = discord.Embed(
            title=f"{ui('search')} Customer Check: {email}",
            description=description,
            color=config.COLORS["success"] if roles_assigned or roles_already_had else config.COLORS["primary"]
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True, delete_after=15)


# ============= INFRASTRUCTURE SETUP =============

async def setup_infrastructure(guild: discord.Guild, bot):
    """Create all channels and infrastructure automatically"""
    print("[...] Setting up infrastructure...")
    
    report = {
        "created": [],
        "existing": [],
        "errors": [],
        "categories": 0,
        "channels": 0,
        "roles": 0
    }
    
    # ========== CATEGORIES ==========
    categories_to_create = ["Information", "Buyers Zone", "VIP Zone", "Tickets"]
    category_refs = {}
    
    for cat_name in categories_to_create:
        cat = discord.utils.get(guild.categories, name=cat_name)
        if not cat:
            try:
                cat = await guild.create_category(cat_name)
                report["created"].append(f"📁 {cat_name}")
                print(f"  [+] Created category: {cat_name}")
            except Exception as e:
                report["errors"].append(f"Category {cat_name}: {e}")
        else:
            report["existing"].append(f"📁 {cat_name}")
        category_refs[cat_name] = cat
        report["categories"] += 1
    
    info_category = category_refs.get("Information")
    buyers_category = category_refs.get("Buyers Zone")
    vip_category = category_refs.get("VIP Zone")
    tickets_category = category_refs.get("Tickets")
    
    # ========== ROLES ==========
    # Ensure all roles exist via role manager
    if bot.role_manager:
        await bot.role_manager.ensure_roles_exist()
        
        # Count roles
        for _, (name, _) in config.PURCHASE_ROLES.items():
            role = discord.utils.get(guild.roles, name=name)
            if role:
                report["roles"] += 1
                report["existing"].append(f"🏷️ {name}")
        
        for _, (name, _) in config.PRODUCT_ROLES.items():
            role = discord.utils.get(guild.roles, name=name)
            if role:
                report["roles"] += 1
        
        for name, _, _ in config.SPECIAL_ROLES.values():
            role = discord.utils.get(guild.roles, name=name)
            if role:
                report["roles"] += 1
    
    verified_name = config.SPECIAL_ROLES["verified_buyer"][0]
    verified_role = discord.utils.get(guild.roles, name=verified_name)
    
    priority_name = config.SPECIAL_ROLES["priority_support"][0]
    priority_role = discord.utils.get(guild.roles, name=priority_name)
    
    # ========== CHANNELS ==========
    
    # Channel definitions: (name, category_key, topic, requires_verified, requires_priority, send_messages)
    channels_config = [
        ("status", "Information", "Software Status | Updated every 10 minutes", False, False, False),
        ("verify", "Information", "Account Verification | Click the button", False, False, False),
        ("support", "Buyers Zone", "Create a support ticket", True, False, False),
        ("buyers-chat", "Buyers Zone", "Chat for verified buyers", True, False, True),
        ("rewards", "Buyers Zone", "Claim your loyalty rewards", True, False, False),
        ("vip-chat", "VIP Zone", "Exclusive chat for VIP customers ($70+)", False, True, True),
        ("vip-support", "VIP Zone", "Priority support for VIP", False, True, False),
        ("logs", "Information", "Bot activity logs", False, False, False),
    ]
    
    channel_refs = {}
    
    for ch_name, cat_key, topic, req_verified, req_priority, allow_send in channels_config:
        channel = discord.utils.get(guild.text_channels, name=ch_name)
        category = category_refs.get(cat_key)
        
        if not channel:
            try:
                # Build permissions
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=not req_verified and not req_priority and ch_name != "logs",
                        send_messages=False,
                        add_reactions=False
                    ),
                    guild.me: discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=True, 
                        manage_messages=True
                    ),
                }
                
                if req_verified and verified_role:
                    overwrites[verified_role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=allow_send
                    )
                
                if req_priority and priority_role:
                    overwrites[priority_role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=allow_send
                    )
                
                # Hide verify channel from verified users
                if ch_name == "verify" and verified_role:
                    overwrites[verified_role] = discord.PermissionOverwrite(
                        read_messages=False
                    )
                
                channel = await guild.create_text_channel(
                    name=ch_name,
                    category=category,
                    overwrites=overwrites,
                    topic=topic
                )
                report["created"].append(f"#️⃣ {ch_name}")
                print(f"  [+] Created channel: {ch_name}")
            except Exception as e:
                report["errors"].append(f"Channel {ch_name}: {e}")
        else:
            # Update permissions for existing verify channel
            if ch_name == "verify" and verified_role:
                try:
                    await channel.set_permissions(verified_role, read_messages=False)
                except Exception as e:
                    print(f"[!] Failed to update verify channel permissions: {e}")
            report["existing"].append(f"#️⃣ {ch_name}")
        
        channel_refs[ch_name] = channel
        report["channels"] += 1
    
    # ========== SETUP EMBEDS ==========
    
    # Status channel
    status_channel = channel_refs.get("status")
    if status_channel:
        await update_status_embed(status_channel, bot)
    
    # Verify channel
    verify_channel = channel_refs.get("verify")
    if verify_channel:
        async for msg in verify_channel.history(limit=10):
            if msg.author == guild.me and msg.embeds:
                break
        else:
            embed = discord.Embed(
                title=f"{ui('shield')} Account Verification",
                description=(
                    f"**Welcome to RobloxCheatz!**\n\n"
                    f"Verify your purchase to unlock:\n\n"
                    f"{ui('check')} Buyer role based on total spent\n"
                    f"{ui('unlock')} Access to private channels\n"
                    f"{ui('dollar')} Discount coupons (up to 10%)\n"
                    f"{ui('crown')} Priority support ($70+)\n"
                    f"{ui('gift')} Loyalty rewards program\n\n"
                    f"{ui('arrow_right')} Click the button below to verify:"
                ),
                color=config.COLORS["primary"]
            )
            embed.set_thumbnail(url=UI_ICONS["shield"])
            embed.set_footer(text="RobloxCheatz | Verification System")
            await verify_channel.send(embed=embed, view=VerifyButtonView())
    
    # Support channel
    support_channel = channel_refs.get("support")
    if support_channel:
        async for msg in support_channel.history(limit=10):
            if msg.author == guild.me and msg.embeds:
                break
        else:
            embed = discord.Embed(
                title=f"{ui('headset')} Customer Support",
                description=(
                    f"Need help? Create a ticket!\n\n"
                    f"**What we can help with:**\n"
                    f"{ui('wrench')} Product issues\n"
                    f"{ui('cart')} Order questions\n"
                    f"{ui('dollar')} Refund requests\n"
                    f"{ui('settings')} Technical problems\n\n"
                    f"**Response Times:**\n"
                    f"{ui('crown')} VIP Customers ($70+): Up to 1 hour\n"
                    f"{ui('time')} Standard Tickets: Up to 24 hours\n\n"
                    f"{ui('arrow_right')} Click the button below to create a ticket:"
                ),
                color=config.COLORS["primary"]
            )
            embed.set_thumbnail(url=UI_ICONS["headset"])
            embed.set_footer(text="RobloxCheatz | Support")
            await support_channel.send(embed=embed, view=TicketView())
    
    # Rewards channel
    rewards_channel = channel_refs.get("rewards")
    if rewards_channel:
        async for msg in rewards_channel.history(limit=10):
            if msg.author == guild.me and msg.embeds:
                break
        else:
            rewards_text = ""
            for reward_type, value, chance, desc in config.REWARDS:
                rewards_text += f"{ui('gift')} {desc} - {chance}%\n"
            
            embed = discord.Embed(
                title=f"{ui('gift')} Loyalty Rewards",
                description=(
                    f"**Earn keys through purchases!**\n\n"
                    f"{ui('key')} Every **{config.LOYALTY_SETTINGS['purchases_per_key']} purchases** = 1 Loyalty Key\n\n"
                    f"**Available Rewards:**\n"
                    f"{rewards_text}\n"
                    f"{ui('arrow_right')} Click the button below to use a key and claim a random reward:"
                ),
                color=config.COLORS["gold"]
            )
            embed.set_thumbnail(url=UI_ICONS["gift"])
            embed.set_footer(text="RobloxCheatz | Loyalty Program")
            await rewards_channel.send(embed=embed, view=ClaimRewardView())
    
    # VIP Support channel
    vip_support = channel_refs.get("vip-support")
    if vip_support:
        async for msg in vip_support.history(limit=10):
            if msg.author == guild.me and msg.embeds:
                break
        else:
            embed = discord.Embed(
                title=f"{ui('crown')} VIP Priority Support",
                description=(
                    f"**Thank you for your purchases!**\n\n"
                    f"As a VIP customer ($70+) you get:\n\n"
                    f"{ui('time')} Priority response time (up to 1 hour)\n"
                    f"{ui('dollar')} Exclusive discounts\n"
                    f"{ui('user')} VIP chat access\n"
                    f"{ui('headset')} Direct admin support\n\n"
                    f"{ui('arrow_right')} Create a priority ticket for fast assistance:"
                ),
                color=config.COLORS["gold"]
            )
            embed.set_thumbnail(url=UI_ICONS["crown"])
            embed.set_footer(text="RobloxCheatz | VIP Support")
            await vip_support.send(embed=embed, view=PriorityTicketView())
    
    # Update config with channel IDs
    config.CHANNELS["status"] = channel_refs.get("status").id if channel_refs.get("status") else None
    config.CHANNELS["verify"] = channel_refs.get("verify").id if channel_refs.get("verify") else None
    config.CHANNELS["support"] = channel_refs.get("support").id if channel_refs.get("support") else None
    config.CHANNELS["buyers_chat"] = channel_refs.get("buyers-chat").id if channel_refs.get("buyers-chat") else None
    config.CHANNELS["rewards"] = channel_refs.get("rewards").id if channel_refs.get("rewards") else None
    config.CHANNELS["vip_chat"] = channel_refs.get("vip-chat").id if channel_refs.get("vip-chat") else None
    config.CHANNELS["vip_support"] = channel_refs.get("vip-support").id if channel_refs.get("vip-support") else None
    config.CHANNELS["logs"] = channel_refs.get("logs").id if channel_refs.get("logs") else None
    
    print("[OK] Infrastructure setup complete!")
    return report


# ============= HTTP SERVER FOR RENDER =============

from aiohttp import web

async def health_handler(request):
    """Health check endpoint for Render"""
    return web.Response(text="RobloxCheatz Bot is running!", status=200)

async def api_tickets_handler(request):
    """API endpoint to get all tickets"""
    try:
        tickets = ticket_api.sync_get_all_active_tickets()
        return web.json_response({"success": True, "tickets": tickets, "count": len(tickets)})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_messages_handler(request):
    """API endpoint to get messages for a ticket"""
    try:
        channel_id = request.query.get("channel_id")
        if not channel_id:
            return web.json_response({"success": False, "error": "channel_id required"}, status=400)
        
        messages = ticket_api.sync_get_ticket_messages(int(channel_id))
        return web.json_response({"success": True, "messages": messages})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_send_handler(request):
    """API endpoint to send message to ticket"""
    try:
        data = await request.json()
        channel_id = data.get("channel_id")
        message = data.get("message")
        sender = data.get("sender", "Admin")
        
        if not channel_id or not message:
            return web.json_response({"success": False, "error": "channel_id and message required"}, status=400)
        
        # Save to MongoDB
        ticket_api.sync_add_ticket_message(int(channel_id), sender, message, "telegram")
        
        # Send to Discord channel
        bot = request.app.get("bot")
        if bot:
            channel = bot.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    description=message,
                    color=0x9B59B6
                )
                embed.set_author(name=f"📱 {sender} (Telegram)")
                await channel.send(embed=embed)
        
        return web.json_response({"success": True})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_delete_handler(request):
    """API endpoint to delete/close a ticket"""
    try:
        data = await request.json()
        channel_id = data.get("channel_id")
        
        if not channel_id:
            return web.json_response({"success": False, "error": "channel_id required"}, status=400)
        
        # Delete from MongoDB
        ticket_api.sync_delete_ticket(int(channel_id))
        
        # Delete Discord channel
        bot = request.app.get("bot")
        if bot:
            channel = bot.get_channel(int(channel_id))
            if channel:
                await channel.delete(reason="Closed via Telegram WebApp")
        
        return web.json_response({"success": True})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

@web.middleware
async def cors_middleware(request, handler):
    """CORS middleware for API requests"""
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

async def telegram_webhook_handler(request):
    """Handle Telegram webhook updates"""
    try:
        data = await request.json()
        await telegram_bot.process_telegram_update(data)
        return web.Response(text="OK", status=200)
    except Exception as e:
        print(f"[!] Telegram webhook error: {e}")
        return web.Response(text="Error", status=500)

async def start_http_server(bot):
    """Start HTTP server for health checks and API"""
    app = web.Application(middlewares=[cors_middleware])
    app["bot"] = bot
    
    # Routes
    app.router.add_get("/", health_handler)
    app.router.add_get("/api/tickets", api_tickets_handler)
    app.router.add_get("/api/messages", api_messages_handler)
    app.router.add_post("/api/send", api_send_handler)
    app.router.add_post("/api/delete", api_delete_handler)
    app.router.add_options("/api/send", lambda r: web.Response())
    app.router.add_options("/api/delete", lambda r: web.Response())
    
    # Telegram webhook endpoint
    app.router.add_post("/telegram/webhook", telegram_webhook_handler)
    
    # Get port from environment (Render sets PORT)
    port = int(os.environ.get("PORT", 10000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[OK] HTTP server started on port {port}")
    
    # Set Telegram webhook (delete old first)
    webhook_url = os.environ.get("WEBHOOK_URL", "https://robloxcheatztg.onrender.com")
    try:
        import httpx
        tg_token = os.environ.get("TELEGRAM_TOKEN")
        async with httpx.AsyncClient() as client:
            # First delete any existing webhook
            await client.post(f"https://api.telegram.org/bot{tg_token}/deleteWebhook")
            print("[OK] Old Telegram webhook deleted")
            
            # Set new webhook
            resp = await client.post(
                f"https://api.telegram.org/bot{tg_token}/setWebhook",
                json={"url": f"{webhook_url}/telegram/webhook", "drop_pending_updates": True}
            )
            result = resp.json()
            if result.get("ok"):
                print(f"[OK] Telegram webhook set to {webhook_url}/telegram/webhook")
            else:
                print(f"[!] Failed to set Telegram webhook: {result}")
    except Exception as e:
        print(f"[!] Error setting Telegram webhook: {e}")
    
    return runner


# ============= MAIN =============

async def main_async():
    """Async main function"""
    # Initialize ticket API database
    ticket_api.init_db()
    
    # Create bot
    bot = VerificationBot()
    
    # Start HTTP server
    http_runner = await start_http_server(bot)
    
    try:
        # Start bot
        await bot.start(config.DISCORD_TOKEN)
    finally:
        # Cleanup
        await http_runner.cleanup()
        await bot.close()

def main():
    """Start the bot"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
