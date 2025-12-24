"""
Role management module
Creates and manages roles based on purchase amounts and products
"""

import discord
from typing import List, Optional
import config


class RoleManager:
    """Manages purchase-based roles and product roles"""
    
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self._role_cache = {}
        self._product_role_cache = {}
    
    async def ensure_roles_exist(self):
        """Create all roles if they don't exist"""
        print("[...] Checking and creating roles...")
        
        # Create purchase level roles
        for amount, (name, color) in sorted(config.PURCHASE_ROLES.items()):
            role = discord.utils.get(self.guild.roles, name=name)
            if not role:
                try:
                    role = await self.guild.create_role(
                        name=name,
                        color=discord.Color(color),
                        hoist=True,
                        mentionable=False
                    )
                    print(f"  [+] Created role: {name}")
                except Exception as e:
                    print(f"  [!] Error creating role {name}: {e}")
            self._role_cache[amount] = role
        
        # Create special roles
        for role_key, (name, color, min_amount) in config.SPECIAL_ROLES.items():
            role = discord.utils.get(self.guild.roles, name=name)
            if not role:
                try:
                    role = await self.guild.create_role(
                        name=name,
                        color=discord.Color(color),
                        hoist=True,
                        mentionable=False
                    )
                    print(f"  [+] Created role: {name}")
                except Exception as e:
                    print(f"  [!] Error creating role {name}: {e}")
            self._role_cache[role_key] = role
        
        # Create product roles
        for product_id, (name, color) in config.PRODUCT_ROLES.items():
            role = discord.utils.get(self.guild.roles, name=name)
            if not role:
                try:
                    role = await self.guild.create_role(
                        name=name,
                        color=discord.Color(color),
                        hoist=False,  # Product roles don't need to be hoisted
                        mentionable=False
                    )
                    print(f"  [+] Created product role: {name}")
                except Exception as e:
                    print(f"  [!] Error creating product role {name}: {e}")
            self._product_role_cache[product_id] = role
        
        print("[OK] All roles checked/created")
    
    def get_role_for_amount(self, amount: float) -> Optional[discord.Role]:
        """Get the appropriate role for a purchase amount"""
        for threshold in sorted(config.PURCHASE_ROLES.keys(), reverse=True):
            if amount >= threshold:
                return self._role_cache.get(threshold)
        return None
    
    async def assign_purchase_roles(self, member: discord.Member, total_spent: float) -> List[discord.Role]:
        """Assign roles based on total spent amount"""
        assigned_roles = []
        
        # Remove all purchase roles first
        roles_to_remove = []
        for amount, (name, _) in config.PURCHASE_ROLES.items():
            role = discord.utils.get(self.guild.roles, name=name)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
            except Exception as e:
                print(f"[!] Error removing roles: {e}")
        
        # Assign the correct role based on total spent
        target_role = self.get_role_for_amount(total_spent)
        if target_role:
            try:
                await member.add_roles(target_role)
                assigned_roles.append(target_role)
            except Exception as e:
                print(f"[!] Error adding role: {e}")
        
        # Assign special roles
        verified_name = config.SPECIAL_ROLES["verified_buyer"][0]
        verified_role = discord.utils.get(self.guild.roles, name=verified_name)
        if verified_role and verified_role not in member.roles and total_spent >= 10:
            try:
                await member.add_roles(verified_role)
                assigned_roles.append(verified_role)
            except Exception as e:
                print(f"[!] Error adding verified role: {e}")
        
        # Priority support for $70+
        if total_spent >= 70:
            priority_name = config.SPECIAL_ROLES["priority_support"][0]
            priority_role = discord.utils.get(self.guild.roles, name=priority_name)
            if priority_role and priority_role not in member.roles:
                try:
                    await member.add_roles(priority_role)
                    assigned_roles.append(priority_role)
                except Exception as e:
                    print(f"[!] Error adding priority role: {e}")
        
        return assigned_roles
    
    async def assign_product_roles(self, member: discord.Member, email: str) -> List[discord.Role]:
        """Assign roles based on purchased products"""
        from komerza_api import api as komerza_api
        
        assigned_roles = []
        
        try:
            # Get customer's purchased products
            products = await komerza_api.get_customer_products(email)
            
            # Map product names to our product IDs
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
            
            # Find which products user has bought
            bought_products = set()
            for product in products:
                product_name = product.get("name", "").lower()
                for product_id, aliases in product_name_map.items():
                    for alias in aliases:
                        if alias in product_name:
                            bought_products.add(product_id)
                            break
            
            # Assign roles for bought products
            for product_id in bought_products:
                if product_id in self._product_role_cache:
                    role = self._product_role_cache[product_id]
                    if role and role not in member.roles:
                        try:
                            await member.add_roles(role)
                            assigned_roles.append(role)
                        except Exception as e:
                            print(f"[!] Error adding product role {product_id}: {e}")
                else:
                    # Try to find role by name if not in cache
                    role_info = config.PRODUCT_ROLES.get(product_id)
                    if role_info:
                        role = discord.utils.get(self.guild.roles, name=role_info[0])
                        if role and role not in member.roles:
                            try:
                                await member.add_roles(role)
                                assigned_roles.append(role)
                                self._product_role_cache[product_id] = role
                            except Exception as e:
                                print(f"[!] Error adding product role {product_id}: {e}")
        
        except Exception as e:
            print(f"[!] Error in assign_product_roles: {e}")
        
        return assigned_roles
    
    async def remove_all_buyer_roles(self, member: discord.Member):
        """Remove all buyer roles from a member (including product roles)"""
        roles_to_remove = []
        
        # Purchase roles
        for _, (name, _) in config.PURCHASE_ROLES.items():
            role = discord.utils.get(self.guild.roles, name=name)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        # Special roles
        for _, (name, _, _) in config.SPECIAL_ROLES.values():
            role = discord.utils.get(self.guild.roles, name=name)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        # Product roles
        for _, (name, _) in config.PRODUCT_ROLES.items():
            role = discord.utils.get(self.guild.roles, name=name)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
            except Exception as e:
                print(f"[!] Error removing roles: {e}")


async def setup_channels_permissions(guild: discord.Guild, role_manager: RoleManager):
    """Setup channel permissions for buyer roles"""
    print("[...] Setting up channel permissions...")
    
    verified_name = config.SPECIAL_ROLES["verified_buyer"][0]
    verified_role = discord.utils.get(guild.roles, name=verified_name)
    
    priority_name = config.SPECIAL_ROLES["priority_support"][0]
    priority_role = discord.utils.get(guild.roles, name=priority_name)
    
    print("[OK] Channel permissions configured")
