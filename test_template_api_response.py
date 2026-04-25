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

def test():
    token = login()
    if not token:
        print('Failed to login')
        return

    session.headers['Authorization'] = f'Bearer {token}'

    # 测试获取模板14的详情
    print("=== 测试获取模板 14 的完整响应 ===")
    response = session.get('http://localhost:8879/api/v1/templates/14')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应类型: {type(data)}")
        print(f"响应包含的键: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
        print(f"modules 字段存在: {'modules' in data}")
        
        # 检查响应结构
        print(f"\n模板名称: {data.get('name')}")
        print(f"modules 类型: {type(data.get('modules'))}")
        
        modules = data.get('modules', [])
        if isinstance(modules, list):
            print(f"modules 长度: {len(modules)}")
            for i, mod in enumerate(modules):
                print(f"  模块[{i}] 类型: {type(mod)}, 键: {list(mod.keys()) if isinstance(mod, dict) else 'not a dict'}")
                if isinstance(mod, dict):
                    print(f"    name: {mod.get('name')}")
                    print(f"    fields 类型: {type(mod.get('fields'))}")
                    fields = mod.get('fields', [])
                    if isinstance(fields, list) and len(fields) > 0:
                        print(f"    fields[0] 键: {list(fields[0].keys()) if isinstance(fields[0], dict) else 'not a dict'}")
                        print(f"    fields[0] name: {fields[0].get('name')}, label: {fields[0].get('label')}")
        
        # 打印完整响应的前500个字符
        print(f"\n完整响应前500字符:")
        print(json.dumps(data, ensure_ascii=False)[:500])
    else:
        print(f"请求失败: {response.status_code}")
        print(f"响应: {response.text}")

if __name__ == '__main__':
    test()
