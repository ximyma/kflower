"""
我的应用模块 - API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

from app.modules.my_apps.service import my_apps_service
from app.modules.my_apps.schemas import (
    ApplicationCreate, ApplicationUpdate, ApplicationResponse, AppDetailResponse,
    AppMenuCreate, AppMenuUpdate, AppMenuResponse, AppMenuSimple,
    FormRelationCreate, FormRelationUpdate, FormRelationResponse,
    AppPluginCreate, AppPluginUpdate, AppPluginResponse,
    MenuTreeNode, VersionCreate, VersionResponse
)
from app.schemas.schemas import BaseResponse
from app.modules.my_apps.models import Application, AppMenu, FormRelation, AppPluginBinding, AppVersion

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
    # aiosqlite 下 JSON 列需要 flag_modified 才能触发脏检测
    json_columns = {'config', 'workflow_ids', 'workflow_config', 'knowledge_base_ids', 'knowledge_config', 'bound_agents'}
    for key, value in update_data.items():
        setattr(app, key, value)
        if key in json_columns:
            flag_modified(app, key)
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
@router.post("/{app_id}/menus", response_model=AppMenuSimple)
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


# ============ 系统插件管理（新版 AppPluginService，精确路由必须在通配路由前面） ============

@router.get("/{app_id}/plugins/bindings", response_model=BaseResponse)
async def get_app_plugin_bindings(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用的系统插件绑定列表"""
    from app.services.app_plugin_service import AppPluginService
    try:
        plugins = AppPluginService.get_app_plugins(app_id)
        return BaseResponse(success=True, data=plugins)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.get("/{app_id}/plugins/available", response_model=BaseResponse)
async def get_available_plugins_for_app(
    app_id: int,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取可绑定到应用的系统插件列表"""
    from app.services.app_plugin_service import AppPluginService
    try:
        plugins = AppPluginService.get_available_plugins(app_id)

        if search:
            search_lower = search.lower()
            plugins = [p for p in plugins if
                search_lower in (p.get("name") or "").lower() or
                search_lower in (p.get("display_name") or "").lower() or
                search_lower in (p.get("description") or "").lower()]

        if category:
            plugins = [p for p in plugins if p.get("category") == category]

        return BaseResponse(success=True, data=plugins)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.post("/{app_id}/plugins/bind", response_model=BaseResponse)
async def bind_plugin_to_app(
    app_id: int,
    bind_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将系统插件绑定到应用"""
    from app.services.app_plugin_service import AppPluginService
    plugin_id = bind_data.get("plugin_id")
    if not plugin_id:
        raise HTTPException(status_code=400, detail="plugin_id 不能为空")
    try:
        result = AppPluginService.bind_plugin(
            app_id=app_id,
            plugin_id=plugin_id,
            config=bind_data.get("config", {}),
            sort_order=bind_data.get("sort_order", 0)
        )
        return BaseResponse(success=result["success"], message=result.get("message"), data=result.get("data"))
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.post("/{app_id}/plugins/trigger", response_model=BaseResponse)
async def trigger_app_plugin_hook(
    app_id: int,
    hook_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发应用插件钩子（测试用）"""
    from app.services.app_plugin_service import AppPluginService
    hook_name = hook_data.get("hook_name")
    context = hook_data.get("context", {})
    if not hook_name:
        raise HTTPException(status_code=400, detail="hook_name 不能为空")
    try:
        result = AppPluginService.trigger_app_plugin_hook(app_id, hook_name, context)
        return BaseResponse(success=True, data=result)
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.delete("/{app_id}/plugins/{binding_id}", response_model=BaseResponse)
async def unbind_app_plugin(
    app_id: int,
    binding_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解除应用与系统插件的绑定"""
    from app.services.app_plugin_service import AppPluginService
    try:
        result = AppPluginService.unbind_plugin(app_id, binding_id)
        return BaseResponse(success=result["success"], message=result.get("message"))
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.put("/{app_id}/plugins/{binding_id}", response_model=BaseResponse)
async def update_app_plugin_binding(
    app_id: int,
    binding_id: int,
    update_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新应用插件绑定配置"""
    from app.services.app_plugin_service import AppPluginService
    try:
        updates = {}
        if "is_enabled" in update_data:
            updates["is_enabled"] = update_data["is_enabled"]
        if "config" in update_data:
            updates["config"] = update_data["config"]
        if "sort_order" in update_data:
            updates["sort_order"] = update_data["sort_order"]

        result = AppPluginService.update_plugin_binding(
            app_id=app_id,
            binding_id=binding_id,
            updates=updates
        )
        return BaseResponse(success=result["success"], message=result.get("message"))
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


# ============ 业务插件管理（旧版 AppPlugin ORM 模型） ============
@router.post("/{app_id}/plugins", response_model=AppPluginResponse)
async def add_plugin(
    app_id: int,
    data: AppPluginCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加业务插件脚本"""
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
    """获取应用的业务插件脚本列表"""
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
    """更新业务插件脚本"""
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
    """删除业务插件脚本"""
    result = await db.execute(select(AppPlugin).where(AppPlugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    await my_apps_service.delete_plugin(db, plugin)
    return {"message": "删除成功"}


# ============ 版本管理（升级方案 5.4） ============
@router.get("/{app_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用版本列表"""
    app = await my_apps_service.get_app(db, app_id, current_user)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    result = await db.execute(
        select(AppVersion)
        .where(AppVersion.app_id == app_id)
        .order_by(AppVersion.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{app_id}/versions", response_model=VersionResponse)
async def create_version(
    app_id: int,
    data: VersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新版本快照"""
    from sqlalchemy.orm import selectinload
    from datetime import datetime
    
    # 获取应用完整数据
    query = select(Application).options(
        selectinload(Application.menus),
        selectinload(Application.relations),
        selectinload(Application.plugins)
    ).where(Application.id == app_id)
    
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 构建快照
    snapshot = {
        "name": app.name,
        "description": app.description,
        "icon": app.icon,
        "theme": app.theme,
        "config": app.config,
        "workflow_ids": app.workflow_ids,
        "workflow_config": app.workflow_config,
        "knowledge_base_ids": app.knowledge_base_ids,
        "knowledge_config": app.knowledge_config,
        "bound_agents": app.bound_agents,
        "menus": [
            {
                "id": m.id,
                "parent_id": m.parent_id,
                "template_id": m.template_id,
                "menu_label": m.menu_label,
                "menu_icon": m.menu_icon,
                "menu_order": m.menu_order,
                "is_visible": m.is_visible,
                "list_page_config": m.list_page_config,
                "form_page_config": m.form_page_config,
                "workflow_id": m.workflow_id,
                "workflow_trigger": m.workflow_trigger,
                "workflow_field_permissions": m.workflow_field_permissions,
                "workflow_auto_approve": m.workflow_auto_approve,
                "workflow_node_mapping": m.workflow_node_mapping,
            }
            for m in app.menus
        ],
        "relations": [
            {
                "id": r.id,
                "from_template_id": r.from_template_id,
                "from_field_name": r.from_field_name,
                "to_template_id": r.to_template_id,
                "relation_type": r.relation_type,
                "display_field": r.display_field,
                "on_delete": r.on_delete,
                "reverse_name": r.reverse_name,
            }
            for r in app.relations
        ],
        "plugins": [
            {
                "id": p.id,
                "name": p.name,
                "trigger_event": p.trigger_event,
                "target_template_id": p.target_template_id,
                "script_code": p.script_code,
                "is_enabled": p.is_enabled,
            }
            for p in app.plugins
        ],
    }
    
    # 清除之前的 is_current
    await db.execute(
        select(AppVersion).where(AppVersion.app_id == app_id, AppVersion.is_current == True)
    )
    # TODO: 批量更新 is_current = False
    
    # 创建版本
    version = AppVersion(
        app_id=app_id,
        version=data.version,
        snapshot=snapshot,
        changelog=data.changelog,
        is_stable=data.is_stable,
        is_current=True,
        published_by=current_user.id,
        published_at=datetime.now()
    )
    db.add(version)
    
    # 更新应用版本号
    app.current_version = data.version
    if data.changelog:
        app.changelog = data.changelog
    
    await db.commit()
    await db.refresh(version)
    
    return version


@router.post("/{app_id}/versions/{version_id}/restore")
async def restore_version(
    app_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复到指定版本"""
    version = await db.get(AppVersion, version_id)
    if not version or version.app_id != app_id:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    app = await db.get(Application, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    snapshot = version.snapshot
    
    # 恢复应用数据
    app.name = snapshot["name"]
    app.description = snapshot.get("description")
    app.icon = snapshot.get("icon")
    app.theme = snapshot.get("theme")
    app.config = snapshot.get("config", {})
    app.workflow_ids = snapshot.get("workflow_ids", [])
    app.workflow_config = snapshot.get("workflow_config", {})
    app.knowledge_base_ids = snapshot.get("knowledge_base_ids", [])
    app.knowledge_config = snapshot.get("knowledge_config", {})
    app.bound_agents = snapshot.get("bound_agents", [])
    app.current_version = version.version
    # aiosqlite 下 JSON 列需要 flag_modified 才能触发脏检测
    for col in ['config', 'workflow_ids', 'workflow_config', 'knowledge_base_ids', 'knowledge_config', 'bound_agents']:
        flag_modified(app, col)
    
    # 删除现有菜单/关系/插件
    for m in await db.execute(select(AppMenu).where(AppMenu.app_id == app_id)):
        await db.delete(m.scalar())
    for r in await db.execute(select(FormRelation).where(FormRelation.app_id == app_id)):
        await db.delete(r.scalar())
    for p in await db.execute(select(AppPlugin).where(AppPlugin.app_id == app_id)):
        await db.delete(p.scalar())
    
    # 恢复菜单
    for menu_data in snapshot.get("menus", []):
        menu = AppMenu(
            app_id=app_id,
            parent_id=menu_data.get("parent_id"),
            template_id=menu_data["template_id"],
            menu_label=menu_data["menu_label"],
            menu_icon=menu_data.get("menu_icon"),
            menu_order=menu_data.get("menu_order", 0),
            is_visible=menu_data.get("is_visible", True),
            list_page_config=menu_data.get("list_page_config", {}),
            form_page_config=menu_data.get("form_page_config", {}),
            workflow_id=menu_data.get("workflow_id"),
            workflow_trigger=menu_data.get("workflow_trigger"),
            workflow_field_permissions=menu_data.get("workflow_field_permissions", {}),
            workflow_auto_approve=menu_data.get("workflow_auto_approve", False),
            workflow_node_mapping=menu_data.get("workflow_node_mapping", []),
        )
        db.add(menu)
    
    # 恢复关系
    for rel_data in snapshot.get("relations", []):
        rel = FormRelation(
            app_id=app_id,
            from_template_id=rel_data["from_template_id"],
            from_field_name=rel_data["from_field_name"],
            to_template_id=rel_data["to_template_id"],
            relation_type=rel_data["relation_type"],
            display_field=rel_data.get("display_field"),
            on_delete=rel_data.get("on_delete", "set_null"),
            reverse_name=rel_data.get("reverse_name"),
        )
        db.add(rel)
    
    
    # 恢复插件
    for plugin_data in snapshot.get("plugins", []):
        plugin = AppPlugin(
            app_id=app_id,
            name=plugin_data["name"],
            trigger_event=plugin_data["trigger_event"],
            target_template_id=plugin_data.get("target_template_id"),
            script_code=plugin_data["script_code"],
            is_enabled=plugin_data.get("is_enabled", True),
        )
        db.add(plugin)
    
    
    await db.commit()
    return {"message": f"已恢复到版本 {version.version}"}


# ============ AI 应用生成 ============

@router.post("/ai-generate")
async def ai_generate_app(
    description: str,
    app_name: str = None,
    skip_workflow: bool = False,
    skip_dashboard: bool = False,
    skip_agent: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI 自动生成应用
    从自然语言描述生成完整应用，包括表单、工作流、关系、仪表盘、智能体
    """
    from app.core.ai_app_generator import get_ai_app_generator
    
    generator = get_ai_app_generator()
    
    result = await generator.generate_from_description(
        description=description,
        db=db,
        user_id=current_user.id,
        organization_id=None,
        app_name=app_name,
        options={
            "skip_workflow": skip_workflow,
            "skip_dashboard": skip_dashboard,
            "skip_agent": skip_agent,
        }
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail="应用生成失败: " + "; ".join(result.get("errors", ["未知错误"]))
        )
    
    return result
