"""
AI数字底座 - RAG检索模块
基于向量数据库的检索增强生成
"""
from typing import List, Dict, Optional, Any
import json
from app.core.ai_digital_base.gateway import ai_gateway
from app.core.config import settings


class EmbeddingService:
    """
    向量化服务
    将文本转换为向量，支持多种embedding模型
    """
    
    def __init__(self):
        self.embedding_client = None
        self._init_client()
    
    def _init_client(self):
        """初始化embedding客户端"""
        try:
            from openai import AsyncOpenAI
            self.embedding_client = AsyncOpenAI(
                api_key=settings.SILICONFLOW_API_KEY or "dummy",
                base_url=settings.EMBEDDING_API_BASE,
            )
        except Exception as e:
            print(f"Embedding client init error: {e}")
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """将文本转换为向量"""
        if not self.embedding_client:
            return None
        
        try:
            response = await self.embedding_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    async def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """批量将文本转换为向量"""
        if not self.embedding_client:
            return [None] * len(texts)
        
        try:
            response = await self.embedding_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Batch embedding error: {e}")
            return [None] * len(texts)


class RAGRetriever:
    """
    RAG检索器
    支持本地向量存储和Qdrant远程向量库
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.local_vectors: List[Dict[str, Any]] = []
        self.qdrant_client = None
        self._init_qdrant()
    
    def _init_qdrant(self):
        """初始化Qdrant客户端"""
        if not settings.QDRANT_ENABLED:
            return
        
        try:
            from qdrant_client import QdrantClient
            self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        except Exception as e:
            print(f"Qdrant client init error: {e}")
    
    async def add_document(
        self,
        collection_name: str,
        doc_id: str,
        text: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加文档到向量库"""
        embedding = await self.embedding_service.embed_text(text)
        if not embedding:
            return False
        
        doc = {
            "id": doc_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        
        if settings.QDRANT_ENABLED and self.qdrant_client:
            # 使用Qdrant远程存储
            try:
                from qdrant_client.models import PointStruct
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=[
                        PointStruct(
                            id=doc_id,
                            vector=embedding,
                            payload={"text": text, "metadata": metadata}
                        )
                    ]
                )
            except Exception as e:
                print(f"Qdrant upsert error: {e}")
                return False
        else:
            # 使用本地向量存储
            self.local_vectors.append(doc)
        
        return True
    
    async def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """检索相关文档"""
        query_embedding = await self.embedding_service.embed_text(query)
        if not query_embedding:
            return []
        
        if settings.QDRANT_ENABLED and self.qdrant_client:
            # 使用Qdrant检索
            try:
                results = self.qdrant_client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=top_k
                )
                return [
                    {
                        "id": result.id,
                        "text": result.payload.get("text"),
                        "score": result.score,
                        "metadata": result.payload.get("metadata", {})
                    }
                    for result in results
                ]
            except Exception as e:
                print(f"Qdrant search error: {e}")
                return []
        else:
            # 使用本地向量检索（简单余弦相似度）
            results = []
            for doc in self.local_vectors:
                if doc["id"].startswith(collection_name):
                    similarity = self._cosine_similarity(query_embedding, doc["embedding"])
                    results.append({
                        "id": doc["id"],
                        "text": doc["text"],
                        "score": similarity,
                        "metadata": doc["metadata"]
                    })
            
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (norm1 * norm2) if norm1 and norm2 else 0
    
    async def generate_with_context(
        self,
        query: str,
        collection_name: str,
        system_prompt: str = "你是一个智能助手，基于给定的上下文回答问题。",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """基于上下文生成回答"""
        # 1. 检索相关文档
        relevant_docs = await self.search(collection_name, query, top_k)
        
        if not relevant_docs:
            # 没有相关文档，直接生成
            return await ai_gateway.chat_with_system_prompt(
                system_prompt=system_prompt,
                user_message=query
            )
        
        # 2. 构建上下文
        context = "\n\n".join([
            f"[文档{i+1}]\n{doc['text']}"
            for i, doc in enumerate(relevant_docs)
        ])
        
        # 3. 带上下文的生成
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"上下文：\n{context}\n\n问题：{query}"}
        ]
        
        return await ai_gateway.chat(messages)


# 全局RAG检索器实例 - 懒加载
_rag_retriever = None

def get_rag_retriever():
    """获取RAG检索器实例（懒加载）"""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()
    return _rag_retriever

# 导出全局实例供其他模块使用
rag_retriever = get_rag_retriever()
