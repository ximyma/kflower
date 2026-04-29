"""
API路由 - 插件管理
支持插件的 CRUD、启用/禁用、模板绑定、钩子测试
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from typing import Optional, List, Dict, Any
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.plugin_manager import get_plugin_manager, BUILTIN_PLUGINS
from app.models.user import User
from app.models.plugin import Plugin, PluginHook
from app.models.plugin_binding import TemplatePlugin
from app.core.plugin_sandbox import test_plugin_hook, get_hook_event_docs, HOOK_EVENTS
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/plugins", tags=["插件管理"])


# ─────────────────────────────────────────────────────────────────────────────
#  插件列表与详情
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=BaseResponse)
async def list_plugins(
    category: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    is_builtin: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取插件列表（支持分类筛选）"""
    query = select(Plugin)

    if category:
        query = query.where(Plugin.category == category)
    if is_enabled is not None:
        query = query.where(Plugin.is_enabled == is_enabled)
    if is_builtin is not None:
        query = query.where(Plugin.is_built_in == is_builtin)
    if search:
        query = query.where(
            or_(
                Plugin.name.ilike(f"%{search}%"),
                Plugin.display_name.ilike(f"%{search}%"),
                Plugin.description.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Plugin.is_built_in.desc(), Plugin.id)
    result = await db.execute(query)
    plugins = result.scalars().all()

    return BaseResponse(success=True, data=[p.to_dict() for p in plugins])


@router.get("/builtin-events", response_model=BaseResponse)
async def list_builtin_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统预置的钩子事件列表"""
    result = await db.execute(select(PluginHook).where(PluginHook.is_active == True))
    hooks = result.scalars().all()
    return BaseResponse(success=True, data=[h.to_dict() for h in hooks])


@router.get("/event-docs", response_model=BaseResponse)
async def get_event_docs(
    current_user: User = Depends(get_current_user)
):
    """获取钩子事件文档（含示例代码）"""
    docs = get_hook_event_docs()
    return BaseResponse(success=True, data=docs)


@router.get("/{plugin_id}", response_model=BaseResponse)
async def get_plugin_detail(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取插件详情"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    return BaseResponse(success=True, data=plugin.to_dict())


# ─────────────────────────────────────────────────────────────────────────────
#  插件生命周期
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=BaseResponse)
async def create_plugin(
    plugin_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新插件（本地/URL安装）"""
    name = plugin_data.get("name", "").strip()
    display_name = plugin_data.get("display_name", "").strip()

    if not name or not display_name:
        raise HTTPException(status_code=400, detail="插件名称和显示名称不能为空")

    # 检查重名
    existing = await db.execute(select(Plugin).where(Plugin.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"插件名 {name} 已存在")

    plugin = Plugin(
        name=name,
        display_name=display_name,
        description=plugin_data.get("description"),
        version=plugin_data.get("version", "1.0.0"),
        author=plugin_data.get("author"),
        homepage=plugin_data.get("homepage"),
        icon=plugin_data.get("icon", "puzzle-piece"),
        category="custom",
        install_type=plugin_data.get("install_type", "local"),
        file_path=plugin_data.get("file_path"),
        download_url=plugin_data.get("download_url"),
        config=plugin_data.get("config", {}),
        hook_code=plugin_data.get("hook_code", {}),
        is_enabled=True,
        is_built_in=False,
        is_installed=True,
        created_by=current_user.id,
    )

    db.add(plugin)
    await db.commit()
    await db.refresh(plugin)

    # 重新初始化插件管理器
    pm = get_plugin_manager()
    pm._load_plugin_instance(plugin)

    return BaseResponse(success=True, message="插件创建成功", data=plugin.to_dict())


@router.put("/{plugin_id}", response_model=BaseResponse)
async def update_plugin(
    plugin_id: int,
    plugin_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新插件配置和钩子代码"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    # 更新字段
    updatable = ["display_name", "description", "version", "author", "homepage",
                  "icon", "config", "hook_code"]
    for field in updatable:
        if field in plugin_data:
            setattr(plugin, field, plugin_data[field])

    await db.commit()
    await db.refresh(plugin)

    # 重新加载插件实例
    pm = get_plugin_manager()
    if plugin.name in pm._loaded_plugins:
        del pm._loaded_plugins[plugin.name]
    pm._load_plugin_instance(plugin)

    return BaseResponse(success=True, message="插件更新成功", data=plugin.to_dict())


@router.post("/{plugin_id}/enable", response_model=BaseResponse)
async def enable_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启用插件"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    plugin.is_enabled = True
    await db.commit()

    pm = get_plugin_manager()
    pm._load_plugin_instance(plugin)

    # 同步 AI 工具状态
    if plugin.category == "ai_tool" and plugin.config:
        tool_name = plugin.config.get("tool_name")
        if tool_name:
            from app.core.agent_engine.tools.registry import tool_registry
            tool_registry.set_tool_enabled(tool_name, True)

    return BaseResponse(success=True, message=f"插件 {plugin.display_name} 已启用")


@router.post("/{plugin_id}/disable", response_model=BaseResponse)
async def disable_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """禁用插件"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    if plugin.is_built_in:
        return BaseResponse(success=False, message="内置插件不能禁用")

    plugin.is_enabled = False
    await db.commit()

    pm = get_plugin_manager()
    msg = pm.disable_plugin(plugin.name)

    # 同步 AI 工具状态
    if plugin.category == "ai_tool" and plugin.config:
        tool_name = plugin.config.get("tool_name")
        if tool_name:
            from app.core.agent_engine.tools.registry import tool_registry
            tool_registry.set_tool_enabled(tool_name, False)

    return BaseResponse(success=True, message=msg["message"])


@router.delete("/{plugin_id}", response_model=BaseResponse)
async def delete_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除插件"""
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()

    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    if plugin.is_built_in:
        return BaseResponse(success=False, message="内置插件不能删除")

    # 从管理器中移除
    pm = get_plugin_manager()
    if plugin.name in pm._loaded_plugins:
        del pm._loaded_plugins[plugin.name]

    # 删除插件（级联删除 TemplatePlugin）
    await db.execute(delete(Plugin).where(Plugin.id == plugin_id))
    await db.commit()

    return BaseResponse(success=True, message="插件已删除")


# ─────────────────────────────────────────────────────────────────────────────
#  模板插件绑定
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/template/{template_id}/bindings", response_model=BaseResponse)
async def list_template_plugins(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板绑定的插件列表"""
    result = await db.execute(
        select(TemplatePlugin, Plugin)
        .join(Plugin, TemplatePlugin.plugin_id == Plugin.id)
        .where(TemplatePlugin.template_id == template_id)
        .order_by(TemplatePlugin.sort_order)
    )
    rows = result.all()

    bindings = []
    for binding, plugin in rows:
        bindings.append({
            "id": binding.id,
            "plugin_id": plugin.id,
            "plugin_name": plugin.name,
            "display_name": plugin.display_name,
            "description": plugin.description,
            "icon": plugin.icon,
            "category": plugin.category,
            "is_enabled": binding.is_enabled,
            "config": binding.config or {},
            "hook_code": plugin.hook_code or {},
            "sort_order": binding.sort_order,
        })

    return BaseResponse(success=True, data=bindings)


@router.post("/template/{template_id}/bind", response_model=BaseResponse)
async def bind_plugin_to_template(
    template_id: int,
    bind_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将插件绑定到模板"""
    plugin_id = bind_data.get("plugin_id")
    config = bind_data.get("config", {})

    if not plugin_id:
        raise HTTPException(status_code=400, detail="plugin_id 不能为空")

    # 检查插件是否存在
    result = await db.execute(select(Plugin).where(Plugin.id == plugin_id))
    plugin = result.scalar_one_or_none()
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")

    # 检查是否已绑定
    existing = await db.execute(
        select(TemplatePlugin).where(
            TemplatePlugin.template_id == template_id,
            TemplatePlugin.plugin_id == plugin_id
        )
    )
    if existing.scalar_one_or_none():
        return BaseResponse(success=False, message="该插件已绑定到此模板")

    binding = TemplatePlugin(
        template_id=template_id,
        plugin_id=plugin_id,
        config=config,
        is_enabled=True,
        sort_order=bind_data.get("sort_order", 0),
    )
    db.add(binding)
    await db.commit()
    await db.refresh(binding)

    return BaseResponse(success=True, message=f"插件 {plugin.display_name} 已绑定", data={
        "id": binding.id, "plugin_id": plugin_id, "template_id": template_id
    })


@router.put("/template/{template_id}/binding/{binding_id}", response_model=BaseResponse)
async def update_template_plugin_binding(
    template_id: int,
    binding_id: int,
    bind_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模板插件绑定配置"""
    result = await db.execute(
        select(TemplatePlugin).where(
            TemplatePlugin.id == binding_id,
            TemplatePlugin.template_id == template_id
        )
    )
    binding = result.scalar_one_or_none()

    if not binding:
        raise HTTPException(status_code=404, detail="绑定记录不存在")

    if "is_enabled" in bind_data:
        binding.is_enabled = bind_data["is_enabled"]
    if "config" in bind_data:
        binding.config = bind_data["config"]
    if "sort_order" in bind_data:
        binding.sort_order = bind_data["sort_order"]

    await db.commit()

    return BaseResponse(success=True, message="绑定配置已更新")


@router.delete("/template/{template_id}/binding/{binding_id}", response_model=BaseResponse)
async def unbind_plugin_from_template(
    template_id: int,
    binding_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解除插件与模板的绑定"""
    result = await db.execute(
        select(TemplatePlugin).where(
            TemplatePlugin.id == binding_id,
            TemplatePlugin.template_id == template_id
        )
    )
    binding = result.scalar_one_or_none()

    if not binding:
        raise HTTPException(status_code=404, detail="绑定记录不存在")

    await db.execute(delete(TemplatePlugin).where(TemplatePlugin.id == binding_id))
    await db.commit()

    return BaseResponse(success=True, message="插件已解除绑定")


# ─────────────────────────────────────────────────────────────────────────────
#  钩子测试
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/test-hook", response_model=BaseResponse)
async def test_hook_code(
    test_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    测试插件钩子代码
    body: {
        code_snippet: str,
        event: str,
        payload: dict
    }
    """
    plugin_name = test_data.get("plugin_name", "test")
    hook_name = test_data.get("event", "") or test_data.get("hook_name", "")
    code = test_data.get("code_snippet", "") or test_data.get("code", "")
    mock_data = test_data.get("payload", {}) or test_data.get("mock_data", {})
    timeout = test_data.get("timeout", 5.0)

    if not hook_name:
        raise HTTPException(status_code=400, detail="event 不能为空")

    result = await test_plugin_hook(plugin_name, hook_name, code, mock_data, timeout)
    return BaseResponse(success=True, data=result)


# ─────────────────────────────────────────────────────────────────────────────
#  统计信息
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats/overview", response_model=BaseResponse)
async def get_plugin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取插件统计概览"""
    total = await db.execute(select(func.count(Plugin.id)))
    total_count = total.scalar() or 0

    enabled = await db.execute(
        select(func.count(Plugin.id)).where(Plugin.is_enabled == True)
    )
    enabled_count = enabled.scalar() or 0

    builtin = await db.execute(
        select(func.count(Plugin.id)).where(Plugin.is_built_in == True)
    )
    builtin_count = builtin.scalar() or 0

    custom = await db.execute(
        select(func.count(Plugin.id)).where(Plugin.category == "custom")
    )
    custom_count = custom.scalar() or 0

    total_bindings = await db.execute(select(func.count(TemplatePlugin.id)))
    bindings_count = total_bindings.scalar() or 0

    # 按分类统计
    cat_result = await db.execute(
        select(Plugin.category, func.count(Plugin.id)).group_by(Plugin.category)
    )
    by_category = [{"category": r[0] or "other", "count": r[1]} for r in cat_result.fetchall()]

    return BaseResponse(success=True, data={
        "total": total_count,
        "enabled": enabled_count,
        "builtin": builtin_count,
        "custom": custom_count,
        "total_bindings": bindings_count,
        "by_category": by_category,
    })
