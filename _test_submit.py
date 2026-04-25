"""模拟后端提交数据流程"""
import json
import sys
sys.path.insert(0, 'kflower-backend')

from app.core.formula_engine import formula_engine

# 模拟前端提交的数据（包含公式计算后的值）
data = {
    'field': '张三',
    'quantity': 3,
    'field_1': 5000,
    'field_2': 200,
    'field_3': 750.0,   # 公式计算结果
    'field_4': 500.0,   # 公式计算结果
    'field_5': 300,      # 公式计算结果
}

# 模拟从数据库读取的字段定义（包含 formula）
fields = [
    {'type': 'text', 'label': '姓名', 'name': 'field'},
    {'type': 'number', 'label': '人数', 'name': 'quantity'},
    {'type': 'number', 'label': '工资总额', 'name': 'field_1'},
    {'type': 'number', 'label': '预留廉政', 'name': 'field_2'},
    {'type': 'number', 'label': '月度绩效考核（15%）', 'name': 'field_3', 'formula': '{field_1}*0.15'},
    {'type': 'number', 'label': '年度绩效考核（10%）', 'name': 'field_4', 'formula': '{field_1}*0.10'},
    {'type': 'number', 'label': '扣养老保险个人部分', 'name': 'field_5', 'formula': '{field_1}*0.06'},
]

# 模拟 submit_template_data 中的公式计算逻辑
main_data = dict(data)
try:
    computed = formula_engine.compute_form(main_data, fields, None)
    main_data.update(computed)
    print(f'公式计算结果: {computed}')
    print(f'最终数据: {main_data}')
except Exception as e:
    print(f'公式计算错误: {e}')
    import traceback
    traceback.print_exc()

# 模拟构建 INSERT 语句
name_to_safe = {}
for field_name in main_data.keys():
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
    if safe_name[0].isdigit():
        safe_name = 'f_' + safe_name
    name_to_safe[field_name] = safe_name

columns = ['template_id', 'created_by']
placeholders = [':template_id', ':created_by']
values = {'template_id': 15, 'created_by': 1}

for field_name, value in main_data.items():
    safe_name = name_to_safe.get(field_name, field_name)
    columns.append(f'"{safe_name}"')
    placeholders.append(f':{safe_name}')
    values[safe_name] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value

print(f'\nColumns: {columns}')
print(f'Values: {values}')
