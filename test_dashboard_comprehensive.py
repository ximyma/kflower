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

# 测试获取不同类型的仪表盘组件数据
def test_widget_data_types():
    token = login()
    if not token:
        return
    
    url = 'http://localhost:8879/api/v1/apps/dashboard/widget/data'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # 测试KPI组件（聚合查询）
    print("=== 测试KPI组件（聚合查询）===")
    kpi_config = {
        "data_source": {
            "type": "aggregation",
            "template_id": 14,
            "aggregate": "count",
            "date_field": "created_at"
        }
    }
    
    try:
        response = requests.post(url, json=kpi_config, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 测试表格组件（列表查询）
    print("\n=== 测试表格组件（列表查询）===")
    table_config = {
        "data_source": {
            "type": "query",
            "template_id": 14,
            "order_by": "-created_at",
            "limit": 5
        }
    }
    
    try:
        response = requests.post(url, json=table_config, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_widget_data_types()
