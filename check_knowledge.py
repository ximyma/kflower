# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'D:\kflower\kflower-frontend\src\common\pc\views\Knowledge.vue', 'r', encoding='utf-8-sig')
c = f.read()
f.close()

# Find createKBForm.embedding_model section
i = c.find('createKBForm.embedding_model')
if i > 0:
    # Find the el-select before it
    start = c.rfind('<el-select', 0, i)
    end = c.find('</el-select>', i) + 11
    print("=== Embedding model select ===")
    print(c[start:end])
    print()

# Find createKBForm.rerank_model section  
i2 = c.find('createKBForm.rerank_model')
if i2 > 0:
    start2 = c.rfind('<el-select', 0, i2)
    end2 = c.find('</el-select>', i2) + 11
    print("=== Rerank model select ===")
    print(c[start2:end2])