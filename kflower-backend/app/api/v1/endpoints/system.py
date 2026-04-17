"""
API路由 - 系统配置
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.ai import SystemConfig as SystemConfigModel
from app.schemas.schemas import BaseResponse, SystemConfigUpdate
from app.core.ai_digital_base.local_services import embedding_service, get_embedding_service
from app.core.config import settings

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/config", response_model=BaseResponse)
async def get_system_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统配置"""
    result = await db.execute(
        select(SystemConfigModel).where(SystemConfigModel.organization_id == None)
    )
    configs = result.scalars().all()
    
    config_dict = {}
    for cfg in configs:
        try:
            if cfg.value_type == "json":
                config_dict[cfg.key] = json.loads(cfg.value) if cfg.value else None
            elif cfg.value_type == "boolean":
                config_dict[cfg.key] = cfg.value.lower() in ("true", "1", "yes") if cfg.value else False
            elif cfg.value_type == "number":
                config_dict[cfg.key] = float(cfg.value) if cfg.value else 0
            else:
                config_dict[cfg.key] = cfg.value
        except:
            config_dict[cfg.key] = cfg.value
    
    # 补充默认值
    defaults = {
        "app_name": "Kflower 企业智能管理低代码平台",
        "ai_provider": "siliconflow",
        "ai_model": "Qwen/Qwen3.5-35B-A3B",
        "ai_api_key": "",
        "theme": "light",
    }
    for k, v in defaults.items():
        if k not in config_dict:
            config_dict[k] = v
    
    return BaseResponse(data=config_dict)


@router.get("/models", response_model=BaseResponse)
async def get_available_models(
    current_user: User = Depends(get_current_user)
):
    """获取可用的AI模型列表"""
    return BaseResponse(data={
        "models": settings.AVAILABLE_MODELS,
        "current_provider": settings.AI_PROVIDER,
        "current_model": settings.SILICONFLOW_MODEL if settings.AI_PROVIDER == "siliconflow" else settings.OLLAMA_MODEL
    })


@router.put("/config/{key}", response_model=BaseResponse)
async def update_system_config(
    key: str,
    request: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新系统配置项"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    result = await db.execute(
        select(SystemConfigModel).where(
            SystemConfigModel.key == key,
            SystemConfigModel.organization_id == None
        )
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = request.value
        if request.description:
            config.description = request.description
    else:
        config = SystemConfigModel(
            key=key,
            value=request.value,
            description=request.description or "",
            organization_id=None
        )
        db.add(config)
    
    await db.commit()
    return BaseResponse(message=f"配置项 {key} 已更新")


@router.post("/config", response_model=BaseResponse)
async def save_system_config(
    configs: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量保存系统配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    import json
    
    for key, value in configs.items():
        value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        value_type = "json" if isinstance(value, (dict, list)) else "string"
        
        result = await db.execute(
            select(SystemConfigModel).where(
                SystemConfigModel.key == key,
                SystemConfigModel.organization_id == None
            )
        )
        config = result.scalar_one_or_none()
        
        if config:
            config.value = value_str
            config.value_type = value_type
        else:
            config = SystemConfigModel(
                key=key,
                value=value_str,
                value_type=value_type,
                organization_id=None
            )
            db.add(config)
    
    await db.commit()
    
    # 刷新 AI Gateway 配置
    from app.core.ai_digital_base.gateway import ai_gateway
    ai_gateway._config_loaded = False  # 强制下次重新加载
    
    return BaseResponse(message="配置已保存")


@router.post("/test-ai", response_model=BaseResponse)
async def test_ai_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 AI 连接"""
    from app.core.ai_digital_base.gateway import ai_gateway
    
    # 加载最新配置
    await ai_gateway.load_config_from_db(db)
    
    # 测试简单对话
    try:
        result = await ai_gateway.chat([
            {"role": "user", "content": "Hello, this is a test. Please respond with 'OK'."}
        ], max_tokens=50)
        
        if "error" in result:
            return BaseResponse(success=False, message=result["error"])
        
        return BaseResponse(
            success=True, 
            message="AI 连接测试成功",
            data={
                "provider": ai_gateway.current_provider,
                "model": ai_gateway.providers.get(ai_gateway.current_provider, {}).get("model"),
                "response": result.get("content", "")[:100]
            }
        )
    except Exception as e:
        return BaseResponse(success=False, message=f"AI 连接测试失败: {str(e)}")


@router.get("/ai-providers", response_model=BaseResponse)
async def list_ai_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出所有支持的 AI 提供商"""
    from app.core.ai_digital_base.model_manager import ai_model_manager
    
    providers = ai_model_manager.get_all_providers()
    
    return BaseResponse(data={
        "providers": providers
    })


@router.get("/ai-models/{provider}", response_model=BaseResponse)
async def list_ai_models(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """动态获取指定提供商的模型列表"""
    from app.core.ai_digital_base.model_manager import ai_model_manager
    from app.core.ai_digital_base.gateway import ai_gateway
    
    # 先加载配置
    await ai_gateway.load_config_from_db(db)
    
    # 获取该提供商的配置
    provider_config = ai_gateway.providers.get(provider, {})
    api_key = provider_config.get("api_key")
    base_url = provider_config.get("base_url")
    
    # 如果没有配置，返回默认模型列表
    if not api_key:
        default_models = ai_model_manager.get_default_models(provider)
        return BaseResponse(data={
            "provider": provider,
            "models": default_models,
            "from_api": False,
            "message": "使用预设模型列表（未配置API Key）"
        })
    
    # 从 API 获取模型列表
    result = await ai_model_manager.list_models_from_api(provider, api_key, base_url)
    
    if result["success"]:
        return BaseResponse(data={
            "provider": provider,
            "models": result["models"],
            "from_api": True,
            "count": result["count"]
        })
    else:
        # API 失败，返回默认列表
        return BaseResponse(data={
            "provider": provider,
            "models": result.get("fallback_models", []),
            "from_api": False,
            "error": result.get("error"),
            "message": "API获取失败，使用预设模型列表"
        })


@router.post("/ai-models/{provider}", response_model=BaseResponse)
async def fetch_ai_models_with_key(
    provider: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """使用指定的 API Key 获取模型列表（用于测试连接）"""
    from app.core.ai_digital_base.model_manager import ai_model_manager
    
    api_key = request.get("api_key") or ""
    base_url = request.get("base_url")
    
    # Ollama 等本地服务不需要 API Key
    is_local = provider in ("ollama",)
    if not api_key and not is_local:
        return BaseResponse(success=False, message="请提供 API Key")
    
    result = await ai_model_manager.list_models_from_api(provider, api_key, base_url)
    
    if result["success"]:
        return BaseResponse(data={
            "provider": provider,
            "models": result["models"],
            "from_api": True,
            "count": result["count"]
        })
    else:
        return BaseResponse(
            success=False, 
            message=f"获取模型列表失败: {result.get('error')}",
            data={"fallback_models": result.get("fallback_models", [])}
        )


@router.get("/embedding-models", response_model=BaseResponse)
async def list_embedding_models(
    current_user: User = Depends(get_current_user)
):
    """获取所有支持的嵌入模型列表"""
    from app.core.ai_digital_base.local_services import EmbeddingService, ST_AVAILABLE

    models = EmbeddingService.get_supported_models()

    # 构建返回数据，标记本地模型是否可用
    model_list = []
    for name, info in models.items():
        model_item = {
            "name": name,
            "provider": info["provider"],
            "dimension": info["dimension"],
            "description": info["description"],
            "available": True if info["provider"] == "api" else ST_AVAILABLE
        }
        model_list.append(model_item)

    return BaseResponse(data={
        "models": model_list,
        "st_available": ST_AVAILABLE,
        "current_model": get_embedding_service().embedding_model if hasattr(get_embedding_service(), 'embedding_model') else None,
        "current_provider": get_embedding_service().embedding_provider if hasattr(get_embedding_service(), 'embedding_provider') else None,
    })


@router.get("/health", response_model=BaseResponse)
async def health_check():
    """系统健康检查"""
    import platform
    import psutil
    
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('D:' if platform.system() == 'Windows' else '/')
    
    return BaseResponse(data={
        "status": "healthy",
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "disk_percent": disk.percent,
        "platform": platform.system(),
    })
