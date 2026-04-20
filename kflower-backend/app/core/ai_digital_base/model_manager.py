"""
AI模型管理 - 动态获取模型列表，支持多模型配置
"""
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from app.core.config import settings
import json


class AIModelManager:
    """
    AI模型管理器 - 支持动态模型列表、多模型配置、完整参数
    """

    # 各服务商的默认基础URL
    PROVIDER_BASE_URLS = {
        "siliconflow": "https://api.siliconflow.cn/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai": "https://api.openai.com/v1",
        "moonshot": "https://api.moonshot.cn/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
        "baidu": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "minimax": "https://api.minimax.chat/v1",
        "ollama": "http://localhost:11434/v1",
    }

    # 默认模型参数配置
    DEFAULT_MODEL_PARAMS = {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.95,
        "top_k": 50,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 120,
        "stream": False,
    }

    # 预设的推荐模型（当API不可用时显示）
    DEFAULT_MODELS = {
        "siliconflow": [
            {"id": "Qwen/Qwen3-32B", "name": "Qwen3-32B", "type": "chat", "context": 32768, "recommended": True},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen2.5-72B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-32B-Instruct", "name": "Qwen2.5-32B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-14B-Instruct", "name": "Qwen2.5-14B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-7B-Instruct", "name": "Qwen2.5-7B-Instruct", "type": "chat", "context": 32768},
            {"id": "deepseek-ai/DeepSeek-V3", "name": "DeepSeek-V3", "type": "chat", "context": 64000, "recommended": True},
            {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek-R1 (推理)", "type": "chat", "context": 64000},
            {"id": "THUDM/glm-4-9b-chat", "name": "GLM-4-9B", "type": "chat", "context": 131072},
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "name": "Llama-3.3-70B", "type": "chat", "context": 131072},
        ],
        "deepseek": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "type": "chat", "context": 64000, "recommended": True},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "type": "chat", "context": 64000},
        ],
        "qwen": [
            {"id": "qwen-max", "name": "Qwen Max", "type": "chat", "context": 32768, "recommended": True},
            {"id": "qwen-plus", "name": "Qwen Plus", "type": "chat", "context": 131072},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "type": "chat", "context": 131072},
            {"id": "qwen-long", "name": "Qwen Long", "type": "chat", "context": 1000000},
        ],
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o", "type": "chat", "context": 128000, "recommended": True},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "type": "chat", "context": 128000},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "type": "chat", "context": 128000},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat", "context": 16385},
        ],
        "moonshot": [
            {"id": "moonshot-v1-8k", "name": "Moonshot V1 8K", "type": "chat", "context": 8192},
            {"id": "moonshot-v1-32k", "name": "Moonshot V1 32K", "type": "chat", "context": 32768},
            {"id": "moonshot-v1-128k", "name": "Moonshot V1 128K", "type": "chat", "context": 131072},
        ],
        "zhipu": [
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "type": "chat", "context": 131072, "recommended": True},
            {"id": "glm-4-0520", "name": "GLM-4 0520", "type": "chat", "context": 131072},
            {"id": "glm-4-air", "name": "GLM-4 Air", "type": "chat", "context": 131072},
        ],
        "ollama": [
            {"id": "qwen2.5:7b", "name": "Qwen2.5 7B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "qwen2.5:14b", "name": "Qwen2.5 14B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "llama3:8b", "name": "Llama3 8B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "deepseek-r1:7b", "name": "DeepSeek-R1 7B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "glm4:9b", "name": "GLM4 9B (本地)", "type": "chat", "context": 4096, "local": True},
        ],
    }
    
    def __init__(self):
        self._cached_models: Dict[str, List[Dict]] = {}
        self._cache_time: Dict[str, float] = {}
        self._cache_ttl = 3600  # 1小时缓存
    
    async def list_models_from_api(self, provider: str, api_key: str, base_url: str = None) -> Dict[str, Any]:
        """
        从 API 动态获取模型列表
        """
        import time
        
        # 检查缓存
        cache_key = f"{provider}:{api_key[:10]}"
        if cache_key in self._cached_models and time.time() - self._cache_time.get(cache_key, 0) < self._cache_ttl:
            return {"success": True, "models": self._cached_models[cache_key], "cached": True}
        
        base_url = base_url or self.PROVIDER_BASE_URLS.get(provider)
        # Ollama 等本地服务不需要 API Key，使用占位值
        is_local = provider in ("ollama",)
        if not api_key:
            if is_local:
                api_key = "ollama"  # 本地服务使用占位 API Key
            else:
                return {
                    "success": False, 
                    "error": "缺少 API Key",
                    "fallback_models": self.DEFAULT_MODELS.get(provider, [])
                }
        if not base_url:
            return {
                "success": False, 
                "error": "缺少 Base URL",
                "fallback_models": self.DEFAULT_MODELS.get(provider, [])
            }
        
        try:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            models_response = await client.models.list()
            
            models = []
            for model in models_response.data:
                models.append({
                    "id": model.id,
                    "name": model.id,  # 大多数API只返回ID
                    "type": "chat",
                    "context": 4096,  # 默认值
                    "created": getattr(model, 'created', None),
                    "owned_by": getattr(model, 'owned_by', 'unknown'),
                })
            
            # 按名称排序
            models.sort(key=lambda x: x["id"])
            
            # 缓存结果
            self._cached_models[cache_key] = models
            self._cache_time[cache_key] = time.time()
            
            return {"success": True, "models": models, "count": len(models)}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_models": self.DEFAULT_MODELS.get(provider, [])
            }
    
    def get_default_models(self, provider: str) -> List[Dict]:
        """获取预设的默认模型列表"""
        return self.DEFAULT_MODELS.get(provider, [])
    
    def get_all_providers(self) -> List[Dict]:
        """获取所有支持的提供商"""
        return [
            {"id": "siliconflow", "name": "SiliconFlow", "description": "国产大模型聚合平台", "default_base_url": self.PROVIDER_BASE_URLS["siliconflow"]},
            {"id": "deepseek", "name": "DeepSeek", "description": "深度求索", "default_base_url": self.PROVIDER_BASE_URLS["deepseek"]},
            {"id": "qwen", "name": "通义千问", "description": "阿里云大模型", "default_base_url": self.PROVIDER_BASE_URLS["qwen"]},
            {"id": "openai", "name": "OpenAI", "description": "GPT系列", "default_base_url": self.PROVIDER_BASE_URLS["openai"]},
            {"id": "moonshot", "name": "Moonshot", "description": "月之暗面 Kimi", "default_base_url": self.PROVIDER_BASE_URLS["moonshot"]},
            {"id": "zhipu", "name": "智谱AI", "description": "GLM系列", "default_base_url": self.PROVIDER_BASE_URLS["zhipu"]},
            {"id": "baidu", "name": "百度文心", "description": "文心一言", "default_base_url": self.PROVIDER_BASE_URLS["baidu"]},
            {"id": "minimax", "name": "MiniMax", "description": "海螺AI", "default_base_url": self.PROVIDER_BASE_URLS["minimax"]},
            {"id": "ollama", "name": "Ollama", "description": "本地大模型服务", "default_base_url": self.PROVIDER_BASE_URLS["ollama"], "no_api_key": True},
            {"id": "custom", "name": "自定义", "description": "自定义OpenAI兼容API", "default_base_url": ""},
        ]

    def get_all_available_models(self) -> Dict[str, List[Dict]]:
        """获取所有可用模型（默认预设）"""
        return self.DEFAULT_MODELS


# 全局模型管理器实例
ai_model_manager = AIModelManager()
