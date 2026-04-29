"""
插件管理器 - 插件生命周期管理（加载/启用/禁用/卸载）
"""
import json
import logging
from typing import Any, Dict, List, Optional, Callable
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  内置插件元信息
# ─────────────────────────────────────────────────────────────────────────────
BUILTIN_PLUGINS = [
    {
        "name": "kflower-calc",
        "display_name": "计算字段",
        "description": "在表单中添加计算类型字段，支持 SUM、IF、VLOOKUP 等公式",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "calculator",
        "category": "builtin",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "supported_formulas": ["SUM", "IF", "VLOOKUP", "CONCAT", "ROUND"],
            "max_formula_depth": 5,
        },
        "hook_code": {
            "before_form_render": "# 计算字段插件\n# context = {fields, data, template_id}\n# 可在此处注入计算结果到字段\nreturn context",
        }
    },
    {
        "name": "kflower-notify",
        "display_name": "通知提醒",
        "description": "支持企业微信、邮件、站内信通知，可绑定表单事件触发",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "bell",
        "category": "builtin",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "channels": ["wecom", "email", "inbox"],
            "default_channel": "wecom",
        },
        "hook_code": {
            "after_form_submit": "# 通知插件\n# context = {data, template_id, user_id, config}\n# 发送通知\nreturn context",
        }
    },
    {
        "name": "kflower-workflow",
        "display_name": "审批流程",
        "description": "为表单添加审批流程，支持多级审批、条件分支、自动通过",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "set-up",
        "category": "builtin",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "max_approvers": 5,
            "timeout_hours": 72,
        },
        "hook_code": {
            "after_form_submit": "# 审批流程插件\n# context = {data, template_id, user_id}\n# 发起审批流程\nreturn context",
        }
    },
    {
        "name": "kflower-report",
        "display_name": "数据报表",
        "description": "生成图表报表，支持折线图、柱状图、饼图、数据导出",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "data-analysis",
        "category": "builtin",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {},
        "hook_code": {}
    },
    {
        "name": "kflower-ai",
        "display_name": "AI 助手",
        "description": "接入大语言模型，支持智能填表、内容生成、数据分析",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "magic-stick",
        "category": "builtin",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "model": "qwen-turbo",
            "max_tokens": 2000,
        },
        "hook_code": {
            "on_list_load": "# AI 助手插件\n# context = {filters, data, template_id}\n# 可添加 AI 分析结果\nreturn context",
        }
    },
    # ─── AI 工具集插件 (category=ai_tool) ───────────────────────────────────────
    {
        "name": "tool-create-template",
        "display_name": "创建模板工具",
        "description": "AI 工具：为智能体提供「创建业务模板」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "document-add",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "create_template",
            "tool_type": "template",
            "parameters": [
                {"name": "name", "type": "string", "required": True},
                {"name": "description", "type": "string", "required": True},
                {"name": "modules", "type": "array", "required": True},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-list-templates",
        "display_name": "查询模板工具",
        "description": "AI 工具：为智能体提供「列出所有模板」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "document",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "list_templates",
            "tool_type": "template",
            "parameters": [
                {"name": "category", "type": "string", "required": False},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-create-workflow",
        "display_name": "创建工作流工具",
        "description": "AI 工具：为智能体提供「创建工作流程」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "connection",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "create_workflow",
            "tool_type": "workflow",
            "parameters": [
                {"name": "name", "type": "string", "required": True},
                {"name": "steps", "type": "array", "required": True},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-execute-workflow",
        "display_name": "执行工作流工具",
        "description": "AI 工具：为智能体提供「执行工作流程」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "video-play",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "execute_workflow",
            "tool_type": "workflow",
            "parameters": [
                {"name": "workflow_id", "type": "string", "required": True},
                {"name": "data", "type": "object", "required": True},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-query-data",
        "display_name": "查询数据工具",
        "description": "AI 工具：为智能体提供「查询业务数据」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "search",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "query_data",
            "tool_type": "query",
            "parameters": [
                {"name": "table", "type": "string", "required": True},
                {"name": "conditions", "type": "object", "required": False},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-get-statistics",
        "display_name": "统计分析工具",
        "description": "AI 工具：为智能体提供「获取统计数据」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "data-analysis",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "get_statistics",
            "tool_type": "analytics",
            "parameters": [
                {"name": "metric", "type": "string", "required": True},
                {"name": "time_range", "type": "string", "required": False},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-send-notification",
        "display_name": "发送通知工具",
        "description": "AI 工具：为智能体提供「发送系统通知」能力",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "bell",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "send_notification",
            "tool_type": "notification",
            "parameters": [
                {"name": "user_id", "type": "string", "required": True},
                {"name": "message", "type": "string", "required": True},
                {"name": "channel", "type": "string", "required": False},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-convert-document",
        "display_name": "文档转换工具",
        "description": "AI 工具：文档格式转换（doc→docx、xls→xlsx、任意→pdf）",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "copy-document",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "convert_document",
            "tool_type": "file",
            "parameters": [
                {"name": "input_path", "type": "string", "required": True},
                {"name": "target_format", "type": "string", "required": True},
                {"name": "output_dir", "type": "string", "required": False},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-extract-excel-json",
        "display_name": "Excel提取工具",
        "description": "AI 工具：将 Excel/CSV 提取为 JSON 数据，用于模板导入和数据分析",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "grid",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "extract_excel_json",
            "tool_type": "file",
            "parameters": [
                {"name": "input_path", "type": "string", "required": True},
                {"name": "sheet_name", "type": "string", "required": False},
                {"name": "header_row", "type": "integer", "required": False},
                {"name": "max_rows", "type": "integer", "required": False},
            ]
        },
        "hook_code": {}
    },
    {
        "name": "tool-auto-convert-upload",
        "display_name": "自动转换上传工具",
        "description": "AI 工具：自动将旧格式文档（doc/xls/ppt）转换为新格式后上传",
        "version": "1.0.0",
        "author": "KFlower",
        "icon": "upload",
        "category": "ai_tool",
        "install_type": "builtin",
        "is_built_in": True,
        "config": {
            "tool_name": "auto_convert_upload",
            "tool_type": "file",
            "parameters": [
                {"name": "input_path", "type": "string", "required": True},
                {"name": "output_dir", "type": "string", "required": False},
            ]
        },
        "hook_code": {}
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  数据库操作工具（避免同步 Session 持有事务导致 aiosqlite 死锁）
#  engine_sync 使用 isolation_level="AUTOCOMMIT"，每个连接操作立即释放
# ─────────────────────────────────────────────────────────────────────────────
def _get_sync_session():
    """获取新的同步 Session（每次调用创建新实例，用完即关）"""
    from app.core.database import engine_sync
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine_sync, expire_on_commit=False)
    return Session()


def _db_exec(fn):
    """执行数据库操作的包装器：创建session、调用fn、确保关闭"""
    db = _get_sync_session()
    try:
        result = fn(db)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
#  PluginManager
# ─────────────────────────────────────────────────────────────────────────────
class PluginManager:
    """
    全局插件管理器（无状态，通过_db_exec每次创建新session）
    """

    def __init__(self):
        self._loaded_plugins: Dict[str, "PluginInstance"] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    # ─────────────────────────────────────────────────────────────────────────
    #  初始化与加载
    # ─────────────────────────────────────────────────────────────────────────

    def initialize(self):
        """初始化插件系统：注册内置插件 + 加载用户插件"""
        try:
            logger.info("[PluginManager] 开始初始化...")
            self._register_builtin_plugins()
            logger.info("[PluginManager] 内置插件注册完成")
            self._load_enabled_plugins()
            logger.info(f"[PluginManager] 插件加载完成，已加载 {len(self._loaded_plugins)} 个")
        except Exception as e:
            logger.error(f"[PluginManager] 初始化失败: {e}", exc_info=True)

    def _register_builtin_plugins(self):
        """注册内置插件到数据库"""
        from app.models.plugin import Plugin, seed_builtin_hooks

        _db_exec(lambda db: seed_builtin_hooks(db))

        def _do_register(db):
            for plugin_def in BUILTIN_PLUGINS:
                existing = db.query(Plugin).filter_by(name=plugin_def["name"]).first()
                if not existing:
                    db.add(Plugin(**plugin_def))
                    logger.info(f"[PluginManager] 注册内置插件: {plugin_def['name']}")

        _db_exec(_do_register)

    def _load_enabled_plugins(self):
        """加载所有已启用且已安装的插件"""
        from app.models.plugin import Plugin

        def _do_load(db):
            plugins = db.query(Plugin).filter(
                Plugin.is_enabled == True,
                Plugin.is_installed == True
            ).all()
            for plugin in plugins:
                self._load_plugin_instance(plugin)

        _db_exec(_do_load)

    def _load_plugin_instance(self, plugin_model):
        """加载单个插件实例"""
        if plugin_model.name in self._loaded_plugins:
            return self._loaded_plugins[plugin_model.name]

        instance = PluginInstance(plugin_model)
        instance.load_hooks()
        self._loaded_plugins[plugin_model.name] = instance

        logger.info(f"[PluginManager] 加载插件: {plugin_model.name} v{plugin_model.version}")
        return instance

    # ─────────────────────────────────────────────────────────────────────────
    #  插件生命周期
    # ─────────────────────────────────────────────────────────────────────────

    def enable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """启用插件"""
        from app.models.plugin import Plugin

        def _do(db):
            plugin = db.query(Plugin).filter_by(name=plugin_name).first()
            if not plugin:
                return {"success": False, "message": f"插件 {plugin_name} 不存在"}
            if plugin.is_built_in:
                return {"success": False, "message": "内置插件不能禁用"}
            plugin.is_enabled = True
            plugin.install_count = (plugin.install_count or 0) + 1
            return plugin

        result = _db_exec(_do)
        if isinstance(result, dict):
            return result
        plugin = result
        # 重新加载实例（插件对象从新session获取，需要重新加载hooks）
        self._load_plugin_instance(plugin)
        return {"success": True, "message": f"插件 {plugin.display_name} 已启用"}

    def disable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """禁用插件"""
        from app.models.plugin import Plugin

        def _do(db):
            plugin = db.query(Plugin).filter_by(name=plugin_name).first()
            if not plugin:
                return {"success": False, "message": f"插件 {plugin_name} 不存在"}
            if plugin.is_built_in:
                return {"success": False, "message": "内置插件不能禁用"}
            plugin.is_enabled = False
            return plugin.display_name

        result = _db_exec(_do)
        if isinstance(result, dict):
            return result
        display_name = result
        if plugin_name in self._loaded_plugins:
            del self._loaded_plugins[plugin_name]
        return {"success": True, "message": f"插件 {display_name} 已禁用"}

    def get_plugin(self, plugin_name: str) -> Optional["PluginInstance"]:
        """获取已加载的插件实例"""
        return self._loaded_plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        from app.models.plugin import Plugin

        def _do(db):
            plugins = db.query(Plugin).order_by(Plugin.id).all()
            return [p.to_dict() for p in plugins]

        return _db_exec(_do)

    def get_plugin_detail(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件详情"""
        from app.models.plugin import Plugin

        def _do(db):
            plugin = db.query(Plugin).filter_by(name=plugin_name).first()
            return plugin.to_dict() if plugin else None

        return _db_exec(_do)

    # ─────────────────────────────────────────────────────────────────────────
    #  钩子触发
    # ─────────────────────────────────────────────────────────────────────────

    async def trigger_hook(
        self,
        hook_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        触发钩子，按顺序执行所有绑定的插件代码
        """
        from app.models.plugin_binding import TemplatePlugin
        from app.models.plugin import Plugin

        template_id = context.get("template_id")
        results = []

        if template_id:
            def _do(db):
                return db.query(TemplatePlugin).filter(
                    TemplatePlugin.template_id == template_id,
                    TemplatePlugin.is_enabled == True
                ).all()

            bindings = _db_exec(_do)
            for binding in bindings:
                plugin_name = binding.plugin.name
                hook_code = binding.plugin.hook_code

                if hook_name not in hook_code or not hook_code[hook_name]:
                    continue

                instance = self._loaded_plugins.get(plugin_name)
                if not instance:
                    continue

                merged_config = {**binding.plugin.config, **binding.config}
                hook_context = {**context, "plugin_config": merged_config}

                try:
                    output = await instance.execute_hook(hook_name, hook_context)
                    results.append({
                        "plugin_name": plugin_name,
                        "plugin_display": binding.plugin.display_name,
                        "success": True,
                        "output": output
                    })
                except Exception as e:
                    results.append({
                        "plugin_name": plugin_name,
                        "plugin_display": binding.plugin.display_name,
                        "success": False,
                        "error": str(e)
                    })
                    logger.error(f"[PluginManager] 钩子 {hook_name} 执行失败 [{plugin_name}]: {e}")
        else:
            for name, instance in self._loaded_plugins.items():
                hook_code = instance.plugin_model.hook_code
                if hook_name not in hook_code or not hook_code[hook_name]:
                    continue
                try:
                    output = await instance.execute_hook(hook_name, context)
                    results.append({
                        "plugin_name": name,
                        "plugin_display": instance.plugin_model.display_name,
                        "success": True,
                        "output": output
                    })
                except Exception as e:
                    results.append({
                        "plugin_name": name,
                        "plugin_display": instance.plugin_model.display_name,
                        "success": False,
                        "error": str(e)
                    })

        return {"hook_name": hook_name, "results": results}

    # ─────────────────────────────────────────────────────────────────────────
    #  辅助方法
    # ─────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """导出管理器状态"""
        return {
            "total_loaded": len(self._loaded_plugins),
            "plugins": [name for name in self._loaded_plugins.keys()],
            "hooks": {name: len(handlers) for name, handlers in self._hooks.items()}
        }


class PluginInstance:
    """
    插件实例 - 代表一个已加载的插件
    """

    def __init__(self, plugin_model):
        self.plugin_model = plugin_model
        self._hooks: Dict[str, str] = {}

    def load_hooks(self):
        """从插件模型加载钩子代码"""
        hook_code = self.plugin_model.hook_code or {}
        if isinstance(hook_code, str):
            try:
                hook_code = json.loads(hook_code)
            except Exception:
                hook_code = {}
        self._hooks = {k: v for k, v in hook_code.items() if v}

    def has_hook(self, hook_name: str) -> bool:
        """检查插件是否有此钩子"""
        return hook_name in self._hooks and self._hooks[hook_name]

    async def execute_hook(
        self,
        hook_name: str,
        context: Dict[str, Any]
    ) -> Any:
        """执行插件钩子代码（沙箱中运行）"""
        from app.core.plugin_sandbox import PluginSandbox

        if hook_name not in self._hooks:
            return None

        code = self._hooks[hook_name]
        sandbox = PluginSandbox(self.plugin_model.name, context)
        return await sandbox.execute(code)


# ─────────────────────────────────────────────────────────────────────────────
#  全局单例（由 main.py 初始化）
# ─────────────────────────────────────────────────────────────────────────────
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
        _plugin_manager.initialize()
    return _plugin_manager
