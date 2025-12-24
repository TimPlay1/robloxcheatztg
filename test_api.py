"""
Тестовый скрипт для API Komerza
"""
import asyncio
import aiohttp
import json

TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6Ijc3ZDFiNDBkLWE2NzYtNGI1MS1hNTg3LWZiZDE4OGI5YmZkZiIsInR5cCI6IkpXVCJ9.eyJuYmYiOiIxNzY2MjI4Mzg5IiwiaXNzIjoiS29tZXJ6YSIsImlhdCI6IjE3NjYyMjgzODkiLCJhdWQiOiJtZXJjaGFudCIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL25hbWUiOiJkMjUxZmFiZS0yODk4LTQ0ODctODU3YS00YzQzYTczNzU2M2MiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjQ4Y2E2MTg5LTljM2UtNDlkOS1hNzcxLWVlM2JiOTQ3MjA5OSIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6InJlZm92b2QwMDFAZ21haWwuY29tIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiRm91clBlcmNlbnRGZWVzIiwiYXBpX2tleV9pZCI6IjUxODhlN2M0LWEzMmUtNGFjMS04YThiLWUzMmQxNTcyNDM1NyIsImV4cCI6IjI1MzQwMjMwMDc5OSIsImtleV9mbGFncyI6ImFwaSIsInNjb3BlIjpbInN0b3Jlcy51cGRhdGUiLCJzdG9yZXMudmlldyIsInN0b3Jlcy5vcmRlcnMudmlldyIsInN0b3Jlcy5wcm9kdWN0cy52aWV3Iiwic3RvcmVzLmNhdGVnb3JpZXMudmlldyIsInN0b3Jlcy5jdXN0b21lcnMudmlldyJdfQ.iattzLUFHiVf9CasrQ2caF_bWQXtCqiRh1trghMFo0VdTtQNMYB_XXo0E1Jevc6PLY1jL9EvmLR7TOsk-JlhhQ"

STORE_ID = "d251fabe-2898-4487-857a-4c43a737563c"
EMAIL = "fivdjgwjcujj@gmail.com"

async def test_api():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "IlyaDiscordBot/1.0",
        "Accept": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Test different endpoints
        endpoints = [
            f"https://api.komerza.com/stores/{STORE_ID}/customers",
            f"https://api.komerza.com/stores/{STORE_ID}/orders",
            f"https://api.komerza.com/stores",
            f"https://api.komerza.com/stores/{STORE_ID}",
        ]
        
        for url in endpoints:
            print(f"\n{'='*50}")
            print(f"Testing: {url}")
            print('='*50)
            try:
                async with session.get(url, headers=headers) as resp:
                    print(f"Status: {resp.status}")
                    print(f"Content-Type: {resp.headers.get('Content-Type')}")
                    text = await resp.text()
                    print(f"Response: {text[:500]}")
            except Exception as e:
                print(f"Error: {e}")
        
        # Test with email filter
        print(f"\n{'='*50}")
        print(f"Testing orders with email: {EMAIL}")
        print('='*50)
        url = f"https://api.komerza.com/stores/{STORE_ID}/orders"
        try:
            async with session.get(url, headers=headers, params={"email": EMAIL}) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(f"Response: {text[:1000]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
