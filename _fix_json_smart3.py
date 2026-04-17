# -*- coding: utf-8 -*-
"""
增强 JSON 导入功能，支持数据记录格式 + 字段定义格式
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 新函数
new_func = r'''function importFromJson() {
  if (!jsonInputText.value.trim()) {
    ElMessage.warning('请输入 JSON 内容')
    return
  }
  
  try {
    let jsonStr = jsonInputText.value.trim()
    
    // 去除 Markdown 代码块
    const codeBlockMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (codeBlockMatch) { jsonStr = codeBlockMatch[1].trim() }
    
    // 提取 JSON 数组
    const arrayMatch = jsonStr.match(/\[[\s\S]*?\]/)
    if (arrayMatch) { jsonStr = arrayMatch[0] }
    
    const parsed = JSON.parse(jsonStr)
    
    if (!Array.isArray(parsed) || parsed.length === 0) {
      ElMessage.error('JSON 格式错误：需要非空数组格式')
      return
    }
    
    const first = parsed[0]
    
    // 判断格式：
    // 格式1: 数据记录 {中文key: 值} - 没有type/label/name
    // 格式2: 字段定义 {type, label, name} - 有type属性
    const isDataFormat = first && typeof first === 'object' && !first.type && !first.label && !first.name
    
    let newFields: any[] = []
    
    if (isDataFormat) {
      // ===== 数据记录格式 =====
      const allKeys = new Set<string>()
      parsed.forEach((record: any) => {
        if (record && typeof record === 'object') {
          Object.keys(record).forEach(key => allKeys.add(key))
        }
      })
      
      const keyList = Array.from(allKeys)
      const samples = parsed.slice(0, 5)
      
      const nameMap: Record<string, string> = {
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
      
      newFields = keyList.map((key: string) => {
        const sampleValues = samples
          .map((r: any) => r[key])
          .filter((v: any) => v !== undefined && v !== null && v !== '')
        
        let type = 'text'
        
        if (sampleValues.length > 0) {
          const s = String(sampleValues[0]).trim()
          if (/^\d{4}-\d{2}-\d{2}$/.test(s)) type = 'date'
          else if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(s)) type = 'datetime'
          else if (/^\d{2}:\d{2}$/.test(s)) type = 'time'
          else if (/^1[3-9]\d{9}$/.test(s) || /^[\d-]{7,}$/.test(s)) type = 'phone'
          else if (/^[\w.-]+@[\w.-]+\.\w+$/.test(s)) type = 'email'
          else if (s.includes('\n') || s.length > 80) type = 'textarea'
          else if (s.length <= 20) {
            const uniq = [...new Set(sampleValues.map(v => String(v)))]
            if (uniq.length >= 2 && uniq.length <= 6) type = 'radio'
          }
        }
        
        const name = nameMap[key] || key.replace(/[^\w]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '').toLowerCase() || 'field_' + key.slice(0, 3)
        
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
      newFields = parsed.map((f: any, idx: number) => ({
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
      newFields.forEach((f: any) => currentTemplate.fields.push(f))
      ElMessage.success('已追加 ' + newFields.length + ' 个字段')
    } else {
      currentTemplate.name = 'JSON导入模板'
      currentTemplate.fields = newFields
    }
    
    showJsonImport.value = false
    jsonInputText.value = ''
    if (viewMode.value === 'list') { viewMode.value = 'design' }
    
  } catch (e: any) {
    ElMessage.error('JSON 解析失败：' + e.message)
  }
}'''

# 查找并替换
marker = 'function importFromJson()'
idx = content.find(marker)
if idx < 0:
    print('[ERROR] 找不到函数')
else:
    # 找函数结束
    brace_count = 0
    func_start = content.find('{', idx) + 1
    i = func_start
    while i < len(content):
        if content[i] == '{': brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1; break
        i += 1
    
    content = content[:idx] + new_func + content[end_idx:]
    print('[OK] importFromJson 已替换')

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)
print('完成')