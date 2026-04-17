/**
 * 批量导入政府部门和企业管理的经典表单模板
 */

import { templateAPI } from '../api'

// 政府部门模板
const governmentTemplates = [
  {
    name: '请假申请表',
    code: 'gov_leave_application',
    category: 'hr',
    description: '政府部门员工请假申请流程',
    fields: [
      { type: 'text', label: '申请人姓名', name: 'applicant_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '请假开始日期', name: 'start_date', required: true, width: '50%' },
      { type: 'date', label: '请假结束日期', name: 'end_date', required: true, width: '50%' },
      { type: 'select', label: '请假类型', name: 'leave_type', required: true, width: '100%', options: ['事假', '病假', '年休假', '婚假', '产假', '其他'] },
      { type: 'textarea', label: '请假事由', name: 'reason', required: true, width: '100%' },
      { type: 'text', label: '联系方式', name: 'contact', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '出差申请表',
    code: 'gov_business_trip',
    category: 'hr',
    description: '政府部门员工出差申请流程',
    fields: [
      { type: 'text', label: '申请人姓名', name: 'applicant_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '出差开始日期', name: 'start_date', required: true, width: '50%' },
      { type: 'date', label: '出差结束日期', name: 'end_date', required: true, width: '50%' },
      { type: 'text', label: '出差地点', name: 'location', required: true, width: '100%' },
      { type: 'select', label: '出差类型', name: 'trip_type', required: true, width: '100%', options: ['公务出差', '培训学习', '会议参会', '其他'] },
      { type: 'textarea', label: '出差事由', name: 'reason', required: true, width: '100%' },
      { type: 'money', label: '预计费用', name: 'estimated_cost', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '报销申请表',
    code: 'gov_expense_reimbursement',
    category: 'finance',
    description: '政府部门费用报销申请流程',
    fields: [
      { type: 'text', label: '申请人姓名', name: 'applicant_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '报销日期', name: 'reimburse_date', required: true, width: '100%' },
      { type: 'select', label: '报销类型', name: 'expense_type', required: true, width: '100%', options: ['差旅费', '办公费', '会议费', '培训费', '其他'] },
      { type: 'money', label: '报销金额', name: 'amount', required: true, width: '100%' },
      { type: 'textarea', label: '报销事由', name: 'reason', required: true, width: '100%' },
      { type: 'upload', label: '附件', name: 'attachments', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '设备采购申请表',
    code: 'gov_equipment_purchase',
    category: 'inventory',
    description: '政府部门设备采购申请流程',
    fields: [
      { type: 'text', label: '申请人姓名', name: 'applicant_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'text', label: '设备名称', name: 'equipment_name', required: true, width: '100%' },
      { type: 'number', label: '数量', name: 'quantity', required: true, width: '50%' },
      { type: 'money', label: '单价', name: 'unit_price', required: true, width: '50%' },
      { type: 'money', label: '总金额', name: 'total_amount', required: true, width: '100%' },
      { type: 'textarea', label: '采购理由', name: 'reason', required: true, width: '100%' },
      { type: 'textarea', label: '技术参数', name: 'specifications', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '会议室预订申请表',
    code: 'gov_meeting_room_booking',
    category: 'general',
    description: '政府部门会议室预订申请流程',
    fields: [
      { type: 'text', label: '申请人姓名', name: 'applicant_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '预订日期', name: 'booking_date', required: true, width: '50%' },
      { type: 'time', label: '开始时间', name: 'start_time', required: true, width: '50%' },
      { type: 'time', label: '结束时间', name: 'end_time', required: true, width: '100%' },
      { type: 'text', label: '会议室名称', name: 'meeting_room', required: true, width: '100%' },
      { type: 'number', label: '参会人数', name: 'attendees', required: true, width: '100%' },
      { type: 'textarea', label: '会议主题', name: 'meeting_topic', required: true, width: '100%' },
      { type: 'textarea', label: '备注', name: 'remarks', width: '100%' }
    ]
  }
]

// 企业管理模板
const enterpriseTemplates = [
  {
    name: '员工入职登记表',
    code: 'emp_employee_onboarding',
    category: 'hr',
    description: '企业员工入职登记流程',
    fields: [
      { type: 'text', label: '姓名', name: 'name', required: true, width: '50%' },
      { type: 'text', label: '性别', name: 'gender', required: true, width: '50%' },
      { type: 'date', label: '出生日期', name: 'birth_date', required: true, width: '50%' },
      { type: 'text', label: '身份证号', name: 'id_card', required: true, width: '50%' },
      { type: 'text', label: '联系电话', name: 'phone', required: true, width: '50%' },
      { type: 'email', label: '电子邮箱', name: 'email', required: true, width: '50%' },
      { type: 'text', label: '应聘职位', name: 'position', required: true, width: '100%' },
      { type: 'text', label: '部门', name: 'department', required: true, width: '100%' },
      { type: 'date', label: '入职日期', name: 'start_date', required: true, width: '100%' },
      { type: 'text', label: '紧急联系人', name: 'emergency_contact', required: true, width: '100%' },
      { type: 'text', label: '紧急联系电话', name: 'emergency_phone', required: true, width: '100%' },
      { type: 'textarea', label: '备注', name: 'remarks', width: '100%' }
    ]
  },
  {
    name: '员工离职申请表',
    code: 'emp_employee_resignation',
    category: 'hr',
    description: '企业员工离职申请流程',
    fields: [
      { type: 'text', label: '申请人姓名', name: 'applicant_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'text', label: '职位', name: 'position', required: true, width: '100%' },
      { type: 'date', label: '申请日期', name: 'apply_date', required: true, width: '50%' },
      { type: 'date', label: '预计离职日期', name: 'resign_date', required: true, width: '50%' },
      { type: 'select', label: '离职原因', name: 'resign_reason', required: true, width: '100%', options: ['个人原因', '职业发展', '薪资待遇', '工作环境', '其他'] },
      { type: 'textarea', label: '详细说明', name: 'reason_detail', required: true, width: '100%' },
      { type: 'textarea', label: '工作交接说明', name: 'handover_note', required: true, width: '100%' },
      { type: 'text', label: '部门主管', name: 'department_manager', required: true, width: '100%' }
    ]
  },
  {
    name: '绩效评估表',
    code: 'emp_performance_evaluation',
    category: 'hr',
    description: '企业员工绩效评估流程',
    fields: [
      { type: 'text', label: '员工姓名', name: 'employee_name', required: true, width: '50%' },
      { type: 'text', label: '所在部门', name: 'department', required: true, width: '50%' },
      { type: 'text', label: '职位', name: 'position', required: true, width: '100%' },
      { type: 'date', label: '评估周期', name: 'evaluation_period', required: true, width: '100%' },
      { type: 'rate', label: '工作质量', name: 'work_quality', required: true, width: '50%' },
      { type: 'rate', label: '工作效率', name: 'work_efficiency', required: true, width: '50%' },
      { type: 'rate', label: '团队合作', name: 'teamwork', required: true, width: '50%' },
      { type: 'rate', label: '创新能力', name: 'innovation', required: true, width: '50%' },
      { type: 'textarea', label: '优点', name: 'strengths', width: '100%' },
      { type: 'textarea', label: '改进建议', name: 'improvements', width: '100%' },
      { type: 'textarea', label: '总体评价', name: 'overall_evaluation', required: true, width: '100%' },
      { type: 'text', label: '评估人', name: 'evaluator', required: true, width: '100%' }
    ]
  },
  {
    name: '供应商信息表',
    code: 'emp_supplier_info',
    category: 'crm',
    description: '企业供应商信息管理',
    fields: [
      { type: 'text', label: '供应商名称', name: 'supplier_name', required: true, width: '100%' },
      { type: 'text', label: '联系人', name: 'contact_person', required: true, width: '50%' },
      { type: 'text', label: '联系电话', name: 'contact_phone', required: true, width: '50%' },
      { type: 'email', label: '电子邮箱', name: 'email', required: true, width: '100%' },
      { type: 'text', label: '地址', name: 'address', required: true, width: '100%' },
      { type: 'text', label: '经营范围', name: 'business_scope', required: true, width: '100%' },
      { type: 'text', label: '资质等级', name: 'qualification_level', width: '100%' },
      { type: 'text', label: '银行账户', name: 'bank_account', width: '100%' },
      { type: 'textarea', label: '备注', name: 'remarks', width: '100%' }
    ]
  },
  {
    name: '客户信息表',
    code: 'emp_customer_info',
    category: 'crm',
    description: '企业客户信息管理',
    fields: [
      { type: 'text', label: '客户名称', name: 'customer_name', required: true, width: '100%' },
      { type: 'text', label: '联系人', name: 'contact_person', required: true, width: '50%' },
      { type: 'text', label: '联系电话', name: 'contact_phone', required: true, width: '50%' },
      { type: 'email', label: '电子邮箱', name: 'email', required: true, width: '100%' },
      { type: 'text', label: '地址', name: 'address', required: true, width: '100%' },
      { type: 'select', label: '客户类型', name: 'customer_type', required: true, width: '100%', options: ['个人', '企业', '政府', '其他'] },
      { type: 'text', label: '行业', name: 'industry', width: '100%' },
      { type: 'textarea', label: '需求描述', name: 'requirements', width: '100%' },
      { type: 'textarea', label: '备注', name: 'remarks', width: '100%' }
    ]
  },
  {
    name: '产品信息表',
    code: 'emp_product_info',
    category: 'inventory',
    description: '企业产品信息管理',
    fields: [
      { type: 'text', label: '产品名称', name: 'product_name', required: true, width: '100%' },
      { type: 'text', label: '产品编码', name: 'product_code', required: true, width: '50%' },
      { type: 'text', label: '分类', name: 'category', required: true, width: '50%' },
      { type: 'money', label: '单价', name: 'unit_price', required: true, width: '100%' },
      { type: 'number', label: '库存数量', name: 'stock_quantity', required: true, width: '100%' },
      { type: 'textarea', label: '产品描述', name: 'description', required: true, width: '100%' },
      { type: 'textarea', label: '规格参数', name: 'specifications', width: '100%' },
      { type: 'image', label: '产品图片', name: 'image', width: '100%' },
      { type: 'textarea', label: '备注', name: 'remarks', width: '100%' }
    ]
  },
  {
    name: '项目立项申请表',
    code: 'emp_project_initiation',
    category: 'project',
    description: '企业项目立项申请流程',
    fields: [
      { type: 'text', label: '项目名称', name: 'project_name', required: true, width: '100%' },
      { type: 'text', label: '项目负责人', name: 'project_manager', required: true, width: '50%' },
      { type: 'text', label: '部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '开始日期', name: 'start_date', required: true, width: '50%' },
      { type: 'date', label: '结束日期', name: 'end_date', required: true, width: '50%' },
      { type: 'money', label: '项目预算', name: 'budget', required: true, width: '100%' },
      { type: 'textarea', label: '项目描述', name: 'description', required: true, width: '100%' },
      { type: 'textarea', label: '项目目标', name: 'objectives', required: true, width: '100%' },
      { type: 'textarea', label: '项目风险', name: 'risks', width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '合同审批表',
    code: 'emp_contract_approval',
    category: 'general',
    description: '企业合同审批流程',
    fields: [
      { type: 'text', label: '合同名称', name: 'contract_name', required: true, width: '100%' },
      { type: 'text', label: '申请人', name: 'applicant', required: true, width: '50%' },
      { type: 'text', label: '部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '申请日期', name: 'apply_date', required: true, width: '100%' },
      { type: 'text', label: '对方单位', name: 'counterparty', required: true, width: '100%' },
      { type: 'money', label: '合同金额', name: 'contract_amount', required: true, width: '100%' },
      { type: 'date', label: '合同期限', name: 'contract_term', required: true, width: '100%' },
      { type: 'textarea', label: '合同内容摘要', name: 'contract_summary', required: true, width: '100%' },
      { type: 'upload', label: '合同附件', name: 'attachments', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '预算申请表',
    code: 'emp_budget_application',
    category: 'finance',
    description: '企业预算申请流程',
    fields: [
      { type: 'text', label: '申请人', name: 'applicant', required: true, width: '50%' },
      { type: 'text', label: '部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '申请日期', name: 'apply_date', required: true, width: '100%' },
      { type: 'text', label: '预算项目', name: 'budget_item', required: true, width: '100%' },
      { type: 'money', label: '申请金额', name: 'apply_amount', required: true, width: '100%' },
      { type: 'select', label: '预算类型', name: 'budget_type', required: true, width: '100%', options: ['办公经费', '差旅费', '培训费', '设备采购', '其他'] },
      { type: 'textarea', label: '申请理由', name: 'reason', required: true, width: '100%' },
      { type: 'textarea', label: '预算明细', name: 'budget_details', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  },
  {
    name: '费用报销表',
    code: 'emp_expense_reimbursement',
    category: 'finance',
    description: '企业费用报销流程',
    fields: [
      { type: 'text', label: '申请人', name: 'applicant', required: true, width: '50%' },
      { type: 'text', label: '部门', name: 'department', required: true, width: '50%' },
      { type: 'date', label: '报销日期', name: 'reimburse_date', required: true, width: '100%' },
      { type: 'select', label: '报销类型', name: 'expense_type', required: true, width: '100%', options: ['差旅费', '办公费', '业务招待费', '交通费', '其他'] },
      { type: 'money', label: '报销金额', name: 'amount', required: true, width: '100%' },
      { type: 'textarea', label: '报销事由', name: 'reason', required: true, width: '100%' },
      { type: 'textarea', label: '费用明细', name: 'expense_details', required: true, width: '100%' },
      { type: 'upload', label: '报销附件', name: 'attachments', required: true, width: '100%' },
      { type: 'text', label: '审批人', name: 'approver', required: true, width: '100%' }
    ]
  }
]

// 导入模板
async function importTemplates() {
  console.log('开始导入模板...')
  
  try {
    // 导入政府部门模板
    console.log('导入政府部门模板...')
    for (const template of governmentTemplates) {
      const result = await templateAPI.create(template)
      console.log(`✓ 导入成功: ${template.name}`)
    }
    
    // 导入企业管理模板
    console.log('\n导入企业管理模板...')
    for (const template of enterpriseTemplates) {
      const result = await templateAPI.create(template)
      console.log(`✓ 导入成功: ${template.name}`)
    }
    
    console.log('\n🎉 所有模板导入完成！')
  } catch (error) {
    console.error('导入模板失败:', error)
  }
}

// 执行导入
if (typeof window !== 'undefined') {
  // 在浏览器环境中
  window.importTemplates = importTemplates
  console.log('模板导入函数已添加到window对象')
} else {
  // 在Node.js环境中
  importTemplates()
}

export { importTemplates, governmentTemplates, enterpriseTemplates }
