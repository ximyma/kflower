"""
行级数据权限 - 模板变量解析与过滤器生成
参考 NocoBase ACL 的 parseJsonTemplate 和 data scope 机制

支持的模板变量：
  {{ ctx.current_user.id }}
  {{ ctx.current_user.organization_id }}
  {{ ctx.current_user.username }}
  {{ ctx.now }}

Scope 格式示例：
  {
    "key": "own",
    "scope": {"created_by": "{{ ctx.current_user.id }}"}
  }
"""
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ScopeFilterEngine:
    """数据范围过滤器引擎"""
    
    # 模板变量正则: {{ ctx.xxx.yyy }}
    _TEMPLATE_PATTERN = re.compile(r'\{\{\s*ctx\.(\w+(?:\.\w+)*)\s*\}\}')

    def resolve_scope(self, scope: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据范围过滤器中的模板变量
        
        Args:
            scope: 数据范围定义，如 {"created_by": "{{ ctx.current_user.id }}"}
            user_context: 用户上下文，如 {"id": 1, "organization_id": 5, "username": "admin"}
        
        Returns:
            解析后的过滤条件，如 {"created_by": 1}
        """
        if not scope:
            return {}
        
        resolved = {}
        for key, value in scope.items():
            if isinstance(value, str) and self._TEMPLATE_PATTERN.search(value):
                resolved[key] = self._resolve_value(value, user_context)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_scope(value, user_context)
            else:
                resolved[key] = value
        
        return resolved

    def _resolve_value(self, template: str, user_context: Dict) -> Any:
        """解析单个值中的模板变量
        
        支持的变量路径：
          {{ ctx.id }}           → user_context['id']
          {{ ctx.username }}     → user_context['username']
          {{ ctx.current_user.id }} → 兼容写法，同 ctx.id
          {{ ctx.now }}          → 当前时间
        """
        def replace_var(match):
            path = match.group(1)
            
            # 去掉 ctx. 前缀
            clean_path = path
            if clean_path.startswith('ctx.'):
                clean_path = clean_path[4:]
            
            # 简化：current_user.xxx → xxx（兼容不同命名）
            if clean_path.startswith('current_user.'):
                clean_path = clean_path[13:]
            
            # now 特殊处理
            if clean_path == 'now':
                return datetime.now().isoformat()
            
            # 直接查找
            val = user_context.get(clean_path)
            if val is not None:
                return str(val)
            
            # 尝试嵌套查找
            parts = clean_path.split('.')
            val = user_context
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p)
                else:
                    return 'null'
            
            return str(val) if val is not None else 'null'
        
        result = self._TEMPLATE_PATTERN.sub(replace_var, template)
        
        # 类型转换
        if result == 'null':
            return None
        if result.lstrip('-').isdigit():
            return int(result)
        if result.lower() in ('true', 'false'):
            return result.lower() == 'true'
        return result

    def apply_scope_to_query(self, query, scope: Dict, db_model) -> Any:
        """将 scope 过滤器应用到 SQLAlchemy 查询
        
        注意：这是一个简化实现，应在安全环境中使用
        """
        for field, value in scope.items():
            if hasattr(db_model, field):
                column = getattr(db_model, field)
                query = query.where(column == value)
        return query

    def get_user_data_scope(
        self,
        user_context: Dict[str, Any],
        db,
        collection_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """获取用户的数据范围过滤器
        
        Args:
            user_context: 用户上下文 (id, role_id, organization_id, ...)
            db: 数据库会话
            collection_name: 集合/表名
        
        Returns:
            解析后的过滤条件，如 {"created_by": 1}
        """
        try:
            from sqlalchemy import select
            from app.models.permission import DataPermission
            
            # 查询用户角色的数据权限
            role_id = user_context.get("role_id")
            if not role_id:
                return None
            
            result = db.execute(
                select(DataPermission).where(
                    DataPermission.role_id == role_id,
                    DataPermission.is_active == True
                )
            )
            data_perms = result.scalars().all()
            
            if not data_perms:
                return None
            
            # 合并所有规则（策略）
            merged_scope = {}
            for perm in data_perms:
                rules = perm.rules or []
                for rule in rules:
                    if isinstance(rule, dict):
                        scope = rule.get("scope", {})
                        if scope:
                            resolved = self.resolve_scope(scope, user_context)
                            merged_scope.update(resolved)
            
            return merged_scope if merged_scope else None
            
        except Exception as e:
            logger.warning(f"获取数据范围失败: {e}")
            return None


# 全局实例
scope_filter_engine = ScopeFilterEngine()
