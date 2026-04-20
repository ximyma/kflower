import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
# Check all .db files
for root, dirs, files in os.walk(r'E:\kkflower\kflower-backend'):
    for f in files:
        if f.endswith('.db'):
            db_path = os.path.join(root, f)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            print(f'{db_path}: {len(tables)} tables')
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
                cnt = cursor.fetchone()[0]
                print(f'  {t}: {cnt} rows')
            conn.close()
