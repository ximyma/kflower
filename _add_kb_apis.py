# -*- coding: utf-8 -*-
"""追加到knowledge.py的新API"""

NEW_APIS = r'''

# ============ 高级检索 ============

@router.get("/search")
async def advanced_search(
    q: str = Query(..., description="搜索关键词"),
    type: str = Query("hybrid", description="检索类型: fulltext/keyword/vector/hybrid"),
    kb_id: Optional[int] = Query(None, description="知识库ID"),
    tag: Optional[str] = Query(None, description="标签过滤"),
    top_k: int = Query(10, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """高级检索：支持全文/关键词/向量/混合四种模式"""
    results = []

    # 全文检索
    if type in ("fulltext", "hybrid"):
        query = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
        if kb_id:
            query = query.where(KnowledgeDocument.knowledge_base_id == kb_id)
        if tag:
            query = query.where(KnowledgeDocument.tags.contains(tag))
        query = query.where(
            (KnowledgeDocument.content.contains(q)) |
            (KnowledgeDocument.title.contains(q))
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

    # 关键词检索
    if type in ("keyword", "hybrid"):
        import jieba
        kw_list = list(jieba.cut(q))
        kw_list = [w for w in kw_list if len(w) > 1]
        if kw_list:
            query = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
            if kb_id:
                query = query.where(KnowledgeDocument.knowledge_base_id == kb_id)
            for kw in kw_list[:5]:
                query = query.where(
                    (KnowledgeDocument.keywords.contains(kw)) |
                    (KnowledgeDocument.title.contains(kw))
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

    # 向量检索
    if type in ("vector", "hybrid"):
        try:
            from app.core.ai_digital_base import rag_retriever
            collection_name = f"kb_{kb_id}" if kb_id else "global"
            vec_results = await rag_retriever.search(
                collection_name=collection_name, query=q, top_k=top_k * 2
            )
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

    return {"results": unique[:top_k], "total": len(unique)}


# ============ 标签管理 ============

@router.get("/tags")
async def list_tags(
    kb_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标签列表"""
    query = select(KnowledgeTag)
    if kb_id:
        query = query.where((KnowledgeTag.kb_id == kb_id) | (KnowledgeTag.kb_id == None))
    result = await db.execute(query.order_by(KnowledgeTag.name))
    tags = result.scalars().all()
    return [
        {"id": t.id, "name": t.name, "color": t.color,
         "description": t.description, "kb_id": t.kb_id,
         "created_at": str(t.created_at) if t.created_at else None}
        for t in tags
    ]


@router.post("/tags", response_model=BaseResponse)
async def create_tag(
    request: KnowledgeTagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建标签"""
    tag = KnowledgeTag(
        name=request.name, color=request.color or "#1890ff",
        description=request.description, kb_id=request.kb_id,
        created_by=current_user.id
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return BaseResponse(message="标签创建成功", data={"id": tag.id, "name": tag.name})


@router.delete("/tags/{tag_id}", response_model=BaseResponse)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除标签"""
    result = await db.execute(select(KnowledgeTag).where(KnowledgeTag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    # 删除关联
    await db.execute(
        update(KnowledgeDocumentTag).where(KnowledgeDocumentTag.tag_id == tag_id).values(tag_id=None)
    )
    await db.delete(tag)
    await db.commit()
    return BaseResponse(message="标签已删除")


@router.post("/documents/{doc_id}/tags", response_model=BaseResponse)
async def add_document_tag(
    doc_id: int,
    request: DocumentTagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """给文档添加标签"""
    result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    tag_result = await db.execute(select(KnowledgeTag).where(KnowledgeTag.id == request.tag_id))
    tag = tag_result.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 检查是否已关联
    exist = await db.execute(
        select(KnowledgeDocumentTag).where(
            KnowledgeDocumentTag.document_id == doc_id,
            KnowledgeDocumentTag.tag_id == request.tag_id
        )
    )
    if exist.scalar_one_or_none():
        return BaseResponse(message="标签已存在")

    rel = KnowledgeDocumentTag(document_id=doc_id, tag_id=request.tag_id)
    db.add(rel)

    # 同步更新文档tags JSON字段
    doc_tags = doc.tags or []
    if tag.name not in doc_tags:
        doc_tags.append(tag.name)
        doc.tags = doc_tags

    await db.commit()
    return BaseResponse(message="标签添加成功")


@router.delete("/documents/{doc_id}/tags/{tag_id}", response_model=BaseResponse)
async def remove_document_tag(
    doc_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除文档标签"""
    result = await db.execute(
        select(KnowledgeDocumentTag).where(
            KnowledgeDocumentTag.document_id == doc_id,
            KnowledgeDocumentTag.tag_id == tag_id
        )
    )
    rel = result.scalar_one_or_none()
    if rel:
        await db.delete(rel)

    # 同步更新文档tags JSON
    doc_result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
    doc = doc_result.scalar_one_or_none()
    if doc and doc.tags:
        tag_result = await db.execute(select(KnowledgeTag).where(KnowledgeTag.id == tag_id))
        tag = tag_result.scalar_one_or_none()
        if tag and tag.name in doc.tags:
            doc.tags = [t for t in doc.tags if t != tag.name]

    await db.commit()
    return BaseResponse(message="标签已移除")


# ============ 笔记管理 ============

@router.get("/notes")
async def list_notes(
    kb_id: Optional[int] = Query(None),
    is_daily: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取笔记列表"""
    query = select(KnowledgeNote).where(KnowledgeNote.is_active == True)
    if kb_id:
        query = query.where(KnowledgeNote.knowledge_base_id == kb_id)
    if is_daily is not None:
        query = query.where(KnowledgeNote.is_daily == is_daily)
    query = query.order_by(KnowledgeNote.updated_at.desc())
    result = await db.execute(query)
    notes = result.scalars().all()
    return [
        {"id": n.id, "title": n.title, "content": (n.content or "")[:500],
         "tags": n.tags, "is_daily": n.is_daily, "note_date": n.note_date,
         "knowledge_base_id": n.knowledge_base_id,
         "created_at": str(n.created_at) if n.created_at else None,
         "updated_at": str(n.updated_at) if n.updated_at else None}
        for n in notes
    ]


@router.post("/notes", response_model=BaseResponse)
async def create_note(
    request: KnowledgeNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建笔记"""
    note = KnowledgeNote(
        title=request.title, content=request.content or "",
        tags=request.tags or [], is_daily=request.is_daily or False,
        note_date=request.note_date, knowledge_base_id=request.knowledge_base_id,
        organization_id=current_user.organization_id, created_by=current_user.id
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return BaseResponse(message="笔记创建成功", data={"id": note.id})


@router.put("/notes/{note_id}", response_model=BaseResponse)
async def update_note(
    note_id: int,
    request: KnowledgeNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新笔记"""
    result = await db.execute(select(KnowledgeNote).where(KnowledgeNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if request.title is not None:
        note.title = request.title
    if request.content is not None:
        note.content = request.content
    if request.tags is not None:
        note.tags = request.tags
    if request.is_daily is not None:
        note.is_daily = request.is_daily
    await db.commit()
    return BaseResponse(message="笔记更新成功")


@router.delete("/notes/{note_id}", response_model=BaseResponse)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除笔记"""
    result = await db.execute(select(KnowledgeNote).where(KnowledgeNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    note.is_active = False
    await db.commit()
    return BaseResponse(message="笔记已删除")


@router.get("/notes/{note_id}")
async def get_note_detail(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取笔记详情"""
    result = await db.execute(select(KnowledgeNote).where(KnowledgeNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {
        "id": note.id, "title": note.title, "content": note.content,
        "tags": note.tags, "is_daily": note.is_daily, "note_date": note.note_date,
        "knowledge_base_id": note.knowledge_base_id,
        "created_at": str(note.created_at) if note.created_at else None,
        "updated_at": str(note.updated_at) if note.updated_at else None,
    }


# ============ 知识图谱 ============

@router.get("/graph")
async def knowledge_graph(
    kb_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """知识图谱数据"""
    nodes = []
    edges = []

    # 知识库节点
    kb_query = select(KnowledgeBase).where(KnowledgeBase.is_active == True)
    if kb_id:
        kb_query = kb_query.where(KnowledgeBase.id == kb_id)
    result = await db.execute(kb_query)
    kbs = result.scalars().all()
    for kb in kbs:
        nodes.append({"id": f"kb_{kb.id}", "name": kb.name, "category": "知识库", "symbolSize": 40})

    # 文档节点（取前100）
    doc_query = select(KnowledgeDocument).where(KnowledgeDocument.is_active == True)
    if kb_id:
        doc_query = doc_query.where(KnowledgeDocument.knowledge_base_id == kb_id)
    doc_query = doc_query.limit(100)
    result = await db.execute(doc_query)
    docs = result.scalars().all()
    doc_ids = set()
    for doc in docs:
        doc_ids.add(doc.id)
        nodes.append({"id": f"doc_{doc.id}", "name": doc.title[:20], "category": "文档", "symbolSize": 20})
        edges.append({"source": f"kb_{doc.knowledge_base_id}", "target": f"doc_{doc.id}"})

    # 标签节点
    tag_query = select(KnowledgeTag)
    result = await db.execute(tag_query)
    tags = result.scalars().all()
    for tag in tags:
        nodes.append({"id": f"tag_{tag.id}", "name": tag.name, "category": "标签", "symbolSize": 15})

    # 文档-标签关联
    if doc_ids:
        rel_query = select(KnowledgeDocumentTag).where(KnowledgeDocumentTag.document_id.in_(doc_ids))
        result = await db.execute(rel_query)
        rels = result.scalars().all()
        for rel in rels:
            edges.append({"source": f"doc_{rel.document_id}", "target": f"tag_{rel.tag_id}"})

    return {"nodes": nodes, "edges": edges}
'''

# 追加到 knowledge.py
with open(r'E:\kkflower\kflower-backend\app\api\v1\endpoints\knowledge.py', 'a', encoding='utf-8') as f:
    f.write(NEW_APIS)

print("Appended new APIs to knowledge.py")
