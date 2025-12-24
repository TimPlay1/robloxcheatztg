"""
Модуль для работы с Komerza API
Получение данных о заказах и клиентах
https://docs.komerza.com/api-reference/introduction
"""

import aiohttp
import asyncio
import json
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import config

# Путь к файлу кэша
CACHE_FILE = "customers_cache.json"


class KomerzaAPI:
    """Клиент для работы с Komerza API"""
    
    def __init__(self):
        self.base_url = config.KOMERZA_API_BASE
        self.token = config.KOMERZA_API_TOKEN
        self.store_id = config.STORE_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "IlyaDiscordBot/1.0"
        }
        self._cache = {}
        self._cache_timestamps = {}
        
        # Кэш всех клиентов по email (загружается при старте)
        self._all_customers = {}  # email -> customer data
        self._customers_loaded = False
        self._last_customers_load = None
    
    def _save_cache_to_file(self):
        """Сохранить кэш клиентов в файл"""
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "count": len(self._all_customers),
                "customers": self._all_customers
            }
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            print(f"💾 Кэш сохранён в файл ({len(self._all_customers)} клиентов)")
        except Exception as e:
            print(f"[!] Ошибка сохранения кэша: {e}")
    
    def _load_cache_from_file(self) -> bool:
        """Загрузить кэш клиентов из файла"""
        try:
            if not os.path.exists(CACHE_FILE):
                return False
            
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            self._all_customers = cache_data.get("customers", {})
            saved_time = cache_data.get("timestamp", "")
            count = cache_data.get("count", 0)
            
            if self._all_customers:
                self._customers_loaded = True
                print(f"📂 Загружено {count} клиентов из кэша (сохранён: {saved_time[:19]})")
                return True
            return False
        except Exception as e:
            print(f"[!] Ошибка загрузки кэша: {e}")
            return False
    
    async def _make_request(self, method: str, endpoint: str, params: dict = None) -> Optional[Dict]:
        """Выполнить запрос к API"""
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, 
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if response.status == 200:
                        if 'json' in content_type or 'text/plain' in content_type:
                            try:
                                data = await response.json()
                                if data.get("success") == True:
                                    return data
                                else:
                                    return None
                            except:
                                return None
                        else:
                            return None
                    elif response.status == 429:
                        await asyncio.sleep(2)
                        return None
                    else:
                        return None
            except asyncio.TimeoutError:
                return None
            except aiohttp.ClientError:
                return None
    
    async def load_all_customers(self):
        """Загрузить всех клиентов - сначала из файла, потом синхронизация"""
        
        # Шаг 1: Попробовать загрузить из файла кэша
        if self._load_cache_from_file():
            # Файл загружен - теперь быстро синхронизируем новых клиентов
            print("🔄 Синхронизация новых клиентов...")
            await self._sync_new_customers()
            return len(self._all_customers)
        
        # Шаг 2: Файла нет - полная загрузка из API
        print("📥 Первая загрузка клиентов в кэш...")
        self._all_customers = {}
        page = 1
        total_loaded = 0
        
        while True:
            result = await self.get_customers_raw(page=page, page_size=100)
            
            if not result or not result.get("data"):
                break
            
            customers = result["data"]
            for customer in customers:
                email = customer.get("emailAddress", "").lower()
                if email:
                    self._all_customers[email] = customer
                    total_loaded += 1
            
            total_pages = result.get("pages", 1)
            print(f"   Страница {page}/{total_pages} ({total_loaded} клиентов)", end="\r")
            
            if page >= total_pages:
                break
            
            page += 1
            await asyncio.sleep(0.02)  # Минимальная задержка
        
        self._customers_loaded = True
        self._last_customers_load = datetime.now()
        print(f"\n✅ Загружено {total_loaded} клиентов в кэш")
        
        # Сохраняем кэш в файл для быстрого старта
        self._save_cache_to_file()
        
        return total_loaded
    
    async def _sync_new_customers(self):
        """Быстрая синхронизация только новых/изменённых клиентов"""
        page = 1
        new_count = 0
        updated_count = 0
        
        # Проверяем первые страницы (где новые клиенты)
        while page <= 30:
            result = await self.get_customers_raw(page=page, page_size=100)
            
            if not result or not result.get("data"):
                break
            
            customers = result["data"]
            page_new = 0
            
            for customer in customers:
                email = customer.get("emailAddress", "").lower()
                if not email:
                    continue
                    
                if email not in self._all_customers:
                    self._all_customers[email] = customer
                    new_count += 1
                    page_new += 1
                else:
                    # Обновляем данные (totalSpend мог измениться)
                    old_spend = self._all_customers[email].get("totalSpend", 0)
                    new_spend = customer.get("totalSpend", 0)
                    if new_spend != old_spend:
                        self._all_customers[email] = customer
                        updated_count += 1
            
            total_pages = result.get("pages", 1)
            
            # Если на странице нет новых - выходим (новые всегда в начале)
            if page > 5 and page_new == 0:
                break
            
            if page >= total_pages:
                break
            
            page += 1
            await asyncio.sleep(0.02)
        
        if new_count > 0 or updated_count > 0:
            print(f"✅ Синхронизировано: +{new_count} новых, ~{updated_count} обновлено")
            self._save_cache_to_file()
        else:
            print("✅ Кэш актуален")
        
        self._last_customers_load = datetime.now()
    
    async def get_customers_raw(self, page: int = 1, page_size: int = 100) -> Optional[Dict]:
        """Получить страницу клиентов напрямую из API (без кэша)"""
        params = {"Page": page, "PageSize": page_size}
        endpoint = f"stores/{self.store_id}/customers"
        return await self._make_request("GET", endpoint, params)
    
    async def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """Получить клиента по email из предзагруженного кэша"""
        email_lower = email.lower()
        
        # Если кэш загружен - ищем в нём (мгновенно)
        if self._customers_loaded and email_lower in self._all_customers:
            return self._all_customers[email_lower]
        
        # Если кэш не загружен - загружаем
        if not self._customers_loaded:
            await self.load_all_customers()
            if email_lower in self._all_customers:
                return self._all_customers[email_lower]
        
        return None
    
    async def refresh_customers_cache(self):
        """Обновить кэш клиентов (загрузить новых)"""
        if not self._customers_loaded:
            await self.load_all_customers()
            return
        
        print("🔄 Обновление кэша клиентов...")
        await self._sync_new_customers()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            # Cache TTL: 5 minutes
            if datetime.now().timestamp() - timestamp < 300:
                return self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Сохранить данные в кэш"""
        self._cache[key] = data
        self._cache_timestamps[key] = datetime.now().timestamp()
    
    async def get_customers(self, page: int = 1, page_size: int = 100, email: str = None) -> Optional[Dict]:
        """Получить список клиентов"""
        cache_key = f"customers_{page}_{page_size}_{email}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        params = {"Page": page, "PageSize": page_size}
        if email:
            params["email"] = email
        
        endpoint = f"stores/{self.store_id}/customers"
        result = await self._make_request("GET", endpoint, params)
        
        if result:
            self._set_cache(cache_key, result)
        return result
    
    async def get_orders(self, page: int = 1, page_size: int = 100) -> Optional[Dict]:
        """Получить список заказов"""
        cache_key = f"orders_{page}_{page_size}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        params = {"Page": page, "PageSize": page_size}
        endpoint = f"stores/{self.store_id}/orders"
        result = await self._make_request("GET", endpoint, params)
        
        if result:
            self._set_cache(cache_key, result)
        return result
    
    async def get_orders_by_email(self, email: str) -> List[Dict]:
        """Получить заказы по email клиента (с использованием Search API)"""
        email_lower = email.lower().strip()
        cache_key = f"orders_email_{email_lower}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        user_orders = []
        page = 1
        max_pages = 10  # Ограничиваем количество страниц
        
        while page <= max_pages:
            # Используем SEARCH endpoint с email в пути!
            params = {
                "Page": page, 
                "PageSize": 100
            }
            # Search endpoint: /stores/{storeId}/orders/search/{query}
            endpoint = f"stores/{self.store_id}/orders/search/{email_lower}"
            result = await self._make_request("GET", endpoint, params)
            
            if not result or not result.get("data"):
                break
            
            orders = result["data"]
            for order in orders:
                # Дополнительно проверяем email (на всякий случай)
                order_email = order.get("customerEmail", "").lower().strip()
                if order_email != email_lower:
                    continue
                    
                status = order.get("status", "").lower()
                # Принимаем оплаченные заказы
                if status in ["completed", "delivered", "paid", "success", "fulfilled"]:
                    user_orders.append(order)
            
            total_pages = result.get("pages", 1)
            if page >= total_pages:
                break
            
            page += 1
            await asyncio.sleep(0.1)
        
        self._set_cache(cache_key, user_orders)
        return user_orders
    
    async def get_customer_total_spent(self, email: str) -> float:
        """Get customer total spent"""
        customer = await self.get_customer_by_email(email)
        if customer:
            total = customer.get("totalSpend", 0)
            if total and total > 0:
                return float(total)
        return 0.0
    
    async def get_customer_purchase_count(self, email: str) -> int:
        """Get customer's purchase count"""
        customer = await self.get_customer_by_email(email)
        if customer:
            count = customer.get("orderCount", customer.get("totalOrders", 0))
            if count and count > 0:
                return int(count)
        # Fallback: count from orders
        orders = await self.get_orders_by_email(email)
        return len(orders)
    
    async def get_customer_products(self, email: str) -> List[Dict]:
        """Получить список купленных продуктов клиента"""
        orders = await self.get_orders_by_email(email)
        products = []
        
        for order in orders:
            items = order.get("items", [])
            for item in items:
                products.append({
                    "name": item.get("productName", ""),
                    "variant": item.get("variantName", ""),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("lineTotal", item.get("amount", 0)),
                    "product_id": item.get("productId", ""),
                })
        
        return products
    
    async def verify_email_exists(self, email: str) -> bool:
        """Проверить существует ли email в базе покупателей"""
        customer = await self.get_customer_by_email(email)
        return customer is not None
    
    def get_stats(self) -> dict:
        """Получить статистику кэша"""
        return {
            "customers_loaded": self._customers_loaded,
            "total_customers": len(self._all_customers),
            "last_load": self._last_customers_load
        }
    
    def clear_cache(self):
        """Очистить кэш"""
        self._cache.clear()
        self._cache_timestamps.clear()


# Глобальный экземпляр API клиента
api = KomerzaAPI()
