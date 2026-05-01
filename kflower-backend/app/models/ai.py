"""
数据库模型 - AI对话和知识库
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AIConversation(Base):
    """AI对话"""
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 对话内容
    messages = Column(JSON, default=list)

    # AI能力类型
    ai_type = Column(String(50), default="general", comment="general/template/workflow/analytics")

    # 关联业务（可选）
    related_type = Column(String(50), nullable=True, comment="template/workflow/permission")
    related_id = Column(Integer, nullable=True)

    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", foreign_keys="AIConversation.user_id", lazy="selectin")
    organization = relationship("Organization", lazy="selectin")


class KnowledgeBase(Base):
    """知识库"""
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True)
    description = Column(Text, nullable=True)

    # 知识库配置
    config = Column(JSON, default=dict)
    embedding_model = Column(String(200), default="text-embedding-v2", comment="嵌入模型")
    rerank_model = Column(String(200), nullable=True, comment="重排模型（AI模型ID或rerank模型名）")
    rerank_enabled = Column(Boolean, default=False, comment="是否启用检索重排")

    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 统计
    doc_count = Column(Integer, default=0)
    vector_count = Column(Integer, default=0)

    # 状态
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    organization = relationship("Organization", lazy="selectin")
    creator = relationship("User", foreign_keys="KnowledgeBase.created_by", lazy="selectin")
    documents = relationship("KnowledgeDocument", back_populates="knowledge_base")

    def __repr__(self):
        return f"<KnowledgeBase {self.name}>"


class KnowledgeDocument(Base):
    """知识文档"""
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)

    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)

    # 文件信息
    file_name = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(50), nullable=True)

    # 向量信息
    vector_id = Column(String(100), nullable=True)
    chunk_count = Column(Integer, default=0)

    # 解析状态
    parsing_status = Column(String(50), default="pending", comment="pending/processing/completed/failed")
    parsing_error = Column(Text, nullable=True)

    # 新增：关键词、摘要、标签
    keywords = Column(JSON, default=list, comment="文档关键词列表")
    summary = Column(Text, nullable=True, comment="文档摘要")
    tags = Column(JSON, default=list, comment="文档标签列表")

    # 状态
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    # 通过关联表关联标签
    doc_tags = relationship("KnowledgeTag", secondary="knowledge_document_tags", back_populates="documents")


class KnowledgeTag(Base):
    """知识库标签"""
    __tablename__ = "knowledge_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default="#1890ff", comment="标签颜色")
    description = Column(String(500), nullable=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=True, comment="所属知识库，为空表示全局标签")

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
    documents = relationship("KnowledgeDocument", secondary="knowledge_document_tags", back_populates="doc_tags")


class KnowledgeDocumentTag(Base):
    """文档-标签关联表"""
    __tablename__ = "knowledge_document_tags"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("knowledge_tags.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class KnowledgeNote(Base):
    """知识笔记"""
    __tablename__ = "knowledge_notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)

    # 标签（JSON数组，存储标签名列表）
    tags = Column(JSON, default=list, comment="标签列表")

    # 是否为每日笔记
    is_daily = Column(Boolean, default=False, comment="是否每日笔记")
    note_date = Column(String(20), nullable=True, comment="笔记日期 YYYY-MM-DD")

    # 关联知识库（可选）
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=True)

    # 组织/用户
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", foreign_keys="KnowledgeNote.created_by", lazy="selectin")
    organization = relationship("Organization", lazy="selectin")
    knowledge_base = relationship("KnowledgeBase", lazy="selectin")


class SystemConfig(Base):
    """系统配置"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string", comment="string/json/boolean/number")
    group = Column(String(50), default="general", comment="分组")
    description = Column(String(500), nullable=True)

    # 组织（为空表示全局配置）
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    is_system = Column(Boolean, default=False)  # 系统内置不可删除
    is_secret = Column(Boolean, default=False)  # 敏感配置

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemConfig {self.key}>"


class AuditLog(Base):
    """审计日志"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # 操作信息
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)

    # 详情
    detail = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # AI相关
    ai_type = Column(String(50), nullable=True, comment="涉及AI能力类型")
    ai_prompt = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", foreign_keys="AuditLog.user_id", lazy="selectin")
    organization = relationship("Organization", lazy="selectin")


class AITask(Base):
    """AI 任务记录表（异步任务）"""
    __tablename__ = "ai_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False, comment="recommend_fields / data_query / anomaly_detection / ...")
    status = Column(String(20), default="pending", comment="pending / processing / completed / failed")
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    # 关系
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")


class AIUsageLog(Base):
    """AI 模型调用日志（成本追踪）"""
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    capability = Column(String(50), nullable=False, comment="调用的能力类型")
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Numeric(10, 6), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 可选：关联用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")


class AIRecommendationCache(Base):
    """智能推荐缓存（避免重复调用）"""
    __tablename__ = "ai_recommendation_cache"

    id = Column(Integer, primary_key=True, index=True)
    context_hash = Column(String(64), unique=True, nullable=False)
    context_type = Column(String(50), nullable=True, comment="field_recommendation / approver_recommendation")
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)


class Agent(Base):
    """智能体配置"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    agent_type = Column(String(50), nullable=False, comment="智能体类型: template_agent, workflow_agent, analytics_agent, query_agent, general_agent, custom")
    description = Column(Text, nullable=True)

    # 配置
    config = Column(JSON, default=dict, comment="智能体配置（提示词、工具、参数等）")
    tools = Column(JSON, default=list, comment="关联的工具列表")

    # ===== 模块绑定（整合优化 1.2） =====
    template_ids = Column(JSON, default=list, comment="绑定的模板ID列表")
    workflow_ids = Column(JSON, default=list, comment="绑定的工作流ID列表")
    knowledge_base_ids = Column(JSON, default=list, comment="绑定的知识库ID列表")
    plugin_ids = Column(JSON, default=list, comment="使用的插件列表")
    system_prompt = Column(Text, nullable=True, comment="专属系统提示词，覆盖默认提示词")
    scope = Column(String(20), default="global", comment="作用域: global/app/template/workflow")

    # 状态
    status = Column(String(20), default="offline", comment="online, offline, disabled")
    task_count = Column(Integer, default=0, comment="已处理任务数")

    # 组织/用户
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    organization = relationship("Organization", lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")

    def __repr__(self):
        return f"<Agent {self.name}>"
