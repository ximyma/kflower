"""
我的应用模块 - API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

from app.modules.my_apps.service import my_apps_service
from app.modules.my_apps.schemas import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, AppDetailResponse,
    AppMenuCreate, AppMenuUpdate, AppMenuResponse,
    FormRelationCreate, FormRelationUpdate, FormRelationResponse,
    AppPluginCreate, AppPluginUpdate, AppPluginResponse,
    MenuTreeNode
)
from app.modules.my_apps.models import Application, AppMenu, FormRelation, AppPlugin

router = APIRouter(prefix="/apps", tags=["我的应用"])


# ============ 应用管理 ============
@router.post("/", response_model=ApplicationResponse)
async def create_app(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建应用"""
    return await my_apps_service.create_app(db, current_user, data)


@router.get("/", response_model=List[ApplicationResponse])
async def list_apps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用列表"""
    return await my_apps_service.get_apps(db, current_user)


@router.get("/{app_id}", response_model=AppDetailResponse)
async def get_app(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用详情（包含菜单、关系、插件）"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return app


@router.put("/{app_id}")
async def update_app(
    app_id: int,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新应用"""
    from sqlalchemy import select
    from app.modules.my_apps.models import Application
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.created_by == current_user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 直接更新，返回简化响应避免序列化问题
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(app, key, value)
    await db.commit()
    await db.refresh(app)
    
    return {
        "id": app.id,
        "code": app.code,
        "name": app.name,
        "description": app.description,
        "icon": app.icon,
        "theme": app.theme,
        "config": app.config,
        "is_published": app.is_published,
        "is_public": app.is_public,
        "created_by": app.created_by,
        "organization_id": app.organization_id,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
    }


@router.delete("/{app_id}")
async def delete_app(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除应用"""
    # 先验证应用存在且属于当前用户
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    # delete_app 需要 ORM 对象，重新查询
    await my_apps_service.delete_app(db, app_id)
    return {"message": "删除成功"}


@router.post("/{app_id}/publish", response_model=ApplicationResponse)
async def publish_app_endpoint(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发布应用"""
    return await my_apps_service.publish_app(db, app_id)


@router.post("/{app_id}/unpublish", response_model=ApplicationResponse)
async def unpublish_app_endpoint(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤回应用（取消发布）"""
    return await my_apps_service.unpublish_app(db, app_id)


# ============ 菜单管理 ============
@router.post("/{app_id}/menus", response_model=AppMenuResponse)
async def add_menu(
    app_id: int,
    data: AppMenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加菜单"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return await my_apps_service.add_menu(db, app_id, data)


@router.put("/menus/{menu_id}", response_model=AppMenuResponse)
async def update_menu(
    menu_id: int,
    data: AppMenuUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新菜单"""
    result = await db.execute(select(AppMenu).where(AppMenu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    return await my_apps_service.update_menu(db, menu, data)


@router.delete("/menus/{menu_id}")
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除菜单"""
    result = await db.execute(select(AppMenu).where(AppMenu.id == menu_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    await my_apps_service.delete_menu(db, menu)
    return {"message": "删除成功"}


@router.get("/{app_id}/menus/tree", response_model=List[MenuTreeNode])
async def get_menu_tree(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取菜单树"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return await my_apps_service.get_menu_tree(db, app_id)


# ============ 表单关系管理 ============
@router.post("/{app_id}/relations", response_model=FormRelationResponse)
async def add_relation(
    app_id: int,
    data: FormRelationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加表单关系"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return await my_apps_service.add_relation(db, app_id, data)


@router.get("/{app_id}/relations", response_model=List[FormRelationResponse])
async def list_relations(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用的关系列表"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return await my_apps_service.get_relations(db, app_id)


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除关系"""
    result = await db.execute(select(FormRelation).where(FormRelation.id == relation_id))
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="关系不存在")
    await my_apps_service.delete_relation(db, relation)
    return {"message": "删除成功"}


# ============ 插件管理 ============
@router.post("/{app_id}/plugins", response_model=AppPluginResponse)
async def add_plugin(
    app_id: int,
    data: AppPluginCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加插件"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return await my_apps_service.add_plugin(db, app_id, data)


@router.get("/{app_id}/plugins", response_model=List[AppPluginResponse])
async def list_plugins(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用的插件列表"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    return await my_apps_service.get_plugins(db, app_id)


@router.put("/plugins/{plugin_id}", response_model=AppPluginResponse)
async def update_plugin(
    plugin_id: int,
    data: AppPluginUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新插件"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return await my_apps_service.update_plugin(db, plugin, data)


@router.delete("/plugins/{plugin_id}")
async def delete_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除插件"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    await my_apps_service.delete_plugin(db, plugin)
    return {"message": "删除成功"}
