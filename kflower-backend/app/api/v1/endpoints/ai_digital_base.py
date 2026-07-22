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
    configured_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取可用模型列表（默认只返回已配置提供商的模型）"""
    await ai_gateway.load_config_from_db(db)
    
    model_manager = AIModelManager()
    
    if configured_only:
        # 只返回已配置提供商的模型
        configured_providers = []
        for name, config in ai_gateway.providers.items():
            # 有 API Key 或本地服务（不需要 API Key）的认为是已配置
            is_local = name.startswith("ollama")
            if config.get("api_key") or is_local:
                configured_providers.append(name)
        
        # 获取这些提供商的模型
        all_models = model_manager.get_all_available_models()
        if provider:
            models = {provider: all_models.get(provider, [])} if provider in configured_providers else {}
        else:
            models = {k: v for k, v in all_models.items() if k in configured_providers}
    else:
        # 返回所有预设模型
        all_models = model_manager.get_all_available_models()
        if provider:
            models = {provider: all_models.get(provider, [])}
        else:
            models = all_models
    
    return {"success": True, "data": models}


# ===== Phase 1 清理：以下 6 个纯 mock 端点已移除 =====
# usage/stats, gateway-stats, data-integration/stats,
# data-integration/connections, data-integration/sync-tasks, migration/stats
# 原因：返回硬编码假数据，误导用户
# 后续如需实现请基于数据库真实查询重新开发