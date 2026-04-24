"""检查应用设计器相关数据"""
import sqlite3
import os
import json

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查找"货物采购"相关的应用
print('=== 查找"货物采购"应用 ===')
cursor.execute('SELECT * FROM applications ORDER BY id DESC LIMIT 10')
for row in cursor.fetchall():
    app = dict(row)
    print(f'ID: {app["id"]}, 名称: {app["name"]}, 编码: {app["code"]}, 已发布: {app.get("is_published", "N/A")}')
    print(f'  created_at: {app.get("created_at")}')

print()
print('=== 所有应用菜单 ===')
cursor.execute('SELECT * FROM app_menus ORDER BY id DESC LIMIT 20')
for row in cursor.fetchall():
    menu = dict(row)
    print(f'ID: {menu["id"]}, 标签: {menu["menu_label"]}, 模板ID: {menu["template_id"]}, 应用ID: {menu["app_id"]}')

print()
print('=== 模板列表（所有）===')
cursor.execute('SELECT id, name, code, is_published FROM templates ORDER BY id DESC')
for row in cursor.fetchall():
    print(f'ID: {row["id"]}, 名称: {row["name"]}, 编码: {row["code"]}, 已发布: {row["is_published"]}')

conn.close()
