import requests, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://localhost:8788/api/v1'

# Login
r = requests.post(f'{BASE}/auth/login', json={'username': 'admin', 'password': 'admin123'}, timeout=10)
if r.status_code != 200:
    print(f'Login failed: {r.status_code}')
    sys.exit(1)
token = r.json().get('access_token', '')
h = {'Authorization': f'Bearer {token}'}
print('Login OK')

# Test all search types
search_types = ['fulltext', 'keyword', 'vector', 'hybrid']
for stype in search_types:
    try:
        r = requests.get(f'{BASE}/knowledge/search', headers=h, params={
            'q': '测试',
            'type': stype,
            'top_k': 5
        }, timeout=15)
        data = r.json()
        results = data.get('results', [])
        print(f'{stype}: {r.status_code} - {len(results)} results')
        if results:
            print(f'  Top: {results[0].get("title", "")[:30]} (score={results[0].get("score", 0):.3f})')
    except Exception as e:
        print(f'{stype}: ERROR - {e}')
