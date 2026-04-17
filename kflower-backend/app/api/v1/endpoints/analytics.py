"""
API路由 - 数据分析与决策支持
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Organization
from app.models.workflow import Workflow, WorkflowInstance, Template
from app.models.ai import KnowledgeBase, KnowledgeDocument, AIConversation
from app.schemas.schemas import BaseResponse

router = APIRouter(prefix="/analytics", tags=["数据分析"])


@router.get("/overview", response_model=BaseResponse)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据分析概览 - 图表数据"""

    # 1. 月度流程趋势（最近6个月）
    monthly_data = []
    now = datetime.now()
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i))
        month_end = month_start + timedelta(days=30)
        month_name = month_start.strftime("%Y-%m")

        result = await db.execute(
            select(func.count(WorkflowInstance.id)).where(
                WorkflowInstance.created_at >= month_start,
                WorkflowInstance.created_at < month_end
            )
        )
        count = result.scalar() or 0
        monthly_data.append({"month": month_name, "count": count})

    # 2. 流程状态分布
    status_result = await db.execute(
        select(WorkflowInstance.status, func.count(WorkflowInstance.id))
        .group_by(WorkflowInstance.status)
    )
    status_data = [{"status": r[0] or "unknown", "count": r[1]} for r in status_result.fetchall()]

    # 3. 知识库统计
    kb_result = await db.execute(
        select(KnowledgeBase.id, KnowledgeBase.name, func.coalesce(func.sum(KnowledgeBase.doc_count), 0))
        .group_by(KnowledgeBase.id, KnowledgeBase.name)
    )
    kb_data = [{"name": r[1], "doc_count": r[2]} for r in kb_result.fetchall()]

    # 4. AI对话趋势（最近6个月）
    ai_data = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i))
        month_end = month_start + timedelta(days=30)
        month_name = month_start.strftime("%Y-%m")

        result = await db.execute(
            select(func.count(AIConversation.id)).where(
                AIConversation.created_at >= month_start,
                AIConversation.created_at < month_end
            )
        )
        count = result.scalar() or 0
        ai_data.append({"month": month_name, "count": count})

    # 5. 模板分类统计
    cat_result = await db.execute(
        select(Template.category, func.count(Template.id))
        .group_by(Template.category)
    )
    category_data = [{"category": r[0] or "其他", "count": r[1]} for r in cat_result.fetchall()]

    # 6. 用户活跃度（最近30天）
    active_users_result = await db.execute(
        select(func.count(func.distinct(WorkflowInstance.created_by))).where(
            WorkflowInstance.created_at >= now - timedelta(days=30)
        )
    )
    active_users = active_users_result.scalar() or 0

    # 7. 流程效率统计
    efficiency_data = await calculate_efficiency(db, now)

    return BaseResponse(data={
        "monthly_workflow": monthly_data,
        "workflow_status": status_data,
        "knowledge_base": kb_data,
        "ai_trend": ai_data,
        "template_category": category_data,
        "active_users": active_users,
        "efficiency": efficiency_data
    })


async def calculate_efficiency(db: AsyncSession, now: datetime):
    """计算流程效率指标"""
    # 平均处理时间
    result = await db.execute(
        select(
            func.avg(
                func.julianday(WorkflowInstance.updated_at) - func.julianday(WorkflowInstance.created_at)
            ) * 24 * 60
        ).where(
            WorkflowInstance.status.in_(['approved', 'rejected', 'completed']),
            WorkflowInstance.updated_at >= now - timedelta(days=30)
        )
    )
    avg_time = result.scalar() or 0

    # 按时完成率（假设24小时内为按时）
    total_result = await db.execute(
        select(func.count(WorkflowInstance.id)).where(
            WorkflowInstance.status.in_(['approved', 'completed']),
            WorkflowInstance.updated_at >= now - timedelta(days=30)
        )
    )
    total = total_result.scalar() or 0

    ontime_result = await db.execute(
        select(func.count(WorkflowInstance.id)).where(
            WorkflowInstance.status.in_(['approved', 'completed']),
            WorkflowInstance.updated_at >= now - timedelta(days=30),
            (func.julianday(WorkflowInstance.updated_at) - func.julianday(WorkflowInstance.created_at)) * 24 <= 24
        )
    )
    ontime = ontime_result.scalar() or 0

    return {
        "avg_processing_time_minutes": round(avg_time, 1),
        "ontime_completion_rate": round(ontime / total * 100, 1) if total > 0 else 0,
        "total_completed": total
    }


@router.get("/workflow-performance", response_model=BaseResponse)
async def get_workflow_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流性能分析"""
    from sqlalchemy import text
    
    now = datetime.now()
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else now - timedelta(days=30)
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else now

    result = await db.execute(
        text("""
            SELECT w.name,
                   COUNT(wi.id) as total,
                   SUM(CASE WHEN wi.status = 'approved' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN wi.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                   SUM(CASE WHEN wi.status = 'running' THEN 1 ELSE 0 END) as running
            FROM workflow_instances wi
            JOIN workflows w ON wi.workflow_id = w.id
            WHERE wi.created_at >= :start AND wi.created_at <= :end
            GROUP BY w.id, w.name
            ORDER BY total DESC
        """),
        {"start": start.isoformat(), "end": end.isoformat()}
    )

    performance = []
    for r in result.fetchall():
        total = r[1] or 0
        approved = r[2] or 0
        performance.append({
            "workflow_name": r[0],
            "total": total,
            "approved": approved,
            "rejected": r[3] or 0,
            "running": r[4] or 0,
            "approval_rate": round(approved / max(total, 1) * 100, 1)
        })

    return BaseResponse(data=performance)


@router.get("/user-activity", response_model=BaseResponse)
async def get_user_activity(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户活跃度分析"""
    now = datetime.now()
    start = now - timedelta(days=days)

    # 按日期统计活跃用户
    daily_activity = []
    for i in range(days):
        day = start + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)

        # 工作流活跃
        wf_result = await db.execute(
            select(func.count(func.distinct(WorkflowInstance.created_by))).where(
                WorkflowInstance.created_at >= day_start,
                WorkflowInstance.created_at < day_end
            )
        )
        wf_active = wf_result.scalar() or 0

        # AI对话活跃
        ai_result = await db.execute(
            select(func.count(func.distinct(AIConversation.user_id))).where(
                AIConversation.created_at >= day_start,
                AIConversation.created_at < day_end
            )
        )
        ai_active = ai_result.scalar() or 0

        daily_activity.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "workflow_users": wf_active,
            "ai_users": ai_active,
            "total": max(wf_active, ai_active)
        })

    # 最活跃用户 TOP 10
    top_users_result = await db.execute(
        select(
            User.username,
            User.full_name,
            func.count(WorkflowInstance.id).label('activity_count')
        )
        .select_from(WorkflowInstance)
        .join(User, WorkflowInstance.created_by == User.id)
        .where(WorkflowInstance.created_at >= start)
        .group_by(User.id, User.username, User.full_name)
        .order_by(desc('activity_count'))
        .limit(10)
    )

    top_users = []
    for r in top_users_result.fetchall():
        top_users.append({
            "username": r[0],
            "full_name": r[1] or r[0],
            "activity_count": r[2]
        })

    return BaseResponse(data={
        "daily_activity": daily_activity,
        "top_users": top_users
    })


@router.get("/template-analytics", response_model=BaseResponse)
async def get_template_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板使用分析"""
    from sqlalchemy import text
    
    now = datetime.now()
    start = now - timedelta(days=30)

    # 热门模板 TOP 10 (基于模板表统计)
    hot_result = await db.execute(
        text("""
            SELECT t.id, t.name, t.category, 0 as usage_count
            FROM templates t
            ORDER BY t.created_at DESC
            LIMIT 10
        """)
    )

    hot_templates = []
    for r in hot_result.fetchall():
        hot_templates.append({
            "id": r[0],
            "name": r[1],
            "category": r[2] or "其他",
            "usage_count": r[3]
        })

    # 分类使用统计
    category_result = await db.execute(
        text("""
            SELECT t.category,
                   COUNT(DISTINCT t.id) as template_count
            FROM templates t
            GROUP BY t.category
        """)
    )

    category_stats = []
    for r in category_result.fetchall():
        category_stats.append({
            "category": r[0] or "其他",
            "template_count": r[1],
            "usage_count": 0
        })

    return BaseResponse(data={
        "hot_templates": hot_templates,
        "category_stats": category_stats
    })


@router.get("/org-performance", response_model=BaseResponse)
async def get_organization_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组织/部门绩效分析"""
    from sqlalchemy import text
    
    now = datetime.now()
    start = now - timedelta(days=30)

    result = await db.execute(
        text("""
            SELECT COALESCE(o.name, '未分配部门'),
                   COUNT(wi.id) as total_instances,
                   SUM(CASE WHEN wi.status = 'approved' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN wi.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                   COUNT(DISTINCT wi.created_by) as active_users
            FROM workflow_instances wi
            JOIN users u ON wi.created_by = u.id
            LEFT JOIN organizations o ON u.organization_id = o.id
            WHERE wi.created_at >= :start
            GROUP BY o.id, o.name
            ORDER BY total_instances DESC
        """),
        {"start": start.isoformat()}
    )

    org_stats = []
    for r in result.fetchall():
        total = r[1] or 0
        approved = r[2] or 0
        org_stats.append({
            "organization": r[0],
            "total_instances": total,
            "approved": approved,
            "rejected": r[3] or 0,
            "active_users": r[4] or 0,
            "approval_rate": round(approved / max(total, 1) * 100, 1)
        })

    return BaseResponse(data=org_stats)


@router.get("/knowledge-analytics", response_model=BaseResponse)
async def get_knowledge_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库使用分析"""
    now = datetime.now()
    start = now - timedelta(days=30)

    # 知识库统计
    kb_result = await db.execute(
        select(
            KnowledgeBase.id,
            KnowledgeBase.name,
            KnowledgeBase.doc_count,
            func.coalesce(func.sum(KnowledgeDocument.file_size), 0).label('total_size')
        )
        .outerjoin(KnowledgeDocument, KnowledgeBase.id == KnowledgeDocument.kb_id)
        .group_by(KnowledgeBase.id, KnowledgeBase.name, KnowledgeBase.doc_count)
    )

    kb_stats = []
    for r in kb_result.fetchall():
        kb_stats.append({
            "id": r[0],
            "name": r[1],
            "doc_count": r[2] or 0,
            "total_size": r[3] or 0
        })

    return BaseResponse(data=kb_stats)


@router.post("/query")
async def query_analytics(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 自然语言查询分析数据"""
    question = request.get("question", "")
    
    # 获取概览数据
    overview = await get_analytics_overview(db, current_user)

    # 用 AI 分析
    try:
        from app.core.ai_digital_base import inference_service
        answer = await inference_service.analyze_data(
            question=question,
            data=overview.data
        )
        return {"answer": answer, "data": overview.data}
    except Exception as e:
        # AI 不可用时返回数据摘要
        data = overview.data
        summary = f"""
📊 **数据分析结果**

**问题**: {question}

**数据概览**:
- 月度流程: {sum(d['count'] for d in data['monthly_workflow'])} 个
- 活跃用户: {data['active_users']} 人
- 知识库: {len(data['knowledge_base'])} 个
- AI对话: {sum(d['count'] for d in data['ai_trend'])} 次

**效率指标**:
- 平均处理时间: {data['efficiency']['avg_processing_time_minutes']} 分钟
- 按时完成率: {data['efficiency']['ontime_completion_rate']}%

*提示: 配置 AI API Key 后可获得更智能的分析结果*
"""
        return {"answer": summary, "data": data}


@router.get("/dashboard-summary", response_model=BaseResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘摘要数据（首页展示用）"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0)
    week_start = today - timedelta(days=today.weekday())

    # 今日统计
    today_instances = await db.execute(
        select(func.count(WorkflowInstance.id)).where(
            WorkflowInstance.created_at >= today
        )
    )
    today_count = today_instances.scalar() or 0

    # 本周统计
    week_instances = await db.execute(
        select(func.count(WorkflowInstance.id)).where(
            WorkflowInstance.created_at >= week_start
        )
    )
    week_count = week_instances.scalar() or 0

    # 待处理任务
    pending_result = await db.execute(
        select(func.count(WorkflowInstance.id)).where(
            WorkflowInstance.status == 'running'
        )
    )
    pending_count = pending_result.scalar() or 0

    # 近期活动
    recent_result = await db.execute(
        select(WorkflowInstance, User.full_name)
        .join(User, WorkflowInstance.created_by == User.id)
        .order_by(desc(WorkflowInstance.updated_at))
        .limit(5)
    )

    recent_activities = []
    for r in recent_result.fetchall():
        instance = r[0]
        recent_activities.append({
            "id": instance.id,
            "title": instance.title or f"流程 #{instance.id}",
            "status": instance.status,
            "user": r[1] or "用户",
            "time": instance.updated_at.strftime("%Y-%m-%d %H:%M")
        })

    return BaseResponse(data={
        "today_instances": today_count,
        "week_instances": week_count,
        "pending_tasks": pending_count,
        "recent_activities": recent_activities
    })