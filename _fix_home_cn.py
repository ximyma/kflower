# -*- coding: utf-8 -*-
"""Fix Home.vue: change all English text to Chinese"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Home.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

replacements = [
    # Template section
    ("'Templates'", "'模板数量'"),
    ("'Workflows'", "'工作流数'"),
    ("'Documents'", "'知识文档'"),
    ("'AI Chats'", "'AI对话'"),
    
    # AI Assistant section
    ("AI Assistant", "AI 智能助手"),
    ("Online", "在线"),
    ("Select AI Model", "选择AI模型"),
    ("Enter your request, e.g.: help me design a procurement process", "输入您的需求，例如：帮我设计一个采购审批流程"),
    ("Submit to AI", "提交给AI"),
    ("AI Settings", "AI配置"),
    ("Quick Commands", "快捷指令"),
    
    # Todo section
    ("Todo List", "待办事项"),
    ("Approve Purchase Request", "审批采购申请"),
    ("From Zhang San #1001", "张三 提交的 #1001"),
    ("Update Knowledge Base", "更新知识库"),
    ("Upload product manual v2.0", "上传产品手册 v2.0"),
    ("Workflow Design", "工作流设计"),
    ("Complete leave approval config", "完成请假审批配置"),
    
    # Recent Activity section
    ("Recent Activity", "最近动态"),
    ('prop="time" label="Time"', 'prop="time" label="时间"'),
    ('prop="user" label="User"', 'prop="user" label="操作人"'),
    ('prop="action" label="Action"', 'prop="action" label="操作"'),
    ('prop="target" label="Target"', 'prop="target" label="对象"'),
    ('label="Status"', 'label="状态"'),
    ("row.status === 'success' ? 'success' : 'warning'", "row.status === 'success' ? 'success' : 'warning'"),
    # Status display
    ("{{ row.status }}", "{{ row.status === 'success' ? '成功' : row.status === 'warning' ? '进行中' : row.status }}"),
    
    # Suggestions
    ("'Design a CRM customer management workflow'", "'设计一个客户管理流程'"),
    ("'Create a procurement approval template'", "'创建一个采购审批模板'"),
    ("'Upload product knowledge documents'", "'上传产品知识文档'"),
    ("'Generate monthly report'", "'生成月度报表'"),
    
    # Warning messages
    ("'Please enter a request'", "'请输入您的需求'"),
]

total = 0
for old, new in replacements:
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        total += count
        print(f"  [OK] '{old}' -> '{new}' ({count}x)")
    else:
        print(f"  [SKIP] '{old}' not found")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print(f"\nTotal replacements: {total}")
print("Home.vue converted to Chinese!")
