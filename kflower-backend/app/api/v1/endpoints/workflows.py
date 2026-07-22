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
            created_at=w.created_at,
            # 斑斑低代码平台扩展字段
            node_definitions=w.node_definitions,
            edge_definitions=w.edge_definitions,
            variables=w.variables,
            form_template_id=w.form_template_id
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
        created_at=workflow.created_at,
        # 斑斑低代码平台扩展字段
        node_definitions=workflow.node_definitions,
        edge_definitions=workflow.edge_definitions,
        variables=workflow.variables,
        form_template_id=workflow.form_template_id
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
        # 斑斑低代码平台扩展字段
        node_definitions=request.node_definitions or [],
        edge_definitions=request.edge_definitions or [],
        variables=request.variables or {},
        form_template_id=request.form_template_id,
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
        created_at=workflow.created_at,
        # 斑斑低代码平台扩展字段
        node_definitions=workflow.node_definitions,
        edge_definitions=workflow.edge_definitions,
        variables=workflow.variables,
        form_template_id=workflow.form_template_id
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
        workflow.nodes = [n.dict() for n in request.nodes]
    if request.edges is not None:
        workflow.edges = [e.dict() for e in request.edges]
    if request.is_active is not None:
        workflow.is_active = request.is_active
    # 斑斑低代码平台扩展字段
    if request.node_definitions is not None:
        workflow.node_definitions = request.node_definitions
    if request.edge_definitions is not None:
        workflow.edge_definitions = request.edge_definitions
    if request.variables is not None:
        workflow.variables = request.variables
    if request.form_template_id is not None:
        workflow.form_template_id = request.form_template_id
    
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
        created_at=workflow.created_at,
        # 斑斑低代码平台扩展字段
        node_definitions=workflow.node_definitions,
        edge_definitions=workflow.edge_definitions,
        variables=workflow.variables,
        form_template_id=workflow.form_template_id
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
    """批准当前任务（使用引擎流转）"""
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

    # 使用引擎完成审批
    engine = WorkflowEngine(db)
    try:
        await engine.complete_task(
            task_id=task.id,
            user_id=current_user.id,
            action="approve",
            opinion=opinion
        )
        return BaseResponse(message="审批通过", data={"task_id": task.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审批失败: {str(e)}")


@router.post("/instances/{instance_id}/reject", response_model=BaseResponse)
async def reject_instance(
    instance_id: int,
    opinion: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝当前任务（使用引擎流转）"""
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

    # 使用引擎完成
    engine = WorkflowEngine(db)
    try:
        await engine.complete_task(
            task_id=task.id,
            user_id=current_user.id,
            action="reject",
            opinion=opinion
        )
        return BaseResponse(message="已拒绝", data={"task_id": task.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


# ============ 工作流执行 ============

@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: int,
    title: str,
    data: dict,
    form_template_id: int = None,
    form_data_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行工作流（整合优化 1.4：支持携带表单数据）"""
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
        form_template_id=form_template_id,
        form_data_id=form_data_id,
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
        elif request.action == "transfer":
            result = await engine.transfer_task(
                task_id=task_id,
                from_user_id=current_user.id,
                to_user_id=request.transfer_to,
                opinion=request.opinion or ""
            )
            message = result.get("message", "任务已转交")
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作类型: {request.action}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    
    return BaseResponse(message=message)


# ============ 新增端点（审批闭环） ============

@router.get("/instances/{instance_id}", response_model=BaseResponse)
async def get_instance_detail(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工作流实例详情（含任务列表、审批日志、时间线）"""
    result = await db.execute(
        select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    # 获取工作流定义
    wf_result = await db.execute(
        select(Workflow).where(Workflow.id == instance.workflow_id)
    )
    workflow = wf_result.scalar_one_or_none()

    # 获取所有任务
    tasks_result = await db.execute(
        select(WorkflowTask, User.full_name.label("assignee_name"))
        .outerjoin(User, WorkflowTask.assignee_id == User.id)
        .where(WorkflowTask.instance_id == instance_id)
        .order_by(WorkflowTask.created_at.desc())
    )
    task_rows = tasks_result.all()
    tasks = [
        {
            "id": row.WorkflowTask.id,
            "node_id": row.WorkflowTask.node_id,
            "node_name": row.WorkflowTask.node_name,
            "node_type": row.WorkflowTask.node_type,
            "assignee_id": row.WorkflowTask.assignee_id,
            "assignee_name": row.assignee_name,
            "status": row.WorkflowTask.status,
            "opinion": row.WorkflowTask.opinion,
            "created_at": row.WorkflowTask.created_at.isoformat() if row.WorkflowTask.created_at else None,
            "completed_at": row.WorkflowTask.completed_at.isoformat() if row.WorkflowTask.completed_at else None,
        }
        for row in task_rows
    ]

    # 获取日志
    logs_result = await db.execute(
        select(WorkflowLog, User.full_name.label("operator_name"))
        .outerjoin(User, WorkflowLog.operator_id == User.id)
        .where(WorkflowLog.instance_id == instance_id)
        .order_by(WorkflowLog.created_at.asc())
    )
    log_rows = logs_result.all()
    logs = [
        {
            "id": row.WorkflowLog.id,
            "action": row.WorkflowLog.action,
            "operator_name": row.operator_name,
            "node_id": row.WorkflowLog.node_id,
            "comment": row.WorkflowLog.comment,
            "created_at": row.WorkflowLog.created_at.isoformat() if row.WorkflowLog.created_at else None,
        }
        for row in log_rows
    ]

    return BaseResponse(data={
        "id": instance.id,
        "workflow_id": instance.workflow_id,
        "workflow_name": workflow.name if workflow else "",
        "title": instance.title,
        "status": instance.status,
        "current_node_id": instance.current_node_id,
        "form_data_id": instance.form_data_id,
        "form_template_id": workflow.form_template_id if workflow else None,
        "variables": instance.variables or {},
        "created_by": instance.created_by,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
        "tasks": tasks,
        "logs": logs,
        "nodes": workflow.nodes if workflow else [],
        "edges": workflow.edges if workflow else [],
    })


@router.post("/instances/{instance_id}/withdraw", response_model=BaseResponse)
async def withdraw_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """撤回已提交的审批实例"""
    result = await db.execute(
        select(WorkflowInstance).where(
            WorkflowInstance.id == instance_id,
            WorkflowInstance.created_by == current_user.id,
            WorkflowInstance.status == "running"
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在或不可撤回")

    # 取消所有 pending 任务
    tasks_result = await db.execute(
        select(WorkflowTask).where(
            WorkflowTask.instance_id == instance_id,
            WorkflowTask.status == "pending"
        )
    )
    pending_tasks = tasks_result.scalars().all()
    for task in pending_tasks:
        task.status = "cancelled"
        task.opinion = "发起人撤回"

    # 更新实例状态
    instance.status = "cancelled"
    instance.completed_at = datetime.now()

    # 记录日志
    log = WorkflowLog(
        instance_id=instance_id,
        action="withdraw",
        operator_id=current_user.id,
        comment="发起人撤回审批"
    )
    db.add(log)

    await db.commit()
    return BaseResponse(message="审批已撤回")


@router.post("/tasks/{task_id}/transfer", response_model=BaseResponse)
async def transfer_task(
    task_id: int,
    transfer_to: int,
    opinion: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """转交任务"""
    engine = WorkflowEngine(db)
    try:
        result = await engine.transfer_task(
            task_id=task_id,
            from_user_id=current_user.id,
            to_user_id=transfer_to,
            opinion=opinion
        )
        return BaseResponse(message=result.get("message", "任务已转交"), data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转交失败: {str(e)}")


# ============ 模板-工作流绑定 ============

@router.post("/bind-template", response_model=BaseResponse)
async def bind_workflow_to_template(
    workflow_id: int,
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将工作流绑定到模板"""
    from app.models.workflow import Template
    
    # 验证工作流存在
    wf_result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = wf_result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 验证模板存在
    tpl_result = await db.execute(select(Template).where(Template.id == template_id))
    template = tpl_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 更新工作流的模板关联
    workflow.form_template_id = template_id
    
    # 更新模板的 workflows 字段
    tpl_workflows = template.workflows or []
    if workflow_id not in tpl_workflows:
        tpl_workflows.append(workflow_id)
        template.workflows = tpl_workflows
    
    await db.commit()
    return BaseResponse(message=f"工作流 '{workflow.name}' 已绑定到模板 '{template.name}'")


@router.get("/by-template/{template_id}", response_model=BaseResponse)
async def get_workflows_by_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板绑定的工作流列表"""
    result = await db.execute(
        select(Workflow).where(
            Workflow.form_template_id == template_id,
            Workflow.is_active == True
        )
    )
    workflows = result.scalars().all()
    
    return BaseResponse(data=[
        {
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "description": w.description,
            "nodes": w.nodes or [],
            "edges": w.edges or [],
            "is_active": w.is_active
        }
        for w in workflows
    ])
