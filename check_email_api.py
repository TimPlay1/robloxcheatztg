"""
Check what API returns for a specific email
"""
import asyncio
import aiohttp
import config

async def check_email(email: str):
    base_url = config.KOMERZA_API_BASE
    token = config.KOMERZA_API_TOKEN
    store_id = config.STORE_ID
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print(f"Checking email: {email}")
    print(f"API Base: {base_url}")
    print(f"Store ID: {store_id}")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Use SEARCH endpoint: /stores/{storeId}/orders/search/{query}
        url = f"{base_url}/stores/{store_id}/orders/search/{email}"
        params = {"Page": 1, "PageSize": 100}
        
        print(f"Fetching orders from: {url}")
        print(f"Params: {params}")
        
        async with session.get(url, headers=headers, params=params) as resp:
            print(f"Status: {resp.status}")
            
            if resp.status == 200:
                data = await resp.json()
                orders = data.get("data", [])
                pages = data.get("pages", 1)
                
                print(f"\nPages: {pages}")
                print(f"Orders on this page: {len(orders)}")
                
                # Filter by exact email match
                exact_orders = [o for o in orders if o.get("customerEmail", "").lower() == email.lower()]
                print(f"Orders with exact email match: {len(exact_orders)}")
                
                # Show first 5 orders
                print("\n" + "=" * 50)
                print("FIRST 5 ORDERS WITH MATCHING EMAIL:")
                print("=" * 50)
                
                for i, order in enumerate(exact_orders[:5]):
                    print(f"\n--- Order #{i+1} ---")
                    print(f"  ID: {order.get('id')}")
                    print(f"  Email: {order.get('customerEmail')}")
                    print(f"  Status: {order.get('status')}")
                    print(f"  Total: ${order.get('amount', 0)}")
                    print(f"  Created: {order.get('dateCreated')}")
                    
                    items = order.get("items", [])
                    print(f"  Items ({len(items)}):")
                    for item in items:
                        print(f"    - {item.get('productName')} (qty: {item.get('quantity')}, ${item.get('amount', 0)})")
                
                # Collect unique product names
                print("\n" + "=" * 50)
                print("ALL UNIQUE PRODUCT NAMES (for this email):")
                print("=" * 50)
                
                unique_products = set()
                for order in exact_orders:
                    for item in order.get("items", []):
                        unique_products.add(item.get("productName", "Unknown"))
                
                for name in sorted(unique_products):
                    print(f"  - {name}")
                
                # Filter paid orders
                paid_statuses = ["completed", "delivered", "paid", "success", "fulfilled"]
                paid_orders = [o for o in exact_orders if o.get("status", "").lower() in paid_statuses]
                print(f"\nPaid orders: {len(paid_orders)}")
                    
            else:
                text = await resp.text()
                print(f"Error: {text}")

if __name__ == "__main__":
    email = "fivdjgwjcujj@gmail.com"
    asyncio.run(check_email(email))
