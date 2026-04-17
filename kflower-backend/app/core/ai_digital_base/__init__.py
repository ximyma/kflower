"""
AI数字底座 - 初始化模块
"""
from app.core.ai_digital_base.gateway import ai_gateway, AIGateway
from app.core.ai_digital_base.conversation import conversation_manager, ConversationManager
from app.core.ai_digital_base import rag
from app.core.ai_digital_base.inference import inference_service, InferenceService

# 懒加载包装器
class LazyRAGRetriever:
    """懒加载RAG检索器"""
    _instance = None
    def __getattr__(self, name):
        from app.core.ai_digital_base.rag import get_rag_retriever
        return getattr(get_rag_retriever(), name)

class LazyEmbeddingService:
    """懒加载嵌入服务"""
    _instance = None
    def __getattr__(self, name):
        from app.core.ai_digital_base.local_services import get_embedding_service
        return getattr(get_embedding_service(), name)

rag_retriever = LazyRAGRetriever()
EmbeddingService = LazyEmbeddingService()

__all__ = [
    "ai_gateway",
    "AIGateway",
    "conversation_manager",
    "ConversationManager",
    "rag_retriever",
    "RAGRetriever",
    "EmbeddingService",
    "inference_service",
    "InferenceService",
]
