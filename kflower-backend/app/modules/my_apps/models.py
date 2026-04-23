"""
我的应用模块 - 数据库模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Application(Base):
    """应用表"""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    theme = Column(String(50), default="light")
    config = Column(JSON, default=dict)
    is_published = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # ===== 流程审批集成（升级方案 4.1） =====
    workflow_ids = Column(JSON, default=list, comment="应用关联的多个工作流列表: [{workflow_id, trigger, config}]")
    workflow_config = Column(JSON, default=dict, comment="全局流程配置: 全局超时时间、通知方式等")
    
    # ===== 知识库集成（升级方案 7.1） =====
    knowledge_base_ids = Column(JSON, default=list, comment="应用绑定的知识库ID列表")
    knowledge_config = Column(JSON, default=dict, comment="知识库配置: auto_index, search_scope, chunk_size")
    
    # ===== 智能体集成（升级方案 5.2） =====
    bound_agents = Column(JSON, default=list, comment="应用绑定的智能体: [{agent_id, context, trigger}]")
    
    # ===== 版本管理（升级方案 5.4） =====
    current_version = Column(String(20), default="1.0.0", comment="当前版本号")
    changelog = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    menus = relationship("AppMenu", back_populates="app", cascade="all, delete-orphan")
    relations = relationship("FormRelation", back_populates="app", cascade="all, delete-orphan")
    plugins = relationship("AppPlugin", back_populates="app", cascade="all, delete-orphan")
    versions = relationship("AppVersion", back_populates="app", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class AppMenu(Base):
    """应用菜单"""
    __tablename__ = "app_menus"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("app_menus.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    menu_label = Column(String(100), nullable=False)
    menu_icon = Column(String(100), nullable=True)
    menu_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    list_page_config = Column(JSON, default=dict)
    form_page_config = Column(JSON, default=dict)
    
    # ===== 流程审批集成（升级方案 4.1） =====
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True, comment="关联的工作流ID")
    workflow_trigger = Column(String(20), default="manual", comment="触发方式: manual/submit/update")
    workflow_field_permissions = Column(JSON, default=dict, comment="流程中字段权限: {node_id: {field: readonly/hidden/edit}}")
    workflow_auto_approve = Column(Boolean, default=False, comment="提交后自动发起流程")
    workflow_node_mapping = Column(JSON, default=dict, comment="表单字段到流程变量的映射")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    app = relationship("Application", back_populates="menus")
    parent = relationship("AppMenu", remote_side=[id], backref="children")
    template = relationship("Template")
    workflow = relationship("Workflow")


class FormRelation(Base):
    """表单关系"""
    __tablename__ = "form_relations"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    from_template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    from_field_name = Column(String(100), nullable=False)
    to_template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    relation_type = Column(String(20), nullable=False)  # belongs_to, has_many, many_to_many
    display_field = Column(String(100), nullable=True)
    on_delete = Column(String(20), default="set_null")
    reverse_name = Column(String(100), nullable=True)
    auto_fill_fields = Column(JSON, nullable=True)  # 自动填充字段映射 [{"from": "name", "to": "customer_name"}]
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    app = relationship("Application", back_populates="relations")
    from_template = relationship("Template", foreign_keys=[from_template_id])
    to_template = relationship("Template", foreign_keys=[to_template_id])


class AppPlugin(Base):
    """应用插件"""
    __tablename__ = "app_plugins"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    name = Column(String(100), nullable=False)
    trigger_event = Column(String(50), nullable=False)  # before_save, after_save, before_delete, after_delete, on_load
    target_template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    script_code = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    app = relationship("Application", back_populates="plugins")
    target_template = relationship("Template")


class AppVersion(Base):
    """应用版本快照（升级方案 5.4）"""
    __tablename__ = "app_versions"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    version = Column(String(20), nullable=False, comment="版本号如1.0.0")
    snapshot = Column(JSON, nullable=False, comment="完整应用快照")
    changelog = Column(Text, nullable=True, comment="变更日志")
    is_stable = Column(Boolean, default=False, comment="是否稳定版")
    is_current = Column(Boolean, default=False, comment="是否为当前版本")
    published_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    app = relationship("Application", back_populates="versions")
    publisher = relationship("User")

    def __repr__(self):
        return f"<AppVersion app={self.app_id} v{self.version}>"
