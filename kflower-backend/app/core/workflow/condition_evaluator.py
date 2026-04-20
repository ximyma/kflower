"""
条件表达式求值器
支持 {{variable}} 表达式和简单逻辑运算
"""
import re
import json
from typing import Dict, Any


class ConditionEvaluator:
    """支持 {{variable}} 表达式和简单逻辑运算"""
    
    async def evaluate(self, expression: str, variables: Dict[str, Any]) -> bool:
        """求值表达式，如: {{amount}} > 1000 and {{status}} == 'approved'"""
        if not expression or expression == "true":
            return True
        if expression == "false":
            return False
        
        # 替换变量占位符
        resolved_expr = self._resolve_variables(expression, variables)
        try:
            # 安全求值
            return bool(eval(resolved_expr, {"__builtins__": {}}, {}))
        except Exception:
            return False
    
    async def render_expression(self, expr: str, variables: Dict[str, Any]) -> str:
        """渲染表达式，返回字符串"""
        return self._resolve_variables(expr, variables)
    
    def _resolve_variables(self, text: str, variables: Dict) -> str:
        """将 {{variable}} 替换为实际值"""
        def replace(match):
            var_path = match.group(1).strip()
            value = self._get_nested_value(variables, var_path)
            if isinstance(value, str):
                return f"'{value}'"
            elif isinstance(value, (int, float)):
                return str(value)
            elif value is None:
                return "None"
            elif isinstance(value, bool):
                return str(value)
            else:
                return json.dumps(value)
        
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        return re.sub(pattern, replace, text)
    
    def _get_nested_value(self, obj: Any, path: str):
        parts = path.split('.')
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            elif isinstance(obj, list):
                try:
                    idx = int(part)
                    obj = obj[idx] if idx < len(obj) else None
                except:
                    return None
            else:
                return None
        return obj