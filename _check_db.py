import sqlite3
conn = sqlite3.connect('E:/kkflower/kflower-backend/kflower-data/kflower.db')
cur = conn.cursor()

# Check all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [r[0] for r in cur.fetchall()])

# Check roles columns
cur.execute("PRAGMA table_info(roles)")
print('roles columns:')
for row in cur.fetchall():
    print(' ', row)

# Check users columns
cur.execute("PRAGMA table_info(users)")
print('users columns:')
for row in cur.fetchall():
    print(' ', row)

conn.close()
