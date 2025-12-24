import requests
import json

API_KEY = "AqGqb9X5uF3fAXPiE_WxFOChWBGAOJeV"
EMAIL = "fivdjgwjcujj@gmail.com"

# 1. Проверяем клиента по email
print("=" * 50)
print(f"Проверка клиента: {EMAIL}")
print("=" * 50)

# Получаем всех клиентов
r = requests.get(f'https://api.komerza.ru/clients?api_key={API_KEY}')
data = r.json()
print(f"\nСтатус ответа: {data.get('status')}")
print(f"Всего клиентов в payload: {len(data.get('payload', []))}")

# Ищем нашего клиента
clients = data.get('payload', [])
found = None
for c in clients:
    if c.get('emailAddress', '').lower() == EMAIL.lower():
        found = c
        break

if found:
    print(f"\n✅ Клиент найден!")
    print(json.dumps(found, indent=2))
else:
    print(f"\n❌ Клиент НЕ найден в списке клиентов")

# 2. Проверяем заказы
print("\n" + "=" * 50)
print("Проверка заказов")
print("=" * 50)

r2 = requests.get(f'https://api.komerza.ru/orders?api_key={API_KEY}')
orders_data = r2.json()
print(f"\nСтатус ответа: {orders_data.get('status')}")
print(f"Всего заказов: {len(orders_data.get('payload', []))}")

# Ищем заказы по email
orders = orders_data.get('payload', [])
user_orders = []
for o in orders:
    # Проверяем email в заказе
    email_in_order = o.get('email', '') or o.get('emailAddress', '') or o.get('customer', {}).get('email', '')
    if email_in_order.lower() == EMAIL.lower():
        user_orders.append(o)

if user_orders:
    print(f"\n✅ Найдено заказов для {EMAIL}: {len(user_orders)}")
    for i, order in enumerate(user_orders, 1):
        print(f"\n--- Заказ #{i} ---")
        print(json.dumps(order, indent=2))
else:
    print(f"\n❌ Заказов для {EMAIL} не найдено")

# 3. Проверяем структуру одного заказа
print("\n" + "=" * 50)
print("Структура первых 3 заказов (для понимания формата)")
print("=" * 50)
for i, order in enumerate(orders[:3], 1):
    print(f"\n--- Пример заказа #{i} ---")
    print(json.dumps(order, indent=2))
