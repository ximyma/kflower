"""
智能体引擎 - 工具注册表
管理所有可用的智能体工具

v2: 与插件系统集成
- AI 工具的启用/禁用状态由 Plugin(category='ai_tool') 控制
- 调用 sync_from_plugin_system() 同步最新状态
"""
from typing import Dict, Any, Callable, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """工具类型"""
    TEMPLATE = "template"
    WORKFLOW = "workflow"
    QUERY = "query"
    ANALYTICS = "analytics"
    FILE = "file"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    tool_type: ToolType
    parameters: List[Dict[str, Any]]  # [{"name": "", "type": "", "required": true}]
    handler: Callable = field(default=None)
    # 插件系统扩展字段
    plugin_name: str = field(default="")      # 对应 Plugin.name
    is_enabled: bool = field(default=True)    # 受插件启用/禁用状态控制

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": self.parameters,
            "plugin_name": self.plugin_name,
            "is_enabled": self.is_enabled,
        }


# ─────────────────────────────────────────────────────────────────────────────
#  默认工具定义（硬编码元信息，插件系统只控制 is_enabled 状态）
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_TOOL_DEFS: List[Dict[str, Any]] = [
    # 模板相关
    {
        "name": "create_template",
        "description": "创建新的业务模板",
        "tool_type": ToolType.TEMPLATE,
        "plugin_name": "tool-create-template",
        "parameters": [
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "modules", "type": "array", "required": True},
        ]
    },
    {
        "name": "list_templates",
        "description": "列出所有模板",
        "tool_type": ToolType.TEMPLATE,
        "plugin_name": "tool-list-templates",
        "parameters": [
            {"name": "category", "type": "string", "required": False},
        ]
    },
    # 工作流
    {
        "name": "create_workflow",
        "description": "创建工作流程",
        "tool_type": ToolType.WORKFLOW,
        "plugin_name": "tool-create-workflow",
        "parameters": [
            {"name": "name", "type": "string", "required": True},
            {"name": "steps", "type": "array", "required": True},
        ]
    },
    {
        "name": "execute_workflow",
        "description": "执行工作流程",
        "tool_type": ToolType.WORKFLOW,
        "plugin_name": "tool-execute-workflow",
        "parameters": [
            {"name": "workflow_id", "type": "string", "required": True},
            {"name": "data", "type": "object", "required": True},
        ]
    },
    # 查询与分析
    {
        "name": "query_data",
        "description": "查询业务数据",
        "tool_type": ToolType.QUERY,
        "plugin_name": "tool-query-data",
        "parameters": [
            {"name": "table", "type": "string", "required": True},
            {"name": "conditions", "type": "object", "required": False},
        ]
    },
    {
        "name": "get_statistics",
        "description": "获取统计数据",
        "tool_type": ToolType.ANALYTICS,
        "plugin_name": "tool-get-statistics",
        "parameters": [
            {"name": "metric", "type": "string", "required": True},
            {"name": "time_range", "type": "string", "required": False},
        ]
    },
    # 通知
    {
        "name": "send_notification",
        "description": "发送通知",
        "tool_type": ToolType.NOTIFICATION,
        "plugin_name": "tool-send-notification",
        "parameters": [
            {"name": "user_id", "type": "string", "required": True},
            {"name": "message", "type": "string", "required": True},
            {"name": "channel", "type": "string", "required": False},
        ]
    },
    # 文件工具
    {
        "name": "convert_document",
        "description": "文档格式转换：doc→docx、xls→xlsx、ppt→pptx、任意→pdf",
        "tool_type": ToolType.FILE,
        "plugin_name": "tool-convert-document",
        "parameters": [
            {"name": "input_path", "type": "string", "required": True},
            {"name": "target_format", "type": "string", "required": True},
            {"name": "output_dir", "type": "string", "required": False},
        ]
    },
    {
        "name": "extract_excel_json",
        "description": "将 Excel/CSV 文件提取为 JSON 数据，用于模板导入和数据分析",
        "tool_type": ToolType.FILE,
        "plugin_name": "tool-extract-excel-json",
        "parameters": [
            {"name": "input_path", "type": "string", "required": True},
            {"name": "sheet_name", "type": "string", "required": False},
            {"name": "header_row", "type": "integer", "required": False},
            {"name": "max_rows", "type": "integer", "required": False},
        ]
    },
    {
        "name": "auto_convert_upload",
        "description": "自动将旧格式文档（doc/xls/ppt）转换为新格式（docx/xlsx/pptx），供上传使用",
        "tool_type": ToolType.FILE,
        "plugin_name": "tool-auto-convert-upload",
        "parameters": [
            {"name": "input_path", "type": "string", "required": True},
            {"name": "output_dir", "type": "string", "required": False},
        ]
    },
    # ===== 系统工具（参考 SoWork2） =====
    {
        "name": "read_file",
        "description": "读取文件内容。支持指定起始行和行数限制",
        "tool_type": ToolType.SYSTEM,
        "parameters": [
            {"name": "path", "type": "string", "required": True, "description": "文件路径"},
            {"name": "offset", "type": "integer", "required": False, "description": "起始行号"},
            {"name": "limit", "type": "integer", "required": False, "description": "最大读取行数"},
        ]
    },
    {
        "name": "write_file",
        "description": "写入文件内容。会覆盖已有文件",
        "tool_type": ToolType.SYSTEM,
        "parameters": [
            {"name": "path", "type": "string", "required": True, "description": "文件路径"},
            {"name": "content", "type": "string", "required": True, "description": "要写入的内容"},
        ]
    },
    {
        "name": "list_files",
        "description": "列出目录中的文件和子目录",
        "tool_type": ToolType.SYSTEM,
        "parameters": [
            {"name": "path", "type": "string", "required": True, "description": "目录路径"},
            {"name": "pattern", "type": "string", "required": False, "description": "文件通配模式，如 *.py"},
        ]
    },
    {
        "name": "search_content",
        "description": "在文件中搜索匹配的文本内容（grep）",
        "tool_type": ToolType.SYSTEM,
        "parameters": [
            {"name": "pattern", "type": "string", "required": True, "description": "搜索的正则表达式"},
            {"name": "path", "type": "string", "required": True, "description": "搜索路径（文件或目录）"},
        ]
    },
    {
        "name": "bash",
        "description": "执行 Shell 命令（仅限安全命令）",
        "tool_type": ToolType.SYSTEM,
        "parameters": [
            {"name": "command", "type": "string", "required": True, "description": "要执行的命令"},
            {"name": "timeout", "type": "integer", "required": False, "description": "超时秒数，默认30"},
        ]
    },
    {
        "name": "get_env_info",
        "description": "获取系统环境信息，包括项目路径、Python版本、数据库状态等",
        "tool_type": ToolType.SYSTEM,
        "parameters": []
    },
    {
        "name": "read_workflow_logs",
        "description": "读取工作流实例的审批日志",
        "tool_type": ToolType.WORKFLOW,
        "parameters": [
            {"name": "instance_id", "type": "integer", "required": True, "description": "工作流实例ID"},
        ]
    },
]


class ToolRegistry:
    """
    工具注册表
    统一管理所有智能体可用的工具

    v2 新增：与插件系统集成
    - 调用 sync_from_plugin_system() 将插件的 is_enabled 状态同步到对应工具
    - get_tools_as_openai_format() 只返回 is_enabled=True 的工具
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        for td in _DEFAULT_TOOL_DEFS:
            self.register(Tool(
                name=td["name"],
                description=td["description"],
                tool_type=td["tool_type"],
                parameters=td["parameters"],
                plugin_name=td.get("plugin_name", ""),
                is_enabled=True,
            ))

    # ─────────────────────────────────────────────────────────────────────────
    #  插件系统集成
    # ─────────────────────────────────────────────────────────────────────────

    def sync_from_plugin_system(self) -> int:
        """
        从插件系统同步 AI 工具的启用状态。
        返回成功同步的工具数量。

        在以下时机调用：
        1. main.py 启动后（PluginManager.initialize() 之后）
        2. 插件启用/禁用 API 调用后
        """
        try:
            from app.core.plugin_manager import _get_sync_session
            from app.models.plugin import Plugin

            db = _get_sync_session()
            try:
                plugins = db.query(Plugin).filter(
                    Plugin.category == "ai_tool"
                ).all()

                # 建立 plugin_name → is_enabled 映射
                enabled_map: Dict[str, bool] = {p.name: p.is_enabled for p in plugins}

                synced = 0
                for tool_name, tool in self.tools.items():
                    if tool.plugin_name and tool.plugin_name in enabled_map:
                        tool.is_enabled = enabled_map[tool.plugin_name]
                        synced += 1

                logger.info(f"[ToolRegistry] 同步 AI 工具插件状态完成，共 {synced} 个工具")
                return synced
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"[ToolRegistry] 同步插件状态失败（使用默认值）: {e}")
            return 0

    def set_tool_enabled(self, tool_name: str, is_enabled: bool) -> bool:
        """直接设置工具启用状态（供插件系统回调调用）"""
        tool = self.tools.get(tool_name)
        if tool:
            tool.is_enabled = is_enabled
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    #  基础操作
    # ─────────────────────────────────────────────────────────────────────────

    def register(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool

    def unregister(self, tool_name: str) -> bool:
        """注销工具"""
        return self.tools.pop(tool_name, None) is not None

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取工具（不管是否启用，供执行器内部使用）"""
        return self.tools.get(tool_name)

    def list_tools(
        self,
        tool_type: Optional[ToolType] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """列出工具"""
        tools = list(self.tools.values())
        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]
        if enabled_only:
            tools = [t for t in tools if t.is_enabled]
        return [t.to_dict() for t in tools]

    def get_tools_as_openai_format(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """获取 OpenAI function calling 格式的工具定义，默认只返回已启用工具"""
        result = []
        for tool in self.tools.values():
            if enabled_only and not tool.is_enabled:
                continue
            properties = {}
            required = []
            for p in tool.parameters:
                prop = {"type": p["type"]}
                if "description" in p:
                    prop["description"] = p["description"]
                if "enum" in p:
                    prop["enum"] = p["enum"]
                properties[p["name"]] = prop
                if p.get("required", False):
                    required.append(p["name"])
            
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        return result


# 全局工具注册表实例
tool_registry = ToolRegistry()
