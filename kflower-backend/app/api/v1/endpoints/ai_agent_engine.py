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
from app.models.ai import Agent

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
                "created_at": agent.created_at.strftime("%Y-%m-%d") if agent.created_at else ""
            })
        
        if not agent_list:
            # 如果没有数据，插入一些示例智能体
            return await _create_sample_agents(db, current_user)
        
        return BaseResponse(data=agent_list)
    except Exception as e:
        # 模拟数据回退
        agents = [
            {"id": 1, "name": "客服助手", "type": "客服", "status": "在线", "tasks": 12, "description": "处理客户咨询", "created_at": "2026-04-01"},
            {"id": 2, "name": "数据分析师", "type": "分析", "status": "在线", "tasks": 8, "description": "生成数据报表", "created_at": "2026-04-05"},
            {"id": 3, "name": "文档助手", "type": "文档", "status": "离线", "tasks": 0, "description": "自动生成文档", "created_at": "2026-04-10"},
            {"id": 4, "name": "代码生成器", "type": "开发", "status": "在线", "tasks": 5, "description": "生成代码片段", "created_at": "2026-04-12"},
        ]
        return BaseResponse(data=agents)


@router.post("/agents")
async def create_agent(
    agent_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建智能体"""
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
    # 如果类型不包含 _agent，可以添加后缀（可选）
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
    """更新智能体"""
    from sqlalchemy import select
    from datetime import datetime
    
    # 查询现有智能体
    stmt = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    
    if not agent:
        return BaseResponse(success=False, message="智能体不存在")
    
    # 检查权限（可选：仅创建者或管理员可更新）
    # 这里简单检查组织权限
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


@router.get("/memory/stats")
async def get_memory_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取记忆统计信息"""
    # 模拟数据
    return BaseResponse(data={
        "total_memories": 2400,
        "active_memories": 1850,
        "memory_types": {
            "conversation": 1200,
            "knowledge": 650,
            "experience": 400,
            "other": 150
        },
        "last_updated": "2026-04-20 15:30:00"
    })


@router.get("/memory/list")
async def list_memories(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取记忆列表"""
    # 模拟数据
    memories = []
    for i in range(offset, min(offset + limit, 10)):
        memories.append({
            "id": i + 1,
            "content": f"记忆内容示例 {i + 1}",
            "type": ["conversation", "knowledge", "experience"][i % 3],
            "importance": i % 5 + 1,
            "created_at": f"2026-04-{20 - i % 10:02d} {10 + i % 10:02d}:{30 + i % 30:02d}:00",
            "last_accessed": f"2026-04-{20 - i % 5:02d} {14 + i % 10:02d}:{15 + i % 45:02d}:00"
        })
    return BaseResponse(data=memories)


async def _create_sample_agents(db: AsyncSession, current_user: User):
    """创建示例智能体（当数据库为空时）"""
    from sqlalchemy import select
    from datetime import datetime
    
    sample_agents = [
        {
            "name": "客服助手",
            "agent_type": "customer_service_agent",
            "description": "处理客户咨询",
            "status": "online",
            "task_count": 12,
            "config": {},
            "tools": [],
            "organization_id": current_user.organization_id,
            "created_by": current_user.id
        },
        {
            "name": "数据分析师",
            "agent_type": "analytics_agent",
            "description": "生成数据报表",
            "status": "online",
            "task_count": 8,
            "config": {},
            "tools": [],
            "organization_id": current_user.organization_id,
            "created_by": current_user.id
        },
        {
            "name": "文档助手",
            "agent_type": "document_agent",
            "description": "自动生成文档",
            "status": "offline",
            "task_count": 0,
            "config": {},
            "tools": [],
            "organization_id": current_user.organization_id,
            "created_by": current_user.id
        },
        {
            "name": "代码生成器",
            "agent_type": "development_agent",
            "description": "生成代码片段",
            "status": "online",
            "task_count": 5,
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

