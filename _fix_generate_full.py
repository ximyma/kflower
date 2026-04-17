# -*- coding: utf-8 -*-
"""
完整重写 generateWithAI 函数，修复作用域问题
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到 generateWithAI 函数的开始和结束
start_marker = 'async function generateWithAI() {'
end_marker = '// JSON 导入功能'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx > 0 and end_idx > start_idx:
    # 新的 generateWithAI 函数
    new_function = '''async function generateWithAI() {
  if (!aiPrompt.value.trim()) { ElMessage.warning('请描述您的需求'); return }
  aiLoading.value = true
  
  // 预设模板（作为后备方案）
  const presetTemplates: Record<string, any[]> = {
    '供应商': [
      { type:'text', label:'供应商名称', name:'supplier_name', required:true, width:'100%', placeholder:'请输入供应商名称' },
      { type:'text', label:'供应商编码', name:'supplier_code', required:true, width:'50%', placeholder:'请输入编码' },
      { type:'select', label:'供应商类型', name:'supplier_type', required:true, width:'50%', options:['原材料供应商','设备供应商','服务供应商','其他'] },
      { type:'divider', label:'联系方式', name:'div1', width:'100%' },
      { type:'text', label:'联系人', name:'contact_person', required:true, width:'50%', placeholder:'请输入联系人' },
      { type:'phone', label:'联系电话', name:'contact_phone', required:true, width:'50%', placeholder:'请输入手机号' },
      { type:'email', label:'电子邮箱', name:'contact_email', width:'50%', placeholder:'请输入邮箱' },
      { type:'textarea', label:'详细地址', name:'address', width:'100%', placeholder:'请输入地址' },
    ],
    '员工入职': [
      { type:'heading', label:'基本信息', name:'h1', width:'100%' },
      { type:'text', label:'姓名', name:'name', required:true, width:'50%', placeholder:'请输入姓名' },
      { type:'text', label:'工号', name:'employee_id', required:true, width:'50%', placeholder:'请输入工号' },
      { type:'select', label:'性别', name:'gender', required:true, width:'50%', options:['男','女'] },
      { type:'date', label:'入职日期', name:'join_date', required:true, width:'50%' },
      { type:'select', label:'部门', name:'department', required:true, width:'50%', options:['技术部','市场部','财务部','行政部'] },
      { type:'text', label:'职位', name:'position', required:true, width:'50%', placeholder:'请输入职位' },
      { type:'phone', label:'手机号码', name:'mobile', required:true, width:'50%', placeholder:'请输入手机号' },
      { type:'email', label:'电子邮箱', name:'email', width:'50%', placeholder:'请输入邮箱' },
    ],
    '客户': [
      { type:'text', label:'客户名称', name:'customer_name', required:true, width:'100%', placeholder:'请输入客户名称' },
      { type:'text', label:'客户编码', name:'customer_code', required:true, width:'50%', placeholder:'请输入编码' },
      { type:'select', label:'客户类型', name:'customer_type', required:true, width:'50%', options:['企业客户','个人客户','政府机构'] },
      { type:'text', label:'联系人', name:'contact_person', required:true, width:'50%', placeholder:'请输入联系人' },
      { type:'phone', label:'联系电话', name:'contact_phone', required:true, width:'50%', placeholder:'请输入手机号' },
    ],
  }
  
  try {
    // 规范化的 AI 提示词
    const systemPrompt = `你是一个专业的表单设计助手。用户会描述他们需要的表单类型，你需要生成对应的表单字段定义。

**重要：只输出 JSON 数组格式，不要输出任何其他文字、解释或Markdown代码块标记！**

每个字段对象包含以下属性：
- type: 字段类型（text/textarea/number/date/select/radio/checkbox/email/phone/money/upload）
- label: 字段标签（中文）
- name: 字段名称（英文小写下划线）
- required: 是否必填（true/false）
- width: 宽度（"50%"或"100%"）
- options: 选项数组（仅 select/radio/checkbox 需要）
- placeholder: 占位提示文字

示例输出：
[{"type":"text","label":"客户名称","name":"customer_name","required":true,"width":"100%","placeholder":"请输入客户名称"},{"type":"phone","label":"联系电话","name":"phone","required":true,"width":"50%","placeholder":"请输入手机号"}]`

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
          { role: 'user', content: aiPrompt.value }
        ],
        temperature: 0.7
      })
    })
    
    const result = await response.json()
    let matchedFields: any[] = []
    
    // 尝试从 AI 响应中解析 JSON
    if (result.success || result.data || result.content) {
      const aiContent = result.data?.content || result.content || result.message || ''
      console.log('AI响应:', aiContent)
      
      // 提取 JSON 数组（去除可能存在的 Markdown 代码块标记）
      let jsonStr = aiContent.replace(/```json\\s*/g, '').replace(/```\\s*/g, '').trim()
      const jsonMatch = jsonStr.match(/\\[[\\s\\S]*\\]/)
      if (jsonMatch) {
        jsonStr = jsonMatch[0]
      }
      
      try {
        matchedFields = JSON.parse(jsonStr)
        console.log('AI生成字段数:', matchedFields.length)
      } catch (e) {
        console.warn('JSON解析失败，尝试使用预设模板')
      }
    }
    
    // 如果 AI 没有返回有效数据，使用预设模板匹配
    if (!matchedFields.length) {
      for (const [key, fields] of Object.entries(presetTemplates)) {
        if (aiPrompt.value.includes(key)) {
          matchedFields = fields
          console.log('使用预设模板:', key)
          break
        }
      }
    }
    
    // 最后的默认模板
    if (!matchedFields.length) {
      matchedFields = [
        { type:'text', label:'名称', name:'name', required:true, width:'50%', placeholder:'请输入名称' },
        { type:'text', label:'编码', name:'code', required:true, width:'50%', placeholder:'请输入编码' },
        { type:'select', label:'类型', name:'type', width:'50%', options:['类型A','类型B','类型C'] },
        { type:'date', label:'日期', name:'date', width:'50%' },
        { type:'textarea', label:'备注', name:'remark', width:'100%', placeholder:'请输入备注' },
      ]
    }
    
    // 转换字段格式
    const newFields = matchedFields.map((f: any) => ({
      ...f,
      _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2),
      optionsText: Array.isArray(f.options) ? f.options.join(',') : '',
      placeholder: f.placeholder || ''
    }))
    
    if (currentTemplate.fields.length > 0) {
      newFields.forEach((f: any) => currentTemplate.fields.push(f))
      ElMessage.success(`已追加 ${newFields.length} 个字段`)
    } else {
      currentTemplate.name = 'AI设计 - ' + aiPrompt.value.slice(0, 15)
      currentTemplate.fields = newFields
      ElMessage.success(`已生成 ${newFields.length} 个字段`)
    }
    
    showAIHelper.value = false
    aiPrompt.value = ''
    viewMode.value = 'design'
    
  } catch (e: any) {
    console.error('AI生成失败:', e)
    ElMessage.error(e.message || 'AI生成失败')
  } finally {
    aiLoading.value = false
  }
}

'''

    # 替换函数
    content = content[:start_idx] + new_function + content[end_idx:]
    print("[OK] generateWithAI 函数已完全重写")
else:
    print("[ERROR] 找不到函数边界")

# 保存文件
with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("修复完成！")