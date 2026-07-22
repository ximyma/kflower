"""
流程引擎核心类
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import (
    Workflow, WorkflowInstance, WorkflowTask, WorkflowNodeInstance,
    WorkflowVariableLog, WorkflowTaskCandidates
)
from app.modules.my_apps.plugin_executor import plugin_executor, PluginContext
from app.core.workflow.node_types import NodeType
from app.core.workflow.condition_evaluator import ConditionEvaluator
from app.core.workflow.assignee_resolver import AssigneeResolver
from app.core.workflow.sla_manager import SLAManager


class WorkflowEngine:
    """流程引擎核心"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.condition_evaluator = ConditionEvaluator()
        self.assignee_resolver = AssigneeResolver()
    
    async def start_instance(self, workflow_id: int, title: str, starter_id: int, 
                              variables: Dict[str, Any], form_data_id: int = None) -> WorkflowInstance:
        """启动流程实例"""
        # 获取流程定义
        result = await self.db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one()
        
        # 创建实例
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            title=title,
            status="running",
            variables=variables,
            form_data_id=form_data_id,
            created_by=starter_id,
            current_node_id=workflow.nodes[0]["id"] if workflow.nodes else None
        )
        self.db.add(instance)
        await self.db.flush()
        
        # 记录变量日志
        await self._log_variables(instance.id, variables, starter_id)
        
        # 启动第一个节点
        if workflow.nodes:
            start_node = workflow.nodes[0]
            await self._enter_node(instance.id, start_node, variables)
        
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def complete_task(self, task_id: int, user_id: int, action: str, 
                            opinion: str = None, data: Dict[str, Any] = None):
        """完成任务（审批/办理）"""
        result = await self.db.execute(select(WorkflowTask).where(WorkflowTask.id == task_id))
        task = result.scalar_one()
        if not task or task.status != "pending":
            raise ValueError("任务不存在或已完成")
        
        # 更新任务
        task.status = "approved" if action == "approve" else "rejected"
        task.opinion = opinion
        task.completed_at = datetime.now()
        
        # 获取流程实例
        inst_result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id))
        instance = inst_result.scalar_one()
        
        # 获取流程定义
        wf_result = await self.db.execute(select(Workflow).where(Workflow.id == instance.workflow_id))
        workflow = wf_result.scalar_one()
        
        # 执行节点后置插件
        node_config = task.node_config or {}
        if node_config.get("config", {}).get("plugins", {}).get("after"):
            await self._run_plugin(node_config["config"]["plugins"]["after"], {
                "task": task, "instance": instance, "user_id": user_id, "data": data
            })
        
        if action == "reject":
            # 拒绝：结束流程
            instance.status = "rejected"
            instance.completed_at = datetime.now()
            await self.db.commit()
            return
        
        # 查找下一个节点
        next_node = await self._find_next_node(workflow, task.node_id, instance.variables)
        if next_node:
            await self._enter_node(instance.id, next_node, instance.variables)
        else:
            # 流程结束
            instance.status = "approved"
            instance.completed_at = datetime.now()
        
        await self.db.commit()
    
    async def transfer_task(self, task_id: int, from_user_id: int, to_user_id: int,
                            opinion: str = "") -> Dict[str, Any]:
        """转交任务"""
        result = await self.db.execute(select(WorkflowTask).where(WorkflowTask.id == task_id))
        task = result.scalar_one_or_none()
        if not task or task.status != "pending":
            raise ValueError("任务不存在或已完成")
        
        # 记录操作日志
        inst_result = await self.db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == task.instance_id)
        )
        instance = inst_result.scalar_one()
        
        log = WorkflowLog(
            instance_id=instance.id,
            action="transfer",
            operator_id=from_user_id,
            node_id=task.node_id,
            comment=f"转交至用户 {to_user_id}: {opinion}"
        )
        self.db.add(log)
        
        # 更新原任务为已转交
        task.status = "transferred"
        task.opinion = task.opinion or "" + f"\n[转交] {opinion}"
        task.completed_at = datetime.now()
        
        # 创建新任务给新处理人
        new_task = WorkflowTask(
            instance_id=task.instance_id,
            node_id=task.node_id,
            node_name=task.node_name,
            node_type=task.node_type or "approval",
            node_config=task.node_config,
            assignee_id=to_user_id,
            status="pending",
            priority=task.priority,
            sla_config=task.sla_config,
            due_date=task.due_date
        )
        self.db.add(new_task)
        await self.db.flush()
        
        # 发送通知
        await self._send_notification(to_user_id, task.node_name, instance.id)
        
        await self.db.commit()
        
        return {"task_id": new_task.id, "message": "任务已转交"}
    
    async def _enter_node(self, instance_id: int, node: Dict, variables: Dict):
        """进入节点"""
        node_type = node.get("type", "task")
        
        # 记录节点实例
        node_instance = WorkflowNodeInstance(
            instance_id=instance_id,
            node_id=node["id"],
            node_name=node.get("name", ""),
            node_type=node_type,
            status="running",
            start_time=datetime.now(),
            variables=variables
        )
        self.db.add(node_instance)
        await self.db.flush()
        
        # 执行节点前置插件
        if node.get("config", {}).get("plugins", {}).get("before"):
            await self._run_plugin(node["config"]["plugins"]["before"], {
                "instance_id": instance_id, "node": node, "variables": variables
            })
        
        # 根据节点类型处理
        if node_type == NodeType.APPROVAL:
            await self._handle_approval_node(instance_id, node, variables)
        elif node_type == NodeType.TASK:
            await self._handle_task_node(instance_id, node, variables)
        elif node_type == NodeType.CC:
            await self._handle_cc_node(instance_id, node, variables)
        elif node_type == NodeType.DATA_FILL:
            await self._handle_data_fill_node(instance_id, node, variables)
        elif node_type == NodeType.CONDITION:
            await self._handle_condition_node(instance_id, node, variables)
        elif node_type == NodeType.PARALLEL:
            await self._handle_parallel_node(instance_id, node, variables)
        elif node_type == NodeType.DATA_CHANGE:
            await self._handle_data_change_node(instance_id, node, variables)
        elif node_type == NodeType.TRIGGER:
            await self._handle_trigger_node(instance_id, node, variables)
        elif node_type == NodeType.DELAY:
            await self._handle_delay_node(instance_id, node, variables)
        elif node_type == NodeType.SUB_PROCESS:
            await self._handle_sub_process_node(instance_id, node, variables)
        # ===== AI 审批节点处理（升级方案 4.2） =====
        elif node_type == NodeType.AI_APPROVAL:
            await self._handle_ai_approval_node(instance_id, node, variables)
        elif node_type == NodeType.AI_REVIEW:
            await self._handle_ai_review_node(instance_id, node, variables)
        elif node_type == NodeType.AI_CLASSIFY:
            await self._handle_ai_classify_node(instance_id, node, variables)
        elif node_type == NodeType.NOTIFICATION:
            await self._handle_notification_node(instance_id, node, variables)
        elif node_type == NodeType.END:
            await self._end_instance(instance_id)
        
        # 更新节点实例完成时间
        node_instance.end_time = datetime.now()
        node_instance.status = "completed"
        await self.db.flush()
    
    async def _handle_approval_node(self, instance_id: int, node: Dict, variables: Dict):
        """处理审批节点：创建任务"""
        config = node.get("config", {})
        assignees = await self.assignee_resolver.resolve(config, variables, self.db)
        
        for assignee in assignees:
            task = WorkflowTask(
                instance_id=instance_id,
                node_id=node["id"],
                node_name=node.get("name", ""),
                status="pending",
                assignee_id=assignee["user_id"],
                node_config=node
            )
            self.db.add(task)
            await self.db.flush()  # 刷新以获取 task.id
            
            # 设置 SLA（升级方案 4.3）
            sla_config = config.get("sla", {})
            if sla_config and sla_config.get("enabled"):
                sla_manager = SLAManager(self.db)
                await sla_manager.setup_task_sla(task.id, {
                    "deadline_hours": sla_config.get("deadline_hours", 24),
                    "reminder_at": sla_config.get("reminder_at", [4, 8, 20]),
                    "escalate_to": sla_config.get("escalate_to", "manager"),
                    "escalate_user_id": sla_config.get("escalate_user_id")
                })
            
            # 抄送或通知
            await self._send_notification(assignee["user_id"], node.get("name", ""), instance_id)
    
    async def _handle_condition_node(self, instance_id: int, node: Dict, variables: Dict):
        """条件分支：根据表达式选择出口"""
        # 获取流程实例和定义
        inst_result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance_id))
        instance = inst_result.scalar_one()
        wf_result = await self.db.execute(select(Workflow).where(Workflow.id == instance.workflow_id))
        workflow = wf_result.scalar_one()
        
        # 使用现有的_find_next_node方法查找下一个节点
        next_node = await self._find_next_node(workflow, node["id"], variables)
        if next_node:
            await self._enter_node(instance_id, next_node, variables)
        else:
            # 如果没有符合条件的出口，记录错误
            logger = logging.getLogger(__name__)
            logger.error(f"条件节点 {node['id']} 没有找到符合条件的出口")
            # 可以考虑结束流程或抛出异常
            await self._auto_goto_next(instance_id, node)
    
    async def _handle_parallel_node(self, instance_id: int, node: Dict, variables: Dict):
        """并行分支：创建多个分支任务"""
        # 获取流程定义
        inst_result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance_id))
        instance = inst_result.scalar_one()
        wf_result = await self.db.execute(select(Workflow).where(Workflow.id == instance.workflow_id))
        workflow = wf_result.scalar_one()
        
        # 获取所有出边
        edges = workflow.edges or []
        outgoing_edges = [e for e in edges if e.get("source") == node["id"]]
        
        logger = logging.getLogger(__name__)
        logger.info(f"并行网关 {node['id']} 分叉为 {len(outgoing_edges)} 条路径")
        
        if not outgoing_edges:
            return
        
        # 并行网关：并发执行所有出边分支
        import asyncio
        
        async def execute_branch(edge: Dict):
            """执行单个并行分支"""
            target_id = edge.get("target")
            for workflow_node in workflow.nodes:
                if workflow_node.get("id") == target_id:
                    try:
                        await self._enter_node(instance_id, workflow_node, variables)
                    except Exception as e:
                        logger.error(f"并行分支 {target_id} 执行失败: {e}")
                    return
        
        # 并发执行所有分支
        await asyncio.gather(*[execute_branch(e) for e in outgoing_edges], return_exceptions=True)
    
    async def _handle_data_change_node(self, instance_id: int, node: Dict, variables: Dict):
        """数据变化节点：增/改/删数据"""
        config = node.get("config", {})
        action = config.get("action")
        target_template_id = config.get("target_template_id")
        data_mapping = config.get("data_mapping", {})
        
        # 渲染数据映射中的表达式
        rendered_data = {}
        for target_field, expr in data_mapping.items():
            rendered_data[target_field] = await self.condition_evaluator.render_expression(expr, variables)
        
        # 执行数据操作
        # 实际需要调用模板数据服务
        logger = logging.getLogger(__name__)
        logger.info(f"数据变更节点执行: action={action}, target_template_id={target_template_id}, data={rendered_data}")
        
        # 这里可以调用模板数据提交/更新/删除API
        # 示例：通过RPC或直接调用服务层
        # 暂时记录日志，实际实现需要根据业务需求
        
        # 自动进入下一节点
        await self._auto_goto_next(instance_id, node)
    
    async def _handle_trigger_node(self, instance_id: int, node: Dict, variables: Dict):
        """触发节点：执行 Python 插件"""
        config = node.get("config", {})
        plugin_id = config.get("plugin_id")
        if plugin_id:
            await self._run_plugin(plugin_id, {
                "instance_id": instance_id,
                "node": node,
                "variables": variables
            })
        
        await self._auto_goto_next(instance_id, node)
    
    async def _handle_delay_node(self, instance_id: int, node: Dict, variables: Dict):
        """延迟节点：定时触发下一节点"""
        config = node.get("config", {})
        delay_seconds = config.get("delay_seconds", 0)
        # 使用 asyncio 延迟或 Celery 任务
        asyncio.create_task(self._delayed_next(instance_id, node, delay_seconds))
    
    async def _delayed_next(self, instance_id: int, node: Dict, delay_seconds: int):
        await asyncio.sleep(delay_seconds)
        await self._auto_goto_next(instance_id, node)
    
    async def _auto_goto_next(self, instance_id: int, current_node: Dict):
        """自动进入下一节点"""
        # 获取流程实例和定义
        inst_result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance_id))
        instance = inst_result.scalar_one()
        wf_result = await self.db.execute(select(Workflow).where(Workflow.id == instance.workflow_id))
        workflow = wf_result.scalar_one()
        
        next_node = await self._find_next_node(workflow, current_node["id"], instance.variables)
        if next_node:
            await self._enter_node(instance_id, next_node, instance.variables)
        else:
            instance.status = "approved"
            instance.completed_at = datetime.now()
            await self.db.commit()
    
    async def _find_next_node(self, workflow: Workflow, current_node_id: str, variables: Dict) -> Optional[Dict]:
        """查找下一个节点（支持条件分支）"""
        edges = workflow.edges or []
        outgoing = [e for e in edges if e.get("source") == current_node_id]
        if not outgoing:
            return None
        
        # 如果有条件分支，需要评估条件
        for edge in outgoing:
            condition = edge.get("label") or edge.get("condition", "true")
            if await self.condition_evaluator.evaluate(condition, variables):
                target_id = edge.get("target")
                for node in workflow.nodes:
                    if node.get("id") == target_id:
                        return node
        return None
    
    async def _run_plugin(self, plugin_id: str, context_data: Dict):
        """执行插件"""
        from app.modules.my_apps.models import AppPlugin
        result = await self.db.execute(select(AppPlugin).where(AppPlugin.id == int(plugin_id)))
        plugin = result.scalar_one_or_none()
        if plugin and plugin.is_enabled:
            context = PluginContext(
                data=context_data,
                old_data=None,
                db=self.db,
                user_id=context_data.get("user_id", 0),
                template_id=0,
                event=plugin.trigger_event,
                app_id=plugin.app_id
            )
            await plugin_executor.execute(plugin.script_code, context)
        else:
            logger = logging.getLogger(__name__)
            logger.warning(f"插件 {plugin_id} 不存在或未启用")
    
    async def _send_notification(self, user_id: int, node_name: str, instance_id: int):
        """发送通知（站内信/邮件）"""
        try:
            from app.models.notification import Notification
            notification = Notification(
                user_id=user_id,
                title=f"新的待办任务",
                content=f"您有一个新的待办任务：「{node_name}」，请及时处理。",
                type="workflow",
                channel="system",
                source_type="workflow",
                source_id=instance_id
            )
            self.db.add(notification)
        except Exception as e:
            logger.warning(f"通知发送失败: {e}")
    
    async def _log_variables(self, instance_id: int, variables: Dict, user_id: int):
        for name, value in variables.items():
            log = WorkflowVariableLog(
                instance_id=instance_id,
                var_name=name,
                var_value=json.dumps(value, ensure_ascii=False),
                changed_by=user_id
            )
            self.db.add(log)
    
    async def _handle_task_node(self, instance_id: int, node: Dict, variables: Dict):
        """处理办理节点 - 分配任务给执行人"""
        config = node.get("config", {})
        assignees = config.get("assignees", [])
        
        if not assignees:
            # 没有指定执行人，自动跳过
            await self._auto_goto_next(instance_id, node)
            return
        
        for assignee in assignees:
            user_id = assignee.get("user_id") if isinstance(assignee, dict) else assignee
            if not user_id:
                continue
            task = WorkflowTask(
                instance_id=instance_id,
                node_id=node["id"],
                node_name=node.get("name", "未命名"),
                node_type=node.get("type", "task"),
                status="pending",
                assignee_id=user_id,
                node_config=node
            )
            self.db.add(task)
            await self.db.flush()
            await self._send_notification(user_id, node.get("name", ""), instance_id)
    
    async def _handle_cc_node(self, instance_id: int, node: Dict, variables: Dict):
        """处理抄送节点 - 发送通知，不阻塞流程"""
        config = node.get("config", {})
        cc_users = config.get("cc_users", [])
        
        for user_id in cc_users:
            uid = user_id.get("user_id") if isinstance(user_id, dict) else user_id
            if uid:
                await self._send_notification(uid, f"抄送：{node.get('name', '')}", instance_id)
        
        # 抄送不阻塞，立即流转
        await self._auto_goto_next(instance_id, node)
    
    async def _handle_data_fill_node(self, instance_id: int, node: Dict, variables: Dict):
        """处理数据填报节点 - 创建待填报任务"""
        config = node.get("config", {})
        assignees = config.get("assignees", [])
        
        if not assignees:
            await self._auto_goto_next(instance_id, node)
            return
        
        for assignee in assignees:
            user_id = assignee.get("user_id") if isinstance(assignee, dict) else assignee
            if not user_id:
                continue
            task = WorkflowTask(
                instance_id=instance_id,
                node_id=node["id"],
                node_name=node.get("name", "未命名"),
                node_type="data_fill",
                status="pending",
                assignee_id=user_id,
                node_config=node
            )
            self.db.add(task)
            await self.db.flush()
            await self._send_notification(user_id, f"数据填报：{node.get('name', '')}", instance_id)
    
    async def _handle_sub_process_node(self, instance_id: int, node: Dict, variables: Dict):
        """处理子流程节点"""
        config = node.get("config", {})
        sub_workflow_id = config.get("sub_workflow_id")
        
        # 启动子流程
        sub_instance = await self.start_instance(
            workflow_id=sub_workflow_id,
            title=f"子流程-{node.get('name', '')}",
            starter_id=variables.get("starter_id"),
            variables=variables,
            form_data_id=None
        )
        # 记录父子关系
        sub_instance.parent_instance_id = instance_id
        await self.db.commit()
    
    async def _end_instance(self, instance_id: int):
        """结束流程实例"""
        result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance_id))
        instance = result.scalar_one()
        instance.status = "approved"
        instance.completed_at = datetime.now()
        await self.db.commit()
    
    # ===== AI 节点处理函数（升级方案 4.2） =====
    async def _handle_ai_approval_node(self, instance_id: int, node: Dict, variables: Dict):
        """AI 自动审批节点"""
        config = node.get("config", {})
        
        # 获取表单数据
        form_data = variables.get("form_data", {})
        
        # 构建审批上下文
        context = {
            "applicant": variables.get("applicant_name", ""),
            "amount": form_data.get("amount", 0),
            "reason": form_data.get("reason", ""),
            "history": [],  # 简化处理，实际应获取历史审批记录
            "rules": config.get("rules", []),
        }
        
        try:
            # 调用 AI 审批能力
            from app.core.ai_digital_base.capability_registry import capability_registry, AICapability
            result = await capability_registry.execute(
                AICapability.AI_APPROVE,
                {
                    "action": "approve",
                    "context": context,
                    "knowledge_base_id": config.get("knowledge_base_id"),
                }
            )
            
            decision = result.get("decision", "escalate")  # "approve" | "reject" | "escalate"
            ai_opinion = result.get("opinion", "")
            confidence = result.get("confidence", 0)
            
            # 记录 AI 审批日志
            logger = logging.getLogger(__name__)
            logger.info(f"AI 审批节点 {node['id']}: decision={decision}, confidence={confidence}")
            
            # 低置信度时转人工
            threshold = config.get("confidence_threshold", 0.8)
            if confidence < threshold or decision == "escalate":
                # 转人工审批
                await self._handle_approval_node(instance_id, node, variables)
            else:
                # AI 直接审批，自动流转
                if decision == "approve":
                    await self._auto_goto_next(instance_id, node)
                else:
                    # 拒绝，结束流程
                    inst_result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance_id))
                    instance = inst_result.scalar_one()
                    instance.status = "rejected"
                    instance.completed_at = datetime.now()
                    await self.db.commit()
                    
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"AI 审批节点执行失败: {e}")
            # 出错时转人工审批
            await self._handle_approval_node(instance_id, node, variables)
    
    async def _handle_ai_review_node(self, instance_id: int, node: Dict, variables: Dict):
        """AI 审核建议节点（人工最终确认）"""
        config = node.get("config", {})
        form_data = variables.get("form_data", {})
        
        context = {
            "applicant": variables.get("applicant_name", ""),
            "amount": form_data.get("amount", 0),
            "reason": form_data.get("reason", ""),
        }
        
        try:
            from app.core.ai_digital_base.capability_registry import capability_registry, AICapability
            result = await capability_registry.execute(
                AICapability.AI_APPROVE,
                {
                    "action": "review",
                    "context": context,
                }
            )
            
            # 将 AI 建议存入变量，供人工审批参考
            ai_suggestion = {
                "suggestion": result.get("suggestion", ""),
                "risk_level": result.get("risk_level", "low"),
                "confidence": result.get("confidence", 0),
            }
            variables["ai_review_result"] = ai_suggestion
            
            # 创建人工审批任务（携带 AI 建议）
            await self._handle_approval_node(instance_id, node, variables)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"AI 审核建议节点执行失败: {e}")
            # 出错时直接创建人工审批任务
            await self._handle_approval_node(instance_id, node, variables)
    
    async def _handle_ai_classify_node(self, instance_id: int, node: Dict, variables: Dict):
        """AI 分类路由节点"""
        config = node.get("config", {})
        form_data = variables.get("form_data", {})
        
        content = form_data.get("content", "")
        categories = config.get("categories", [])
        
        if not categories:
            # 没有配置分类，直接进入默认分支
            await self._auto_goto_next(instance_id, node)
            return
        
        try:
            from app.core.ai_digital_base.capability_registry import capability_registry, AICapability
            result = await capability_registry.execute(
                AICapability.AI_CLASSIFY,
                {
                    "content": content,
                    "categories": categories,
                }
            )
            
            classified_category = result.get("category", categories[0])
            confidence = result.get("confidence", 0)
            
            logger = logging.getLogger(__name__)
            logger.info(f"AI 分类节点 {node['id']}: category={classified_category}, confidence={confidence}")
            
            # 根据分类结果选择分支
            # 获取流程定义
            inst_result = await self.db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance_id))
            instance = inst_result.scalar_one()
            wf_result = await self.db.execute(select(Workflow).where(Workflow.id == instance.workflow_id))
            workflow = wf_result.scalar_one()
            
            # 查找匹配的出边
            edges = workflow.edges or []
            for edge in edges:
                if edge.get("source") == node["id"]:
                    edge_label = edge.get("label", "")
                    if edge_label == classified_category or edge_label in ["默认", "default", "other"]:
                        target_id = edge.get("target")
                        for workflow_node in workflow.nodes:
                            if workflow_node.get("id") == target_id:
                                await self._enter_node(instance_id, workflow_node, variables)
                                return
            
            # 没有找到匹配分支，进入默认下一节点
            await self._auto_goto_next(instance_id, node)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"AI 分类节点执行失败: {e}")
            # 出错时进入默认分支
            await self._auto_goto_next(instance_id, node)
    
    async def _handle_notification_node(self, instance_id: int, node: Dict, variables: Dict):
        """通知节点"""
        config = node.get("config", {})
        
        message = config.get("message", "")
        recipients = config.get("recipients", [])
        channel = config.get("channel", "in_app")  # in_app | email | sms
        
        # 渲染消息模板
        rendered_message = await self.condition_evaluator.render_expression(message, variables)
        
        logger = logging.getLogger(__name__)
        logger.info(f"通知节点 {node['id']}: channel={channel}, recipients={recipients}, message={rendered_message[:50]}...")
        
        # 实际实现：调用通知服务发送消息
        # 这里简化处理，仅记录日志
        for recipient in recipients:
            user_id = recipient.get("user_id")
            if user_id:
                await self._send_notification(user_id, rendered_message, instance_id)
        
        # 自动进入下一节点
        await self._auto_goto_next(instance_id, node)