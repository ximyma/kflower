# -*- coding: utf-8 -*-
"""
修复重复的 async 关键字
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 修复重复的 async
content = content.replace('async async function generateWithAI()', 'async function generateWithAI()')

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("修复完成！")