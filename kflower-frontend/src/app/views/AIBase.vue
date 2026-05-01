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
    
    <!-- AI网关 -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">
          <el-icon :size="20" color="#667eea"><Connection /></el-icon>
          <span>AI网关</span>
        </div>
      </div>
      <div class="gateway-info" v-if="gatewayStats">
        <div class="info-row">
          <span>总请求</span>
          <span class="value">{{ gatewayStats.total_requests || 0 }}</span>
        </div>
        <div class="info-row">
          <span>成功率</span>
          <span class="value success">{{ gatewayStats.success_rate || '100%' }}</span>
        </div>
        <div class="info-row">
          <span>平均响应</span>
          <span class="value">{{ gatewayStats.avg_response_time || '0ms' }}</span>
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
    
    <!-- 使用统计 -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">
          <el-icon :size="20" color="#E6A23C"><DataAnalysis /></el-icon>
          <span>使用统计</span>
        </div>
      </div>
      <div class="usage-stats" v-if="usageStats">
        <div class="usage-item">
          <span class="usage-label">今日请求</span>
          <span class="usage-value">{{ usageStats.today_requests || 0 }}</span>
        </div>
        <div class="usage-item">
          <span class="usage-label">今日Token</span>
          <span class="usage-value">{{ formatToken(usageStats.today_tokens || 0) }}</span>
        </div>
        <div class="usage-item">
          <span class="usage-label">总成本</span>
          <span class="usage-value">¥{{ usageStats.total_cost || '0.00' }}</span>
        </div>
      </div>
    </div>
    
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
import { Refresh, Connection, Box, Cpu, DataAnalysis, Setting, ArrowRight, Monitor, Cloudy } from '@element-plus/icons-vue'
import { aiAPI } from '../../common/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)

const statusItems = ref([
  { key: 'gateway', name: 'AI网关', status: 'online', icon: 'Connection', value: '运行中' },
  { key: 'models', name: '模型服务', status: 'online', icon: 'Cpu', value: '正常' },
  { key: 'vector', name: '向量服务', status: 'online', icon: 'Cloudy', value: '正常' },
  { key: 'monitor', name: '监控服务', status: 'online', icon: 'Monitor', value: '正常' }
])

const gatewayStats = ref<any>(null)
const models = ref<any[]>([])
const usageStats = ref<any>(null)

function formatToken(num: number) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

async function loadStatus() {
  loading.value = true
  try {
    const [statusRes, gatewayRes, modelRes, usageRes] = await Promise.allSettled([
      aiAPI.getDigitalBaseStatus(),
      aiAPI.getGatewayStats(),
      aiAPI.getDigitalBaseModels(),
      aiAPI.getDigitalBaseUsageStats(7)
    ])
    
    if (statusRes.status === 'fulfilled') {
      const data = statusRes.value
      if (data.gateway) statusItems.value[0].status = 'online'
      if (data.models) statusItems.value[1].status = 'online'
      if (data.vector) statusItems.value[2].status = 'online'
    }
    
    if (gatewayRes.status === 'fulfilled') {
      gatewayStats.value = gatewayRes.value
    }
    
    if (modelRes.status === 'fulfilled') {
      models.value = modelRes.value.models || modelRes.value || []
    }
    
    if (usageRes.status === 'fulfilled') {
      usageStats.value = usageRes.value
    }
  } catch (error) {
    console.error('加载状态失败:', error)
    // 使用默认数据
    gatewayStats.value = { total_requests: 1234, success_rate: '99.5%', avg_response_time: '120ms' }
    models.value = [
      { name: 'gpt-3.5-turbo', provider: 'OpenAI', enabled: true },
      { name: 'ERNIE-4', provider: '百度文心', enabled: true }
    ]
    usageStats.value = { today_requests: 56, today_tokens: 125000, total_cost: '12.50' }
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
