"""
智能体引擎 - 工具调用执行器
实现工具的实际执行逻辑
"""
from typing import Dict, Any, Optional, List
from app.core.agent_engine.tools.registry import tool_registry, ToolType
from app.core.database import get_db
from sqlalchemy import text
import json
import logging

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    工具执行器
    负责执行智能体调用的工具
    """
    
    def __init__(self):
        self.handlers = {
            "create_template": self._create_template,
            "list_templates": self._list_templates,
            "create_workflow": self._create_workflow,
            "execute_workflow": self._execute_workflow,
            "query_data": self._query_data,
            "get_statistics": self._get_statistics,
            "send_notification": self._send_notification,
            # 文档转换工具
            "convert_document": self._convert_document,
            "extract_excel_json": self._extract_excel_json,
            "auto_convert_upload": self._auto_convert_upload,
        }
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工具调用（整合优化 1.3：确保错误正确上抛）

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            context: 执行上下文（用户ID、租户ID等）

        Returns:
            执行结果
        """
        # 检查工具是否存在
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"工具 '{tool_name}' 不存在"}

        # 检查工具是否启用
        if not tool.is_enabled:
            return {"success": False, "error": f"工具 '{tool_name}' 已被禁用"}

        # 获取执行器
        handler = self.handlers.get(tool_name)
        if not handler:
            return {"success": False, "error": f"工具 '{tool_name}' 暂无执行器"}

        # 执行工具
        try:
            result = await handler(arguments, context or {})
            # 统一返回格式：确保 result 包含 success 字段
            if isinstance(result, dict) and "error" in result:
                return {"success": False, "tool": tool_name, "error": result["error"]}
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"工具执行错误: {tool_name} - {e}", exc_info=True)
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    async def _create_template(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建模板"""
        from app.models.workflow import Template
        
        async with get_db() as db:
            template = Template(
                name=args.get("name"),
                description=args.get("description", ""),
                category=args.get("category", "general"),
                config=json.dumps(args.get("modules", [])),
                created_by=context.get("user_id")
            )
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            return {
                "template_id": template.id,
                "name": template.name,
                "message": f"模板 '{template.name}' 创建成功"
            }
    
    async def _list_templates(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """列出模板"""
        from app.models.workflow import Template
        
        async with get_db() as db:
            query = "SELECT id, name, description, category FROM templates WHERE is_active = 1"
            params = {}
            
            if args.get("category"):
                query += " AND category = :category"
                params["category"] = args["category"]
            
            result = await db.execute(text(query), params)
            templates = [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": row[3]
                }
                for row in result.fetchall()
            ]
            
            return {
                "templates": templates,
                "count": len(templates)
            }
    
    async def _create_workflow(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建工作流"""
        from app.models.workflow import Workflow
        
        async with get_db() as db:
            workflow = Workflow(
                name=args.get("name"),
                description=args.get("description", ""),
                definition=json.dumps(args.get("steps", [])),
                created_by=context.get("user_id")
            )
            db.add(workflow)
            await db.commit()
            await db.refresh(workflow)
            
            return {
                "workflow_id": workflow.id,
                "name": workflow.name,
                "message": f"工作流 '{workflow.name}' 创建成功"
            }
    
    async def _execute_workflow(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行工作流"""
        from app.core.workflow_executor import workflow_executor
        
        workflow_id = args.get("workflow_id")
        data = args.get("data", {})
        
        result = await workflow_executor.execute(
            workflow_id=workflow_id,
            input_data=data,
            user_id=context.get("user_id")
        )
        
        return result
    
    async def _query_data(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """查询数据"""
        table = args.get("table")
        conditions = args.get("conditions", {})
        
        async with get_db() as db:
            # 构建查询
            query = f"SELECT * FROM {table} WHERE 1=1"
            params = {}
            
            for key, value in conditions.items():
                query += f" AND {key} = :{key}"
                params[key] = value
            
            query += " LIMIT 100"
            
            result = await db.execute(text(query), params)
            columns = result.keys()
            rows = result.fetchall()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "data": data,
                "count": len(data),
                "table": table
            }
    
    async def _get_statistics(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取统计数据"""
        metric = args.get("metric")
        time_range = args.get("time_range", "today")
        
        async with get_db() as db:
            # 根据指标类型获取统计数据
            if metric == "workflow_count":
                result = await db.execute(
                    text("SELECT COUNT(*) FROM workflow_instances WHERE created_at >= date('now', '-1 day')")
                )
                count = result.scalar()
                return {"metric": metric, "value": count, "time_range": time_range}
            
            elif metric == "user_activity":
                result = await db.execute(
                    text("SELECT COUNT(DISTINCT created_by) FROM workflow_instances WHERE created_at >= date('now', '-7 day')")
                )
                count = result.scalar()
                return {"metric": metric, "value": count, "time_range": "7 days"}
            
            elif metric == "pending_tasks":
                result = await db.execute(
                    text("SELECT COUNT(*) FROM workflow_instances WHERE status = 'running'")
                )
                count = result.scalar()
                return {"metric": metric, "value": count}
            
            else:
                return {"error": f"Unknown metric: {metric}"}
    
    async def _send_notification(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送通知"""
        user_id = args.get("user_id")
        message = args.get("message")
        channel = args.get("channel", "system")
        
        # TODO: 实现实际的通知发送逻辑
        # 这里可以集成邮件、短信、企业微信等渠道
        
        logger.info(f"Notification sent to {user_id} via {channel}: {message}")
        
        return {
            "success": True,
            "user_id": user_id,
            "channel": channel,
            "message": "通知已发送"
        }

    async def _convert_document(
        self,
        args: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """文档格式转换"""
        from app.core.doc_converter import convert_document
        input_path = args.get("input_path", "")
        target_format = args.get("target_format", "")
        output_dir = args.get("output_dir")
        if not input_path or not target_format:
            return {"error": "input_path 和 target_format 为必填参数"}
        return convert_document(input_path, target_format, output_dir)

    async def _extract_excel_json(
        self,
        args: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Excel/CSV 提取为 JSON"""
        from app.core.doc_converter import excel_to_json
        input_path = args.get("input_path", "")
        if not input_path:
            return {"error": "input_path 为必填参数"}
        return excel_to_json(
            input_path,
            sheet_name=args.get("sheet_name"),
            header_row=int(args.get("header_row", 0)),
            max_rows=int(args.get("max_rows", 2000)),
        )

    async def _auto_convert_upload(
        self,
        args: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """自动转换旧格式文档"""
        from app.core.doc_converter import auto_convert_for_upload
        input_path = args.get("input_path", "")
        if not input_path:
            return {"error": "input_path 为必填参数"}
        return auto_convert_for_upload(input_path, args.get("output_dir"))


# 全局工具执行器实例
tool_executor = ToolExecutor()