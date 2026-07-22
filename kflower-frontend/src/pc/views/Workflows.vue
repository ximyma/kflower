<template>
  <div class="workflows-page">
    <div class="page-header">
      <div class="header-left">
        <h2>流程审批</h2>
        <el-tag type="info">{{ allWorkflows.length }} 个流程</el-tag>
      </div>
      <div class="header-right">
        <el-input v-model="searchText" placeholder="搜索流程..." clearable style="width:200px" @input="handleSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建流程
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="workflow-tabs">
      <!-- 流程定义 -->
      <el-tab-pane label="流程定义" name="definitions">
        <div v-if="filteredWorkflows.length === 0" class="empty-container">
          <el-empty description="暂无流程定义">
            <el-button type="primary" @click="openCreateDialog">创建流程</el-button>
          </el-empty>
        </div>
        <div v-else class="workflow-grid">
          <el-card v-for="wf in filteredWorkflows" :key="wf.id" class="workflow-card" shadow="hover">
            <template #header>
              <div class="workflow-header">
                <div class="wf-icon" :style="{ background: getWorkflowColor(wf.name) }">
                  <el-icon :size="24"><Operation /></el-icon>
                </div>
                <div class="wf-info">
                  <h3>{{ wf.name }}</h3>
                  <span class="wf-code">{{ wf.code || '未编码' }}</span>
                </div>
                <el-tag :type="wf.is_active ? 'success' : 'info'" size="small">
                  {{ wf.is_active ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </template>
            <p class="wf-desc">{{ wf.description || '暂无描述' }}</p>
            <div class="wf-meta">
              <span><el-icon><List /></el-icon> {{ wf.node_count || 0 }} 个节点</span>
              <span><el-icon><Timer /></el-icon> {{ formatDate(wf.created_at) }}</span>
            </div>
            <div class="wf-actions">
              <el-button type="primary" size="small" link @click="handleExecute(wf)">发起</el-button>
              <el-button type="success" size="small" link @click="handleDesign(wf)">设计</el-button>
              <el-button size="small" link @click="handleEdit(wf)">编辑</el-button>
              <el-button type="danger" size="small" link @click="handleDelete(wf)">删除</el-button>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
      
      <!-- 待我审批 -->
      <el-tab-pane name="pending">
        <template #label>
          <span>待我审批 <el-badge :value="pendingList.length" :hidden="pendingList.length === 0" /></span>
        </template>
        <div v-if="pendingList.length === 0" class="empty-container">
          <el-empty description="暂无待审批项">
            <template #image><el-icon :size="64" color="#67C23A"><CircleCheck /></el-icon></template>
          </el-empty>
        </div>
        <el-table v-else :data="pendingList" style="width: 100%" v-loading="loadingPending">
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="workflow_name" label="流程" width="150" />
          <el-table-column prop="applicant" label="申请人" width="100" />
          <el-table-column prop="created_at" label="申请时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleApprove(row)">批准</el-button>
              <el-button type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
              <el-button type="info" size="small" link @click="handleViewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 我发起的 -->
      <el-tab-pane label="我发起的" name="my">
        <div v-if="myList.length === 0" class="empty-container">
          <el-empty description="暂无发起记录" />
        </div>
        <el-table v-else :data="myList" style="width: 100%" v-loading="loadingMy">
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="workflow_name" label="流程" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="发起时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" link @click="handleViewDetail(row)">详情</el-button>
              <el-button 
                v-if="row.status === 'pending'" 
                type="warning" 
                size="small" 
                link 
                @click="handleWithdraw(row)"
              >
                撤回
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <!-- 执行记录 -->
      <el-tab-pane label="执行记录" name="history">
        <div v-if="historyList.length === 0" class="empty-container">
          <el-empty description="暂无执行记录" />
        </div>
        <el-table v-else :data="historyList" style="width: 100%" v-loading="loadingHistory">
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="workflow_name" label="流程" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="180">
            <template #default="{ row }">
              {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" link @click="handleViewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建流程对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建新流程" width="600px">
      <el-form :model="newWorkflowForm" label-width="100px" :rules="wfRules" ref="wfFormRef">
        <el-form-item label="流程名称" prop="name">
          <el-input v-model="newWorkflowForm.name" placeholder="请输入流程名称" />
        </el-form-item>
        <el-form-item label="流程编码" prop="code">
          <el-input v-model="newWorkflowForm.code" placeholder="请输入流程编码" />
        </el-form-item>
        <el-form-item label="流程描述">
          <el-input v-model="newWorkflowForm.description" type="textarea" :rows="3" placeholder="请输入流程描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit" :loading="creating">创建并设计</el-button>
      </template>
    </el-dialog>

    <!-- 流程详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="流程详情" width="700px">
      <el-descriptions :column="2" border v-if="currentWorkflow">
        <el-descriptions-item label="流程名称">{{ currentWorkflow.name }}</el-descriptions-item>
        <el-descriptions-item label="流程编码">{{ currentWorkflow.code }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentWorkflow.is_active ? 'success' : 'info'">
            {{ currentWorkflow.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentWorkflow.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentWorkflow.description || '暂无' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDesign(currentWorkflow)">编辑流程</el-button>
      </template>
    </el-dialog>
    <!-- 实例时间线对话框 -->
    <el-dialog v-model="timelineDialogVisible" :title="`审批详情 - ${timelineData.title || ''}`" width="700px" @close="timelineData = {}">
      <div v-if="!timelineData.id" class="empty-container">
        <el-empty description="加载中..." />
      </div>
      <div v-else>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="流程">{{ timelineData.workflow_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(timelineData.status)">{{ getStatusText(timelineData.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发起时间">{{ formatDate(timelineData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatDate(timelineData.completed_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <h4>审批时间线</h4>
        <el-timeline v-if="timelineData.logs && timelineData.logs.length">
          <el-timeline-item
            v-for="log in timelineData.logs"
            :key="log.id"
            :timestamp="formatDate(log.created_at)"
            :type="log.action === 'approved' || log.action === 'approve' ? 'success' : log.action === 'rejected' ? 'danger' : 'primary'"
          >
            <strong>{{ log.operator_name || '系统' }}</strong>
            <span v-if="log.action === 'created'"> 发起审批</span>
            <span v-else-if="log.action === 'approved' || log.action === 'approve'"> 审批通过</span>
            <span v-else-if="log.action === 'rejected'"> 审批拒绝</span>
            <span v-else-if="log.action === 'withdraw'"> 撤回审批</span>
            <span v-else> {{ log.action }}</span>
            <div v-if="log.comment" style="color:#909399;font-size:12px;margin-top:4px">"{{ log.comment }}"</div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无审批记录" :image-size="60" />
      </div>
      <template #footer>
        <el-button @click="timelineDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Timer, CircleCheck, Operation } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { workflowAPI } from '../../common/api'

const router = useRouter()

const activeTab = ref('definitions')
const searchText = ref('')

// 流程定义
const allWorkflows = ref<any[]>([])
const filteredWorkflows = computed(() => {
  if (!searchText.value) return allWorkflows.value
  const q = searchText.value.toLowerCase()
  return allWorkflows.value.filter(w => 
    (w.name || '').toLowerCase().includes(q) || 
    (w.code || '').toLowerCase().includes(q)
  )
})

// 待我审批
const pendingList = ref<any[]>([])
const loadingPending = ref(false)

// 我发起的
const myList = ref<any[]>([])
const loadingMy = ref(false)

// 执行记录
const historyList = ref<any[]>([])
const loadingHistory = ref(false)

// 对话框
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const timelineDialogVisible = ref(false)
const creating = ref(false)

// 表单
const wfFormRef = ref<FormInstance>()
const newWorkflowForm = ref({
  name: '',
  code: '',
  description: ''
})
const currentWorkflow = ref<any>({})
const timelineInstance = ref<any>(null)
const timelineData = ref<any>({})

const wfRules: FormRules = {
  name: [{ required: true, message: '请输入流程名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入流程编码', trigger: 'blur' }]
}

// 颜色映射
const colorMap: Record<string, string> = {}
const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9C27B0', '#00BCD4', '#FF5722']

function getWorkflowColor(name: string) {
  if (!colorMap[name]) {
    colorMap[name] = colors[Object.keys(colorMap).length % colors.length]
  }
  return colorMap[name]
}

function getStatusType(status?: string) {
  const map: Record<string, string> = {
    running: 'warning',
    approved: 'success',
    rejected: 'danger',
    cancelled: 'info',
    draft: 'info',
    pending: 'warning',
    completed: 'success',
    active: 'success',
    disabled: 'info'
  }
  return map[status || ''] || 'info'
}

function getStatusText(status?: string) {
  const map: Record<string, string> = {
    running: '进行中',
    approved: '已批准',
    rejected: '已拒绝',
    cancelled: '已撤回',
    draft: '草稿',
    pending: '待审批',
    completed: '已完成',
    active: '启用',
    disabled: '禁用'
  }
  return map[status || ''] || status || '-'
}

function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function handleSearch() {}

// ========== 加载数据 ==========

async function loadWorkflows() {
  try {
    const res: any = await workflowAPI.list({ limit: 100 })
    if (res && res.success !== false) {
      const list = Array.isArray(res) ? res : (res.data || [])
      allWorkflows.value = list.map((w: any) => ({
        ...w,
        node_count: Array.isArray(w.nodes) ? w.nodes.length : (w.node_count || 0)
      }))
    }
  } catch (e) {
    console.warn('Failed to load workflows')
  }
}

async function loadPendingTasks() {
  loadingPending.value = true
  try {
    // 使用 workflowAPI 获取真实待办数据
    const res: any = await workflowAPI.getPendingInstances()
    if (res && res.success !== false) {
      const items = Array.isArray(res) ? res : (res.data || res.items || [])
      pendingList.value = items
    } else {
      pendingList.value = []
    }
  } catch (e) {
    console.warn('Failed to load pending tasks')
    pendingList.value = []
  } finally {
    loadingPending.value = false
  }
}

async function loadMyList() {
  loadingMy.value = true
  try {
    const res: any = await workflowAPI.getMyInstances()
    if (res && res.success !== false) {
      myList.value = Array.isArray(res) ? res : (res.data || [])
    }
  } catch (e) {
    myList.value = []
  } finally {
    loadingMy.value = false
  }
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const res: any = await workflowAPI.getAllInstances()
    if (res && res.success !== false) {
      historyList.value = Array.isArray(res) ? res : (res.data || [])
    }
  } catch (e) {
    historyList.value = []
  } finally {
    loadingHistory.value = false
  }
}

// ========== 操作 ==========

function openCreateDialog() {
  newWorkflowForm.value = { name: '', code: '', description: '' }
  createDialogVisible.value = true
}

async function handleCreateSubmit() {
  if (!wfFormRef.value) return
  await wfFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    creating.value = true
    try {
      const res: any = await workflowAPI.create(newWorkflowForm.value)
      if (res && res.success !== false) {
        ElMessage.success('流程创建成功，正在跳转到设计器...')
        createDialogVisible.value = false
        const wf = res.data || res
        const wfId = wf.id
        if (wfId) {
          router.push(`/workflows/design/${wfId}`)
        } else {
          loadWorkflows()
        }
      } else {
        ElMessage.error(res?.message || '创建失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '创建失败')
    } finally {
      creating.value = false
    }
  })
}

function handleEdit(wf: any) {
  currentWorkflow.value = wf
  detailDialogVisible.value = true
}

async function handleViewDetail(row: any) {
  const instanceId = row.instance_id || row.id
  if (!instanceId) { ElMessage.warning('无法获取实例ID'); return }
  timelineDialogVisible.value = true
  try {
    const res: any = await workflowAPI.getInstanceDetail(instanceId)
    timelineData.value = res.data || res || {}
    timelineInstance.value = row
  } catch (e: any) {
    ElMessage.error('获取实例详情失败: ' + (e.message || '未知错误'))
    timelineDialogVisible.value = false
  }
}

function handleDesign(wf: any) {
  router.push(`/workflows/design/${wf.id}`)
}

function handleExecute(wf: any) {
  // 发起审批 - 创建实例
  ElMessageBox.prompt('请输入审批标题', '发起审批', {
    confirmButtonText: '发起',
    inputPlaceholder: '例如：请假申请-张三'
  }).then(async ({ value }) => {
    if (!value) return
    try {
      // 使用新引擎启动实例
      const startData = {
        title: value,
        variables: {},
        form_data_id: null
      }
      await workflowAPI.executeStart(wf.id, startData)
      ElMessage.success('审批流程已发起')
      // 刷新列表
      loadMyList()
      loadHistory()
    } catch (e: any) {
      // 如果 executeStart 不可用，尝试 execute
      try {
        await workflowAPI.execute(wf.id, value, {})
        ElMessage.success('审批流程已发起')
        loadMyList()
        loadHistory()
      } catch (e2: any) {
        ElMessage.error(e2.message || '发起失败')
      }
    }
  }).catch(() => {})
}

async function handleDelete(wf: any) {
  try {
    await ElMessageBox.confirm(`确定要删除流程 "${wf.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    const res: any = await workflowAPI.delete(wf.id)
    if (res && res.success !== false) {
      ElMessage.success('删除成功')
      loadWorkflows()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

// ========== 审批操作（调用真实API） ==========

async function handleApprove(row: any) {
  try {
    await ElMessageBox.confirm(`确定批准 "${row.title || row.node_name}" 吗？`, '确认批准', { type: 'success' })
    const taskId = row.id
    await workflowAPI.submitTaskAction(taskId, { action: 'approve', opinion: '同意' })
    ElMessage.success('已批准')
    await Promise.all([loadPendingTasks(), loadMyList(), loadHistory()])
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('审批失败: ' + (e?.response?.data?.detail || e.message || ''))
  }
}

async function handleReject(row: any) {
  try {
    await ElMessageBox.confirm(`确定拒绝 "${row.title || row.node_name}" 吗？`, '确认拒绝', { type: 'warning' })
    await workflowAPI.submitTaskAction(row.id, { action: 'reject', opinion: '不同意' })
    ElMessage.warning('已拒绝')
    await Promise.all([loadPendingTasks(), loadMyList(), loadHistory()])
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('操作失败: ' + (e?.response?.data?.detail || e.message || ''))
  }
}

async function handleWithdraw(row: any) {
  try {
    await ElMessageBox.confirm(`确定撤回 "${row.title}" 吗？`, '确认撤回', { type: 'warning' })
    const instanceId = row.instance_id || row.id
    await workflowAPI.withdrawInstance(instanceId)
    ElMessage.info('已撤回')
    await Promise.all([loadMyList(), loadPendingTasks(), loadHistory()])
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('撤回失败: ' + (e?.response?.data?.detail || e.message || ''))
  }
}

onMounted(() => {
  loadWorkflows()
  loadPendingTasks()
  loadMyList()
  loadHistory()
})
</script>

<style scoped>
.workflows-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workflow-tabs {
  background: var(--el-bg-color);
}

.empty-container {
  padding: 40px 0;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.workflow-card {
  margin-bottom: 0;
}

.workflow-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.wf-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.wf-info {
  flex: 1;
}

.wf-info h3 {
  margin: 0 0 4px;
  font-size: 16px;
}

.wf-code {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.wf-desc {
  color: var(--el-text-color-regular);
  font-size: 13px;
  margin: 12px 0;
  min-height: 40px;
}

.wf-meta {
  display: flex;
  gap: 16px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-bottom: 12px;
}

.wf-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.wf-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}
</style>
