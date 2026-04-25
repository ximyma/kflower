"""直接测试 INSERT 语句"""
import sqlite3, json

conn = sqlite3.connect('kflower-backend/kflower-data/kflower.db')
c = conn.cursor()

# 模拟提交的数据
data = {
    'field': '测试村',
    'quantity': 10,
    'field_1': 5000,
    'field_2': 250,
    'field_3': 750,
    'field_4': 500,
    'field_5': 600,
    'field_6': 5400,
    'remark': '测试'
}

# 构建 INSERT
columns = ['template_id', 'created_by']
placeholders = ['?', '?']
values = [15, 1]

for field_name, value in data.items():
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
    if safe_name[0].isdigit():
        safe_name = 'f_' + safe_name
    columns.append(f'"{safe_name}"')
    placeholders.append('?')
    processed = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
    values.append(processed)

insert_sql = f"INSERT INTO form_data_15 ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
print('SQL:', insert_sql)
print('Values:', values)

try:
    c.execute(insert_sql, values)
    conn.commit()
    print('SUCCESS: row inserted')
except Exception as e:
    print('ERROR:', e)
    conn.rollback()
finally:
    conn.close()
