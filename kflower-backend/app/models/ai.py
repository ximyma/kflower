"""
数据库模型 - AI对话和知识库
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
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
    user = relationship("User")
    organization = relationship("Organization")


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
    organization = relationship("Organization")
    creator = relationship("User")
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
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


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
    user = relationship("User")
    organization = relationship("Organization")
