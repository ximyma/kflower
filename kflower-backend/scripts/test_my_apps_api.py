"""
我的应用模块 - API 测试脚本
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8878/api/v1"
TOKEN = ""  # 登录后填入 token

def login():
    """登录获取 token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        global TOKEN
        TOKEN = response.json()["token"]
        print(f"✅ 登录成功，Token: {TOKEN[:20]}...")
        return True
    else:
        print(f"❌ 登录失败：{response.text}")
        return False

def test_create_app():
    """测试创建应用"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        f"{BASE_URL}/apps/",
        headers=headers,
        json={
            "name": "测试进销存系统",
            "description": "这是一个测试应用",
            "icon": "ShoppingCart",
            "theme": "light"
        }
    )
    if response.status_code == 200:
        app = response.json()
        print(f"✅ 创建应用成功：{app['name']} (ID: {app['id']})")
        return app['id']
    else:
        print(f"❌ 创建应用失败：{response.text}")
        return None

def test_list_apps(app_id):
    """测试获取应用列表"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/apps/", headers=headers)
    if response.status_code == 200:
        apps = response.json()
        print(f"✅ 获取应用列表成功，共 {len(apps)} 个应用")
        for app in apps:
            print(f"  - {app['name']} (已发布：{app['is_published']})")
    else:
        print(f"❌ 获取应用列表失败：{response.text}")

def test_add_menu(app_id):
    """测试添加菜单"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(
        f"{BASE_URL}/apps/{app_id}/menus",
        headers=headers,
        json={
            "template_id": 1,  # 假设已有模板 ID 为 1
            "menu_label": "客户管理",
            "menu_icon": "User",
            "menu_order": 1
        }
    )
    if response.status_code == 200:
        menu = response.json()
        print(f"✅ 添加菜单成功：{menu['menu_label']} (ID: {menu['id']})")
    else:
        print(f"❌ 添加菜单失败：{response.text}")

def test_publish_app(app_id):
    """测试发布应用"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(f"{BASE_URL}/apps/{app_id}/publish", headers=headers)
    if response.status_code == 200:
        app = response.json()
        print(f"✅ 发布应用成功：{app['name']}")
    else:
        print(f"❌ 发布应用失败：{response.text}")

def main():
    """主测试流程"""
    print("=" * 50)
    print("开始测试我的应用模块 API")
    print("=" * 50)
    
    # 1. 登录
    if not login():
        return
    
    # 2. 创建应用
    app_id = test_create_app()
    if not app_id:
        return
    
    # 3. 获取应用列表
    test_list_apps(app_id)
    
    # 4. 添加菜单（需要已有模板）
    # test_add_menu(app_id)
    
    # 5. 发布应用
    test_publish_app(app_id)
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n测试异常：{e}")
        import traceback
        traceback.print_exc()
