# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Check if showJsonImport is defined
print('showJsonImport defined:', 'const showJsonImport' in c or 'ref(false)' in c and 'showJsonImport' in c)
print('openJsonImport defined:', 'function openJsonImport' in c)
print('importFromJson defined:', 'function importFromJson' in c)
print('jsonInputText defined:', 'const jsonInputText' in c)

# Check dialog presence
print('\nDialog v-models:')
for pattern in ['v-model="showAIHelper"', 'v-model="showJsonImport"', 'v-model=showAIHelper', 'v-model=showJsonImport']:
    pos = c.find(pattern)
    if pos > 0:
        print(f'  Found: {pattern} at {pos}')

# Check JSON dialog definition
json_pos = c.find('<!-- JSON 导入对话框 -->')
if json_pos > 0:
    print('\nJSON dialog found at:', json_pos)
    print(c[json_pos:json_pos+500])
else:
    print('\nJSON dialog NOT found!')
    # Check where it should be
    import_end = c.find('<!-- 数据提交弹窗 -->')
    print('Import section end at:', import_end)
