import requests
import json

# 创建会话
session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json'
})

# 先登录获取token
def login():
    url = 'http://localhost:8879/api/v1/auth/login'
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = session.post(url, json=login_data)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Login failed: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test():
    token = login()
    if not token:
        print('Failed to login')
        return

    session.headers['Authorization'] = f'Bearer {token}'

    try:
        # 1. 获取应用列表
        apps_response = session.get('http://localhost:8879/api/v1/apps/')
        if apps_response.status_code == 200:
            apps = apps_response.json()
            print('=== 1. 获取应用列表 ===')
            print(f'应用数量: {len(apps)}')
            for app in apps:
                print(f"  - {app['name']} (ID: {app['id']}, is_published: {app.get('is_published', False)})")

            if len(apps) == 0:
                print('No apps found')
                return

            app_id = apps[0]['id']
            app_name = apps[0]['name']

            # 2. 获取应用详情
            print(f'\n=== 2. 获取应用详情 (ID: {app_id}) ===')
            detail_response = session.get(f'http://localhost:8879/api/v1/apps/{app_id}')
            if detail_response.status_code == 200:
                detail = detail_response.json()
                print(f"应用名称: {detail.get('name')}")
                print(f"is_published: {detail.get('is_published')}")
                dashboard_in_config = detail.get('config', {}).get('dashboard')
                print(f"config.dashboard 存在: {dashboard_in_config is not None}")
                if dashboard_in_config:
                    print(f"config.dashboard 页数: {len(dashboard_in_config.get('pages', []))}")
                else:
                    print("config.dashboard 不存在")
            else:
                print(f"获取应用详情失败: {detail_response.status_code}")

            # 3. 直接获取仪表盘配置
            print(f'\n=== 3. 直接获取仪表盘配置 ===')
            dashboard_response = session.get(f'http://localhost:8879/api/v1/apps/{app_id}/dashboard')
            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                print(f"success: {dashboard_data.get('success')}")
                print(f"message: {dashboard_data.get('message')}")
                data = dashboard_data.get('data', {})
                print(f"data 页数: {len(data.get('pages', []))}")
                if data.get('pages'):
                    for page in data['pages']:
                        print(f"  页面: {page.get('name')}, widgets数量: {len(page.get('widgets', []))}")
                        for widget in page.get('widgets', []):
                            print(f"    - {widget.get('title')} ({widget.get('type')}), template_id: {widget.get('data_source', {}).get('template_id')}")
            else:
                print(f"获取仪表盘配置失败: {dashboard_response.status_code}")

            # 4. 测试获取组件数据
            print(f'\n=== 4. 测试获取组件数据 ===')
            if dashboard_data.get('data', {}).get('pages'):
                for page in dashboard_data['data']['pages']:
                    for widget in page.get('widgets', []):
                        ds = widget.get('data_source')
                        if ds and ds.get('template_id'):
                            print(f"\n测试组件: {widget.get('title')} (type: {widget.get('type')})")
                            print(f"  data_source: {json.dumps(ds, ensure_ascii=False)}")
                            try:
                                widget_response = session.post('http://localhost:8879/api/v1/apps/dashboard/widget/data', json=widget)
                                if widget_response.status_code == 200:
                                    wd = widget_response.json()
                                    print(f"  成功: {wd.get('success')}, message: {wd.get('message')}")
                                    if wd.get('success') and wd.get('data'):
                                        print(f"  数据: {json.dumps(wd['data'], ensure_ascii=False)[:200]}")
                                else:
                                    print(f"  失败: {widget_response.status_code}")
                                    print(f"  Response: {json.dumps(widget_response.json(), indent=2, ensure_ascii=False)}")
                            except Exception as e:
                                print(f"  异常: {e}")

    except Exception as e:
        print(f'Test error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test()
