"""检查数据库结构"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'kflower-backend', 'kflower-data', 'kflower.db')
print(f"数据库路径: {db_path}")
print(f"文件存在: {os.path.exists(db_path)}")

conn = sqlite3.connect(db_path)
# 列出所有表
r = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = r.fetchall()
print(f"\n所有表 ({len(tables)}):")
for t in tables:
    print(f"  {t[0]}")

# 检查 form_data_15
r = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='form_data_15'")
if r.fetchone():
    r = conn.execute('PRAGMA table_info(form_data_15)')
    print("\nform_data_15 列:")
    for row in r.fetchall():
        print(f"  cid={row[0]}, name={row[1]}, type={row[2]}, notnull={row[3]}, dflt={row[4]}, pk={row[5]}")
else:
    print("\nform_data_15 表不存在!")

conn.close()
