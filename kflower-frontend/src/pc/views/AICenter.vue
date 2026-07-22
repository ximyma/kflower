<template>
  <div class="ai-center-page">
    <div class="page-header">
      <h2>AI 能力中心</h2>
      <p class="subtitle">统一的 AI 功能入口：对话、工具集、智能体管理、数字底座</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="ai-tabs">
      <!-- Tab 1: AI 对话 -->
      <el-tab-pane label="AI 对话" name="chat">
        <AIChatDialog />
      </el-tab-pane>

      <!-- Tab 2: 工具集 -->
      <el-tab-pane label="工具集" name="tools">
        <ToolsPanel />
      </el-tab-pane>

      <!-- Tab 3: 智能体 -->
      <el-tab-pane label="智能体" name="agents">
        <AgentsPanel />
      </el-tab-pane>

      <!-- Tab 4: 数字底座 -->
      <el-tab-pane label="数字底座" name="digital-base">
        <DigitalBasePanel />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AIChatDialog from '@/common/components/AIChatDialog.vue'
import ToolsPanel from './ai-center/ToolsPanel.vue'
import AgentsPanel from './ai-center/AgentsPanel.vue'
import DigitalBasePanel from './ai-center/DigitalBasePanel.vue'

const activeTab = ref('chat')
</script>

<style scoped>
.ai-center-page { padding: 0; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; color: var(--el-text-color-primary); }
.subtitle { margin: 6px 0 0; color: var(--el-text-color-regular); font-size: 14px; }
.ai-tabs { background: var(--el-bg-color); min-height: 500px; }
</style>
