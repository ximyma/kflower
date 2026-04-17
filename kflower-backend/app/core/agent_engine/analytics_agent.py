"""
智能体引擎 - 决策分析智能体
"""
from typing import Dict, Any
from app.core.agent_engine.orchestrator import BaseAgent, AgentType, Task
from app.core.ai_digital_base.inference import inference_service


class AnalyticsAgent(BaseAgent):
    """决策分析智能体"""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.ANALYTICS_AGENT,
            name="数据分析助手",
            description="帮助用户进行数据分析和可视化"
        )
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行分析任务"""
        action = task.input_data.get("action", "query")
        
        if action == "query":
            # 自然语言数据查询
            query = task.input_data.get("query", "")
            data_context = task.input_data.get("data_context", "")
            return await self._query_data(query, data_context)
        
        elif action == "chart":
            # 生成图表配置
            query = task.input_data.get("query", "")
            data_description = task.input_data.get("data_description", "")
            return await self._generate_chart(query, data_description)
        
        elif action == "analyze":
            # 深度分析
            data = task.input_data.get("data", "")
            analysis_type = task.input_data.get("analysis_type", "general")
            return await self._analyze_data(data, analysis_type)
        
        return {"error": "Unknown action"}
    
    async def _query_data(self, query: str, data_context: str) -> Dict[str, Any]:
        """自然语言数据查询"""
        result = await inference_service.analyze_data(query, data_context)
        self.add_to_memory({
            "type": "data_query",
            "query": query,
            "result": result
        })
        return result
    
    async def _generate_chart(self, query: str, data_description: str) -> Dict[str, Any]:
        """生成图表配置"""
        result = await inference_service.generate_chart_config(query, data_description)
        self.add_to_memory({
            "type": "chart_generated",
            "query": query,
            "config": result
        })
        return result
    
    async def _analyze_data(self, data: str, analysis_type: str) -> Dict[str, Any]:
        """深度数据分析"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        prompts = {
            "trend": "趋势分析：识别数据中的趋势和模式",
            "anomaly": "异常检测：发现数据中的异常值",
            "correlation": "相关性分析：找出变量之间的关系",
            "forecast": "预测分析：基于历史数据预测未来",
            "general": "综合分析：提供全面的数据分析"
        }
        
        system_prompt = f"""你是一个数据分析专家。进行{prompts.get(analysis_type, '综合分析')}。

分析数据，提供：
1. 主要发现
2. 关键指标
3. 异常情况（如有）
4. 建议和行动项"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"分析数据：\n{data}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        return {"analysis": result["content"], "analysis_type": analysis_type}
