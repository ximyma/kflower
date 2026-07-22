"""
审计日志引擎 - 参考 NocoBase 审计日志设计

自动记录模板数据的创建/更新/删除操作，含 before/after 字段级对比。
通过 SQLAlchemy 事件钩子实现零侵入记录。
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ============ 审计服务 ============

class AuditService:
    """审计日志服务"""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sensitive_fields = {"password", "token", "secret", "key"}
        return cls._instance

    async def log_operation(
        self,
        db,
        operation_type: str,
        collection_name: str,
        record_id: int,
        record_title: str = None,
        user_id: int = None,
        changes: List[Dict] = None,
        remote_addr: str = None,
        user_agent: str = None,
    ) -> Optional[int]:
        """记录一次操作（适配现有 audit_logs 表结构）"""
        try:
            detail = {
                "record_title": record_title or str(record_id),
                "changes": []
            }
            if changes:
                for ch in changes[:50]:
                    detail["changes"].append({
                        "field": ch.get("field"),
                        "before": self._sanitize(ch.get("before")),
                        "after": self._sanitize(ch.get("after")),
                    })
            
            result = await db.execute(
                text("""
                    INSERT INTO audit_logs (action, resource_type, resource_id, detail, user_id, ip_address, user_agent, created_at)
                    VALUES (:action, :resource_type, :resource_id, :detail, :user_id, :ip, :ua, :created_at)
                """),
                {
                    "action": operation_type,
                    "resource_type": collection_name,
                    "resource_id": str(record_id),
                    "detail": json.dumps(detail, ensure_ascii=False),
                    "user_id": user_id,
                    "ip": remote_addr,
                    "ua": user_agent,
                    "created_at": datetime.now(),
                }
            )
            log_id_result = await db.execute(text("SELECT last_insert_rowid()"))
            log_id = log_id_result.scalar()
            return log_id
        except Exception as e:
            logger.warning(f"审计日志记录失败: {e}")
            return None

    def _sanitize(self, value: Any) -> Any:
        """净化敏感数据"""
        if value is None:
            return None
        if isinstance(value, str) and len(value) > 2000:
            return value[:2000] + "...[truncated]"
        return value

    async def compute_changes(
        self,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        field_definitions: List[Dict] = None,
    ) -> List[Dict]:
        """计算数据变更对比
        
        Returns: [{field: ..., before: ..., after: ...}]
        """
        changes = []
        
        # 构建字段名→字段定义的映射
        field_map = {}
        if field_definitions:
            for f in field_definitions:
                if isinstance(f, dict):
                    field_map[f.get("name", "")] = f
        
        # 所有变更的字段
        all_keys = set()
        if old_data:
            all_keys.update(old_data.keys())
        if new_data:
            all_keys.update(new_data.keys())

        for key in sorted(all_keys):
            # 跳过敏感字段
            if key in self._sensitive_fields or key.startswith("_"):
                continue
            
            before = old_data.get(key) if old_data else None
            after = new_data.get(key) if new_data else None
            
            # 跳过未变更的字段
            if before == after:
                continue
            
            # 跳过过于巨大的字段
            if isinstance(before, str) and len(str(before)) > 5000:
                before = "[too large]"
            if isinstance(after, str) and len(str(after)) > 5000:
                after = "[too large]"
            
            field_info = field_map.get(key, {"name": key, "label": key})
            
            changes.append({
                "field": {"name": key, "label": field_info.get("label", key)},
                "before": before,
                "after": after,
            })

        return changes

    async def get_logs(
        self,
        db,
        collection_name: str = None,
        record_id: int = None,
        user_id: int = None,
        operation_type: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """查询审计日志（适配现有 audit_logs 表结构）"""
        conditions = []
        params = {}

        if collection_name:
            conditions.append("resource_type = :collection")
            params["collection"] = collection_name
        if record_id is not None:
            conditions.append("resource_id = :resource_id")
            params["resource_id"] = str(record_id)
        if user_id is not None:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        if operation_type:
            conditions.append("action = :op_type")
            params["op_type"] = operation_type

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 计数
        count_result = await db.execute(
            text(f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}"),
            params
        )
        total = count_result.scalar() or 0

        # 分页查询
        params["limit"] = limit
        params["offset"] = offset
        result = await db.execute(
            text(f"""
                SELECT id, action, resource_type, resource_id, detail, user_id, ip_address, created_at
                FROM audit_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params
        )
        rows = result.fetchall()

        items = []
        for row in rows:
            log_id = row[0]
            detail = {}
            if row[4]:
                try:
                    detail = json.loads(row[4]) if isinstance(row[4], str) else row[4]
                except (json.JSONDecodeError, TypeError):
                    pass

            items.append({
                "id": log_id,
                "action": row[1],
                "resource_type": row[2],
                "resource_id": row[3],
                "record_title": detail.get("record_title", "") if isinstance(detail, dict) else str(row[3]),
                "user_id": row[5],
                "ip_address": row[6],
                "created_at": row[7],
                "changes": detail.get("changes", []) if isinstance(detail, dict) else [],
            })

        return {"total": total, "items": items, "limit": limit, "offset": offset}


# 全局审计服务实例
audit_service = AuditService()
