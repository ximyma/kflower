<!--
  Phase 1 清理：原 662 行纯 mock 数据页面已降级为占位页
  原页面显示 6 个假数据库连接 + 5 个假同步任务 + 假数据质量指标
  数据集成功能将合并到数据迁移模块中统一管理
-->
<template>
  <UnderConstruction
    title="数据集成"
    message="数据集成功能正在进行模块整合，将合并到数据迁移模块中提供统一的数据接入体验。"
    phase="Phase 3 计划整合"
  />
</template>

<script setup lang="ts">
import UnderConstruction from '@/common/components/UnderConstruction.vue'
</script>
