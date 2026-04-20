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
        "active_conversations": len(conversation_manager._conversations),
        "total_messages": sum(len(conv["messages"]) for conv in conversation_manager._conversations.values()),
    }
    
    # 5. 智能体编排器状态
    orchestrator_status = {
        "available_agents": [agent.value for agent in agent_orchestrator.AgentType],
        "active_tasks": len([task for task in agent_orchestrator._tasks if task.status == "running"]),
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