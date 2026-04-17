"""
智能体引擎 - 流程审批智能体
"""
from typing import Dict, Any
from app.core.agent_engine.orchestrator import BaseAgent, AgentType, Task
from app.core.ai_digital_base.inference import inference_service


class WorkflowAgent(BaseAgent):
    """流程审批智能体"""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.WORKFLOW_AGENT,
            name="流程审批助手",
            description="帮助用户设计和优化业务流程审批"
        )
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行流程审批任务"""
        action = task.input_data.get("action", "design")
        
        if action == "design":
            # 设计新流程
            description = task.input_data.get("description", "")
            return await self._design_workflow(description)
        
        elif action == "optimize":
            # 优化现有流程
            workflow_data = task.input_data.get("workflow_data", {})
            return await self._optimize_workflow(workflow_data)
        
        elif action == "recommend":
            # 推荐审批人
            context = task.input_data.get("context", {})
            return await self._recommend_approvers(context)
        
        elif action == "summarize":
            # 总结审批内容
            content = task.input_data.get("content", "")
            return await self._summarize_approval(content)
        
        return {"error": "Unknown action"}
    
    async def _design_workflow(self, description: str) -> Dict[str, Any]:
        """设计工作流程"""
        result = await inference_service.explain_workflow(description)
        self.add_to_memory({
            "type": "workflow_designed",
            "description": description,
            "result": result
        })
        return result
    
    async def _optimize_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化工作流程"""
        return await inference_service.explain_workflow(
            f"现有流程：{workflow_data.get('name', '')}\n描述：{workflow_data.get('description', '')}"
        )
    
    async def _recommend_approvers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """推荐审批人"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个审批流程专家。根据业务上下文，推荐合适的审批人。

考虑因素：
- 审批金额或重要程度
- 部门或业务类型
- 历史审批记录
- 当前在岗情况

输出JSON格式：
{
    "recommended_approvers": [
        {"user_id": "xxx", "name": "姓名", "reason": "推荐原因"}
    ],
    "approval_levels": [
        {"level": 1, "threshold": "金额范围", "approvers": []}
    ]
}"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"业务上下文：{context}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return {"error": "解析失败"}
    
    async def _summarize_approval(self, content: str) -> Dict[str, Any]:
        """总结审批内容"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个审批助手。快速总结审批申请的核心内容，并提供审批建议。

输出JSON格式：
{
    "summary": "一句话总结",
    "key_points": ["要点1", "要点2"],
    "risk_level": "low/medium/high",
    "suggestions": ["建议1", "建议2"]
}"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"审批内容：\n{content}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            import json
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return {"summary": result["content"]}
