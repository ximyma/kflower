"""
API路由 - 工作流管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Workflow, WorkflowInstance, WorkflowTask, WorkflowLog
from app.schemas.schemas import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, BaseResponse,
    WorkflowExecuteRequest, WorkflowTaskActionRequest
)
from app.core.workflow.engine import WorkflowEngine

router = APIRouter(prefix="/workflows", tags=["流程审批"])


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流列表"""
    query = select(Workflow).where(Workflow.is_active == True)
    
    if search:
        query = query.where(
            (Workflow.name.contains(search)) |
            (Workflow.description.contains(search))
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    return [
        WorkflowResponse(
            id=w.id,
            name=w.name,
            code=w.code,
            description=w.description,
            flow_type=w.flow_type,
            nodes=w.nodes or [],
            edges=w.edges or [],
            is_active=w.is_active,
            created_at=w.created_at
        )
        for w in workflows
    ]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流详情"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        code=workflow.code,
        description=workflow.description,
        flow_type=workflow.flow_type,
        nodes=workflow.nodes or [],
        edges=workflow.edges or [],
        is_active=workflow.is_active,
        created_at=workflow.created_at
    )


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工作流"""
    code = request.code or f"wf_{uuid.uuid4().hex[:8]}"
    
    workflow = Workflow(
        name=request.name,
        code=code,
        description=request.description,
        flow_type=request.flow_type,
        nodes=[n.dict() for n in request.nodes],
        edges=[e.dict() for e in request.edges],
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        code=workflow.code,
        description=workflow.description,
        flow_type=workflow.flow_type,
        nodes=workflow.nodes or [],
        edges=workflow.edges or [],
        is_active=workflow.is_active,
        created_at=workflow.created_at
    )


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    request: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工作流"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    if request.name is not None:
        workflow.name = request.name
    if request.description is not None:
        workflow.description = request.description
    if request.nodes is not None:
        workflow.nodes = request.nodes
    if request.edges is not None:
        workflow.edges = request.edges
    if request.is_active is not None:
        workflow.is_active = request.is_active
    
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        code=workflow.code,
        description=workflow.description,
        flow_type=workflow.flow_type,
        nodes=workflow.nodes or [],
        edges=workflow.edges or [],
        is_active=workflow.is_active,
        created_at=workflow.created_at
    )


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作流"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    workflow.is_active = False
    await db.commit()
    
    return BaseResponse(message="工作流已删除")


# ============ 工作流实例端点 ============

@router.get("/instances/my", response_model=BaseResponse)
async def get_my_instances(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """我发起的实例列表"""
    query = (
        select(WorkflowInstance, Workflow.name.label("workflow_name"))
        .join(Workflow, WorkflowInstance.workflow_id == Workflow.id)
        .where(WorkflowInstance.created_by == current_user.id)
        .order_by(WorkflowInstance.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    items = [
        {
            "id": row.WorkflowInstance.id,
            "title": row.WorkflowInstance.title,
            "workflow_name": row.workflow_name,
            "status": row.WorkflowInstance.status,
            "created_at": row.WorkflowInstance.created_at.isoformat() if row.WorkflowInstance.created_at else None,
        }
        for row in rows
    ]
    return BaseResponse(data=items)


@router.get("/instances/pending", response_model=BaseResponse)
async def get_pending_tasks(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """待我审批的任务列表"""
    query = (
        select(WorkflowTask, WorkflowInstance.title, Workflow.name.label("workflow_name"), User.full_name.label("applicant"))
        .join(WorkflowInstance, WorkflowTask.instance_id == WorkflowInstance.id)
        .join(Workflow, WorkflowInstance.workflow_id == Workflow.id)
        .join(User, WorkflowInstance.created_by == User.id)
        .where(
            WorkflowTask.assignee_id == current_user.id,
            WorkflowTask.status == "pending"
        )
        .order_by(WorkflowTask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    items = [
        {
            "id": row.WorkflowTask.id,
            "instance_id": row.WorkflowTask.instance_id,
            "title": row.title,
            "workflow_name": row.workflow_name,
            "node_name": row.WorkflowTask.node_name,
            "applicant": row.applicant,
            "created_at": row.WorkflowTask.created_at.isoformat() if row.WorkflowTask.created_at else None,
        }
        for row in rows
    ]
    return BaseResponse(data=items)


@router.get("/instances/", response_model=BaseResponse)
async def list_all_instances(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """全部实例列表"""
    query = (
        select(WorkflowInstance, Workflow.name.label("workflow_name"), Workflow.description.label("workflow_description"))
        .join(Workflow, WorkflowInstance.workflow_id == Workflow.id)
        .order_by(WorkflowInstance.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    items = [
        {
            "id": row.WorkflowInstance.id,
            "name": row.WorkflowInstance.title,
            "description": row.workflow_description,
            "workflow_name": row.workflow_name,
            "node_count": len(row.WorkflowInstance.data) if isinstance(row.WorkflowInstance.data, (list, dict)) else 0,
            "status": row.WorkflowInstance.status,
            "created_at": row.WorkflowInstance.created_at.isoformat() if row.WorkflowInstance.created_at else None,
        }
        for row in rows
    ]
    return BaseResponse(data=items)


@router.post("/instances/{instance_id}/approve", response_model=BaseResponse)
async def approve_instance(
    instance_id: int,
    opinion: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批准当前任务"""
    # 查找待审批的任务
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.instance_id == instance_id,
            WorkflowTask.assignee_id == current_user.id,
            WorkflowTask.status == "pending"
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="没有待审批的任务")

    # 更新任务状态
    task.status = "approved"
    task.opinion = opinion
    task.completed_at = datetime.now()

    # 记录日志
    log = WorkflowLog(
        instance_id=instance_id,
        action="approved",
        operator_id=current_user.id,
        node_id=task.node_id,
        comment=opinion
    )
    db.add(log)

    # 检查该实例是否还有其他 pending 任务
    pending_result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.instance_id == instance_id,
            WorkflowTask.status == "pending"
        )
    )
    remaining = pending_result.scalars().all()

    # 如果没有更多 pending 任务，更新实例状态为 approved
    if not remaining:
        inst_result = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = inst_result.scalar_one_or_none()
        if instance:
            instance.status = "approved"
            instance.completed_at = datetime.now()

    await db.commit()
    return BaseResponse(message="审批通过")


@router.post("/instances/{instance_id}/reject", response_model=BaseResponse)
async def reject_instance(
    instance_id: int,
    opinion: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝当前任务"""
    # 查找待审批的任务
    result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.instance_id == instance_id,
            WorkflowTask.assignee_id == current_user.id,
            WorkflowTask.status == "pending"
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="没有待审批的任务")

    # 更新任务状态
    task.status = "rejected"
    task.opinion = opinion
    task.completed_at = datetime.now()

    # 记录日志
    log = WorkflowLog(
        instance_id=instance_id,
        action="rejected",
        operator_id=current_user.id,
        node_id=task.node_id,
        comment=opinion
    )
    db.add(log)

    # 更新实例状态为 rejected
    inst_result = await db.execute(
        select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
    )
    instance = inst_result.scalar_one_or_none()
    if instance:
        instance.status = "rejected"
        instance.completed_at = datetime.now()

    await db.commit()
    return BaseResponse(message="已拒绝")


# ============ 工作流执行 ============

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    title: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行工作流"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 创建工作流实例
    instance = WorkflowInstance(
        workflow_id=workflow_id,
        title=title,
        data=data,
        status="running",
        current_node_id=workflow.nodes[0]["id"] if workflow.nodes else None,
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    
    # 记录日志
    log = WorkflowLog(
        instance_id=instance.id,
        action="created",
        operator_id=current_user.id,
        comment="工作流实例创建"
    )
    db.add(log)
    await db.commit()
    
    return BaseResponse(message="工作流已启动", data={"instance_id": instance.id})


@router.post("/{workflow_id}/start")
async def start_workflow_instance(
    workflow_id: int,
    request: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动工作流实例（使用新引擎）"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 使用新引擎启动实例
    engine = WorkflowEngine(db)
    try:
        instance = await engine.start_instance(
            workflow_id=workflow_id,
            title=request.title,
            starter_id=current_user.id,
            variables=request.variables,
            form_data_id=request.form_data_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动工作流失败: {str(e)}")
    
    return BaseResponse(
        message="工作流实例已启动",
        data={
            "instance_id": instance.id,
            "title": instance.title,
            "status": instance.status,
            "current_node_id": instance.current_node_id
        }
    )


@router.post("/tasks/{task_id}/action")
async def workflow_task_action(
    task_id: int,
    request: WorkflowTaskActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """工作流任务操作（审批/拒绝/转交）"""
    engine = WorkflowEngine(db)
    try:
        if request.action == "approve":
            await engine.complete_task(
                task_id=task_id,
                user_id=current_user.id,
                action="approve",
                opinion=request.opinion,
                data=request.data
            )
            message = "任务已批准"
        elif request.action == "reject":
            await engine.complete_task(
                task_id=task_id,
                user_id=current_user.id,
                action="reject",
                opinion=request.opinion
            )
            message = "任务已拒绝"
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    
    return BaseResponse(message=message)
