"""
工作流核心模块
"""
from .node_types import NodeType
from .condition_evaluator import ConditionEvaluator
from .assignee_resolver import AssigneeResolver
from .engine import WorkflowEngine

__all__ = [
    "NodeType",
    "ConditionEvaluator",
    "AssigneeResolver", 
    "WorkflowEngine"
]