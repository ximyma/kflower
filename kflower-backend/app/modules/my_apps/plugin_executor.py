"""
插件执行器 - 安全执行用户Python代码
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

# 尝试导入 RestrictedPython
try:
    from RestrictedPython import compile_restricted
    from restricted import safe_globals
    RESTRICTED_AVAILABLE = True
except ImportError:
    try:
        from RestrictedPython import compile_restricted
        # 创建安全的基础函数
        _safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'bool': bool, 'dict': dict,
            'enumerate': enumerate, 'float': float, 'int': int, 'len': len,
            'list': list, 'max': max, 'min': min, 'pow': pow, 'range': range,
            'round': round, 'set': set, 'sorted': sorted, 'str': str, 'sum': sum,
            'tuple': tuple, 'zip': zip, 'print': print, 'map': map, 'filter': filter,
            'isinstance': isinstance, 'issubclass': issubclass, 'type': type,
            'getattr': getattr, 'setattr': setattr, 'hasattr': hasattr,
            'open': None,  # 禁用文件操作
            '__import__': None,  # 禁用动态导入
            'eval': None,  # 禁用 eval
            'exec': None,  # 禁用 exec
        }
        RESTRICTED_AVAILABLE = True
    except ImportError:
        RESTRICTED_AVAILABLE = False
        logger.warning("RestrictedPython not installed, using safe eval fallback")


class PluginContext:
    """
    插件执行上下文
    提供插件脚本可用的所有API和工具
    """
    def __init__(
        self,
        data: Dict[str, Any],
        old_data: Optional[Dict[str, Any]],
        db: AsyncSession,
        user_id: int,
        template_id: int,
        event: str,
        app_id: int
    ):
        self._data = data
        self._old_data = old_data
        self._db = db
        self._user_id = user_id
        self._template_id = template_id
        self._event = event
        self._app_id = app_id

    @property
    def data(self) -> Dict[str, Any]:
        """当前操作的数据"""
        return self._data

    @property
    def old_data(self) -> Optional[Dict[str, Any]]:
        """更新前的数据（仅用于 update/delete 操作）"""
        return self._old_data

    @property
    def db(self) -> AsyncSession:
        """数据库会话"""
        return self._db

    @property
    def user_id(self) -> int:
        """当前用户ID"""
        return self._user_id

    @property
    def template_id(self) -> int:
        """当前模板ID"""
        return self._template_id

    @property
    def event(self) -> str:
        """触发事件名称"""
        return self._event

    @property
    def app_id(self) -> int:
        """所属应用ID"""
        return self._app_id

    async def update_record(self, target_template_id: int, record_id: int, update_data: Dict[str, Any]):
        """
        更新指定模板的记录
        用法：await context.update_record(123, 456, {'status': 'approved'})
        """
        return await _update_record_async(self._db, target_template_id, record_id, update_data)

    async def create_record(self, target_template_id: int, record_data: Dict[str, Any]) -> int:
        """
        创建指定模板的新记录
        返回新记录的ID
        """
        return await _create_record_async(self._db, target_template_id, record_data)

    async def query_records(self, target_template_id: int, filters: list = None, limit: int = 100) -> list:
        """
        查询指定模板的记录
        filters: [{"field": "status", "op": "=", "value": "active"}]
        返回记录列表
        """
        return await _query_records_async(self._db, target_template_id, filters, limit)

    def send_notification(self, user_id: int, title: str, content: str):
        """
        发送站内通知
        """
        logger.info(f"[Notification] To user {user_id}: {title} - {content}")
        # 这里可以集成到实际的通知系统

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        getattr(logger, level, logger.info)(f"[Plugin:{self._app_id}] {message}")


async def _update_record_async(db: AsyncSession, template_id: int, record_id: int, update_data: Dict[str, Any]):
    """异步更新记录"""
    # 获取表名
    from sqlalchemy import select
    from app.models.workflow import Template

    # 直接构建 SQL（安全的动态表名）
    table_name = f"form_data_{template_id}"

    if not table_name.startswith("form_data_"):
        raise ValueError("Invalid table name")

    set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
    sql = f"UPDATE {table_name} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = :rid"
    params = {**update_data, "rid": record_id}

    # 清理params中的None值
    params = {k: v for k, v in params.items() if v is not None}

    return await db.execute(text(sql), params)


async def _create_record_async(db: AsyncSession, template_id: int, record_data: Dict[str, Any]) -> int:
    """异步创建记录，返回新ID"""
    table_name = f"form_data_{template_id}"

    if not table_name.startswith("form_data_"):
        raise ValueError("Invalid table name")

    columns = list(record_data.keys()) + ["template_id", "created_at", "updated_at"]
    placeholders = [f":{k}" for k in record_data.keys()] + [":template_id", "CURRENT_TIMESTAMP", "CURRENT_TIMESTAMP"]
    values = {**record_data, "template_id": template_id}

    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

    result = await db.execute(text(sql), values)
    await db.commit()

    # 获取新插入的ID
    res = await db.execute(text("SELECT last_insert_rowid()"))
    return res.scalar()


async def _query_records_async(db: AsyncSession, template_id: int, filters: list = None, limit: int = 100) -> list:
    """异步查询记录"""
    table_name = f"form_data_{template_id}"

    if not table_name.startswith("form_data_"):
        raise ValueError("Invalid table name")

    where_clause = "WHERE 1=1"
    params = {}

    if filters:
        for i, f in enumerate(filters):
            field = f.get("field", "")
            op = f.get("op", "=")
            value = f.get("value", "")
            key = f"p{i}"

            if op == "=":
                where_clause += f" AND {field} = :{key}"
            elif op == ">":
                where_clause += f" AND {field} > :{key}"
            elif op == "<":
                where_clause += f" AND {field} < :{key}"
            elif op == ">=":
                where_clause += f" AND {field} >= :{key}"
            elif op == "<=":
                where_clause += f" AND {field} <= :{key}"
            elif op == "like":
                where_clause += f" AND {field} LIKE :{key}"
                value = f"%{value}%"
            elif op == "in":
                if isinstance(value, list):
                    placeholders = [f":{key}_{j}" for j in range(len(value))]
                    where_clause += f" AND {field} IN ({','.join(placeholders)})"
                    for j, v in enumerate(value):
                        params[f"{key}_{j}"] = v
                    continue

            params[key] = value

    sql = f"SELECT * FROM {table_name} {where_clause} LIMIT :limit"
    params["limit"] = limit

    result = await db.execute(text(sql), params)
    rows = result.fetchall()
    columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


class PluginExecutor:
    """插件执行器"""

    # 安全函数白名单
    SAFE_BUILTINS = {
        'abs': abs, 'all': all, 'any': any, 'bool': bool, 'dict': dict,
        'enumerate': enumerate, 'float': float, 'int': int, 'len': len,
        'list': list, 'max': max, 'min': min, 'pow': pow, 'range': range,
        'round': round, 'set': set, 'sorted': sorted, 'str': str, 'sum': sum,
        'tuple': tuple, 'zip': zip, 'print': print, 'map': map, 'filter': filter,
        'isinstance': isinstance, 'issubclass': issubclass,
        'True': True, 'False': False, 'None': None,
    }

    # 禁用危险函数
    FORBIDDEN_NAMES = {
        '__import__', 'eval', 'exec', 'open', 'file', 'input', 'compile',
        'reload', '__builtins__', '__globals__', '__locals__', 'globals',
        'locals', 'getattr', 'setattr', 'delattr', 'hasattr',
        'memoryview', 'buffer', 'bytearray', 'property', 'classmethod',
        'staticmethod', 'super', 'type', 'object',
    }

    @staticmethod
    async def execute(
        script_code: str,
        context: PluginContext,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        执行插件脚本
        :param script_code: Python脚本代码
        :param context: 插件上下文
        :param timeout: 超时时间（秒）
        :return: {"success": bool, "output": any, "error": str}
        """
        if not script_code or not script_code.strip():
            return {"success": False, "error": "插件代码为空"}

        # 检查代码安全性
        security_check = PluginExecutor._check_security(script_code)
        if not security_check["safe"]:
            return {"success": False, "error": f"代码安全检查失败: {security_check['reason']}"}

        # 准备执行环境
        execution_globals = {
            '__builtins__': PluginExecutor.SAFE_BUILTINS,
            '__name__': '__plugin__',
            'context': context,
        }

        try:
            # 编译代码
            if RESTRICTED_AVAILABLE:
                byte_code = compile_restricted(script_code, filename='<plugin>', mode='exec')
                if hasattr(byte_code, 'errors') and byte_code.errors:
                    errors = '; '.join(str(e) for e in byte_code.errors)
                    return {"success": False, "error": f"编译错误: {errors}"}
                code_to_exec = byte_code
            else:
                # 回退到普通编译
                code_to_exec = compile(script_code, '<plugin>', 'exec')

            # 执行代码
            async def run_plugin():
                exec(code_to_exec, execution_globals)

                # 查找并执行事件钩子函数
                for event_name in ['after_save', 'before_save', 'after_delete', 'before_delete', 'on_load']:
                    if event_name in execution_globals:
                        func = execution_globals[event_name]
                        if callable(func):
                            result = func(context)
                            # 处理协程
                            if asyncio.iscoroutine(result):
                                result = await result
                            return result

                return None

            # 带超时执行
            output = await asyncio.wait_for(run_plugin(), timeout=timeout)
            return {"success": True, "output": output}

        except asyncio.TimeoutError:
            return {"success": False, "error": f"插件执行超时（{timeout}秒）"}
        except SyntaxError as e:
            return {"success": False, "error": f"语法错误: {str(e)}"}
        except Exception as e:
            logger.exception(f"Plugin execution error: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _check_security(code: str) -> Dict[str, Any]:
        """检查代码安全性"""
        forbidden_found = []

        for name in PluginExecutor.FORBIDDEN_NAMES:
            if name in code:
                # 排除注释中的
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if f'#{name}' in line or f'"{name}"' in line or f"'{name}'" in line:
                        continue
                    if name in line:
                        forbidden_found.append(f"{name} (line {i+1})")

        if forbidden_found:
            return {
                "safe": False,
                "reason": f"禁止使用: {', '.join(forbidden_found)}"
            }

        # 检查危险模式
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess',
            'import socket', 'import requests', 'import httpx',
            'subprocess.', 'os.system', 'os.popen',
            'eval(', 'exec(', 'compile(',
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                return {
                    "safe": False,
                    "reason": f"危险模式: {pattern}"
                }

        return {"safe": True}


# 全局实例
plugin_executor = PluginExecutor()
