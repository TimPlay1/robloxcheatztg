"""
Скрипт для создания каналов и категорий на сервере
Запустите один раз для настройки структуры сервера
"""

import discord
from discord.ext import commands
import asyncio
import config


class SetupBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
    
    async def on_ready(self):
        print(f"🤖 Бот запущен как {self.user}")
        
        guild = self.get_guild(config.GUILD_ID)
        if not guild:
            print(f"❌ Сервер с ID {config.GUILD_ID} не найден!")
            await self.close()
            return
        
        print(f"📍 Сервер: {guild.name}")
        print("=" * 50)
        
        await self.setup_server(guild)
        
        print("=" * 50)
        print("✅ Настройка завершена!")
        print("\n📝 Не забудьте:")
        print("1. Скопировать ID каналов в config.py")
        print("2. Настроить позиции ролей в настройках сервера")
        print("3. Запустить основного бота: python bot.py")
        
        await self.close()
    
    async def setup_server(self, guild: discord.Guild):
        """Создать структуру сервера"""
        
        # === СОЗДАНИЕ РОЛЕЙ ===
        print("\n🎨 Создание ролей...")
        
        roles_created = []
        
        # Роли по уровням покупок
        for amount, (name, color, emoji) in config.PURCHASE_ROLES.items():
            role = discord.utils.get(guild.roles, name=name)
            if not role:
                role = await guild.create_role(
                    name=name,
                    color=discord.Color(color),
                    hoist=True,
                    mentionable=True
                )
                print(f"  ✅ Создана роль: {name}")
                roles_created.append(role)
            else:
                print(f"  ⏭️ Роль уже существует: {name}")
        
        # Специальные роли
        for key, (name, color, min_amount) in config.SPECIAL_ROLES.items():
            role = discord.utils.get(guild.roles, name=name)
            if not role:
                role = await guild.create_role(
                    name=name,
                    color=discord.Color(color),
                    hoist=True,
                    mentionable=True
                )
                print(f"  ✅ Создана роль: {name}")
                roles_created.append(role)
            else:
                print(f"  ⏭️ Роль уже существует: {name}")
        
        # Роли по продуктам
        for key, (name, color) in config.PRODUCT_ROLES.items():
            role = discord.utils.get(guild.roles, name=name)
            if not role:
                role = await guild.create_role(
                    name=name,
                    color=discord.Color(color),
                    hoist=True,
                    mentionable=True
                )
                print(f"  ✅ Создана роль: {name}")
                roles_created.append(role)
            else:
                print(f"  ⏭️ Роль уже существует: {name}")
        
        await asyncio.sleep(1)
        
        # === СОЗДАНИЕ КАТЕГОРИЙ ===
        print("\n📁 Создание категорий...")
        
        # Категория для покупателей
        buyers_category = discord.utils.get(guild.categories, name="🛒 Buyers Only")
        if not buyers_category:
            buyers_category = await guild.create_category(
                name="🛒 Buyers Only",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                }
            )
            print(f"  ✅ Создана категория: 🛒 Buyers Only (ID: {buyers_category.id})")
        else:
            print(f"  ⏭️ Категория уже существует: 🛒 Buyers Only (ID: {buyers_category.id})")
        
        # Категория для VIP
        vip_category = discord.utils.get(guild.categories, name="⭐ VIP Zone")
        if not vip_category:
            vip_category = await guild.create_category(
                name="⭐ VIP Zone",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                }
            )
            print(f"  ✅ Создана категория: ⭐ VIP Zone (ID: {vip_category.id})")
        else:
            print(f"  ⏭️ Категория уже существует: ⭐ VIP Zone (ID: {vip_category.id})")
        
        await asyncio.sleep(1)
        
        # === СОЗДАНИЕ КАНАЛОВ ===
        print("\n💬 Создание каналов...")
        
        # Получаем роли
        verified_role = discord.utils.get(guild.roles, name=config.SPECIAL_ROLES["verified_buyer"][0])
        priority_role = discord.utils.get(guild.roles, name=config.SPECIAL_ROLES["priority_support"][0])
        
        channels_info = {}
        
        # Канал верификации (публичный)
        verify_channel = discord.utils.get(guild.text_channels, name="🔐-verify")
        if not verify_channel:
            verify_channel = await guild.create_text_channel(
                name="🔐-verify",
                topic="Введите /verify email@example.com для верификации вашего аккаунта покупателя"
            )
            print(f"  ✅ Создан канал: 🔐-verify (ID: {verify_channel.id})")
        else:
            print(f"  ⏭️ Канал уже существует: 🔐-verify (ID: {verify_channel.id})")
        channels_info["verification"] = verify_channel.id
        
        # Канал логов (для админов)
        logs_channel = discord.utils.get(guild.text_channels, name="📋-verification-logs")
        if not logs_channel:
            logs_channel = await guild.create_text_channel(
                name="📋-verification-logs",
                topic="Логи верификаций",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                }
            )
            print(f"  ✅ Создан канал: 📋-verification-logs (ID: {logs_channel.id})")
        else:
            print(f"  ⏭️ Канал уже существует: 📋-verification-logs (ID: {logs_channel.id})")
        channels_info["logs"] = logs_channel.id
        
        # Приватные анонсы (только для покупателей)
        announcements = discord.utils.get(guild.text_channels, name="📢-private-announcements")
        if not announcements:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            if verified_role:
                overwrites[verified_role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
            
            announcements = await guild.create_text_channel(
                name="📢-private-announcements",
                topic="Приватные анонсы для покупателей",
                category=buyers_category,
                overwrites=overwrites
            )
            print(f"  ✅ Создан канал: 📢-private-announcements (ID: {announcements.id})")
        else:
            print(f"  ⏭️ Канал уже существует: 📢-private-announcements (ID: {announcements.id})")
        channels_info["private_announcements"] = announcements.id
        
        # Чат покупателей $10+
        chat_10 = discord.utils.get(guild.text_channels, name="💬-buyers-chat")
        if not chat_10:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            if verified_role:
                overwrites[verified_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            chat_10 = await guild.create_text_channel(
                name="💬-buyers-chat",
                topic="Чат для всех покупателей ($10+)",
                category=buyers_category,
                overwrites=overwrites
            )
            print(f"  ✅ Создан канал: 💬-buyers-chat (ID: {chat_10.id})")
        else:
            print(f"  ⏭️ Канал уже существует: 💬-buyers-chat (ID: {chat_10.id})")
        channels_info["buyers_chat_10"] = chat_10.id
        
        # Чат $50+
        role_50 = discord.utils.get(guild.roles, name=config.PURCHASE_ROLES[50][0])
        chat_50 = discord.utils.get(guild.text_channels, name="⭐-50-chat")
        if not chat_50:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            # Даем доступ всем ролям $50+
            for amount, (name, color, emoji) in config.PURCHASE_ROLES.items():
                if amount >= 50:
                    role = discord.utils.get(guild.roles, name=name)
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            chat_50 = await guild.create_text_channel(
                name="⭐-50-chat",
                topic="Эксклюзивный чат для покупателей $50+",
                category=buyers_category,
                overwrites=overwrites
            )
            print(f"  ✅ Создан канал: ⭐-50-chat (ID: {chat_50.id})")
        else:
            print(f"  ⏭️ Канал уже существует: ⭐-50-chat (ID: {chat_50.id})")
        channels_info["buyers_chat_50"] = chat_50.id
        
        # VIP чат $70+
        chat_70 = discord.utils.get(guild.text_channels, name="✨-vip-chat")
        if not chat_70:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            if priority_role:
                overwrites[priority_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            chat_70 = await guild.create_text_channel(
                name="✨-vip-chat",
                topic="VIP чат для покупателей $70+",
                category=vip_category,
                overwrites=overwrites
            )
            print(f"  ✅ Создан канал: ✨-vip-chat (ID: {chat_70.id})")
        else:
            print(f"  ⏭️ Канал уже существует: ✨-vip-chat (ID: {chat_70.id})")
        channels_info["buyers_chat_70"] = chat_70.id
        
        # Приоритетная поддержка
        priority_channel = discord.utils.get(guild.text_channels, name="🎯-priority-support")
        if not priority_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            if priority_role:
                overwrites[priority_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            priority_channel = await guild.create_text_channel(
                name="🎯-priority-support",
                topic="Приоритетная поддержка для VIP покупателей ($70+)",
                category=vip_category,
                overwrites=overwrites
            )
            print(f"  ✅ Создан канал: 🎯-priority-support (ID: {priority_channel.id})")
        else:
            print(f"  ⏭️ Канал уже существует: 🎯-priority-support (ID: {priority_channel.id})")
        channels_info["priority_support"] = priority_channel.id
        
        # Legend чат $100
        role_100 = discord.utils.get(guild.roles, name=config.PURCHASE_ROLES[100][0])
        chat_100 = discord.utils.get(guild.text_channels, name="👑-legend-chat")
        if not chat_100:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
            }
            if role_100:
                overwrites[role_100] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            chat_100 = await guild.create_text_channel(
                name="👑-legend-chat",
                topic="Легендарный чат для топ покупателей ($100+)",
                category=vip_category,
                overwrites=overwrites
            )
            print(f"  ✅ Создан канал: 👑-legend-chat (ID: {chat_100.id})")
        else:
            print(f"  ⏭️ Канал уже существует: 👑-legend-chat (ID: {chat_100.id})")
        channels_info["buyers_chat_100"] = chat_100.id
        
        # === ВЫВОД КОНФИГУРАЦИИ ===
        print("\n" + "=" * 50)
        print("📋 СКОПИРУЙТЕ ЭТО В config.py:")
        print("=" * 50)
        print("\nCHANNELS = {")
        for key, channel_id in channels_info.items():
            print(f'    "{key}": {channel_id},')
        print("}")
        print("\nCATEGORIES = {")
        print(f'    "buyers_only": {buyers_category.id},')
        print(f'    "vip_only": {vip_category.id},')
        print("}")


def main():
    print("=" * 50)
    print("🛠️ SETUP BOT - Настройка сервера")
    print("=" * 50)
    print(f"\nИспользуется сервер ID: {config.GUILD_ID}")
    print("Убедитесь, что ID сервера в config.py корректный!")
    print()
    
    bot = SetupBot()
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
