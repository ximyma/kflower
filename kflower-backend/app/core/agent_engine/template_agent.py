"""
智能体引擎 - 模板设计智能体
"""
from typing import Dict, Any
from app.core.agent_engine.orchestrator import BaseAgent, AgentType, Task
from app.core.ai_digital_base.inference import inference_service


class TemplateAgent(BaseAgent):
    """模板设计智能体"""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.TEMPLATE_AGENT,
            name="模板设计助手",
            description="帮助用户创建和管理业务模板，支持对话式生成"
        )
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行模板设计任务"""
        action = task.input_data.get("action", "generate")
        
        if action == "generate":
            # 根据描述生成模板
            description = task.input_data.get("description", "")
            return await self._generate_template(description)
        
        elif action == "suggest_fields":
            # 推荐字段
            module_name = task.input_data.get("module_name", "")
            description = task.input_data.get("description", "")
            fields = await inference_service.suggest_fields(module_name, description)
            return {"fields": fields}
        
        elif action == "optimize":
            # 优化现有模板
            template_data = task.input_data.get("template_data", {})
            return await self._optimize_template(template_data)
        
        return {"error": "Unknown action"}
    
    async def _generate_template(self, description: str) -> Dict[str, Any]:
        """生成模板"""
        result = await inference_service.generate_template(description)
        self.add_to_memory({
            "type": "template_generated",
            "description": description,
            "result": result
        })
        return result
    
    async def _optimize_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化模板"""
        system_prompt = """你是一个模板优化专家。分析提供的模板，找出优化建议。

输出JSON格式：
{
    "optimizations": ["建议1", "建议2", ...],
    "potential_issues": ["问题1", ...],
    "improved_template": {优化后的模板}
}"""
        
        from app.core.ai_digital_base.gateway import ai_gateway
        import json
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"优化以下模板：{json.dumps(template_data, ensure_ascii=False)}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        try:
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return {"suggestions": result["content"]}
