"""
智能体引擎 - 工具注册表
管理所有可用的智能体工具
"""
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class ToolType(Enum):
    """工具类型"""
    TEMPLATE = "template"
    WORKFLOW = "workflow"
    QUERY = "query"
    ANALYTICS = "analytics"
    FILE = "file"
    NOTIFICATION = "notification"
    CUSTOM = "custom"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    tool_type: ToolType
    parameters: List[Dict[str, Any]]  # [{"name": "", "type": "", "required": true}]
    handler: Callable = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": self.parameters
        }


class ToolRegistry:
    """
    工具注册表
    统一管理所有智能体可用的工具
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 模板相关工具
        self.register(Tool(
            name="create_template",
            description="创建新的业务模板",
            tool_type=ToolType.TEMPLATE,
            parameters=[
                {"name": "name", "type": "string", "required": True},
                {"name": "description", "type": "string", "required": True},
                {"name": "modules", "type": "array", "required": True}
            ]
        ))
        
        self.register(Tool(
            name="list_templates",
            description="列出所有模板",
            tool_type=ToolType.TEMPLATE,
            parameters=[
                {"name": "category", "type": "string", "required": False}
            ]
        ))
        
        # 工作流相关工具
        self.register(Tool(
            name="create_workflow",
            description="创建工作流程",
            tool_type=ToolType.WORKFLOW,
            parameters=[
                {"name": "name", "type": "string", "required": True},
                {"name": "steps", "type": "array", "required": True}
            ]
        ))
        
        self.register(Tool(
            name="execute_workflow",
            description="执行工作流程",
            tool_type=ToolType.WORKFLOW,
            parameters=[
                {"name": "workflow_id", "type": "string", "required": True},
                {"name": "data", "type": "object", "required": True}
            ]
        ))
        
        # 查询相关工具
        self.register(Tool(
            name="query_data",
            description="查询业务数据",
            tool_type=ToolType.QUERY,
            parameters=[
                {"name": "table", "type": "string", "required": True},
                {"name": "conditions", "type": "object", "required": False}
            ]
        ))
        
        self.register(Tool(
            name="get_statistics",
            description="获取统计数据",
            tool_type=ToolType.ANALYTICS,
            parameters=[
                {"name": "metric", "type": "string", "required": True},
                {"name": "time_range", "type": "string", "required": False}
            ]
        ))
        
        # 文件工具
        self.register(Tool(
            name="upload_file",
            description="上传文件",
            tool_type=ToolType.FILE,
            parameters=[
                {"name": "file", "type": "file", "required": True},
                {"name": "folder", "type": "string", "required": False}
            ]
        ))
        
        self.register(Tool(
            name="download_file",
            description="下载文件",
            tool_type=ToolType.FILE,
            parameters=[
                {"name": "file_id", "type": "string", "required": True}
            ]
        ))
        
        # 通知工具
        self.register(Tool(
            name="send_notification",
            description="发送通知",
            tool_type=ToolType.NOTIFICATION,
            parameters=[
                {"name": "user_id", "type": "string", "required": True},
                {"name": "message", "type": "string", "required": True},
                {"name": "channel", "type": "string", "required": False}
            ]
        ))
    
    def register(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool
    
    def unregister(self, tool_name: str) -> bool:
        """注销工具"""
        return self.tools.pop(tool_name, None) is not None
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(tool_name)
    
    def list_tools(self, tool_type: Optional[ToolType] = None) -> List[Dict[str, Any]]:
        """列出工具"""
        tools = list(self.tools.values())
        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]
        return [t.to_dict() for t in tools]
    
    def get_tools_as_openai_format(self) -> List[Dict[str, Any]]:
        """获取OpenAI格式的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            p["name"]: {"type": p["type"]}
                            for p in tool.parameters
                        },
                        "required": [
                            p["name"] for p in tool.parameters
                            if p.get("required", False)
                        ]
                    }
                }
            }
            for tool in self.tools.values()
        ]


# 全局工具注册表实例
tool_registry = ToolRegistry()
