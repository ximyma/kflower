# -*- coding: utf-8 -*-
"""
增强 JSON 导入功能，支持两种格式：
1. 数据记录格式：[{"字段名": "值", ...}, ...]
2. 字段定义格式：[{"type":"text","label":"名称","name":"name"}, ...]
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 新的 importFromJson 函数
new_import_from_json = '''function importFromJson() {
  if (!jsonInputText.value.trim()) {
    ElMessage.warning('请输入 JSON 内容')
    return
  }
  
  try {
    let jsonStr = jsonInputText.value.trim()
    
    // 去除 Markdown 代码块标记
    const codeBlockMatch = jsonStr.match(/```(?:json)?\\s*([\\s\\S]*?)```/)
    if (codeBlockMatch) { jsonStr = codeBlockMatch[1].trim() }
    
    // 提取 JSON 数组
    const arrayMatch = jsonStr.match(/\\[[\\s\\S]*?\\]/)
    if (arrayMatch) { jsonStr = arrayMatch[0] }
    
    const parsed = JSON.parse(jsonStr)
    
    if (!Array.isArray(parsed)) {
      ElMessage.error('JSON 格式错误：需要数组格式')
      return
    }
    
    let newFields: any[] = []
    
    // ===== 判断格式 =====
    // 格式1：数据记录格式 - 数组元素是 {中文字段名: 值} 结构
    // 格式2：字段定义格式 - 数组元素有 type/label/name 属性
    
    const first = parsed[0]
    const isDataFormat = first && typeof first === 'object' && !first.type && !first.label && !first.name
    
    if (isDataFormat) {
      // ===== 数据记录格式：提取所有字段名，智能推断类型 =====
      console.log('检测到数据记录格式，智能推断字段类型')
      
      // 收集所有记录中的所有唯一字段名
      const allKeys = new Set<string>()
      parsed.forEach((record: any) => {
        if (record && typeof record === 'object') {
          Object.keys(record).forEach(key => allKeys.add(key))
        }
      })
      
      const keyList = Array.from(allKeys)
      const sampleRecords = parsed.slice(0, 3) // 取前3条作为样本推断类型
      
      newFields = keyList.map((key: string) => {
        // 从样本数据推断字段类型
        const sampleValues = sampleRecords
          .map((r: any) => r[key])
          .filter((v: any) => v !== undefined && v !== null && v !== '')
        
        let type = 'text'
        if (sampleValues.length > 0) {
          const sample = sampleValues[0]
          
          if (typeof sample === 'number') {
            type = 'number'
          } else if (typeof sample === 'boolean') {
            type = 'switch'
          } else if (sample instanceof Array) {
            // 如果包含\n换行符或者内容较长，可能是多行文本
            const strVal = String(sample)
            if (strVal.includes('\\n') || strVal.length > 50) {
              type = 'textarea'
            } else {
              // 逗号分隔的多个选项
              type = 'select'
            }
          } else {
            const strVal = String(sample).trim()
            
            // 时间类推断
            if (/^\\d{4}-\\d{2}-\\d{2}$/.test(strVal)) {
              type = 'date'
            } else if (/^\\d{4}-\\d{2}-\\d{2}[T ]\\d{2}:\\d{2}/.test(strVal)) {
              type = 'datetime'
            } else if (/^\\d{2}:\\d{2}$/.test(strVal)) {
              type = 'time'
            }
            // 邮箱
            else if (/^[\\w.-]+@[\\w.-]+\\.\\w+$/.test(strVal)) {
              type = 'email'
            }
            // 手机/电话
            else if (/^1[3-9]\\d{9}$/.test(strVal) || /^[\\d-]{7,}$/.test(strVal)) {
              type = 'phone'
            }
            // URL
            else if (/^https?:\\/\\//.test(strVal)) {
              type = 'url'
            }
            // 多行文本（包含换行或长度>50）
            else if (strVal.includes('\\n') || strVal.length > 80) {
              type = 'textarea'
            }
            // 枚举类（人名、职位等常见短文本，可考虑用select，但保守起见默认text）
            else if (strVal.length <= 20) {
              // 如果该字段所有值都一样，可以用radio；否则默认text
              const uniqueVals = new Set(sampleValues.map((v: any) => String(v)))
              if (uniqueVals.size <= 3 && uniqueVals.size > 1) {
                type = 'radio'
              } else {
                type = 'text'
              }
            }
          }
        }
        
        // 将中文字段名转为英文下划线命名
        const nameMap: Record<string, string> = {
          '会议主题': 'meeting_topic', '会议时间': 'meeting_time', '会议地点': 'meeting_location',
          '参与人员': 'participants', '主持人': 'host', '记录人': 'recorder',
          '议程': 'agenda', '讨论内容': 'discussion', '决议事项': 'resolutions',
          '后续行动': 'follow_up', '负责人': 'responsible', '截止日期': 'deadline',
          '备注': 'remark', '客户名称': 'customer_name', '联系人': 'contact_person',
          '联系电话': 'contact_phone', '供应商名称': 'supplier_name', '员工姓名': 'employee_name',
          '部门': 'department', '职位': 'position', '入职日期': 'join_date',
          '请假类型': 'leave_type', '开始日期': 'start_date', '结束日期': 'end_date',
          '请假原因': 'reason', '申请人': 'applicant', '申请日期': 'apply_date',
          '审批人': 'approver', '审批状态': 'status', '审批意见': 'comment',
          '费用类型': 'expense_type', '金额': 'amount', '报销金额': 'reimburse_amount',
          '事由': 'description', '申请人部门': 'applicant_dept', '票据数量': 'receipt_count',
          '出差地点': 'destination', '开始时间': 'start_time', '结束时间': 'end_time',
          '交通工具': 'transportation', '出差任务': 'mission',
        }
        
        const name = nameMap[key] || key
          .replace(/[\\u4e00-\\u9fa5]+/g, (m) => m.length > 2 ? m[0] + m[m.length-1] : m)
          .replace(/[^a-zA-Z0-9_]/g, '_')
          .replace(/_+/g, '_')
          .replace(/^_|_$/g, '')
          .toLowerCase()
        
        return {
          type,
          label: key,
          name: name || `field_${key}`,
          required: false,
          width: '100%',
          options: type === 'select' || type === 'radio' ? Array.from(new Set(sampleValues.map((v: any) => String(v)))) : [],
          optionsText: (type === 'select' || type === 'radio') ? Array.from(new Set(sampleValues.map((v: any) => String(v)))).join(',') : '',
          placeholder: '',
          _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
        }
      })
      
      ElMessage.success(`从 ${parsed.length} 条记录中识别出 ${newFields.length} 个字段`)
    } else {
      // ===== 字段定义格式：直接使用结构化定义 =====
      newFields = parsed.map((f: any, idx: number) => ({
        type: f.type || 'text',
        label: f.label || `字段${idx + 1}`,
        name: f.name || `field_${idx + 1}`,
        required: !!f.required,
        width: f.width || '50%',
        options: Array.isArray(f.options) ? f.options : [],
        optionsText: Array.isArray(f.options) ? f.options.join(',') : '',
        placeholder: f.placeholder || '',
        _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
      }))
      
      ElMessage.success(`已导入 ${newFields.length} 个字段`)
    }
    
    if (currentTemplate.fields.length > 0) {
      newFields.forEach((f: any) => currentTemplate.fields.push(f))
      ElMessage.success(`已追加 ${newFields.length} 个字段`)
    } else {
      currentTemplate.name = 'JSON导入模板'
      currentTemplate.fields = newFields
    }
    
    showJsonImport.value = false
    jsonInputText.value = ''
    if (viewMode.value === 'list') { viewMode.value = 'design' }
    
  } catch (e: any) {
    console.error('JSON解析失败:', e)
    ElMessage.error('JSON 解析失败：' + e.message)
  }
}'''

# 替换旧的 importFromJson 函数
old_func = 'function importFromJson() {\n  if (!jsonInputText.value.trim()) {\n    ElMessage.warning(\'请输入 JSON 内容\')\n    return\n  }\n  \n  try {\n    // 尝试解析 JSON\n    let jsonStr = jsonInputText.value.trim()\n    \n    // 如果是 Markdown 代码块，提取其中的 JSON\n    const codeBlockMatch = jsonStr.match(/```(?:json)?\\s*([\\s\\S]*?)```/)\n    if (codeBlockMatch) {\n      jsonStr = codeBlockMatch[1].trim()\n    }\n    \n    // 提取 JSON 数组\n    const arrayMatch = jsonStr.match(/\\[[\\s\\S]*?\\]/\n    if (arrayMatch) {\n      jsonStr = arrayMatch[0]\n    }\n    \n    const fields = JSON.parse(jsonStr)\n    \n    if (!Array.isArray(fields)) {\n      ElMessage.error(\'JSON 格式错误：需要数组格式\')\n      return\n    }\n    \n    // 转换字段格式\n    const newFields = fields.map((f: any, idx: number) => ({\n      type: f.type || \'text\',\n      label: f.label || `字段${idx + 1}`,\n      name: f.name || `field_${idx + 1}`,\n      required: !!f.required,\n      width: f.width || \'50%\',\n      options: f.options || [],\n      optionsText: Array.isArray(f.options) ? f.options.join(\',\') : \'\',\n      placeholder: f.placeholder || \'\',\n      _key: \'field_\' + Date.now() + \'_\' + Math.random().toString(36).slice(2)\n    }))\n    \n    if (currentTemplate.fields.length > 0) {\n      newFields.forEach((f: any) => currentTemplate.fields.push(f))\n      ElMessage.success(`已追加 ${newFields.length} 个字段`)\n    } else {\n      currentTemplate.name = \'JSON导入模板\'\n      currentTemplate.fields = newFields\n      ElMessage.success(`已导入 ${newFields.length} 个字段`)\n    }\n    \n    showJsonImport.value = false\n    jsonInputText.value = \'\''
new_func = new_import_from_json

if old_func in content:
    content = content.replace(old_func, new_func)
    print("[OK] importFromJson 已增强")
else:
    print("[WARN] 找不到原函数，尝试精确替换")
    # 精确找到函数开始
    start = content.find('function importFromJson() {')
    end = content.find('\n}', start) + 2
    # 找到函数结束（最后一个 }）
    # 简单方法：替换从 start 到下一个空函数声明
    if start > 0:
        # 找到函数结束 - 查找对应的 }
        brace_count = 0
        func_start = content.find('{', start) + 1
        i = func_start
        while i < len(content):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
            i += 1
        content = content[:start] + new_func + content[end:]
        print("[OK] 通过精确位置替换")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("完成！")