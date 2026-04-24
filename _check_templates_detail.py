"""检查模板详细信息"""
import sqlite3

db_path = r"e:\kkflower\kflower-backend\kflower-data\kflower.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查所有模板（按创建时间倒序）
print("=== 所有模板（按创建时间倒序）===")
cursor.execute("""
    SELECT id, name, code, is_published, config, created_at, updated_at
    FROM templates
    ORDER BY created_at DESC
""")
for row in cursor.fetchall():
    template_id, name, code, is_published, config, created_at, updated_at = row
    print(f"ID: {template_id}")
    print(f"  名称: {name}")
    print(f"  编码: {code}")
    print(f"  已发布: {is_published}")
    print(f"  创建: {created_at}")
    print(f"  更新: {updated_at}")
    
    # 解析 config
    import json
    if config:
        try:
            cfg = json.loads(config) if isinstance(config, str) else config
            fields = cfg.get('fields', [])
            print(f"  字段数: {len(fields)}")
        except:
            print(f"  配置解析失败")
    print()

# 检查今天创建的模板
print("=== 今天的模板 ===")
cursor.execute("""
    SELECT id, name, code, is_published, created_at
    FROM templates
    WHERE date(created_at) = date('now')
    ORDER BY created_at DESC
""")
rows = cursor.fetchall()
if not rows:
    print("  今天没有创建新模板")
else:
    for row in rows:
        print(f"ID: {row[0]}, 名称: {row[1]}, 已发布: {row[3]}, 创建: {row[4]}")

conn.close()
