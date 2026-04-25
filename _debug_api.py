import requests, json, sys

BASE = 'http://127.0.0.1:8878/api/v1'

r = requests.post(f'{BASE}/auth/login', json={'username':'admin','password':'admin123'}, timeout=5)
token = r.json().get('access_token')
headers = {'Authorization':f'Bearer {token}', 'Content-Type':'application/json'}

r = requests.get(f'{BASE}/apps/', headers=headers, timeout=5)
with open('e:\\kkflower\\_debug_output.txt', 'w', encoding='utf-8') as f:
    f.write(f'Status: {r.status_code}\n')
    f.write(f'Headers: {dict(r.headers)}\n')
    f.write(f'Body: {r.text}\n')
