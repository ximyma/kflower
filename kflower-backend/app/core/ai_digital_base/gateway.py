"""
AI数字底座 - AI网关模块
统一的AI模型调用入口，支持多模型切换和动态配置
"""
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import httpx
from app.core.config import settings
import json


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
    
    async def load_config_from_db(self, db=None):
        """从数据库加载动态配置"""
        if self._config_loaded:
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
                            if p not in self.providers:
                                self.providers[p] = {
                                    "api_key": m.get("apiKey"),
                                    "base_url": m.get("baseUrl") or self._get_default_base_url(p),
                                    "model": m.get("modelId"),
                                }
                            # 保存用户配置的所有参数
                            params = m.get("params") or {}
                            if params:
                                self.providers[p].update({
                                    "timeout": params.get("timeout", 120),
                                    "temperature": params.get("temperature", 0.7),
                                    "topP": params.get("topP", 0.9),
                                    "topK": params.get("topK", 40),
                                    "maxTokens": params.get("maxTokens", 8192),
                                    "contextWindow": params.get("contextWindow", 32768),
                                    "frequencyPenalty": params.get("frequencyPenalty", 0),
                                    "presencePenalty": params.get("presencePenalty", 0),
                                    "repeatPenalty": params.get("repeatPenalty", 1.1),
                                    "maxRetries": params.get("maxRetries", 3),
                                    "stream": params.get("stream", True),
                                    "extraParams": params.get("extraParams", ""),
                                })
                            # 也支持直接放在模型配置顶层
                            if m.get("timeout"):
                                self.providers[p]["timeout"] = m.get("timeout")
                except Exception:
                    pass
        
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
        """获取默认 API Base URL"""
        urls = {
            "deepseek": "https://api.deepseek.com/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "siliconflow": "https://api.siliconflow.cn/v1",
            "openai": "https://api.openai.com/v1",
            "moonshot": "https://api.moonshot.cn/v1",
            "zhipu": "https://open.bigmodel.cn/api/paas/v4",
            "baidu": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
            "minimax": "https://api.minimax.chat/v1",
            "ollama": "http://localhost:11434/v1",
        }
        return urls.get(provider, "")
    
    def set_current_provider(self, provider: str):
        """设置当前使用的提供商"""
        if provider in self.providers:
            self.current_provider = provider
    
    def _get_client(self, provider: str) -> Optional[AsyncOpenAI]:
        """获取指定 provider 的客户端"""
        if provider not in self._clients:
            config = self.providers.get(provider)
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
        top_k: int = None,
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
            top_k: Top-K采样
            frequency_penalty: 频率惩罚（-2到2）
            presence_penalty: 存在惩罚（-2到2）
            timeout: 请求超时秒数
            stream: 是否流式输出
            
        Returns:
            包含响应内容的字典
        """
        provider = provider or self.current_provider
        p_config = self.providers.get(provider, {})
        
        # 从provider配置中获取默认值
        if temperature is None:
            temperature = p_config.get("temperature", 0.7)
        if max_tokens is None:
            max_tokens = p_config.get("maxTokens", 4096)
        if top_p is None:
            top_p = p_config.get("topP", 0.95)
        if top_k is None:
            top_k = p_config.get("topK", 50)
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
            # 构建请求参数
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }
            # 添加可选参数
            if top_p and top_p != 0.95:
                request_params["top_p"] = top_p
            if top_k and top_k != 50:
                request_params["top_k"] = top_k
            if frequency_penalty and frequency_penalty != 0.0:
                request_params["frequency_penalty"] = frequency_penalty
            if presence_penalty and presence_penalty != 0.0:
                request_params["presence_penalty"] = presence_penalty
            # 合并额外参数
            request_params.update(kwargs)
            
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
            if "401" in error_msg or "Invalid" in error_msg:
                return {"error": f"API Key 无效或已过期，请在「设置 -> AI配置」中检查配置。错误详情: {error_msg}"}
            elif "rate" in error_msg.lower():
                return {"error": f"API 调用频率超限，请稍后重试。错误详情: {error_msg}"}
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


# 全局AI网关实例
ai_gateway = AIGateway()
