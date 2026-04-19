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
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    menus = relationship("AppMenu", back_populates="app", cascade="all, delete-orphan")
    relations = relationship("FormRelation", back_populates="app", cascade="all, delete-orphan")
    plugins = relationship("AppPlugin", back_populates="app", cascade="all, delete-orphan")
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
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    app = relationship("Application", back_populates="menus")
    parent = relationship("AppMenu", remote_side=[id], backref="children")
    template = relationship("Template")


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
