"""
SLA 管理器 - 处理流程审批的超时、催办和自动升级
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowTask, WorkflowInstance, Workflow

logger = logging.getLogger(__name__)


class SLAManager:
    """SLA 管理器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def setup_task_sla(self, task_id: int, sla_config: Dict[str, Any]):
        """
        为任务设置 SLA
        
        Args:
            sla_config: {
                "deadline_hours": 24,      # 截止小时数
                "reminder_at": [4, 8, 20], # 提前提醒时间点（小时）
                "escalate_to": "manager"   # 升级对象
            }
        """
        if not sla_config or not sla_config.get("deadline_hours"):
            return
        
        deadline_hours = sla_config.get("deadline_hours", 24)
        deadline = datetime.now() + timedelta(hours=deadline_hours)
        
        # 更新任务 SLA 配置
        await self.db.execute(
            update(WorkflowTask).where(WorkflowTask.id == task_id).values(
                sla_config=sla_config,
                sla_deadline=deadline,
                sla_status="normal"
            )
        )
        await self.db.commit()
        
        logger.info(f"任务 {task_id} SLA 设置完成，截止时间: {deadline}")
    
    async def check_sla_status(self, task_id: int) -> Dict[str, Any]:
        """检查任务的 SLA 状态"""
        result = await self.db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.sla_deadline:
            return {"status": "none", "overdue": False}
        
        now = datetime.now()
        deadline = task.sla_deadline
        
        # 计算剩余时间
        remaining = deadline - now
        remaining_hours = remaining.total_seconds() / 3600
        
        # 确定状态
        if remaining_hours < 0:
            status = "overdue"
        elif remaining_hours < 4:
            status = "warning"
        else:
            status = "normal"
        
        # 更新状态
        if task.sla_status != status:
            task.sla_status = status
            await self.db.commit()
        
        return {
            "status": status,
            "overdue": remaining_hours < 0,
            "remaining_hours": remaining_hours,
            "deadline": deadline.isoformat(),
            "reminder_sent": task.reminder_sent or []
        }
    
    async def process_reminders(self):
        """处理所有待办任务的催办提醒"""
        # 获取所有待办且设置了 SLA 的任务
        result = await self.db.execute(
            select(WorkflowTask).where(
                and_(
                    WorkflowTask.status == "pending",
                    WorkflowTask.sla_deadline.isnot(None)
                )
            )
        )
        tasks = result.scalars().all()
        
        for task in tasks:
            await self._check_and_send_reminder(task)
    
    async def _check_and_send_reminder(self, task: WorkflowTask):
        """检查并发送催办提醒"""
        sla_config = task.sla_config or {}
        reminder_at = sla_config.get("reminder_at", [4, 8, 20])
        reminder_sent = task.reminder_sent or []
        
        now = datetime.now()
        deadline = task.sla_deadline
        
        if not deadline:
            return
        
        # 计算距离截止的小时数
        remaining_hours = (deadline - now).total_seconds() / 3600
        
        # 检查是否需要发送提醒
        for reminder_hour in reminder_at:
            # 如果剩余时间小于提醒阈值，且未发送过该提醒
            if remaining_hours <= reminder_hour and reminder_hour not in reminder_sent:
                await self._send_reminder(task, reminder_hour, remaining_hours)
                reminder_sent.append(reminder_hour)
                task.reminder_sent = reminder_sent
                await self.db.commit()
                break
    
    async def _send_reminder(self, task: WorkflowTask, reminder_hour: int, remaining_hours: float):
        """发送催办提醒"""
        logger.info(f"发送催办提醒: 任务 {task.id}, 剩余 {remaining_hours:.1f} 小时")
        
        # 构建提醒消息
        message = f"催办提醒：您有一个待办任务「{task.node_name}」即将超时（剩余 {remaining_hours:.1f} 小时）"
        
        # 发送站内通知
        try:
            from app.models.notification import Notification
            notification = Notification(
                user_id=task.assignee_id,
                title="工作流催办提醒",
                content=message,
                type="reminder",
                channel="system",
                source_type="workflow",
                source_id=task.instance_id
            )
            self.db.add(notification)
        except Exception as e:
            logger.error(f"催办通知发送失败: {e}")
    
    async def process_escalations(self):
        """处理超时升级"""
        now = datetime.now()
        
        # 获取已超时的任务
        result = await self.db.execute(
            select(WorkflowTask).where(
                and_(
                    WorkflowTask.status == "pending",
                    WorkflowTask.sla_deadline < now,
                    WorkflowTask.sla_status != "escalated"
                )
            )
        )
        tasks = result.scalars().all()
        
        for task in tasks:
            await self._escalate_task(task)
    
    async def _escalate_task(self, task: WorkflowTask):
        """升级任务"""
        sla_config = task.sla_config or {}
        escalate_to = sla_config.get("escalate_to", "manager")
        escalate_user_id = sla_config.get("escalate_user_id")
        
        logger.info(f"任务 {task.id} 已超时，升级到: {escalate_to}")
        
        # 更新状态为已升级
        task.sla_status = "escalated"
        await self.db.commit()
        
        # 发送升级通知
        try:
            from app.models.notification import Notification
            
            # 通知升级对象
            if escalate_user_id:
                notification = Notification(
                    user_id=escalate_user_id,
                    title="工作流任务升级",
                    content=f"任务「{task.node_name}」已超时升级，请及时处理。",
                    type="escalation",
                    channel="system",
                    source_type="workflow",
                    source_id=task.instance_id
                )
                self.db.add(notification)
            
            # 同时通知原处理人
            if task.assignee_id and task.assignee_id != escalate_user_id:
                notification2 = Notification(
                    user_id=task.assignee_id,
                    title="工作流任务已升级",
                    content=f"您的任务「{task.node_name}」因超时已被升级处理。",
                    type="escalation",
                    channel="system",
                    source_type="workflow",
                    source_id=task.instance_id
                )
                self.db.add(notification2)
        except Exception as e:
            logger.error(f"升级通知发送失败: {e}")
    
    async def extend_sla(self, task_id: int, extend_hours: int, reason: str = None):
        """延长 SLA 截止时间"""
        result = await self.db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.sla_deadline:
            return False
        
        # 延长截止时间
        new_deadline = task.sla_deadline + timedelta(hours=extend_hours)
        task.sla_deadline = new_deadline
        task.sla_status = "normal"  # 重置状态
        await self.db.commit()
        
        logger.info(f"任务 {task_id} SLA 延长 {extend_hours} 小时，新截止时间: {new_deadline}")
        return True
    
    async def get_sla_statistics(self, workflow_id: Optional[int] = None, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取 SLA 统计信息"""
        query = select(WorkflowTask).where(WorkflowTask.sla_deadline.isnot(None))
        
        if workflow_id:
            # 需要关联 WorkflowInstance 获取 workflow_id
            pass
        
        if start_date:
            query = query.where(WorkflowTask.created_at >= start_date)
        if end_date:
            query = query.where(WorkflowTask.created_at <= end_date)
        
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        total = len(tasks)
        normal = sum(1 for t in tasks if t.sla_status == "normal")
        warning = sum(1 for t in tasks if t.sla_status == "warning")
        overdue = sum(1 for t in tasks if t.sla_status == "overdue")
        escalated = sum(1 for t in tasks if t.sla_status == "escalated")
        
        # 计算平均处理时间
        completed_tasks = [t for t in tasks if t.completed_at and t.created_at]
        if completed_tasks:
            avg_hours = sum(
                (t.completed_at - t.created_at).total_seconds() / 3600 
                for t in completed_tasks
            ) / len(completed_tasks)
        else:
            avg_hours = 0
        
        return {
            "total": total,
            "normal": normal,
            "warning": warning,
            "overdue": overdue,
            "escalated": escalated,
            "avg_processing_hours": round(avg_hours, 2),
            "on_time_rate": round((normal + warning) / total * 100, 2) if total > 0 else 0
        }


# 全局 SLA 管理器实例
async def get_sla_manager(db: AsyncSession) -> SLAManager:
    """获取 SLA 管理器实例"""
    return SLAManager(db)
