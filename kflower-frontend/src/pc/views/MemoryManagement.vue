<!--
  Phase 1 清理：原 672 行半功能页面已降级为占位页
  原页面调用的 /memory/stats 和 /memory/list 端点已移除（返回硬编码空数据）
  记忆管理功能将在 Phase 2 Agent 重构时基于真实持久化存储重新实现
-->
<template>
  <UnderConstruction
    title="记忆管理"
    message="智能体长期记忆与短期记忆管理功能正在重构中，Phase 2 将基于数据库持久化重新实现。"
    phase="Phase 2 计划重构"
  />
</template>

<script setup lang="ts">
import UnderConstruction from '@/common/components/UnderConstruction.vue'
</script>
