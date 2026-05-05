<template>
  <div class="app-my-apps">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <span class="header-title">我的应用</span>
        <span class="header-count">{{ apps.length }}个</span>
      </div>
      <el-button type="primary" size="small" round @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建
      </el-button>
    </div>

    <!-- 搜索 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索我的应用..."
        clearable
        size="large"
        :prefix-icon="Search"
        @input="onSearch"
      />
    </div>

    <!-- 应用列表 -->
    <div class="app-list" v-loading="loading">
      <!-- 空状态 -->
      <div v-if="filteredApps.length === 0 && !loading" class="empty-state">
        <div class="empty-icon">
          <el-icon :size="56"><Grid /></el-icon>
        </div>
        <p class="empty-title">{{ searchKeyword ? '没有找到相关应用' : '还没有应用' }}</p>
        <p class="empty-desc">{{ searchKeyword ? '试试其他关键词' : '创建一个开始使用吧' }}</p>
        <el-button v-if="!searchKeyword" type="primary" round @click="showCreateDialog = true">
          创建第一个应用
        </el-button>
      </div>

      <!-- 应用卡片 -->
      <div
        v-for="app in filteredApps"
        :key="app.id"
        class="app-card"
      >
        <!-- 卡片左侧：图标 -->
        <div class="card-icon" :style="{ background: getAppGradient(app.id) }">
          <el-icon :size="26"><component :is="app.icon || 'Grid'" /></el-icon>
        </div>

        <!-- 卡片内容 -->
        <div class="card-body">
          <div class="card-name">{{ app.name }}</div>
          <div class="card-meta">
            <span class="card-time" v-if="app.updated_at">{{ formatTime(app.updated_at) }}</span>
            <span class="card-badge" v-if="app.is_published">
              <el-icon><CircleCheckFilled /></el-icon> 已发布
            </span>
          </div>
          <div class="card-desc" v-if="app.description">{{ app.description }}</div>
        </div>

        <!-- 两个大按钮：查看 & 设计 -->
        <div class="card-actions">
          <el-button 
            type="primary" 
            size="small" 
            round 
            @click.stop="openApp(app)"
            class="action-btn view-btn"
          >
            <el-icon><View /></el-icon>查看
          </el-button>
          <el-button 
            type="info" 
            size="small" 
            round 
            @click.stop="openDesigner(app)"
            class="action-btn design-btn"
          >
            <el-icon><Edit /></el-icon>设计
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑应用对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingApp ? '编辑应用' : '创建新应用'"
      width="92%"
      :close-on-click-modal="false"
      :before-close="() => showCreateDialog = false"
    >
      <el-form :model="newApp" label-position="top" size="large">
        <el-form-item label="应用名称" required>
          <el-input
            v-model="newApp.name"
            placeholder="例如：行政管理、项目跟踪"
            maxlength="30"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="应用描述（可选）">
          <el-input
            v-model="newApp.description"
            type="textarea"
            :rows="2"
            placeholder="简要描述这个应用的用途"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false" size="large">取消</el-button>
        <el-button type="primary" @click="handleCreateApp" :loading="creating" size="large">
          {{ editingApp ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Plus, Grid, Search, View, Edit,
  CircleCheckFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import appAPI from '../../common/api/myApps'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const apps = ref<any[]>([])
const searchKeyword = ref('')
const showCreateDialog = ref(false)
const editingApp = ref<any>(null)

const newApp = ref({ name: '', description: '' })

// 渐变色方案
const gradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
  'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
  'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
]

function getAppGradient(id: number) {
  return gradients[id % gradients.length]
}

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const filteredApps = computed(() => {
  if (!searchKeyword.value.trim()) return apps.value
  const kw = searchKeyword.value.toLowerCase()
  return apps.value.filter(a =>
    a.name.toLowerCase().includes(kw) ||
    (a.description || '').toLowerCase().includes(kw)
  )
})

async function loadApps() {
  loading.value = true
  try {
    const res = await appAPI.list()
    apps.value = res.items || res || []
  } catch (error) {
    console.error('[MyApps] 加载应用失败:', error)
    apps.value = []
  } finally {
    loading.value = false
  }
}

let searchTimer: any = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    // 实时过滤，不需要额外请求
  }, 300)
}

function openApp(app: any) {
  // 进入应用首页，展示模板列表
  router.push(`/app/app-home/${app.id}`)
}

function openDesigner(app: any) {
  // 进入应用设计器
  router.push(`/app/app-designer/${app.id}`)
}

async function handleCreateApp() {
  if (!newApp.value.name.trim()) {
    ElMessage.warning('请输入应用名称')
    return
  }

  creating.value = true
  try {
    if (editingApp.value) {
      await appAPI.update(editingApp.value.id, {
        name: newApp.value.name,
        description: newApp.value.description
      })
      ElMessage.success('应用信息已保存')
    } else {
      const res = await appAPI.create({
        name: newApp.value.name,
        description: newApp.value.description
      })
      ElMessage.success('应用创建成功')
      // 创建后直接进入应用设计器
      router.push(`/app/app-designer/${res.id}`)
      loadApps()
      showCreateDialog.value = false
      newApp.value = { name: '', description: '' }
      editingApp.value = null
      return
    }
    showCreateDialog.value = false
    newApp.value = { name: '', description: '' }
    editingApp.value = null
    loadApps()
  } catch (error) {
    ElMessage.error(editingApp.value ? '保存失败' : '创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadApps()
})
</script>

<style scoped>
.app-my-apps {
  padding: 0 16px 30px;
  min-height: 100%;
  background: #f5f7fa;
}

/* 头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 12px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
}

.header-count {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 搜索栏 */
.search-bar {
  margin-bottom: 16px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 22px;
  background: white;
  box-shadow: 0 0 0 1px #e8e8e8;
  padding: 6px 16px;
}

.search-bar :deep(.el-input__inner) {
  font-size: 14px;
}

/* 应用列表 */
.app-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f0f2f5 0%, #e8e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #c0c4cc;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 20px;
}

/* 应用卡片 */
.app-card {
  background: white;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
}

/* 卡片图标 */
.card-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}

/* 卡片内容 */
.card-body {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 3px;
}

.card-time {
  font-size: 11px;
  color: #c0c4cc;
}

.card-badge {
  font-size: 11px;
  color: #67C23A;
  display: flex;
  align-items: center;
  gap: 2px;
}

.card-desc {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 操作按钮 */
.card-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  padding: 6px 12px;
  font-size: 12px;
  line-height: 1;
  min-width: 70px;
}

.view-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.design-btn {
  background: #f5f7fa;
  border: 1px solid #e8e8f0;
  color: #606266;
}

.view-btn:hover {
  opacity: 0.9;
}

.design-btn:hover {
  background: #e8e8f0;
}
</style>