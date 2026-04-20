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