"""
流程节点类型枚举
"""
from enum import Enum


class NodeType(str, Enum):
    """节点类型"""
    START = "start"
    END = "end"
    APPROVAL = "approval"      # 审批节点
    TASK = "task"              # 办理节点（无审批动作）
    CC = "cc"                  # 抄送节点
    DATA_FILL = "data_fill"    # 数据填报节点
    CONDITION = "condition"    # 条件分支
    PARALLEL = "parallel"      # 并行分支
    PARALLEL_JOIN = "parallel_join"
    SUB_PROCESS = "sub_process"
    TRIGGER = "trigger"        # 触发节点（调用插件）
    DATA_CHANGE = "data_change" # 数据变化节点（增/改/删）
    DELAY = "delay"            # 延迟节点（定时器）