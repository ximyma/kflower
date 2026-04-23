"""
通知 API 端点
提供系统通知发送功能和通知模板管理
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.notification_template import NotificationTemplate
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/notifications", tags=["通知"])


# ============ Schemas ============

class NotificationSendRequest(BaseModel):
    user_id: Optional[int] = None
    message: str
    channel: str = "system"  # system | email | sms


class NotificationTemplateCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    channels: List[str] = ["system"]
    subject: Optional[str] = None
    content: str
    category: str = "general"
    event_type: Optional[str] = None
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    channels: Optional[List[str]] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    event_type: Optional[str] = None
    is_active: Optional[bool] = None


class SendWithTemplateRequest(BaseModel):
    template_id: int
    user_ids: List[int]  # 接收人ID列表
    variables: Optional[dict] = None  # 模板变量 {title, applicant, status, ...}
    channels: Optional[List[str]] = None  # 覆盖模板默认渠道


# ============ 原有 API ============

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
        {"id": "wecom", "name": "企业微信", "icon": "ChatDotRound"},
        {"id": "dingtalk", "name": "钉钉", "icon": "ChatDotRound"},
    ])


# ============ 通知模板 CRUD ============

@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
    event_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取通知模板列表"""
    query = select(NotificationTemplate)
    
    if category:
        query = query.where(NotificationTemplate.category == category)
    if event_type:
        query = query.where(NotificationTemplate.event_type == event_type)
    if is_active is not None:
        query = query.where(NotificationTemplate.is_active == is_active)
    
    query = query.order_by(NotificationTemplate.created_at.desc())
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return BaseResponse(data=[{
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "description": t.description,
        "channels": t.channels or ["system"],
        "subject": t.subject,
        "content": t.content,
        "category": t.category,
        "event_type": t.event_type,
        "is_system": t.is_system,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in templates])


@router.post("/templates")
async def create_template(
    request: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建通知模板"""
    # 检查编码唯一性
    if request.code:
        existing_query = select(NotificationTemplate).where(
            NotificationTemplate.code == request.code
        )
        result = await db.execute(existing_query)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="模板编码已存在")
    
    template = NotificationTemplate(
        name=request.name,
        code=request.code,
        description=request.description,
        channels=request.channels,
        subject=request.subject,
        content=request.content,
        category=request.category,
        event_type=request.event_type,
        is_active=request.is_active,
        created_by=current_user.id,
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return BaseResponse(message="模板创建成功", data={"id": template.id})


@router.get("/templates/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个通知模板"""
    query = select(NotificationTemplate).where(
        NotificationTemplate.id == template_id
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return BaseResponse(data={
        "id": template.id,
        "name": template.name,
        "code": template.code,
        "description": template.description,
        "channels": template.channels or ["system"],
        "subject": template.subject,
        "content": template.content,
        "category": template.category,
        "event_type": template.event_type,
        "is_system": template.is_system,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    })


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    request: NotificationTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新通知模板"""
    query = select(NotificationTemplate).where(
        NotificationTemplate.id == template_id
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 系统内置模板不允许修改
    if template.is_system:
        raise HTTPException(status_code=403, detail="系统内置模板不允许修改")
    
    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    
    return BaseResponse(message="模板更新成功")


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除通知模板"""
    query = select(NotificationTemplate).where(
        NotificationTemplate.id == template_id
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 系统内置模板不允许删除
    if template.is_system:
        raise HTTPException(status_code=403, detail="系统内置模板不允许删除")
    
    await db.delete(template)
    await db.commit()
    
    return BaseResponse(message="模板删除成功")


# ============ 使用模板发送 ============

@router.post("/send-with-template")
async def send_with_template(
    request: SendWithTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """使用模板发送通知"""
    # 获取模板
    query = select(NotificationTemplate).where(
        NotificationTemplate.id == request.template_id
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已禁用")
    
    # 渲染模板内容
    content = template.content
    subject = template.subject or template.name
    
    # 替换变量
    variables = request.variables or {}
    for key, value in variables.items():
        content = content.replace(f"{{{key}}}", str(value))
        if subject:
            subject = subject.replace(f"{{{key}}}", str(value))
    
    # 确定发送渠道
    channels = request.channels or template.channels or ["system"]
    
    # TODO: 实际发送逻辑（邮件/短信/企微/钉钉）
    # 目前返回模拟结果
    results = []
    for user_id in request.user_ids:
        for channel in channels:
            results.append({
                "user_id": user_id,
                "channel": channel,
                "subject": subject,
                "content": content,
                "status": "sent",
            })
    
    return BaseResponse(
        message=f"通知已发送给 {len(request.user_ids)} 个用户",
        data={
            "template_id": template.id,
            "template_name": template.name,
            "channels": channels,
            "recipient_count": len(request.user_ids),
            "results": results,
        }
    )
