# -*- coding: utf-8 -*-
"""知识库快速功能测试 - 重点测试不依赖AI的服务"""
import asyncio
import httpx
import traceback
import json

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {}

async def main():
    print("=" * 60)
    print("知识库快速功能测试")
    print("=" * 60)

    # 1. 登录
    print("\n[1] 登录...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    HEADERS["Authorization"] = f"Bearer {token}"
                    print("    OK")
            else:
                print(f"    FAIL: {response.status_code}")
                return
    except Exception as e:
        print(f"    ERROR: {e}")
        return

    if not HEADERS:
        print("    No token")
        return

    # 2. 知识库CRUD
    print("\n[2] 知识库CRUD...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 列出
            response = await client.get(f"{BASE_URL}/knowledge/bases", headers=HEADERS)
            if response.status_code == 200:
                bases = response.json()
                print(f"    列表: {len(bases)} 个")
                if bases:
                    kb_id = bases[0]["id"]
                    print(f"    使用KB ID: {kb_id}")

                    # 获取详情
                    response = await client.get(f"{BASE_URL}/knowledge/bases/{kb_id}", headers=HEADERS)
                    if response.status_code == 200:
                        kb = response.json()
                        print(f"    详情: {kb.get('name')} (doc_count={kb.get('doc_count')})")
                    else:
                        print(f"    详情获取失败: {response.status_code}")
            else:
                print(f"    FAIL: {response.status_code}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 3. 文档上传
    print("\n[3] 文档管理...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 列出文档
            response = await client.get(f"{BASE_URL}/knowledge/documents", headers=HEADERS)
            if response.status_code == 200:
                docs = response.json()
                print(f"    列表: {len(docs)} 个")
                if docs:
                    doc = docs[0]
                    print(f"    示例: {doc.get('title')} [{doc.get('parsing_status')}]")
                    print(f"    关键词: {doc.get('keywords', [])[:3]}")
                    print(f"    摘要: {doc.get('summary', '无')[:50]}...")
            else:
                print(f"    FAIL: {response.status_code}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 4. 全文检索（不涉及向量）
    print("\n[4] 全文检索...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/knowledge/search",
                headers=HEADERS,
                params={"q": "Python", "type": "fulltext", "top_k": 5}
            )
            print(f"    状态: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"    结果: {len(results)} 条")
                for r in results[:3]:
                    print(f"      - {r.get('title', 'unknown')[:30]} (score: {r.get('score', 0):.3f})")
            else:
                print(f"    错误: {response.text[:200]}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 5. 标签管理
    print("\n[5] 标签管理...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/knowledge/tags", headers=HEADERS)
            if response.status_code == 200:
                tags = response.json()
                print(f"    列表: {len(tags)} 个")
            else:
                print(f"    FAIL: {response.status_code}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 6. 笔记管理
    print("\n[6] 笔记管理...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/knowledge/notes", headers=HEADERS)
            if response.status_code == 200:
                notes = response.json()
                print(f"    列表: {len(notes)} 个")
            else:
                print(f"    FAIL: {response.status_code}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 7. AI状态检查
    print("\n[7] AI配置状态检查...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/ai/digital-base/status", headers=HEADERS)
            print(f"    状态: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"    embedding_provider: {data.get('embedding_provider')}")
                print(f"    llm_provider: {data.get('llm_provider')}")
            else:
                print(f"    错误: {response.text[:200]}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 8. 系统配置
    print("\n[8] 系统AI配置...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BASE_URL}/system/ai-config-status", headers=HEADERS)
            print(f"    状态: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"    AI配置: {json.dumps(data, ensure_ascii=False)[:200]}")
            else:
                print(f"    错误: {response.text[:200]}")
    except Exception as e:
        print(f"    ERROR: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
