"""
通知 API 端点
提供系统通知发送功能
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/notifications", tags=["通知"])


class NotificationSendRequest(BaseModel):
    user_id: Optional[int] = None
    message: str
    channel: str = "system"  # system | email | sms


@router.post("/send")
async def send_notification(
    request: NotificationSendRequest,
    current_user: User = Depends(get_current_user),
):
    """
    发送通知（当前为日志记录，后续可扩展邮件/短信/WebSocket）
    """
    # 后续可接入：邮件服务、企业微信、钉钉、WebSocket 推送等
    # 目前记录到日志并返回成功
    return BaseResponse(
        message="通知已发送",
        data={
            "from": current_user.full_name or current_user.username,
            "to_user_id": request.user_id,
            "channel": request.channel,
            "message": request.message,
        }
    )


@router.get("/channels")
async def list_channels(
    current_user: User = Depends(get_current_user),
):
    """获取支持的发送渠道"""
    return BaseResponse(data=[
        {"id": "system", "name": "系统通知", "icon": "Bell"},
        {"id": "email", "name": "邮件", "icon": "Message"},
        {"id": "sms", "name": "短信", "icon": "Phone"},
    ])
