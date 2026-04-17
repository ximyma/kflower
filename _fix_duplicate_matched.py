# -*- coding: utf-8 -*-
"""
移除重复的 matchedFields 声明和旧代码
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 移除重复的代码块（旧的预设模板匹配逻辑）
old_block = '''    }
    let matchedFields: any[] = []
    for (const [key, fields] of Object.entries(templates)) {
      if (aiPrompt.value.includes(key)) { matchedFields = fields; break }
    }
    // 尝试从 AI 响应中解析 JSON
    let matchedFields: any[] = []'''

new_block = '''    }
    // 尝试从 AI 响应中解析 JSON
    let matchedFields: any[] = []'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("[OK] 重复代码已移除")
else:
    print("[WARN] 未找到重复代码")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("修复完成！")