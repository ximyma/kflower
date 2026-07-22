<template>
  <div class="app-ai-base">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>AI数字底座</h2>
      <el-button type="primary" size="small" @click="refreshStatus">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>
    
    <!-- 状态概览 -->
    <div class="status-overview" v-loading="loading">
      <div class="status-card" v-for="item in statusItems" :key="item.key">
        <div class="status-icon" :class="item.status">
          <el-icon :size="24"><component :is="item.icon" /></el-icon>
        </div>
        <div class="status-info">
          <span class="status-name">{{ item.name }}</span>
          <span class="status-value">{{ item.value }}</span>
        </div>
        <div class="status-badge" :class="item.status">
          {{ item.status === 'online' ? '在线' : '离线' }}
        </div>
      </div>
    </div>
    
    <!-- 模型管理 -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">
          <el-icon :size="20" color="#67C23A"><Box /></el-icon>
          <span>模型管理</span>
        </div>
      </div>
      <div class="model-list">
        <div v-if="models.length === 0" class="empty-text">暂无配置的模型</div>
        <div v-for="model in models" :key="model.name" class="model-item">
          <div class="model-icon">
            <el-icon :size="18"><Cpu /></el-icon>
          </div>
          <div class="model-info">
            <span class="model-name">{{ model.name }}</span>
            <span class="model-provider">{{ model.provider }}</span>
          </div>
          <el-tag size="small" :type="model.enabled ? 'success' : 'info'">
            {{ model.enabled ? '已启用' : '未启用' }}
          </el-tag>
        </div>
      </div>
    </div>
    
    <!-- Phase 1: 网关统计和使用统计 mock 端点已移除，
         后续 Phase 3 将基于真实数据重新实现 -->
    
    <!-- 配置入口 -->
    <div class="config-tip" @click="openConfig">
      <el-icon :size="20"><Setting /></el-icon>
      <span>高级配置需要在电脑端进行</span>
      <el-icon :size="16"><ArrowRight /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { Refresh, Connection, Box, Cpu, Setting, ArrowRight, Monitor, Cloudy } from '@element-plus/icons-vue'
import { aiAPI } from '../../common/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)

const statusItems = ref([
  { key: 'gateway', name: 'AI网关', status: 'online', icon: 'Connection', value: '运行中' },
  { key: 'models', name: '模型服务', status: 'online', icon: 'Cpu', value: '正常' },
  { key: 'vector', name: '向量服务', status: 'online', icon: 'Cloudy', value: '正常' },
  { key: 'monitor', name: '监控服务', status: 'online', icon: 'Monitor', value: '正常' }
])

const gatewayStats = ref<any>(null)  // mock 端点已移除
const models = ref<any[]>([])
const usageStats = ref<any>(null)  // mock 端点已移除

async function loadStatus() {
  loading.value = true
  try {
    const [statusRes, modelRes] = await Promise.allSettled([
      aiAPI.getDigitalBaseStatus(),
      aiAPI.getDigitalBaseModels()
    ])
    
    if (statusRes.status === 'fulfilled') {
      const data = statusRes.value?.data || statusRes.value || {}
      if (data.health?.ai_gateway) statusItems.value[0].status = 'online'
      else statusItems.value[0].status = 'offline'
      if (data.model_manager?.total_models > 0) statusItems.value[1].status = 'online'
      else statusItems.value[1].status = 'offline'
    }
    
    if (modelRes.status === 'fulfilled') {
      const data = modelRes.value?.data || modelRes.value || {}
      models.value = Object.entries(data).flatMap(([provider, modelList]: [string, any]) =>
        Array.isArray(modelList) ? modelList.map((m: any) => ({ ...m, provider })) : []
      )
    }
    
    // mock 端点已移除，不再拉取 gateway-stats 和 usage-stats
    gatewayStats.value = null
    usageStats.value = null
  } catch {
    statusItems.value.forEach(item => item.status = 'offline')
    models.value = []
  } finally {
    loading.value = false
  }
}

function refreshStatus() {
  loadStatus()
  ElMessage.success('已刷新')
}

function openConfig() {
  ElMessage.info('请在电脑端进行高级配置')
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
.app-ai-base {
  padding-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.status-overview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.status-card {
  background: white;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon.online {
  background: #f0f9eb;
  color: #67C23A;
}

.status-icon.offline {
  background: #fef0f0;
  color: #F56C6C;
}

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.status-name {
  font-size: 12px;
  color: #909399;
}

.status-value {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
}

.status-badge.online {
  background: #f0f9eb;
  color: #67C23A;
}

.status-badge.offline {
  background: #fef0f0;
  color: #F56C6C;
}

.section-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.section-header {
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.gateway-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

.info-row .value {
  font-weight: 500;
}

.info-row .value.success {
  color: #67C23A;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-text {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 20px;
}

.model-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.model-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #ecf5ff;
  color: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.model-name {
  font-size: 13px;
  color: #303133;
}

.model-provider {
  font-size: 11px;
  color: #909399;
}

.usage-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.usage-item {
  text-align: center;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.usage-label {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-bottom: 4px;
}

.usage-value {
  font-size: 16px;
  font-weight: 600;
  color: #667eea;
}

.config-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px;
  background: white;
  border-radius: 12px;
  color: #909399;
  font-size: 13px;
  cursor: pointer;
}

.config-tip:active {
  background: #f5f7fa;
}

.config-tip span {
  flex: 1;
}
</style>
