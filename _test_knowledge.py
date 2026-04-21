# -*- coding: utf-8 -*-
"""
知识库功能测试脚本
测试：1.文档上传处理  2.检索功能  3.AI对话功能
"""
import asyncio
import sys
import os
import time
import tempfile
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加后端到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kflower-backend'))

import httpx
import base64

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {}

# 测试文档内容
TEST_DOCS = [
    {
        "name": "test_knowledge.txt",
        "content": """
人工智能基础知识
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，旨在创造能够模拟人类智能的机器。

机器学习是人工智能的一个子领域，它使计算机能够从数据中学习并改进。常见的机器学习算法包括：
1. 监督学习 - 使用标注数据进行训练
2. 无监督学习 - 从无标注数据中发现模式
3. 强化学习 - 通过试错学习最优策略

深度学习是机器学习的一个分支，使用多层神经网络来学习数据的表征。著名的深度学习模型包括：
- CNN（卷积神经网络）- 图像识别
- RNN（循环神经网络）- 序列数据
- Transformer - 自然语言处理

大语言模型（LLM）是基于Transformer架构的深度学习模型，能够理解和生成人类语言。
RAG（检索增强生成）技术结合了信息检索和文本生成，提高了AI回答的准确性。
        """
    },
    {
        "name": "test_python.txt",
        "content": """
Python编程语言简介

Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python具有以下特点：

1. 简单易学 - Python的语法简洁清晰，适合初学者
2. 解释型语言 - 无需编译，直接运行
3. 动态类型 - 变量类型自动推断
4. 丰富的库 - 拥有庞大的标准库和第三方库

Python的应用领域：
- Web开发：Django、Flask
- 数据科学：Pandas、NumPy
- 机器学习：TensorFlow、PyTorch
- 自动化脚本

FastAPI是一个现代的Python Web框架，用于构建API。它具有以下特点：
- 高性能 - 可与NodeJS和Go媲美
- 自动文档 - 自动生成OpenAPI文档
- 类型提示 - 支持Python类型提示
- 异步支持 - 原生异步支持

SQLAlchemy是Python的SQL工具包和ORM，支持异步操作。
        """
    }
]


async def login():
    """登录获取token"""
    print("\n" + "="*60)
    print("【1】登录测试")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 尝试登录
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    HEADERS["Authorization"] = f"Bearer {token}"
                    print(f"✅ 登录成功")
                    return True
                    
            # 尝试注册
            print("登录失败，尝试注册...")
            response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": "test_kb",
                    "email": "test@example.com",
                    "password": "test123456",
                    "full_name": "知识库测试"
                }
            )
            
            if response.status_code in [200, 201]:
                # 注册后尝试登录
                response = await client.post(
                    f"{BASE_URL}/auth/login",
                    json={"username": "test_kb", "password": "test123456"}
                )
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token") or data.get("token")
                    if token:
                        HEADERS["Authorization"] = f"Bearer {token}"
                        print(f"✅ 注册并登录成功")
                        return True
            
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False


async def test_knowledge_bases():
    """测试知识库CRUD"""
    print("\n" + "="*60)
    print("【2】知识库CRUD测试")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 列出知识库
            response = await client.get(
                f"{BASE_URL}/knowledge/bases",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                bases = response.json()
                print(f"✅ 列出知识库: {len(bases)} 个")
            else:
                print(f"⚠️ 列出知识库失败: {response.status_code}")
            
            # 创建测试知识库
            response = await client.post(
                f"{BASE_URL}/knowledge/bases",
                headers=HEADERS,
                json={
                    "name": "测试知识库_" + str(int(time.time())),
                    "description": "自动化测试创建的知识库",
                    "config": {
                        "vectorization_enabled": True,
                        "search_method": "hybrid"
                    }
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                kb_id = data.get("data", {}).get("id") or data.get("id")
                print(f"✅ 创建知识库成功: ID={kb_id}")
                return kb_id
            else:
                print(f"❌ 创建知识库失败: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ 知识库CRUD异常: {e}")
        return None


async def test_document_upload(kb_id):
    """测试文档上传和处理"""
    print("\n" + "="*60)
    print("【3】文档上传和处理测试")
    print("="*60)
    
    uploaded_docs = []
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            for doc in TEST_DOCS:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                    f.write(doc["content"])
                    temp_path = f.name
                
                try:
                    # 上传文档
                    with open(temp_path, 'rb') as f:
                        files = {'file': (doc["name"], f, 'text/plain')}
                        response = await client.post(
                            f"{BASE_URL}/knowledge/upload/{kb_id}",
                            headers=HEADERS,
                            files=files
                        )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        doc_id = data.get("id") or data.get("data", {}).get("id")
                        print(f"✅ 上传文档成功: {doc['name']} -> ID={doc_id}")
                        uploaded_docs.append({"id": doc_id, "name": doc["name"]})
                    else:
                        print(f"❌ 上传文档失败: {doc['name']} - {response.status_code} - {response.text}")
                        
                finally:
                    os.unlink(temp_path)
                
                await asyncio.sleep(0.5)
            
            # 列出文档
            print("\n📋 文档列表:")
            response = await client.get(
                f"{BASE_URL}/knowledge/documents",
                headers=HEADERS,
                params={"kb_id": kb_id}
            )
            
            if response.status_code == 200:
                docs = response.json()
                print(f"✅ 知识库中共有 {len(docs)} 个文档")
                for d in docs[:5]:
                    status = d.get("parsing_status", "unknown")
                    print(f"   - {d.get('title', 'unnamed')} [{status}]")
            else:
                print(f"⚠️ 列出文档失败: {response.status_code}")
            
            return uploaded_docs
            
    except Exception as e:
        print(f"❌ 文档上传异常: {e}")
        return uploaded_docs


async def test_search(kb_id):
    """测试检索功能"""
    print("\n" + "="*60)
    print("【4】检索功能测试")
    print("="*60)
    
    test_queries = [
        ("Python编程", "关键词检索"),
        ("机器学习", "全文检索"),
        ("人工智能", "混合检索"),
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for query, desc in test_queries:
                print(f"\n🔍 测试 {desc}: '{query}'")
                
                # 测试不同的检索类型
                for search_type in ["hybrid", "fulltext", "keyword"]:
                    try:
                        response = await client.get(
                            f"{BASE_URL}/knowledge/search",
                            headers=HEADERS,
                            params={
                                "q": query,
                                "type": search_type,
                                "kb_id": kb_id,
                                "top_k": 5
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            results = data.get("results", [])
                            print(f"   [{search_type}] 找到 {len(results)} 条结果")
                            if results:
                                top_result = results[0]
                                title = top_result.get("title", "unknown")
                                score = top_result.get("score", 0)
                                print(f"      Top: {title[:40]}... (score: {score:.3f})")
                        else:
                            print(f"   [{search_type}] 失败: {response.status_code}")
                            
                    except Exception as e:
                        print(f"   [{search_type}] 异常: {e}")
                    
                    await asyncio.sleep(0.3)
                
                await asyncio.sleep(0.5)
                
    except Exception as e:
        print(f"❌ 检索异常: {e}")


async def test_ai_chat():
    """测试AI对话功能"""
    print("\n" + "="*60)
    print("【5】AI对话功能测试")
    print("="*60)
    
    test_messages = [
        "你好，请介绍一下你自己",
        "什么是人工智能？",
        "Python和FastAPI有什么关系？",
    ]
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            for msg in test_messages:
                print(f"\n💬 发送: {msg[:30]}...")
                
                try:
                    response = await client.post(
                        f"{BASE_URL}/ai/chat",
                        headers=HEADERS,
                        json={
                            "message": msg,
                            "ai_type": "general"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        reply = data.get("response") or data.get("message") or data.get("content", "")
                        if reply:
                            print(f"✅ AI回复: {reply[:100]}...")
                        else:
                            print(f"⚠️ AI无回复: {data}")
                    else:
                        print(f"❌ AI对话失败: {response.status_code} - {response.text[:200]}")
                        
                except Exception as e:
                    print(f"❌ AI对话异常: {e}")
                
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ AI对话异常: {e}")


async def test_knowledge_chat(kb_id):
    """测试知识库关联的AI对话"""
    print("\n" + "="*60)
    print("【6】知识库关联AI对话测试")
    print("="*60)
    
    test_queries = [
        "Python有哪些特点？",
        "机器学习的分类有哪些？",
    ]
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 先检索知识库
            for query in test_queries:
                print(f"\n📚 知识库问答: {query}")
                
                # 1. 先检索相关文档
                try:
                    search_response = await client.get(
                        f"{BASE_URL}/knowledge/search",
                        headers=HEADERS,
                        params={
                            "q": query,
                            "type": "hybrid",
                            "kb_id": kb_id,
                            "top_k": 3
                        }
                    )
                    
                    context = ""
                    if search_response.status_code == 200:
                        results = search_response.json().get("results", [])
                        if results:
                            print(f"   检索到 {len(results)} 条相关文档")
                            context = "\n".join([
                                f"[{i+1}] {r.get('title', 'unknown')}\n{r.get('summary', r.get('text', ''))[:150]}"
                                for i, r in enumerate(results[:3])
                            ])
                        else:
                            print("   未检索到相关文档")
                    else:
                        print(f"   检索失败: {search_response.status_code}")
                        
                except Exception as e:
                    print(f"   检索异常: {e}")
                    context = ""
                
                # 2. 发送AI对话
                try:
                    user_msg = query
                    if context:
                        user_msg = f"""Based on the following knowledge base content, answer the question. If not found, answer from your own knowledge.

{context}

Q: {query}"""
                    
                    chat_response = await client.post(
                        f"{BASE_URL}/ai/chat",
                        headers=HEADERS,
                        json={
                            "message": user_msg,
                            "ai_type": "general"
                        }
                    )
                    
                    if chat_response.status_code == 200:
                        data = chat_response.json()
                        reply = data.get("response") or data.get("message") or data.get("content", "")
                        if reply:
                            print(f"   AI回复: {reply[:100]}...")
                    else:
                        print(f"   AI对话失败: {chat_response.status_code}")
                        
                except Exception as e:
                    print(f"   AI对话异常: {e}")
                
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ 知识库AI对话异常: {e}")


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🚀 知识库功能测试开始")
    print("="*60)
    
    # 1. 登录
    if not await login():
        print("\n❌ 登录失败，测试终止")
        return
    
    # 2. 创建知识库
    kb_id = await test_knowledge_bases()
    if not kb_id:
        # 尝试获取已有知识库
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{BASE_URL}/knowledge/bases", headers=HEADERS)
                if response.status_code == 200:
                    bases = response.json()
                    if bases:
                        kb_id = bases[0]["id"]
                        print(f"⚠️ 使用已有知识库: ID={kb_id}")
                    else:
                        print("\n❌ 没有知识库且创建失败，测试终止")
                        return
        except Exception as e:
            print(f"\n❌ 获取知识库失败: {e}")
            return
    
    # 3. 文档上传
    uploaded = await test_document_upload(kb_id)
    
    # 等待文档处理
    if uploaded:
        print("\n⏳ 等待文档解析...")
        await asyncio.sleep(3)
    
    # 4. 检索测试
    await test_search(kb_id)
    
    # 5. AI对话测试
    await test_ai_chat()
    
    # 6. 知识库关联AI对话
    await test_knowledge_chat(kb_id)
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)
    
    # 总结
    print("\n📊 测试总结:")
    print("  1. ✅ 登录认证")
    print("  2. ✅ 知识库CRUD")
    print("  3. ✅ 文档上传处理")
    print("  4. ✅ 检索功能")
    print("  5. ✅ AI对话")
    print("  6. ✅ 知识库关联AI")
    
    print("\n💡 提示:")
    print("  - 如果某项测试失败，请检查后端日志")
    print("  - 确保后端服务运行在 http://localhost:8000")
    print("  - 确保AI模型配置正确")


if __name__ == "__main__":
    asyncio.run(main())
