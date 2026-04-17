# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix header - move title to separate line above actions
old_header = '''    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-title">
        <el-icon :size="20"><MagicStick /></el-icon>
        <span>AI 智能助手</span>
      </div>
      <div class="header-actions">'''

new_header = '''    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-title-row">
        <el-icon :size="20"><MagicStick /></el-icon>
        <span class="header-title-text">AI 智能助手</span>
      </div>
      <div class="header-actions">'''

count = content.count(old_header)
print(f"Header replacement: found {count}")
if count == 1:
    content = content.replace(old_header, new_header)

# Fix CSS - add new styles for title row
old_css = '''.header-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; }'''

new_css = '''.header-title-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 600; margin-bottom: 8px;
}
.header-title-text { letter-spacing: 2px; }
.header-actions { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }'''

if old_css in content:
    content = content.replace(old_css, new_css)
    print("[OK] CSS updated")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Header fixed!")