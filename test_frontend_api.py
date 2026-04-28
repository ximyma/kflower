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

# 测试获取应用的仪表盘数据
def test_dashboard_data():
    token = login()
    if not token:
        print('Failed to login')
        return

    # 设置token
    session.headers['Authorization'] = f'Bearer {token}'

    try:
        # 获取应用列表
        apps_response = session.get('http://localhost:8879/api/v1/apps/')
        if apps_response.status_code == 200:
            apps = apps_response.json()
            print('Apps:', apps)

            if len(apps) == 0:
                print('No apps found')
                return

            app_id = apps[0]['id']
            print('Testing app:', app_id, apps[0]['name'])

            # 获取仪表盘配置
            dashboard_response = session.get(f'http://localhost:8879/api/v1/apps/{app_id}/dashboard')
            if dashboard_response.status_code == 200:
                print('Dashboard config:', json.dumps(dashboard_response.json(), indent=2, ensure_ascii=False))

                # 测试获取组件数据
                if 'data' in dashboard_response.json() and 'pages' in dashboard_response.json()['data']:
                    pages = dashboard_response.json()['data']['pages']
                    for page in pages:
                        if 'widgets' in page:
                            for widget in page['widgets']:
                                if widget.get('data_source') and widget['data_source'].get('template_id'):
                                    print(f"\nTesting widget: {widget['title']} ({widget['type']})")
                                    try:
                                        widget_response = session.post('http://localhost:8879/api/v1/apps/dashboard/widget/data', json=widget)
                                        if widget_response.status_code == 200:
                                            print('Widget data:', json.dumps(widget_response.json(), indent=2, ensure_ascii=False))
                                        else:
                                            print(f'Error getting widget data: {widget_response.status_code}')
                                            print(f'Response: {json.dumps(widget_response.json(), indent=2, ensure_ascii=False)}')
                                    except Exception as e:
                                        print(f'Error getting widget data: {e}')
            else:
                print(f'Error getting dashboard config: {dashboard_response.status_code}')
                print(f'Response: {json.dumps(dashboard_response.json(), indent=2, ensure_ascii=False)}')
        else:
            print(f'Error getting apps: {apps_response.status_code}')
            print(f'Response: {json.dumps(apps_response.json(), indent=2, ensure_ascii=False)}')
    except Exception as e:
        print(f'Test error: {e}')

if __name__ == '__main__':
    test_dashboard_data()
