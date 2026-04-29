"""
插件绑定模型 - 模板/应用与插件的关联关系
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TemplatePlugin(Base):
    """模板-插件绑定表"""
    __tablename__ = "template_plugins"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False)
    config = Column(JSON, default=dict, comment="插件在此模板的配置参数")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系（使用类引用，字符串引用在跨模块时可能引发 mapper 配置顺序问题）
    plugin = relationship("Plugin", back_populates="template_plugins")


class AppPlugin(Base):
    """应用-插件绑定表"""
    __tablename__ = "app_plugins"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False)
    config = Column(JSON, default=dict, comment="插件在此应用的配置参数")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    plugin = relationship("Plugin", back_populates="app_plugins")
