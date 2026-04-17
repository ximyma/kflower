# -*- coding: utf-8 -*-
"""
Fix Settings.vue - remove old availableModels array properly
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到并删除旧的 availableModels 数组定义
# 它应该在 script setup 部分

# 找到所有 const availableModels 出现的位置
import re

# 删除旧的 availableModels 数组定义（带中括号）
pattern = r"const availableModels_OLD = \[[\s\S]*?\]\n"
content = re.sub(pattern, "", content)
print("Removed availableModels_OLD")

# 也删除原始的 availableModels 数组（如果还存在）
pattern2 = r"const availableModels = \[\s*\{[^]]*label[^]]*\}[^]]*\]"
matches = re.findall(pattern2, content)
for m in matches:
    content = content.replace(m, "// availableModels moved to dynamic loading")
    print("Removed old availableModels array")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Done")
