"""
权限管理模型 - Permission 和 DataPermission
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# 角色-权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Permission(Base):
    """权限"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True, comment="权限代码")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(Text, nullable=True, comment="描述")
    
    # 权限类型
    type = Column(String(50), default="api", comment="api/menu/button/data")
    
    # 资源路径（用于API权限）
    resource = Column(String(200), nullable=True, comment="资源路径")
    method = Column(String(20), nullable=True, comment="HTTP方法")
    
    # 菜单配置
    icon = Column(String(100), nullable=True, comment="菜单图标")
    path = Column(String(200), nullable=True, comment="菜单路径")
    order = Column(Integer, default=0, comment="排序")
    parent_id = Column(Integer, ForeignKey("permissions.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    parent = relationship("Permission", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<Permission {self.code}>"


class DataPermission(Base):
    """数据权限规则"""
    __tablename__ = "data_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True)
    
    # 权限规则配置
    rules = Column(JSON, default=list, comment="规则配置")
    
    # 关联角色
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DataPermission {self.name}>"
