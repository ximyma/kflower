<template>
  <div class="app-data-view-page">
    <div class="page-header">
      <h2>📊 应用数据视图</h2>
      <p class="subtitle">统一查看应用的跨模块关联数据</p>
    </div>

    <!-- 应用选择器 -->
    <el-card class="app-selector-card">
      <el-form :inline="true">
        <el-form-item label="选择应用">
          <el-select
            v-model="selectedAppId"
            placeholder="请选择应用"
            style="width: 300px"
            filterable
            @change="onAppChange"
          >
            <el-option
              v-for="app in apps"
              :key="app.id"
              :label="app.name"
              :value="app.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAppData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 无应用选中时的提示 -->
    <el-empty v-if="!selectedAppId" description="请先选择一个应用" style="margin-top: 60px" />

    <!-- 数据概览 -->
    <div v-if="selectedAppId" class="data-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card templates">
            <div class="stat-icon"><el-icon><Document /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ appStats.templateCount }}</div>
              <div class="stat-label">绑定模板</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card workflows">
            <div class="stat-icon"><el-icon><Connection /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ appStats.workflowCount }}</div>
              <div class="stat-label">绑定工作流</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card agents">
            <div class="stat-icon"><el-icon><User /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ appStats.agentCount }}</div>
              <div class="stat-label">绑定智能体</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card knowledge">
            <div class="stat-icon"><el-icon><Reading /></el-icon></div>
            <div class="stat-info">
              <div class="stat-value">{{ appStats.knowledgeCount }}</div>
              <div class="stat-label">绑定知识库</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 详细信息区域 -->
    <div v-if="selectedAppId" class="data-detail">
      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 模板数据 -->
        <el-tab-pane label="模板数据" name="templates">
          <div class="tab-content">
            <el-table :data="templateData" style="width: 100%" v-loading="loading">
              <el-table-column prop="name" label="模板名称" min-width="150" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
                    {{ row.is_published ? '已发布' : '草稿' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="dataCount" label="数据条数" width="120" align="center" />
              <el-table-column prop="updatedAt" label="最后更新" width="180" />
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="viewTemplate(row)">查看</el-button>
                  <el-button type="success" size="small" link @click="openTemplateData(row)">数据</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="templateData.length === 0 && !loading" description="暂无绑定的模板" />
          </div>
        </el-tab-pane>

        <!-- 工作流数据 -->
        <el-tab-pane label="工作流数据" name="workflows">
          <div class="tab-content">
            <el-table :data="workflowData" style="width: 100%" v-loading="loading">
              <el-table-column prop="name" label="工作流名称" min-width="150" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
                    {{ row.is_published ? '已发布' : '草稿' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="instanceCount" label="实例数" width="100" align="center" />
              <el-table-column prop="runningCount" label="进行中" width="100" align="center">
                <template #default="{ row }">
                  <el-tag type="warning" size="small" v-if="row.runningCount > 0">
                    {{ row.runningCount }}
                  </el-tag>
                  <span v-else>0</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="viewWorkflow(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="workflowData.length === 0 && !loading" description="暂无绑定的工作流" />
          </div>
        </el-tab-pane>

        <!-- 智能体数据 -->
        <el-tab-pane label="智能体数据" name="agents">
          <div class="tab-content">
            <el-table :data="agentData" style="width: 100%" v-loading="loading">
              <el-table-column prop="name" label="智能体名称" min-width="150" />
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === '在线' ? 'success' : row.status === '禁用' ? 'danger' : 'info'" size="small">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="templateCount" label="绑定模板" width="120" align="center" />
              <el-table-column prop="knowledgeCount" label="绑定知识库" width="120" align="center" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="configureAgent(row)">配置</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="agentData.length === 0 && !loading" description="暂无绑定的智能体" />
          </div>
        </el-tab-pane>

        <!-- 知识库数据 -->
        <el-tab-pane label="知识库数据" name="knowledge">
          <div class="tab-content">
            <el-table :data="knowledgeData" style="width: 100%" v-loading="loading">
              <el-table-column prop="name" label="知识库名称" min-width="150" />
              <el-table-column prop="docCount" label="文档数" width="100" align="center" />
              <el-table-column prop="vectorCount" label="向量数" width="100" align="center" />
              <el-table-column prop="updatedAt" label="最后更新" width="180" />
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="viewKnowledge(row)">查看</el-button>
                  <el-button type="success" size="small" link @click="manageDocuments(row)">文档</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="knowledgeData.length === 0 && !loading" description="暂无绑定的知识库" />
          </div>
        </el-tab-pane>

        <!-- 应用菜单 -->
        <el-tab-pane label="应用菜单" name="menus">
          <div class="tab-content">
            <el-tree
              :data="menuTree"
              :props="{ label: 'label', children: 'children' }"
              node-key="id"
              default-expand-all
            >
              <template #default="{ node, data }">
                <span class="menu-tree-node">
                  <el-icon><component :is="data.icon || 'Document'" /></el-icon>
                  <span>{{ node.label }}</span>
                  <el-tag size="small" type="info" v-if="data.template_id" style="margin-left: 8px">
                    已绑定模板
                  </el-tag>
                  <el-tag size="small" type="warning" v-if="data.workflow_id" style="margin-left: 4px">
                    已绑定工作流
                  </el-tag>
                </span>
              </template>
            </el-tree>
            <el-empty v-if="menuTree.length === 0 && !loading" description="暂无菜单" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Document, Connection, User, Reading } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'
import { templateAPI, aiAPI, workflowAPI } from '@/common/api/index'

const router = useRouter()

const loading = ref(false)
const apps = ref<any[]>([])
const selectedAppId = ref<number | null>(null)
const activeTab = ref('templates')

// 统计数据
const appStats = reactive({
  templateCount: 0,
  workflowCount: 0,
  agentCount: 0,
  knowledgeCount: 0,
})

// 各模块数据
const templateData = ref<any[]>([])
const workflowData = ref<any[]>([])
const agentData = ref<any[]>([])
const knowledgeData = ref<any[]>([])
const menuTree = ref<any[]>([])

// 加载应用列表
async function loadApps() {
  try {
    const res = await appAPI.list()
    apps.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    console.error('加载应用列表失败', e)
  }
}

// 应用选择变更
async function onAppChange(appId: number) {
  selectedAppId.value = appId
  if (appId) {
    await loadAppData()
  }
}

// 加载应用完整数据
async function loadAppData() {
  if (!selectedAppId.value) return

  loading.value = true
  try {
    const appId = selectedAppId.value

    // 并行加载所有数据
    await Promise.all([
      loadAppDetail(appId),
      loadTemplates(appId),
      loadWorkflows(appId),
      loadAgents(appId),
      loadKnowledgeBases(appId),
      loadMenus(appId),
    ])
  } catch (e: any) {
    console.error('加载应用数据失败', e)
    ElMessage.error('加载数据失败：' + (e.message || ''))
  } finally {
    loading.value = false
  }
}

// 加载应用详情
async function loadAppDetail(appId: number) {
  try {
    const res: any = await appAPI.get(appId)
    // 更新统计数据
    appStats.templateCount = res.bound_templates?.length || 0
    appStats.workflowCount = res.workflow_ids?.length || 0
    appStats.agentCount = res.bound_agents?.length || 0
    appStats.knowledgeCount = res.knowledge_base_ids?.length || 0
  } catch (e) {
    console.error('加载应用详情失败', e)
  }
}

// 加载绑定的模板
async function loadTemplates(appId: number) {
  try {
    const res = await templateAPI.list({ limit: 100 })
    const allTemplates = Array.isArray(res) ? res : (res.data || [])
    
    // 获取应用详情以获取绑定的模板ID
    const appRes: any = await appAPI.get(appId)
    const boundTemplateIds = appRes.bound_templates || appRes.template_ids || []
    
    // 过滤出绑定的模板
    templateData.value = allTemplates
      .filter((t: any) => boundTemplateIds.includes(t.id))
      .map((t: any) => ({
        ...t,
        dataCount: t.data_count || 0,
        updatedAt: t.updated_at ? new Date(t.updated_at).toLocaleString() : '-',
      }))
    
    // 更新统计
    appStats.templateCount = templateData.value.length
  } catch (e) {
    console.error('加载模板数据失败', e)
    templateData.value = []
  }
}

// 加载绑定的工作流
async function loadWorkflows(appId: number) {
  try {
    const res: any = await fetch('/api/v1/workflows/', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())
    const allWorkflows = Array.isArray(res) ? res : (res.data || [])
    
    // 获取应用详情以获取绑定的工作流ID
    const appRes: any = await appAPI.get(appId)
    const boundWorkflowIds = appRes.workflow_ids || []
    
    // 过滤出绑定的工作流
    workflowData.value = allWorkflows
      .filter((w: any) => boundWorkflowIds.includes(w.id))
      .map((w: any) => ({
        ...w,
        name: w.name || w.title,
        instanceCount: w.instance_count || 0,
        runningCount: w.running_count || 0,
      }))
    
    // 更新统计
    appStats.workflowCount = workflowData.value.length
  } catch (e) {
    console.error('加载工作流数据失败', e)
    workflowData.value = []
  }
}

// 加载绑定的智能体
async function loadAgents(appId: number) {
  try {
    const res = await aiAPI.getAgentEngineAgents()
    const allAgents = res.data || []
    
    // 获取应用详情以获取绑定的智能体ID
    const appRes: any = await appAPI.get(appId)
    const boundAgentIds = appRes.bound_agents || []
    
    // 过滤出绑定的智能体
    agentData.value = allAgents
      .filter((a: any) => boundAgentIds.includes(a.id))
      .map((a: any) => ({
        ...a,
        templateCount: parseJsonArray(a.template_ids).length,
        knowledgeCount: parseJsonArray(a.knowledge_base_ids).length,
      }))
    
    // 更新统计
    appStats.agentCount = agentData.value.length
  } catch (e) {
    console.error('加载智能体数据失败', e)
    agentData.value = []
  }
}

// 加载绑定的知识库
async function loadKnowledgeBases(appId: number) {
  try {
    const res = await fetch('/api/v1/knowledge-bases/', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())
    const allKb = Array.isArray(res) ? res : (res.data || [])
    
    // 获取应用详情以获取绑定的知识库ID
    const appRes: any = await appAPI.get(appId)
    const boundKbIds = appRes.knowledge_base_ids || []
    
    // 过滤出绑定的知识库
    knowledgeData.value = allKb
      .filter((kb: any) => boundKbIds.includes(kb.id))
      .map((kb: any) => ({
        ...kb,
        updatedAt: kb.updated_at ? new Date(kb.updated_at).toLocaleString() : '-',
      }))
    
    // 更新统计
    appStats.knowledgeCount = knowledgeData.value.length
  } catch (e) {
    console.error('加载知识库数据失败', e)
    knowledgeData.value = []
  }
}

// 加载菜单树
async function loadMenus(appId: number) {
  try {
    const res = await appAPI.getMenuTree(appId)
    menuTree.value = res || []
  } catch (e) {
    console.error('加载菜单失败', e)
    menuTree.value = []
  }
}

// 解析 JSON 数组
function parseJsonArray(value: any): number[] {
  if (!value) return []
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// 操作函数
function viewTemplate(row: any) {
  router.push(`/template-designer/${row.id}`)
}

function openTemplateData(row: any) {
  router.push(`/template-data/${row.id}`)
}

function viewWorkflow(row: any) {
  router.push(`/workflow-designer/${row.id}`)
}

function configureAgent(row: any) {
  router.push('/agent-orchestrator')
}

function viewKnowledge(row: any) {
  router.push('/knowledge-base')
}

function manageDocuments(row: any) {
  router.push('/knowledge-base')
}

// 初始化
onMounted(() => {
  loadApps()
})
</script>

<style scoped lang="scss">
.app-data-view-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;

  h2 {
    margin: 0;
    font-size: 24px;
    color: var(--el-text-color-primary);
  }

  .subtitle {
    margin: 8px 0 0;
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}

.app-selector-card {
  margin-bottom: 24px;
}

.data-overview {
  margin-bottom: 24px;
}

.stat-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  gap: 16px;

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
  }

  &.templates .stat-icon {
    background: #ecf5ff;
    color: #409EFF;
  }

  &.workflows .stat-icon {
    background: #f0f9eb;
    color: #67C23A;
  }

  &.agents .stat-icon {
    background: #fef0f0;
    color: #F56C6C;
  }

  &.knowledge .stat-icon {
    background: #fdf6ec;
    color: #E6A23C;
  }

  .stat-info {
    flex: 1;

    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .stat-label {
      font-size: 13px;
      color: var(--el-text-color-secondary);
      margin-top: 4px;
    }
  }
}

.data-detail {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  padding: 16px;
}

.detail-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 16px;
  }
}

.tab-content {
  min-height: 300px;
}

.menu-tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
</style>
