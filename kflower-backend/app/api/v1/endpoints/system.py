"""
API路由 - 系统配置
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
import json
import os
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.ai import SystemConfig as SystemConfigModel
from app.schemas.schemas import BaseResponse, SystemConfigUpdate
from app.core.ai_digital_base.local_services import embedding_service, get_embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    from app.core.ai_digital_base.gateway import ai_gateway
    
    # 先加载配置
    await ai_gateway.load_config_from_db(db)
    
    providers = ai_model_manager.get_all_providers()
    
    # 添加动态 Ollama 连接作为独立提供商
    ollama_connections = ai_gateway.list_ollama_connections()
    for conn in ollama_connections:
        providers.append({
            "id": conn["id"],
            "name": f"Ollama - {conn['name']}",
            "description": f"本地 Ollama ({conn['url']})",
            "default_base_url": conn["url"],
            "no_api_key": True,
            "is_dynamic_connection": True,
        })
    
    return BaseResponse(data={
        "providers": providers
    })


@router.get("/ollama-connections", response_model=BaseResponse)
async def list_ollama_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有配置的 Ollama 连接"""
    from app.core.ai_digital_base.gateway import ai_gateway
    
    await ai_gateway.load_config_from_db(db)
    connections = ai_gateway.list_ollama_connections()
    
    return BaseResponse(data={
        "connections": connections
    })


@router.post("/ollama-connections/test", response_model=BaseResponse)
async def test_ollama_connection(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """测试 Ollama 连接"""
    url = request.get("url", "http://localhost:11434")
    timeout = request.get("timeout", 5)
    
    try:
        import httpx
        import asyncio
        
        async def check_connection():
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(f"{url.rstrip('/')}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return True, models
                return False, []
        
        is_connected, models = asyncio.run(check_connection())
        
        if is_connected:
            return BaseResponse(
                success=True,
                message=f"连接成功，发现 {len(models)} 个模型",
                data={"connected": True, "models": models}
            )
        else:
            return BaseResponse(success=False, message="连接失败，请检查 Ollama 服务是否启动")
    except Exception as e:
        return BaseResponse(success=False, message=f"连接失败: {str(e)}")


@router.get("/rerank-models", response_model=BaseResponse)
async def list_rerank_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有可用的 Rerank 模型（包括系统配置的模型）"""
    from app.core.ai_digital_base.local_services import ST_AVAILABLE
    
    # 系统预设的 Rerank 模型
    preset_models = [
        {"id": "BAAI/bge-reranker-v2-m3", "name": "BGE Reranker v2 m3", "provider": "local", "description": "多语言重排模型，精度高"},
        {"id": "BAAI/bge-reranker-large", "name": "BGE Reranker Large", "provider": "local", "description": "大型重排模型（需要下载）"},
        {"id": "BAAI/bge-reranker-base", "name": "BGE Reranker Base", "provider": "local", "description": "基础重排模型"},
        {"id": "cohere/rerank-english-v3.0", "name": "Cohere Rerank English", "provider": "api", "description": "英文重排，Cohere API"},
        {"id": "cohere/rerank-multilingual-v3.0", "name": "Cohere Rerank Multilingual", "provider": "api", "description": "多语言重排，Cohere API"},
    ]
    
    # 从数据库加载自定义的 Rerank 模型
    custom_models = []
    try:
        result = await db.execute(
            select(SystemConfigModel).where(
                SystemConfigModel.key == "rerank_models",
                SystemConfigModel.organization_id == None
            )
        )
        config = result.scalar_one_or_none()
        if config and config.value:
            custom = json.loads(config.value) if isinstance(config.value, str) else config.value
            for m in (custom if isinstance(custom, list) else []):
                if isinstance(m, dict):
                    custom_models.append({
                        "id": m.get("model") or m.get("name"),
                        "name": m.get("name") or m.get("model"),
                        "provider": m.get("provider", "api"),
                        "description": f"自定义模型，API: {m.get('apiUrl', 'N/A')}",
                        "is_custom": True,
                    })
    except Exception as e:
        logger.warning(f"加载自定义 rerank 模型失败: {e}")
    
    # 检查本地模型是否可用
    st_available = ST_AVAILABLE
    
    return BaseResponse(data={
        "models": preset_models + custom_models,
        "st_available": st_available,
        "st_model_path": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bge-reranker-v2-m3") if st_available else None,
    })


@router.post("/rerank-models/test", response_model=BaseResponse)
async def test_rerank_model(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """测试 Rerank 模型"""
    model_id = request.get("model_id")
    
    if not model_id:
        return BaseResponse(success=False, message="请指定模型ID")
    
    try:
        from sentence_transformers import CrossEncoder
        import os
        
        # 确定模型路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        local_path = os.path.join(project_root, "bge-reranker-v2-m3")
        
        # 检查是否使用本地模型
        if "bge-reranker-v2-m3" in model_id and os.path.exists(local_path):
            model_path = local_path
        else:
            model_path = model_id
        
        # 尝试加载模型
        logger.info(f"测试加载 Rerank 模型: {model_path}")
        ce = CrossEncoder(model_path, max_length=512)
        
        # 执行简单测试
        pairs = [("什么是人工智能？", "人工智能是研究如何让机器像人类一样思考和学习的科学。")]
        scores = ce.predict(pairs)
        
        return BaseResponse(
            success=True,
            message=f"模型 {model_id} 测试成功",
            data={"model": model_id, "test_score": float(scores[0])}
        )
    except ImportError:
        return BaseResponse(success=False, message="sentence-transformers 未安装，无法测试本地 Rerank 模型")
    except Exception as e:
        return BaseResponse(success=False, message=f"测试失败: {str(e)}")


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
    
    # 如果是 Ollama，检查是否有动态连接的 Ollama
    if provider == "ollama":
        ollama_connections = ai_gateway.list_ollama_connections()
        if ollama_connections:
            # 返回第一个连接的配置作为默认
            first_conn = ollama_connections[0]
            api_key = "ollama"
            base_url = first_conn.get("url", "http://localhost:11434")
    
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
    """获取所有支持的嵌入模型列表（包括内置和自定义）"""
    from app.core.ai_digital_base.local_services import EmbeddingService, ST_AVAILABLE

    # 获取所有模型（内置 + 自定义）
    all_models = get_embedding_service().get_all_models()

    return BaseResponse(data={
        "models": all_models,
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
