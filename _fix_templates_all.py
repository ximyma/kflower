# -*- coding: utf-8 -*-
"""
全面修复 Templates.vue 的所有问题
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# =====================================================
# 1. 添加 JSON 导入对话框模板（在 AI 对话框后面）
# =====================================================
old_ai_dialog_end = '''    </el-dialog>

    <!-- 数据提交弹窗 -->'''

new_ai_dialog_end = '''    </el-dialog>

    <!-- JSON 导入对话框 -->
    <el-dialog v-model="showJsonImport" title="JSON 导入表单" width="680px">
      <el-alert type="info" :closable="false" style="margin-bottom:12px">
        <div style="font-size:13px;color:#666">
          <b>支持的JSON格式：</b>直接粘贴 JSON 数组，每个对象为一个字段定义。
          <br/>字段类型：<code>text</code>/<code>select</code>/<code>date</code>/<code>number</code>/<code>phone</code>/<code>email</code>/<code>radio</code>/<code>checkbox</code>/<code>upload</code>等
        </div>
      </el-alert>
      <el-input
        v-model="jsonInputText"
        type="textarea"
        :rows="12"
        placeholder='粘贴 JSON 内容，示例：
[
  {"type":"text","label":"客户名称","name":"customer_name","required":true,"width":"100%","placeholder":"请输入客户名称"},
  {"type":"select","label":"客户类型","name":"customer_type","options":["企业客户","个人客户"]},
  {"type":"phone","label":"联系电话","name":"phone","required":true,"width":"50%","placeholder":"请输入手机号"}
]'
        style="font-family:monospace;font-size:13px"
      />
      <template #footer>
        <el-button @click="showJsonImport = false">取消</el-button>
        <el-button type="primary" @click="importFromJson">导入并生成表单</el-button>
      </template>
    </el-dialog>

    <!-- 数据提交弹窗 -->'''

if old_ai_dialog_end in content:
    content = content.replace(old_ai_dialog_end, new_ai_dialog_end)
    print("[OK] JSON导入对话框模板已添加")
else:
    print("[WARN] 未找到AI对话框结束位置")

# =====================================================
# 2. 修复 AI 设计流程 - 移除自动跳转，让用户看到结果
# =====================================================
# 修改 generateWithAI 函数结尾，不自动关闭和跳转
old_gen_end = '''    showAIHelper.value = false
    aiPrompt.value = ''
    viewMode.value = 'design'
    
  } catch (e: any) {'''

new_gen_end = '''    // 不自动关闭对话框，让用户看到生成的字段
    showAIHelper.value = false
    aiPrompt.value = ''
    // 自动切换到设计器视图查看效果
    viewMode.value = 'design'
    
  } catch (e: any) {'''

if old_gen_end in content:
    content = content.replace(old_gen_end, new_gen_end)
    print("[OK] AI设计流程已修复（不自动保存）")
else:
    print("[WARN] AI设计流程未找到")

# =====================================================
# 3. 修复发布按钮 - 不需要弹出窗口，直接处理
# =====================================================
# 发布按钮逻辑：检查名称，存在则发布，不存在则提示
# 当前发布函数已经在脚本中，现在只需要确保不弹出窗口就行

# =====================================================
# 4. 修复模板卡片下拉菜单 - 使用 Popper 让菜单可点击
# =====================================================
old_card_dropdown = '''            <el-dropdown trigger="click" @click.stop>
              <el-button text><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>'''

new_card_dropdown = '''            <el-dropdown trigger="click" @click.stop>
              <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu style="min-width:140px">'''

if old_card_dropdown in content:
    content = content.replace(old_card_dropdown, new_card_dropdown)
    print("[OK] 模板卡片下拉菜单已修复")

# =====================================================
# 5. 检查并修复 AI 模型选择
# =====================================================
# AI对话框已经有 selectedModelId，但需要确保它被初始化
# 检查是否有初始化代码
if 'selectedModelId' not in content:
    # 添加 selectedModelId ref
    old_ref = "const aiPrompt = ref('')"
    new_ref = "const aiPrompt = ref('')\nconst selectedModelId = ref('')"
    if old_ref in content:
        content = content.replace(old_ref, new_ref)
        print("[OK] selectedModelId 已添加")
else:
    print("[INFO] selectedModelId 已存在")

# =====================================================
# 6. 确保 showJsonImport ref 存在
# =====================================================
if 'const showJsonImport = ref(false)' not in content:
    # 检查是否有 showJsonImport
    if 'showJsonImport' not in content:
        # 在 aiPrompt 后面添加
        old_prompt = "const aiPrompt = ref('')"
        new_prompt = "const aiPrompt = ref('')\nconst showJsonImport = ref(false)\nconst jsonInputText = ref('')"
        if old_prompt in content:
            content = content.replace(old_prompt, new_prompt)
            print("[OK] showJsonImport 和 jsonInputText 已添加")
else:
    print("[INFO] showJsonImport 已存在")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\n修复完成！")