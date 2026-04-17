# -*- coding: utf-8 -*-
"""
精确替换 importFromJson 函数
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

marker = 'function importFromJson()'
idx = content.find(marker)
if idx < 0:
    print('[ERROR] 找不到函数')
    sys.exit(1)

# 找函数开始的 {
func_brace_start = content.find('{', idx)
if func_brace_start < 0:
    print('[ERROR] 找不到函数开始的 {')
    sys.exit(1)

# 找函数结束的 }  (匹配括号)
brace_count = 0
i = func_brace_start
while i < len(content):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end_idx = i + 1
            break
    i += 1

print(f'函数范围: {idx} 到 {end_idx} (长度 {end_idx - idx})')
old_func = content[idx:end_idx]
print(f'原函数前100字符: {repr(old_func[:100])}')
print(f'原函数后50字符: {repr(old_func[-50:])}')

# 新的完整函数
new_func = '''function importFromJson() {
  if (!jsonInputText.value.trim()) {
    ElMessage.warning('请输入 JSON 内容')
    return
  }
  
  try {
    let jsonStr = jsonInputText.value.trim()
    
    const codeBlockMatch = jsonStr.match(/```(?:json)?\\s*([\\s\\S]*?)```/)
    if (codeBlockMatch) { jsonStr = codeBlockMatch[1].trim() }
    
    const arrayMatch = jsonStr.match(/\\[[\\s\\S]*?\\]/)
    if (arrayMatch) { jsonStr = arrayMatch[0] }
    
    const parsed = JSON.parse(jsonStr)
    
    if (!Array.isArray(parsed) || parsed.length === 0) {
      ElMessage.error('JSON 格式错误：需要非空数组格式')
      return
    }
    
    const first = parsed[0]
    const isDataFormat = first && typeof first === 'object' && !first.type && !first.label && !first.name
    
    let newFields = []
    
    if (isDataFormat) {
      // ===== 数据记录格式智能转换 =====
      const allKeys = new Set()
      parsed.forEach((record) => {
        if (record && typeof record === 'object') {
          Object.keys(record).forEach(key => allKeys.add(key))
        }
      })
      
      const keyList = Array.from(allKeys)
      const samples = parsed.slice(0, 5)
      
      const nameMap = {
        '会议主题':'meeting_topic','会议时间':'meeting_time','会议地点':'meeting_location',
        '参与人员':'participants','主持人':'host','记录人':'recorder',
        '议程':'agenda','讨论内容':'discussion','决议事项':'resolutions',
        '后续行动':'follow_up','负责人':'responsible','截止日期':'deadline',
        '备注':'remark','客户名称':'customer_name','联系人':'contact_person',
        '联系电话':'contact_phone','供应商名称':'supplier_name','员工姓名':'employee_name',
        '部门':'department','职位':'position','入职日期':'join_date',
        '请假类型':'leave_type','开始日期':'start_date','结束日期':'end_date',
        '请假原因':'reason','申请人':'applicant','申请日期':'apply_date',
        '审批人':'approver','审批状态':'status','审批意见':'comment',
        '费用类型':'expense_type','金额':'amount','事由':'description',
        '出差地点':'destination','交通工具':'transportation','出差任务':'mission',
      }
      
      newFields = keyList.map((key) => {
        const sampleValues = samples
          .map(r => r[key])
          .filter(v => v !== undefined && v !== null && v !== '')
        
        let type = 'text'
        
        if (sampleValues.length > 0) {
          const s = String(sampleValues[0]).trim()
          if (/^\\d{4}-\\d{2}-\\d{2}$/.test(s)) type = 'date'
          else if (/^\\d{4}-\\d{2}-\\d{2}[T ]\\d{2}:\\d{2}/.test(s)) type = 'datetime'
          else if (/^\\d{2}:\\d{2}$/.test(s)) type = 'time'
          else if (/^1[3-9]\\d{9}$/.test(s) || /^[\\d-]{7,}$/.test(s)) type = 'phone'
          else if (/^[\\w.-]+@[\\w.-]+\\.\\w+$/.test(s)) type = 'email'
          else if (s.includes('\\n') || s.length > 80) type = 'textarea'
          else if (s.length <= 20) {
            const uniq = [...new Set(sampleValues.map(v => String(v)))]
            if (uniq.length >= 2 && uniq.length <= 6) type = 'radio'
          }
        }
        
        const rawName = nameMap[key] || key.replace(/[^\\w]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '').toLowerCase()
        const name = rawName || 'field_' + key.slice(0, 3)
        
        const isEnum = type === 'radio' || type === 'select'
        const uniqueVals = [...new Set(sampleValues.map(v => String(v)))]
        
        return {
          type, label: key, name,
          required: false, width: '100%',
          options: isEnum ? uniqueVals : [],
          optionsText: isEnum ? uniqueVals.join(',') : '',
          placeholder: '',
          _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
        }
      })
      
      ElMessage.success('从 ' + parsed.length + ' 条记录识别出 ' + newFields.length + ' 个字段')
    } else {
      // ===== 字段定义格式 =====
      newFields = parsed.map((f, idx) => ({
        type: f.type || 'text',
        label: f.label || ('字段' + (idx + 1)),
        name: f.name || ('field_' + (idx + 1)),
        required: !!f.required,
        width: f.width || '50%',
        options: Array.isArray(f.options) ? f.options : [],
        optionsText: Array.isArray(f.options) ? f.options.join(',') : '',
        placeholder: f.placeholder || '',
        _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
      }))
      ElMessage.success('已导入 ' + newFields.length + ' 个字段')
    }
    
    if (currentTemplate.fields.length > 0) {
      newFields.forEach(f => currentTemplate.fields.push(f))
      ElMessage.success('已追加 ' + newFields.length + ' 个字段')
    } else {
      currentTemplate.name = 'JSON导入模板'
      currentTemplate.fields = newFields
    }
    
    showJsonImport.value = false
    jsonInputText.value = ''
    if (viewMode.value === 'list') { viewMode.value = 'design' }
    
  } catch (e) {
    ElMessage.error('JSON 解析失败：' + (e.message || String(e)))
  }
}'''

# 验证新函数括号匹配
bc = 0
for ch in new_func:
    if ch == '{': bc += 1
    elif ch == '}': bc -= 1
print(f'新函数括号匹配: {bc} (应为0)')

content = content[:idx] + new_func + content[end_idx:]
print(f'文件大小: {len(content)}')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('[OK] 完成')