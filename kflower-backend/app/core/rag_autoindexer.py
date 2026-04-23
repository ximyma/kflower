"""
RAG 自动索引服务
当应用启用 auto_index 时，表单提交后自动向量化到知识库
"""
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class RAGAutoIndexer:
    """
    RAG 自动索引器
    监听表单提交事件，自动将数据索引到绑定的知识库
    """
    
    def __init__(self):
        self._rag_retriever = None
    
    def _get_rag_retriever(self):
        """懒加载 RAG 检索器"""
        if self._rag_retriever is None:
            from app.core.ai_digital_base.rag import get_rag_retriever
            self._rag_retriever = get_rag_retriever()
        return self._rag_retriever
    
    async def should_auto_index(
        self,
        app_id: int,
        db: AsyncSession
    ) -> tuple[bool, List[int], Dict[str, Any]]:
        """
        检查应用是否启用自动索引
        
        Returns:
            (should_index, knowledge_base_ids, knowledge_config)
        """
        from app.modules.my_apps.models import Application
        
        result = await db.execute(
            select(Application).where(Application.id == app_id)
        )
        app = result.scalar_one_or_none()
        
        if not app:
            return False, [], {}
        
        kb_ids = app.knowledge_base_ids or []
        kb_config = app.knowledge_config or {}
        
        # 检查是否启用自动索引
        auto_index = kb_config.get("auto_index", False)
        
        if not auto_index:
            return False, [], kb_config
        
        if not kb_ids:
            logger.warning(f"App#{app_id} 启用了 auto_index 但未绑定知识库")
            return False, [], kb_config
        
        return True, kb_ids, kb_config
    
    def format_form_data_as_text(
        self,
        template_name: str,
        template_code: str,
        field_values: Dict[str, Any],
        field_labels: Dict[str, str],  # {field_name: field_label}
        data_id: int,
    ) -> str:
        """
        将表单数据格式化为可索引的文本
        
        格式示例：
        [采购申请单] (PO-2026-001)
        申请人: 张三
        申请部门: 技术部
        申请日期: 2026-04-24
        金额: 5000.00 元
        用途: 办公设备采购
        审批状态: 待审批
        """
        lines = [f"[{template_name}] (ID: {data_id})"]
        
        for field_name, value in field_values.items():
            if value is None or value == "":
                continue
            
            # 获取字段标签
            field_label = field_labels.get(field_name, field_name)
            
            # 格式化值
            value_str = self._format_value(value)
            
            lines.append(f"{field_label}: {value_str}")
        
        return "\n".join(lines)
    
    def _format_value(self, value: Any) -> str:
        """格式化字段值为字符串"""
        if isinstance(value, bool):
            return "是" if value else "否"
        elif isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(value)
    
    async def index_form_submission(
        self,
        app_id: int,
        template_id: int,
        template_name: str,
        template_code: str,
        data_id: int,
        field_values: Dict[str, Any],
        field_labels: Dict[str, str],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        索引表单提交数据到知识库
        
        Args:
            app_id: 应用ID
            template_id: 模板ID
            template_name: 模板名称
            template_code: 模板代码
            data_id: 数据记录ID
            field_values: 字段值 {field_name: value}
            field_labels: 字段标签 {field_name: label}
            db: 数据库会话
        
        Returns:
            {
                "success": bool,
                "indexed_count": int,
                "errors": List[str]
            }
        """
        result = {
            "success": True,
            "indexed_count": 0,
            "errors": []
        }
        
        try:
            # 检查是否应该自动索引
            should_index, kb_ids, kb_config = await self.should_auto_index(app_id, db)
            
            if not should_index:
                logger.debug(f"App#{app_id} 未启用自动索引")
                return result
            
            # 格式化数据为文本
            text = self.format_form_data_as_text(
                template_name=template_name,
                template_code=template_code,
                field_values=field_values,
                field_labels=field_labels,
                data_id=data_id,
            )
            
            # 构建文档ID: app_{app_id}_template_{template_id}_data_{data_id}
            doc_id = f"app_{app_id}_tpl_{template_id}_data_{data_id}"
            
            # 构建元数据
            metadata = {
                "app_id": app_id,
                "template_id": template_id,
                "template_name": template_name,
                "template_code": template_code,
                "data_id": data_id,
                "indexed_at": datetime.now().isoformat(),
                "type": "form_submission",
            }
            
            # 使用 app 级别的 collection（或 KB 级别）
            collection_strategy = kb_config.get("collection_strategy", "app")
            
            if collection_strategy == "app":
                # 应用级别：一个应用一个 collection
                collection_name = f"app_{app_id}"
                
                success = await self._index_to_collection(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    text=text,
                    metadata=metadata,
                    kb_id=kb_ids[0] if kb_ids else None,  # 使用第一个KB的配置
                    kb_config=kb_config,
                )
                
                if success:
                    result["indexed_count"] = 1
                else:
                    result["errors"].append(f"索引到 collection={collection_name} 失败")
            
            elif collection_strategy == "kb":
                # 知识库级别：每个 KB 一个 collection
                for kb_id in kb_ids:
                    collection_name = f"kb_{kb_id}"
                    
                    success = await self._index_to_collection(
                        collection_name=collection_name,
                        doc_id=f"{doc_id}_kb{kb_id}",
                        text=text,
                        metadata={**metadata, "kb_id": kb_id},
                        kb_id=kb_id,
                        kb_config=kb_config,
                    )
                    
                    if success:
                        result["indexed_count"] += 1
                    else:
                        result["errors"].append(f"索引到 KB#{kb_id} 失败")
            
            elif collection_strategy == "template":
                # 模板级别：每个模板一个 collection
                collection_name = f"app_{app_id}_tpl_{template_id}"
                
                success = await self._index_to_collection(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    text=text,
                    metadata=metadata,
                    kb_id=kb_ids[0] if kb_ids else None,
                    kb_config=kb_config,
                )
                
                if success:
                    result["indexed_count"] = 1
                else:
                    result["errors"].append(f"索引到 template collection 失败")
            
            if result["errors"]:
                result["success"] = False
            
            logger.info(
                f"RAG AutoIndex: app={app_id}, template={template_id}, "
                f"data={data_id}, indexed={result['indexed_count']}, "
                f"errors={len(result['errors'])}"
            )
            
        except Exception as e:
            logger.error(f"RAG AutoIndex error: {e}", exc_info=True)
            result["success"] = False
            result["errors"].append(str(e))
        
        return result
    
    async def _index_to_collection(
        self,
        collection_name: str,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any],
        kb_id: Optional[int],
        kb_config: Dict[str, Any],
    ) -> bool:
        """
        索引文档到指定 collection
        """
        try:
            retriever = self._get_rag_retriever()
            
            success = await retriever.add_document(
                collection_name=collection_name,
                doc_id=doc_id,
                text=text,
                metadata=metadata,
                kb_id=kb_id,
                kb_config=kb_config,
            )
            
            if success:
                logger.debug(f"文档 {doc_id} 已索引到 {collection_name}")
            else:
                logger.warning(f"文档 {doc_id} 索引到 {collection_name} 失败")
            
            return success
            
        except Exception as e:
            logger.error(f"索引到 {collection_name} 异常: {e}")
            return False
    
    async def search_app_knowledge(
        self,
        app_id: int,
        query: str,
        top_k: int = 5,
        db: AsyncSession = None,
    ) -> List[Dict[str, Any]]:
        """
        在应用绑定的知识库中搜索
        
        Args:
            app_id: 应用ID
            query: 查询文本
            top_k: 返回结果数
            db: 数据库会话
        
        Returns:
            List[{"id", "text", "score", "metadata", "kb_id"}]
        """
        from app.modules.my_apps.models import Application
        
        if not db:
            return []
        
        result = await db.execute(
            select(Application).where(Application.id == app_id)
        )
        app = result.scalar_one_or_none()
        
        if not app:
            return []
        
        kb_ids = app.knowledge_base_ids or []
        kb_config = app.knowledge_config or {}
        
        if not kb_ids:
            return []
        
        collection_strategy = kb_config.get("collection_strategy", "app")
        retriever = self._get_rag_retriever()
        
        all_results = []
        
        if collection_strategy == "app":
            # 应用级别：搜索 app collection
            collection_name = f"app_{app_id}"
            results = await retriever.search(
                collection_name=collection_name,
                query=query,
                top_k=top_k,
                kb_id=kb_ids[0] if kb_ids else None,
                kb_config=kb_config,
            )
            all_results.extend(results)
        
        elif collection_strategy == "kb":
            # 知识库级别：搜索每个 KB collection
            for kb_id in kb_ids:
                collection_name = f"kb_{kb_id}"
                results = await retriever.search(
                    collection_name=collection_name,
                    query=query,
                    top_k=top_k // len(kb_ids) if len(kb_ids) > 1 else top_k,
                    kb_id=kb_id,
                    kb_config=kb_config,
                )
                for r in results:
                    r["kb_id"] = kb_id
                all_results.extend(results)
        
        elif collection_strategy == "template":
            # 模板级别：需要搜索所有相关模板 collection
            # 这需要知道应用绑定了哪些模板
            # 简化处理：搜索 app 级别
            collection_name = f"app_{app_id}"
            results = await retriever.search(
                collection_name=collection_name,
                query=query,
                top_k=top_k,
                kb_id=kb_ids[0] if kb_ids else None,
                kb_config=kb_config,
            )
            all_results.extend(results)
        
        # 按分数排序并返回 top_k
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results[:top_k]
    
    async def delete_form_index(
        self,
        app_id: int,
        template_id: int,
        data_id: int,
        db: AsyncSession,
    ) -> bool:
        """
        删除表单数据的索引（数据删除时调用）
        
        Note: 当前 RAGRetriever 没有 delete 方法，这是一个占位实现
        """
        # TODO: 实现 RAGRetriever.delete_document() 后完善
        logger.warning(
            f"RAG 删除索引功能未实现: app={app_id}, template={template_id}, data={data_id}"
        )
        return False


# 全局实例
_rag_autoindexer = None

def get_rag_autoindexer() -> RAGAutoIndexer:
    """获取 RAG 自动索引器实例（懒加载）"""
    global _rag_autoindexer
    if _rag_autoindexer is None:
        _rag_autoindexer = RAGAutoIndexer()
    return _rag_autoindexer
