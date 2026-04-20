"""
AI 能力统一调用 API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.ai_digital_base.capability_registry import AICapability, capability_registry
from app.core.ai_digital_base.gateway import ai_gateway
from app.models.user import User
from app.models.ai import AIUsageLog
from app.schemas.schemas import BaseResponse
import time
import json

router = APIRouter(prefix="/ai/capability", tags=["AI能力"])


class AICapabilityRequest(BaseModel):
    capability: str  # 能力名称
    input_data: Dict[str, Any]
    model_override: Optional[str] = None
    provider_override: Optional[str] = None


@router.post("/execute")
async def execute_capability(
    request: AICapabilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行 AI 能力"""
    start_time = time.time()
    
    try:
        capability = AICapability(request.capability)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的能力: {request.capability}")
    
    # 可选：动态切换模型
    original_provider = None
    if request.model_override or request.provider_override:
        original_provider = ai_gateway.current_provider
        if request.provider_override:
            ai_gateway.set_current_provider(request.provider_override)
    
    try:
        result = await capability_registry.execute(
            capability, 
            request.input_data,
            context={"user_id": current_user.id, "db": db}
        )
    except Exception as e:
        result = {"success": False, "error": str(e)}
    finally:
        # 恢复原模型
        if original_provider:
            ai_gateway.set_current_provider(original_provider)
    
    # 记录使用日志
    duration_ms = int((time.time() - start_time) * 1000)
    usage_log = AIUsageLog(
        model_id=ai_gateway.current_provider or "unknown",
        provider=ai_gateway.current_provider,
        capability=request.capability,
        duration_ms=duration_ms,
        user_id=current_user.id
    )
    db.add(usage_log)
    await db.commit()
    
    return BaseResponse(
        success=result.get("success", False),
        message=result.get("error", "执行成功"),
        data=result
    )


@router.get("/list")
async def list_capabilities(current_user: User = Depends(get_current_user)):
    """列出所有可用的 AI 能力"""
    capabilities = [
        {"name": c.value, "description": get_capability_description(c)}
        for c in AICapability
    ]
    return BaseResponse(data=capabilities)


def get_capability_description(capability: AICapability) -> str:
    descriptions = {
        AICapability.RECOMMEND_FIELDS: "根据模块描述推荐字段",
        AICapability.NATURAL_LANGUAGE_QUERY: "自然语言查询数据",
        AICapability.DETECT_ANOMALIES: "检测数据异常",
        AICapability.RECOMMEND_APPROVERS: "智能推荐审批人",
        AICapability.SUMMARIZE_APPROVAL: "总结审批内容",
        AICapability.RECOMMEND_CHART: "推荐图表类型",
        AICapability.GENERATE_INSIGHT: "生成数据洞察",
        AICapability.TRANSLATE_TO_EN: "翻译为英文字段名",
        AICapability.INFER_FIELD_TYPE: "推断字段类型",
        AICapability.GENERATE_DEFAULT_VALUE: "生成默认值",
        AICapability.GENERATE_REPORT_SUMMARY: "生成报告摘要",
        AICapability.OPTIMIZE_WORKFLOW: "优化工作流程",
        AICapability.PREDICT_TREND: "预测趋势",
        AICapability.GENERATE_APP_FROM_DESC: "根据描述生成应用",
        AICapability.GENERATE_TEMPLATE_FROM_DESC: "根据描述生成模板",
        AICapability.GENERATE_WORKFLOW_FROM_DESC: "根据描述生成工作流",
        AICapability.SUMMARIZE_TEXT: "总结文本",
        AICapability.EXTRACT_KEYWORDS: "提取关键词",
    }
    return descriptions.get(capability, "AI 辅助功能")