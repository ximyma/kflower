<!--
  Phase 1 清理：原 402 行纯 mock 数据页面已降级为占位页
  原页面所有数据（路由策略/限流配置/端点列表/开发进度）均为硬编码假数据
  AI 网关配置功能已并入 AIDigitalBase 页面
-->
<template>
  <UnderConstruction
    title="AI 网关"
    message="AI 网关配置和管理功能正在进行架构整合，将合并到 AI 数字底座模块中。"
    phase="Phase 3 计划重构"
  />
</template>

<script setup lang="ts">
import UnderConstruction from '@/common/components/UnderConstruction.vue'
</script>
