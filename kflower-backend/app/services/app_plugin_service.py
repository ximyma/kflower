"""
应用插件服务 - 插件与应用绑定管理
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.plugin import Plugin
from app.models.plugin_binding import AppPlugin
from app.core.plugin_manager import get_plugin_manager


class AppPluginService:
    """应用插件服务"""

    @staticmethod
    async def get_app_plugins(app_id: int) -> List[Dict[str, Any]]:
        """获取应用绑定的所有插件"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppPlugin, Plugin)
                .join(Plugin, AppPlugin.plugin_id == Plugin.id)
                .where(AppPlugin.app_id == app_id)
                .order_by(AppPlugin.sort_order)
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
                    "version": plugin.version,
                    "author": plugin.author,
                    "icon": plugin.icon,
                    "category": plugin.category,
                    "is_enabled": binding.is_enabled,
                    "config": binding.config or {},
                    "hook_code": plugin.hook_code or {},
                    "sort_order": binding.sort_order,
                    "created_at": binding.created_at.isoformat() if binding.created_at else None,
                })
            return bindings

    @staticmethod
    async def bind_plugin(
        app_id: int,
        plugin_id: int,
        config: Optional[Dict[str, Any]] = None,
        sort_order: int = 0
    ) -> Dict[str, Any]:
        """将插件绑定到应用"""
        async with AsyncSessionLocal() as session:
            plugin = await session.get(Plugin, plugin_id)
            if not plugin:
                return {"success": False, "message": "插件不存在"}

            result = await session.execute(
                select(AppPlugin).where(
                    and_(
                        AppPlugin.app_id == app_id,
                        AppPlugin.plugin_id == plugin_id
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return {"success": False, "message": "该插件已绑定到此应用"}

            binding = AppPlugin(
                app_id=app_id,
                plugin_id=plugin_id,
                config=config or {},
                is_enabled=True,
                sort_order=sort_order,
            )
            session.add(binding)
            await session.commit()
            await session.refresh(binding)

            return {
                "success": True,
                "message": f"插件 {plugin.display_name} 已绑定",
                "data": {
                    "id": binding.id,
                    "plugin_id": plugin_id,
                    "app_id": app_id,
                }
            }

    @staticmethod
    async def unbind_plugin(app_id: int, binding_id: int) -> Dict[str, Any]:
        """解除插件与应用的绑定"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppPlugin).where(
                    and_(
                        AppPlugin.id == binding_id,
                        AppPlugin.app_id == app_id
                    )
                )
            )
            binding = result.scalar_one_or_none()
            if not binding:
                return {"success": False, "message": "绑定记录不存在"}

            await session.delete(binding)
            await session.commit()

            return {"success": True, "message": "插件已解除绑定"}

    @staticmethod
    async def update_binding(
        app_id: int,
        binding_id: int,
        is_enabled: Optional[bool] = None,
        config: Optional[Dict[str, Any]] = None,
        sort_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """更新应用插件绑定配置"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppPlugin).where(
                    and_(
                        AppPlugin.id == binding_id,
                        AppPlugin.app_id == app_id
                    )
                )
            )
            binding = result.scalar_one_or_none()
            if not binding:
                return {"success": False, "message": "绑定记录不存在"}

            if is_enabled is not None:
                binding.is_enabled = is_enabled
            if config is not None:
                binding.config = config
            if sort_order is not None:
                binding.sort_order = sort_order

            await session.commit()

            return {"success": True, "message": "绑定配置已更新"}

    @staticmethod
    async def trigger_hook(
        app_id: int,
        hook_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """触发应用绑定的所有插件钩子"""
        pm = get_plugin_manager()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppPlugin, Plugin)
                .join(Plugin, AppPlugin.plugin_id == Plugin.id)
                .where(
                    and_(
                        AppPlugin.app_id == app_id,
                        AppPlugin.is_enabled == True
                    )
                )
                .order_by(AppPlugin.sort_order)
            )
            rows = result.all()

            results = []
            for binding, plugin in rows:
                hook_code = plugin.hook_code or {}
                if hook_name not in hook_code or not hook_code[hook_name]:
                    continue

                instance = pm.get_plugin(plugin.name)
                if not instance:
                    continue

                plugin_cfg = plugin.config or {}
                binding_cfg = binding.config or {}
                merged_config = dict(plugin_cfg)
                merged_config.update(binding_cfg)
                hook_context = dict(context)
                hook_context["plugin_config"] = merged_config

                try:
                    output = await instance.execute_hook(hook_name, hook_context)
                    results.append({
                        "plugin_name": plugin.name,
                        "plugin_display": plugin.display_name,
                        "success": True,
                        "output": output
                    })
                except Exception as e:
                    results.append({
                        "plugin_name": plugin.name,
                        "plugin_display": plugin.display_name,
                        "success": False,
                        "error": str(e)
                    })

            return {"hook_name": hook_name, "app_id": app_id, "results": results}

    @staticmethod
    async def get_available_plugins(
        app_id: int,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取可绑定到应用的插件列表（排除已绑定的）"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppPlugin.plugin_id).where(
                    AppPlugin.app_id == app_id
                )
            )
            bound_plugin_ids = [row[0] for row in result.fetchall()]

            query = select(Plugin).where(
                and_(
                    Plugin.is_enabled == True,
                    Plugin.is_installed == True
                )
            )
            if bound_plugin_ids:
                query = query.where(Plugin.id.not_in(bound_plugin_ids))
            if category:
                query = query.where(Plugin.category == category)
            if search:
                query = query.where(
                    or_(
                        Plugin.name.ilike(f"%{search}%"),
                        Plugin.display_name.ilike(f"%{search}%"),
                        Plugin.description.ilike(f"%{search}%")
                    )
                )

            result = await session.execute(query.order_by(Plugin.id))
            plugins = result.scalars().all()

            return [p.to_dict() for p in plugins]

    @staticmethod
    async def get_app_bound_plugin_ids(app_id: int) -> List[int]:
        """获取应用绑定的所有插件ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AppPlugin.plugin_id).where(
                    and_(
                        AppPlugin.app_id == app_id,
                        AppPlugin.is_enabled == True
                    )
                )
            )
            return [row[0] for row in result.fetchall()]
