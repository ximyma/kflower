<template>
  <div class="digital-base-panel">
    <div class="panel-header">
      <h3>AI 数字底座状态</h3>
      <el-button size="small" @click="loadStatus" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <el-descriptions :column="2" border v-loading="loading">
      <el-descriptions-item label="网关状态">
        <el-tag :type="statusData.gatewayOnline ? 'success' : 'danger'">
          {{ statusData.gatewayOnline ? '在线' : '离线' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="当前提供商">
        <el-tag type="info">{{ statusData.provider || '未配置' }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="模型总数">
        {{ statusData.totalModels }}
      </el-descriptions-item>
      <el-descriptions-item label="活跃对话">
        {{ statusData.activeConversations }}
      </el-descriptions-item>
      <el-descriptions-item label="整体状态">
        <el-tag :type="statusData.healthy ? 'success' : 'warning'">
          {{ statusData.healthy ? '健康' : '降级' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="可用提供商">
        <el-tag v-for="p in statusData.providers" :key="p" size="small" style="margin:2px">{{ p }}</el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <el-card style="margin-top:16px" shadow="never">
      <template #header><span>模型配置</span></template>
      <div v-if="statusData.providers.length === 0" style="color:#909399;text-align:center;padding:20px">
        暂未配置 AI 模型，请前往「系统设置」配置
      </div>
      <div v-else>
        <el-button type="primary" plain size="small" @click="$router.push('/settings?tab=ai-models')">
          前往配置 AI 模型
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { aiAPI } from '@/common/api'

const loading = ref(false)
const statusData = reactive({
  gatewayOnline: false,
  provider: '',
  totalModels: 0,
  activeConversations: 0,
  healthy: false,
  providers: [] as string[]
})

async function loadStatus() {
  loading.value = true
  try {
    const res = await aiAPI.getDigitalBaseStatus()
    const data = res?.data || res || {}
    statusData.gatewayOnline = data.health?.ai_gateway === true
    statusData.provider = data.gateway?.current_provider || ''
    statusData.totalModels = data.model_manager?.total_models || 0
    statusData.activeConversations = data.conversation_manager?.active_conversations || 0
    statusData.healthy = data.overall_status === 'healthy'
    statusData.providers = data.gateway?.available_providers || []
  } catch { /* 静默 */ }
  loading.value = false
}

onMounted(() => loadStatus())
</script>

<style scoped>
.digital-base-panel { padding: 4px 0; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { margin: 0; font-size: 16px; }
</style>
