import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8788/api/v1'

# Login with JSON body
r = requests.post(f'{BASE}/auth/login', json={'username': 'admin', 'password': 'admin123'}, timeout=5)
print(f'Login: {r.status_code}')
data = r.json()
token = data.get('access_token', '')
print(f'Token: {token[:20]}...' if token else f'Error: {data}')

if not token:
    sys.exit(1)

h = {'Authorization': f'Bearer {token}'}

tests = [
    ('KB list', 'GET', '/knowledge/bases', None),
    ('KB create', 'POST', '/knowledge/bases', {'name': 'TestKB', 'description': 'test', 'embedding_model': 'E:\\models\\all-mpnet-base-v2', 'rerank_enabled': True, 'rerank_model': 'E:\\models\\bge-reranker-v2-m3'}),
    ('Tags', 'GET', '/knowledge/tags', None),
    ('Create tag', 'POST', '/knowledge/tags', {'name': 'test-tag', 'color': '#1890ff'}),
    ('Notes', 'GET', '/knowledge/notes', None),
    ('Create note', 'POST', '/knowledge/notes', {'title': 'Test', 'content': 'hello'}),
    ('Search', 'GET', '/knowledge/search?q=test&type=hybrid', None),
    ('Graph', 'GET', '/knowledge/graph', None),
]

ok = fail = 0
for name, method, url, body in tests:
    try:
        if method == 'GET':
            r = requests.get(f'{BASE}{url}', headers=h, timeout=5)
        else:
            r = requests.post(f'{BASE}{url}', headers=h, json=body, timeout=5)
        if r.status_code < 300:
            ok += 1
            print(f'[OK] {name}: {r.status_code}')
        else:
            fail += 1
            print(f'[FAIL] {name}: {r.status_code} {r.text[:100]}')
    except Exception as e:
        fail += 1
        print(f'[ERR] {name}: {e}')

print(f'\n{ok}/{ok+fail} passed')
