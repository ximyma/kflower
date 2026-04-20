import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8788/api/v1'

# Try login
r = requests.post(f'{BASE}/auth/login', data={'username': 'admin', 'password': 'admin123'}, timeout=5)
print(f'Login status: {r.status_code}')
login_data = r.json()
print(f'Login keys: {list(login_data.keys())}')

# Try with different token key names
token = login_data.get('access_token') or login_data.get('token') or login_data.get('accessToken') or ''
print(f'Token: {token[:20]}...' if token else 'NO TOKEN')

if token:
    h = {'Authorization': f'Bearer {token}'}
    r2 = requests.get(f'{BASE}/knowledge/bases', headers=h, timeout=5)
    print(f'KB list: {r2.status_code}')
