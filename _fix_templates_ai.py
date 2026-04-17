# -*- coding: utf-8 -*-
"""
完善模板设计模块功能
1. AI设计实际调用AI API，使用规范化提示词
2. 新增JSON导入功能
3. 新增发布和删除功能
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# =====================================================
# 1. 替换 generateWithAI 函数 - 实际调用 AI API
# =====================================================
old_generate = '''function generateWithAI() {
  if (!aiPrompt.value.trim()) { ElMessage.warning('请描述您的需求'); return }
  aiLoading.value = true
  try {
    // 预设模板匹配
    const templates: Record<string, any[]> = {'''

new_generate = '''async function generateWithAI() {
  if (!aiPrompt.value.trim()) { ElMessage.warning('请描述您的需求'); return }
  aiLoading.value = true
  try {
    // 调用 AI API 生成表单字段
    const systemPrompt = `你是一个专业的表单设计助手。用户会描述他们需要的表单类型，你需要生成对应的表单字段定义。

**输出要求**：
1. 只输出 JSON 数组格式，不要输出任何其他文字或解释
2. 每个字段对象包含以下属性：
   - type: 字段类型（text/textarea/number/date/datetime/time/select/radio/checkbox/switch/email/phone/url/money/rate/upload/image/richtext/divider/heading）
   - label: 字段标签（中文）
   - name: 字段名称（英文小写下划线）
   - required: 是否必填（true/false）
   - width: 宽度（"50%"或"100%"）
   - options: 选项数组（仅 select/radio/checkbox 需要）
   - placeholder: 占位提示文字

**示例输出**：
[
  {"type":"text","label":"客户名称","name":"customer_name","required":true,"width":"100%","placeholder":"请输入客户名称"},
  {"type":"select","label":"客户类型","name":"customer_type","required":true,"width":"50%","options":["企业客户","个人客户"],"placeholder":"请选择类型"},
  {"type":"phone","label":"联系电话","name":"phone","required":true,"width":"50%","placeholder":"请输入手机号"}
]

请根据用户需求生成合适的表单字段。`

    const userPrompt = aiPrompt.value
    
    // 调用 AI API
    const response = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('kflower_token')
      },
      body: JSON.stringify({
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.7
      })
    })
    
    const result = await response.json()
    
    if (!result.success && !result.data) {
      // 如果 AI 调用失败，使用预设模板
      const templates: Record<string, any[]> = {'''

if old_generate in content:
    content = content.replace(old_generate, new_generate)
    print("[OK] generateWithAI 函数开头已替换")

# =====================================================
# 2. 替换匹配逻辑后的处理 - 解析AI返回的JSON
# =====================================================
old_match_logic = '''    if (!matchedFields.length) {
      matchedFields = [
        { type:'text', label:'名称', name:'name', required:true, width:'50%' },
        { type:'text', label:'编码', name:'code', required:true, width:'50%' },
        { type:'select', label:'类型', name:'type', width:'50%', options:['类型A','类型B','类型C'] },
        { type:'date', label:'日期', name:'date', width:'50%' },
        { type:'textarea', label:'备注', name:'remark', width:'100%' },
      ]
    }'''

new_match_logic = '''    // 尝试从 AI 响应中解析 JSON
    let matchedFields: any[] = []
    
    if (result.data?.content || result.content || result.message) {
      const aiContent = result.data?.content || result.content || result.message || ''
      console.log('AI响应:', aiContent)
      
      // 尝试提取 JSON 数组
      let jsonStr = aiContent
      const jsonMatch = aiContent.match(/\[[\s\S]*\]/)
      if (jsonMatch) {
        jsonStr = jsonMatch[0]
      }
      
      try {
        matchedFields = JSON.parse(jsonStr)
        console.log('解析到字段:', matchedFields.length)
      } catch (e) {
        console.error('JSON解析失败:', e)
        ElMessage.warning('AI返回格式不正确，请重试或使用JSON导入')
        // 使用预设模板
      }
    }
    
    // 如果 AI 没有返回有效数据，使用预设模板匹配
    if (!matchedFields.length) {
      for (const [key, fields] of Object.entries(templates)) {
        if (aiPrompt.value.includes(key)) { matchedFields = fields; break }
      }
    }
    
    // 最后的默认模板
    if (!matchedFields.length) {
      matchedFields = [
        { type:'text', label:'名称', name:'name', required:true, width:'50%', placeholder:'请输入名称' },
        { type:'text', label:'编码', name:'code', required:true, width:'50%', placeholder:'请输入编码' },
        { type:'select', label:'类型', name:'type', width:'50%', options:['类型A','类型B','类型C'], placeholder:'请选择类型' },
        { type:'date', label:'日期', name:'date', width:'50%' },
        { type:'textarea', label:'备注', name:'remark', width:'100%', placeholder:'请输入备注' },
      ]
    }'''

if old_match_logic in content:
    content = content.replace(old_match_logic, new_match_logic)
    print("[OK] AI响应解析逻辑已替换")

# =====================================================
# 3. 添加 JSON 导入对话框
# =====================================================
# 在 showAIHelper 对话框后添加 JSON 导入对话框
old_ai_dialog_end = '''    showAIHelper.value = false; aiPrompt.value = ''
    // 自动切换到设计器视图
    if (viewMode.value === 'list') { viewMode.value = 'design' }
    // 自动保存模板
    await saveTemplate()
  } catch { ElMessage.error('AI生成失败') }
  finally { aiLoading.value = false }
}'''

new_ai_dialog_end = '''    showAIHelper.value = false; aiPrompt.value = ''
    // 自动切换到设计器视图
    if (viewMode.value === 'list') { viewMode.value = 'design' }
    // 不自动保存，让用户确认后再保存
    ElMessage.success(`已生成 ${matchedFields.length} 个字段，请检查后保存`)
  } catch (e: any) {
    console.error('AI生成失败:', e)
    ElMessage.error(e.message || 'AI生成失败')
  }
  finally { aiLoading.value = false }
}

// JSON 导入功能
const showJsonImport = ref(false)
const jsonInputText = ref('')

function openJsonImport() {
  jsonInputText.value = ''
  showJsonImport.value = true
}

function importFromJson() {
  if (!jsonInputText.value.trim()) {
    ElMessage.warning('请输入 JSON 内容')
    return
  }
  
  try {
    // 尝试解析 JSON
    let jsonStr = jsonInputText.value.trim()
    
    // 如果是 Markdown 代码块，提取其中的 JSON
    const codeBlockMatch = jsonStr.match(/```(?:json)?\\s*([\\s\\S]*?)```/)
    if (codeBlockMatch) {
      jsonStr = codeBlockMatch[1].trim()
    }
    
    // 提取 JSON 数组
    const arrayMatch = jsonStr.match(/\\[[\\s\\S]*\\]/)
    if (arrayMatch) {
      jsonStr = arrayMatch[0]
    }
    
    const fields = JSON.parse(jsonStr)
    
    if (!Array.isArray(fields)) {
      ElMessage.error('JSON 格式错误：需要数组格式')
      return
    }
    
    // 转换字段格式
    const newFields = fields.map((f: any, idx: number) => ({
      type: f.type || 'text',
      label: f.label || `字段${idx + 1}`,
      name: f.name || `field_${idx + 1}`,
      required: !!f.required,
      width: f.width || '50%',
      options: f.options || [],
      optionsText: Array.isArray(f.options) ? f.options.join(',') : '',
      placeholder: f.placeholder || '',
      _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
    }))
    
    if (currentTemplate.fields.length > 0) {
      newFields.forEach((f: any) => currentTemplate.fields.push(f))
      ElMessage.success(`已追加 ${newFields.length} 个字段`)
    } else {
      currentTemplate.name = 'JSON导入模板'
      currentTemplate.fields = newFields
      ElMessage.success(`已导入 ${newFields.length} 个字段`)
    }
    
    showJsonImport.value = false
    jsonInputText.value = ''
    
    // 切换到设计器视图
    if (viewMode.value === 'list') {
      viewMode.value = 'design'
    }
  } catch (e: any) {
    console.error('JSON解析失败:', e)
    ElMessage.error('JSON 解析失败：' + e.message)
  }
}'''

if old_ai_dialog_end in content:
    content = content.replace(old_ai_dialog_end, new_ai_dialog_end)
    print("[OK] JSON导入功能已添加")

# =====================================================
# 4. 在 header-right 中添加 JSON 导入按钮
# =====================================================
old_header = '''          <el-button @click="showImport = true">
            <el-icon><Upload /></el-icon> 导入文件
          </el-button>'''

new_header = '''          <el-button @click="openJsonImport">
            <el-icon><Document /></el-icon> JSON导入
          </el-button>
          <el-button @click="showImport = true">
            <el-icon><Upload /></el-icon> 导入文件
          </el-button>'''

if old_header in content:
    content = content.replace(old_header, new_header)
    print("[OK] JSON导入按钮已添加")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\nTemplates.vue 第一部分修复完成！")