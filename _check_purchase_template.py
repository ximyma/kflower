"""检查"货物采购单"模板和动态表"""
import sqlite3
import os

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
if not os.path.exists(db_path):
    print(f"数据库不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查找"货物采购单"模板
print('=== 查找"货物采购单"模板 ===')
cursor.execute('''
    SELECT id, name, code, is_published, category, created_at, updated_at 
    FROM templates 
    WHERE name LIKE '%采购%' OR name LIKE '%货物%'
    ORDER BY id DESC
''')
templates = cursor.fetchall()
for row in templates:
    print(f'ID: {row[0]}, 名称: {row[1]}, 编码: {row[2]}, 已发布: {row[3]}, 分类: {row[4]}, 创建: {row[5]}, 更新: {row[6]}')

# 查找所有模板
print()
print('=== 所有模板（最近10个）===')
cursor.execute('SELECT id, name, code, is_published FROM templates ORDER BY id DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, 名称: {row[1]}, 编码: {row[2]}, 已发布: {row[3]}')

# 检查动态数据表
print()
print('=== 动态表单数据表 ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_data_%' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    print(f'  {t[0]}')
print(f'共 {len(tables)} 个表单数据表')

conn.close()
