"""
插件钩子调度器
在业务事件触发时，查找并执行绑定的插件钩子

整合优化 2.2：创建插件钩子统一调度器
表单提交/删除/列表加载时，自动触发绑定到该应用的插件对应钩子。
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HookEvent:
    """钩子事件定义"""
    # 事件名称（与 AppMenu.trigger_event 匹配）
    FORM_SUBMIT = "form.submit"           # 表单提交后
    FORM_SUBMIT_BEFORE = "form.submit.before"  # 表单提交前
    FORM_UPDATE = "form.update"          # 表单更新后
    FORM_DELETE = "form.delete"          # 表单删除后
    FORM_LOAD = "form.load"              # 表单加载时
    LIST_LOAD = "list.load"             # 列表加载时
    WORKFLOW_START = "workflow.start"    # 工作流启动前
    WORKFLOW_END = "workflow.end"        # 工作流结束后
    MANUAL_TRIGGER = "manual"            # 手动触发


class PluginDispatcher:
    """
    插件事件调度器

    使用方式：
        from app.core.plugin_dispatcher import plugin_dispatcher

        # 在表单提交后触发
        result = await plugin_dispatcher.dispatch(
            event="form.submit",
            app_id=app_id,
            template_id=template_id,
            payload={"data": form_data, "user_id": user_id},
            db=db
        )
    """

    def __init__(self):
        self._hook_cache: Dict[str, List[Dict]] = {}  # 缓存：app_id -> 插件列表

    async def dispatch(
        self,
        event: str,
        app_id: int,
        template_id: Optional[int] = None,
        payload: Dict[str, Any] = None,
        db=None
    ) -> Dict[str, Any]:
        """
        触发指定事件，执行所有匹配的插件钩子

        Args:
            event: 事件名，如 "form.submit"
            app_id: 应用ID
            template_id: 模板ID（可选）
            payload: 事件数据
            db: 数据库会话

        Returns:
            经过插件处理后的 payload（插件可修改数据）
        """
        from app.services.app_plugin_service import AppPluginService

        payload = payload or {}

        # 获取该应用绑定的插件及其钩子
        try:
            bindings = await self._get_app_plugin_bindings(app_id, db)
        except Exception as e:
            logger.warning(f"获取应用插件绑定失败: {e}")
            bindings = []

        # 筛选匹配事件的插件
        matched_plugins = []
        for binding in bindings:
            trigger_events = binding.get("trigger_event", "")
            # 支持多个事件用逗号分隔
            if event in trigger_events.split(","):
                matched_plugins.append(binding)

        if not matched_plugins:
            logger.debug(f"应用 {app_id} 没有绑定事件 {event} 的插件")
            return payload

        # 按 sort_order 排序
        matched_plugins.sort(key=lambda x: x.get("sort_order", 0))

        # 执行每个插件钩子
        result = payload.copy()
        for plugin in matched_plugins:
            if not plugin.get("is_enabled", True):
                continue

            try:
                modified = await self._execute_hook(plugin, result, db)
                if modified is not None:
                    result = modified
            except Exception as e:
                logger.error(f"插件钩子执行错误 [{plugin.get('name')} / {event}]: {e}")
                # 继续执行其他插件，不中断流程

        return result

    async def _get_app_plugin_bindings(
        self,
        app_id: int,
        db
    ) -> List[Dict]:
        """获取应用绑定的插件列表"""
        from app.services.app_plugin_service import AppPluginService

        # 先检查缓存（1分钟内有效）
        cache_key = f"app_{app_id}_plugins"
        if cache_key in self._hook_cache:
            cached_time, cached_data = self._hook_cache[cache_key]
            import time
            if time.time() - cached_time < 60:  # 1分钟缓存
                return cached_data

        # 从数据库获取
        try:
            bindings = AppPluginService.get_bindings_for_event(app_id, None, db)
            import time
            self._hook_cache[cache_key] = (time.time(), bindings)
            return bindings
        except Exception as e:
            logger.warning(f"获取插件绑定失败: {e}")
            return []

    async def _execute_hook(
        self,
        plugin: Dict[str, Any],
        payload: Dict[str, Any],
        db
    ) -> Optional[Dict[str, Any]]:
        """执行单个插件钩子（沙箱执行）"""
        from app.modules.my_apps.plugin_executor import plugin_executor, PluginContext

        script_code = plugin.get("script_code") or plugin.get("hook_code", "")
        if not script_code:
            return None

        plugin_config = plugin.get("config", {}) or plugin.get("plugin_config", {})

        try:
            context = PluginContext(
                data=payload,
                old_data=payload.get("_old_data"),
                db=db,
                user_id=payload.get("user_id", 0),
                template_id=payload.get("template_id", 0),
                event=plugin.get("trigger_event", ""),
                app_id=payload.get("app_id", 0)
            )

            # 执行插件脚本
            success, result = await plugin_executor.execute(script_code, context)

            if success and isinstance(result, dict):
                return result

            return None

        except Exception as e:
            logger.error(f"插件执行失败: {plugin.get('name')} - {e}")
            return None

    def clear_cache(self):
        """清除插件缓存"""
        self._hook_cache.clear()


# 全局插件调度器实例
plugin_dispatcher = PluginDispatcher()


# 便捷函数：在表单提交时调用
async def dispatch_form_submit(
    app_id: int,
    template_id: int,
    form_data: Dict[str, Any],
    user_id: int,
    db,
    is_update: bool = False
) -> Dict[str, Any]:
    """
    表单提交/更新时触发插件钩子

    Args:
        app_id: 应用ID
        template_id: 模板ID
        form_data: 表单数据
        user_id: 当前用户ID
        db: 数据库会话
        is_update: 是否为更新操作

    Returns:
        处理后的表单数据
    """
    event = HookEvent.FORM_UPDATE if is_update else HookEvent.FORM_SUBMIT
    return await plugin_dispatcher.dispatch(
        event=event,
        app_id=app_id,
        template_id=template_id,
        payload={
            "data": form_data,
            "user_id": user_id,
            "template_id": template_id,
            "app_id": app_id,
            "_is_update": is_update,
        },
        db=db
    )


# 便捷函数：在工作流启动时调用
async def dispatch_workflow_start(
    app_id: int,
    workflow_id: int,
    form_data_id: int,
    variables: Dict[str, Any],
    user_id: int,
    db
) -> Dict[str, Any]:
    """
    工作流启动前触发插件钩子

    Args:
        app_id: 应用ID
        workflow_id: 工作流ID
        form_data_id: 表单数据ID
        variables: 工作流变量
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        处理后的变量
    """
    return await plugin_dispatcher.dispatch(
        event=HookEvent.WORKFLOW_START,
        app_id=app_id,
        payload={
            "workflow_id": workflow_id,
            "form_data_id": form_data_id,
            "variables": variables,
            "user_id": user_id,
            "app_id": app_id,
        },
        db=db
    )
