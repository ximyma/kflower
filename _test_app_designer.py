"""测试应用详情 API"""
import requests
import json

# 模拟登录获取 token
login_data = {
    "username": "admin",
    "password": "admin123"
}

# 登录
session = requests.Session()
try:
    login_resp = session.post("http://127.0.0.1:8788/api/v1/auth/login", json=login_data)
    print(f"登录状态: {login_resp.status_code}")
    if login_resp.status_code == 200:
        token = login_resp.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
except Exception as e:
    print(f"登录失败: {e}")
    exit(1)

# 获取应用详情
try:
    resp = session.get("http://127.0.0.1:8788/api/v1/apps/5")  # 货物采购应用
    print(f"应用详情 API 状态: {resp.status_code}")
    print(f"响应内容: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:2000]}")
except Exception as e:
    print(f"获取应用详情失败: {e}")

# 获取菜单树
try:
    resp = session.get("http://127.0.0.1:8788/api/v1/apps/5/menus/tree")
    print(f"\n菜单树 API 状态: {resp.status_code}")
    print(f"响应内容: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"获取菜单树失败: {e}")

# 获取模板列表
try:
    resp = session.get("http://127.0.0.1:8788/api/v1/templates/")
    print(f"\n模板列表 API 状态: {resp.status_code}")
    templates = resp.json()
    print(f"模板总数: {len(templates) if isinstance(templates, list) else 'N/A'}")
    # 找货物采购单
    for t in (templates if isinstance(templates, list) else []):
        if '货物' in str(t.get('name', '')):
            print(f"货物采购相关模板: {json.dumps(t, ensure_ascii=False)}")
except Exception as e:
    print(f"获取模板列表失败: {e}")
