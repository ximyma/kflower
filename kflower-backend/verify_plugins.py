"""验证插件系统所有API端点"""
import urllib.request, json

# Login
body = json.dumps({'username': 'admin', 'password': 'admin123'}).encode()
req = urllib.request.Request('http://localhost:8788/api/v1/auth/login', data=body, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=5) as resp:
    token = json.loads(resp.read().decode()).get('access_token', '')

h = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}

# 1. Plugins list
req1 = urllib.request.Request('http://localhost:8788/api/v1/plugins/', headers=h)
with urllib.request.urlopen(req1, timeout=5) as r:
    d = json.loads(r.read().decode())
    items = d.get('data', [])
    print(f'[Plugins] count={len(items)}')
    for p in items:
        name = p.get('name', '')
        enabled = p.get('is_enabled', False)
        builtin = p.get('is_built_in', False)
        print(f'  {name} | enabled={enabled} | builtin={builtin}')

# 2. Hooks list
req2 = urllib.request.Request('http://localhost:8788/api/v1/plugins/builtin-events', headers=h)
try:
    with urllib.request.urlopen(req2, timeout=5) as r:
        d = json.loads(r.read().decode())
        hooks = d.get('data', [])
        print(f'\n[Hooks] count={len(hooks)}')
        for hk in hooks:
            print(f'  {hk.get("name")} ({hk.get("event")})')
except Exception as e:
    print(f'[Hooks] error: {e}')

# 3. Event docs
req3 = urllib.request.Request('http://localhost:8788/api/v1/plugins/event-docs', headers=h)
try:
    with urllib.request.urlopen(req3, timeout=5) as r:
        d = json.loads(r.read().decode())
        docs = d.get('data', {})
        print(f'\n[EventDocs] keys={list(docs.keys())[:5]}')
except Exception as e:
    print(f'[EventDocs] error: {e}')

# 4. Get single plugin
if items:
    pid = items[0].get('id')
    req4 = urllib.request.Request(f'http://localhost:8788/api/v1/plugins/{pid}', headers=h)
    try:
        with urllib.request.urlopen(req4, timeout=5) as r:
            d = json.loads(r.read().decode())
            p = d.get('data', {})
            print(f'\n[Plugin Detail] name={p.get("name")} version={p.get("version")}')
    except Exception as e:
        print(f'[Plugin Detail] error: {e}')

print('\nAll endpoint checks done!')
