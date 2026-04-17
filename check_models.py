# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Knowledge.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Find where these arrays are populated
for var in ['apiEmbeddingModels', 'localEmbeddingModels', 'rerankModels']:
    i = c.find(f'{var}.value')
    if i > 0:
        start = c.rfind('const ', max(0, i-500), i)
        end = c.find('\n', i)
        print(f"=== {var} ===")
        print(c[start:end].strip()[:300])
        print()
    else:
        # Try different pattern
        i2 = c.find(f'const {var}')
        if i2 > 0:
            end2 = c.find('\n', i2 + 10)
            print(f"=== {var} ===")
            print(c[i2:end2].strip()[:200])
            print()