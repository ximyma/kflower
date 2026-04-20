import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://localhost:8788/api/v1'
r = requests.post(f'{BASE}/auth/login', json={'username': 'admin', 'password': 'admin123'}, timeout=5)
token = r.json().get('access_token', '')
h = {'Authorization': f'Bearer {token}'}

# Test search with detail
r = requests.get(f'{BASE}/knowledge/search', headers=h, params={'q': 'test', 'type': 'fulltext', 'top_k': 3}, timeout=10)
print(f'Search: {r.status_code}')
print(r.text[:500])

print('---')

# Test graph with detail
r = requests.get(f'{BASE}/knowledge/graph', headers=h, params={'kb_id': 1}, timeout=10)
print(f'Graph: {r.status_code}')
print(r.text[:500])
