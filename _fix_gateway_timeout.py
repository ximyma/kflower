# -*- coding: utf-8 -*-
"""Fix gateway.py: use user-configured timeout, and re-create client when needed"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-backend\app\core\ai_digital_base\gateway.py'
with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
    content = f.read()

# Fix 1: _get_client should use longer timeout
old_client = """            # 使用较长的超时时间，因为 AI 生成可能需要更久
            api_timeout = httpx.Timeout(180.0, connect=30.0)
            self._clients[provider] = AsyncOpenAI(
                api_key=api_key,
                base_url=config.get("base_url") or self._get_default_base_url(provider),
                timeout=api_timeout,
            )"""

new_client = """            # 使用较长的超时时间，因为 AI 生成可能需要更久（默认5分钟）
            user_timeout = config.get("timeout", 300)
            api_timeout = httpx.Timeout(float(user_timeout), connect=30.0)
            self._clients[provider] = AsyncOpenAI(
                api_key=api_key,
                base_url=config.get("base_url") or self._get_default_base_url(provider),
                timeout=api_timeout,
            )"""

count1 = content.count(old_client)
print(f"_get_client timeout: found {count1}")
if count1 == 1:
    content = content.replace(old_client, new_client)
    print("  [OK] _get_client uses user timeout")

# Fix 2: chat method should pass timeout and re-create client if needed
old_chat_call = """            response = await client.chat.completions.create(**request_params)"""

new_chat_call = """            # 如果用户指定了更长的超时，重新创建客户端
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
            
            response = await client.chat.completions.create(**request_params)"""

count2 = content.count(old_chat_call)
print(f"chat.completions.create: found {count2}")
if count2 == 1:
    content = content.replace(old_chat_call, new_chat_call)
    print("  [OK] chat method respects user timeout")

with open(path, 'w', encoding='utf-8-sig', errors='replace') as f:
    f.write(content)

print("\ngateway.py updated!")
