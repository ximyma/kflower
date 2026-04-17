# -*- coding: utf-8 -*-
"""
Fix saveTemplate - send fields as modules format
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到 saveTemplate 函数中的 API 调用
old_create = "const res: any = await templateAPI.create({ name:currentTemplate.name, code:currentTemplate.code, description:currentTemplate.description, category:currentTemplate.category, fields:fieldsToSave })"

# 改为发送 modules 格式
new_create = "const res: any = await templateAPI.create({ name:currentTemplate.name, code:currentTemplate.code, description:currentTemplate.description, category:currentTemplate.category, modules:[{name:'main', label:'主表单', fields:fieldsToSave}] })"

if old_create in content:
    content = content.replace(old_create, new_create)
    print('Fixed create API call: fields -> modules')
else:
    print('Create pattern not found, checking...')
    idx = content.find('templateAPI.create')
    if idx > 0:
        print(f'Found at {idx}')
        print(content[idx:idx+300])

# 同样修复 update 调用
old_update = "await templateAPI.update(currentTemplate.id, { name:currentTemplate.name, code:currentTemplate.code, description:currentTemplate.description, category:currentTemplate.category, fields:fieldsToSave })"
new_update = "await templateAPI.update(currentTemplate.id, { name:currentTemplate.name, code:currentTemplate.code, description:currentTemplate.description, category:currentTemplate.category, modules:[{name:'main', label:'主表单', fields:fieldsToSave}] })"

if old_update in content:
    content = content.replace(old_update, new_update)
    print('Fixed update API call: fields -> modules')
else:
    print('Update pattern not found')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('Done')
