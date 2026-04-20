"""
AI 能力具体实现
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import Counter

from app.core.ai_digital_base.gateway import ai_gateway
from app.core.ai_digital_base.capability_registry import AICapability, capability_registry
from app.models.workflow import Template
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


# ========== 表单设计能力 ==========

@capability_registry.register(AICapability.RECOMMEND_FIELDS)
async def recommend_fields(input_data: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
    """
    根据模块描述推荐字段
    Input: {"module_name": "客户信息", "description": "用于记录客户的基本信息和联系方式"}
    Output: {"fields": [{"name": "customer_name", "label": "客户名称", "type": "text", "required": true}, ...]}
    """
    module_name = input_data.get("module_name", "")
    description = input_data.get("description", "")
    
    system_prompt = """你是一个表单设计专家。根据模块名称和描述，推荐合适的字段列表。

输出 JSON 数组，每个字段包含：
- name: 字段标识（英文小写，下划线分隔）
- label: 字段标签（中文）
- type: 字段类型（text/number/date/select/radio/checkbox/textarea/email/phone/money）
- required: 是否必填（true/false）
- options: 如果是 select/radio/checkbox，提供选项数组

只输出 JSON 数组，不要其他内容。"""
    
    user_message = f"模块名称：{module_name}\n模块描述：{description}"
    
    response = await ai_gateway.chat_with_system_prompt(system_prompt, user_message, temperature=0.3)
    
    if "error" in response:
        return {"success": False, "error": response["error"]}
    
    try:
        content = response["content"].strip()
        # 提取 JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        fields = json.loads(content)
        if not isinstance(fields, list):
            fields = [fields]
        return {"success": True, "fields": fields}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON 解析失败: {str(e)}", "raw": content}


@capability_registry.register(AICapability.INFER_FIELD_TYPE)
async def infer_field_type(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据字段标签和样本数据推断字段类型
    Input: {"label": "手机号码", "sample_values": ["13812345678", "13987654321"]}
    Output: {"type": "phone", "confidence": 0.95}
    """
    label = input_data.get("label", "")
    sample_values = input_data.get("sample_values", [])
    
    # 先使用规则匹配
    type_rules = {
        "phone": [r'^1[3-9]\d{9}$', r'^\d{11}$'],
        "email": [r'^[\w.-]+@[\w.-]+\.\w+$'],
        "date": [r'^\d{4}-\d{1,2}-\d{1,2}$', r'^\d{4}/\d{1,2}/\d{1,2}$'],
        "number": [r'^\d+$', r'^\d+\.\d+$'],
        "money": [r'^\d+(\.\d{1,2})?$'],
        "url": [r'^https?://']
    }
    
    label_lower = label.lower()
    for field_type, patterns in type_rules.items():
        for pattern in patterns:
            if any(re.match(pattern, str(v)) for v in sample_values[:5] if v):
                return {"type": field_type, "confidence": 0.9}
    
    # 关键词匹配
    keyword_map = {
        "phone": ["电话", "手机", "移动", "联系方式"],
        "email": ["邮箱", "邮件", "email"],
        "date": ["日期", "时间", "生日", "创建时间"],
        "number": ["数量", "金额", "价格", "单价", "总数"],
        "textarea": ["备注", "描述", "说明", "详情"],
        "select": ["类型", "状态", "分类", "等级", "性别"]
    }
    for field_type, keywords in keyword_map.items():
        if any(kw in label_lower for kw in keywords):
            return {"type": field_type, "confidence": 0.7}
    
    # 默认文本
    return {"type": "text", "confidence": 0.5}


@capability_registry.register(AICapability.TRANSLATE_TO_EN)
async def translate_to_en(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """将中文翻译为英文字段名"""
    text = input_data.get("text", "")
    
    if not text:
        return {"success": True, "name": "field"}
    
    # 常见映射
    common_map = {
        "姓名": "name", "名称": "name", "标题": "title",
        "编码": "code", "编号": "code", "电话": "phone",
        "手机": "mobile", "邮箱": "email", "地址": "address",
        "日期": "date", "时间": "time", "备注": "remark",
        "说明": "description", "金额": "amount", "数量": "quantity",
        "价格": "price", "单价": "unit_price", "状态": "status",
        "类型": "type", "分类": "category", "等级": "level"
    }
    
    if text in common_map:
        return {"success": True, "name": common_map[text]}
    
    # 调用 AI 翻译
    system_prompt = "将中文翻译为英文变量名（小写，下划线分隔），只输出结果，不要解释。"
    response = await ai_gateway.chat_with_system_prompt(system_prompt, text, temperature=0.1)
    
    if "error" in response:
        # 降级处理
        import re
        name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', text)
        name = re.sub(r'[\u4e00-\u9fa5]', '_', name).lower()
        name = re.sub(r'_+', '_', name).strip('_')
        if not name:
            name = "field"
        return {"success": True, "name": name}
    
    name = response["content"].strip().lower().replace(" ", "_")
    name = re.sub(r'[^a-z0-9_]', '', name)
    return {"success": True, "name": name or "field"}


# ========== 数据查询能力 ==========

@capability_registry.register(AICapability.NATURAL_LANGUAGE_QUERY)
async def natural_language_query(input_data: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
    """
    自然语言查询数据
    Input: {"query": "查询本月新增的客户", "template_id": 123}
    Output: {"sql": "SELECT * FROM ...", "data": [...], "explanation": "..."}
    """
    query = input_data.get("query", "")
    template_id = input_data.get("template_id")
    
    if not template_id:
        return {"success": False, "error": "缺少 template_id"}
    
    # 获取模板信息
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Template).where(Template.id == template_id))
        template = result.scalar_one_or_none()
        if not template:
            return {"success": False, "error": "模板不存在"}
        
        # 获取字段定义
        fields = []
        for mod in template.modules or []:
            for f in mod.get("fields", []):
                fields.append({"name": f.get("name"), "label": f.get("label"), "type": f.get("type")})
        
        table_name = template.config.get("table_name", f"form_data_{template_id}")
        
        # 构建提示词，让 AI 生成 SQL
        system_prompt = f"""你是一个数据查询专家。根据用户的自然语言查询，生成 SQL 语句。

表名：{table_name}
表结构：
{json.dumps(fields, ensure_ascii=False, indent=2)}

只输出 SQL 语句，不要其他内容。使用参数化查询占位符 :value。
示例：SELECT * FROM {table_name} WHERE created_at >= date('now', '-30 day')
"""
        
        response = await ai_gateway.chat_with_system_prompt(system_prompt, query, temperature=0.1)
        
        if "error" in response:
            return {"success": False, "error": response["error"]}
        
        sql = response["content"].strip()
        # 清理 SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        # 执行查询
        from sqlalchemy import text
        try:
            result = await db.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            return {"success": True, "sql": sql, "data": data, "count": len(data)}
        except Exception as e:
            return {"success": False, "error": f"SQL 执行失败: {str(e)}", "sql": sql}


@capability_registry.register(AICapability.DETECT_ANOMALIES)
async def detect_anomalies(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    检测数据异常
    Input: {"data": [{"amount": 1000}, {"amount": 999999}], "field": "amount"}
    Output: {"anomalies": [{"index": 1, "value": 999999, "reason": "超出平均值3倍标准差"}]}
    """
    data = input_data.get("data", [])
    field = input_data.get("field", "")
    
    if not data or not field:
        return {"success": True, "anomalies": []}
    
    values = [row.get(field) for row in data if row.get(field) is not None]
    if len(values) < 3:
        return {"success": True, "anomalies": []}
    
    # 计算统计量
    import numpy as np
    arr = np.array([float(v) for v in values])
    mean = np.mean(arr)
    std = np.std(arr)
    
    anomalies = []
    for idx, row in enumerate(data):
        val = row.get(field)
        if val is not None:
            try:
                fval = float(val)
                if std > 0 and abs(fval - mean) > 3 * std:
                    anomalies.append({
                        "index": idx,
                        "value": val,
                        "reason": f"超出平均值 {mean:.2f} 超过3倍标准差"
                    })
                elif fval == 0 and mean > 0:
                    anomalies.append({
                        "index": idx,
                        "value": val,
                        "reason": "值为0，可能数据缺失"
                    })
            except:
                pass
    
    return {"success": True, "anomalies": anomalies, "statistics": {"mean": float(mean), "std": float(std)}}


# ========== 流程审批能力 ==========

@capability_registry.register(AICapability.RECOMMEND_APPROVERS)
async def recommend_approvers(input_data: Dict[str, Any], context: Dict = None) -> Dict[str, Any]:
    """
    智能推荐审批人
    Input: {"amount": 50000, "department": "销售部", "applicant_id": 1}
    Output: {"approvers": [{"user_id": 10, "name": "张三", "reason": "部门经理"}, ...]}
    """
    amount = input_data.get("amount", 0)
    department = input_data.get("department", "")
    
    # 基于规则的推荐
    approvers = []
    
    # 根据金额确定审批级别
    if amount > 50000:
        # 需要总经理审批
        approvers.append({"role": "总经理", "level": 3, "reason": f"金额 {amount} 超过 50000"})
    if amount > 10000:
        approvers.append({"role": "财务总监", "level": 2, "reason": f"金额 {amount} 超过 10000"})
    approvers.append({"role": "部门经理", "level": 1, "reason": "部门负责人审批"})
    
    # 从数据库查询实际用户（简化）
    # 实际应从用户表根据角色和部门查询
    
    return {"success": True, "approvers": approvers}


@capability_registry.register(AICapability.SUMMARIZE_APPROVAL)
async def summarize_approval(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    总结审批内容
    Input: {"content": "申请购买笔记本电脑一台，预算8000元，理由：工作需要"}
    Output: {"summary": "采购笔记本电脑，预算8000元", "risk_level": "low", "suggestions": ["建议批准"]}
    """
    content = input_data.get("content", "")
    
    if not content:
        return {"success": False, "error": "内容为空"}
    
    system_prompt = """你是一个审批助手。总结审批申请的核心内容，并给出审批建议。

输出 JSON：
{
    "summary": "一句话总结",
    "key_points": ["要点1", "要点2"],
    "risk_level": "low/medium/high",
    "suggestions": ["建议1", "建议2"]
}"""
    
    response = await ai_gateway.chat_with_system_prompt(system_prompt, content, temperature=0.2)
    
    if "error" in response:
        return {"success": False, "error": response["error"]}
    
    try:
        content = response["content"].strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        result = json.loads(content)
        return {"success": True, **result}
    except json.JSONDecodeError:
        return {"success": True, "summary": response["content"][:200], "risk_level": "medium"}


# ========== 仪表盘能力 ==========

@capability_registry.register(AICapability.RECOMMEND_CHART)
async def recommend_chart(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据数据集推荐图表类型
    Input: {"data_description": "月度销售额趋势", "data_sample": [{"month": "1月", "sales": 1000}, ...]}
    Output: {"chart_type": "line", "config": {...}, "reason": "适合展示趋势"}
    """
    data_description = input_data.get("data_description", "")
    data_sample = input_data.get("data_sample", [])
    
    system_prompt = """你是一个数据可视化专家。根据数据描述和样本，推荐最合适的图表类型。

输出 JSON：
{
    "chart_type": "line/bar/pie/scatter/table/kpi",
    "title": "推荐标题",
    "x_axis": "X轴字段名",
    "y_axis": ["Y轴字段名"],
    "reason": "推荐理由"
}"""
    
    user_message = f"数据描述：{data_description}\n数据样本：{json.dumps(data_sample[:3], ensure_ascii=False)}"
    
    response = await ai_gateway.chat_with_system_prompt(system_prompt, user_message, temperature=0.2)
    
    if "error" in response:
        # 降级推荐
        if "趋势" in data_description or "月份" in data_description:
            return {"chart_type": "line", "reason": "适合展示趋势"}
        elif "占比" in data_description or "分布" in data_description:
            return {"chart_type": "pie", "reason": "适合展示占比"}
        else:
            return {"chart_type": "bar", "reason": "适合对比"}
    
    try:
        content = response["content"].strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except:
        return {"chart_type": "line", "reason": "默认推荐"}


@capability_registry.register(AICapability.GENERATE_INSIGHT)
async def generate_insight(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成数据洞察
    Input: {"data_summary": {"total": 1000, "avg": 50, "trend": "上升"}, "template_name": "销售订单"}
    Output: {"insights": ["总销售额1000元，较上月增长15%", "平均客单价50元，处于健康水平"], "suggestions": ["建议加强高价值客户维护"]}
    """
    data_summary = input_data.get("data_summary", {})
    template_name = input_data.get("template_name", "")
    
    system_prompt = """你是一个数据分析师。根据数据摘要，生成 3-5 条关键洞察和行动建议。

输出 JSON：
{
    "insights": ["洞察1", "洞察2", ...],
    "suggestions": ["建议1", "建议2", ...],
    "summary": "一句话总结"
}"""
    
    user_message = f"模板名称：{template_name}\n数据摘要：{json.dumps(data_summary, ensure_ascii=False)}"
    
    response = await ai_gateway.chat_with_system_prompt(system_prompt, user_message, temperature=0.3)
    
    if "error" in response:
        return {"insights": ["数据已加载，可进一步分析"], "suggestions": ["配置更多图表"]}
    
    try:
        content = response["content"].strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except:
        return {"insights": [response["content"][:200]], "suggestions": []}