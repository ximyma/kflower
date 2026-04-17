# -*- coding: utf-8 -*-
"""
Fix openDesigner - extract fields from modules
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到 openDesigner 函数中解析 fields 的部分
old_parse = '''  let fields: any[] = []
  if (t.fields) { try { fields = typeof t.fields === 'string' ? JSON.parse(t.fields) : t.fields } catch {} }
  currentTemplate.fields = fields.map(f => ({...f, _key: 'field_'+Math.random().toString(36).slice(2), optionsText: Array.isArray(f.options) ? f.options.join(',') : '' }))'''

# 改为从 modules 中提取 fields
new_parse = '''  let fields: any[] = []
  // 优先从 modules 中提取 fields
  if (t.modules && Array.isArray(t.modules)) {
    for (const mod of t.modules) {
      if (mod.fields && Array.isArray(mod.fields)) {
        fields = fields.concat(mod.fields)
      }
    }
  }
  // 兼容旧格式：直接存储的 fields
  if (fields.length === 0 && t.fields) { 
    try { fields = typeof t.fields === 'string' ? JSON.parse(t.fields) : t.fields } catch {} 
  }
  currentTemplate.fields = fields.map(f => ({...f, _key: 'field_'+Math.random().toString(36).slice(2), optionsText: Array.isArray(f.options) ? f.options.join(',') : '' }))'''

if old_parse in content:
    content = content.replace(old_parse, new_parse)
    print('Fixed openDesigner: extract fields from modules')
else:
    print('Pattern not found, checking...')
    idx = content.find('let fields: any[]')
    if idx > 0:
        print(f'Found at {idx}')
        print(content[idx:idx+400])

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('Done')
