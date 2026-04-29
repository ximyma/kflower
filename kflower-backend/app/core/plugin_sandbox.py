"""
插件沙箱 - 为新插件系统提供安全的 Python 代码执行环境
基于 my_apps/plugin_executor.py 的成熟实现
"""
import asyncio
import logging
import sys
import io
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 复用现有的执行器核心
try:
    from app.modules.my_apps.plugin_executor import (
        PluginExecutor,
        PluginContext,
        RESTRICTED_AVAILABLE
    )
except ImportError:
    logger.warning("Could not import from plugin_executor, using fallback")
    RESTRICTED_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
#  超时异步执行
# ─────────────────────────────────────────────────────────────────────────────

async def _run_with_timeout(coro, timeout_seconds: float = 5.0) -> Any:
    """在超时限制内运行协程"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Plugin execution timed out after {timeout_seconds}s")


# ─────────────────────────────────────────────────────────────────────────────
#  沙箱执行器
# ─────────────────────────────────────────────────────────────────────────────

class PluginSandbox:
    """
    插件沙箱 - 执行用户编写的插件钩子代码
    安全隔离 + 超时控制
    """

    DEFAULT_TIMEOUT = 5.0  # 默认超时 5 秒

    def __init__(
        self,
        plugin_name: str,
        context: Optional[Dict[str, Any]] = None
    ):
        self.plugin_name = plugin_name
        self.context = context or {}
        self._logs: list = []

    def _make_context(self) -> "PluginContext":
        """从字典创建 PluginContext"""
        from app.modules.my_apps.plugin_executor import PluginContext
        # Get sync session for DB operations
        session = None
        try:
            from app.core.database import engine_sync
            session = engine_sync.connect()
        except (ImportError, AttributeError):
            pass

        return PluginContext(
            data=self.context.get("data", {}),
            old_data=self.context.get("old_data"),
            db=session,
            user_id=self.context.get("user_id", 1),
            template_id=self.context.get("template_id", 0),
            event=self.context.get("event", ""),
            app_id=self.context.get("app_id", 0)
        )

    async def execute(self, code: str) -> Dict[str, Any]:
        """
        执行插件代码，返回执行结果
        {
            success: bool,
            output: Any,
            logs: list,
            error: str | None,
            duration_ms: float
        }
        """
        import time
        start = time.time()

        # 1. 捕获 print 输出
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()

        result = {
            "success": False,
            "output": None,
            "logs": [],
            "error": None,
            "duration_ms": 0
        }

        try:
            # 2. 构建上下文对象
            ctx = self._make_context()

            # 3. 执行代码（带超时）
            timeout = self.context.get("timeout", self.DEFAULT_TIMEOUT)
            output = await _run_with_timeout(
                PluginExecutor.execute(code, ctx),
                timeout_seconds=timeout
            )

            # 4. 收集日志
            captured_output = captured.getvalue()
            if captured_output:
                self._logs.append(captured_output.strip())

            result["success"] = True
            result["output"] = output
            result["logs"] = self._logs

        except TimeoutError as e:
            result["error"] = f"执行超时: {str(e)}"
            logger.warning(f"[PluginSandbox:{self.plugin_name}] Timeout: {e}")
        except SyntaxError as e:
            result["error"] = f"语法错误: {str(e)}"
            logger.warning(f"[PluginSandbox:{self.plugin_name}] SyntaxError: {e}")
        except Exception as e:
            result["error"] = f"执行错误: {str(e)}"
            logger.error(f"[PluginSandbox:{self.plugin_name}] Error: {e}", exc_info=True)
        finally:
            sys.stdout = old_stdout  # 恢复 stdout
            result["duration_ms"] = int((time.time() - start) * 1000)

        return result

    def log(self, message: str):
        """记录日志"""
        self._logs.append(message)


# ─────────────────────────────────────────────────────────────────────────────
#  辅助函数（供前端直接调用测试）
# ─────────────────────────────────────────────────────────────────────────────

async def test_plugin_hook(
    plugin_name: str,
    hook_name: str,
    code: str,
    mock_data: Dict[str, Any],
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    测试插件钩子代码
    """
    sandbox = PluginSandbox(plugin_name, {**mock_data, "timeout": timeout})
    return await sandbox.execute(code)


# ─────────────────────────────────────────────────────────────────────────────
#  钩子事件定义
# ─────────────────────────────────────────────────────────────────────────────

HOOK_EVENTS = {
    # 事件名: (描述, 触发时机)
    "before_form_render": ("表单渲染前", "list/form 加载时"),
    "after_form_submit": ("表单提交后", "数据保存成功后"),
    "before_form_submit": ("表单提交前", "数据保存前，可修改数据"),
    "after_data_delete": ("数据删除后", "删除操作完成后"),
    "on_list_load": ("列表加载时", "查询数据时"),
    "on_field_change": ("字段变更时", "字段值变化时"),
    "on_cron_schedule": ("定时任务", "cron 表达式触发"),
    "on_api_called": ("API调用时", "外部 API 访问时"),
}


def get_hook_event_docs() -> Dict[str, Any]:
    """返回钩子事件文档"""
    return {
        name: {
            "display_name": info[0],
            "timing": info[1],
            "example": _HOOK_EXAMPLES.get(name, "")
        }
        for name, info in HOOK_EVENTS.items()
    }


_HOOK_EXAMPLES = {
    "after_form_submit": '''# 发送通知示例
title = f"新订单: {data.get('order_no', '')}"
send_notification(1, title, str(data))
log("通知已发送")
''',
    "on_list_load": '''# 添加筛选条件
filters.append({"field": "status", "op": "=", "value": "active"})
log(f"已添加筛选，当前记录数: {len(data)}")
''',
    "before_form_submit": '''# 数据校验
if data.get("amount", 0) <= 0:
    raise ValueError("金额必须大于0")
data["status"] = "pending"
''',
}
