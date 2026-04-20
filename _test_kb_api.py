import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8788/api/v1'
r = requests.post(f'{BASE}/auth/login', data={'username': 'admin', 'password': 'admin123'}, timeout=5)
token = r.json().get('access_token', '')
h = {'Authorization': f'Bearer {token}'}

tests = [
    ('KB list', 'GET', '/knowledge/bases'),
    ('KB create', 'POST', '/knowledge/bases', {'name': 'TestKB', 'description': 'test', 'embedding_model': 'E:\\models\\all-mpnet-base-v2', 'rerank_enabled': True, 'rerank_model': 'E:\\models\\bge-reranker-v2-m3'}),
    ('Tags list', 'GET', '/knowledge/tags'),
    ('Tag create', 'POST', '/knowledge/tags', {'name': 'test-tag', 'color': '#1890ff'}),
    ('Notes list', 'GET', '/knowledge/notes'),
    ('Note create', 'POST', '/knowledge/notes', {'title': 'Test note', 'content': 'hello', 'tags': ['test']}),
    ('Search', 'GET', '/knowledge/search?q=test&type=hybrid&top_k=5'),
    ('Graph', 'GET', '/knowledge/graph'),
]

ok = 0
fail = 0
for name, method, url, *body in tests:
    try:
        if method == 'GET':
            r = requests.get(f'{BASE}{url}', headers=h, timeout=5)
        else:
            r = requests.post(f'{BASE}{url}', headers=h, json=body[0] if body else {}, timeout=5)
        if r.status_code < 300:
            ok += 1
            print(f'[OK] {name}: {r.status_code}')
        else:
            fail += 1
            print(f'[FAIL] {name}: {r.status_code} {r.text[:150]}')
    except Exception as e:
        fail += 1
        print(f'[ERR] {name}: {e}')

print(f'\nResult: {ok} OK, {fail} FAIL')
