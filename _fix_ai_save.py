# -*- coding: utf-8 -*-
"""
Fix AI generate - auto switch to designer view and prompt to save
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 修改提示消息
old_msg = "ElMessage.success('已生成表单，请调整后保存')"
new_msg = "ElMessage.success('已生成表单，请点击右侧「保存」按钮')"
if old_msg in content:
    content = content.replace(old_msg, new_msg)
    print('Fixed: 提示消息已更新')

# 2. 修改追加字段的消息
old_msg2 = "ElMessage.success(`已追加 ${newFields.length} 个字段`)"
new_msg2 = "ElMessage.success(`已追加 ${newFields.length} 个字段到画布，请点击保存`)"
if old_msg2 in content:
    content = content.replace(old_msg2, new_msg2)
    print('Fixed: 追加消息已更新')

# 3. 在 AI 生成完成后自动切换到设计器视图
old_switch = "showAIHelper.value = false; aiPrompt.value = ''"
new_switch = """showAIHelper.value = false; aiPrompt.value = ''
    // 自动切换到设计器视图
    if (viewMode.value === 'list') { viewMode.value = 'design' }"""
if old_switch in content and '自动切换到设计器视图' not in content:
    content = content.replace(old_switch, new_switch)
    print('Fixed: 已添加自动切换逻辑')

# 写回文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print('Done: AI 生成后自动切换到设计器并提示保存')
