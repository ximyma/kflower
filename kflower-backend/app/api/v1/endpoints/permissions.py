"""
权限管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.permission import Permission, DataPermission
from app.models.user import Organization, User, Role

router = APIRouter(prefix="/permissions", tags=["权限管理"])


# ============ Pydantic Schema ============

class PermissionCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    type: str = "api"
    resource: Optional[str] = None
    method: Optional[str] = None
    icon: Optional[str] = None
    path: Optional[str] = None
    order: int = 0
    parent_id: Optional[int] = None


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    type: str
    resource: Optional[str]
    method: Optional[str]
    icon: Optional[str]
    path: Optional[str]
    order: int
    parent_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    type: str = "custom"
    data_scope: str = "all"
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    type: str
    data_scope: str
    is_active: bool
    is_default: bool
    permissions: List[int] = []

    class Config:
        from_attributes = True


class RoleAssign(BaseModel):
    user_ids: List[int]
    role_ids: List[int]


# ============ 角色管理（放在 /{permission_id} 之前避免路由冲突） ============

@router.get("/roles/", response_model=List[RoleResponse])
async def list_roles(
    type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    query = select(Role)
    
    if type:
        query = query.where(Role.type == type)
    
    result = await db.execute(query.order_by(Role.id))
    roles = result.scalars().all()
    
    # 转换为响应格式
    return [
        RoleResponse(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            type=role.type,
            data_scope=role.data_scope,
            is_active=role.is_active,
            is_default=role.is_default,
            permissions=role.permissions or []
        ) for role in roles
    ]


@router.post("/roles/", response_model=RoleResponse)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建角色"""
    result = await db.execute(
        select(Role).where(Role.code == data.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="角色代码已存在")
    
    role = Role(
        code=data.code,
        name=data.name,
        description=data.description,
        type=data.type,
        data_scope=data.data_scope,
        permissions=data.permission_ids
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    return RoleResponse(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        type=role.type,
        data_scope=role.data_scope,
        is_active=role.is_active,
        is_default=role.is_default,
        permissions=role.permissions or []
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色"""
    result = await db.execute(
        select(Role).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    permission_ids = update_data.pop("permission_ids", None)
    
    for key, value in update_data.items():
        setattr(role, key, value)
    
    if permission_ids is not None:
        role.permissions = permission_ids
    
    await db.commit()
    await db.refresh(role)
    
    return RoleResponse(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        type=role.type,
        data_scope=role.data_scope,
        is_active=role.is_active,
        is_default=role.is_default,
        permissions=role.permissions or []
    )


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色"""
    result = await db.execute(
        select(Role).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.is_default:
        raise HTTPException(status_code=400, detail="默认角色不能删除")
    
    role.is_active = False
    await db.commit()
    return {"message": "删除成功"}


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色详情"""
    result = await db.execute(
        select(Role).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return RoleResponse(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        type=role.type,
        data_scope=role.data_scope,
        is_active=role.is_active,
        is_default=role.is_default,
        permissions=role.permissions or []
    )


# ============ 初始化默认权限 ============

# ============ 权限管理（放在角色路由之后，避免 {permission_id} 与 roles 冲突） ============

@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    type: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限列表"""
    query = select(Permission).where(Permission.is_active == True)
    
    if type:
        query = query.where(Permission.type == type)
    if parent_id is not None:
        query = query.where(Permission.parent_id == parent_id)
    
    result = await db.execute(query.order_by(Permission.order, Permission.id))
    permissions = result.scalars().all()
    return permissions


@router.post("/", response_model=PermissionResponse)
async def create_permission(
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建权限"""
    result = await db.execute(
        select(Permission).where(Permission.code == data.code)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="权限代码已存在")
    
    permission = Permission(**data.model_dump())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


@router.get("/init", response_model=dict)
async def init_permissions_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查初始化状态"""
    result = await db.execute(select(Permission).limit(1))
    exists = result.scalar_one_or_none() is not None
    return {"initialized": exists}


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限详情"""
    result = await db.execute(
        select(Permission).where(Permission.id == permission_id)
    )
    permission = result.scalar_one_or_none()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    return permission


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除权限"""
    result = await db.execute(
        select(Permission).where(Permission.id == permission_id)
    )
    permission = result.scalar_one_or_none()
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    permission.is_active = False
    await db.commit()
    return {"message": "删除成功"}


@router.post("/init")
async def init_default_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """初始化默认权限和角色"""
    
    # 检查是否已初始化
    result = await db.execute(select(Role).where(Role.code == "admin"))
    if result.scalar_one_or_none():
        return {"message": "已初始化，跳过"}
    
    # 创建默认权限
    default_permissions = [
        {"code": "system:user:view", "name": "查看用户", "type": "api", "resource": "/api/v1/users", "method": "GET"},
        {"code": "system:user:create", "name": "创建用户", "type": "api", "resource": "/api/v1/users", "method": "POST"},
        {"code": "system:user:update", "name": "更新用户", "type": "api", "resource": "/api/v1/users/{id}", "method": "PUT"},
        {"code": "system:user:delete", "name": "删除用户", "type": "api", "resource": "/api/v1/users/{id}", "method": "DELETE"},
        {"code": "system:role:view", "name": "查看角色", "type": "api", "resource": "/api/v1/permissions/roles", "method": "GET"},
        {"code": "system:role:manage", "name": "管理角色", "type": "api", "resource": "/api/v1/permissions/roles", "method": "POST"},
        {"code": "system:permission:view", "name": "查看权限", "type": "api", "resource": "/api/v1/permissions", "method": "GET"},
        {"code": "system:permission:manage", "name": "管理权限", "type": "api", "resource": "/api/v1/permissions", "method": "POST"},
    ]
    
    perm_ids = []
    for perm_data in default_permissions:
        perm = Permission(**perm_data)
        db.add(perm)
        await db.flush()
        perm_ids.append(perm.id)
    
    # 创建默认角色
    roles = [
        Role(code="admin", name="系统管理员", type="system", data_scope="all", permissions=perm_ids, is_default=True),
        Role(code="user", name="普通用户", type="system", data_scope="self", permissions=[]),
        Role(code="manager", name="部门经理", type="system", data_scope="department", permissions=[1, 5, 7]),
    ]
    
    for role in roles:
        db.add(role)
    
    await db.commit()
    return {"message": "初始化成功", "permissions": len(default_permissions), "roles": len(roles)}
