"""插件系统端到端测试"""
import urllib.request, json

BASE = 'http://localhost:8788/api/v1'

def api(method, path, data=None, token=None):
    url = f'{BASE}{path}'
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

# 1. Login
r = api('POST', '/auth/login', {'username': 'admin', 'password': 'admin123'})
token = r.get('access_token', '')
print(f'1. Login: OK (token len={len(token)})')

# 2. List plugins
r = api('GET', '/plugins/', token=token)
plugins = r.get('data', [])
print(f'2. List plugins: {len(plugins)} plugins')

# 3. Create custom plugin
new_plugin = {
    'name': 'my-test-plugin',
    'display_name': '测试插件',
    'description': 'E2E测试用自定义插件',
    'version': '1.0.0',
    'author': 'Test',
    'icon': 'test',
    'install_type': 'local',
    'config': {'test_key': 'test_value'},
    'hook_code': {
        'before_form_submit': '# Test hook code\nreturn context',
        'after_form_submit': '# Notify hook\nreturn context'
    }
}
r = api('POST', '/plugins/', new_plugin, token)
print(f'3. Create custom plugin: success={r.get("success")} name={r.get("data", {}).get("name")}')
custom_id = r.get('data', {}).get('id')

# 4. Get plugin detail
if custom_id:
    r = api('GET', f'/plugins/{custom_id}', token=token)
    print(f'4. Get detail: name={r.get("data", {}).get("name")} hooks={list(r.get("data", {}).get("hook_code", {}).keys())}')

# 5. Update plugin
if custom_id:
    r = api('PUT', f'/plugins/{custom_id}', {
        'description': 'Updated description',
        'config': {'test_key': 'updated_value', 'new_key': 42}
    }, token)
    print(f'5. Update plugin: success={r.get("success")}')

# 6. Disable custom plugin
if custom_id:
    r = api('POST', f'/plugins/{custom_id}/disable', token=token)
    print(f'6. Disable plugin: success={r.get("success")} msg={r.get("message")}')

# 7. Enable custom plugin
if custom_id:
    r = api('POST', f'/plugins/{custom_id}/enable', token=token)
    print(f'7. Enable plugin: success={r.get("success")} msg={r.get("message")}')

# 8. Get stats
r = api('GET', '/plugins/stats/overview', token=token)
stats = r.get('data', {})
print(f'8. Stats: total={stats.get("total")} enabled={stats.get("enabled")} builtin={stats.get("builtin")} custom={stats.get("custom")}')

# 9. Test hook code
r = api('POST', '/plugins/test-hook', {
    'plugin_name': 'my-test-plugin',
    'hook_name': 'before_form_submit',
    'code': 'result = {"processed": True, "fields": context.get("fields", [])}\nreturn result',
    'mock_data': {'fields': ['name', 'email'], 'template_id': 1},
    'timeout': 5.0
}, token)
print(f'9. Test hook: success={r.get("success")} data_keys={list(r.get("data", {}).keys())}')

# 10. Bind plugin to template (template_id=1)
if custom_id:
    r = api('POST', '/plugins/template/1/bind', {'plugin_id': custom_id, 'config': {'scope': 'test'}}, token)
    print(f'10. Bind to template: success={r.get("success")} msg={r.get("message")}')

# 11. List template bindings
r = api('GET', '/plugins/template/1/bindings', token=token)
bindings = r.get('data', [])
print(f'11. Template bindings: {len(bindings)} bindings')

# 12. Delete custom plugin
if custom_id:
    # First unbind
    if bindings:
        bid = bindings[0].get('id')
        r = api('DELETE', f'/plugins/template/1/binding/{bid}', token=token)
        print(f'12a. Unbind: success={r.get("success")}')
    r = api('DELETE', f'/plugins/{custom_id}', token=token)
    print(f'12b. Delete plugin: success={r.get("success")} msg={r.get("message")}')

print('\n=== All E2E tests completed! ===')
