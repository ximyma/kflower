<template>
  <div class="app-workspace">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>我的工作区</h2>
    </div>
    
    <!-- 统计概览 -->
    <div class="stats-grid" v-loading="loading">
      <div class="stat-card" v-for="stat in stats" :key="stat.key" @click="navigateTo(stat.path)">
        <div class="stat-icon" :style="{ background: stat.color }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </div>
    
    <!-- 最近活动 -->
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">最近活动</span>
      </div>
      <div class="activity-list" v-if="activities.length > 0">
        <div v-for="item in activities" :key="item.id" class="activity-item">
          <div class="activity-icon" :class="item.type">
            <el-icon :size="16"><component :is="getActivityIcon(item.type)" /></el-icon>
          </div>
          <div class="activity-info">
            <span class="activity-text">{{ item.text }}</span>
            <span class="activity-time">{{ item.time }}</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-text">暂无最近活动</div>
    </div>
    
    <!-- 快捷操作 -->
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">快捷操作</span>
      </div>
      <div class="quick-actions">
        <div class="quick-item" @click="$router.push('/app/templates')">
          <el-icon :size="24" color="#409EFF"><Document /></el-icon>
          <span>新建模板</span>
        </div>
        <div class="quick-item" @click="$router.push('/app/workflows')">
          <el-icon :size="24" color="#67C23A"><Connection /></el-icon>
          <span>发起流程</span>
        </div>
        <div class="quick-item" @click="$router.push('/app/knowledge')">
          <el-icon :size="24" color="#F56C6C"><Files /></el-icon>
          <span>上传文档</span>
        </div>
        <div class="quick-item" @click="$router.push('/app/chat')">
          <el-icon :size="24" color="#667eea"><ChatDotRound /></el-icon>
          <span>AI对话</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, Connection, Files, ChatDotRound, DataAnalysis, User, Clock, Edit, Check } from '@element-plus/icons-vue'
import { dashboardAPI } from '../../common/api'

const router = useRouter()
const loading = ref(false)

const stats = ref([
  { key: 'templates', label: '我的模板', value: 0, icon: 'Document', color: '#409EFF', path: '/app/templates' },
  { key: 'workflows', label: '我的流程', value: 0, icon: 'Connection', color: '#67C23A', path: '/app/workflows' },
  { key: 'knowledge', label: '知识库', value: 0, icon: 'Files', color: '#F56C6C', path: '/app/knowledge' },
  { key: 'agents', label: '智能体', value: 0, icon: 'Cpu', color: '#E6A23C', path: '/app/agents' }
])

const activities = ref<any[]>([])

function getActivityIcon(type: string) {
  const icons: Record<string, string> = {
    create: 'Edit',
    approve: 'Check',
    update: 'Document',
    default: 'Clock'
  }
  return icons[type] || icons.default
}

async function loadWorkspace() {
  loading.value = true
  try {
    const res = await dashboardAPI.getStats()
    stats.value[0].value = res.templates || 0
    stats.value[1].value = res.workflows || 0
    stats.value[2].value = res.knowledge || 0
    stats.value[3].value = res.agents || 0
  } catch (error) {
    console.error('加载工作区失败:', error)
    // 使用默认数据
    stats.value[0].value = 5
    stats.value[1].value = 12
    stats.value[2].value = 3
    stats.value[3].value = 2
  }
  
  try {
    const actRes = await dashboardAPI.getRecentActivities(5)
    activities.value = actRes.activities || actRes || []
  } catch (error) {
    activities.value = [
      { id: 1, type: 'create', text: '创建了"请假申请"模板', time: '10分钟前' },
      { id: 2, type: 'approve', text: '审批通过了"采购申请"', time: '30分钟前' },
      { id: 3, type: 'update', text: '更新了知识库"产品手册"', time: '1小时前' }
    ]
  } finally {
    loading.value = false
  }
}

function navigateTo(path: string) {
  router.push(path)
}

onMounted(() => {
  loadWorkspace()
})
</script>

<style scoped>
.app-workspace {
  padding-bottom: 20px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:active {
  transform: scale(0.97);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 12px;
  color: #909399;
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
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-icon.create {
  background: #ecf5ff;
  color: #409EFF;
}

.activity-icon.approve {
  background: #f0f9eb;
  color: #67C23A;
}

.activity-icon.update {
  background: #fdf6ec;
  color: #E6A23C;
}

.activity-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.activity-text {
  font-size: 13px;
  color: #303133;
}

.activity-time {
  font-size: 11px;
  color: #c0c4cc;
}

.empty-text {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 20px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  background: #f5f7fa;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.quick-item:active {
  background: #ebeef5;
}

.quick-item span {
  font-size: 11px;
  color: #606266;
}
</style>
