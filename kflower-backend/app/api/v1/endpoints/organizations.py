"""
API路由 - 组织架构
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Organization
from app.schemas.schemas import BaseResponse, OrganizationCreate

router = APIRouter(prefix="/organizations", tags=["组织架构"])


@router.get("/", response_model=BaseResponse)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织架构树"""
    result = await db.execute(select(Organization).order_by(Organization.sort_order))
    orgs = result.scalars().all()
    
    return BaseResponse(data={
        "organizations": [
            {
                "id": org.id,
                "name": org.name,
                "code": org.code,
                "parent_id": org.parent_id,
                "level": org.level,
                "path": org.path,
                "is_active": org.is_active,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "userCount": 0,  # 后续统计
            }
            for org in orgs
        ]
    })


@router.post("/", response_model=BaseResponse)
async def create_organization(
    request: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建组织"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 计算层级和路径
    level = 1
    path = "/"
    if request.parent_id:
        parent = await db.get(Organization, request.parent_id)
        if parent:
            level = parent.level + 1
            path = parent.path + str(parent.id) + "/"
    
    org = Organization(
        name=request.name,
        code=request.code,
        parent_id=request.parent_id,
        level=level,
        path=path,
        description=request.description,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    
    return BaseResponse(message="组织创建成功", data={"id": org.id})


@router.get("/{org_id}", response_model=BaseResponse)
async def get_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织详情"""
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    # 统计用户数
    result = await db.execute(
        select(User).where(User.organization_id == org_id)
    )
    user_count = len(result.scalars().all())
    
    return BaseResponse(data={
        "id": org.id,
        "name": org.name,
        "code": org.code,
        "parent_id": org.parent_id,
        "level": org.level,
        "path": org.path,
        "description": org.description,
        "is_active": org.is_active,
        "user_count": user_count,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    })


@router.delete("/{org_id}", response_model=BaseResponse)
async def delete_organization(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除组织"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    
    await db.delete(org)
    await db.commit()
    
    return BaseResponse(message="组织已删除")
