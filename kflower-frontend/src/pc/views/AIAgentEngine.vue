<template>
  <div class="ai-agent-engine-page">
    <div class="page-header">
      <h2>AI 智能体引擎</h2>
      <p class="subtitle">管理智能体、工具调用和任务执行</p>
    </div>

    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon agent"><el-icon><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.agents_count }}</div>
            <div class="stat-label">智能体数量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon task"><el-icon><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.tasks_total }}</div>
            <div class="stat-label">任务总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon tool"><el-icon><Tools /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.tools_count }}</div>
            <div class="stat-label">可用工具</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon status"><el-icon><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.orchestrator_status }}</div>
            <div class="stat-label">编排器</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="14">
        <el-card class="module-card">
          <template #header>
            <div class="card-header">
              <span>智能体列表</span>
              <div>
                <el-button type="primary" size="small" @click="showCreateDialog = true">创建智能体</el-button>
                <el-button size="small" @click="loadAll" :loading="loading">刷新</el-button>
              </div>
            </div>
          </template>

          <el-table :data="agents" style="width:100%" v-loading="loading">
            <el-table-column prop="name" label="名称" min-width="150">
              <template #default="{ row }">
                <div class="agent-name">
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === '在线' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tasks" label="任务数" width="80" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="toggleAgentStatus(row)">
                  {{ row.status === '在线' ? '停用' : '启用' }}
                </el-button>
                <el-button type="danger" size="small" link @click="deleteAgentItem(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!loading && agents.length === 0" class="empty-hint">
            暂未创建智能体，点击"创建智能体"开始
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="module-card">
          <template #header>
            <div class="card-header">
              <span>工具列表</span>
            </div>
          </template>
          <div v-if="tools.length > 0">
            <div v-for="tool in tools" :key="tool.name" class="tool-item">
              <div class="tool-info">
                <span class="tool-name">{{ tool.name }}</span>
                <span class="tool-desc">{{ tool.description }}</span>
              </div>
              <el-tag :type="tool.enabled ? 'success' : 'info'" size="small">
                {{ tool.enabled ? '启用' : '禁用' }}
              </el-tag>
            </div>
          </div>
          <div v-else class="empty-hint">暂无工具</div>
        </el-card>

        <el-card class="module-card" style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>AI 配置</span>
              <el-button size="small" @click="$router.push('/settings?tab=ai-models')">配置</el-button>
            </div>
          </template>
          <div class="config-section">
            <div class="config-item">
              <span class="config-label">当前模型</span>
              <el-tag type="success">{{ currentModel || '未配置' }}</el-tag>
            </div>
            <div class="config-item">
              <span class="config-label">网关状态</span>
              <el-tag :type="gatewayStatus ? 'success' : 'danger'">
                {{ gatewayStatus ? '已连接' : '未连接' }}
              </el-tag>
            </div>
            <el-button type="primary" plain style="width:100%;margin-top:12px" @click="$router.push('/settings?tab=ai-models')">
              前往配置 AI 模型
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 创建智能体对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建智能体" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="输入智能体名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="createForm.type" style="width:100%">
            <el-option label="通用助手" value="general" />
            <el-option label="数据分析" value="analytics" />
            <el-option label="模板设计" value="template" />
            <el-option label="工作流" value="workflow" />
            <el-option label="查询" value="query" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="智能体功能描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="createForm.status">
            <el-radio value="在线">在线</el-radio>
            <el-radio value="离线">离线</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createAgent" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, List, Tools, Connection } from '@element-plus/icons-vue'
import { aiAPI } from '@/common/api'

const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)

const agents = ref<any[]>([])
const tools = ref<any[]>([])

const stats = ref({
  agents_count: 0,
  tasks_total: 0,
  tools_count: 0,
  orchestrator_status: '未知'
})

const currentModel = ref<string | null>(null)
const gatewayStatus = ref(false)

const createForm = ref({
  name: '',
  type: 'general',
  description: '',
  status: '在线'
})

async function loadAgentEngineStatus() {
  try {
    const res = await aiAPI.getAgentEngineStatus()
    if (res && res.data) {
      stats.value = {
        agents_count: res.data.agents_count || 0,
        tasks_total: res.data.tasks_total || 0,
        tools_count: res.data.tools_count || 0,
        orchestrator_status: res.data.orchestrator_status || '已停止'
      }
    }
  } catch {
    // 静默处理
  }
}

async function loadAgents() {
  try {
    const res = await aiAPI.getAgentEngineAgents()
    if (res && res.data) {
      agents.value = Array.isArray(res.data) ? res.data : []
    }
  } catch {
    // 静默处理
  }
}

async function loadTools() {
  try {
    const res = await aiAPI.getAgentEngineTools()
    if (res && res.data) {
      tools.value = Array.isArray(res.data) ? res.data : []
    }
  } catch {
    // 静默处理
  }
}

async function loadDigitalBaseStatus() {
  try {
    const res = await aiAPI.getDigitalBaseStatus()
    if (res && res.data) {
      gatewayStatus.value = res.data.health?.ai_gateway === true
    }
  } catch {
    // 静默处理
  }
}

async function loadAll() {
  loading.value = true
  await Promise.allSettled([
    loadAgentEngineStatus(),
    loadAgents(),
    loadTools(),
    loadDigitalBaseStatus()
  ])
  loading.value = false
}

async function createAgent() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入智能体名称')
    return
  }
  creating.value = true
  try {
    await aiAPI.createAgent({
      name: createForm.value.name,
      type: createForm.value.type,
      description: createForm.value.description,
      status: createForm.value.status
    })
    ElMessage.success('智能体创建成功')
    showCreateDialog.value = false
    createForm.value = { name: '', type: 'general', description: '', status: '在线' }
    await loadAgents()
    await loadAgentEngineStatus()
  } catch (e: any) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function toggleAgentStatus(row: any) {
  const newStatus = row.status === '在线' ? '离线' : '在线'
  try {
    await aiAPI.updateAgent(row.id, { status: newStatus })
    ElMessage.success(`智能体已${newStatus === '在线' ? '启用' : '停用'}`)
    await loadAgents()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

async function deleteAgentItem(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除智能体「${row.name}」？`, '确认删除', { type: 'warning' })
    await aiAPI.deleteAgent(row.id)
    ElMessage.success('删除成功')
    await loadAgents()
    await loadAgentEngineStatus()
  } catch {
    // 取消
  }
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.ai-agent-engine-page { padding: 0; }
.page-header { margin-bottom: 24px; }
.page-header h2 { margin: 0; font-size: 24px; color: var(--el-text-color-primary); }
.subtitle { margin: 8px 0 0; color: var(--el-text-color-regular); font-size: 14px; }
.overview-cards { margin-bottom: 24px; }
.stat-card { background: var(--el-bg-color); border-radius: 8px; padding: 20px; border: 1px solid #ebeef5; display: flex; align-items: center; gap: 16px; height: 100%; }
.stat-icon { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.stat-icon.agent { background: #ecf5ff; color: #409EFF; }
.stat-icon.task { background: #f0f9eb; color: #67C23A; }
.stat-icon.tool { background: #fdf6ec; color: #E6A23C; }
.stat-icon.status { background: #f4f4f5; color: #909399; }
.stat-value { font-size: 28px; font-weight: 600; color: var(--el-text-color-primary); }
.stat-label { font-size: 13px; color: var(--el-text-color-secondary); margin-top: 4px; }
.module-card { height: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.agent-name { display: flex; align-items: center; gap: 8px; }
.tool-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #ebeef5; }
.tool-item:last-child { border-bottom: none; }
.tool-info { flex: 1; }
.tool-name { font-weight: 500; display: block; }
.tool-desc { font-size: 12px; color: var(--el-text-color-secondary); }
.config-section { padding: 4px 0; }
.config-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
.config-label { color: var(--el-text-color-regular); }
.empty-hint { text-align: center; color: var(--el-text-color-secondary); padding: 40px 0; font-size: 14px; }
</style>
