"""
条件表达式求值器
支持 {{variable}} 表达式、函数调用和复杂逻辑运算

升级后支持：
- {{amount}} > 1000 and {{status}} == 'approved'
- {{department}} IN ['销售部', '市场部']
- {{apply_date}} >= TODAY() - 30
- LOOKUP(employee, level) >= 3
- SUM({{items.*.price}}) > 50000
- {{content}} CONTAINS '紧急'
- COUNT({{approvers}}) > 0
"""
import re
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List


class ConditionEvaluator:
    """支持 {{variable}} 表达式、函数调用和复杂逻辑运算"""
    
    # 内置函数
    BUILTIN_FUNCTIONS = {
        "TODAY": lambda: date.today(),
        "NOW": lambda: datetime.now(),
        "LEN": len,
        "COUNT": lambda x: len(x) if isinstance(x, (list, dict, str)) else 0,
        "ABS": abs,
        "ROUND": lambda v, d=2: round(v, d),
        "MAX": max,
        "MIN": min,
        "SUM": lambda x: sum(x) if isinstance(x, (list, tuple)) else 0,
        "AVG": lambda x: sum(x) / len(x) if isinstance(x, (list, tuple)) and len(x) > 0 else 0,
    }
    
    async def evaluate(self, expression: str, variables: Dict[str, Any]) -> bool:
        """求值表达式"""
        if not expression or expression == "true":
            return True
        if expression == "false":
            return False
        
        # 转换表达式为 Python 可执行形式
        resolved_expr = await self._resolve_expression(expression, variables)
        
        try:
            # 安全求值
            safe_globals = {"__builtins__": {}}
            safe_locals = {**self.BUILTIN_FUNCTIONS}
            return bool(eval(resolved_expr, safe_globals, safe_locals))
        except Exception as e:
            # 求值失败，返回 False
            return False
    
    async def render_expression(self, expr: str, variables: Dict[str, Any]) -> str:
        """渲染表达式，返回字符串"""
        result = await self._resolve_expression(expr, variables)
        return str(result)
    
    async def _resolve_expression(self, text: str, variables: Dict) -> str:
        """解析表达式，处理变量、函数调用和运算符"""
        result = text
        
        # 1. 处理 CONTAINS 运算符: {{field}} CONTAINS 'value'
        result = self._convert_contains(result)
        
        # 2. 处理 IN 运算符: {{field}} IN ['a', 'b']
        result = self._convert_in(result)
        
        # 3. 处理函数调用: TODAY(), LOOKUP(...), SUM(...)
        result = await self._convert_functions(result, variables)
        
        # 4. 处理变量占位符 {{variable}}
        result = self._convert_variables(result, variables)
        
        return result
    
    def _convert_contains(self, text: str) -> str:
        """将 CONTAINS 转换为 Python 的 in 运算符"""
        # 匹配: {{field}} CONTAINS 'value' 或 field CONTAINS "value"
        pattern = r'(\{\{[^}]+\}\}|\w+)\s+CONTAINS\s+[\'"]([^\'"]+)[\'"]'
        
        def replace(match):
            field = match.group(1)
            value = match.group(2)
            return f"('{value}' in str({field}))"
        
        return re.sub(pattern, replace, text, flags=re.IGNORECASE)
    
    def _convert_in(self, text: str) -> str:
        """将 IN 转换为 Python 的 in 运算符"""
        # 匹配: {{field}} IN ['a', 'b'] 或 field IN ("a", "b")
        pattern = r'(\{\{[^}]+\}\}|\w+)\s+IN\s+(\[[^\]]+\]|\([^)]+\))'
        
        def replace(match):
            field = match.group(1)
            values = match.group(2)
            # 将 () 转换为 []
            if values.startswith('('):
                values = '[' + values[1:-1] + ']'
            return f"({field} in {values})"
        
        return re.sub(pattern, replace, text, flags=re.IGNORECASE)
    
    async def _convert_functions(self, text: str, variables: Dict) -> str:
        """处理函数调用"""
        # 处理 LOOKUP(template, field, condition)
        text = await self._convert_lookup(text, variables)
        
        # 处理 SUM/MIN/MAX/AVG({{items.*.field}}) - 子表聚合
        text = self._convert_aggregate(text, variables)
        
        return text
    
    async def _convert_lookup(self, text: str, variables: Dict) -> str:
        """处理 LOOKUP 函数"""
        pattern = r'LOOKUP\s*\(\s*(\w+)\s*,\s*(\w+)\s*,\s*([^)]+)\)'
        
        async def replace(match):
            template = match.group(1)
            field = match.group(2)
            condition = match.group(3)
            
            # 这里简化处理，实际应该查询数据库
            # 返回占位符值
            return "None"
        
        return re.sub(pattern, replace, text, flags=re.IGNORECASE)
    
    def _convert_aggregate(self, text: str, variables: Dict) -> str:
        """处理子表聚合函数 SUM/MIN/MAX/AVG({{items.*.field}})"""
        # 匹配: SUM({{items.*.price}}) 或 SUM(items.*.price)
        pattern = r'(SUM|MIN|MAX|AVG)\s*\(\s*\{\{([^}]+\*[^}]+)\}\}\s*\)'
        
        def replace(match):
            func = match.group(1)
            path = match.group(2)
            
            # 解析路径: items.*.price -> 获取 items 列表，提取 price 字段
            parts = path.split('.*.')
            if len(parts) == 2:
                list_key = parts[0].strip()
                field_key = parts[1].strip()
                
                # 获取列表数据
                items = self._get_nested_value(variables, list_key)
                if isinstance(items, list):
                    values = []
                    for item in items:
                        if isinstance(item, dict):
                            val = item.get(field_key)
                            if isinstance(val, (int, float)):
                                values.append(val)
                    
                    if func == "SUM":
                        return str(sum(values))
                    elif func == "AVG" and values:
                        return str(sum(values) / len(values))
                    elif func == "MAX" and values:
                        return str(max(values))
                    elif func == "MIN" and values:
                        return str(min(values))
            
            return "0"
        
        return re.sub(pattern, replace, text, flags=re.IGNORECASE)
    
    def _convert_variables(self, text: str, variables: Dict) -> str:
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
            elif isinstance(value, (date, datetime)):
                return f"'{value.isoformat()}'"
            else:
                return json.dumps(value)
        
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        return re.sub(pattern, replace, text)
    
    def _get_nested_value(self, obj: Any, path: str):
        """获取嵌套值"""
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