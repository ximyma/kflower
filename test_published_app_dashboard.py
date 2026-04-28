import requests
import json

# 先登录获取token
def login():
    url = 'http://localhost:8879/api/v1/auth/login'
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=login_data)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Login failed: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

# 测试获取发布应用的仪表盘数据
def test_published_app_dashboard():
    token = login()
    if not token:
        return
    
    # 首先获取应用列表，找到一个已发布的应用
    app_list_url = 'http://localhost:8879/api/v1/apps/'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        # 获取应用列表
        app_response = requests.get(app_list_url, headers=headers)
        if app_response.status_code == 200:
            apps = app_response.json()
            print(f"获取到 {len(apps)} 个应用")
            
            # 找到第一个已发布的应用
            published_app = None
            for app in apps:
                if app.get('is_published'):
                    published_app = app
                    break
            
            if not published_app:
                print("没有找到已发布的应用")
                return
            
            app_id = published_app['id']
            print(f"测试已发布应用: {published_app['name']} (ID: {app_id})")
            
            # 获取仪表盘配置
            dashboard_url = f'http://localhost:8879/api/v1/apps/{app_id}/dashboard'
            dashboard_response = requests.get(dashboard_url, headers=headers)
            if dashboard_response.status_code == 200:
                dashboard_config = dashboard_response.json()
                print(f"获取到仪表盘配置: {json.dumps(dashboard_config, indent=2, ensure_ascii=False)}")
                
                # 测试获取组件数据
                if 'data' in dashboard_config and 'pages' in dashboard_config['data']:
                    pages = dashboard_config['data']['pages']
                    for page in pages:
                        if 'widgets' in page:
                            for widget in page['widgets']:
                                if widget.get('data_source') and widget['data_source'].get('template_id'):
                                    print(f"\n测试组件: {widget['title']} (类型: {widget['type']})")
                                    # 调用 getWidgetData API
                                    widget_data_url = 'http://localhost:8879/api/v1/apps/dashboard/widget/data'
                                    widget_response = requests.post(widget_data_url, json=widget, headers=headers)
                                    print(f"Status code: {widget_response.status_code}")
                                    print(f"Response: {json.dumps(widget_response.json(), indent=2, ensure_ascii=False)}")
            else:
                print(f"获取仪表盘配置失败: {dashboard_response.status_code}")
                print(f"Response: {json.dumps(dashboard_response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"获取应用列表失败: {app_response.status_code}")
            print(f"Response: {json.dumps(app_response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_published_app_dashboard()
