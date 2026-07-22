<!--
  Phase 1 清理：原 2595 行原型页面已降级为占位页
  原页面包含拖拽画布/组件面板/执行日志/聊天对话框等大量 UI 组件
  但零后端集成，所有数据均为硬编码 mock
  智能体编排功能将在 Phase 2 Agent 重构时重新实现
-->
<template>
  <UnderConstruction
    title="智能体编排器"
    message="智能体编排功能正在进行重构，Phase 2 将基于 ReAct Agent 架构重新实现真智能体编排能力。"
    phase="Phase 2 计划重构"
  />
</template>

<script setup lang="ts">
import UnderConstruction from '@/common/components/UnderConstruction.vue'
</script>
