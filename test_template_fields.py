import requests
import json

session = requests.Session()
session.headers.update({'Content-Type': 'application/json'})

def login():
    url = 'http://localhost:8879/api/v1/auth/login'
    try:
        response = session.post(url, json={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            return response.json()['access_token']
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_template_fields():
    token = login()
    if not token:
        print('Failed to login')
        return

    session.headers['Authorization'] = f'Bearer {token}'

    # 获取应用列表
    apps_response = session.get('http://localhost:8879/api/v1/apps/')
    if apps_response.status_code != 200:
        print(f"获取应用列表失败: {apps_response.status_code}")
        return

    apps = apps_response.json()
    if not apps:
        print('No apps found')
        return

    app_id = apps[0]['id']
    print(f"测试应用: {apps[0]['name']} (ID: {app_id})")

    # 获取仪表盘配置
    dashboard_response = session.get(f'http://localhost:8879/api/v1/apps/{app_id}/dashboard')
    if dashboard_response.status_code != 200:
        print(f"获取仪表盘配置失败: {dashboard_response.status_code}")
        return

    dashboard_data = dashboard_response.json()

    # 找到所有template_id
    template_ids = set()
    if dashboard_data.get('data', {}).get('pages'):
        for page in dashboard_data['data']['pages']:
            for widget in page.get('widgets', []):
                if widget.get('data_source', {}).get('template_id'):
                    template_ids.add(widget['data_source']['template_id'])

    print(f"\n找到 {len(template_ids)} 个模板ID: {template_ids}")

    # 测试获取模板详情
    for template_id in template_ids:
        print(f"\n=== 测试获取模板 {template_id} 的详情 ===")
        try:
            template_response = session.get(f'http://localhost:8879/api/v1/templates/{template_id}')
            print(f"Status: {template_response.status_code}")
            if template_response.status_code == 200:
                template_data = template_response.json()
                print(f"模板名称: {template_data.get('name')}")
                print(f"modules 存在: {'modules' in template_data}")
                if 'modules' in template_data:
                    modules = template_data['modules']
                    print(f"modules 数量: {len(modules)}")
                    for mod in modules:
                        print(f"  模块: {mod.get('name')}, fields数量: {len(mod.get('fields', []))}")
                        # 打印前3个字段
                        for field in mod.get('fields', [])[:3]:
                            print(f"    - name: {field.get('name')}, label: {field.get('label')}")
                else:
                    print(f"modules 字段: {list(template_data.keys())}")
            else:
                print(f"获取模板详情失败: {template_response.status_code}")
                print(f"Response: {template_response.text[:500]}")
        except Exception as e:
            print(f"异常: {e}")

if __name__ == '__main__':
    test_template_fields()
