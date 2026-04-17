# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

pos = c.find('v-model="showAIHelper"')
print('AI dialog at:', pos)
end = c.find('</el-dialog>', pos) + 12
print('End at:', end)
print('After:')
print(repr(c[end:end+200]))