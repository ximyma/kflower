"""
智能体引擎 - 智能体编排器
核心的多智能体协作编排引擎
"""
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import json


class AgentType(Enum):
    """智能体类型（Phase 2 精简：移除 4 个伪 Agent，保留核心类型）"""
    GENERAL_AGENT = "general_agent"       # 通用 ReAct 智能体（统一入口）


class Task:
    """任务对象"""
    def __init__(
        self,
        task_id: str,
        description: str,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        priority: int = 1
    ):
        self.task_id = task_id
        self.description = description
        self.agent_type = agent_type
        self.input_data = input_data
        self.priority = priority
        self.status = "pending"  # pending, running, completed, failed
        self.result: Optional[Dict[str, Any]] = None
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class BaseAgent:
    """
    基础智能体类
    所有具体智能体的父类
    """
    
    def __init__(self, agent_type: AgentType, name: str, description: str):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.tools: List[Callable] = []
        self.memory: List[Dict[str, Any]] = []
    
    def add_tool(self, tool: Callable) -> None:
        """添加工具"""
        self.tools.append(tool)
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行任务"""
        raise NotImplementedError
    
    def add_to_memory(self, entry: Dict[str, Any]) -> None:
        """添加到记忆"""
        self.memory.append({
            "timestamp": datetime.now().isoformat(),
            **entry
        })
    
    def get_recent_memory(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的记忆"""
        return self.memory[-count:]


class UnifiedReactAgent(BaseAgent):
    """
    统一 ReAct 智能体（Phase 2 重构）
    接管原 4 个伪 Agent 的所有功能，基于 agent_service 的 ReAct 循环实现真正的自主决策
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.GENERAL_AGENT,
            name="统一智能体",
            description="基于 ReAct 循环的通用智能体，支持工具调用和自主决策"
        )
    
    async def execute(self, task: Task) -> Dict[str, Any]:
        """执行任务：委托给 agent_service 的 ReAct 循环"""
        try:
            from app.core.agent_engine.agent_service import agent_service
            
            action = task.input_data.get("action", "chat")
            message = task.input_data.get("message", task.description)
            model = task.input_data.get("model")
            
            if action == "chat" or action == "query":
                result = await agent_service.chat(
                    message=message,
                    model=model,
                    history=task.input_data.get("history", []),
                    use_tools=task.input_data.get("use_tools", True)
                )
                return {"success": True, "response": result.get("response", ""), "data": result}
            
            elif action == "generate_template":
                result = await agent_service.generate_template(message)
                return {"success": True, "data": result}
            
            elif action == "analyze":
                result = await agent_service.analyze_intent(message)
                return {"success": True, "data": result}
            
            else:
                # 默认走 ReAct 对话
                result = await agent_service.chat(
                    message=message,
                    model=model,
                    use_tools=True
                )
                return {"success": True, "response": result.get("response", "")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


class AgentOrchestrator:
    """
    智能体编排器
    管理和调度多个智能体协作完成任务
    """
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self._init_default_agents()
    
    def _init_default_agents(self):
        """初始化默认智能体（Phase 2：统一 ReAct Agent）"""
        # 注册统一 ReAct 智能体，接管所有任务类型
        self.register_agent(UnifiedReactAgent())
    
    def register_agent(self, agent: BaseAgent) -> None:
        """注册智能体"""
        self.agents[agent.agent_type] = agent
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """执行单个任务"""
        agent = self.agents.get(task.agent_type)
        if not agent:
            return {"error": f"Agent {task.agent_type.value} not found"}
        
        task.status = "running"
        try:
            result = await agent.execute(task)
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()
            self.completed_tasks.append(task)
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            return {"error": str(e)}
    
    async def execute_multi_agent_task(
        self,
        tasks: List[Task],
        coordination_strategy: str = "sequential"
    ) -> List[Dict[str, Any]]:
        """
        执行多智能体协作任务
        
        Args:
            tasks: 任务列表
            coordination_strategy: 协作策略
                - sequential: 顺序执行
                - parallel: 并行执行
                - hierarchical: 分层执行
        """
        if coordination_strategy == "sequential":
            results = []
            for task in tasks:
                result = await self.execute_task(task)
                results.append(result)
                # 如果某个任务失败，可以选择停止或继续
            return results
        
        elif coordination_strategy == "parallel":
            import asyncio
            results = await asyncio.gather(
                *[self.execute_task(task) for task in tasks],
                return_exceptions=True
            )
            return results
        
        elif coordination_strategy == "hierarchical":
            # 分层执行：先执行主任务，再执行子任务
            results = []
            main_task = tasks[0]
            main_result = await self.execute_task(main_task)
            results.append(main_result)
            
            # 根据主任务结果，生成子任务
            sub_tasks = self._generate_sub_tasks(main_result, tasks[1:])
            for sub_task in sub_tasks:
                sub_result = await self.execute_task(sub_task)
                results.append(sub_result)
            
            return results
        
        return []
    
    def _generate_sub_tasks(
        self,
        main_result: Dict[str, Any],
        available_tasks: List[Task]
    ) -> List[Task]:
        """根据主任务结果生成子任务"""
        # 简单的实现：返回所有可用任务
        # 实际应该根据主任务结果动态生成
        return available_tasks
    
    def get_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """获取指定类型的智能体"""
        return self.agents.get(agent_type)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有注册的智能体"""
        return [
            {
                "type": agent.agent_type.value,
                "name": agent.name,
                "description": agent.description,
                "tools_count": len(agent.tools)
            }
            for agent in self.agents.values()
        ]
    
    def get_task_history(self, count: int = 20) -> List[Dict[str, Any]]:
        """获取任务历史"""
        all_tasks = self.completed_tasks + [t for t in self.task_queue if t.status == "pending"]
        all_tasks.sort(key=lambda x: x.created_at, reverse=True)
        return [task.to_dict() for task in all_tasks[:count]]
    
    def is_running(self) -> bool:
        """判断编排器是否有正在执行的任务"""
        return any(t.status == "running" for t in self.task_queue)
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务执行统计信息"""
        all_tasks = self.task_queue + self.completed_tasks
        status_count = {}
        for t in all_tasks:
            status_count[t.status] = status_count.get(t.status, 0) + 1
        return {
            "total": len(all_tasks),
            "pending": status_count.get("pending", 0),
            "running": status_count.get("running", 0),
            "completed": status_count.get("completed", 0),
            "failed": status_count.get("failed", 0)
        }
    
    def get_tasks(self, status_filter: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """按状态过滤获取任务列表"""
        all_tasks = self.task_queue + self.completed_tasks
        if status_filter:
            all_tasks = [t for t in all_tasks if t.status == status_filter]
        all_tasks.sort(key=lambda x: x.created_at, reverse=True)
        return [t.to_dict() for t in all_tasks[:limit]]


# 全局智能体编排器实例
agent_orchestrator = AgentOrchestrator()
