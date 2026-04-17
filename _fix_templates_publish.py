# -*- coding: utf-8 -*-
"""
完善模板设计模块功能 - 第二部分
1. 添加 JSON 导入对话框模板
2. 添加发布功能
3. 添加删除功能完善
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# =====================================================
# 1. 在模板中添加 JSON 导入对话框
# =====================================================
# 找到 AI 设计对话框结束位置，在其后添加 JSON 导入对话框
old_import_end = '''      </template>
    </el-dialog>

    <!-- 数据提交弹窗 -->'''

new_json_dialog = '''      </template>
    </el-dialog>

    <!-- JSON 导入对话框 -->
    <el-dialog v-model="showJsonImport" title="JSON 导入" width="650px">
      <el-alert type="info" :closable="false" style="margin-bottom:16px">
        <template #title>支持的JSON格式</template>
        <div style="font-size:12px;color:#666;margin-top:4px">
          直接粘贴 JSON 数组或包含 JSON 的 Markdown 代码块。示例：<br/>
          <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px">
            [{"type":"text","label":"名称","name":"name","required":true}]
          </code>
        </div>
      </el-alert>
      <el-input
        v-model="jsonInputText"
        type="textarea"
        :rows="12"
        placeholder='粘贴 JSON 内容，例如：
[
  {"type":"text","label":"客户名称","name":"customer_name","required":true,"width":"100%"},
  {"type":"select","label":"类型","name":"type","options":["A","B","C"]}
]

字段类型：text/textarea/number/date/select/radio/checkbox/email/phone/money/upload等'
      />
      <template #footer>
        <el-button @click="showJsonImport = false">取消</el-button>
        <el-button type="primary" @click="importFromJson">导入</el-button>
      </template>
    </el-dialog>

    <!-- 数据提交弹窗 -->'''

if old_import_end in content:
    content = content.replace(old_import_end, new_json_dialog)
    print("[OK] JSON导入对话框已添加")

# =====================================================
# 2. 添加发布功能
# =====================================================
# 在脚本部分添加发布相关函数
old_save_template = '''async function saveTemplate() {'''

new_publish_func = '''// 发布模板到数据库
const publishing = ref(false)

async function publishTemplate(template?: any) {
  const tpl = template || currentTemplate
  if (!tpl.name) {
    ElMessage.warning('请输入模板名称')
    return
  }
  if (!tpl.fields || tpl.fields.length === 0) {
    ElMessage.warning('请添加表单字段')
    return
  }
  
  publishing.value = true
  try {
    // 构建发布数据
    const publishData = {
      name: tpl.name,
      code: tpl.code || tpl.name.toLowerCase().replace(/\s+/g, '_'),
      description: tpl.description || '',
      category: tpl.category || 'general',
      is_published: true,
      modules: [{
        name: 'main',
        fields: tpl.fields.map((f: any) => ({
          type: f.type,
          label: f.label,
          name: f.name,
          required: f.required,
          width: f.width,
          options: f.options || [],
          placeholder: f.placeholder || ''
        }))
      }]
    }
    
    // 调用后端发布 API
    const res = await templateAPI.saveTemplate(tpl.id, publishData)
    
    if (res.success) {
      ElMessage.success('模板已发布，可正常使用')
      await loadTemplates()
    } else {
      ElMessage.error(res.message || '发布失败')
    }
  } catch (e: any) {
    console.error('发布失败:', e)
    ElMessage.error(e.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

async function saveTemplate() {'''

if old_save_template in content:
    content = content.replace(old_save_template, new_publish_func)
    print("[OK] 发布功能已添加")

# 3. 在设计器工具栏中添加发布按钮
old_toolbar = '''        <div class="toolbar-right">
          <el-button @click="previewTemplate"><el-icon><View /></el-icon> 预览</el-button>
          <el-button type="primary" @click="saveTemplate"><el-icon><Select /></el-icon> 保存</el-button>'''

new_toolbar = '''        <div class="toolbar-right">
          <el-button @click="previewTemplate"><el-icon><View /></el-icon> 预览</el-button>
          <el-button @click="saveTemplate"><el-icon><Select /></el-icon> 保存</el-button>
          <el-button type="success" @click="publishTemplate" :loading="publishing"><el-icon><Promotion /></el-icon> 发布</el-button>'''

if old_toolbar in content:
    content = content.replace(old_toolbar, new_toolbar)
    print("[OK] 发布按钮已添加到设计器工具栏")

# 4. 在模板卡片菜单中添加发布选项
old_dropdown = '''                  <el-dropdown-item divided @click.stop="deleteTemplate(t)"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>'''

new_dropdown = '''                  <el-dropdown-item @click.stop="publishTemplate(t)"><el-icon><Promotion /></el-icon> 发布</el-dropdown-item>
                  <el-dropdown-item divided @click.stop="deleteTemplate(t)"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>'''

if old_dropdown in content:
    content = content.replace(old_dropdown, new_dropdown)
    print("[OK] 发布选项已添加到模板菜单")

# 5. 添加 Promotion 图标导入
old_icons = "import { Plus, Search, Upload, MagicStick"
new_icons = "import { Plus, Search, Upload, MagicStick, Promotion"

if old_icons in content:
    content = content.replace(old_icons, new_icons)
    print("[OK] Promotion 图标已导入")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\nTemplates.vue 第二部分修复完成！")