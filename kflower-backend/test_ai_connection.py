import asyncio
from app.core.ai_digital_base.gateway import ai_gateway

async def test_ai_connection():
    print("测试AI模型连接...")
    
    # 测试SiliconFlow（远程模型）
    print("\n测试SiliconFlow模型...")
    try:
        response = await ai_gateway.chat(
            messages=[{"role": "user", "content": "你好，测试连接"}],
            provider="siliconflow",
            timeout=30
        )
        print(f"SiliconFlow响应: {response}")
    except Exception as e:
        print(f"SiliconFlow测试失败: {e}")
    
    # 测试Ollama（本地模型）
    print("\n测试Ollama模型...")
    try:
        response = await ai_gateway.chat(
            messages=[{"role": "user", "content": "你好，测试连接"}],
            provider="ollama",
            timeout=30
        )
        print(f"Ollama响应: {response}")
    except Exception as e:
        print(f"Ollama测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_connection())
