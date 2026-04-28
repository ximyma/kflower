# -*- coding: utf-8 -*-
import sys, json, sqlite3, requests
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8788/api/v1"
token = requests.post(f"{BASE}/auth/login", json={"username":"admin","password":"admin123"}, timeout=5).json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 1. 拿仪表盘配置
r = requests.get(f"{BASE}/apps/1/dashboard", headers=h, timeout=5).json()
pages = r['data']['pages']
print("=== 仪表盘配置 ===")
for p in pages:
    print(f"Page: {p['name']}")
    for w in p.get('widgets', []):
        ds = w.get('data_source', {})
        print(f"  Widget '{w['title']}' type={w['type']} group_by={w.get('group_by')} ds.type={ds.get('type')} template_id={ds.get('template_id')} aggregate={ds.get('aggregate')}")

# 2. 拿模板字段
conn = sqlite3.connect(r'E:\kkflower\kflower-backend\kflower-data\kflower.db')
cur = conn.cursor()
cur.execute("SELECT id, name, modules FROM templates WHERE id=14")
row = cur.fetchone()
if row:
    tid, name, modules_raw = row
    modules = json.loads(modules_raw) if isinstance(modules_raw, str) else (modules_raw or [])
    print(f"\n=== 模板(id=14): {name} ===")
    for mod in modules or []:
        print(f"  Module: {mod.get('label', mod.get('name'))}")
        for f in mod.get('fields', []) or []:
            print(f"    {f['name']} → {f.get('label', f['name'])}")

# 3. 测试各类型 widget 的数据
print("\n=== widget 数据测试 ===")
for p in pages:
    for w in p.get('widgets', []):
        ds = w.get('data_source') or {}
        if ds.get('template_id'):
            resp = requests.post(f"{BASE}/apps/dashboard/widget/data", json=w, headers=h, timeout=5)
            result = resp.json()
            print(f"\n{w['title']} ({w['type']}, ds.type={ds.get('type')}):")
            print(f"  API: {resp.status_code} -> {json.dumps(result.get('data', result), ensure_ascii=False)[:300]}")

conn.close()