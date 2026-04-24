"""检查应用菜单表结构和数据"""
import sqlite3

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查 app_menus 表结构
print("=== app_menus 表结构 ===")
cursor.execute("PRAGMA table_info(app_menus)")
for col in cursor.fetchall():
    print(f"  {col[1]}: {col[2]}")

print()

# 检查所有应用菜单
print("=== 所有应用菜单 ===")
cursor.execute("SELECT * FROM app_menus")
rows = cursor.fetchall()
if not rows:
    print("  (空)")
else:
    cursor.execute("PRAGMA table_info(app_menus)")
    cols = [col[1] for col in cursor.fetchall()]
    print(f"  列: {cols}")
    for row in rows:
        print(f"  {row}")

print()

# 检查最新的应用详情
print("=== 最新应用详情 ===")
cursor.execute("""
    SELECT a.id, a.name, a.is_published, a.created_at,
           COUNT(am.id) as menu_count
    FROM applications a
    LEFT JOIN app_menus am ON a.id = am.app_id
    GROUP BY a.id
    ORDER BY a.created_at DESC
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, 名称: {row[1]}, 已发布: {row[2]}, 创建: {row[3]}, 菜单数: {row[4]}")

conn.close()
