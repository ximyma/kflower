"""检查 AI 设计助手生成的最新应用和模板"""
import sqlite3

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查最新的应用（按创建时间排序）
print("=== 应用列表（最新）===")
cursor.execute("""
    SELECT id, name, code, is_published, created_at
    FROM applications
    ORDER BY created_at DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, 名称: {row[1]}, 编码: {row[2]}, 已发布: {row[3]}, 创建: {row[4]}")

print()

# 检查最新的模板
print("=== 模板列表（最新）===")
cursor.execute("""
    SELECT id, name, code, is_published, category, created_at
    FROM templates
    ORDER BY created_at DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, 名称: {row[1]}, 编码: {row[2]}, 已发布: {row[3]}, 分类: {row[4]}, 创建: {row[5]}")

print()

# 检查动态数据表
print("=== 动态数据表 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_data_%' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    print(f"  {t[0]}")
print(f"共 {len(tables)} 个数据表")

print()

# 检查 app_menus（应用菜单关联）
print("=== 应用菜单 ===")
cursor.execute("""
    SELECT am.id, am.menu_label, am.template_id, am.app_id, t.name, t.is_published
    FROM app_menus am
    LEFT JOIN templates t ON am.template_id = t.id
    ORDER BY am.id DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"菜单ID: {row[0]}, 标签: {row[1]}, 模板ID: {row[2]}, 应用ID: {row[3]}, 模板名: {row[4]}, 已发布: {row[5]}")

conn.close()
