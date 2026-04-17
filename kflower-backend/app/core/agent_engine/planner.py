"""
智能体引擎 - 任务规划器
将复杂任务分解为可执行的子任务
"""
from typing import List, Dict, Any, Optional
from app.core.agent_engine.orchestrator import Task, AgentType
from app.core.ai_digital_base.gateway import ai_gateway
import json


class TaskPlanner:
    """
    任务规划器
    将用户复杂请求分解为可执行的智能体任务序列
    """
    
    def __init__(self):
        self.gateway = ai_gateway
    
    async def decompose_task(self, user_request: str) -> List[Dict[str, Any]]:
        """
        将复杂任务分解为子任务
        
        Returns:
            子任务列表，每个子任务包含:
            {
                "description": "任务描述",
                "agent_type": "智能体类型",
                "priority": 优先级,
                "dependencies": ["前置任务ID"]
            }
        """
        system_prompt = """你是一个任务分解专家。用户描述一个复杂请求，你需要将其分解为可执行的子任务。

考虑以下智能体类型：
- template_agent: 模板设计相关
- workflow_agent: 流程审批相关
- analytics_agent: 决策分析相关
- query_agent: 数据查询相关
- permission_agent: 权限管理相关
- general_agent: 通用任务

输出JSON数组格式：
[
    {
        "task_id": "task_1",
        "description": "子任务描述",
        "agent_type": "智能体类型",
        "priority": 1,
        "dependencies": []
    }
]"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"分解以下任务：{user_request}"
        )
        
        if "error" in result:
            return [{"task_id": "error", "description": user_request, "agent_type": "general_agent", "priority": 1}]
        
        try:
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            tasks = json.loads(content)
            return tasks
        except:
            # 解析失败，返回默认任务
            return [
                {
                    "task_id": "task_1",
                    "description": user_request,
                    "agent_type": "general_agent",
                    "priority": 1,
                    "dependencies": []
                }
            ]
    
    async def plan_execution_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """
        规划执行顺序
        根据依赖关系确定任务的执行顺序
        """
        # 构建依赖图
        task_ids = {t["task_id"] for t in tasks}
        dependency_graph: Dict[str, List[str]] = {t["task_id"]: t.get("dependencies", []) for t in tasks}
        
        # 拓扑排序
        sorted_ids = []
        visited = set()
        
        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            for dep in dependency_graph.get(task_id, []):
                if dep in task_ids:
                    visit(dep)
            sorted_ids.append(task_id)
        
        for task_id in dependency_graph:
            visit(task_id)
        
        return sorted_ids
    
    async def estimate_task_complexity(self, task_description: str) -> Dict[str, Any]:
        """估算任务复杂度"""
        system_prompt = """分析以下任务的复杂度：

输出JSON格式：
{
    "complexity": "low/medium/high",
    "estimated_time_minutes": 预估时间(分钟),
    "requires_multi_agent": true/false,
    "required_capabilities": ["能力1", "能力2"]
}"""

        result = await self.gateway.chat_with_system_prompt(
            system_prompt=system_prompt,
            user_message=f"分析任务：{task_description}"
        )
        
        if "error" in result:
            return {"complexity": "medium", "estimated_time_minutes": 5}
        
        try:
            content = result["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except:
            return {"complexity": "medium", "estimated_time_minutes": 5}


# 全局任务规划器实例
task_planner = TaskPlanner()
