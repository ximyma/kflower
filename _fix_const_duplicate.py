# -*- coding: utf-8 -*-
"""
修复 Settings.vue - 移除重复的 const saveBasicSettings
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 查找并移除 const saveBasicSettings 声明
import re

# 模式: const saveBasicSettings = () => ... 或 const saveBasicSettings = ...
pattern = r"const saveBasicSettings = [^\n]+\n"
matches = list(re.finditer(pattern, content))
print(f"Found {len(matches)} const saveBasicSettings declarations")

for m in matches:
    print(f"  Removing: {m.group().strip()[:60]}...")
    
content = re.sub(pattern, '', content)

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\n修复完成！")