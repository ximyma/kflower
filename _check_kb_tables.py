import sqlite3
for db in [r'E:\kkflower\kflower-backend\kflower.db', r'E:\kkflower\kflower-backend\knmerp.db']:
    print(f"\n=== {db} ===")
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        for t in tables:
            if 'knowledge' in t.lower() or 'tag' in t.lower() or 'note' in t.lower():
                print(f"  {t}")
                cursor.execute(f"PRAGMA table_info({t})")
                for col in cursor.fetchall():
                    print(f"    {col[1]} {col[2]}")
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
