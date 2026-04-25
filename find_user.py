import sqlite3
conn = sqlite3.connect(r'E:\kkflower\kflower-backend\kflower-data\kflower.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, username, email FROM users LIMIT 5")
for u in cur.fetchall():
    print(f"User: id={u['id']}, username={u['username']}, email={u['email']}")
conn.close()
