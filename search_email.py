import asyncio
import aiohttp

async def search_all():
    token = "eyJhbGciOiJFUzI1NiIsImtpZCI6Ijc3ZDFiNDBkLWE2NzYtNGI1MS1hNTg3LWZiZDE4OGI5YmZkZiIsInR5cCI6IkpXVCJ9.eyJuYmYiOiIxNzY2MjI4Mzg5IiwiaXNzIjoiS29tZXJ6YSIsImlhdCI6IjE3NjYyMjgzODkiLCJhdWQiOiJtZXJjaGFudCIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL25hbWUiOiJkMjUxZmFiZS0yODk4LTQ0ODctODU3YS00YzQzYTczNzU2M2MiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjQ4Y2E2MTg5LTljM2UtNDlkOS1hNzcxLWVlM2JiOTQ3MjA5OSIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6InJlZm92b2QwMDFAZ21haWwuY29tIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiRm91clBlcmNlbnRGZWVzIiwiYXBpX2tleV9pZCI6IjUxODhlN2M0LWEzMmUtNGFjMS04YThiLWUzMmQxNTcyNDM1NyIsImV4cCI6IjI1MzQwMjMwMDc5OSIsImtleV9mbGFncyI6ImFwaSIsInNjb3BlIjpbInN0b3Jlcy51cGRhdGUiLCJzdG9yZXMudmlldyIsInN0b3Jlcy5vcmRlcnMudmlldyIsInN0b3Jlcy5wcm9kdWN0cy52aWV3Iiwic3RvcmVzLmNhdGVnb3JpZXMudmlldyIsInN0b3Jlcy5jdXN0b21lcnMudmlldyJdfQ.iattzLUFHiVf9CasrQ2caF_bWQXtCqiRh1trghMFo0VdTtQNMYB_XXo0E1Jevc6PLY1jL9EvmLR7TOsk-JlhhQ"
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "Bot/1.0"}
    target = "fivdjgwjcujj"
    
    stores = [
        ("ROBLOXCHEATZ", "d1550f0a-b430-49a9-807a-21f33df2d603"),
        ("COOLDOWN", "accfd156-c305-4254-a666-da252fddd134"),
        ("banzai", "f81dc87d-0b92-4cba-af57-2c1bda7a685b"),
    ]
    
    async with aiohttp.ClientSession() as s:
        for store_name, store_id in stores:
            print(f"\n=== Searching in {store_name} ===")
            
            # Search customers - ALL pages
            total_pages = 9999
            for page in range(1, 100):
                if page > total_pages:
                    break
                url = f"https://api.komerza.com/stores/{store_id}/customers"
                params = {"Page": page, "PageSize": 100}
                async with s.get(url, headers=headers, params=params) as r:
                    if r.status != 200:
                        print(f"  Error {r.status} on page {page}")
                        break
                    data = await r.json()
                    if not data.get("data"):
                        break
                    total_pages = data.get("pages", 1)
                    for c in data["data"]:
                        email = c.get("emailAddress", "").lower()
                        if target in email:
                            print(f"FOUND CUSTOMER: {email} - spent ${c.get('totalSpend', 0)}")
                print(f"  Checked customers page {page}/{total_pages}", end="\r")
            print()
            
            # Search orders - ALL pages
            total_pages = 9999
            for page in range(1, 200):
                if page > total_pages:
                    break
                url = f"https://api.komerza.com/stores/{store_id}/orders"
                params = {"Page": page, "PageSize": 100}
                async with s.get(url, headers=headers, params=params) as r:
                    if r.status != 200:
                        break
                    data = await r.json()
                    if not data.get("data"):
                        break
                    total_pages = data.get("pages", 1)
                    for o in data["data"]:
                        email = o.get("customerEmail", "").lower()
                        if target in email:
                            print(f"FOUND ORDER: {email} - ${o.get('amountPaid', 0)} status={o.get('status')}")
                print(f"  Checked orders page {page}/{total_pages}", end="\r")
            print()

asyncio.run(search_all())
