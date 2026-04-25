import requests, json, sqlite3

BASE = "http://localhost:8788/api/v1"

# 尝试所有可能的登录端点
for url in [f"{BASE}/auth/login", f"{BASE}/login", "/api/auth/login"]:
    try:
        r = requests.post(url, json={"username": "admin", "password": "123456"}, timeout=3)
        print(f"{url}: {r.status_code} -> {r.text[:200]}")
    except Exception as e:
        print(f"{url}: ERROR {e}")

# 直接查看后端路由
print("\n--- Checking what's actually running on 8788 ---")
r = requests.get("http://localhost:8788/docs", timeout=3)
print(f"Swagger: {r.status_code}")

# 尝试不需要认证的端点
r2 = requests.get("http://localhost:8788/api/v1/apps/", timeout=3)
print(f"Apps (no auth): {r2.status_code}")
