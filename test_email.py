import asyncio
import sys
sys.path.insert(0, '.')
from komerza_api import api

async def test():
    # Test with email that we know exists
    email = 'fivdjgwjcujj@gmail.com'
    print(f'Searching for: {email}')
    print('This may take a while (email is on page 99)...')
    
    customer = await api.get_customer_by_email(email)
    if customer:
        print(f'FOUND customer:')
        print(f'  Email: {customer.get("emailAddress")}')
        print(f'  Total Spent: ${customer.get("totalSpend", 0):.2f}')
        print(f'  Total Orders: {customer.get("totalOrders", 0)}')
        print(f'  Status: {customer.get("status")}')
    else:
        print('Customer NOT found')

asyncio.run(test())
