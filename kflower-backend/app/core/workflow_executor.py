"""
工作流执行引擎
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models.workflow import (
    Workflow, WorkflowInstance, WorkflowTask, WorkflowLog
)
from app.models.user import User


class WorkflowExecutor:
    """工作流执行器（兼容性包装，内部委托给 WorkflowEngine）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute(self, workflow_id: int, input_data: Dict[str, Any] = None, 
                      user_id: int = None) -> Dict[str, Any]:
        """执行工作流（兼容性包装，委托给 WorkflowEngine）"""
        from app.core.workflow.engine import WorkflowEngine
        
        input_data = input_data or {}
        engine = WorkflowEngine(self.db)
        instance = await engine.start_instance(
            workflow_id=workflow_id,
            title=input_data.get("title", "自动触发的工作流"),
            starter_id=user_id or input_data.get("created_by", 1),
            variables=input_data,
            form_data_id=input_data.get("form_data_id")
        )
        return {
            "instance_id": instance.id,
            "status": instance.status,
            "title": instance.title
        }
    
    async def create_instance(
        self,
        workflow_id: int,
        title: str,
        data: Dict[str, Any],
        created_by: int
    ) -> WorkflowInstance:
        """创建工作流实例"""
        # 获取工作流定义
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # 创建实例
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            title=title,
            data=data,
            created_by=created_by,
            organization_id=workflow.organization_id,
            status="running"
        )
        self.db.add(instance)
        await self.db.flush()
        
        # 创建初始任务
        await self._create_initial_tasks(instance, workflow, created_by)
        
        # 记录日志
        await self._log_action(instance, "start", created_by)
        
        await self.db.commit()
        return instance
    
    async def _create_initial_tasks(
        self,
        instance: WorkflowInstance,
        workflow: Workflow,
        created_by: int
    ):
        """创建初始任务"""
        nodes = workflow.nodes or []
        edges = workflow.edges or []
        
        # 找到开始节点
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if not start_nodes:
            return
        
        start_node = start_nodes[0]
        instance.current_node_id = start_node.get("id")
        
        # 找到开始节点的后继节点
        next_nodes = self._get_next_nodes(start_node.get("id"), nodes, edges)
        
        for node in next_nodes:
            task = WorkflowTask(
                instance_id=instance.id,
                node_id=node.get("id"),
                node_name=node.get("name", "未命名"),
                status="pending"
            )
            self.db.add(task)
    
    def _get_next_nodes(
        self,
        node_id: str,
        nodes: List[Dict],
        edges: List[Dict]
    ) -> List[Dict]:
        """获取节点的后继节点"""
        # 找到从当前节点出发的所有边
        out_edges = [e for e in edges if e.get("source") == node_id]
        
        # 获取目标节点
        next_ids = [e.get("target") for e in out_edges]
        return [n for n in nodes if n.get("id") in next_ids]
    
    async def approve_task(
        self,
        task_id: int,
        assignee_id: int,
        opinion: str = "",
        variables: Dict[str, Any] = None
    ) -> WorkflowInstance:
        """审批任务"""
        # 获取任务
        result = await self.db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # 获取实例
        result = await self.db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id)
        )
        instance = result.scalar_one_or_none()
        
        # 获取工作流
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == instance.workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        # 更新任务状态
        task.status = "approved"
        task.opinion = opinion
        task.completed_at = datetime.now()
        task.assignee_id = assignee_id
        
        # 更新实例变量
        if variables:
            instance.data = {**instance.data, **variables}
        
        # 记录日志
        await self._log_action(instance, "approve", assignee_id, task.node_id, opinion)
        
        # 流转到下一个节点
        await self._move_to_next_nodes(instance, workflow, task.node_id, assignee_id)
        
        await self.db.commit()
        return instance
    
    async def reject_task(
        self,
        task_id: int,
        assignee_id: int,
        opinion: str = ""
    ) -> WorkflowInstance:
        """拒绝任务"""
        result = await self.db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        result = await self.db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id)
        )
        instance = result.scalar_one_or_none()
        
        # 更新任务状态
        task.status = "rejected"
        task.opinion = opinion
        task.completed_at = datetime.now()
        task.assignee_id = assignee_id
        
        # 更新实例状态
        instance.status = "rejected"
        instance.completed_at = datetime.now()
        
        # 记录日志
        await self._log_action(instance, "reject", assignee_id, task.node_id, opinion)
        
        await self.db.commit()
        return instance
    
    async def _move_to_next_nodes(
        self,
        instance: WorkflowInstance,
        workflow: Workflow,
        current_node_id: str,
        operator_id: int
    ):
        """移动到下一个节点"""
        nodes = workflow.nodes or []
        edges = workflow.edges or []
        
        # 获取当前节点
        current_node = next((n for n in nodes if n.get("id") == current_node_id), None)
        if not current_node:
            return
        
        # 检查是否有条件分支
        next_nodes = self._get_next_nodes(current_node_id, nodes, edges)
        
        if not next_nodes:
            # 没有后续节点，工作流结束
            instance.status = "approved"
            instance.completed_at = datetime.now()
            await self._log_action(instance, "complete", operator_id)
            return
        
        # 判断节点类型
        next_node = next_nodes[0]
        node_type = next_node.get("type")
        
        if node_type == "end":
            # 结束节点
            instance.status = "approved"
            instance.completed_at = datetime.now()
            await self._log_action(instance, "complete", operator_id)
        else:
            # 创建新任务
            task = WorkflowTask(
                instance_id=instance.id,
                node_id=next_node.get("id"),
                node_name=next_node.get("name", "未命名"),
                status="pending"
            )
            self.db.add(task)
            instance.current_node_id = next_node.get("id")
            await self._log_action(
                instance, "task_created", operator_id, 
                next_node.get("id"), f"创建任务: {next_node.get('name')}"
            )
    
    async def transfer_task(
        self,
        task_id: int,
        from_user_id: int,
        to_user_id: int,
        opinion: str = ""
    ) -> WorkflowTask:
        """转交任务"""
        result = await self.db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        result = await self.db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id)
        )
        instance = result.scalar_one_or_none()
        
        # 更新任务
        task.assignee_id = to_user_id
        task.status = "transferred"
        
        # 记录日志
        await self._log_action(
            instance, "transfer", from_user_id,
            task.node_id, f"转交给用户 {to_user_id}: {opinion}"
        )
        
        # 创建新任务
        new_task = WorkflowTask(
            instance_id=task.instance_id,
            node_id=task.node_id,
            node_name=task.node_name,
            status="pending",
            assignee_id=to_user_id
        )
        self.db.add(new_task)
        
        await self.db.commit()
        return new_task
    
    async def _log_action(
        self,
        instance: WorkflowInstance,
        action: str,
        operator_id: int,
        node_id: str = None,
        comment: str = None
    ):
        """记录工作流日志"""
        log = WorkflowLog(
            instance_id=instance.id,
            action=action,
            operator_id=operator_id,
            node_id=node_id,
            comment=comment
        )
        self.db.add(log)
    
    async def get_instance_detail(self, instance_id: int) -> Dict[str, Any]:
        """获取实例详情"""
        result = await self.db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        # 获取任务列表
        result = await self.db.execute(
            select(WorkflowTask)
            .where(WorkflowTask.instance_id == instance_id)
            .order_by(WorkflowTask.created_at.desc())
        )
        tasks = result.scalars().all()
        
        # 获取日志列表
        result = await self.db.execute(
            select(WorkflowLog)
            .where(WorkflowLog.instance_id == instance_id)
            .order_by(WorkflowLog.created_at.desc())
        )
        logs = result.scalars().all()
        
        return {
            "instance": instance,
            "tasks": tasks,
            "logs": logs
        }
