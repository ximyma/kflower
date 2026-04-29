"""
模板插件服务 - 插件与模板的绑定管理
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine_sync
from app.models.plugin import Plugin
from app.models.plugin_binding import TemplatePlugin
from app.core.plugin_manager import get_plugin_manager


class TemplatePluginService:
    """模板插件服务"""

    HOOK_POINTS = {
        "before_form_render": "表单渲染前",
        "after_form_submit": "表单提交后",
        "before_form_submit": "表单提交前",
        "after_data_delete": "数据删除后",
        "on_list_load": "列表加载时",
        "on_field_change": "字段值变更时",
        "on_cron_schedule": "定时任务",
        "on_api_called": "API调用时",
    }

    @staticmethod
    async def get_template_plugins(template_id: int) -> List[Dict[str, Any]]:
        """获取模板绑定的所有插件"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
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
        template_id: int,
        plugin_id: int,
        config: Optional[Dict[str, Any]] = None,
        sort_order: int = 0
    ) -> Dict[str, Any]:
        """将插件绑定到模板"""
        async with AsyncSessionLocal() as session:
            plugin = await session.get(Plugin, plugin_id)
            if not plugin:
                return {"success": False, "message": "插件不存在"}

            result = await session.execute(
                select(TemplatePlugin).where(
                    and_(
                        TemplatePlugin.template_id == template_id,
                        TemplatePlugin.plugin_id == plugin_id
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return {"success": False, "message": "该插件已绑定到此模板"}

            binding = TemplatePlugin(
                template_id=template_id,
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
                    "template_id": template_id,
                }
            }

    @staticmethod
    async def unbind_plugin(template_id: int, binding_id: int) -> Dict[str, Any]:
        """解除插件与模板的绑定"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TemplatePlugin).where(
                    and_(
                        TemplatePlugin.id == binding_id,
                        TemplatePlugin.template_id == template_id
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
        template_id: int,
        binding_id: int,
        is_enabled: Optional[bool] = None,
        config: Optional[Dict[str, Any]] = None,
        sort_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """更新模板插件绑定配置"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TemplatePlugin).where(
                    and_(
                        TemplatePlugin.id == binding_id,
                        TemplatePlugin.template_id == template_id
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
        template_id: int,
        hook_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """触发模板绑定的所有插件钩子"""
        pm = get_plugin_manager()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TemplatePlugin, Plugin)
                .join(Plugin, TemplatePlugin.plugin_id == Plugin.id)
                .where(
                    and_(
                        TemplatePlugin.template_id == template_id,
                        TemplatePlugin.is_enabled == True
                    )
                )
                .order_by(TemplatePlugin.sort_order)
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

            return {"hook_name": hook_name, "template_id": template_id, "results": results}

    @staticmethod
    async def get_available_plugins(
        template_id: int,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取可绑定到模板的插件列表（排除已绑定的）"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TemplatePlugin.plugin_id).where(
                    TemplatePlugin.template_id == template_id
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
