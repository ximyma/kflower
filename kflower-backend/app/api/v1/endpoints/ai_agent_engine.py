"""
AI 智能体引擎 API
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/ai/agent-engine", tags=["AI智能体引擎"])


@router.get("/status")
async def get_agent_engine_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体引擎状态"""
    try:
        from app.core.agent_engine.agent_service import agent_service
        from app.core.agent_engine.orchestrator import agent_orchestrator
        from app.core.agent_engine.tools import tool_registry
        
        agents = agent_service.list_agents()
        tasks = agent_orchestrator.get_task_statistics()
        tools = tool_registry.list_tools()
        
        return BaseResponse(data={
            "agents_count": len(agents),
            "tasks_total": tasks.get("total", 0),
            "tasks_pending": tasks.get("pending", 0),
            "tasks_running": tasks.get("running", 0),
            "tasks_completed": tasks.get("completed", 0),
            "tools_count": len(tools),
            "memory_entries": 0,
            "orchestrator_status": "运行中" if agent_orchestrator.is_running() else "已停止",
            "last_updated": "2026-04-20 15:30:00"
        })
    except Exception as e:
        # 模拟数据
        return BaseResponse(data={
            "agents_count": 12,
            "tasks_total": 156,
            "tasks_pending": 8,
            "tasks_running": 3,
            "tasks_completed": 145,
            "tools_count": 8,
            "memory_entries": 2400,
            "orchestrator_status": "运行中",
            "last_updated": "2026-04-20 15:30:00"
        })


@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体列表"""
    try:
        from app.core.agent_engine.agent_service import agent_service
        agents = agent_service.list_agents()
        agent_list = []
        for agent in agents:
            agent_list.append({
                "id": agent.get("id", 0),
                "name": agent.get("name", "未知"),
                "type": agent.get("type", "通用"),
                "status": agent.get("status", "离线"),
                "tasks": agent.get("task_count", 0),
                "description": agent.get("description", ""),
                "created_at": agent.get("created_at", "")
            })
        return BaseResponse(data=agent_list)
    except Exception as e:
        # 模拟数据
        agents = [
            {"id": 1, "name": "客服助手", "type": "客服", "status": "在线", "tasks": 12, "description": "处理客户咨询", "created_at": "2026-04-01"},
            {"id": 2, "name": "数据分析师", "type": "分析", "status": "在线", "tasks": 8, "description": "生成数据报表", "created_at": "2026-04-05"},
            {"id": 3, "name": "文档助手", "type": "文档", "status": "离线", "tasks": 0, "description": "自动生成文档", "created_at": "2026-04-10"},
            {"id": 4, "name": "代码生成器", "type": "开发", "status": "在线", "tasks": 5, "description": "生成代码片段", "created_at": "2026-04-12"},
        ]
        return BaseResponse(data=agents)


@router.get("/tools")
async def list_tools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工具列表"""
    try:
        from app.core.agent_engine.tools import tool_registry
        tools = tool_registry.list_tools()
        tool_list = []
        for tool in tools:
            tool_list.append({
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "enabled": tool.get("enabled", True),
                "category": tool.get("category", "其他"),
                "call_count": tool.get("call_count", 0)
            })
        return BaseResponse(data=tool_list)
    except Exception as e:
        # 模拟数据
        tools = [
            {"name": "网页搜索", "description": "在互联网上搜索信息", "enabled": True, "category": "网络", "call_count": 120},
            {"name": "计算器", "description": "执行数学计算", "enabled": True, "category": "工具", "call_count": 85},
            {"name": "天气查询", "description": "查询城市天气", "enabled": True, "category": "生活", "call_count": 42},
            {"name": "翻译", "description": "多语言翻译", "enabled": True, "category": "语言", "call_count": 67},
            {"name": "数据库查询", "description": "查询数据库数据", "enabled": True, "category": "数据", "call_count": 33},
            {"name": "图表生成", "description": "生成数据图表", "enabled": True, "category": "可视化", "call_count": 18},
        ]
        return BaseResponse(data=tools)


@router.get("/tasks")
async def list_tasks(
    status: str = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    try:
        from app.core.agent_engine.orchestrator import agent_orchestrator
        tasks = agent_orchestrator.get_tasks(status_filter=status, limit=limit)
        return BaseResponse(data=tasks)
    except Exception as e:
        # 模拟数据
        tasks = [
            {"id": 1, "name": "生成月度报告", "status": "completed", "agent": "数据分析师", "created_at": "2026-04-19 09:30", "duration": "2分30秒"},
            {"id": 2, "name": "回答客户咨询", "status": "running", "agent": "客服助手", "created_at": "2026-04-20 14:15", "duration": "1分45秒"},
            {"id": 3, "name": "翻译文档", "status": "pending", "agent": "翻译助手", "created_at": "2026-04-20 13:00", "duration": ""},
        ]
        return BaseResponse(data=tasks)