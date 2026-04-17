"""
智能体引擎 - 数据查询智能体
"""
from typing import Dict, Any
from app.core.agent_engine.orchestrator import BaseAgent, AgentType, Task


class QueryAgent(BaseAgent):
    """数据查询智能体"""
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.QUERY_AGENT,
            name="数据查询助手",
            description="帮助用户查询和处理业务数据"
        )
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行查询任务"""
        action = task.input_data.get("action", "query")
        
        if action == "query":
            # 执行查询
            table = task.input_data.get("table", "")
            conditions = task.input_data.get("conditions", {})
            return await self._execute_query(table, conditions)
        
        elif action == "aggregate":
            # 聚合查询
            table = task.input_data.get("table", "")
            metrics = task.input_data.get("metrics", [])
            group_by = task.input_data.get("group_by", [])
            return await self._aggregate_query(table, metrics, group_by)
        
        elif action == "explain":
            # 解释查询结果
            query_result = task.input_data.get("result", {})
            return await self._explain_result(query_result)
        
        return {"error": "Unknown action"}
    
    async def _execute_query(self, table: str, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据查询"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个数据查询专家。将用户的查询条件转换为SQL或API查询参数。

根据表名和条件，返回JSON格式：
{
    "sql": "SELECT * FROM table WHERE ...",
    "api_params": {"key": "value"},
    "estimated_rows": 预估行数
}"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"表名：{table}\n条件：{conditions}"
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
            return {"sql": f"SELECT * FROM {table}"}
    
    async def _aggregate_query(
        self,
        table: str,
        metrics: list,
        group_by: list
    ) -> Dict[str, Any]:
        """聚合查询"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个数据查询专家。生成聚合查询SQL。

输出JSON格式：
{
    "sql": "SELECT SUM(x), AVG(y) FROM table GROUP BY z",
    "description": "查询说明"
}"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"表名：{table}\n指标：{metrics}\n分组：{group_by}"
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
            return {"sql": f"SELECT {','.join(metrics)} FROM {table} GROUP BY {','.join(group_by)}"}
    
    async def _explain_result(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """解释查询结果"""
        from app.core.ai_digital_base.gateway import ai_gateway
        
        system_prompt = """你是一个数据分析师。解释查询结果，用通俗易懂的语言说明数据含义。"""
        
        result = await ai_gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"查询结果：\n{query_result}"
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        return {"explanation": result["content"]}
