import requests, sys, io, time
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://localhost:8788/api/v1'
r = requests.post(f'{BASE}/auth/login', json={'username': 'admin', 'password': 'admin123'}, timeout=30)
token = r.json().get('access_token', '')
h = {'Authorization': f'Bearer {token}'}

r = requests.get(f'{BASE}/knowledge/bases', headers=h, timeout=10)
kb_id = r.json()[0]['id']

# Upload + auto parse
t0 = time.time()
files = {'file': ('quick_test.txt', io.BytesIO('AI knowledge base system test content with keywords about vector search and semantic matching.'.encode('utf-8')), 'text/plain')}
r = requests.post(f'{BASE}/knowledge/upload/{kb_id}', headers=h, files=files, timeout=30)
print(f'Upload+Parse: {r.status_code} ({time.time()-t0:.1f}s)')
d = r.json()
print(f'  status={d.get("parsing_status")} id={d.get("id")}')

if d.get('id'):
    doc_id = d['id']
    r2 = requests.get(f'{BASE}/knowledge/documents/{doc_id}', headers=h, timeout=10)
    doc = r2.json()
    print(f'Get: status={doc.get("parsing_status")} kw={doc.get("keywords")} summary={doc.get("summary","")[:40]}')
    r3 = requests.delete(f'{BASE}/knowledge/documents/{doc_id}', headers=h, timeout=10)
    print(f'Delete: {r3.status_code}')

print('Done')
