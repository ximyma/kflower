<template>
  <div class="page-container">

    <!-- ===== 顶部操作栏 ===== -->
    <div class="page-header">
      <h3>流程审批</h3>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建流程
        </el-button>
      </div>
    </div>

    <!-- ===== 三个 Tab ===== -->
    <el-tabs v-model="activeTab" @tab-change="onTabChange">

      <!-- ===== Tab1: 我的流程 ===== -->
      <el-tab-pane label="我的流程" name="my">
        <div class="search-bar">
          <el-input v-model="mySearch" placeholder="搜索我的流程..." clearable style="width:280px" @input="debounceLoadMy">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
        <div v-if="myLoading" class="loading-area"><el-skeleton :rows="3" animated /></div>
        <el-empty v-else-if="myWorkflows.length === 0" description="暂无我的流程，点击新建开始">
          <el-button type="primary" @click="openCreateDialog">新建流程</el-button>
        </el-empty>
        <el-row :gutter="16" v-else>
          <el-col :xs="24" :sm="12" :md="8" v-for="w in myWorkflows" :key="w.id">
            <el-card shadow="hover" class="wf-card">
              <div class="wf-card-header">
                <div class="wf-icon" :class="getFlowTypeClass(w.flow_type)">
                  <el-icon :size="18"><Finished /></el-icon>
                </div>
                <div class="wf-info">
                  <h4>{{ w.name }}</h4>
                  <span class="wf-code">{{ w.code || '' }}</span>
                </div>
                <el-tag size="small" :type="w.is_active ? 'success' : 'info'">
                  {{ w.is_active ? '运行中' : '停用' }}
                </el-tag>
              </div>
              <p class="wf-desc">{{ w.description || '暂无描述' }}</p>
              <div class="wf-meta">
                <span><el-icon><Clock /></el-icon> {{ formatDate(w.created_at) }}</span>
              </div>
              <div class="wf-actions">
                <el-button size="small" type="primary" plain @click="goDesigner(w)">
                  <el-icon><SetUp /></el-icon> 设计
                </el-button>
                <el-button size="small" plain @click="openExecuteDialog(w)">
                  <el-icon><VideoPlay /></el-icon> 执行
                </el-button>
                <el-button size="small" plain @click="openEditDialog(w)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" type="danger" plain @click="deleteWorkflow(w)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ===== Tab2: 待我审批 ===== -->
      <el-tab-pane label="待我审批" name="pending">
        <div v-if="pendingLoading" class="loading-area"><el-skeleton :rows="4" animated /></div>
        <el-empty v-else-if="pendingTasks.length === 0" description="暂无待审批任务" />
        <el-table v-else :data="pendingTasks" stripe>
          <el-table-column prop="title" label="申请标题" min-width="160" />
          <el-table-column prop="workflow_name" label="所属流程" width="140" />
          <el-table-column prop="applicant" label="申请人" width="100" />
          <el-table-column prop="created_at" label="申请时间" width="160">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="approveTask(row)">
                <el-icon><Check /></el-icon> 通过
              </el-button>
              <el-button size="small" type="danger" @click="rejectTask(row)">
                <el-icon><Close /></el-icon> 拒绝
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ===== Tab3: 全部流程 ===== -->
      <el-tab-pane label="全部流程" name="all">
        <div class="search-bar">
          <el-input v-model="allSearch" placeholder="搜索流程名称..." clearable style="width:280px" @input="debounceLoadAll">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="allStatusFilter" placeholder="状态筛选" clearable style="width:120px" @change="loadAllWorkflows">
            <el-option label="全部" value="" />
            <el-option label="运行中" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </div>
        <div v-if="allLoading" class="loading-area"><el-skeleton :rows="4" animated /></div>
        <el-table v-else :data="allWorkflows" stripe>
          <el-table-column prop="name" label="流程名称" min-width="160" />
          <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
          <el-table-column prop="flow_type" label="类型" width="100">
            <template #default="{ row }">{{ getFlowTypeLabel(row.flow_type) }}</template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '运行中' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" plain @click="goDesigner(row)">
                <el-icon><SetUp /></el-icon> 设计
              </el-button>
              <el-button size="small" plain @click="openEditDialog(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" plain @click="deleteWorkflow(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="allTotal > pageSize"
          :total="allTotal"
          :page-size="pageSize"
          :current-page="allPage"
          layout="prev, pager, next, total"
          @current-change="onAllPageChange"
          style="margin-top:16px;justify-content:center"
        />
      </el-tab-pane>

    </el-tabs>

    <!-- ===== 新建/编辑流程弹窗 ===== -->
    <el-dialog v-model="showDialog" :title="editingWorkflow ? '编辑流程' : '新建流程'" width="520px">
      <el-form :model="dialogForm" label-width="90px" :rules="dialogRules" ref="dialogFormRef">
        <el-form-item label="流程名称" prop="name">
          <el-input v-model="dialogForm.name" placeholder="请输入流程名称" />
        </el-form-item>
        <el-form-item label="流程描述" prop="description">
          <el-input v-model="dialogForm.description" type="textarea" :rows="3" placeholder="流程功能描述..." />
        </el-form-item>
        <el-form-item label="流程类型" prop="flow_type">
          <el-select v-model="dialogForm.flow_type" style="width:100%">
            <el-option label="普通流程" value="normal" />
            <el-option label="审批流程" value="approval" />
            <el-option label="文档流程" value="document" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="dialogForm.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveWorkflow">
          {{ editingWorkflow ? '保存修改' : '创建并设计' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 执行流程弹窗 ===== -->
    <el-dialog v-model="showExecuteDialog" title="执行流程" width="600px">
      <p style="color:#666;margin-bottom:16px">为流程「{{ executingWorkflow?.name }}」提交申请数据：</p>
      <el-form :model="executeForm" label-width="120px" ref="executeFormRef">
        <el-form-item label="申请标题" required>
          <el-input v-model="executeForm.title" placeholder="本次申请的简要标题" />
        </el-form-item>
        <el-form-item v-for="f in executeFields" :key="f.name" :label="f.label + (f.required ? ' *' : '')" :required="f.required">
          <el-input v-if="f.type === 'text'" v-model="executeForm.data[f.name]" :placeholder="f.placeholder" />
          <el-input v-else-if="f.type === 'textarea'" v-model="executeForm.data[f.name]" type="textarea" :rows="3" />
          <el-input-number v-else-if="f.type === 'number'" v-model="executeForm.data[f.name]" style="width:100%" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="executeForm.data[f.name]" type="date" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="executeForm.data[f.name]" style="width:100%">
            <el-option v-for="o in (f.options || [])" :key="o" :label="o" :value="o" />
          </el-select>
          <el-radio-group v-else-if="f.type === 'radio'" v-model="executeForm.data[f.name]">
            <el-radio v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-radio>
          </el-radio-group>
          <el-switch v-else-if="f.type === 'switch'" v-model="executeForm.data[f.name]" />
          <el-input v-else v-model="executeForm.data[f.name]" :placeholder="f.placeholder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExecuteDialog = false">取消</el-button>
        <el-button type="primary" :loading="executeLoading" @click="confirmExecute">
          提交申请
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Edit, Delete, View, SetUp, Search, Finished, Clock, Warning,
  Check, Close, Operation, VideoPlay, MagicStick
} from '@element-plus/icons-vue'
import { workflowAPI } from '../../api'

const router = useRouter()

// ===== 状态 =====
const activeTab = ref('my')
const mySearch = ref('')
const allSearch = ref('')
const allStatusFilter = ref('')
const myLoading = ref(false)
const pendingLoading = ref(false)
const allLoading = ref(false)
const pageSize = 10
const allPage = ref(1)
const allTotal = ref(0)

// ===== 数据 =====
const myWorkflows = ref<any[]>([])
const pendingTasks = ref<any[]>([])
const allWorkflows = ref<any[]>([])
let loadMyTimer: any = null
let loadAllTimer: any = null

function debounceLoadMy() { clearTimeout(loadMyTimer); loadMyTimer = setTimeout(loadMyWorkflows, 350) }
function debounceLoadAll() { clearTimeout(loadAllTimer); loadAllTimer = setTimeout(loadAllWorkflows, 350) }
function onTabChange(tab: string) {
  if (tab === 'my' && myWorkflows.value.length === 0) loadMyWorkflows()
  if (tab === 'pending' && pendingTasks.value.length === 0) loadPendingTasks()
  if (tab === 'all' && allWorkflows.value.length === 0) loadAllWorkflows()
}
function onAllPageChange(p: number) { allPage.value = p; loadAllWorkflows() }

// ===== 加载列表 =====
async function loadMyWorkflows() {
  myLoading.value = true
  try {
    const res: any = await workflowAPI.list({ search: mySearch.value || undefined, limit: 50 })
    myWorkflows.value = Array.isArray(res) ? res : (res.items || [])
  } catch { myWorkflows.value = [] }
  finally { myLoading.value = false }
}
async function loadPendingTasks() {
  pendingLoading.value = true
  try {
    // 调用后端待办接口，不存在时显示空
    const res: any = await (window as any).fetch('/api/v1/workflows/instances/pending', {
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') }
    })
    if (res.ok) {
      const json = await res.json()
      pendingTasks.value = Array.isArray(json) ? json : (json.items || json.data || [])
    } else {
      pendingTasks.value = []
    }
  } catch { pendingTasks.value = [] }
  finally { pendingLoading.value = false }
}
async function loadAllWorkflows() {
  allLoading.value = true
  try {
    const params: any = { skip: (allPage.value - 1) * pageSize, limit: pageSize }
    if (allSearch.value) params.search = allSearch.value
    const res: any = await workflowAPI.list(params)
    allWorkflows.value = Array.isArray(res) ? res : (res.items || [])
    allTotal.value = res.total || allWorkflows.value.length
  } catch { allWorkflows.value = []; allTotal.value = 0 }
  finally { allLoading.value = false }
}

// ===== 审批操作 =====
async function approveTask(task: any) {
  try {
    await ElMessageBox.confirm(`确定批准「${task.title}」？`, '审批确认', { type: 'success' })
    const res = await (window as any).fetch(`/api/v1/workflows/instances/${task.id}/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '')
      },
      body: JSON.stringify({ opinion: '同意' })
    })
    if (res.ok) {
      ElMessage.success('已批准')
      pendingTasks.value = pendingTasks.value.filter(t => t.id !== task.id)
    } else {
      ElMessage.error('操作失败，请重试')
    }
  } catch {}
}
async function rejectTask(task: any) {
  try {
    await ElMessageBox.confirm(`确定拒绝「${task.title}」？`, '审批确认', { type: 'warning' })
    const res = await (window as any).fetch(`/api/v1/workflows/instances/${task.id}/reject`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '')
      },
      body: JSON.stringify({ opinion: '不同意' })
    })
    if (res.ok) {
      ElMessage.warning('已拒绝')
      pendingTasks.value = pendingTasks.value.filter(t => t.id !== task.id)
    } else {
      ElMessage.error('操作失败，请重试')
    }
  } catch {}
}

// ===== 新建/编辑流程 =====
const showDialog = ref(false)
const editingWorkflow = ref<any>(null)
const dialogFormRef = ref()
const dialogForm = reactive({
  name: '',
  description: '',
  flow_type: 'normal',
  is_active: true
})
const dialogRules = {
  name: [{ required: true, message: '请输入流程名称', trigger: 'blur' }]
}
function openCreateDialog() {
  editingWorkflow.value = null
  dialogForm.name = ''
  dialogForm.description = ''
  dialogForm.flow_type = 'normal'
  dialogForm.is_active = true
  showDialog.value = true
}
function openEditDialog(w: any) {
  editingWorkflow.value = w
  dialogForm.name = w.name
  dialogForm.description = w.description || ''
  dialogForm.flow_type = w.flow_type || 'normal'
  dialogForm.is_active = w.is_active !== false
  showDialog.value = true
}
async function confirmSaveWorkflow() {
  if (!dialogForm.name.trim()) { ElMessage.warning('请输入流程名称'); return }
  try {
    if (editingWorkflow.value) {
      await workflowAPI.update(editingWorkflow.value.id, {
        name: dialogForm.name,
        description: dialogForm.description,
        flow_type: dialogForm.flow_type,
        is_active: dialogForm.is_active
      })
      // 更新本地数据
      const update = (list: any[]) => {
        const idx = list.findIndex(x => x.id === editingWorkflow.value.id)
        if (idx !== -1) Object.assign(list[idx], dialogForm)
      }
      update(myWorkflows.value); update(allWorkflows.value)
      ElMessage.success('保存成功')
    } else {
      const res: any = await workflowAPI.create({
        name: dialogForm.name,
        description: dialogForm.description,
        flow_type: dialogForm.flow_type,
        is_active: dialogForm.is_active,
        nodes: [],
        edges: []
      })
      myWorkflows.value.unshift(res)
      allWorkflows.value.unshift(res)
      ElMessage.success('流程已创建')
      showDialog.value = false
      // 自动跳转到设计器
      router.push('/workflows/design/' + res.id)
      return
    }
    showDialog.value = false
  } catch { ElMessage.error('保存失败') }
}
async function deleteWorkflow(w: any) {
  try {
    await ElMessageBox.confirm(`确定删除流程「${w.name}」？此操作不可恢复！`, '危险操作', { type: 'error' })
    await workflowAPI.delete(w.id)
    myWorkflows.value = myWorkflows.value.filter(x => x.id !== w.id)
    allWorkflows.value = allWorkflows.value.filter(x => x.id !== w.id)
    ElMessage.success('已删除')
  } catch {}
}

// ===== 执行流程 =====
const showExecuteDialog = ref(false)
const executeFormRef = ref()
const executingWorkflow = ref<any>(null)
const executeForm = reactive({ title: '', data: {} as Record<string, any> })
const executeFields = ref<any[]>([])
const executeLoading = ref(false)
function openExecuteDialog(w: any) {
  executingWorkflow.value = w
  executeForm.title = ''
  executeForm.data = {}
  // 尝试从 nodes 或 template 中解析字段
  let fields: any[] = []
  if (w.nodes && w.nodes.length > 0) {
    // 工作流节点中含字段定义
    fields = w.nodes.filter((n: any) => n.fields).flatMap((n: any) => n.fields)
  }
  if (fields.length === 0) {
    // 通用字段
    fields = [
      { name: 'reason', label: '申请原因', type: 'textarea', required: true, placeholder: '请详细描述申请理由' },
      { name: 'remark', label: '备注说明', type: 'textarea', required: false, placeholder: '其他补充说明' },
    ]
  }
  executeFields.value = fields
  fields.forEach(f => { if (!(f.name in executeForm.data)) executeForm.data[f.name] = '' })
  showExecuteDialog.value = true
}
async function confirmExecute() {
  if (!executeForm.title.trim()) { ElMessage.warning('请填写申请标题'); return }
  executeLoading.value = true
  try {
    await workflowAPI.execute(executingWorkflow.value.id, {
      title: executeForm.title,
      data: executeForm.data
    })
    ElMessage.success('申请已提交，请等待审批')
    showExecuteDialog.value = false
  } catch { ElMessage.error('提交失败，请稍后重试') }
  finally { executeLoading.value = false }
}

// ===== 工具函数 =====
function goDesigner(w: any) {
  router.push('/workflows/design/' + w.id)
}
function formatDate(s: string | null) {
  if (!s) return '-'
  return new Date(s).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
function getFlowTypeClass(t: string) {
  return { normal: 'type-normal', approval: 'type-approval', document: 'type-document' }[t || 'normal'] || 'type-normal'
}
function getFlowTypeLabel(t: string) {
  return { normal: '普通', approval: '审批', document: '文档' }[t || 'normal'] || '普通'
}

onMounted(() => {
  loadMyWorkflows()
})
</script>

<style scoped>
.page-container { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h3 { margin: 0; }
.header-actions { display: flex; gap: 8px; }
.search-bar { display: flex; gap: 10px; align-items: center; margin-bottom: 14px; }
.loading-area { padding: 30px 0; }

/* ===== 流程卡片 ===== */
.wf-card { margin-bottom: 16px; }
.wf-card:hover .wf-actions { opacity: 1; }
.wf-card-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.wf-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.type-normal { background: #409EFF; }
.type-approval { background: #67C23A; }
.type-document { background: #E6A23C; }
.wf-info { flex: 1; min-width: 0; }
.wf-info h4 { margin: 0 0 2px; font-size: 15px; }
.wf-code { font-size: 11px; color: #aaa; font-family: monospace; }
.wf-desc { margin: 0 0 8px; font-size: 13px; color: #666; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-meta { font-size: 12px; color: #aaa; margin-bottom: 10px; display: flex; gap: 12px; align-items: center; }
.wf-meta span { display: flex; align-items: center; gap: 4px; }
.wf-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; flex-wrap: wrap; }
</style>
