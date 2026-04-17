# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()
funcs = ['loadBasicSettings', 'loadModuleAISettings', 'loadOCRConfig']
for func in funcs:
    exists = ('function ' + func in c) or ('async function ' + func in c)
    print(f'{func}: {exists}')