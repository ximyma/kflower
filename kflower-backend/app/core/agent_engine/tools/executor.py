"""
智能体引擎 - 工具调用执行器
实现工具的实际执行逻辑
"""
from typing import Dict, Any, Optional, List
from app.core.agent_engine.tools.registry import tool_registry, ToolType
from app.core.database import get_db
from sqlalchemy import text
import json
import os
import sys
import logging
from datetime import datetime

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
            # 系统工具
            "read_file": self._read_file,
            "write_file": self._write_file,
            "list_files": self._list_files,
            "search_content": self._search_content,
            "bash": self._bash,
            "get_env_info": self._get_env_info,
            "read_workflow_logs": self._read_workflow_logs,
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
        from app.core.workflow.engine import WorkflowEngine
        
        workflow_id = args.get("workflow_id")
        title = args.get("title", "Agent触发的工作流")
        data = args.get("data", {})
        user_id = context.get("user_id", 1)
        
        async with get_db() as db:
            engine = WorkflowEngine(db)
            instance = await engine.start_instance(
                workflow_id=workflow_id,
                title=title,
                starter_id=user_id,
                variables=data
            )
            
            return {
                "instance_id": instance.id,
                "status": instance.status,
                "title": instance.title,
                "message": f"工作流实例 {instance.id} 已启动"
            }
    
    async def _query_data(
        self, 
        args: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """查询数据（安全版：白名单验证表名）"""
        table = args.get("table", "")
        conditions = args.get("conditions", {})
        
        # 白名单验证表名
        allowed_tables = {"templates", "workflows", "workflow_instances", "workflow_tasks", 
                         "users", "organizations", "plugins", "notifications", "knowledge_bases"}
        # 也允许 form_data_ 前缀的动态表
        if table not in allowed_tables and not table.startswith("form_data_"):
            return {"error": f"不允许查询表: {table}"}
        
        async with get_db() as db:
            # 表名已通过白名单验证（安全）
            query = f'SELECT * FROM "{table}" WHERE 1=1'
            params = {}
            
            for key, value in conditions.items():
                # 列名验证：仅允许字母数字和下划线
                safe_key = "".join(c for c in key if c.isalnum() or c == "_")
                if safe_key != key:
                    return {"error": f"不允许的列名: {key}"}
                param_name = f"p_{safe_key}_{len(params)}"
                query += f' AND "{safe_key}" = :{param_name}'
                params[param_name] = value
            
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

    # ===== 系统工具处理 =====
    
    def _resolve_safe_path(self, path: str) -> str:
        """安全路径解析：限制在工作区范围内，防止路径穿越"""
        workspace = os.path.abspath(os.environ.get("PROJECT_ROOT", "D:/kkflower"))
        
        # 如果传入绝对路径，必须限制在工作区范围内
        if os.path.isabs(path):
            full_path = os.path.abspath(path)
        else:
            full_path = os.path.abspath(os.path.join(workspace, path))
        
        # 路径穿越检测：规范化后的路径必须在工作区内
        if not full_path.startswith(workspace):
            raise ValueError(f"路径不在允许范围内: {path}")
        
        # 额外检测 .. 穿越
        if ".." in path.split(os.sep):
            raise ValueError(f"路径包含非法字符: {path}")
        
        return full_path
    
    async def _read_file(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """读取文件"""
        path = args.get("path", "")
        offset = args.get("offset", 0)
        limit = args.get("limit", 100)
        
        if not path:
            return {"error": "path 为必填参数"}
        
        # 安全检查：不允许读取敏感文件
        forbidden = ["/etc/passwd", "/etc/shadow", ".env", "credentials", "secrets"]
        if any(f in path for f in forbidden):
            return {"error": "不允许读取敏感文件"}
        
        try:
            # 使用安全路径解析器
            full_path = self._resolve_safe_path(path)
            
            if not os.path.exists(full_path):
                return {"error": f"文件不存在: {path}"}
            
            if os.path.isdir(full_path):
                return {"error": f"目标是一个目录: {path}"}
            
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            total = len(lines)
            selected = lines[offset:offset + limit]
            content = "".join(selected)
            
            return {
                "content": content,
                "path": path,
                "total_lines": total,
                "offset": offset,
                "limit": limit,
                "shown_lines": len(selected)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _write_file(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """写入文件"""
        path = args.get("path", "")
        content = args.get("content", "")
        
        if not path:
            return {"error": "path 为必填参数"}
        
        try:
            full_path = self._resolve_safe_path(path)
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {
                "success": True,
                "path": path,
                "size": len(content),
                "message": f"文件已写入: {path}"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _list_files(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """列出文件"""
        path = args.get("path", ".")
        pattern = args.get("pattern", "*")
        
        try:
            full_path = self._resolve_safe_path(path)
            
            import glob
            files = glob.glob(os.path.join(full_path, pattern))
            # 限制数量
            files = files[:200]
            
            result = []
            for f in files:
                stat = os.stat(f)
                result.append({
                    "name": os.path.basename(f),
                    "path": f,
                    "size": stat.st_size,
                    "is_dir": os.path.isdir(f),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return {"files": result, "count": len(result)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _search_content(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """搜索文件内容"""
        pattern = args.get("pattern", "")
        path = args.get("path", ".")
        
        if not pattern:
            return {"error": "pattern 为必填参数"}
        
        try:
            full_path = self._resolve_safe_path(path)
            
            import subprocess
            # 使用 grep 搜索
            cmd = ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.vue", 
                   "--include=*.md", "--include=*.json", "-m", "50", pattern, full_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, 
                                   cwd=workspace)
            
            output = result.stdout.strip()
            if not output:
                return {"matches": [], "count": 0, "message": "未找到匹配结果"}
            
            lines = output.split("\n")[:50]
            return {"matches": lines, "count": len(lines)}
        except subprocess.TimeoutExpired:
            return {"error": "搜索超时"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _bash(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """执行 Shell 命令（Phase 4 安全加固：白名单模式）"""
        command = args.get("command", "")
        timeout = args.get("timeout", 30)
        
        if not command:
            return {"error": "command 为必填参数"}
        
        # 白名单：仅允许安全的只读/信息类命令
        allowed_commands = ["ls", "dir", "cat", "head", "tail", "wc", "find", "grep",
                           "echo", "date", "whoami", "pwd", "uname", "hostname",
                           "python --version", "node --version", "npm --version", "pip list",
                           "git status", "git log", "git branch", "git diff", "git stash list",
                           "df", "du", "free", "uptime", "ps"]
        
        # 提取命令基础部分进行白名单检查
        cmd_base = command.strip().split()[0] if command.strip() else ""
        if cmd_base not in [c.split()[0] for c in allowed_commands]:
            return {"error": f"不允许执行命令: {cmd_base}。仅支持安全的只读命令。",
                    "allowed_commands": allowed_commands}
        
        # 黑名单：即使基础命令在白名单中，也禁止危险参数组合
        dangerous_patterns = ["|", ";", "&&", "||", "$(", "`", ">", ">>", "<", "rm -", 
                             "mkfs", "dd ", "shutdown", "reboot", "chmod", "chown", 
                             "wget", "curl", "nc ", "telnet", "/dev/", "/etc/", "/proc/"]
        if any(p in command for p in dangerous_patterns):
            return {"error": "命令包含禁止的模式"}
        
        try:
            workspace = os.environ.get("PROJECT_ROOT", "D:/kkflower")
            import subprocess
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=min(timeout, 30), cwd=workspace
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            return {
                "stdout": output[:2000] if output else "",
                "stderr": error[:500] if error else "",
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": f"命令执行超时（{timeout}s）"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_env_info(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """获取系统环境信息"""
        from app.core.database import engine
        from sqlalchemy import text
        
        try:
            python_version = sys.version
            
            # 数据库状态
            db_status = "unknown"
            try:
                async with get_db() as db:
                    result = await db.execute(text("SELECT 1"))
                    db_status = "connected"
            except:
                db_status = "disconnected"
            
            # 项目路径
            project_root = os.environ.get("PROJECT_ROOT", os.getcwd())
            
            return {
                "python_version": python_version,
                "database_status": db_status,
                "project_root": project_root,
                "platform": sys.platform,
                "current_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _read_workflow_logs(self, args: Dict, context: Dict) -> Dict[str, Any]:
        """读取工作流审批日志"""
        instance_id = args.get("instance_id")
        if not instance_id:
            return {"error": "instance_id 为必填参数"}
        
        async with get_db() as db:
            from sqlalchemy import select
            from app.models.workflow import WorkflowLog, WorkflowInstance
            result = await db.execute(
                select(WorkflowLog).where(
                    WorkflowLog.instance_id == instance_id
                ).order_by(WorkflowLog.created_at.asc())
            )
            logs = result.scalars().all()
            
            return {
                "instance_id": instance_id,
                "logs": [
                    {
                        "action": l.action,
                        "operator_id": l.operator_id,
                        "comment": l.comment,
                        "created_at": l.created_at.isoformat() if l.created_at else None
                    }
                    for l in logs
                ],
                "count": len(logs)
            }


# 全局工具执行器实例
tool_executor = ToolExecutor()