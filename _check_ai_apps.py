"""检查 AI 生成的应用和数据库表"""
import sqlite3
import os

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
if not os.path.exists(db_path):
    print(f"数据库不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查应用
print('=== 应用列表 ===')
cursor.execute('SELECT id, name, code, is_published, created_at FROM applications ORDER BY id DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, 名称: {row[1]}, 编码: {row[2]}, 已发布: {row[3]}, 创建时间: {row[4]}')

print()
print('=== 模板列表 ===')
cursor.execute('SELECT id, name, code, is_published, category, created_at FROM templates ORDER BY id DESC LIMIT 20')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, 名称: {row[1]}, 编码: {row[2]}, 已发布: {row[3]}, 分类: {row[4]}, 创建: {row[5]}')

print()
print('=== 动态表单数据表 ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_data_%' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    print(f'  {t[0]}')
print(f'共 {len(tables)} 个表单数据表')

print()
print('=== 应用菜单 ===')
cursor.execute("""
    SELECT am.id, am.menu_label, am.template_id, t.name, t.code
    FROM app_menus am
    LEFT JOIN templates t ON am.template_id = t.id
    ORDER BY am.id DESC LIMIT 15
""")
for row in cursor.fetchall():
    print(f'菜单ID: {row[0]}, 标签: {row[1]}, 模板ID: {row[2]}, 模板名: {row[3]}, 编码: {row[4]}')

conn.close()
