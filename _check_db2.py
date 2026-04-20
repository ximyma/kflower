import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
db_path = r'E:\kkflower\kflower-backend\kflower.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'knowledge%'")
for r in cursor.fetchall():
    print(f'Table: {r[0]}')
    cursor2 = conn.cursor()
    cursor2.execute(f"PRAGMA table_info({r[0]})")
    for col in cursor2.fetchall():
        print(f'  {col[1]}: {col[2]}')
conn.close()
