"""测试模板 API"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 登录获取 token
login_data = {
    "username": "admin",
    "password": "admin123"
}

# 先尝试登录
try:
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
    print(f"登录状态: {resp.status_code}")
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        print(f"获取 Token: {token[:20]}...")
    else:
        print(f"登录失败: {resp.text}")
        token = None
except Exception as e:
    print(f"无法连接到后端: {e}")
    print("后端可能没有启动")
    token = None

if token:
    headers = {"Authorization": f"Bearer {token}"}

    # 测试创建模板
    template_data = {
        "name": "测试模板",
        "description": "API测试",
        "category": "测试",
        "ai_generated": True,
        "modules": [{
            "name": "test_module",
            "label": "测试模块",
            "fields": [
                {"name": "field1", "label": "字段1", "type": "text"},
                {"name": "field2", "label": "字段2", "type": "number"}
            ]
        }]
    }

    print("\n=== 测试创建模板 ===")
    try:
        resp = requests.post(f"{BASE_URL}/templates/", json=template_data, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text[:500]}")
    except Exception as e:
        print(f"创建模板失败: {e}")
