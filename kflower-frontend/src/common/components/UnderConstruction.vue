<template>
  <div class="under-construction">
    <div class="uc-content">
      <el-icon class="uc-icon"><Tools /></el-icon>
      <h2>{{ title }}</h2>
      <p>{{ message }}</p>
      <el-tag v-if="phase" type="warning" size="large">{{ phase }}</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tools } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '功能规划中' },
  message: { type: String, default: '该功能正在进行架构优化，即将以更好的体验回归。' },
  phase: { type: String, default: '' }
})
</script>

<style scoped>
.under-construction {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 60px 20px;
}
.uc-content {
  text-align: center;
  max-width: 500px;
}
.uc-icon {
  font-size: 64px;
  color: #c0c4cc;
  margin-bottom: 20px;
}
.uc-content h2 {
  font-size: 24px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}
.uc-content p {
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
  margin-bottom: 20px;
}
</style>
