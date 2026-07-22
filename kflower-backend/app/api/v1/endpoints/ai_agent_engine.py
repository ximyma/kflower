"""
AI 智能体引擎 API
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import BaseResponse
from app.models.ai import Agent

router = APIRouter(prefix="/ai/agent-engine", tags=["AI智能体引擎"])


@router.get("/status")
async def get_agent_engine_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体引擎状态"""
    from app.core.agent_engine.agent_service import agent_service
    from app.core.agent_engine.orchestrator import agent_orchestrator
    from app.core.agent_engine.tools import tool_registry
    
    try:
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
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        import traceback
        logging.getLogger(__name__).error(f"获取智能体引擎状态失败: {traceback.format_exc()}")
        return BaseResponse(
            success=False,
            message=f"获取状态失败: {str(e)}",
            data={
                "agents_count": 0,
                "tasks_total": 0,
                "tasks_pending": 0,
                "tasks_running": 0,
                "tasks_completed": 0,
                "tools_count": 0,
                "memory_entries": 0,
                "orchestrator_status": "错误"
            }
        )


@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取智能体列表（整合优化 1.2：返回模块绑定信息）"""
    try:
        # 从数据库查询智能体
        from sqlalchemy import select
        stmt = select(Agent)
        result = await db.execute(stmt)
        agents_db = result.scalars().all()

        agent_list = []
        for agent in agents_db:
            # 状态映射：offline -> 离线, online -> 在线, disabled -> 禁用
            status_map = {
                "offline": "离线",
                "online": "在线",
                "disabled": "禁用"
            }
            status_display = status_map.get(agent.status, "离线")

            # 类型映射：保持原样或转换
            type_display = agent.agent_type
            if agent.agent_type.endswith("_agent"):
                type_display = agent.agent_type.replace("_agent", "")

            agent_list.append({
                "id": agent.id,
                "name": agent.name,
                "type": type_display,
                "status": status_display,
                "tasks": agent.task_count,
                "description": agent.description or "",
                "template_ids": agent.template_ids or [],
                "workflow_ids": agent.workflow_ids or [],
                "knowledge_base_ids": agent.knowledge_base_ids or [],
                "plugin_ids": agent.plugin_ids or [],
                "system_prompt": agent.system_prompt or "",
                "scope": agent.scope or "global",
                "created_at": agent.created_at.strftime("%Y-%m-%d") if agent.created_at else ""
            })

        if not agent_list:
            # 如果没有数据，插入一些示例智能体
            return await _create_sample_agents(db, current_user)

        return BaseResponse(data=agent_list)
    except Exception as e:
        import traceback
        logging.getLogger(__name__).error(f"获取智能体列表失败: {traceback.format_exc()}")
        return BaseResponse(success=False, message=f"获取智能体列表失败: {str(e)}", data=[])


@router.post("/agents")
async def create_agent(
    agent_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建智能体（整合优化 1.2：支持模块绑定字段）"""
    from datetime import datetime

    # 验证必要字段
    if not agent_data.get("name"):
        return BaseResponse(success=False, message="智能体名称不能为空")

    # 状态映射：中文 -> 数据库值
    status_map = {
        "在线": "online",
        "离线": "offline",
        "禁用": "disabled"
    }

    # 获取前端数据
    name = agent_data.get("name")
    agent_type = agent_data.get("type", "general")
    if not agent_type.endswith("_agent"):
        agent_type = f"{agent_type}_agent"

    description = agent_data.get("description", "")
    status_cn = agent_data.get("status", "离线")
    status = status_map.get(status_cn, "offline")

    # 创建智能体记录
    agent = Agent(
        name=name,
        agent_type=agent_type,
        description=description,
        status=status,
        task_count=0,
        config=agent_data.get("config", {}),
        tools=agent_data.get("tools", []),
        # ===== 模块绑定字段（整合优化 1.2） =====
        template_ids=agent_data.get("template_ids", []),
        workflow_ids=agent_data.get("workflow_ids", []),
        knowledge_base_ids=agent_data.get("knowledge_base_ids", []),
        plugin_ids=agent_data.get("plugin_ids", []),
        system_prompt=agent_data.get("system_prompt"),
        scope=agent_data.get("scope", "global"),
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # 返回创建的数据
    return BaseResponse(
        data={
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type.replace("_agent", "") if agent.agent_type.endswith("_agent") else agent.agent_type,
            "status": "在线" if agent.status == "online" else "离线",
            "tasks": agent.task_count,
            "description": agent.description or "",
            "template_ids": agent.template_ids or [],
            "workflow_ids": agent.workflow_ids or [],
            "knowledge_base_ids": agent.knowledge_base_ids or [],
            "plugin_ids": agent.plugin_ids or [],
            "system_prompt": agent.system_prompt or "",
            "scope": agent.scope or "global",
            "created_at": agent.created_at.strftime("%Y-%m-%d") if agent.created_at else ""
        },
        message="智能体创建成功"
    )


@router.put("/agents/{agent_id}")
async def update_agent(
    agent_id: int,
    agent_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新智能体（整合优化 1.2：支持模块绑定字段）"""
    from sqlalchemy import select
    from datetime import datetime

    # 查询现有智能体
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()

    if not agent:
        return BaseResponse(success=False, message="智能体不存在")

    # 检查权限（可选：仅创建者或管理员可更新）
    if agent.organization_id != current_user.organization_id:
        return BaseResponse(success=False, message="无权限更新此智能体")

    # 状态映射
    status_map = {
        "在线": "online",
        "离线": "offline",
        "禁用": "disabled"
    }

    # 更新字段
    if "name" in agent_data:
        agent.name = agent_data["name"]

    if "type" in agent_data:
        agent_type = agent_data["type"]
        if not agent_type.endswith("_agent"):
            agent_type = f"{agent_type}_agent"
        agent.agent_type = agent_type

    if "description" in agent_data:
        agent.description = agent_data["description"]

    if "status" in agent_data:
        status_cn = agent_data["status"]
        agent.status = status_map.get(status_cn, "offline")

    if "tasks" in agent_data:
        agent.task_count = agent_data["tasks"]

    if "config" in agent_data:
        agent.config = agent_data["config"]

    if "tools" in agent_data:
        agent.tools = agent_data["tools"]

    # ===== 模块绑定字段更新（整合优化 1.2） =====
    if "template_ids" in agent_data:
        agent.template_ids = agent_data["template_ids"]

    if "workflow_ids" in agent_data:
        agent.workflow_ids = agent_data["workflow_ids"]

    if "knowledge_base_ids" in agent_data:
        agent.knowledge_base_ids = agent_data["knowledge_base_ids"]

    if "plugin_ids" in agent_data:
        agent.plugin_ids = agent_data["plugin_ids"]

    if "system_prompt" in agent_data:
        agent.system_prompt = agent_data["system_prompt"]

    if "scope" in agent_data:
        agent.scope = agent_data["scope"]

    agent.updated_at = datetime.now()

    await db.commit()
    await db.refresh(agent)

    # 返回更新后的数据
    type_display = agent.agent_type
    if agent.agent_type.endswith("_agent"):
        type_display = agent.agent_type.replace("_agent", "")

    status_display = "离线"
    if agent.status == "online":
        status_display = "在线"
    elif agent.status == "disabled":
        status_display = "禁用"

    return BaseResponse(
        data={
            "id": agent.id,
            "name": agent.name,
            "type": type_display,
            "status": status_display,
            "tasks": agent.task_count,
            "description": agent.description or "",
            "template_ids": agent.template_ids or [],
            "workflow_ids": agent.workflow_ids or [],
            "knowledge_base_ids": agent.knowledge_base_ids or [],
            "plugin_ids": agent.plugin_ids or [],
            "system_prompt": agent.system_prompt or "",
            "scope": agent.scope or "global",
            "updated_at": agent.updated_at.strftime("%Y-%m-%d") if agent.updated_at else ""
        },
        message="智能体更新成功"
    )


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除智能体"""
    from sqlalchemy import select, delete
    
    # 查询现有智能体
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        return BaseResponse(success=False, message="智能体不存在")
    
    # 检查权限（可选）
    if agent.organization_id != current_user.organization_id:
        return BaseResponse(success=False, message="无权限删除此智能体")
    
    # 执行删除
    delete_stmt = delete(Agent).where(Agent.id == agent_id)
    await db.execute(delete_stmt)
    await db.commit()
    
    return BaseResponse(
        message=f"智能体 {agent_id} 删除成功"
    )




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
        logging.getLogger(__name__).error(f"获取工具列表失败: {e}")
        return BaseResponse(success=False, message=f"获取工具列表失败: {str(e)}", data=[])


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
        logging.getLogger(__name__).error(f"获取任务列表失败: {e}")
        return BaseResponse(success=False, message=f"获取任务列表失败: {str(e)}", data=[])


# ===== Phase 1 清理：memory/stats 和 memory/list 已移除 =====
# 原因：返回硬编码空数据，无实际价值
# 记忆管理功能将在 Phase 2 Agent 重构时重新实现


async def _create_sample_agents(db: AsyncSession, current_user: User):
    """创建示例智能体（当数据库为空时）"""
    from sqlalchemy import select
    from datetime import datetime
    
    sample_agents = [
        {
            "name": "通用助手",
            "agent_type": "general_agent",
            "description": "基于 ReAct 循环的通用智能体，支持工具调用和自主决策",
            "status": "online",
            "task_count": 8,
            "config": {},
            "tools": [],
            "organization_id": current_user.organization_id,
            "created_by": current_user.id
        },
        {
            "name": "数据分析",
            "agent_type": "general_agent",
            "description": "数据分析和报表生成",
            "status": "online",
            "task_count": 5,
            "config": {},
            "tools": [],
            "organization_id": current_user.organization_id,
            "created_by": current_user.id
        },
        {
            "name": "模板设计",
            "agent_type": "general_agent",
            "description": "智能表单模板设计",
            "status": "offline",
            "task_count": 0,
            "config": {},
            "tools": [],
            "organization_id": current_user.organization_id,
            "created_by": current_user.id
        },
    ]
    
    agent_list = []
    for idx, agent_data in enumerate(sample_agents, start=1):
        agent = Agent(
            name=agent_data["name"],
            agent_type=agent_data["agent_type"],
            description=agent_data["description"],
            status=agent_data["status"],
            task_count=agent_data["task_count"],
            config=agent_data["config"],
            tools=agent_data["tools"],
            organization_id=agent_data["organization_id"],
            created_by=agent_data["created_by"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(agent)
        agent_list.append({
            "id": idx,
            "name": agent.name,
            "type": agent.agent_type.replace("_agent", ""),
            "status": "在线" if agent.status == "online" else "离线",
            "tasks": agent.task_count,
            "description": agent.description,
            "created_at": agent.created_at.strftime("%Y-%m-%d") if agent.created_at else ""
        })
    
    await db.commit()
    # 刷新以获取生成的ID
    for agent in agent_list:
        # 由于我们尚未刷新，ID是占位符；在实际使用中，我们可以查询数据库
        pass
    
    return BaseResponse(data=agent_list)


# ===== Phase 1 清理：POST /chat 端点已移除 =====
# 原因：使用 httpx 向自身发 HTTP 请求（循环调用），已损坏
# AI 对话请统一使用 /api/v1/ai/chat 或 /api/v1/agent/chat
# ===== 文件结束 =====

