"""
AI数字底座 - 初始化模块
"""
from app.core.ai_digital_base.gateway import ai_gateway, AIGateway
from app.core.ai_digital_base.conversation import conversation_manager, ConversationManager
from app.core.ai_digital_base.rag import rag_retriever, RAGRetriever
from app.core.ai_digital_base.local_services import embedding_service, EmbeddingService
from app.core.ai_digital_base.inference import inference_service, InferenceService

__all__ = [
    "ai_gateway",
    "AIGateway",
    "conversation_manager",
    "ConversationManager",
    "rag_retriever",
    "RAGRetriever",
    "embedding_service",
    "EmbeddingService",
    "inference_service",
    "InferenceService",
]
