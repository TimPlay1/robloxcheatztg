"""Test live API endpoint"""
import requests

API_URL = "https://robloxcheatztg.onrender.com"

print("Testing API endpoints...")

# Test health
try:
    r = requests.get(f"{API_URL}/", timeout=30)
    print(f"[Health /] Status: {r.status_code}, Body: {r.text[:100]}")
except Exception as e:
    print(f"[Health /] Error: {e}")

# Test /health
try:
    r = requests.get(f"{API_URL}/health", timeout=30)
    print(f"[Health /health] Status: {r.status_code}, Body: {r.text[:100]}")
except Exception as e:
    print(f"[Health /health] Error: {e}")

# Test tickets API
try:
    r = requests.get(f"{API_URL}/api/tickets", timeout=30)
    print(f"[Tickets] Status: {r.status_code}")
    print(f"[Tickets] Headers: {dict(r.headers)}")
    print(f"[Tickets] Body: {r.text[:500]}")
except Exception as e:
    print(f"[Tickets] Error: {e}")
