# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Knowledge.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Find where loadEmbeddingModels is called
calls = []
for i, line in enumerate(c.split('\n'), 1):
    if 'loadEmbeddingModels' in line and (';' in line or 'await' in line):
        calls.append((i, line.strip()))
        
for i, line in calls:
    print(f"Line {i}: {line}")