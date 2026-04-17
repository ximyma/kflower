# -*- coding: utf-8 -*-
"""Fix __init__.py to use lazy loading"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-backend\app\core\ai_digital_base\__init__.py'
with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
    content = f.read()

old_init = '''"""
AI数字底座 - 初始化模块
"""
from app.core.ai_digital_base.gateway import ai_gateway, AIGateway
from app.core.ai_digital_base.conversation import conversation_manager, ConversationManager
from app.core.ai_digital_base.rag import rag_retriever, RAGRetriever, EmbeddingService
from app.core.ai_digital_base.inference import inference_service, InferenceService

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
]'''

new_init = '''"""
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
]'''

if old_init in content:
    content = content.replace(old_init, new_init)
    print("[OK] __init__.py updated")
else:
    print("[WARN] Could not find old __init__ content")

with open(path, 'w', encoding='utf-8-sig', errors='replace') as f:
    f.write(content)

print("__init__.py fixed!")