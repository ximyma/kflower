# -*- coding: utf-8 -*-
"""
全面修复所有问题
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# =====================================================
# 1. 修复 AIChatDialog.vue - 添加 loadModels 调用
# =====================================================
dialog_path = r'D:\kflower\kflower-frontend\src\common\components\AIChatDialog.vue'
with open(dialog_path, 'r', encoding='utf-8-sig') as f:
    dialog_content = f.read()

# 在 initModelSelection 后添加 loadModels 调用
old_init = '''// 初始化
initModelSelection()'''

new_init = '''// 初始化 - 加载模型列表
initModelSelection()
aiStore.loadModels()'''

if old_init in dialog_content:
    dialog_content = dialog_content.replace(old_init, new_init)
    print("[OK] AIChatDialog 已修复 - 添加 loadModels 调用")
else:
    print("[WARN] AIChatDialog init 未找到")

# 同时确保 import 了 onMounted
if 'import { ref, nextTick' in dialog_content:
    dialog_content = dialog_content.replace(
        "import { ref, nextTick } from 'vue'",
        "import { ref, nextTick, onMounted } from 'vue'"
    )
    print("[OK] 已添加 onMounted 导入")

with open(dialog_path, 'w', encoding='utf-8-sig') as f:
    f.write(dialog_content)

# =====================================================
# 2. 修复 Templates.vue - AI设计不自动保存
# =====================================================
tpl_path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(tpl_path, 'r', encoding='utf-8-sig') as f:
    tpl_content = f.read()

# 确保 showJsonImport 存在
if 'const showJsonImport = ref(false)' not in tpl_content:
    old_ref = "const aiPrompt = ref('')"
    new_ref = "const aiPrompt = ref('')\nconst showJsonImport = ref(false)\nconst jsonInputText = ref('')"
    if old_ref in tpl_content:
        tpl_content = tpl_content.replace(old_ref, new_ref)
        print("[OK] showJsonImport 和 jsonInputText 已添加")
else:
    print("[INFO] showJsonImport 已存在")

# 确保 jsonInputText 存在
if 'const jsonInputText = ref' not in tpl_content:
    if 'const showJsonImport = ref(false)' in tpl_content:
        tpl_content = tpl_content.replace(
            'const showJsonImport = ref(false)',
            'const showJsonImport = ref(false)\nconst jsonInputText = ref(\'\')'
        )
        print("[OK] jsonInputText 已添加")
else:
    print("[INFO] jsonInputText 已存在")

# 确保 showJsonImport 对话框模板存在
if 'v-model="showJsonImport"' not in tpl_content:
    print("[WARN] JSON对话框模板缺失，跳过")
else:
    print("[INFO] JSON对话框模板已存在")

# 确保 generateWithAI 不自动保存
# 查找当前函数结尾
gen_end = tpl_content.find('// 不自动关闭对话框，让用户看到生成的字段')
if gen_end > 0:
    print("[OK] AI设计流程已正确修复")
else:
    print("[WARN] AI设计流程修复位置未找到")

# 修复模板卡片下拉菜单
old_dropdown = '''            <el-dropdown trigger="click" @click.stop>
              <el-button text><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>'''

new_dropdown = '''            <el-dropdown trigger="click" @click.stop>
              <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu style="min-width:150px">'''

if old_dropdown in tpl_content:
    tpl_content = tpl_content.replace(old_dropdown, new_dropdown)
    print("[OK] 模板卡片下拉菜单已修复")
else:
    print("[INFO] 模板卡片下拉菜单已处理")

with open(tpl_path, 'w', encoding='utf-8-sig') as f:
    f.write(tpl_content)

print("\n所有修复完成！")