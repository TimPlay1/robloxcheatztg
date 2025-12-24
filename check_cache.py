import json

# Загружаем кэш
with open('customers_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

EMAIL = "fivdjgwjcujj@gmail.com"

customers = cache.get("customers", {})
print(f"Всего клиентов в кэше: {len(customers)}")

# Ищем клиента
if EMAIL.lower() in customers:
    customer = customers[EMAIL.lower()]
    print(f"\n✅ Клиент найден: {EMAIL}")
    print(json.dumps(customer, indent=2, ensure_ascii=False))
else:
    print(f"\n❌ Клиент {EMAIL} НЕ найден в кэше")
    # Попробуем найти похожие
    for email in list(customers.keys())[:10]:
        print(f"  - {email}")
