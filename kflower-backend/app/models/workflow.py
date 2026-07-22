"""
数据库模型 - 模板和工作流
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Template(Base):
    """业务模板"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    code = Column(String(100), unique=True, comment="模板编码")
    description = Column(Text, nullable=True, comment="模板描述")
    category = Column(String(50), comment="分类：inventory/order/hr/crm/project")
    
    # 模板配置
    config = Column(JSON, default=dict, comment="模板配置JSON")
    modules = Column(JSON, default=list, comment="模块列表")
    workflows = Column(JSON, default=list, comment="关联工作流")
    
    # AI生成信息
    ai_generated = Column(Boolean, default=False, comment="是否AI生成")
    ai_prompt = Column(Text, nullable=True, comment="AI生成时的提示词")
    
    # 状态
    is_published = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False, comment="是否公开共享")  # False=私有, True=共享
    is_template = Column(Boolean, default=True)  # 是否为模板库模板
    
    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    organization = relationship("Organization")
    creator = relationship("User")
    instances = relationship("TemplateInstance", back_populates="template")
    
    def __repr__(self):
        return f"<Template {self.name}>"


class TemplateInstance(Base):
    """模板实例（基于模板创建的应用）"""
    __tablename__ = "template_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    
    # 实例数据
    config = Column(JSON, default=dict)
    
    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    template = relationship("Template", back_populates="instances")
    organization = relationship("Organization")
    creator = relationship("User")


class Workflow(Base):
    """工作流"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True)
    description = Column(Text, nullable=True)
    
    # 工作流定义
    flow_type = Column(String(50), default="normal", comment="normal/fork/parallel")
    definition = Column(JSON, default=dict, comment="流程定义")
    nodes = Column(JSON, default=list, comment="节点定义")
    edges = Column(JSON, default=list, comment="连线定义")
    
    # 升级扩展字段（按照 dd4chat.txt 方案）
    node_definitions = Column(JSON, default=list, comment="节点详细配置")
    edge_definitions = Column(JSON, default=list, comment="连线条件")
    variables = Column(JSON, default=dict, comment="流程变量定义")
    form_template_id = Column(Integer, nullable=True, comment="主表单模板ID")
    
    # AI辅助
    ai_optimized = Column(Boolean, default=False)
    ai_suggestions = Column(JSON, default=list)
    
    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    organization = relationship("Organization")
    creator = relationship("User")
    instances = relationship("WorkflowInstance", back_populates="workflow")
    
    def __repr__(self):
        return f"<Workflow {self.name}>"


class WorkflowInstance(Base):
    """工作流实例"""
    __tablename__ = "workflow_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    
    # 实例数据
    title = Column(String(200), nullable=False)
    data = Column(JSON, default=dict)
    
    # 升级扩展字段（按照 dd4chat.txt 方案）
    variables = Column(JSON, default=dict, comment="运行时变量")
    parent_instance_id = Column(Integer, nullable=True, comment="子流程父实例")
    form_data_id = Column(Integer, nullable=True, comment="主表单数据ID")
    
    # 流程状态
    status = Column(String(50), default="draft", comment="draft/running/approved/rejected/cancelled")
    current_node_id = Column(String(100), nullable=True)
    
    # 发起人
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # AI辅助
    ai_suggestions = Column(JSON, default=list)
    ai_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    workflow = relationship("Workflow", back_populates="instances")
    organization = relationship("Organization")
    creator = relationship("User")
    tasks = relationship("WorkflowTask", back_populates="instance")
    logs = relationship("WorkflowLog", back_populates="instance")


class WorkflowTask(Base):
    """工作流任务"""
    __tablename__ = "workflow_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)
    
    node_id = Column(String(100), nullable=False)
    node_name = Column(String(200), nullable=False)
    node_type = Column(String(50), nullable=True, comment="节点类型: approval/task/cc/data_fill等")
    
    # 升级扩展字段（按照 dd4chat.txt 方案）
    node_config = Column(JSON, default=dict, comment="节点配置快照")
    due_date = Column(DateTime, nullable=True, comment="截止时间")
    priority = Column(Integer, default=0, comment="优先级")
    variables = Column(JSON, default=dict, comment="任务级变量")
    
    # ===== SLA 超时管理（升级方案 4.4） =====
    sla_config = Column(JSON, default=dict, comment="SLA配置: {deadline_hours, reminder_at, escalate_to}")
    sla_deadline = Column(DateTime, nullable=True, comment="SLA截止时间")
    sla_status = Column(String(20), default="normal", comment="SLA状态: normal/warning/overdue/escalated")
    reminder_sent = Column(JSON, default=list, comment="已发送的提醒时间")
    
    # 处理人
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 状态
    status = Column(String(50), default="pending", comment="pending/approved/rejected/transferred")
    opinion = Column(Text, nullable=True, comment="审批意见")
    
    # 时间
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    instance = relationship("WorkflowInstance", back_populates="tasks")
    assignee = relationship("User")


class WorkflowLog(Base):
    """工作流日志"""
    __tablename__ = "workflow_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)
    
    action = Column(String(50), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    node_id = Column(String(100), nullable=True)
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    instance = relationship("WorkflowInstance", back_populates="logs")
    operator = relationship("User")


class WorkflowNodeInstance(Base):
    """工作流节点实例（记录每个节点执行历史）"""
    __tablename__ = "workflow_node_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=False)
    node_id = Column(String(100), nullable=False)
    node_name = Column(String(200), nullable=True)
    node_type = Column(String(50), nullable=True)
    status = Column(String(20), default="pending", comment="pending, running, completed, skipped")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    variables = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    instance = relationship("WorkflowInstance")


class WorkflowVariableLog(Base):
    """工作流变量日志（用于历史追踪）"""
    __tablename__ = "workflow_variable_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("workflow_instances.id"), nullable=True)
    var_name = Column(String(100), nullable=False)
    var_value = Column(Text, nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime, server_default=func.now())
    
    # 关系
    instance = relationship("WorkflowInstance")
    changer = relationship("User")


class WorkflowTaskCandidates(Base):
    """工作流任务候选人表（支持多候选人/组）"""
    __tablename__ = "workflow_task_candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("workflow_tasks.id"), nullable=False)
    candidate_type = Column(String(20), comment="user, role, dept")
    candidate_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    task = relationship("WorkflowTask")


class SubTableData(Base):
    """子表/明细表数据 — 存储主表记录的子表行"""
    __tablename__ = "subtable_data"

    id = Column(Integer, primary_key=True, index=True)
    parent_record_id = Column(Integer, nullable=False, comment="主表记录ID（动态表中的 id）")
    parent_table_name = Column(String(200), nullable=False, comment="主表动态表名（如 form_data_1）")
    parent_field_name = Column(String(100), nullable=False, comment="主表中子表字段名")
    row_index = Column(Integer, default=0, comment="行序号（从0开始）")
    row_data = Column(JSON, default=dict, comment="子表行数据 JSON")
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True, comment="关联模板ID")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    template = relationship("Template")
