# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Find AI helper dialog
ai_dialog_start = c.find('<el-dialog v-model="showAIHelper"')
ai_dialog_end = c.find('</el-dialog>', ai_dialog_start)
print('AI dialog: {} to {}'.format(ai_dialog_start, ai_dialog_end))
if ai_dialog_end > 0:
    print(c[ai_dialog_start:ai_dialog_end+12])