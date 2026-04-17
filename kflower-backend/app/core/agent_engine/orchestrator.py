"""
智能体引擎 - 智能体编排器
核心的多智能体协作编排引擎
"""
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import json


class AgentType(Enum):
    """智能体类型"""
    TEMPLATE_AGENT = "template_agent"      # 模板设计智能体
    WORKFLOW_AGENT = "workflow_agent"      # 流程审批智能体
    ANALYTICS_AGENT = "analytics_agent"   # 决策分析智能体
    QUERY_AGENT = "query_agent"           # 数据查询智能体
    PERMISSION_AGENT = "permission_agent" # 权限管理智能体
    GENERAL_AGENT = "general_agent"       # 通用智能体


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
        """初始化默认智能体"""
        from app.core.agent_engine.template_agent import TemplateAgent
        from app.core.agent_engine.workflow_agent import WorkflowAgent
        from app.core.agent_engine.analytics_agent import AnalyticsAgent
        from app.core.agent_engine.query_agent import QueryAgent
        
        # 注册默认智能体
        self.register_agent(TemplateAgent())
        self.register_agent(WorkflowAgent())
        self.register_agent(AnalyticsAgent())
        self.register_agent(QueryAgent())
    
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


# 全局智能体编排器实例
agent_orchestrator = AgentOrchestrator()
