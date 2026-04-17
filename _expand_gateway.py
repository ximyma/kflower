# -*- coding: utf-8 -*-
"""
Expand AI Gateway with full parameters and attachment support
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-backend\app\core\ai_digital_base\gateway.py'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find and replace the chat method signature and body
old_chat_sig = '''    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        统一的聊天接口
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            provider: AI提供商，默认使用配置的默认提供商
            model: 指定模型
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            包含响应内容的字典
        """'''

new_chat_sig = '''    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        top_k: int = 50,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        timeout: int = 120,
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
        """'''

if old_chat_sig in content:
    content = content.replace(old_chat_sig, new_chat_sig)
    print("Updated chat method signature")
else:
    print("Chat signature not found")

# Update the client creation to use timeout
old_client = '''            self._clients[provider] = AsyncOpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
            )'''

new_client = '''            self._clients[provider] = AsyncOpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"],
                timeout=httpx.Timeout(timeout, connect=30.0),
            )'''

if old_client in content:
    content = content.replace(old_client, new_client)
    print("Updated client with timeout")

# Update the chat.completions.create call to include all parameters
old_create = '''            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )'''

new_create = '''            # 构建请求参数
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
            
            response = await client.chat.completions.create(**request_params)'''

if old_create in content:
    content = content.replace(old_create, new_create)
    print("Updated create call with full parameters")
else:
    print("Create call not found")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Gateway expanded")
