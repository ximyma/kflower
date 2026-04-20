# 重写知识库搜索函数 - 增强召回率和准确率
import re

path = r'E:\kkflower\kflower-backend\app\api\v1\endpoints\knowledge.py'
with open(path, encoding='utf-8') as f:
    content = f.read()

# 找到搜索函数的开始位置
old_search_start = '''# ============ 高级检索 ============

async def _do_vector_search(query: str, kb_id: Optional[int], top_k: int) -> List[Dict[str, Any]]:
    """独立的向量搜索函数，支持懒加载模型"""
    from app.core.ai_digital_base import rag_retriever
    collection_name = f"kb_{kb_id}" if kb_id else "global"
    return await rag_retriever.search(collection_name=collection_name, query=query, top_k=top_k)


@router.get("/search")
async def advanced_search('''

new_search_code = '''# ============ 高级检索 ============

def _compute_bm25_score(query_terms: List[str], doc_text: str, avg_doc_len: float = 100) -> float:
    """简化的BM25评分"""
    if not query_terms or not doc_text:
        return 0.0
    k1, b = 1.5, 0.75
    doc_len = len(doc_text)
    score = 0.0
    doc_lower = doc_text.lower()
    for term in query_terms:
        tf = doc_lower.count(term.lower())
        if tf > 0:
            idf = 1.0  # 简化IDF
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
    return score


def _extract_tags_from_json(tags_json: Any) -> List[str]:
    """从JSON字段提取标签名列表"""
    if not tags_json:
        return []
    if isinstance(tags_json, str):
        try:
            tags_json = json.loads(tags_json)
        except:
            return [tags_json] if tags_json else []
    if isinstance(tags_json, list):
        return [t.get('name', t) if isinstance(t, dict) else str(t) for t in tags_json]
    return []


async def _do_vector_search(query: str, kb_id: Optional[int], top_k: int) -> List[Dict[str, Any]]:
    """独立的向量搜索函数，支持懒加载模型"""
    try:
        from app.core.ai_digital_base import rag_retriever
        collection_name = f"kb_{kb_id}" if kb_id else "global"
        return await rag_retriever.search(collection_name=collection_name, query=query, top_k=top_k)
    except Exception as e:
        logger.warning(f"向量检索异常: {e}")
        return []


@router.get("/search")
async def advanced_search('''

content = content.replace(old_search_start, new_search_code)

# 替换搜索主体逻辑
old_body = '''    """高级检索：支持全文/关键词/向量/混合四种模式"""
    results = []

    # 全文检索
    if type in ("fulltext", "hybrid"):
        query = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
        if kb_id:
            query = query.where(KnowledgeDocument.knowledge_base_id == kb_id)
        if tag:
            # SQLite JSON contains workaround: use LIKE for tag matching
            query = query.where(KnowledgeDocument.tags.astext.like(f'%"{tag}"%'))
        query = query.where(
            (KnowledgeDocument.content.ilike(f"%{q}%")) |
            (KnowledgeDocument.title.ilike(f"%{q}%"))
        ).limit(top_k * 2)
        result = await db.execute(query)
        docs = result.scalars().all()
        for doc in docs:
            results.append({
                "id": doc.id, "title": doc.title, "type": "fulltext",
                "kb_id": doc.knowledge_base_id, "score": 1.0,
                "keywords": doc.keywords, "tags": doc.tags,
                "summary": (doc.summary or "")[:200],
                "created_at": str(doc.created_at) if doc.created_at else None,
            })

    # 关键词检索：jieba分词后匹配title
    if type in ("keyword", "hybrid"):
        import jieba
        kw_list = list(jieba.cut(q))
        kw_list = [w for w in kw_list if len(w) > 1]
        if kw_list:
            query = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
            if kb_id:
                query = query.where(KnowledgeDocument.knowledge_base_id == kb_id)
            # 关键词模式下匹配标题和摘要
            for kw in kw_list[:5]:
                query = query.where(
                    (KnowledgeDocument.title.ilike(f"%{kw}%")) |
                    (KnowledgeDocument.summary.ilike(f"%{kw}%"))
                )
            query = query.limit(top_k * 2)
            result = await db.execute(query)
            docs = result.scalars().all()
            existing_ids = {r["id"] for r in results}
            for doc in docs:
                if doc.id not in existing_ids:
                    results.append({
                        "id": doc.id, "title": doc.title, "type": "keyword",
                        "kb_id": doc.knowledge_base_id, "score": 0.8,
                        "keywords": doc.keywords, "tags": doc.tags,
                        "summary": (doc.summary or "")[:200],
                        "created_at": str(doc.created_at) if doc.created_at else None,
                    })

    # 向量检索（有超时保护，加载模型可能很慢）
    if type in ("vector", "hybrid"):
        import asyncio
        try:
            vec_results = await asyncio.wait_for(_do_vector_search(q, kb_id, top_k * 2), timeout=5.0)
            if vec_results:
                existing_ids = {r["id"] for r in results}
                for vr in vec_results:
                    doc_id = vr.get("metadata", {}).get("doc_id")
                    if doc_id and doc_id not in existing_ids:
                        results.append({
                            "id": doc_id, "title": vr.get("metadata", {}).get("doc_title", ""),
                            "type": "vector", "kb_id": kb_id,
                            "score": vr.get("score", 0.5),
                            "text": vr.get("text", "")[:300],
                            "keywords": vr.get("metadata", {}).get("keywords", []),
                            "created_at": None,
                        })
        except asyncio.TimeoutError:
            logger.warning("向量检索超时，跳过")
        except Exception as e:
            logger.warning(f"向量检索失败: {e}")

    # Rerank
    if kb_id and len(results) > top_k:
        kb_result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id, KnowledgeBase.is_active == True)
        )
        kb = kb_result.scalar_one_or_none()
        if kb and kb.rerank_enabled and kb.rerank_model:
            results = await _rerank_results(q, results, kb.rerank_model, top_k)

    # 去重
    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    return {"results": unique[:top_k], "total": len(unique)}'''

new_body = '''    """高级检索：支持全文/关键词/向量/混合四种模式，使用RRF融合"""
    import jieba
    import asyncio
    from sqlalchemy import or_, func
    
    results = {}  # 用dict存储，key=doc_id，便于RRF融合
    query_terms = [w for w in jieba.cut(q) if len(w) > 1]
    
    # ========== 1. 全文检索（BM25评分）==========
    if type in ("fulltext", "hybrid"):
        query_obj = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
        if kb_id:
            query_obj = query_obj.where(KnowledgeDocument.knowledge_base_id == kb_id)
        if tag:
            # 标签过滤：检查tags JSON数组是否包含该标签
            query_obj = query_obj.where(
                or_(
                    KnowledgeDocument.tags.astext.like(f'%"name": "{tag}"%'),
                    KnowledgeDocument.tags.astext.like(f'%"{tag}"%')
                )
            )
        # 全文匹配：标题 OR 内容 OR 摘要
        query_obj = query_obj.where(
            or_(
                KnowledgeDocument.title.ilike(f"%{q}%"),
                KnowledgeDocument.content.ilike(f"%{q}%"),
                KnowledgeDocument.summary.ilike(f"%{q}%")
            )
        ).limit(top_k * 3)
        result = await db.execute(query_obj)
        docs = result.scalars().all()
        for rank, doc in enumerate(docs):
            if doc.id not in results:
                results[doc.id] = {
                    "id": doc.id, "title": doc.title,
                    "kb_id": doc.knowledge_base_id,
                    "keywords": doc.keywords, "tags": doc.tags,
                    "summary": (doc.summary or "")[:200],
                    "content": (doc.content or "")[:500],
                    "created_at": str(doc.created_at) if doc.created_at else None,
                    "scores": {}, "rrf_score": 0.0
                }
            # BM25评分
            bm25 = _compute_bm25_score(query_terms, (doc.title or "") + " " + (doc.content or ""))
            results[doc.id]["scores"]["fulltext"] = bm25
            results[doc.id]["scores"]["fulltext_rank"] = rank + 1
    
    # ========== 2. 关键词检索（OR逻辑，jieba分词）==========
    if type in ("keyword", "hybrid") and query_terms:
        # 构建OR条件
        or_conditions = []
        for kw in query_terms[:8]:  # 取前8个关键词
            or_conditions.append(KnowledgeDocument.title.ilike(f"%{kw}%"))
            or_conditions.append(KnowledgeDocument.summary.ilike(f"%{kw}%"))
            or_conditions.append(KnowledgeDocument.content.ilike(f"%{kw}%"))
        
        if or_conditions:
            query_obj = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
            if kb_id:
                query_obj = query_obj.where(KnowledgeDocument.knowledge_base_id == kb_id)
            query_obj = query_obj.where(or_(*or_conditions)).limit(top_k * 3)
            result = await db.execute(query_obj)
            docs = result.scalars().all()
            for rank, doc in enumerate(docs):
                if doc.id not in results:
                    results[doc.id] = {
                        "id": doc.id, "title": doc.title,
                        "kb_id": doc.knowledge_base_id,
                        "keywords": doc.keywords, "tags": doc.tags,
                        "summary": (doc.summary or "")[:200],
                        "content": (doc.content or "")[:500],
                        "created_at": str(doc.created_at) if doc.created_at else None,
                        "scores": {}, "rrf_score": 0.0
                    }
                # 计算匹配的关键词数量作为分数
                matched = sum(1 for kw in query_terms if kw.lower() in (doc.title or "").lower() or kw.lower() in (doc.content or "").lower())
                results[doc.id]["scores"]["keyword"] = matched / len(query_terms) if query_terms else 0
                results[doc.id]["scores"]["keyword_rank"] = rank + 1
    
    # ========== 3. 向量检索 ==========
    if type in ("vector", "hybrid"):
        try:
            vec_results = await asyncio.wait_for(_do_vector_search(q, kb_id, top_k * 2), timeout=8.0)
            if vec_results:
                for rank, vr in enumerate(vec_results):
                    doc_id = vr.get("metadata", {}).get("doc_id")
                    if doc_id:
                        if doc_id not in results:
                            results[doc_id] = {
                                "id": doc_id,
                                "title": vr.get("metadata", {}).get("doc_title", "未知文档"),
                                "kb_id": kb_id,
                                "keywords": vr.get("metadata", {}).get("keywords", []),
                                "tags": [],
                                "summary": "",
                                "content": vr.get("text", "")[:500],
                                "created_at": None,
                                "scores": {}, "rrf_score": 0.0
                            }
                        results[doc_id]["scores"]["vector"] = vr.get("score", 0.5)
                        results[doc_id]["scores"]["vector_rank"] = rank + 1
        except asyncio.TimeoutError:
            logger.warning("向量检索超时，跳过")
        except Exception as e:
            logger.warning(f"向量检索失败: {e}")
    
    # ========== 4. RRF融合评分 ==========
    k = 60  # RRF常数
    for doc_id, doc in results.items():
        rrf = 0.0
        for score_type in ["fulltext", "keyword", "vector"]:
            rank_key = f"{score_type}_rank"
            if rank_key in doc["scores"]:
                rrf += 1.0 / (k + doc["scores"][rank_key])
        doc["rrf_score"] = rrf
        # 综合分数（RRF + 原始分数加权）
        doc["score"] = rrf * 0.6 + max(doc["scores"].get("fulltext", 0), doc["scores"].get("keyword", 0), doc["scores"].get("vector", 0)) * 0.4
    
    # ========== 5. Rerank重排（可选）==========
    sorted_results = sorted(results.values(), key=lambda x: x["score"], reverse=True)
    if kb_id and len(sorted_results) > top_k:
        kb_result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id, KnowledgeBase.is_active == True)
        )
        kb = kb_result.scalar_one_or_none()
        if kb and kb.rerank_enabled and kb.rerank_model:
            try:
                sorted_results = await _rerank_results(q, sorted_results, kb.rerank_model, top_k * 2)
            except Exception as e:
                logger.warning(f"Rerank失败: {e}")
    
    # ========== 6. 返回结果 ==========
    sorted_results = sorted(sorted_results, key=lambda x: x.get("rerank_score", x.get("score", 0)), reverse=True)
    
    # 清理内部字段
    for r in sorted_results:
        r.pop("scores", None)
        r.pop("rrf_score", None)
        r.pop("content", None)  # 不返回完整内容
    
    return {"results": sorted_results[:top_k], "total": len(sorted_results)}'''

content = content.replace(old_body, new_body)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# 验证语法
import ast
try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax error: {e}')
