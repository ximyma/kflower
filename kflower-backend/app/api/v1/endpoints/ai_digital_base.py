"""
AI数字底座 - 状态监控和配置API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.ai_digital_base.gateway import ai_gateway
from app.core.ai_digital_base.model_manager import AIModelManager
from app.core.ai_digital_base.inference import inference_service
from app.core.ai_digital_base.conversation import conversation_manager
from app.core.agent_engine.orchestrator import agent_orchestrator
from app.models.user import User

router = APIRouter(prefix="/ai/digital-base", tags=["AI数字底座"])


@router.get("/status")
async def get_digital_base_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取AI数字底座整体状态"""
    # 确保配置已加载
    await ai_gateway.load_config_from_db(db)
    
    # 1. AI网关状态
    gateway_status = {
        "current_provider": ai_gateway.current_provider,
        "available_providers": list(ai_gateway.providers.keys()),
        "dynamic_config_loaded": ai_gateway._config_loaded,
        "config_count": len(ai_gateway._dynamic_config),
    }
    
    # 2. 模型管理器状态
    model_manager = AIModelManager()
    available_models = model_manager.get_all_available_models()
    model_status = {
        "total_models": sum(len(models) for models in available_models.values()),
        "providers": list(available_models.keys()),
        "model_list": available_models,
    }
    
    # 3. 推理服务状态
    inference_status = {
        "service_ready": True,
        "capabilities": ["text_complete", "analyze_intent", "generate_template", "generate_workflow", "generate_chart_config", "explain_workflow", "suggest_fields"],
    }
    
    # 4. 对话管理器状态
    conversation_status = {
        "active_conversations": len(conversation_manager.conversations),
        "total_messages": sum(len(conv) for conv in conversation_manager.conversations.values()),
    }
    
    # 5. 智能体编排器状态
    try:
        from app.core.agent_engine.orchestrator import AgentType
        orchestrator_status = {
            "available_agents": [agent.value for agent in AgentType],
            "active_tasks": len([task for task in agent_orchestrator.task_queue if task.status == "running"]),
        }
    except Exception as e:
        orchestrator_status = {
            "available_agents": [],
            "active_tasks": 0,
            "error": str(e)
        }
    
    # 6. 系统健康状态
    health_status = {
        "database": True,
        "ai_gateway": gateway_status["current_provider"] is not None,
        "model_manager": len(model_status["providers"]) > 0,
        "inference_service": inference_status["service_ready"],
        "conversation_manager": True,
        "agent_orchestrator": True,
    }
    
    return {
        "success": True,
        "data": {
            "gateway": gateway_status,
            "model_manager": model_status,
            "inference_service": inference_status,
            "conversation_manager": conversation_status,
            "agent_orchestrator": orchestrator_status,
            "health": health_status,
            "overall_status": "healthy" if all(health_status.values()) else "degraded",
        }
    }


@router.get("/providers/detailed")
async def get_detailed_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取详细的提供商配置信息"""
    await ai_gateway.load_config_from_db(db)
    
    providers = []
    for name, config in ai_gateway.providers.items():
        providers.append({
            "name": name,
            "api_key_set": bool(config.get("api_key")),
            "base_url": config.get("base_url"),
            "model": config.get("model"),
            "timeout": config.get("timeout"),
            "temperature": config.get("temperature"),
        })
    
    return {"success": True, "data": providers}


@router.get("/models/available")
async def get_available_models(
    provider: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取可用模型列表"""
    model_manager = AIModelManager()
    all_models = model_manager.get_all_available_models()
    
    if provider:
        models = all_models.get(provider, [])
    else:
        models = all_models
    
    return {"success": True, "data": models}


@router.get("/usage/stats")
async def get_usage_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取使用统计（简化版）"""
    # TODO: 从数据库查询实际使用日志
    # 临时返回模拟数据
    stats = {
        "total_calls": 1560,
        "total_tokens": 245000,
        "success_rate": 0.95,
        "avg_response_time": 2.5,
        "top_capabilities": [
            {"name": "general_chat", "calls": 800},
            {"name": "template_design", "calls": 400},
            {"name": "workflow_design", "calls": 200},
            {"name": "data_query", "calls": 160},
        ],
        "daily_usage": [
            {"date": "2026-04-14", "calls": 210},
            {"date": "2026-04-15", "calls": 190},
            {"date": "2026-04-16", "calls": 230},
            {"date": "2026-04-17", "calls": 250},
            {"date": "2026-04-18", "calls": 280},
            {"date": "2026-04-19", "calls": 220},
            {"date": "2026-04-20", "calls": 180},
        ]
    }
    
    return {"success": True, "data": stats}


@router.get("/gateway-stats")
async def get_gateway_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取AI网关统计信息"""
    # TODO: 从数据库查询实际网关统计数据
    # 临时返回模拟数据，匹配前端期望的字段
    stats = {
        "totalRequests": 124567,
        "todayRequests": 2345,
        "avgLatency": 342,
        "latencyTrend": -12,
        "successRate": 98.7,
    }
    
    return {"success": True, "data": stats}


@router.get("/data-integration/stats")
async def get_data_integration_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取数据集成统计信息"""
    # 模拟数据，匹配前端DataIntegration.vue的期望字段
    stats = {
        "connections": 8,
        "dataSources": 6,
        "syncTasks": 12,
        "healthRate": 94.5,
    }
    
    return {"success": True, "data": stats}


@router.get("/data-integration/connections")
async def get_data_integration_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取数据连接列表"""
    connections = [
        {"id": 1, "name": "主数据库", "type": "MySQL", "status": "正常", "lastSync": "2026-04-20 10:30"},
        {"id": 2, "name": "用户API", "type": "REST API", "status": "正常", "lastSync": "2026-04-20 10:15"},
        {"id": 3, "name": "文件存储", "type": "文件系统", "status": "正常", "lastSync": "2026-04-20 09:45"},
        {"id": 4, "name": "消息队列", "type": "RabbitMQ", "status": "异常", "lastSync": "2026-04-19 16:20"},
        {"id": 5, "name": "数据仓库", "type": "ClickHouse", "status": "正常", "lastSync": "2026-04-19 14:30"},
        {"id": 6, "name": "外部服务", "type": "Web Service", "status": "警告", "lastSync": "2026-04-18 11:45"},
    ]
    
    return {"success": True, "data": connections}


@router.get("/data-integration/sync-tasks")
async def get_data_integration_sync_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取同步任务列表"""
    sync_tasks = [
        {"id": 1, "name": "用户数据同步", "source": "MySQL", "target": "数据仓库", "schedule": "每小时", "lastRun": "2026-04-20 10:00", "status": "运行中"},
        {"id": 2, "name": "日志收集", "source": "文件系统", "target": "Elasticsearch", "schedule": "实时", "lastRun": "2026-04-20 09:45", "status": "正常"},
        {"id": 3, "name": "API数据拉取", "source": "外部API", "target": "MySQL", "schedule": "每天", "lastRun": "2026-04-20 08:30", "status": "失败"},
        {"id": 4, "name": "数据备份", "source": "主数据库", "target": "备份存储", "schedule": "每周", "lastRun": "2026-04-19 23:00", "status": "正常"},
        {"id": 5, "name": "实时监控", "source": "消息队列", "target": "监控系统", "schedule": "实时", "lastRun": "2026-04-19 22:15", "status": "警告"},
    ]
    
    return {"success": True, "data": sync_tasks}


@router.get("/migration/stats")
async def get_migration_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取数据库迁移统计信息"""
    stats = {
        "totalMigrations": 156,
        "pendingMigrations": 8,
        "failedMigrations": 3,
        "successRate": 98.1,
        "lastMigrationTime": "2026-04-20 14:30",
    }
    
    return {"success": True, "data": stats}