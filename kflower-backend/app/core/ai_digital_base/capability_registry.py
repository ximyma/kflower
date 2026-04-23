"""
AI 能力注册中心 - 统一管理所有 AI 能力
"""
from typing import Dict, Any, Callable, Optional
from enum import Enum
import inspect
import logging

logger = logging.getLogger(__name__)


class AICapability(str, Enum):
    """AI 能力枚举"""
    # 表单设计
    RECOMMEND_FIELDS = "recommend_fields"
    INFER_FIELD_TYPE = "infer_field_type"
    GENERATE_DEFAULT_VALUE = "generate_default_value"
    
    # 数据查询
    NATURAL_LANGUAGE_QUERY = "natural_language_query"
    DETECT_ANOMALIES = "detect_anomalies"
    GENERATE_REPORT_SUMMARY = "generate_report_summary"
    
    # 流程审批
    RECOMMEND_APPROVERS = "recommend_approvers"
    SUMMARIZE_APPROVAL = "summarize_approval"
    OPTIMIZE_WORKFLOW = "optimize_workflow"
    
    # ===== AI 审批能力（升级方案 4.2） =====
    AI_APPROVE = "ai_approve"           # AI 自动审批
    AI_CLASSIFY = "ai_classify"         # AI 内容分类
    AI_SUMMARIZE_WORKFLOW = "ai_summarize_workflow"  # 总结流程执行情况
    
    # 仪表盘
    RECOMMEND_CHART = "recommend_chart"
    GENERATE_INSIGHT = "generate_insight"
    PREDICT_TREND = "predict_trend"
    
    # 应用搭建
    GENERATE_APP_FROM_DESC = "generate_app_from_desc"
    GENERATE_TEMPLATE_FROM_DESC = "generate_template_from_desc"
    GENERATE_WORKFLOW_FROM_DESC = "generate_workflow_from_desc"
    
    # 辅助功能
    TRANSLATE_TO_EN = "translate_to_en"
    SUMMARIZE_TEXT = "summarize_text"
    EXTRACT_KEYWORDS = "extract_keywords"


class AICapabilityRegistry:
    """AI 能力注册表"""
    
    def __init__(self):
        self._handlers: Dict[AICapability, Callable] = {}
    
    def register(self, capability: AICapability):
        """装饰器：注册能力处理器"""
        def decorator(func: Callable):
            self._handlers[capability] = func
            logger.info(f"Registered AI capability: {capability.value}")
            return func
        return decorator
    
    def get_handler(self, capability: AICapability) -> Optional[Callable]:
        return self._handlers.get(capability)
    
    async def execute(
        self, 
        capability: AICapability, 
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行能力"""
        handler = self.get_handler(capability)
        if not handler:
            return {"success": False, "error": f"Capability {capability.value} not registered"}
        
        # 检查签名，决定是否传递 context
        sig = inspect.signature(handler)
        if len(sig.parameters) == 2:
            return await handler(input_data, context)
        else:
            return await handler(input_data)


# 全局实例
capability_registry = AICapabilityRegistry()


# ===== AI 审批能力处理器（升级方案 4.2） =====

@capability_registry.register(AICapability.AI_APPROVE)
async def handle_ai_approve(input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    AI 自动审批处理器
    
    Args:
        input_data: {
            "action": "approve" | "review",
            "context": {
                "applicant": str,
                "amount": float,
                "reason": str,
                "history": list,
                "rules": list
            },
            "knowledge_base_id": int (optional)
        }
    
    Returns:
        {
            "decision": "approve" | "reject" | "escalate",
            "opinion": str,
            "confidence": float,
            "suggestion": str (for review mode),
            "risk_level": "low" | "medium" | "high"
        }
    """
    from app.core.ai_digital_base.gateway import ai_gateway
    
    action = input_data.get("action", "approve")
    ctx = input_data.get("context", {})
    
    amount = ctx.get("amount", 0)
    reason = ctx.get("reason", "")
    applicant = ctx.get("applicant", "")
    rules = ctx.get("rules", [])
    
    # 构建 AI 提示词
    system_prompt = """你是一个智能审批助手。根据提供的申请信息，做出审批决策。

审批规则：
1. 金额超过 10000 需要谨慎评估
2. 申请理由不充分（少于10字）应拒绝或要求补充
3. 涉及敏感关键词（如"紧急"、"加急"）需要升级人工审批

输出格式（JSON）：
{
    "decision": "approve|reject|escalate",
    "confidence": 0.0-1.0,
    "opinion": "审批意见",
    "risk_level": "low|medium|high",
    "suggestion": "改进建议（仅review模式）"
}"""

    user_prompt = f"""申请人: {applicant}
金额: {amount}
申请理由: {reason}
审批规则: {rules}

请做出审批决策。"""

    try:
        # 调用 AI 网关
        response = await ai_gateway.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        if "error" in response:
            # AI 调用失败，返回 escalate 让人工处理
            return {
                "decision": "escalate",
                "opinion": f"AI 服务异常: {response.get('error', 'unknown')}",
                "confidence": 0.0,
                "risk_level": "high",
                "suggestion": "请人工审核"
            }
        
        content = response.get("content", "")
        
        # 尝试解析 JSON 响应
        import json
        import re
        
        # 提取 JSON 部分
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "decision": result.get("decision", "escalate"),
                    "opinion": result.get("opinion", ""),
                    "confidence": float(result.get("confidence", 0.5)),
                    "risk_level": result.get("risk_level", "medium"),
                    "suggestion": result.get("suggestion", "")
                }
            except json.JSONDecodeError:
                pass
        
        # 无法解析 JSON，根据关键词判断
        content_lower = content.lower()
        if "approve" in content_lower or "通过" in content_lower or "同意" in content_lower:
            decision = "approve"
            confidence = 0.8
        elif "reject" in content_lower or "拒绝" in content_lower or "不同意" in content_lower:
            decision = "reject"
            confidence = 0.8
        else:
            decision = "escalate"
            confidence = 0.5
        
        return {
            "decision": decision,
            "opinion": content[:200],
            "confidence": confidence,
            "risk_level": "medium",
            "suggestion": ""
        }
        
    except Exception as e:
        logger.error(f"AI 审批处理异常: {e}")
        return {
            "decision": "escalate",
            "opinion": f"处理异常: {str(e)}",
            "confidence": 0.0,
            "risk_level": "high",
            "suggestion": "请人工审核"
        }


@capability_registry.register(AICapability.AI_CLASSIFY)
async def handle_ai_classify(input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    AI 内容分类处理器
    
    Args:
        input_data: {
            "content": str,
            "categories": list[str]
        }
    
    Returns:
        {
            "category": str,
            "confidence": float,
            "reasoning": str
        }
    """
    from app.core.ai_digital_base.gateway import ai_gateway
    
    content = input_data.get("content", "")
    categories = input_data.get("categories", [])
    
    if not categories:
        return {
            "category": "",
            "confidence": 0.0,
            "reasoning": "未提供分类选项"
        }
    
    # 构建提示词
    categories_str = "\n".join([f"- {c}" for c in categories])
    
    system_prompt = f"""你是一个内容分类助手。根据提供的内容，选择最合适的分类。

可选分类：
{categories_str}

输出格式（JSON）：
{{
    "category": "选择的分类",
    "confidence": 0.0-1.0,
    "reasoning": "分类理由"
}}"""

    user_prompt = f"""请对以下内容进行分类：

{content[:1000]}  # 限制长度

请输出 JSON 格式的分类结果。"""

    try:
        response = await ai_gateway.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        
        if "error" in response:
            # 返回第一个分类作为默认
            return {
                "category": categories[0] if categories else "",
                "confidence": 0.0,
                "reasoning": f"AI 服务异常: {response.get('error', 'unknown')}"
            }
        
        resp_content = response.get("content", "")
        
        # 尝试解析 JSON
        import json
        import re
        
        json_match = re.search(r'\{[^}]+\}', resp_content, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                category = result.get("category", "")
                # 确保分类在选项中
                if category not in categories:
                    category = categories[0] if categories else ""
                return {
                    "category": category,
                    "confidence": float(result.get("confidence", 0.5)),
                    "reasoning": result.get("reasoning", "")
                }
            except json.JSONDecodeError:
                pass
        
        # 无法解析，根据关键词匹配
        resp_lower = resp_content.lower()
        for cat in categories:
            if cat.lower() in resp_lower:
                return {
                    "category": cat,
                    "confidence": 0.6,
                    "reasoning": "基于关键词匹配"
                }
        
        # 默认返回第一个分类
        return {
            "category": categories[0] if categories else "",
            "confidence": 0.5,
            "reasoning": "默认分类"
        }
        
    except Exception as e:
        logger.error(f"AI 分类处理异常: {e}")
        return {
            "category": categories[0] if categories else "",
            "confidence": 0.0,
            "reasoning": f"处理异常: {str(e)}"
        }