"""修复数据库中双重编码的 config"""
import json, sqlite3

conn = sqlite3.connect(r'e:\kkflower\kflower-backend\kflower-data\kflower.db')
cur = conn.execute('SELECT id, config FROM applications')
for row in cur.fetchall():
    app_id = row[0]
    raw = row[1]
    if raw is None:
        continue
    # 检查是否双重编码：先 json.loads 一次看是不是字符串
    try:
        first_pass = json.loads(raw)
        if isinstance(first_pass, str):
            # 双重编码，需要再解析一次
            second_pass = json.loads(first_pass)
            # 保存为单层 JSON 字符串
            single = json.dumps(second_pass, ensure_ascii=False)
            conn.execute('UPDATE applications SET config = ? WHERE id = ?', (single, app_id))
            print(f'Fixed app {app_id}: double-encoded -> single JSON string')
        elif isinstance(first_pass, dict):
            # 已经是 dict，SQLAlchemy 存的时候加了外层引号
            single = json.dumps(first_pass, ensure_ascii=False)
            conn.execute('UPDATE applications SET config = ? WHERE id = ?', (single, app_id))
            print(f'Fixed app {app_id}: quoted dict -> plain JSON string')
        else:
            print(f'App {app_id}: config is {type(first_pass).__name__}, no fix needed')
    except json.JSONDecodeError:
        print(f'App {app_id}: config is not valid JSON, skipping')

conn.commit()
conn.close()
print('Done')
