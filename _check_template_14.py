"""检查模板14的配置详情"""
import sqlite3
import json

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 获取模板详情
cursor.execute('SELECT * FROM templates WHERE id = 14')
template = dict(cursor.fetchone())
print('=== 模板14详情 ===')
print(f'ID: {template["id"]}')
print(f'名称: {template["name"]}')
print(f'编码: {template["code"]}')
print(f'已发布: {template["is_published"]}')
print()

# 解析 modules
print('=== modules 配置 ===')
if template.get('modules'):
    try:
        modules = json.loads(template['modules'])
        print(json.dumps(modules, indent=2, ensure_ascii=False))
    except:
        print(template['modules'])
else:
    print('(无)')

print()
print('=== config 配置 ===')
if template.get('config'):
    try:
        config = json.loads(template['config'])
        print(json.dumps(config, indent=2, ensure_ascii=False))
    except:
        print(template['config'])
else:
    print('(无)')

# 检查动态表结构
print()
print('=== form_data_14 表结构 ===')
cursor.execute("PRAGMA table_info(form_data_14)")
for col in cursor.fetchall():
    print(f'  {col["name"]}: {col["type"]}')

conn.close()
