"""
数据库模型 - 用户和组织架构
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organization(Base):
    """组织架构"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="组织名称")
    code = Column(String(100), unique=True, comment="组织编码")
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, comment="父组织ID")
    level = Column(Integer, default=1, comment="层级")
    path = Column(String(500), comment="路径")
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    parent = relationship("Organization", remote_side=[id], backref="children")


class Role(Base):
    """角色"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # 角色类型: system(系统内置), custom(自定义)
    type = Column(String(20), default="custom")
    
    # 数据权限范围: all(全部), self(本人), department(本部门), custom(自定义)
    data_scope = Column(String(20), default="all")
    
    is_system = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # 权限列表 (JSON格式存储权限ID)
    permissions = Column(JSON, default=list)
    
    # 数据权限规则
    data_permission_rules = Column(JSON, default=list)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class User(Base):
    """用户"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar = Column(String(500), nullable=True)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    organization = relationship("Organization")


class UserRole(Base):
    """用户角色关联"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
