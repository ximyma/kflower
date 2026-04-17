<template>
  <div class="home-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-text">
        <h2>{{ greeting }}，{{ userName }}</h2>
        <p>欢迎使用 Kflower 企业智能管理平台</p>
      </div>
      <div class="quick-actions">
        <el-button type="primary" @click="$router.push('/templates')">
          <el-icon><Plus /></el-icon> 新建模板
        </el-button>
        <el-button @click="$router.push('/workflows')">
          <el-icon><Grid /></el-icon> 新建流程
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="stat in stats" :key="stat.title">
        <el-card shadow="hover" class="stat-card" @click="handleStatClick(stat.route)">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-title">{{ stat.title }}</p>
              <p class="stat-value">{{ stat.value }}</p>
              <p class="stat-sub" v-if="stat.sub">{{ stat.sub }}</p>
            </div>
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="28"><component :is="stat.icon" /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主要内容区 -->
    <el-row :gutter="16" class="main-content">
      <!-- 左侧 - AI助手和快捷操作 -->
      <el-col :xs="24" :lg="14">
        <!-- AI智能助手 -->
        <el-card class="ai-card">
          <template #header>
            <div class="card-header">
              <span><el-icon class="header-icon"><MagicStick /></el-icon> AI 智能助手</span>
              <el-tag type="success" size="small">在线</el-tag>
            </div>
          </template>
          <div class="ai-input-area">
            <el-input
              v-model="aiPrompt"
              type="textarea"
              :rows="3"
              placeholder="输入您的需求，AI将帮助您完成工作，例如：
• 设计一个客户管理流程
• 创建采购审批模板
• 生成数据统计报表"
            />
            <div class="ai-actions">
              <el-button type="primary" @click="handleAIPrompt" :loading="aiLoading">
                <el-icon><Promotion /></el-icon>
                发送
              </el-button>
              <el-button @click="aiPrompt = ''">清空</el-button>
            </div>
          </div>
          <div class="ai-suggestions">
            <span class="suggestions-label">快捷指令：</span>
            <el-tag
              v-for="s in suggestions"
              :key="s.text"
              class="suggestion-tag"
              @click="aiPrompt = s.text"
            >
              {{ s.text }}
            </el-tag>
          </div>
        </el-card>

        <!-- 快捷入口 -->
        <el-card class="quick-entry-card">
          <template #header>
            <span><el-icon class="header-icon"><Menu /></el-icon> 快捷入口</span>
          </template>
          <el-row :gutter="12">
            <el-col :span="6" v-for="entry in quickEntries" :key="entry.title">
              <div class="quick-entry-item" @click="$router.push(entry.path)">
                <div class="entry-icon" :style="{ background: entry.color }">
                  <el-icon :size="24"><component :is="entry.icon" /></el-icon>
                </div>
                <span class="entry-title">{{ entry.title }}</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 右侧 - 待办和动态 -->
      <el-col :xs="24" :lg="10">
        <!-- 待办事项 -->
        <el-card class="todo-card">
          <template #header>
            <div class="card-header">
              <span><el-icon class="header-icon"><Bell /></el-icon> 待办事项</span>
              <el-badge :value="pendingTasks.length" :hidden="pendingTasks.length === 0">
                <el-button link @click="$router.push('/workflows?tab=pending')">查看全部</el-button>
              </el-badge>
            </div>
          </template>
          <div v-if="pendingTasks.length === 0" class="empty-todo">
            <el-icon :size="48" color="#dcdfe6"><CircleCheck /></el-icon>
            <p>暂无待办事项</p>
          </div>
          <el-timeline v-else>
            <el-timeline-item
              v-for="todo in pendingTasks.slice(0, 5)"
              :key="todo.id"
              :timestamp="formatTime(todo.created_at)"
              :type="todo.type === 'approval' ? 'warning' : 'primary'"
              placement="top"
            >
              <el-card shadow="hover" class="todo-item">
                <h4>{{ todo.title }}</h4>
                <p class="todo-info">
                  <el-tag size="small">{{ todo.workflow_name }}</el-tag>
                  <span class="applicant">申请人：{{ todo.applicant }}</span>
                </p>
                <div class="todo-actions">
                  <el-button type="success" size="small" @click="handleApprove(todo)">批准</el-button>
                  <el-button type="danger" size="small" @click="handleReject(todo)">拒绝</el-button>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <!-- 最新动态 -->
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <span><el-icon class="header-icon"><Clock /></el-icon> 最新动态</span>
              <el-button link @click="loadActivities">刷新</el-button>
            </div>
          </template>
          <div v-loading="loadingActivities">
            <div v-if="recentActivities.length === 0" class="empty-activity">
              <p>暂无动态</p>
            </div>
            <el-timeline v-else>
              <el-timeline-item
                v-for="act in recentActivities.slice(0, 8)"
                :key="act.id"
                :timestamp="formatTime(act.created_at)"
                :type="getActivityType(act.action)"
                placement="top"
              >
                <span>{{ act.action }}</span>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Plus, Grid, MagicStick, Promotion, Menu, Bell, Clock, CircleCheck,
  Document, Folder, ChatDotRound, DataLine, Setting, User, FolderOpened
} from '@element-plus/icons-vue'
import { dashboardAPI } from '../../common/api'
import { useAIStore } from '../../common/store/ai'

const aiStore = useAIStore()
const aiPrompt = ref('')
const aiLoading = ref(false)
const loadingActivities = ref(false)

const userName = computed(() => {
  const user = JSON.parse(localStorage.getItem('kflower_user') || '{}')
  return user.full_name || user.username || '用户'
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const stats = ref([
  { title: '表单模板', value: 0, sub: '个模板', icon: 'Document', color: '#409EFF', route: '/templates' },
  { title: '工作流', value: 0, sub: '个流程', icon: 'Grid', color: '#67C23A', route: '/workflows' },
  { title: '知识文档', value: 0, sub: '份文档', icon: 'FolderOpened', color: '#E6A23C', route: '/knowledge' },
  { title: 'AI对话', value: 0, sub: '次对话', icon: 'ChatDotRound', color: '#F56C6C', route: '/ai' }
])

const pendingTasks = ref<any[]>([])

const recentActivities = ref<any[]>([])

const suggestions = [
  { text: '设计一个客户管理流程' },
  { text: '创建采购审批模板' },
  { text: '上传产品知识文档' },
  { text: '生成月度数据报表' }
]

const quickEntries = [
  { title: '模板设计', icon: 'Document', path: '/templates', color: '#409EFF' },
  { title: '流程审批', icon: 'Grid', path: '/workflows', color: '#67C23A' },
  { title: '知识库', icon: 'FolderOpened', path: '/knowledge', color: '#E6A23C' },
  { title: '决策分析', icon: 'DataLine', path: '/analytics', color: '#909399' },
  { title: '系统配置', icon: 'Setting', path: '/settings', color: '#F56C6C' },
  { title: '用户管理', icon: 'User', path: '/users', color: '#9C27B0' }
]

function formatTime(timeStr: string) {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

function getActivityType(action: string) {
  if (action.includes('登录')) return 'primary'
  if (action.includes('创建')) return 'success'
  if (action.includes('审批') || action.includes('通过')) return 'warning'
  if (action.includes('删除')) return 'danger'
  return 'info'
}

function handleStatClick(route: string) {
  if (route) window.location.href = route
}

async function handleAIPrompt() {
  if (!aiPrompt.value.trim()) {
    ElMessage.warning('请输入需求')
    return
  }
  aiLoading.value = true
  aiStore.sendMessage(aiPrompt.value)
  aiPrompt.value = ''
  aiLoading.value = false
  aiStore.toggleChat()
}

async function loadDashboard() {
  try {
    const res: any = await dashboardAPI.getStats()
    if (res && res.success !== false) {
      const data = res.data || {}
      stats.value[0].value = data.template_count ?? 0
      stats.value[1].value = data.workflow_count ?? 0
      stats.value[2].value = data.knowledge_doc_count ?? 0
      stats.value[3].value = data.ai_chat_count ?? 0
    }
  } catch (e) {
    console.warn('Dashboard API not available')
  }
}

async function loadPendingTasks() {
  try {
    const res: any = await dashboardAPI.getPendingTasks()
    if (res && res.success !== false) {
      pendingTasks.value = res.data?.tasks || []
    }
  } catch (e) {
    console.warn('Pending tasks API not available')
  }
}

async function loadActivities() {
  loadingActivities.value = true
  try {
    const res: any = await dashboardAPI.getRecentActivities(10)
    if (res && res.success !== false) {
      recentActivities.value = res.data?.activities || []
    }
  } catch (e) {
    console.warn('Activities API not available')
  } finally {
    loadingActivities.value = false
  }
}

function handleApprove(todo: any) {
  ElMessage.success(`已批准：${todo.title}`)
}

function handleReject(todo: any) {
  ElMessage.info(`已拒绝：${todo.title}`)
}

onMounted(() => {
  loadDashboard()
  loadPendingTasks()
  loadActivities()
})
</script>

<style scoped>
.home-page {
  padding: 0;
}

.welcome-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #409EFF 0%, #337ecc 100%);
  border-radius: 8px;
  margin-bottom: 20px;
  color: white;
}

.welcome-text h2 {
  margin: 0 0 4px;
  font-size: 22px;
}

.welcome-text p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.quick-actions {
  display: flex;
  gap: 12px;
}

.quick-actions .el-button {
  background: rgba(255,255,255,0.2);
  border-color: rgba(255,255,255,0.4);
  color: white;
}

.quick-actions .el-button:hover {
  background: rgba(255,255,255,0.3);
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-info .stat-title {
  color: #909399;
  font-size: 13px;
  margin: 0 0 8px;
}

.stat-info .stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.stat-info .stat-sub {
  color: #c0c4cc;
  font-size: 12px;
  margin: 4px 0 0;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.main-content {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .header-icon {
  margin-right: 8px;
  vertical-align: middle;
}

.ai-card {
  margin-bottom: 16px;
}

.ai-input-area {
  margin-bottom: 16px;
}

.ai-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.ai-suggestions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.suggestions-label {
  color: #909399;
  font-size: 13px;
}

.suggestion-tag {
  cursor: pointer;
}

.quick-entry-card {
  margin-bottom: 16px;
}

.quick-entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.quick-entry-item:hover {
  background: #f5f7fa;
}

.entry-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 8px;
}

.entry-title {
  font-size: 13px;
  color: #606266;
}

.todo-card {
  margin-bottom: 16px;
}

.empty-todo {
  text-align: center;
  padding: 32px 0;
  color: #909399;
}

.empty-todo p {
  margin: 12px 0 0;
}

.todo-item h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.todo-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 12px;
  color: #606266;
  font-size: 13px;
}

.todo-actions {
  display: flex;
  gap: 8px;
}

.activity-card {
  margin-bottom: 16px;
}

.empty-activity {
  text-align: center;
  padding: 32px 0;
  color: #909399;
}
</style>
