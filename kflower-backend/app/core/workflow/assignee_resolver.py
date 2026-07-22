"""
审批人解析器 - 增强版
支持前端设计器的所有审批人来源类型
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class AssigneeResolver:
    async def resolve(self, node_config: Dict, variables: Dict, db) -> List[Dict[str, Any]]:
        """解析审批人列表
        
        支持的 assignee_type:
        - user/specified: 指定用户 ID
        - role: 按角色查询用户
        - submitter: 发起人本人
        - department_manager: 部门主管
        - expression: 表达式解析 {{variable.path}}
        - form_field: 表单字段值
        - form_member_field: 表单成员字段（用户选择器）
        - form_department_field: 表单部门字段
        - all: 会签（多个审批人，可指定多人）
        - any: 或签（任意审批人）
        - self_select: 自选审批人
        """
        assignee_type = node_config.get("assignee_type", "user")
        assignee_value = node_config.get("assignee_value")
        assignee_config = node_config.get("assignee_config", {})
        
        # 统一处理前端不同的字段名
        assignees = node_config.get("assignees", [])
        if assignees and isinstance(assignees, list):
            # NocoBase 风格：直接从 assignees 列表获取
            return await self._resolve_from_assignees(assignees, variables, db)
        
        if assignee_type in ("user", "specified"):
            return await self._resolve_user(assignee_value, variables, db)
        elif assignee_type == "role":
            return await self._resolve_role(assignee_value, db)
        elif assignee_type == "submitter":
            return self._resolve_submitter(variables)
        elif assignee_type == "department_manager":
            return await self._resolve_department_manager(variables, db)
        elif assignee_type == "expression":
            return await self._resolve_expression(assignee_value, variables, db)
        elif assignee_type == "form_field":
            return self._resolve_form_field(assignee_value, variables)
        elif assignee_type == "form_member_field":
            return await self._resolve_form_member_field(assignee_value, variables, db)
        elif assignee_type == "form_department_field":
            return await self._resolve_form_department_field(assignee_value, variables, db)
        elif assignee_type in ("all", "any"):
            return await self._resolve_multi_assignee(assignee_config, variables, db)
        elif assignee_type == "self_select":
            return []  # 自选审批人，运行时由用户指定
        
        logger.warning(f"未知的 assignee_type: {assignee_type}, value={assignee_value}")
        return []
    
    async def _resolve_from_assignees(self, assignees: List, variables: Dict, db) -> List[Dict]:
        """从 assignees 列表解析（NocoBase 风格）"""
        result = []
        for a in assignees:
            if isinstance(a, dict):
                uid = a.get("user_id") or a.get("id")
                if uid:
                    result.append({"user_id": int(uid), "name": a.get("name", "")})
            elif isinstance(a, (int, str)):
                result.append({"user_id": int(a)})
        return result
    
    async def _resolve_user(self, value, variables: Dict, db) -> List[Dict]:
        """指定用户"""
        if isinstance(value, (int, str)):
            try:
                return [{"user_id": int(value)}]
            except (ValueError, TypeError):
                pass
        # value 可能是数组
        if isinstance(value, list):
            return [{"user_id": int(v)} for v in value]
        return []
    
    async def _resolve_role(self, role_id, db) -> List[Dict]:
        """根据角色查询用户"""
        from app.models.user import User
        try:
            stmt = select(User).where(
                User.role_id == int(role_id) if hasattr(User, 'role_id') else User.id > 0
            )
            result = await db.execute(stmt)
            users = result.scalars().all()
            return [{"user_id": u.id, "name": getattr(u, 'realname', str(u.id))} for u in users]
        except Exception as e:
            logger.warning(f"角色解析失败: {e}")
            return []
    
    def _resolve_submitter(self, variables: Dict) -> List[Dict]:
        """发起人本人"""
        starter_id = variables.get("starter_id") or variables.get("created_by")
        if starter_id:
            return [{"user_id": int(starter_id)}]
        return []
    
    async def _resolve_department_manager(self, variables: Dict, db) -> List[Dict]:
        """部门主管"""
        from app.models.user import User
        starter_id = variables.get("starter_id") or variables.get("created_by")
        if starter_id:
            try:
                stmt = select(User).where(User.id == int(starter_id))
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                if user and hasattr(user, 'manager_id') and user.manager_id:
                    return [{"user_id": user.manager_id}]
            except Exception as e:
                logger.warning(f"部门主管解析失败: {e}")
        return []
    
    async def _resolve_expression(self, expr: str, variables: Dict, db) -> List[Dict]:
        """表达式解析"""
        resolved = self._resolve_variable(expr, variables)
        if resolved:
            try:
                return [{"user_id": int(resolved)}]
            except (ValueError, TypeError):
                pass
        return []
    
    def _resolve_form_field(self, field_name: str, variables: Dict) -> List[Dict]:
        """从表单字段值获取"""
        if not field_name:
            return []
        user_id = variables.get(field_name)
        if user_id:
            try:
                return [{"user_id": int(user_id)}]
            except (ValueError, TypeError):
                pass
        return []
    
    async def _resolve_form_member_field(self, field_name: str, variables: Dict, db) -> List[Dict]:
        """表单成员字段（用户选择器组件）"""
        value = variables.get(field_name)
        if not value:
            return []
        # value 可能是单个ID或ID数组
        if isinstance(value, list):
            return [{"user_id": int(v)} for v in value]
        try:
            return [{"user_id": int(value)}]
        except (ValueError, TypeError):
            return []
    
    async def _resolve_form_department_field(self, field_name: str, variables: Dict, db) -> List[Dict]:
        """表单部门字段 - 获取部门下的所有用户"""
        from app.models.user import User
        dept_id = variables.get(field_name)
        if not dept_id:
            return []
        try:
            stmt = select(User).where(
                User.department_id == int(dept_id)
            )
            result = await db.execute(stmt)
            users = result.scalars().all()
            return [{"user_id": u.id} for u in users]
        except Exception as e:
            logger.warning(f"部门成员解析失败: {e}")
            return []
    
    async def _resolve_multi_assignee(self, config: Dict, variables: Dict, db) -> List[Dict]:
        """多审批人（会签/或签）"""
        assignees = config.get("assignees", [])
        if assignees:
            return await self._resolve_from_assignees(assignees, variables, db)
        # 回退：从 value 字段解析
        user_ids = config.get("user_ids", [])
        return [{"user_id": uid} for uid in user_ids]
    
    def _resolve_variable(self, expr: str, variables: Dict) -> Any:
        """解析变量表达式 {{path.to.field}}"""
        if not expr:
            return None
        if expr.startswith("{{") and expr.endswith("}}"):
            path = expr[2:-2].strip()
            parts = path.split('.')
            val = variables
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    return None
            return val
        return expr