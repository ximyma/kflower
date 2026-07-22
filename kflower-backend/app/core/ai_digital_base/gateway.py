"""
AI数字底座 - AI网关模块
统一的AI模型调用入口，支持多模型切换和动态配置
"""
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import httpx
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class AIGateway:
    """
    AI网关 - 统一的大模型调用接口
    支持：DeepSeek、通义千问、SiliconFlow等
    支持从数据库动态读取配置
    """
    
    def __init__(self):
        # 默认配置（从环境变量）
        self.providers: Dict[str, Dict] = {
            "deepseek": {
                "api_key": settings.DEEPSEEK_API_KEY,
                "base_url": settings.DEEPSEEK_API_BASE,
                "model": settings.DEEPSEEK_MODEL,
            },
            "qwen": {
                "api_key": settings.QWEN_API_KEY,
                "base_url": settings.QWEN_API_BASE,
                "model": settings.QWEN_MODEL,
            },
            "siliconflow": {
                "api_key": settings.SILICONFLOW_API_KEY,
                "base_url": settings.SILICONFLOW_API_BASE,
                "model": settings.SILICONFLOW_MODEL,
            },
            "ollama": {
                "api_key": settings.OLLAMA_API_KEY,
                "base_url": settings.OLLAMA_API_BASE,
                "model": settings.OLLAMA_MODEL,
            },
        }
        self.current_provider = settings.AI_PROVIDER
        self._clients: Dict[str, AsyncOpenAI] = {}
        
        # 动态配置缓存
        self._dynamic_config: Dict[str, Any] = {}
        self._config_loaded = False
    
    async def load_config_from_db(self, db=None, force=False):
        """从数据库加载动态配置"""
        if self._config_loaded and not force:
            return
            
        try:
            if db is None:
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    await self._load_config_from_session(session)
            else:
                await self._load_config_from_session(db)
        except Exception as e:
            print(f"加载AI配置失败: {e}")
    
    async def _load_config_from_session(self, session):
        """从数据库会话加载配置"""
        from sqlalchemy import select
        from app.models.ai import SystemConfig
        
        result = await session.execute(
            select(SystemConfig).where(SystemConfig.organization_id == None)
        )
        configs = result.scalars().all()
        
        for cfg in configs:
            if cfg.key == "ai_provider":
                self.current_provider = cfg.value or self.current_provider
            elif cfg.key == "ai_api_key":
                # 更新当前 provider 的 API key
                if self.current_provider in self.providers:
                    self.providers[self.current_provider]["api_key"] = cfg.value
                else:
                    # 动态添加 provider
                    self.providers[self.current_provider] = {
                        "api_key": cfg.value,
                        "base_url": self._get_default_base_url(self.current_provider),
                        "model": None,
                    }
            elif cfg.key == "ai_model":
                # 更新当前 provider 的模型
                if self.current_provider in self.providers:
                    self.providers[self.current_provider]["model"] = cfg.value
            elif cfg.key == "ai_base_url":
                # 更新当前 provider 的 Base URL
                if self.current_provider in self.providers:
                    self.providers[self.current_provider]["base_url"] = cfg.value
                else:
                    self.providers[self.current_provider] = {
                        "api_key": None,
                        "base_url": cfg.value or self._get_default_base_url(self.current_provider),
                        "model": None,
                    }
        
        # 加载多模型配置（ai_models）
        for cfg in configs:
            if cfg.key == "ai_models":
                try:
                    models_list = json.loads(cfg.value) if cfg.value else []
                    for m in models_list:
                        p = m.get("provider")
                        if p:
                            # 构建完整的配置对象
                            base_url = m.get("baseUrl") or self._get_default_base_url(p)
                            api_key = m.get("apiKey") or ""
                            model_id = m.get("modelId") or ""
                            
                            # 获取参数配置
                            params = m.get("params") or {}
                            
                            # 创建完整配置
                            full_config = {
                                "api_key": api_key,
                                "base_url": base_url,
                                "model": model_id,
                                "timeout": params.get("timeout", 120) or m.get("timeout") or 120,
                                "temperature": params.get("temperature", 0.7) or 0.7,
                                "topP": params.get("topP", 0.95) or 0.95,
                                "maxTokens": params.get("maxTokens", 4096) or 4096,
                                "frequencyPenalty": params.get("frequencyPenalty", 0.0) or 0.0,
                                "presencePenalty": params.get("presencePenalty", 0.0) or 0.0,
                            }
                            
                            # 同时保存到 providers 和 _dynamic_config
                            self.providers[p] = full_config.copy()
                            self._dynamic_config[p] = full_config
                            
                            logger.info(f"Loaded model config: provider={p}, model={model_id}, base_url={base_url}")
                except Exception as e:
                    logger.error(f"Failed to load ai_models: {e}")
        
        # 加载 Ollama 本地连接配置（动态添加多个 Ollama 连接）
        for cfg in configs:
            if cfg.key == "local_ollama_connections":
                try:
                    connections = json.loads(cfg.value) if cfg.value else []
                    for conn in connections:
                        if conn.get("enabled", True) and conn.get("url"):
                            conn_id = f"ollama_{conn.get('id', conn.get('name', 'local'))}"
                            base_url = conn.get("url", "")
                            api_path = conn.get("apiPath", "/v1")
                            # 组合完整 URL
                            full_url = f"{base_url.rstrip('/')}{api_path}"
                            default_model = conn.get("defaultModel", "")
                            
                            self.providers[conn_id] = {
                                "api_key": "ollama",  # 占位值
                                "base_url": full_url,
                                "model": default_model,
                                "timeout": conn.get("timeout", 300),
                                "temperature": 0.7,
                                "topP": 0.95,
                                "maxTokens": 4096,
                                "frequencyPenalty": 0.0,
                                "presencePenalty": 0.0,
                                "description": conn.get("name", "Ollama 连接"),
                                "_is_ollama_connection": True,  # 标记为动态 Ollama 连接
                                "_original_url": base_url,
                            }
                            logger.info(f"Loaded Ollama connection: {conn_id}, url={full_url}, default_model={default_model}")
                except Exception as e:
                    logger.error(f"Failed to load local_ollama_connections: {e}")
        
        # 加载模块 AI 设置
        for cfg in configs:
            if cfg.key == "module_ai_settings":
                try:
                    module_settings = json.loads(cfg.value) if cfg.value else {}
                    self._dynamic_config["_module_settings"] = module_settings
                    logger.info(f"Loaded module AI settings: {list(module_settings.keys())}")
                except Exception as e:
                    logger.error(f"Failed to load module_ai_settings: {e}")
        
        # 清除客户端缓存，强制重新创建
        self._clients.clear()
        self._config_loaded = True
    
    def update_provider_config(self, provider: str, api_key: str = None, model: str = None):
        """动态更新提供商配置"""
        if provider not in self.providers:
            self.providers[provider] = {
                "api_key": None,
                "base_url": self._get_default_base_url(provider),
                "model": None,
            }
        
        if api_key is not None:
            self.providers[provider]["api_key"] = api_key
        if model is not None:
            self.providers[provider]["model"] = model
        
        # 清除该 provider 的客户端缓存
        if provider in self._clients:
            del self._clients[provider]
    
    def _get_default_base_url(self, provider: str) -> str:
        """获取默认 API Base URL（统一配置源：model_manager.PROVIDER_BASE_URLS）"""
        from app.core.ai_digital_base.model_manager import AIModelManager
        return AIModelManager.PROVIDER_BASE_URLS.get(provider, "")
    
    def set_current_provider(self, provider: str):
        """设置当前使用的提供商"""
        if provider in self.providers:
            self.current_provider = provider
    
    def _get_client(self, provider: str) -> Optional[AsyncOpenAI]:
        """获取指定 provider 的客户端"""
        if provider not in self._clients:
            # 优先从 _dynamic_config 获取（用户配置的模型），再从 providers 获取
            config = self._dynamic_config.get(provider) or self.providers.get(provider)
            if not config:
                return None
            # Ollama 等本地服务不需要 API Key，使用占位值
            api_key = config.get("api_key")
            if not api_key:
                if provider == "ollama":
                    api_key = "ollama"  # 占位值
                else:
                    return None
            # 使用较长的超时时间，因为 AI 生成可能需要更久（默认5分钟）
            user_timeout = config.get("timeout", 300)
            api_timeout = httpx.Timeout(float(user_timeout), connect=30.0)
            self._clients[provider] = AsyncOpenAI(
                api_key=api_key,
                base_url=config.get("base_url") or self._get_default_base_url(provider),
                timeout=api_timeout,
            )
        return self._clients[provider]
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None,
        frequency_penalty: float = None,
        presence_penalty: float = None,
        timeout: int = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        统一的聊天接口
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            provider: AI提供商
            model: 指定模型
            temperature: 温度（0-2，越高越有创造性）
            max_tokens: 最大输出token数
            top_p: Nucleus采样（0-1）
            frequency_penalty: 频率惩罚（-2到2）
            presence_penalty: 存在惩罚（-2到2）
            timeout: 请求超时秒数
            stream: 是否流式输出
            
        Returns:
            包含响应内容的字典
        """
        # 如果指定了模型，需要找到对应的 provider
        if model and not provider:
            for p_name, p_cfg in self.providers.items():
                if p_cfg.get("model") == model:
                    provider = p_name
                    break
            # 如果还没找到，尝试通过 model 查找（可能 provider key 不同）
            if not provider:
                for p_name, p_cfg in self._dynamic_config.items():
                    if p_cfg.get("model") == model:
                        provider = p_name
                        break
        
        provider = provider or self.current_provider
        # 优先从 _dynamic_config 获取（用户配置的模型），再从 providers 获取（默认配置）
        p_config = self._dynamic_config.get(provider) or self.providers.get(provider, {})
        
        # 从provider配置中获取默认值
        if temperature is None:
            temperature = p_config.get("temperature", 0.7)
        if max_tokens is None:
            max_tokens = p_config.get("maxTokens", 4096)
        if top_p is None:
            top_p = p_config.get("topP", 0.95)
        if frequency_penalty is None:
            frequency_penalty = p_config.get("frequencyPenalty", 0.0)
        if presence_penalty is None:
            presence_penalty = p_config.get("presencePenalty", 0.0)
        if timeout is None:
            timeout = p_config.get("timeout", 120)
        
        client = self._get_client(provider)
        
        if not client:
            return {"error": f"Provider {provider} not configured or missing API key. Please configure API Key in Settings -> AI Configuration."}
        
        # 选择模型
        if model is None:
            model = p_config.get("model", "gpt-3.5-turbo")
        
        # 处理额外参数
        extra_params = p_config.get("extraParams", "")
        if extra_params and isinstance(extra_params, str):
            try:
                kwargs.update(json.loads(extra_params))
            except:
                pass
        
        try:
            # 构建请求参数 - 只使用 OpenAI 标准 API 参数
            request_params = {
                "model": model,
                "messages": messages,
                "stream": stream,
            }
            
            # temperature 参数
            if temperature is not None:
                request_params["temperature"] = temperature
            
            # max_tokens 参数 - 大多数 API 支持
            if max_tokens is not None:
                request_params["max_tokens"] = max_tokens
            
            # top_p 参数
            if top_p and top_p != 0.95:
                request_params["top_p"] = top_p
            
            # frequency_penalty 参数
            if frequency_penalty and frequency_penalty != 0.0:
                request_params["frequency_penalty"] = frequency_penalty
            
            # presence_penalty 参数
            if presence_penalty and presence_penalty != 0.0:
                request_params["presence_penalty"] = presence_penalty
            
            # 合并额外参数，但严格过滤掉可能导致问题的参数
            # 只允许安全的 OpenAI API 参数通过
            safe_params = {
                "temperature", "max_tokens", "top_p", 
                "frequency_penalty", "presence_penalty",
                "seed", "response_format"
            }
            for k, v in kwargs.items():
                # 跳过不支持的参数
                if k.lower() in safe_params:
                    request_params[k] = v
            
            # 如果用户指定了更长的超时，重新创建客户端
            effective_timeout = timeout or 120
            current_client_timeout = getattr(client, '_timeout', None)
            if current_client_timeout and effective_timeout > 180:
                # 重新创建客户端以使用更长的超时
                config = self.providers.get(provider, {})
                api_timeout = httpx.Timeout(float(effective_timeout), connect=30.0)
                client = AsyncOpenAI(
                    api_key=client.api_key,
                    base_url=client.base_url,
                    timeout=api_timeout,
                )
            
            response = await client.chat.completions.create(**request_params)
            
            if stream:
                return {"stream": response}
            else:
                return {
                    "content": response.choices[0].message.content,
                    "model": model,
                    "provider": provider,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                }
        except Exception as e:
            error_msg = str(e)
            # 捕获 API 返回的错误响应
            if "Internal" in error_msg or "internal" in error_msg:
                return {"error": f"AI 服务内部错误，请稍后重试。如果问题持续存在，请检查 API 配置是否正确。"}
            if "401" in error_msg or "Invalid" in error_msg or "Authentication" in error_msg:
                return {"error": f"API Key 无效或已过期，请在「设置 -> AI配置」中检查配置。错误详情: {error_msg}"}
            elif "rate" in error_msg.lower() or "429" in error_msg:
                return {"error": f"API 调用频率超限，请稍后重试。错误详情: {error_msg}"}
            elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                return {"error": f"AI 服务响应超时，请稍后重试。"}
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                return {"error": f"网络连接错误，请检查网络后重试。错误详情: {error_msg}"}
            else:
                return {"error": f"AI 调用失败: {error_msg}"}
    
    async def chat_with_system_prompt(
        self,
        system_prompt: str,
        user_message: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """带系统提示词的对话"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return await self.chat(messages, provider, **kwargs)
    
    async def function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict],
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """函数调用接口"""
        provider = provider or self.current_provider
        
        try:
            response = await self.chat(
                messages=messages,
                provider=provider,
                tools=[{"type": "function", "function": f} for f in functions],
                tool_choice="auto",
                **kwargs
            )
            return response
        except Exception as e:
            return {"error": str(e)}
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """列出所有已配置的AI提供商"""
        return [
            {
                "name": name,
                "configured": bool(config.get("api_key")),
                "default_model": config.get("model"),
                "base_url": config.get("base_url"),
            }
            for name, config in self.providers.items()
        ]
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置信息"""
        provider_config = self.providers.get(self.current_provider, {})
        return {
            "provider": self.current_provider,
            "model": provider_config.get("model"),
            "configured": bool(provider_config.get("api_key")),
        }
    
    def get_module_model(self, module: str, default_model_id: str = None) -> Optional[str]:
        """
        获取指定模块的 AI 模型配置
        
        Args:
            module: 模块名，如 chatGeneral, chatTemplate, chatWorkflow 等
            default_model_id: 如果模块未配置，返回的默认模型ID
            
        Returns:
            模型ID 或 None
        """
        # 确保配置已加载
        if not self._config_loaded:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果在异步上下文中，创建task
                    pass
                else:
                    loop.run_until_complete(self.load_config_from_db())
            except:
                pass
        
        module_settings = self._dynamic_config.get("_module_settings", {})
        model_id = module_settings.get(module)
        
        if model_id:
            return model_id
        
        # 如果模块未配置，尝试查找默认模型
        if default_model_id:
            return default_model_id
        
        # 返回当前配置的模型
        return self.providers.get(self.current_provider, {}).get("model")
    
    def list_ollama_connections(self) -> List[Dict[str, Any]]:
        """列出所有已配置的 Ollama 连接"""
        connections = []
        for name, config in self.providers.items():
            if config.get("_is_ollama_connection"):
                connections.append({
                    "id": name,
                    "name": config.get("description", name),
                    "url": config.get("_original_url", config.get("base_url")),
                    "default_model": config.get("model"),
                    "status": "connected",  # TODO: 实际检测连接状态
                })
        return connections


# 全局AI网关实例
ai_gateway = AIGateway()
