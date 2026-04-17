# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

print('Script section:')
s = c.find('<script')
e = c.find('</script>')
if s >= 0 and e >= 0:
    print(c[s:e][:3000])
