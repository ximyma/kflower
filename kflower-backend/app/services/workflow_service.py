"""
业务服务 - 流程审批服务
智能流程引擎
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from app.models.workflow import Workflow, WorkflowInstance, WorkflowTask, WorkflowLog
from app.models.user import User
from app.core.ai_digital_base.inference import inference_service


class WorkflowService:
    """流程审批服务 - 智能流程引擎"""
    
    # 流程节点类型
    NODE_TYPES = {
        "start": {"name": "开始", "icon": "el-icon-video-play", "color": "#67C23A"},
        "end": {"name": "结束", "icon": "el-icon-video-pause", "color": "#F56C6C"},
        "task": {"name": "任务", "icon": "el-icon-document", "color": "#409EFF"},
        "approval": {"name": "审批", "icon": "el-icon-circle-check", "color": "#E6A23C"},
        "condition": {"name": "条件", "icon": "el-icon-question", "color": "#909399"},
        "parallel": {"name": "并行", "icon": "el-icon-s-grid", "color": "#F56C6C"},
        "subprocess": {"name": "子流程", "icon": "el-icon-document-copy", "color": "#67C23A"}
    }
    
    # 预设流程模板
    FLOW_TEMPLATES = {
        "leave": {
            "name": "请假审批流程",
            "category": "人事",
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 200},
                {"id": "fill", "type": "task", "name": "填写请假单", "x": 220, "y": 200},
                {"id": "check_manager", "type": "condition", "name": "请假天数>3?", "x": 340, "y": 200},
                {"id": "dept_approval", "type": "approval", "name": "部门经理审批", "x": 460, "y": 120},
                {"id": "hr_approval", "type": "approval", "name": "HR审批", "x": 460, "y": 280},
                {"id": "end", "type": "end", "name": "结束", "x": 580, "y": 200}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "fill"},
                {"id": "e2", "source": "fill", "target": "check_manager"},
                {"id": "e3", "source": "check_manager", "target": "dept_approval", "label": "是"},
                {"id": "e4", "source": "check_manager", "target": "hr_approval", "label": "否"},
                {"id": "e5", "source": "dept_approval", "target": "hr_approval"},
                {"id": "e6", "source": "hr_approval", "target": "end"}
            ]
        },
        "purchase": {
            "name": "采购审批流程",
            "category": "采购",
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 200},
                {"id": "apply", "type": "task", "name": "提交采购申请", "x": 220, "y": 200},
                {"id": "amount_check", "type": "condition", "name": "金额>10000?", "x": 340, "y": 200},
                {"id": "manager_approval", "type": "approval", "name": "部门经理", "x": 460, "y": 100},
                {"id": "finance_approval", "type": "approval", "name": "财务审批", "x": 460, "y": 200},
                {"id": "boss_approval", "type": "approval", "name": "总经理审批", "x": 460, "y": 300},
                {"id": "end", "type": "end", "name": "结束", "x": 580, "y": 200}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "apply"},
                {"id": "e2", "source": "apply", "target": "amount_check"},
                {"id": "e3", "source": "amount_check", "target": "manager_approval", "label": "是"},
                {"id": "e4", "source": "amount_check", "target": "finance_approval", "label": "否"},
                {"id": "e5", "source": "manager_approval", "target": "finance_approval"},
                {"id": "e6", "source": "finance_approval", "target": "boss_approval", "label": "金额>50000"},
                {"id": "e7", "source": "finance_approval", "target": "end"},
                {"id": "e8", "source": "boss_approval", "target": "end"}
            ]
        },
        "expense": {
            "name": "费用报销流程",
            "category": "财务",
            "nodes": [
                {"id": "start", "type": "start", "name": "开始", "x": 100, "y": 200},
                {"id": "fill", "type": "task", "name": "填写报销单", "x": 220, "y": 200},
                {"id": "leader_approval", "type": "approval", "name": "直属领导", "x": 340, "y": 200},
                {"id": "finance_check", "type": "approval", "name": "财务复核", "x": 460, "y": 200},
                {"id": "payment", "type": "task", "name": "付款", "x": 580, "y": 200},
                {"id": "end", "type": "end", "name": "结束", "x": 700, "y": 200}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "fill"},
                {"id": "e2", "source": "fill", "target": "leader_approval"},
                {"id": "e3", "source": "leader_approval", "target": "finance_check"},
                {"id": "e4", "source": "finance_check", "target": "payment"},
                {"id": "e5", "source": "payment", "target": "end"}
            ]
        }
    }
    
    @classmethod
    async def design_workflow(
        cls,
        description: str
    ) -> Dict[str, Any]:
        """AI设计工作流"""
        # AI分析流程
        result = await inference_service.explain_workflow(description)
        
        if "error" not in result:
            return result
        
        # 返回基础结构
        return {
            "workflow_name": cls._extract_name(description),
            "nodes": [],
            "edges": [],
            "suggestions": ["请详细描述流程步骤"]
        }
    
    @classmethod
    async def optimize_workflow(
        cls,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化工作流"""
        nodes = workflow_data.get("nodes", [])
        edges = workflow_data.get("edges", [])
        
        optimizations = []
        
        # 检查孤立节点
        connected = set()
        for edge in edges:
            connected.add(edge.get("source"))
            connected.add(edge.get("target"))
        
        for node in nodes:
            if node.get("id") not in connected and node.get("type") not in ["start", "end"]:
                optimizations.append(f"节点'{node.get('name')}'未连接到任何其他节点")
        
        # 检查审批节点
        approval_nodes = [n for n in nodes if n.get("type") == "approval"]
        if len(approval_nodes) > 5:
            optimizations.append("审批节点过多，建议考虑并行审批或简化流程")
        
        # 建议优化
        if len(nodes) > 10:
            optimizations.append("流程较复杂，建议拆分为子流程")
        
        return {
            "original_nodes": len(nodes),
            "original_edges": len(edges),
            "optimizations": optimizations,
            "optimized_workflow": workflow_data
        }
    
    @classmethod
    async def recommend_approvers(
        cls,
        context: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """智能推荐审批人"""
        # 基于上下文推荐
        amount = context.get("amount", 0)
        department = context.get("department", "")
        category = context.get("category", "")
        
        # 根据金额确定审批级别
        approval_levels = []
        
        if amount > 50000:
            approval_levels.append({
                "level": 1,
                "role": "部门经理",
                "required": True
            })
            approval_levels.append({
                "level": 2,
                "role": "财务总监",
                "required": True
            })
            approval_levels.append({
                "level": 3,
                "role": "总经理",
                "required": True
            })
        elif amount > 10000:
            approval_levels.append({
                "level": 1,
                "role": "部门经理",
                "required": True
            })
            approval_levels.append({
                "level": 2,
                "role": "财务经理",
                "required": True
            })
        else:
            approval_levels.append({
                "level": 1,
                "role": "部门经理",
                "required": True
            })
        
        # 查询符合条件的用户
        result = await db.execute(
            select(User).where(User.is_active == True).limit(10)
        )
        users = result.scalars().all()
        
        recommendations = []
        for level in approval_levels:
            # 简单匹配，实际应该根据角色和部门
            for user in users[:1]:
                recommendations.append({
                    "level": level["level"],
                    "role": level["role"],
                    "required": level["required"],
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "reason": f"根据{level['role']}角色和{amount}元金额自动分配"
                })
                break
        
        return recommendations
    
    @classmethod
    async def execute_workflow(
        cls,
        workflow_id: int,
        title: str,
        data: Dict[str, Any],
        user_id: int,
        organization_id: Optional[int],
        db: AsyncSession
    ) -> WorkflowInstance:
        """执行工作流"""
        # 获取工作流定义
        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise ValueError("工作流不存在")
        
        # 创建实例
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            title=title,
            data=data,
            status="running",
            current_node_id=workflow.nodes[0]["id"] if workflow.nodes else None,
            organization_id=organization_id,
            created_by=user_id
        )
        
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        
        # 创建第一个任务
        if workflow.nodes:
            first_node = workflow.nodes[0]
            task = WorkflowTask(
                instance_id=instance.id,
                node_id=first_node["id"],
                node_name=first_node["name"],
                status="pending"
            )
            db.add(task)
            await db.commit()
        
        # 记录日志
        log = WorkflowLog(
            instance_id=instance.id,
            action="created",
            operator_id=user_id,
            comment="工作流实例创建"
        )
        db.add(log)
        await db.commit()
        
        return instance
    
    @classmethod
    async def process_task(
        cls,
        task_id: int,
        action: str,  # approve/reject/transfer
        opinion: Optional[str],
        user_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """处理任务"""
        result = await db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return {"error": "任务不存在"}
        
        # 更新任务状态
        if action == "approve":
            task.status = "approved"
        elif action == "reject":
            task.status = "rejected"
        elif action == "transfer":
            task.status = "transferred"
        
        task.opinion = opinion
        task.completed_at = datetime.now()
        
        # 更新实例状态
        instance_result = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id)
        )
        instance = instance_result.scalar_one_or_none()
        
        if instance:
            if action == "reject":
                instance.status = "rejected"
            elif action == "approve":
                # 查找下一个节点
                next_node = cls._find_next_node(task.node_id, instance)
                if next_node:
                    instance.current_node_id = next_node["id"]
                    # 创建下一个任务
                    next_task = WorkflowTask(
                        instance_id=instance.id,
                        node_id=next_node["id"],
                        node_name=next_node["name"],
                        status="pending"
                    )
                    db.add(next_task)
                else:
                    instance.status = "approved"
                    instance.completed_at = datetime.now()
        
        # 记录日志
        log = WorkflowLog(
            instance_id=task.instance_id,
            action=action,
            operator_id=user_id,
            node_id=task.node_id,
            comment=opinion
        )
        db.add(log)
        
        await db.commit()
        
        return {"success": True, "action": action}
    
    @classmethod
    def _find_next_node(
        cls,
        current_node_id: str,
        instance: WorkflowInstance
    ) -> Optional[Dict[str, Any]]:
        """查找下一个节点"""
        workflow_result = None
        # 这里需要重新查询工作流，后续优化
        
        edges = instance.workflow.edges if hasattr(instance, 'workflow') and instance.workflow else []
        nodes = instance.workflow.nodes if hasattr(instance, 'workflow') and instance.workflow else []
        
        # 找到从当前节点出发的边
        next_edges = [e for e in edges if e.get("source") == current_node_id]
        
        if next_edges:
            next_edge = next_edges[0]
            next_node_id = next_edge.get("target")
            
            for node in nodes:
                if node.get("id") == next_node_id:
                    return node
        
        return None
    
    @classmethod
    def get_templates(cls) -> List[Dict[str, Any]]:
        """获取流程模板"""
        return [
            {
                "key": key,
                "name": template["name"],
                "category": template["category"],
                "node_count": len(template["nodes"]),
                "preview": template
            }
            for key, template in cls.FLOW_TEMPLATES.items()
        ]


workflow_service = WorkflowService()
