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
