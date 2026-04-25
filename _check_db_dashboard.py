"""检查数据库中的表单数据表和模板信息"""
import sqlite3

conn = sqlite3.connect('e:/kkflower/kflower-backend/kflower-data/kflower.db')
cur = conn.cursor()

# 查看所有动态表单表
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_data_%' ORDER BY name")
tables = cur.fetchall()
print('=== 动态表单表 ===')
for t in tables:
    name = t[0]
    cnt = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    print(f'{name}: {cnt} 条记录')
    if cnt > 0:
        # 查看表结构
        cur.execute(f'PRAGMA table_info("{name}")')
        cols = cur.fetchall()
        print(f'  字段: {[c[1] for c in cols]}')
        # 查看前2条数据
        rows = cur.execute(f'SELECT * FROM "{name}" LIMIT 2').fetchall()
        for row in rows:
            print(f'  数据: {dict(zip([c[1] for c in cols], row))}')

# 查看模板
cur.execute('SELECT id, name, is_published, config FROM templates ORDER BY id')
templates = cur.fetchall()
print('\n=== 模板列表 ===')
for t in templates:
    print(f'ID={t[0]}, name={t[1]}, published={t[2]}')
    config = t[3]
    if config and isinstance(config, str) and len(config) > 10:
        import json
        try:
            cfg = json.loads(config)
            modules = cfg.get('modules', [])
            if modules:
                fields = modules[0].get('fields', [])
                print(f'  字段: {[f.get("name") for f in fields]}')
        except:
            pass

# 查看应用
cur.execute('SELECT id, name, config FROM applications ORDER BY id')
apps = cur.fetchall()
print('\n=== 应用列表 ===')
for a in apps:
    config = a[2]
    has_dashboard = False
    if config and isinstance(config, str):
        import json
        try:
            cfg = json.loads(config)
            if 'dashboard' in cfg:
                has_dashboard = True
                pages = cfg['dashboard'].get('pages', [])
                w_count = sum(len(p.get('widgets', [])) for p in pages)
                print(f'ID={a[0]}, name={a[1]}, 有仪表盘({len(pages)}页, {w_count}个组件)')
        except:
            pass
    if not has_dashboard:
        print(f'ID={a[0]}, name={a[1]}, 无仪表盘')

conn.close()
