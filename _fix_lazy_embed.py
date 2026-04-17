# -*- coding: utf-8 -*-
"""Fix embedding model loading - lazy load and add config UI"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Fix 1: Make embedding_service and rag_retriever lazy-loaded
rag_path = r'D:\kflower\kflower-backend\app\core\ai_digital_base\rag.py'
with open(rag_path, 'r', encoding='utf-8-sig', errors='replace') as f:
    rag_content = f.read()

# Replace global instance with lazy getter
old_ending = '''
# 全局RAG检索器实例
rag_retriever = RAGRetriever()'''

new_ending = '''
# 全局RAG检索器实例 - 懒加载
_rag_retriever = None

def get_rag_retriever():
    """获取RAG检索器实例（懒加载）"""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()
    return _rag_retriever

# 为了兼容旧代码
@property
def rag_retriever():
    return get_rag_retriever()'''

if old_ending in rag_content:
    rag_content = rag_content.replace(old_ending, new_ending)
    print("[OK] rag.py lazy loading")
else:
    print("[WARN] Could not find rag.py ending")

with open(rag_path, 'w', encoding='utf-8-sig', errors='replace') as f:
    f.write(rag_content)

# Fix 2: Also make embedding_service lazy-loaded in local_services.py
local_services_path = r'D:\kflower\kflower-backend\app\core\ai_digital_base\local_services.py'
with open(local_services_path, 'r', encoding='utf-8-sig', errors='replace') as f:
    ls_content = f.read()

# Find the module-level embedding_service instantiation
old_service = 'embedding_service = EmbeddingService()'
new_service = '''# 懒加载，避免启动时初始化失败的模型
_embedding_service = None

def get_embedding_service():
    """获取嵌入服务实例（懒加载）"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

# 保持向后兼容
embedding_service = type('LazyEmbeddingService', (), {
    '__getattr__': lambda self, name: getattr(get_embedding_service(), name)
})()'''

if old_service in ls_content:
    ls_content = ls_content.replace(old_service, new_service)
    print("[OK] local_services.py lazy loading")
else:
    print("[WARN] Could not find embedding_service instantiation")

# Also lazy-load rerank_service
old_rerank = 'rerank_service = RerankService()'
new_rerank = '''# 懒加载
_rerank_service = None

def get_rerank_service():
    """获取重排服务实例（懒加载）"""
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService()
    return _rerank_service

rerank_service = type('LazyRerankService', (), {
    '__getattr__': lambda self, name: getattr(get_rerank_service(), name)
})()'''

if old_rerank in ls_content:
    ls_content = ls_content.replace(old_rerank, new_rerank)
    print("[OK] rerank_service lazy loading")

with open(local_services_path, 'w', encoding='utf-8-sig', errors='replace') as f:
    f.write(ls_content)

print("\nBackend lazy loading applied!")