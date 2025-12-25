"""
Telegram Bot for VIP Ticket Management
Allows admin to respond to VIP tickets via Telegram
Uses MongoDB for ticket storage
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Import ticket API for MongoDB operations
import ticket_api

# Configuration (required - set via environment variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SECRET_KEY = os.environ.get("TELEGRAM_SECRET_KEY", "change_this_secret_key")
AUTHORIZED_USERS_FILE = "telegram_authorized.json"
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://robloxcheatztg.vercel.app")

# Store for active chat sessions
# Format: {telegram_user_id: {"ticket_channel_id": int, "discord_user_id": int, "username": str}}
active_chats: Dict[int, dict] = {}

# Authorized Telegram users
authorized_users: set = set()

# Discord bot reference (will be set from main bot)
discord_bot = None

# Logo URL for Discord embeds
LOGO_URL = "https://raw.githubusercontent.com/TimPlay1/robloxcheatz/main/public/logo.jpg"


def load_authorized_users():
    """Load authorized users from MongoDB"""
    global authorized_users
    try:
        authorized_users = ticket_api.sync_get_authorized_users()
        print(f"[OK] Loaded {len(authorized_users)} authorized Telegram users from MongoDB")
    except Exception as e:
        print(f"[!] Error loading authorized users: {e}")
        authorized_users = set()


def save_authorized_user(user_id: int):
    """Save single authorized user to MongoDB"""
    try:
        ticket_api.sync_add_authorized_user(user_id)
        authorized_users.add(user_id)
    except Exception as e:
        print(f"[!] Error saving authorized user: {e}")


def remove_authorized_user(user_id: int):
    """Remove authorized user from MongoDB"""
    try:
        ticket_api.sync_remove_authorized_user(user_id)
        authorized_users.discard(user_id)
    except Exception as e:
        print(f"[!] Error removing authorized user: {e}")


def is_authorized(user_id: int) -> bool:
    """Check if user is authorized"""
    return user_id in authorized_users


def get_tickets_from_db() -> list:
    """Get all active tickets from MongoDB"""
    return ticket_api.sync_get_all_active_tickets()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    if is_authorized(user_id):
        # Show main menu
        keyboard = [
            [InlineKeyboardButton("📋 Active Tickets", callback_data="list_tickets")],
            [InlineKeyboardButton("🌐 Open Web Panel", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("🔓 Logout", callback_data="logout")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎮 *ROBLOXCHEATZ VIP SUPPORT PANEL*\n"
            "════════════════════════════════\n\n"
            "Welcome back! You're authorized.\n\n"
            "Use the buttons below or reply to ticket notifications.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🔐 *AUTHORIZATION REQUIRED*\n"
            "════════════════════════════\n\n"
            "Please enter the secret key to access the VIP Support Panel:\n\n"
            "Use: `/auth <secret_key>`",
            parse_mode="Markdown"
        )


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /auth command for authorization"""
    user_id = update.effective_user.id
    
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: `/auth <secret_key>`", parse_mode="Markdown")
        return
    
    key = context.args[0]
    
    if key == SECRET_KEY:
        save_authorized_user(user_id)
        
        keyboard = [
            [InlineKeyboardButton("📋 Active Tickets", callback_data="list_tickets")],
            [InlineKeyboardButton("🔓 Logout", callback_data="logout")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ *AUTHORIZATION SUCCESSFUL*\n"
            "════════════════════════════\n\n"
            "You now have access to the VIP Support Panel.\n"
            "You'll receive notifications for new VIP tickets.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Invalid secret key. Access denied.")


async def list_tickets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of active tickets from MongoDB"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.edit_message_text("❌ Not authorized. Use /auth to login.")
        return
    
    # Get tickets from MongoDB
    tickets = get_tickets_from_db()
    
    if not tickets:
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📭 *NO ACTIVE VIP TICKETS*\n"
            "════════════════════════════\n\n"
            "You'll be notified when a new VIP ticket is created.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return
    
    # Build ticket list
    text = "📋 *ACTIVE VIP TICKETS*\n"
    text += "════════════════════════════\n\n"
    keyboard = []
    
    for ticket in tickets:
        channel_id = ticket.get("channel_id")
        discord_user = ticket.get("discord_username", "Unknown")
        email = ticket.get("email", "N/A")
        total_spent = ticket.get("total_spent", 0)
        created = ticket.get("created_at", "")
        if isinstance(created, datetime):
            created = created.strftime("%Y-%m-%d %H:%M")
        
        text += f"👤 *{discord_user}*\n"
        text += f"   📧 {email}\n"
        text += f"   💰 ${total_spent:.2f}\n"
        text += f"   🕐 {created}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"💬 Chat with {discord_user}", callback_data=f"chat_{channel_id}"),
            InlineKeyboardButton("🗑️", callback_data=f"delete_{channel_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start chat with a specific ticket"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.edit_message_text("❌ Not authorized.")
        return
    
    # Extract channel ID from callback data
    channel_id = int(query.data.split("_")[1])
    
    # Get ticket from MongoDB
    tickets = get_tickets_from_db()
    ticket = None
    for t in tickets:
        if t.get("channel_id") == channel_id:
            ticket = t
            break
    
    if not ticket:
        await query.edit_message_text("❌ Ticket not found or closed.")
        return
    
    # Set active chat
    active_chats[user_id] = {
        "ticket_channel_id": channel_id,
        "discord_user_id": ticket.get("discord_user_id"),
        "username": ticket.get("discord_username")
    }
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Ticket", callback_data=f"delete_{channel_id}")],
        [InlineKeyboardButton("❌ Exit Chat", callback_data="exit_chat")],
        [InlineKeyboardButton("🔙 Back to Tickets", callback_data="list_tickets")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💬 *CHAT MODE ACTIVE*\n"
        f"════════════════════════════\n\n"
        f"👤 Chatting with: *{ticket.get('discord_username')}*\n"
        f"📧 Email: {ticket.get('email', 'N/A')}\n"
        f"💰 Total Spent: ${ticket.get('total_spent', 0):.2f}\n\n"
        f"📝 Type your message and it will be sent to the Discord ticket.\n"
        f"You'll see their replies here.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Load message history from Discord channel
    if discord_bot:
        try:
            channel = discord_bot.get_channel(channel_id)
            if channel:
                # Get last 20 messages
                messages_list = []
                async for msg in channel.history(limit=20, oldest_first=True):
                    # Skip the first welcome message from bot
                    if msg.author.bot and msg.embeds and "Ticket Created" in str(msg.embeds[0].title if msg.embeds[0].title else ""):
                        continue
                    
                    if msg.author.bot:
                        # Admin message via Telegram
                        if msg.embeds:
                            for embed in msg.embeds:
                                if embed.description:
                                    messages_list.append(f"👑 *VIP Support:*\n{embed.description}")
                    else:
                        # User message
                        if msg.content:
                            messages_list.append(f"👤 *{msg.author.display_name}:*\n{msg.content}")
                
                if messages_list:
                    history_text = "📜 *MESSAGE HISTORY:*\n────────────────────\n\n"
                    history_text += "\n\n".join(messages_list[-10:])  # Last 10 messages
                    
                    await telegram_app.bot.send_message(
                        chat_id=user_id,
                        text=history_text,
                        parse_mode="Markdown"
                    )
        except Exception as e:
            print(f"[!] Error loading message history: {e}")


async def delete_ticket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a ticket"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.edit_message_text("❌ Not authorized.")
        return
    
    # Extract channel ID from callback data
    channel_id = int(query.data.split("_")[1])
    
    # Find ticket info before deleting
    tickets = get_tickets_from_db()
    ticket_info = None
    for t in tickets:
        if t.get("channel_id") == channel_id:
            ticket_info = t
            break
    
    if not ticket_info:
        await query.edit_message_text("❌ Ticket not found or already deleted.")
        return
    
    # Delete from MongoDB
    result = ticket_api.sync_delete_ticket(channel_id)
    
    # Delete Discord channel
    if discord_bot:
        try:
            channel = discord_bot.get_channel(channel_id)
            if channel:
                await channel.delete(reason="Ticket deleted via Telegram")
        except Exception as e:
            print(f"[!] Error deleting Discord channel: {e}")
    
    # Remove from active chats
    for uid, chat_info in list(active_chats.items()):
        if chat_info.get("ticket_channel_id") == channel_id:
            del active_chats[uid]
    
    keyboard = [
        [InlineKeyboardButton("📋 Active Tickets", callback_data="list_tickets")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🗑️ *TICKET DELETED*\n"
        f"════════════════════════════\n\n"
        f"Ticket for *{ticket_info.get('discord_username')}* has been deleted.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def exit_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exit current chat"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id in active_chats:
        del active_chats[user_id]
    
    keyboard = [
        [InlineKeyboardButton("📋 Active Tickets", callback_data="list_tickets")],
        [InlineKeyboardButton("🔓 Logout", callback_data="logout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ Exited chat mode.\n\nSelect an option:",
        reply_markup=reply_markup
    )


async def logout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logout user"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id in authorized_users:
        remove_authorized_user(user_id)
    
    if user_id in active_chats:
        del active_chats[user_id]
    
    await query.edit_message_text(
        "🔒 You have been logged out.\n\nUse /auth to login again."
    )


async def back_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id in active_chats:
        del active_chats[user_id]
    
    keyboard = [
        [InlineKeyboardButton("📋 Active Tickets", callback_data="list_tickets")],
        [InlineKeyboardButton("🔓 Logout", callback_data="logout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎮 *ROBLOXCHEATZ VIP SUPPORT PANEL*\n"
        "════════════════════════════════\n\n"
        "Select an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages - forward to Discord if in chat mode"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Not authorized. Use /auth to login.")
        return
    
    if user_id not in active_chats:
        await update.message.reply_text(
            "💡 You're not in chat mode.\n\n"
            "Use /start and select a ticket to chat with."
        )
        return
    
    chat_info = active_chats[user_id]
    channel_id = chat_info["ticket_channel_id"]
    message_text = update.message.text
    
    # Forward to Discord
    if discord_bot:
        try:
            channel = discord_bot.get_channel(channel_id)
            if channel:
                # Send as support message
                import discord
                embed = discord.Embed(
                    description=message_text,
                    color=0xFFD700  # Gold for admin
                )
                embed.set_author(name="👑 VIP Support", icon_url=LOGO_URL)
                embed.set_footer(text="Response via Telegram")
                
                await channel.send(embed=embed)
                await update.message.reply_text("✅ Message sent!")
            else:
                await update.message.reply_text("❌ Ticket channel not found. It may have been closed.")
                # Remove from active chats
                del active_chats[user_id]
        except Exception as e:
            await update.message.reply_text(f"❌ Error sending message: {e}")
    else:
        await update.message.reply_text("❌ Discord bot not connected.")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    data = query.data
    
    if data == "list_tickets":
        await list_tickets_callback(update, context)
    elif data.startswith("chat_"):
        await chat_callback(update, context)
    elif data.startswith("delete_"):
        await delete_ticket_callback(update, context)
    elif data == "exit_chat":
        await exit_chat_callback(update, context)
    elif data == "logout":
        await logout_callback(update, context)
    elif data == "back_main":
        await back_main_callback(update, context)
    else:
        await query.answer("Unknown action")


# ============= Functions called from Discord bot =============

async def notify_new_vip_ticket(
    channel_id: int,
    discord_user_id: int,
    discord_username: str,
    email: str,
    total_spent: float,
    purchase_count: int,
    level: int
):
    """Send notification to Telegram about new VIP ticket"""
    global telegram_app
    
    # Check if Telegram is enabled
    if not is_telegram_enabled():
        print(f"[!] Telegram not enabled - skipping VIP ticket notification for {discord_username}")
        return
    
    if not authorized_users:
        print("[!] No authorized Telegram users to notify")
        return
    
    # Build notification message
    text = (
        "🎫 *NEW VIP TICKET!*\n"
        "════════════════════════════\n\n"
        f"👤 *User:* {discord_username}\n"
        f"📧 *Email:* {email}\n"
        f"💰 *Total Spent:* ${total_spent:.2f}\n"
        f"🛒 *Purchases:* {purchase_count}\n"
        f"⭐ *Level:* {level}\n"
        f"🕐 *Time:* {datetime.now().strftime('%H:%M')}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"💬 Reply to {discord_username}", callback_data=f"chat_{channel_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send to all authorized users
    print(f"[TELEGRAM] Sending VIP ticket notification to {len(authorized_users)} users...")
    for user_id in authorized_users:
        try:
            await telegram_app.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            print(f"[TELEGRAM] Notification sent to user {user_id}")
        except Exception as e:
            print(f"[!] Error sending Telegram notification to {user_id}: {e}")


async def notify_ticket_message(channel_id: int, username: str, message: str):
    """Forward ticket message to Telegram"""
    global telegram_app
    
    # Check if Telegram is enabled
    if not is_telegram_enabled():
        return
    
    # Find users who are chatting with this ticket
    for user_id, chat_info in active_chats.items():
        if chat_info.get("ticket_channel_id") == channel_id:
            try:
                await telegram_app.bot.send_message(
                    chat_id=user_id,
                    text=f"👤 *{username}:*\n{message}",
                    parse_mode="Markdown"
                )
                print(f"[TELEGRAM] Message forwarded to {user_id}")
            except Exception as e:
                print(f"[!] Error forwarding message to Telegram: {e}")


async def notify_ticket_closed(channel_id: int):
    """Notify that ticket was closed"""
    global telegram_app
    
    # Check if Telegram is enabled
    if not is_telegram_enabled():
        return
    
    # Get ticket info from DB
    tickets = get_tickets_from_db()
    ticket_info = None
    for t in tickets:
        if t.get("channel_id") == channel_id:
            ticket_info = t
            break
    
    if ticket_info:
        # Notify users in chat
        for user_id, chat_info in list(active_chats.items()):
            if chat_info.get("ticket_channel_id") == channel_id:
                try:
                    await telegram_app.bot.send_message(
                        chat_id=user_id,
                        text=f"🔒 Ticket with *{ticket_info.get('discord_username')}* has been closed.",
                        parse_mode="Markdown"
                    )
                    print(f"[TELEGRAM] Ticket closed notification sent to {user_id}")
                except Exception as e:
                    print(f"[!] Error notifying ticket closure: {e}")
                del active_chats[user_id]


# ============= Telegram App Instance =============
telegram_app: Optional[Application] = None
telegram_polling_task = None  # For local polling mode


def is_telegram_enabled() -> bool:
    """Check if Telegram bot is properly configured"""
    return bool(TELEGRAM_TOKEN and telegram_app)


def is_local_mode() -> bool:
    """Check if running in local mode (not on Render/Vercel)"""
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    return "localhost" in webhook_url or not webhook_url or "onrender.com" not in webhook_url


async def telegram_polling_loop():
    """Run Telegram polling in background"""
    global telegram_app
    print("[OK] Starting Telegram polling loop...")
    try:
        # Delete any existing webhook first
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        print("[OK] Webhook deleted, starting polling...")
        
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        print("[OK] Telegram polling started!")
        # Keep running
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("[!] Telegram polling cancelled")
    except Exception as e:
        print(f"[!] Telegram polling error: {e}")


async def start_telegram_bot(discord_bot_instance):
    """Start the Telegram bot (webhook or polling mode)"""
    global telegram_app, discord_bot, telegram_polling_task
    
    discord_bot = discord_bot_instance
    
    # Check if token is configured
    if not TELEGRAM_TOKEN:
        print("[!] TELEGRAM_TOKEN not set - Telegram bot disabled")
        return
    
    try:
        load_authorized_users()
        
        # Create application
        telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("auth", auth_command))
        telegram_app.add_handler(CallbackQueryHandler(callback_handler))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Initialize
        await telegram_app.initialize()
        
        if is_local_mode():
            # Local mode - use polling
            print("[OK] Telegram bot starting in POLLING mode (local)...")
            await telegram_app.start()
            # Start polling in background
            telegram_polling_task = asyncio.create_task(telegram_polling_loop())
            print("[OK] Telegram bot polling active!")
        else:
            # Production mode - use webhooks
            print("[OK] Telegram bot initializing (webhook mode)...")
            await telegram_app.start()
            print("[OK] Telegram bot ready for webhooks!")
        
        print(f"[OK] Authorized users: {len(authorized_users)}")
    except Exception as e:
        import traceback
        print(f"[!] Failed to start Telegram bot: {e}")
        traceback.print_exc()
        telegram_app = None


async def process_telegram_update(update_data: dict):
    """Process incoming Telegram update from webhook"""
    global telegram_app
    if telegram_app:
        from telegram import Update
        update = Update.de_json(update_data, telegram_app.bot)
        await telegram_app.process_update(update)


async def stop_telegram_bot():
    """Stop the Telegram bot"""
    global telegram_app, telegram_polling_task
    
    if telegram_polling_task:
        telegram_polling_task.cancel()
        try:
            await telegram_polling_task
        except asyncio.CancelledError:
            pass
        telegram_polling_task = None
    
    if telegram_app:
        if telegram_app.updater and telegram_app.updater.running:
            await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
        print("[OK] Telegram bot stopped")
