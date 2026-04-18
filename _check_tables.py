import sqlite3
import json

conn = sqlite3.connect('kflower-backend/kflower-data/kflower.db')
cursor = conn.cursor()

# 查找所有 form_data 开头的表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_data%'")
tables = cursor.fetchall()
print('Form data tables:', [t[0] for t in tables])

# 检查模板的 table_name
cursor.execute('SELECT id, name, config FROM templates LIMIT 10')
for row in cursor.fetchall():
    config = json.loads(row[2]) if row[2] else {}
    table_name = config.get('table_name', 'NOT FOUND')
    print(f'Template {row[0]}: {row[1]}, table_name={table_name}')

conn.close()
