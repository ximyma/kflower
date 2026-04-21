<template>
  <div class="app-workflows">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>流程审批</h2>
      <el-button type="primary" size="small" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建流程
      </el-button>
    </div>
    
    <!-- Tab切换 -->
    <div class="tab-bar">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        {{ tab.label }}
        <span v-if="tab.count" class="tab-badge">{{ tab.count }}</span>
      </div>
    </div>
    
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索流程..."
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    
    <!-- 流程列表 -->
    <div class="workflow-list" v-loading="loading">
      <div v-if="filteredWorkflows.length === 0 && !loading" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Connection /></el-icon>
        <p>{{ currentTab === 'pending' ? '暂无待审批流程' : currentTab === 'my' ? '暂无我的流程' : '暂无流程' }}</p>
      </div>
      
      <div
        v-for="workflow in filteredWorkflows"
        :key="workflow.id"
        class="workflow-item"
        @click="viewWorkflow(workflow)"
      >
        <div class="workflow-status" :class="workflow.status || 'pending'">
          <el-icon :size="20"><component :is="getStatusIcon(workflow.status)" /></el-icon>
        </div>
        <div class="workflow-info">
          <h3>{{ workflow.title || workflow.name || '未命名流程' }}</h3>
          <p class="workflow-type">{{ workflow.workflow_type || '审批流程' }}</p>
          <div class="workflow-meta">
            <span class="workflow-time">{{ formatTime(workflow.created_at) }}</span>
            <el-tag v-if="workflow.status" size="small" :type="getStatusType(workflow.status)">
              {{ getStatusText(workflow.status) }}
            </el-tag>
          </div>
        </div>
        <el-icon :size="18" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
    </div>
    
    <!-- 新建流程对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建流程" width="90%" :close-on-click-modal="false">
      <el-form :model="newWorkflow" label-position="top">
        <el-form-item label="流程名称" required>
          <el-input v-model="newWorkflow.name" placeholder="请输入流程名称" />
        </el-form-item>
        <el-form-item label="流程类型">
          <el-select v-model="newWorkflow.type" placeholder="选择类型" style="width: 100%">
            <el-option label="审批流程" value="approval" />
            <el-option label="填写流程" value="form" />
            <el-option label="知会流程" value="notify" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newWorkflow.description" type="textarea" :rows="2" placeholder="流程描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createWorkflow" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Connection, ArrowRight, MoreFilled, Check, Clock, Close, Edit } from '@element-plus/icons-vue'
import { workflowAPI } from '../../common/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const workflows = ref<any[]>([])
const searchText = ref('')
const currentTab = ref('pending')
const showCreateDialog = ref(false)

const newWorkflow = ref({
  name: '',
  type: 'approval',
  description: ''
})

const tabs = [
  { key: 'pending', label: '待审批', count: 0 },
  { key: 'my', label: '我的发起', count: 0 },
  { key: 'all', label: '全部流程', count: 0 }
]

const filteredWorkflows = computed(() => {
  let list = workflows.value
  
  if (currentTab.value === 'pending') {
    list = list.filter(w => w.status === 'pending')
  } else if (currentTab.value === 'my') {
    list = list.filter(w => w.is_initiator)
  }
  
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    list = list.filter(w => 
      (w.title || w.name || '').toLowerCase().includes(keyword)
    )
  }
  
  return list
})

function getStatusIcon(status: string) {
  const icons: Record<string, string> = {
    pending: 'Clock',
    approved: 'Check',
    rejected: 'Close',
    processing: 'Edit'
  }
  return icons[status] || icons.pending
}

function getStatusType(status: string) {
  const types: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    processing: 'primary'
  }
  return types[status] || types.pending
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    pending: '待审批',
    approved: '已通过',
    rejected: '已拒绝',
    processing: '进行中'
  }
  return texts[status] || texts.pending
}

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString()
}

async function loadWorkflows() {
  loading.value = true
  try {
    const res = await workflowAPI.list({ limit: 100 })
    workflows.value = res.items || res || []
    
    // 更新tab计数
    tabs[0].count = workflows.value.filter(w => w.status === 'pending').length
    tabs[1].count = workflows.value.filter(w => w.is_initiator).length
    tabs[2].count = workflows.value.length
  } catch (error) {
    console.error('加载流程失败:', error)
  } finally {
    loading.value = false
  }
}

function viewWorkflow(workflow: any) {
  // 跳转到移动端流程设计器
  router.push(`/app/workflow-designer/${workflow.id}`)
}

async function createWorkflow() {
  if (!newWorkflow.value.name.trim()) {
    ElMessage.warning('请输入流程名称')
    return
  }

  creating.value = true
  try {
    const res = await workflowAPI.create({
      name: newWorkflow.value.name,
      type: newWorkflow.value.type,
      description: newWorkflow.value.description
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newWorkflow.value = { name: '', type: 'approval', description: '' }
    // 跳转到流程设计器
    router.push(`/app/workflow-designer/${res.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.app-workflows {
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

.tab-bar {
  display: flex;
  background: white;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 12px;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 10px;
  font-size: 13px;
  color: #606266;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item.active {
  background: #667eea;
  color: white;
}

.tab-badge {
  display: inline-block;
  margin-left: 4px;
  padding: 0 6px;
  font-size: 10px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
}

.tab-item:not(.active) .tab-badge {
  background: #f0f0f0;
}

.search-bar {
  margin-bottom: 12px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 20px;
}

.workflow-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state p {
  margin-top: 16px;
}

.workflow-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.workflow-item:active {
  transform: scale(0.98);
}

.workflow-status {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.workflow-status.pending {
  background: #fdf6ec;
  color: #E6A23C;
}

.workflow-status.approved {
  background: #f0f9eb;
  color: #67C23A;
}

.workflow-status.rejected {
  background: #fef0f0;
  color: #F56C6C;
}

.workflow-status.processing {
  background: #ecf5ff;
  color: #409EFF;
}

.workflow-info {
  flex: 1;
  min-width: 0;
}

.workflow-info h3 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-type {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.workflow-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-time {
  font-size: 11px;
  color: #c0c4cc;
}
</style>
