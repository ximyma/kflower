"""
公式引擎 - 为智能表单提供类 Excel 的公式/函数系统

支持：
- 数学函数：SUM, AVG, MAX, MIN, ROUND, ABS, FLOOR, CEIL, POWER, SQRT, MOD
- 字符串函数：LEN, CONCAT, LEFT, RIGHT, MID, UPPER, LOWER, TRIM, REPLACE, CONTAINS
- 日期函数：TODAY, NOW, YEAR, MONTH, DAY, DATEDIFF, DATE_FORMAT
- 逻辑函数：IF, AND, OR, NOT, ISNULL, ISEMPTY, SWITCH
- 统计函数（跨行聚合）：SUMIF, COUNTIF, AVGIF

表达式示例：
  {单价} * {数量}                          → 自动计算总价
  SUM({明细。金额})                         → 子表金额求和
  IF({年龄} >= 18, "成年", "未成年")       → 条件判断
  ROUND({金额} * 0.13, 2)                 → 保留两位小数
  DATEDIFF({结束日期}, {开始日期})         → 日期差（天）
  CONCAT({姓名}, "-", {工号})             → 字符串拼接
"""

import ast
import math
import re
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


# ============ 内置函数注册 ============

class FormulaFunctions:
    """内置函数实现"""

    # ---- 数学函数 ----
    @staticmethod
    def SUM(*args):
        vals = []
        for a in args:
            if isinstance(a, (list, tuple)):
                vals.extend(a)
            else:
                vals.append(a)
        return sum(float(v) for v in vals if v is not None and str(v).strip() != '')

    @staticmethod
    def AVG(*args):
        vals = []
        for a in args:
            if isinstance(a, (list, tuple)):
                vals.extend(a)
            else:
                vals.append(a)
        nums = [float(v) for v in vals if v is not None and str(v).strip() != '']
        return sum(nums) / len(nums) if nums else 0

    @staticmethod
    def MAX(*args):
        vals = []
        for a in args:
            if isinstance(a, (list, tuple)):
                vals.extend(a)
            else:
                vals.append(a)
        nums = [float(v) for v in vals if v is not None and str(v).strip() != '']
        return max(nums) if nums else 0

    @staticmethod
    def MIN(*args):
        vals = []
        for a in args:
            if isinstance(a, (list, tuple)):
                vals.extend(a)
            else:
                vals.append(a)
        nums = [float(v) for v in vals if v is not None and str(v).strip() != '']
        return min(nums) if nums else 0

    @staticmethod
    def ROUND(value, digits=2):
        try:
            return round(float(value), int(digits))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def ABS(value):
        try:
            return abs(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def FLOOR(value):
        try:
            return math.floor(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def CEIL(value):
        try:
            return math.ceil(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def POWER(base, exp):
        try:
            return pow(float(base), float(exp))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def SQRT(value):
        try:
            return math.sqrt(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def MOD(value, divisor):
        try:
            return float(value) % float(divisor)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0

    # ---- 字符串函数 ----
    @staticmethod
    def LEN(value):
        return len(str(value)) if value is not None else 0

    @staticmethod
    def CONCAT(*args):
        return ''.join(str(a) for a in args if a is not None)

    @staticmethod
    def LEFT(value, n):
        s = str(value) if value is not None else ''
        return s[:int(n)]

    @staticmethod
    def RIGHT(value, n):
        s = str(value) if value is not None else ''
        return s[-int(n):]

    @staticmethod
    def MID(value, start, length):
        s = str(value) if value is not None else ''
        return s[int(start) - 1:int(start) - 1 + int(length)]

    @staticmethod
    def UPPER(value):
        return str(value).upper() if value is not None else ''

    @staticmethod
    def LOWER(value):
        return str(value).lower() if value is not None else ''

    @staticmethod
    def TRIM(value):
        return str(value).strip() if value is not None else ''

    @staticmethod
    def REPLACE(text, old, new):
        return str(text).replace(str(old), str(new)) if text is not None else ''

    @staticmethod
    def CONTAINS(text, substr):
        return str(substr) in str(text) if text is not None else False

    # ---- 逻辑函数 ----
    @staticmethod
    def IF(condition, true_val, false_val=''):
        return true_val if condition else false_val

    @staticmethod
    def AND(*args):
        return all(bool(a) for a in args)

    @staticmethod
    def OR(*args):
        return any(bool(a) for a in args)

    @staticmethod
    def NOT(value):
        return not bool(value)

    @staticmethod
    def ISNULL(value):
        return value is None

    @staticmethod
    def ISEMPTY(value):
        if value is None:
            return True
        return str(value).strip() == ''

    @staticmethod
    def SWITCH(expr, *args):
        """SWITCH(表达式，值 1, 结果 1, 值 2, 结果 2, ..., 默认值)"""
        pairs = list(args)
        i = 0
        while i + 1 < len(pairs):
            if expr == pairs[i]:
                return pairs[i + 1]
            i += 2
        # 如果有奇数个参数，最后一个是默认值
        if len(pairs) % 2 == 1:
            return pairs[-1]
        return ''

    # ---- 日期函数 ----
    @staticmethod
    def TODAY():
        return date.today().strftime('%Y-%m-%d')

    @staticmethod
    def NOW():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def YEAR(date_str):
        try:
            d = _parse_date(date_str)
            return d.year if d else ''
        except Exception:
            return ''

    @staticmethod
    def MONTH(date_str):
        try:
            d = _parse_date(date_str)
            return d.month if d else ''
        except Exception:
            return ''

    @staticmethod
    def DAY(date_str):
        try:
            d = _parse_date(date_str)
            return d.day if d else ''
        except Exception:
            return ''

    @staticmethod
    def DATEDIFF(end_date_str, start_date_str, unit='day'):
        try:
            d1 = _parse_date(end_date_str)
            d2 = _parse_date(start_date_str)
            if d1 and d2:
                delta = d1 - d2
                if unit == 'day':
                    return delta.days
                elif unit == 'hour':
                    return delta.days * 24
                elif unit == 'month':
                    return (d1.year - d2.year) * 12 + (d1.month - d2.month)
                elif unit == 'year':
                    return d1.year - d2.year
            return 0
        except Exception:
            return 0

    @staticmethod
    def DATE_FORMAT(date_str, fmt='%Y-%m-%d'):
        try:
            d = _parse_date(date_str)
            return d.strftime(fmt) if d else ''
        except Exception:
            return ''

    # ---- 聚合函数（用于子表字段） ----
    @staticmethod
    def SUMIF(values, conditions, condition_values):
        """SUMIF(金额列表，条件列表，条件值) → 条件求和"""
        if not isinstance(values, list):
            return 0
        result = 0
        for i, v in enumerate(values):
            if i < len(conditions) and str(conditions[i]) == str(condition_values):
                try:
                    result += float(v)
                except (TypeError, ValueError):
                    pass
        return result

    @staticmethod
    def COUNTIF(values, condition_value):
        """COUNTIF(值列表，条件值) → 条件计数"""
        if not isinstance(values, list):
            return 0
        return sum(1 for v in values if str(v) == str(condition_value))

    @staticmethod
    def AVGIF(values, conditions, condition_value):
        """AVGIF(金额列表，条件列表，条件值) → 条件平均"""
        if not isinstance(values, list):
            return 0
        nums = []
        for i, v in enumerate(values):
            if i < len(conditions) and str(conditions[i]) == str(condition_value):
                try:
                    nums.append(float(v))
                except (TypeError, ValueError):
                    pass
        return sum(nums) / len(nums) if nums else 0


def _parse_date(date_str):
    """解析日期字符串"""
    if date_str is None:
        return None
    if isinstance(date_str, (date, datetime)):
        return date_str
    s = str(date_str).strip()
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ============ 公式引擎核心 ============

# 允许的 AST 节点类型（白名单安全）
ALLOWED_NODE_TYPES = {
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp,
    ast.Compare, ast.Call, ast.Constant, ast.Name,
    ast.IfExp, ast.List, ast.Tuple,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub, ast.Not,
    ast.And, ast.Or,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Load, ast.Store,
    # 支持子表字段引用：items.amt → Attribute
    ast.Attribute,
}


def _check_ast_safe(node) -> bool:
    """检查 AST 节点是否安全（防止代码注入）"""
    if type(node) not in ALLOWED_NODE_TYPES:
        return False
    for child in ast.iter_child_nodes(node):
        if not _check_ast_safe(child):
            return False
    return True


# 内置函数注册表
BUILTIN_FUNCTIONS: Dict[str, Any] = {}
for _name in dir(FormulaFunctions):
    if not _name.startswith('_'):
        BUILTIN_FUNCTIONS[_name] = getattr(FormulaFunctions, _name)


class FormulaEngine:
    """
    公式引擎
    
    用法：
        engine = FormulaEngine()
        
        # 计算公式
        result = engine.evaluate("{单价} * {数量}", {"单价": 10, "数量": 5})
        # → 50
        
        # 批量计算表单所有公式字段
        computed = engine.compute_form(form_data, field_definitions)
    """

    def __init__(self):
        self.functions = BUILTIN_FUNCTIONS.copy()

    def evaluate(self, formula: str, context: Dict[str, Any]) -> Any:
        """
        求值公式
        :param formula: 公式字符串，字段名用 {} 包裹，例如 "{单价} * {数量}"
        :param context: 字段值字典，例如 {"单价": 10, "数量": 5}
        :return: 计算结果
        """
        if not formula:
            return None

        try:
            # 1. 将 {字段名} 替换为 Python 安全变量名
            expr, var_map = self._preprocess(formula, context)

            # 2. 解析 AST
            tree = ast.parse(expr, mode='eval')

            # 3. 安全检查
            if not _check_ast_safe(tree):
                logger.warning(f"Formula contains unsafe AST nodes: {formula}")
                return None

            # 4. 编译并执行
            code = compile(tree, '<formula>', 'eval')
            result = eval(code, {'__builtins__': {}}, {**var_map, **self.functions})
            return result

        except ZeroDivisionError:
            return 0
        except Exception as e:
            logger.debug(f"Formula evaluation error: {formula!r}, error: {e}")
            return None

    def _preprocess(self, formula: str, context: Dict[str, Any]):
        """
        预处理：将 {字段名} 替换为安全的 Python 变量名，并准备变量字典
        同时支持子表字段引用：{明细。金额} → _sub_ 明细__金额
        """
        var_map = {}
        processed = formula

        # 匹配 {字段名} 或 {模块。字段名}
        pattern = re.compile(r'\{([^}]+)\}')
        matches = pattern.findall(formula)

        # 使用列表去重但保持顺序
        seen = set()
        unique_matches = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique_matches.append(m)

        for field_ref in unique_matches:
            # 生成安全变量名：使用字段的 Unicode 编码确保唯一性
            # 例如：单价 → _f_ 单价_5355_4EF7
            # 子表字段：items.amt → _f_items__amt_... (用__连接表名和字段名)
            unicode_parts = [hex(ord(c))[2:] for c in field_ref.replace('.', '__')]
            safe_name = '_f_' + field_ref.replace('.', '__') + '_' + '_'.join(unicode_parts)

            # 解析字段路径（支持子表：明细。金额）
            if '.' in field_ref:
                parts = field_ref.split('.', 1)
                sub_table_name = parts[0].strip()
                sub_field_name = parts[1].strip()
                # 从 context 中获取子表数据
                sub_data = context.get(sub_table_name, [])
                if isinstance(sub_data, list):
                    value = [row.get(sub_field_name) for row in sub_data if isinstance(row, dict)]
                else:
                    value = []
            else:
                value = context.get(field_ref)
                # 数字类型转换
                if isinstance(value, str) and value.strip():
                    try:
                        value = float(value)
                        if value == int(value):
                            value = int(value)
                    except ValueError:
                        pass

            var_map[safe_name] = value
            processed = processed.replace('{' + field_ref + '}', safe_name)

        return processed, var_map

    def compute_form(
        self,
        form_data: Dict[str, Any],
        field_definitions: List[Dict],
        sub_tables: Optional[Dict[str, List[Dict]]] = None
    ) -> Dict[str, Any]:
        """
        批量计算表单中所有公式字段

        :param form_data: 当前表单数据
        :param field_definitions: 字段定义列表
        :param sub_tables: 子表数据 {子表名：[{行数据}, ...]}
        :return: 包含公式计算结果的字典
        """
        result = {}

        # 构建上下文（合并表单数据和子表数据）
        context = dict(form_data)
        if sub_tables:
            context.update(sub_tables)

        for field in field_definitions:
            if not isinstance(field, dict):
                continue
            formula = field.get('formula')
            if not formula:
                continue
            field_name = field.get('name', '')
            if not field_name:
                continue

            value = self.evaluate(formula, context)
            if value is not None:
                result[field_name] = value
                # 将计算结果加入 context，以便后续字段可引用
                context[field_name] = value

        return result

    def validate_formula(self, formula: str) -> Dict[str, Any]:
        """
        验证公式语法
        :return: {"valid": bool, "error": str, "variables": [字段名列表]}
        """
        if not formula:
            return {"valid": False, "error": "公式不能为空", "variables": []}

        # 提取变量
        pattern = re.compile(r'\{([^}]+)\}')
        variables = pattern.findall(formula)

        # 用占位符替换，用数字 1 代替
        mock_context = {v: 1 for v in variables}
        try:
            expr, var_map = self._preprocess(formula, mock_context)
            tree = ast.parse(expr, mode='eval')
            if not _check_ast_safe(tree):
                return {"valid": False, "error": "公式包含不允许的语法", "variables": variables}
            return {"valid": True, "error": None, "variables": variables}
        except SyntaxError as e:
            return {"valid": False, "error": f"语法错误：{e.msg}", "variables": variables}
        except Exception as e:
            return {"valid": False, "error": str(e), "variables": variables}


# ============ 校验规则引擎 ============

class ValidationEngine:
    """
    字段校验规则引擎

    支持的校验规则类型：
    - required: 必填
    - min_value / max_value: 数值范围
    - min_length / max_length: 字符串长度
    - regex: 正则表达式
    - custom_formula: 自定义公式（返回 True/False）
    - in_list: 值必须在列表中
    - not_in_list: 值不能在列表中
    - date_range: 日期范围
    """

    def __init__(self):
        self.formula_engine = FormulaEngine()

    def validate_field(
        self,
        field_def: Dict,
        value: Any,
        form_data: Optional[Dict] = None
    ) -> List[str]:
        """
        校验单个字段，返回错误消息列表（空列表表示通过）
        """
        errors = []
        label = field_def.get('label', field_def.get('name', ''))
        validation_rules = field_def.get('validation_rules', [])

        if not validation_rules:
            # 向后兼容：检查老式 required
            if field_def.get('required') and _is_empty(value):
                errors.append(f"{label} 不能为空")
            return errors

        for rule in validation_rules:
            if not isinstance(rule, dict):
                continue
            rule_type = rule.get('type', '')
            msg = rule.get('message', '')

            if rule_type == 'required':
                if _is_empty(value):
                    errors.append(msg or f"{label} 不能为空")

            elif rule_type == 'min_value':
                if value is not None and not _is_empty(value):
                    try:
                        if float(value) < float(rule.get('value', 0)):
                            errors.append(msg or f"{label} 不能小于 {rule.get('value')}")
                    except (TypeError, ValueError):
                        pass

            elif rule_type == 'max_value':
                if value is not None and not _is_empty(value):
                    try:
                        if float(value) > float(rule.get('value', 0)):
                            errors.append(msg or f"{label} 不能大于 {rule.get('value')}")
                    except (TypeError, ValueError):
                        pass

            elif rule_type == 'min_length':
                if value is not None:
                    if len(str(value)) < int(rule.get('value', 0)):
                        errors.append(msg or f"{label} 长度不能少于 {rule.get('value')} 个字符")

            elif rule_type == 'max_length':
                if value is not None:
                    if len(str(value)) > int(rule.get('value', 0)):
                        errors.append(msg or f"{label} 长度不能超过 {rule.get('value')} 个字符")

            elif rule_type == 'regex':
                if value is not None and not _is_empty(value):
                    pattern = rule.get('value', '')
                    if pattern and not re.match(pattern, str(value)):
                        errors.append(msg or f"{label} 格式不正确")

            elif rule_type == 'in_list':
                allowed = rule.get('value', [])
                if value is not None and not _is_empty(value):
                    if str(value) not in [str(v) for v in allowed]:
                        errors.append(msg or f"{label} 的值不在允许列表中")

            elif rule_type == 'not_in_list':
                forbidden = rule.get('value', [])
                if value is not None and not _is_empty(value):
                    if str(value) in [str(v) for v in forbidden]:
                        errors.append(msg or f"{label} 的值不允许使用")

            elif rule_type == 'custom_formula':
                formula = rule.get('value', '')
                if formula and form_data is not None:
                    ctx = dict(form_data)
                    ctx[field_def.get('name', '')] = value
                    result = self.formula_engine.evaluate(formula, ctx)
                    if result is False or result == 0:
                        errors.append(msg or f"{label} 校验不通过")

        return errors

    def validate_form(
        self,
        field_definitions: List[Dict],
        form_data: Dict
    ) -> Dict[str, List[str]]:
        """
        校验整个表单，返回 {字段名：[错误消息，...]}
        """
        errors = {}
        for field in field_definitions:
            if not isinstance(field, dict):
                continue
            name = field.get('name', '')
            value = form_data.get(name)
            field_errors = self.validate_field(field, value, form_data)
            if field_errors:
                errors[name] = field_errors
        return errors


# ============ 条件显示/隐藏引擎 ============

class VisibilityEngine:
    """
    字段条件显示/隐藏引擎

    visibility_rule 格式：
    {
        "type": "formula",          # formula / simple
        "formula": "{身份} == '个人'",     # 公式模式
        # 或简单模式：
        "field": "身份",
        "operator": "eq",           # eq/neq/gt/lt/gte/lte/contains/in
        "value": "个人"
    }
    """

    def __init__(self):
        self.formula_engine = FormulaEngine()

    def is_visible(self, field_def: Dict, form_data: Dict) -> bool:
        """
        判断字段是否可见
        :return: True=可见，False=隐藏
        """
        rule = field_def.get('visibility_rule')
        if not rule:
            return True  # 无规则，默认可见

        if isinstance(rule, str):
            # 字符串格式：直接作为公式
            result = self.formula_engine.evaluate(rule, form_data)
            return bool(result)

        if not isinstance(rule, dict):
            return True

        rule_type = rule.get('type', 'simple')

        if rule_type == 'formula':
            formula = rule.get('formula', '')
            result = self.formula_engine.evaluate(formula, form_data)
            return bool(result)

        elif rule_type == 'simple':
            field = rule.get('field', '')
            operator = rule.get('operator', 'eq')
            expected = rule.get('value')
            actual = form_data.get(field)
            return _compare(actual, operator, expected)

        return True

    def compute_visibility(self, field_definitions: List[Dict], form_data: Dict) -> Dict[str, bool]:
        """
        批量计算所有字段的可见性
        :return: {字段名：bool}
        """
        result = {}
        for field in field_definitions:
            if isinstance(field, dict):
                name = field.get('name', '')
                result[name] = self.is_visible(field, form_data)
        return result


# ============ 级联选项引擎 ============

class CascadeEngine:
    """
    级联选项引擎

    cascade_source 格式（字段属性中）：
    {
        "parent_field": "省份",       # 父字段名
        "options_map": {              # 父字段值 → 子选项列表
            "广东": ["广州", "深圳", "东莞"],
            "浙江": ["杭州", "宁波", "温州"]
        }
    }
    """

    def get_options(self, field_def: Dict, form_data: Dict) -> List[str]:
        """根据表单数据获取字段的级联选项"""
        cascade = field_def.get('cascade_source')
        if not cascade:
            return field_def.get('options', []) or []

        parent_field = cascade.get('parent_field', '')
        options_map = cascade.get('options_map', {})

        parent_value = form_data.get(parent_field, '')
        return options_map.get(str(parent_value), [])

    def compute_all_options(self, field_definitions: List[Dict], form_data: Dict) -> Dict[str, List]:
        """批量计算所有字段的可用选项"""
        result = {}
        for field in field_definitions:
            if isinstance(field, dict):
                name = field.get('name', '')
                if field.get('cascade_source') or field.get('type') in ('select', 'radio', 'checkbox'):
                    result[name] = self.get_options(field, form_data)
        return result


# ============ 工具函数 ============

def _is_empty(value) -> bool:
    """判断值是否为空"""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _compare(actual, operator: str, expected) -> bool:
    """简单比较运算"""
    try:
        if operator == 'eq':
            return str(actual) == str(expected)
        elif operator == 'neq':
            return str(actual) != str(expected)
        elif operator == 'gt':
            return float(actual) > float(expected)
        elif operator == 'lt':
            return float(actual) < float(expected)
        elif operator == 'gte':
            return float(actual) >= float(expected)
        elif operator == 'lte':
            return float(actual) <= float(expected)
        elif operator == 'contains':
            return str(expected) in str(actual)
        elif operator == 'in':
            if isinstance(expected, list):
                return str(actual) in [str(v) for v in expected]
            return str(actual) == str(expected)
        elif operator == 'not_in':
            if isinstance(expected, list):
                return str(actual) not in [str(v) for v in expected]
            return str(actual) != str(expected)
        elif operator == 'is_empty':
            return _is_empty(actual)
        elif operator == 'not_empty':
            return not _is_empty(actual)
    except (TypeError, ValueError):
        pass
    return False


# ============ 全局实例 ============
formula_engine = FormulaEngine()
validation_engine = ValidationEngine()
visibility_engine = VisibilityEngine()
cascade_engine = CascadeEngine()
