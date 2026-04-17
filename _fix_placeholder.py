# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    c = f.read()

# Find the problematic placeholder line
old_ph = 'placeholder="粘贴 JSON 内容，示例：&#10;["&#10;  {\\"type\\":\\"text\\",\\"label\\":\\"客户名称\\",\\"name\\":\\"customer_name\\",\\"required\\":true,\\"width\\":\\"100%\\"},"&#10;  {\\"type\\":\\"select\\",\\"label\\":\\"类型\\",\\"name\\":\\"type\\",\\"options\\":[\\"A\\",\\"B\\"]}"&#10;]"'
new_ph = 'placeholder=\'粘贴 JSON 数组，例如：[{"type":"text","label":"名称","name":"name"}]\''

print('Looking for old placeholder...')
if old_ph in c:
    c = c.replace(old_ph, new_ph)
    print('Fixed!')
else:
    print('Not found, trying partial match...')
    if '粘贴 JSON 内容' in c:
        # Find and replace just the placeholder
        i = c.find('v-model="jsonInputText"')
        if i > 0:
            end = c.find('/>', i)
            if end > 0:
                old_line = c[i:end+2]
                print('Found line:', repr(old_line[:100]))
                new_line = 'v-model="jsonInputText"\n        type="textarea"\n        :rows="12"\n        placeholder=\'粘贴 JSON，例如：[{"type":"text","label":"名称","name":"name"}]\'\n        style="font-family:monospace;font-size:13px"'
                # Count the lines to replace
                line_start = c.rfind('\n', 0, i)
                line_end = c.find('\n', end)
                c = c[:line_start+1] + new_line + '\n      ' + c[line_end+1:]
                print('Fixed via line replacement!')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(c)
print('Done!')
