import sqlite3
conn = sqlite3.connect('kflower.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for row in cursor.fetchall():
    print(f'  {row[0]}')
conn.close()
