import sqlite3
conn = sqlite3.connect('E:/kkflower/kflower-backend/kflower-data/kflower.db')

# Check roles columns
cur = conn.execute('PRAGMA table_info(roles)')
cols = [r[1] for r in cur.fetchall()]
print('Current roles cols:', cols)
print('Has data_permission_rules:', 'data_permission_rules' in cols)

if 'data_permission_rules' not in cols:
    conn.execute("ALTER TABLE roles ADD COLUMN data_permission_rules TEXT DEFAULT '[]'")
    conn.commit()
    print('Column data_permission_rules added!')

# Verify
cur2 = conn.execute('PRAGMA table_info(roles)')
cols2 = [r[1] for r in cur2.fetchall()]
print('After migration:', cols2)

conn.close()
