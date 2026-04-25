import requests
import json

# 创建会话
session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json'
})

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
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_widget_data_with_full_headers():
    token = login()
    if not token:
        print('Failed to login')
        return

    # 模拟前端请求，设置和axios一样的headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    # 获取应用
    apps_response = session.get('http://localhost:8879/api/v1/apps/', headers=headers)
    if apps_response.status_code != 200:
        print(f"获取应用列表失败: {apps_response.status_code}")
        return

    apps = apps_response.json()
    app_id = apps[0]['id']

    # 获取仪表盘配置
    dashboard_response = session.get(f'http://localhost:8879/api/v1/apps/{app_id}/dashboard', headers=headers)
    if dashboard_response.status_code != 200:
        print(f"获取仪表盘配置失败: {dashboard_response.status_code}")
        return

    dashboard_data = dashboard_response.json()

    # 测试所有组件
    if dashboard_data.get('data', {}).get('pages'):
        for page in dashboard_data['data']['pages']:
            for widget in page.get('widgets', []):
                ds = widget.get('data_source')
                if ds and ds.get('template_id'):
                    print(f"\n测试组件: {widget.get('title')} (type: {widget.get('type')})")
                    print(f"  widget.i: {widget.get('i')}")
                    print(f"  widget.data_source.template_id: {ds.get('template_id')}")

                    # 发送请求
                    try:
                        widget_response = session.post(
                            'http://localhost:8879/api/v1/apps/dashboard/widget/data',
                            json=widget,
                            headers=headers
                        )
                        print(f"  Status: {widget_response.status_code}")
                        wd = widget_response.json()
                        print(f"  success: {wd.get('success')}")
                        print(f"  message: {wd.get('message')}")
                        if wd.get('success') and wd.get('data'):
                            print(f"  data.value/data.count: {wd['data'].get('value') or wd['data'].get('count')}")
                        elif not wd.get('success'):
                            print(f"  ERROR: {wd.get('message')}")
                    except Exception as e:
                        print(f"  Exception: {e}")

if __name__ == '__main__':
    test_widget_data_with_full_headers()
