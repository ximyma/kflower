# -*- coding: utf-8 -*-
"""
Fix countFields - support modules format
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 修复 countFields 函数
old_func = '''function countFields(fields: any) {
  if (!fields) return 0
  if (Array.isArray(fields)) return fields.length
  try { return JSON.parse(fields).length } catch { return 0 }
}'''

new_func = '''function countFields(fields: any) {
  if (!fields) return 0
  // 如果是 modules 格式
  if (Array.isArray(fields) && fields.length > 0 && fields[0].fields) {
    let count = 0
    for (const mod of fields) {
      if (mod.fields && Array.isArray(mod.fields)) count += mod.fields.length
    }
    return count
  }
  if (Array.isArray(fields)) return fields.length
  try { return JSON.parse(fields).length } catch { return 0 }
}'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print('Fixed countFields: support modules format')
else:
    print('Pattern not found')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('Done')
