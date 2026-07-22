"""
通知记录模型
用于工作流、智能体等系统通知的持久化存储
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Notification(Base):
    """通知记录"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="接收用户ID")
    title = Column(String(500), nullable=False, comment="通知标题")
    content = Column(Text, nullable=True, comment="通知内容")
    
    # 分类
    type = Column(String(50), default="system", comment="通知类型: workflow/reminder/system/task/escalation")
    channel = Column(String(50), default="system", comment="发送渠道: system/email/sms/wecom")
    
    # 关联
    source_type = Column(String(50), nullable=True, comment="来源类型: workflow/agent/template/plugin")
    source_id = Column(Integer, nullable=True, comment="来源ID")
    
    # 状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")
    
    # 创建信息
    created_at = Column(DateTime, server_default=func.now())
