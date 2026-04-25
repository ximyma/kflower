import sys, json, sqlite3
db = sqlite3.connect('kflower-backend/kflower-data/kflower.db')
app = db.execute('SELECT id, name, config FROM applications WHERE id=1').fetchone()
config = json.loads(app[2])
dashboard = config.get('dashboard', {})
pages = dashboard.get('pages', [])
for page in pages:
    name = page.get('name', '?')
    print(f'Page: {name}')
    for w in page.get('widgets', []):
        ds = w.get('data_source', {})
        tid = ds.get('template_id')
        print(f'  Widget: {w["i"]} type={w["type"]} template_id={tid}')
        print(f'    data_source keys: {list(ds.keys())}')
        # 检查 data_source 是否包含所有必要字段
        required = ['type', 'template_id', 'aggregate', 'field', 'date_range', 'filters']
        missing = [k for k in required if k not in ds]
        if missing:
            print(f'    MISSING keys: {missing}')
        else:
            print(f'    All required keys present')
db.close()
