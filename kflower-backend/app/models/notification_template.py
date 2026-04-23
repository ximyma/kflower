"""
通知模板模型
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NotificationTemplate(Base):
    """通知模板"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    code = Column(String(100), unique=True, comment="模板编码")
    description = Column(Text, nullable=True, comment="模板描述")

    # 渠道和内容
    channels = Column(JSON, default=lambda: ["system"], comment="支持渠道: [system,email,sms,wecom,dingtalk]")
    subject = Column(String(500), nullable=True, comment="通知标题（邮件/站内信）")
    content = Column(Text, nullable=False, comment="通知内容模板，支持变量 {title},{applicant},{status},{result},{url},{comment}")

    # 分类和类型
    category = Column(String(50), default="general", comment="分类: approval/reminder/system/task/escalation")
    event_type = Column(String(50), nullable=True, comment="触发事件: task_assigned/approval_completed/deadline_reminder/escalation/custom")

    # 状态
    is_system = Column(Boolean, default=False, comment="是否系统内置模板")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
