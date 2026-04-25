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

# 测试获取仪表盘数据
def test_get_widget_data():
    token = login()
    if not token:
        return
    
    url = 'http://localhost:8879/api/v1/apps/dashboard/widget/data'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # 测试数据 - 模拟一个KPI组件
    widget_config = {
        "data_source": {
            "type": "aggregation",
            "template_id": 14,
            "aggregate": "count",
            "date_field": "created_at"
        }
    }
    
    try:
        response = requests.post(url, json=widget_config, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_get_widget_data()
