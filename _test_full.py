import requests, sys, io, time
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://localhost:8788/api/v1'

r = requests.post(f'{BASE}/auth/login', json={'username': 'admin', 'password': 'admin123'}, timeout=10)
token = r.json().get('access_token', '')
h = {'Authorization': f'Bearer {token}'}

# Get KB
r = requests.get(f'{BASE}/knowledge/bases', headers=h, timeout=10)
kb_id = r.json()[0]['id']
print(f'KB id={kb_id}')

# 1. Upload (should auto-parse text+keywords)
t0 = time.time()
files = {'file': ('auto_test.txt', io.BytesIO('人工智能技术正在快速发展，深度学习在自然语言处理领域取得了突破性进展。知识库系统通过向量检索和语义匹配技术，实现了智能化的文档管理和信息检索。'.encode('utf-8')), 'text/plain')}
r = requests.post(f'{BASE}/knowledge/upload/{kb_id}', headers=h, files=files, timeout=30)
elapsed = time.time() - t0
data = r.json()
print(f'Upload+Parse: {r.status_code} ({elapsed:.1f}s) status={data.get("parsing_status")}')

if data.get('id'):
    doc_id = data['id']
    # 2. Check document (should have keywords + summary)
    r = requests.get(f'{BASE}/knowledge/documents/{doc_id}', headers=h, timeout=10)
    doc = r.json()
    print(f'Get doc: status={doc.get("parsing_status")} keywords={doc.get("keywords")} summary={doc.get("summary","")[:30]}...')

    # 3. Vectorize
    t1 = time.time()
    r = requests.post(f'{BASE}/knowledge/vectorize/{doc_id}', headers=h, timeout=120)
    t2 = time.time()
    print(f'Vectorize: {r.status_code} ({t2-t1:.1f}s) message={r.json().get("message")}')

    # 4. Delete
    r = requests.delete(f'{BASE}/knowledge/documents/{doc_id}', headers=h, timeout=10)
    print(f'Delete: {r.status_code}')
else:
    print(f'Upload failed: {data}')

# 5. Vectorize-all test
r = requests.post(f'{BASE}/knowledge/vectorize-all/{kb_id}', headers=h, timeout=120)
print(f'\nVectorize-all: {r.status_code} {r.json().get("message")[:60]}')

print('\nDone')
