# -*- coding: utf-8 -*-
"""
修复 Settings.vue - 移除重复的函数定义
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到所有 async function saveBasicSettings 的位置
import re
matches = list(re.finditer(r'async function saveBasicSettings', content))
print(f"Found {len(matches)} saveBasicSettings functions")

if len(matches) > 1:
    # 保留第一个，删除后续的
    # 找到第二个函数的范围并删除
    first_end = matches[0].start()
    
    # 找到第二个函数的开始和结束
    second_start = matches[1].start()
    # 找到第二个函数的结束（下一个 async function 或文件结束）
    next_func = content.find('async function', second_start + 10)
    if next_func > 0:
        second_end = next_func
    else:
        second_end = len(content)
    
    # 删除第二个函数
    content = content[:second_start] + content[second_end:]
    print(f"[OK] Removed duplicate saveBasicSettings at position {second_start}")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\n修复完成！")