/**
 * 批量导入政府部门和企业管理的经典工作流模板
 */

import { workflowAPI } from '../api'

// 生成工作流节点和连接
function generateWorkflow(name, description, flowType, nodes, connections) {
  return {
    name,
    description,
    flow_type: flowType,
    is_active: true,
    nodes,
    edges: connections
  }
}

// 政府部门工作流
const governmentWorkflows = [
  {
    name: '请假审批流程',
    description: '政府部门员工请假申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '员工提交请假申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '人事部门审核', x: 550, y: 100, description: '人事部门审核', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 700, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'end-1' }
    ]
  },
  {
    name: '出差审批流程',
    description: '政府部门员工出差申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '员工提交出差申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 700, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'end-1' }
    ]
  },
  {
    name: '报销审批流程',
    description: '政府部门费用报销申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交报销', x: 250, y: 100, description: '员工提交报销申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '领导审批', x: 550, y: 200, description: '分管领导审批', assignee: 'assignee' },
      { id: 'condition-1', type: 'condition', name: '金额判断', x: 400, y: 200, description: '判断报销金额', condition: 'amount > 5000' },
      { id: 'end-1', type: 'end', name: '结束', x: 700, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'condition-1' },
      { id: 'conn-4', from: 'condition-1', to: 'task-3' },
      { id: 'conn-5', from: 'condition-1', to: 'task-4' },
      { id: 'conn-6', from: 'task-3', to: 'end-1' },
      { id: 'conn-7', from: 'task-4', to: 'end-1' }
    ]
  },
  {
    name: '设备采购审批流程',
    description: '政府部门设备采购申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '部门提交采购申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '采购部门执行', x: 700, y: 100, description: '采购部门执行采购', assignee: 'assignee' },
      { id: 'task-5', type: 'task', name: '验收', x: 850, y: 100, description: '设备验收', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 1000, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'task-5' },
      { id: 'conn-6', from: 'task-5', to: 'end-1' }
    ]
  },
  {
    name: '会议室预订审批流程',
    description: '政府部门会议室预订申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '提交会议室预订申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '行政部门审核', x: 400, y: 100, description: '行政部门审核', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 550, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'end-1' }
    ]
  }
]

// 企业管理工作流
const enterpriseWorkflows = [
  {
    name: '员工入职审批流程',
    description: '企业员工入职申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '人事部门提交入职申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '总经理审批', x: 550, y: 100, description: '总经理审批', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '办理入职', x: 700, y: 100, description: '人事部门办理入职手续', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 850, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'end-1' }
    ]
  },
  {
    name: '员工离职审批流程',
    description: '企业员工离职申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '员工提交离职申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '工作交接', x: 550, y: 100, description: '员工进行工作交接', assignee: 'initiator' },
      { id: 'task-4', type: 'task', name: '人事部门审核', x: 700, y: 100, description: '人事部门审核', assignee: 'assignee' },
      { id: 'task-5', type: 'task', name: '财务部门审核', x: 850, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 1000, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'task-5' },
      { id: 'conn-6', from: 'task-5', to: 'end-1' }
    ]
  },
  {
    name: '绩效评估流程',
    description: '企业员工绩效评估流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '员工自评', x: 250, y: 100, description: '员工进行自我评价', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '主管评价', x: 400, y: 100, description: '部门主管评价', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '人事部门审核', x: 550, y: 100, description: '人事部门审核', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '结果反馈', x: 700, y: 100, description: '向员工反馈评估结果', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 850, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'end-1' }
    ]
  },
  {
    name: '合同审批流程',
    description: '企业合同审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交合同', x: 250, y: 100, description: '业务部门提交合同', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '法务部门审核', x: 400, y: 100, description: '法务部门审核合同', assignee: 'assignee' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核合同', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '总经理审批', x: 700, y: 100, description: '总经理审批合同', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 850, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'end-1' }
    ]
  },
  {
    name: '预算申请审批流程',
    description: '企业预算申请审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交申请', x: 250, y: 100, description: '部门提交预算申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '总经理审批', x: 700, y: 100, description: '总经理审批', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 850, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'end-1' }
    ]
  },
  {
    name: '费用报销审批流程',
    description: '企业费用报销审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交报销', x: 250, y: 100, description: '员工提交报销申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'condition-1', type: 'condition', name: '金额判断', x: 400, y: 200, description: '判断报销金额', condition: 'amount > 10000' },
      { id: 'task-4', type: 'task', name: '总经理审批', x: 550, y: 200, description: '总经理审批', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 700, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'condition-1' },
      { id: 'conn-4', from: 'condition-1', to: 'task-3' },
      { id: 'conn-5', from: 'condition-1', to: 'task-4' },
      { id: 'conn-6', from: 'task-3', to: 'end-1' },
      { id: 'conn-7', from: 'task-4', to: 'end-1' }
    ]
  },
  {
    name: '项目立项审批流程',
    description: '企业项目立项审批流程',
    flow_type: 'approval',
    nodes: [
      { id: 'start-1', type: 'start', name: '开始', x: 100, y: 100, description: '流程开始' },
      { id: 'task-1', type: 'task', name: '提交立项', x: 250, y: 100, description: '部门提交项目立项申请', assignee: 'initiator' },
      { id: 'task-2', type: 'task', name: '部门主管审批', x: 400, y: 100, description: '部门主管审批', assignee: 'manager' },
      { id: 'task-3', type: 'task', name: '财务部门审核', x: 550, y: 100, description: '财务部门审核', assignee: 'assignee' },
      { id: 'task-4', type: 'task', name: '技术部门审核', x: 700, y: 100, description: '技术部门审核', assignee: 'assignee' },
      { id: 'task-5', type: 'task', name: '总经理审批', x: 850, y: 100, description: '总经理审批', assignee: 'assignee' },
      { id: 'end-1', type: 'end', name: '结束', x: 1000, y: 100, description: '流程结束' }
    ],
    connections: [
      { id: 'conn-1', from: 'start-1', to: 'task-1' },
      { id: 'conn-2', from: 'task-1', to: 'task-2' },
      { id: 'conn-3', from: 'task-2', to: 'task-3' },
      { id: 'conn-4', from: 'task-3', to: 'task-4' },
      { id: 'conn-5', from: 'task-4', to: 'task-5' },
      { id: 'conn-6', from: 'task-5', to: 'end-1' }
    ]
  }
]

// 导入工作流
async function importWorkflows() {
  console.log('开始导入工作流...')
  
  try {
    // 导入政府部门工作流
    console.log('导入政府部门工作流...')
    for (const workflow of governmentWorkflows) {
      const result = await workflowAPI.create(workflow)
      console.log(`✓ 导入成功: ${workflow.name}`)
    }
    
    // 导入企业管理工作流
    console.log('\n导入企业管理工作流...')
    for (const workflow of enterpriseWorkflows) {
      const result = await workflowAPI.create(workflow)
      console.log(`✓ 导入成功: ${workflow.name}`)
    }
    
    console.log('\n🎉 所有工作流导入完成！')
  } catch (error) {
    console.error('导入工作流失败:', error)
  }
}

// 执行导入
if (typeof window !== 'undefined') {
  // 在浏览器环境中
  window.importWorkflows = importWorkflows
  console.log('工作流导入函数已添加到window对象')
} else {
  // 在Node.js环境中
  importWorkflows()
}

export { importWorkflows, governmentWorkflows, enterpriseWorkflows }
