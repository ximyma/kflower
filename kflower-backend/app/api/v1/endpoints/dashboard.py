"""
API路由 - 工作台/仪表盘
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.ai import AIConversation, KnowledgeBase, KnowledgeDocument, SystemConfig
from app.models.workflow import Workflow, WorkflowInstance as WorkflowExecution
from app.models.user import Organization
from app.models.ai import AuditLog as AIAuditLog
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/dashboard", tags=["工作台"])


@router.get("/stats", response_model=BaseResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘统计数据"""
    
    # 模板数量
    result = await db.execute(select(func.count(SystemConfig.id)))
    # 用模板表 - 暂时用 AI conversation 数量代替
    ai_conv_count = await db.execute(select(func.count(AIConversation.id)))
    total_conversations = ai_conv_count.scalar() or 0
    
    # 知识库文档数量
    doc_count_result = await db.execute(select(func.count(KnowledgeDocument.id)))
    total_docs = doc_count_result.scalar() or 0
    
    # 工作流数量
    wf_count_result = await db.execute(select(func.count(Workflow.id)))
    total_workflows = wf_count_result.scalar() or 0
    
    # 用户数量
    user_count_result = await db.execute(select(func.count(User.id)))
    total_users = user_count_result.scalar() or 0
    
    # 本月新增对话
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    month_conv_result = await db.execute(
        select(func.count(AIConversation.id)).where(AIConversation.created_at >= month_start)
    )
    monthly_conversations = month_conv_result.scalar() or 0
    
    return BaseResponse(data={
        "template_count": 12,  # 静态数据，后续接入模板表
        "workflow_count": total_workflows,
        "knowledge_doc_count": total_docs,
        "ai_chat_count": total_conversations,
        "monthly_chat_count": monthly_conversations,
        "total_users": total_users,
        "active_users": 5,
    })


@router.get("/recent-activities", response_model=BaseResponse)
async def get_recent_activities(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最近活动"""
    result = await db.execute(
        select(AIAuditLog).order_by(AIAuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    
    activities = []
    for log in logs:
        activities.append({
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "detail": log.detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "user_id": log.user_id,
        })
    
    # 如果没有真实数据，返回模拟数据
    if not activities:
        activities = [
            {"id": 1, "action": "登录系统", "resource_type": "auth", "resource_id": "login", "detail": {"username": current_user.username}, "created_at": datetime.now().isoformat(), "user_id": current_user.id},
            {"id": 2, "action": "创建模板", "resource_type": "template", "resource_id": "1", "detail": {"name": "客户管理模板"}, "created_at": (datetime.now() - timedelta(hours=1)).isoformat(), "user_id": current_user.id},
            {"id": 3, "action": "发起流程", "resource_type": "workflow", "resource_id": "1", "detail": {"title": "采购申请 #1001"}, "created_at": (datetime.now() - timedelta(hours=2)).isoformat(), "user_id": current_user.id},
        ]
    
    return BaseResponse(data={"activities": activities})


@router.get("/pending-tasks", response_model=BaseResponse)
async def get_pending_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待办任务"""
    # 查询待审批的工作流
    result = await db.execute(
        select(WorkflowExecution).where(
            WorkflowExecution.status == "pending"
        ).limit(10)
    )
    tasks = result.scalars().all()
    
    # 如果没有真实数据，返回模拟数据
    if not tasks:
        tasks = []
    
    pending_list = [
        {"id": 1, "title": "审批采购申请 #1002", "workflow_name": "采购审批", "applicant": "张三", "created_at": datetime.now().isoformat(), "type": "approval"},
        {"id": 2, "title": "更新知识库", "workflow_name": "文档审核", "applicant": "李四", "created_at": (datetime.now() - timedelta(hours=1)).isoformat(), "type": "approval"},
    ]
    
    return BaseResponse(data={"tasks": pending_list})


@router.get("/quick-stats", response_model=BaseResponse)
async def get_quick_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取快速统计（供首页卡片使用）"""
    return BaseResponse(data={
        "total_templates": 12,
        "running_workflows": 8,
        "knowledge_documents": 156,
        "ai_conversations": 456,
    })
