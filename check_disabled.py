# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Knowledge.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Check for disabled attribute on model selects
for field in ['embedding_model', 'rerank_model']:
    i = c.find('v-model="createKBForm.' + field + '"')
    if i > 0:
        # Check around the el-select for disabled
        start = c.rfind('<el-select', 0, i)
        has_disabled = ':disabled' in c[start:i+50] or 'disabled=' in c[start:i+50]
        print(f'{field}: disabled={has_disabled}')
    else:
        print(f'{field}: not found')