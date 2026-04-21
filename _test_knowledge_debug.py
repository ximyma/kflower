# -*- coding: utf-8 -*-
"""知识库详细诊断测试"""
import asyncio
import httpx
import traceback

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {}

async def main():
    print("=" * 60)
    print("知识库详细诊断测试")
    print("=" * 60)

    # 1. 登录
    print("\n[1] 登录测试...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            print(f"    状态码: {response.status_code}")
            print(f"    响应: {response.text[:200]}")
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    HEADERS["Authorization"] = f"Bearer {token}"
                    print("    登录成功!")
    except Exception as e:
        print(f"    登录异常: {e}")
        traceback.print_exc()
        return

    if not HEADERS:
        print("    未获取到token，测试终止")
        return

    # 2. 获取知识库列表
    print("\n[2] 获取知识库列表...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/knowledge/bases",
                headers=HEADERS
            )
            print(f"    状态码: {response.status_code}")
            if response.status_code == 200:
                bases = response.json()
                print(f"    知识库数量: {len(bases)}")
                if bases:
                    kb_id = bases[0]["id"]
                    print(f"    使用知识库ID: {kb_id}")

                    # 3. 测试高级检索
                    print("\n[3] 测试高级检索...")
                    for search_type in ["hybrid", "fulltext", "keyword", "vector"]:
                        try:
                            response = await client.get(
                                f"{BASE_URL}/knowledge/search",
                                headers=HEADERS,
                                params={
                                    "q": "Python",
                                    "type": search_type,
                                    "kb_id": kb_id,
                                    "top_k": 5
                                }
                            )
                            print(f"\n    [{search_type}] 状态码: {response.status_code}")
                            if response.status_code == 200:
                                data = response.json()
                                print(f"    响应类型: {type(data)}")
                                print(f"    结果数: {len(data.get('results', []))}")
                            else:
                                print(f"    错误: {response.text[:200]}")
                        except Exception as e:
                            print(f"\n    [{search_type}] 异常: {e}")
                            traceback.print_exc()
            else:
                print(f"    错误: {response.text[:200]}")
    except Exception as e:
        print(f"    异常: {e}")
        traceback.print_exc()

    # 4. 测试AI对话
    print("\n[4] 测试AI对话...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/ai/chat",
                headers=HEADERS,
                json={
                    "message": "你好",
                    "ai_type": "general"
                }
            )
            print(f"    状态码: {response.status_code}")
            print(f"    响应: {response.text[:300]}")
    except Exception as e:
        print(f"    异常: {e}")
        traceback.print_exc()

    # 5. 测试 agent/chat
    print("\n[5] 测试 Agent Chat...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/agent/chat",
                headers=HEADERS,
                json={
                    "message": "你好"
                }
            )
            print(f"    状态码: {response.status_code}")
            print(f"    响应: {response.text[:300]}")
    except Exception as e:
        print(f"    异常: {e}")
        traceback.print_exc()

    # 6. 检查AI数字底座状态
    print("\n[6] 检查AI数字底座状态...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/ai/digital-base/status",
                headers=HEADERS
            )
            print(f"    状态码: {response.status_code}")
            print(f"    响应: {response.text[:300]}")
    except Exception as e:
        print(f"    异常: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
