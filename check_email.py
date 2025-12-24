import json

data = json.load(open('customers_cache.json', encoding='utf-8'))
email = 'fivdjgwjcujj@gmail.com'
clients = []
for c in data.get('customers', []):
    e = c.get('email')
    if e and e.lower() == email.lower():
        clients.append(c)
print(f'Found {len(clients)} purchases for {email}:')
for c in clients:
    name = c.get('project_name', 'Unknown')
    print(f'- {name}')
