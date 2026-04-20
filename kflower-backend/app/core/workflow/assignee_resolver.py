"""
审批人解析器
"""
from typing import List, Dict, Any
from sqlalchemy import select


class AssigneeResolver:
    async def resolve(self, node_config: Dict, variables: Dict, db) -> List[Dict]:
        """解析审批人列表"""
        assignee_type = node_config.get("assignee_type", "user")
        assignee_value = node_config.get("assignee_value")
        
        if assignee_type == "user":
            return [{"user_id": int(assignee_value)}]
        elif assignee_type == "role":
            # 根据角色查询用户
            from app.models.user import User, Role, UserRole
            stmt = select(User).join(UserRole).join(Role).where(Role.id == int(assignee_value))
            result = await db.execute(stmt)
            users = result.scalars().all()
            return [{"user_id": u.id} for u in users]
        elif assignee_type == "expression":
            # 表达式解析，如 {{applicant.manager_id}}
            resolved = self._resolve_variable(assignee_value, variables)
            return [{"user_id": int(resolved)}] if resolved else []
        elif assignee_type == "form_field":
            # 从表单字段获取
            field_name = assignee_value
            user_id = variables.get(field_name)
            return [{"user_id": user_id}] if user_id else []
        return []
    
    def _resolve_variable(self, expr: str, variables: Dict):
        # 简化实现
        if expr.startswith("{{") and expr.endswith("}}"):
            path = expr[2:-2].strip()
            parts = path.split('.')
            val = variables
            for p in parts:
                val = val.get(p) if isinstance(val, dict) else None
            return val
        return expr