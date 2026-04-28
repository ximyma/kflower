<template>
  <div class="data-modeling-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.push('/templates')">
          <el-icon><ArrowLeft /></el-icon> 返回模板设计
        </el-button>
        <h2>📊 数据建模</h2>
        <el-tag type="info">{{ stats.total_models }} 个模型</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="openConnectionDialog">
          <el-icon><Connection /></el-icon> 连接数据库
        </el-button>
        <el-button @click="openKflowerCopy">
          <el-icon><CopyDocument /></el-icon> 复制内部表
        </el-button>
        <el-button @click="openAIModeling">
          <el-icon><MagicStick /></el-icon> AI 建模
        </el-button>
        <el-button type="primary" @click="openCreateModelDialog">
          <el-icon><Plus /></el-icon> 新建模型
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: var(--el-color-primary);">
          <el-icon :size="24"><Coin /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_models }}</div>
          <div class="stat-label">数据模型</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: var(--el-color-success);">
          <el-icon :size="24"><Grid /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_created }}</div>
          <div class="stat-label">已建表</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: var(--el-color-warning);">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_templates }}</div>
          <div class="stat-label">已生成模板</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: var(--el-color-danger);">
          <el-icon :size="24"><Connection /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_connections }}</div>
          <div class="stat-label">数据库连接</div>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div class="model-list" v-loading="loading">
      <el-empty v-if="models.length === 0 && !loading" description="暂无数据模型">
        <div class="empty-actions">
          <el-button type="primary" @click="openCreateModelDialog">
            <el-icon><Plus /></el-icon> 新建模型
          </el-button>
          <el-button @click="openAIModeling">
            <el-icon><MagicStick /></el-icon> AI 建模
          </el-button>
        </div>
      </el-empty>

      <div v-else class="model-cards">
        <el-card v-for="m in models" :key="m.id" shadow="hover" class="model-card" @click="openDesigner(m)">
          <div class="card-top">
            <div class="card-icon" :style="{ background: getSourceColor(m.source_type) }">
              <el-icon :size="20"><component :is="getSourceIcon(m.source_type)" /></el-icon>
            </div>
            <div class="card-title">
              <h4>{{ m.title }}</h4>
              <span class="card-name">{{ m.name }}</span>
            </div>
            <div class="card-badges">
              <el-tag v-if="m.is_created" type="success" size="small">已建表</el-tag>
              <el-tag v-else type="info" size="small">未建表</el-tag>
              <el-tag v-if="m.template_id" type="warning" size="small">已生成模板</el-tag>
            </div>
          </div>
          <div class="card-desc" v-if="m.description">{{ m.description }}</div>
          <div class="card-meta">
            <span><el-icon><Coin /></el-icon> {{ m.field_count }} 字段</span>
            <span><el-icon><Clock /></el-icon> {{ formatTime(m.updated_at) }}</span>
            <el-tag size="small" :type="getSourceTagType(m.source_type)">
              {{ getSourceLabel(m.source_type) }}
            </el-tag>
          </div>
          <div class="card-actions" @click.stop>
            <el-button size="small" type="primary" text @click="openDesigner(m)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button v-if="!m.is_created" size="small" type="success" text @click="createTable(m)">
              <el-icon><Grid /></el-icon> 建表
            </el-button>
            <el-button v-if="!m.template_id" size="small" type="warning" text @click="generateTemplate(m)">
              <el-icon><Document /></el-icon> 生成模板
            </el-button>
            <el-button v-if="m.template_id" size="small" text @click="goToTemplate(m)">
              <el-icon><View /></el-icon> 查看模板
            </el-button>
            <el-button size="small" type="danger" text @click="deleteModel(m)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <!-- ===== 新建模型对话框 ===== -->
    <el-dialog v-model="showCreateDialog" title="新建数据模型" width="600px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="表名" required>
          <el-input v-model="createForm.name" placeholder="英文小写下划线，如 customers" />
        </el-form-item>
        <el-form-item label="显示名" required>
          <el-input v-model="createForm.title" placeholder="中文名称，如 客户信息表" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createModel" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- ===== AI建模对话框 ===== -->
    <el-dialog v-model="showAIModeling" title="🤖 AI 数据建模" width="640px" :close-on-click-modal="false">
      <div class="ai-modeling-content">
        <p class="ai-hint">用自然语言描述你的业务需求，AI自动设计数据表结构</p>
        <el-input
          v-model="aiRequirement"
          type="textarea"
          :rows="4"
          placeholder="例如：我需要设计一个客户订单管理系统，包含客户信息、订单、产品..."
        />
        <div class="ai-examples">
          <span>示例：</span>
          <el-tag v-for="ex in aiExamples" :key="ex" size="small" @click="aiRequirement = ex" style="cursor:pointer">
            {{ ex }}
          </el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAIModeling = false">取消</el-button>
        <el-button type="primary" @click="doAIModeling" :loading="aiLoading">
          <el-icon><MagicStick /></el-icon> 生成数据模型
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 复制内部表对话框 ===== -->
    <el-dialog v-model="showKflowerCopy" title="📋 复制 Kflower 内部数据表" width="700px">
      <div v-loading="loadingKflowerTables">
        <el-empty v-if="kflowerTables.length === 0" description="暂无已发布的数据表" />
        <div v-else class="kflower-table-list">
          <div v-for="t in kflowerTables" :key="t.table_name" class="kflower-table-item">
            <div class="kt-info">
              <span class="kt-name">{{ t.template_name }}</span>
              <span class="kt-table">{{ t.table_name }}</span>
              <el-tag size="small">{{ t.field_count }} 字段</el-tag>
              <el-tag size="small" type="info">{{ t.row_count }} 条数据</el-tag>
            </div>
            <el-button size="small" type="primary" @click="doCopyKflowerTable(t)">
              <el-icon><CopyDocument /></el-icon> 复制为模板
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- ===== 连接数据库对话框 ===== -->
    <el-dialog v-model="showConnectionDialog" title="🔗 连接外部数据库" width="550px" :close-on-click-modal="false">
      <el-form :model="connectionForm" label-width="90px">
        <el-form-item label="连接名称" required>
          <el-input v-model="connectionForm.name" placeholder="如：公司ERP库" />
        </el-form-item>
        <el-form-item label="数据库类型" required>
          <el-select v-model="connectionForm.db_type" style="width:100%">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
          </el-select>
        </el-form-item>
        <template v-if="connectionForm.db_type !== 'sqlite'">
          <el-form-item label="主机地址">
            <el-input v-model="connectionForm.host" placeholder="192.168.1.100" />
          </el-form-item>
          <el-form-item label="端口">
            <el-input-number v-model="connectionForm.port" :min="1" :max="65535" />
          </el-form-item>
        </template>
        <el-form-item :label="connectionForm.db_type === 'sqlite' ? '文件路径' : '数据库名'">
          <el-input v-model="connectionForm.database" :placeholder="connectionForm.db_type === 'sqlite' ? 'C:/data/mydb.sqlite' : 'company_db'" />
        </el-form-item>
        <template v-if="connectionForm.db_type !== 'sqlite'">
          <el-form-item label="用户名">
            <el-input v-model="connectionForm.username" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="connectionForm.password" type="password" show-password />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="testConnection" :loading="testingConn">测试连接</el-button>
        <el-button @click="showConnectionDialog = false">取消</el-button>
        <el-button type="primary" @click="saveConnection" :loading="savingConn">保存</el-button>
      </template>
    </el-dialog>

    <!-- ===== 复制表命名对话框 ===== -->
    <el-dialog v-model="showCopyNameDialog" title="复制为新模板" width="400px">
      <el-form label-width="80px">
        <el-form-item label="新模板名">
          <el-input v-model="copyTemplateName" placeholder="输入新模板名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCopyNameDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCopyTable" :loading="copying">确认复制</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Edit, Delete, Coin, Connection, MagicStick, Document,
  Grid, ArrowLeft, View, CopyDocument, Clock, SetUp, Operation
} from '@element-plus/icons-vue'
import { dataModelAPI } from '../../common/api'

const router = useRouter()

// 状态
const loading = ref(false)
const models = ref<any[]>([])
const stats = ref({
  total_models: 0,
  total_created: 0,
  total_templates: 0,
  total_connections: 0,
})

// 新建模型
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  name: '',
  title: '',
  description: '',
})

// AI建模
const showAIModeling = ref(false)
const aiRequirement = ref('')
const aiLoading = ref(false)
const aiExamples = [
  '客户订单管理系统',
  '员工考勤与薪资管理',
  '仓库进销存管理',
  '项目任务跟踪系统',
]

// Kflower内部表复制
const showKflowerCopy = ref(false)
const loadingKflowerTables = ref(false)
const kflowerTables = ref<any[]>([])
const showCopyNameDialog = ref(false)
const copyTemplateName = ref('')
const copyingSourceTable = ref('')
const copying = ref(false)

// 数据库连接
const showConnectionDialog = ref(false)
const testingConn = ref(false)
const savingConn = ref(false)
const connectionForm = ref({
  name: '',
  db_type: 'mysql',
  host: '',
  port: 3306,
  database: '',
  username: '',
  password: '',
})

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const [modelsRes, statsRes] = await Promise.all([
      dataModelAPI.listModels(),
      dataModelAPI.getStats(),
    ])
    if (modelsRes?.success) {
      models.value = modelsRes?.data || []
    }
    if (statsRes?.success) {
      stats.value = statsRes?.data || stats.value
    }
  } catch (e: any) {
    ElMessage.error('加载数据失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 新建模型
function openCreateModelDialog() {
  createForm.value = { name: '', title: '', description: '' }
  showCreateDialog.value = true
}

async function createModel() {
  if (!createForm.value.name || !createForm.value.title) {
    ElMessage.warning('请填写表名和显示名')
    return
  }
  creating.value = true
  try {
    const res = await dataModelAPI.createModel(createForm.value)
    if (res?.success) {
      ElMessage.success('创建成功')
      showCreateDialog.value = false
      const modelId = res?.data?.id
      if (modelId) {
        router.push(`/data-modeling/designer/${modelId}`)
      } else {
        loadData()
      }
    } else {
      ElMessage.error(res?.message || '创建失败')
    }
  } catch (e: any) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

// AI建模
function openAIModeling() {
  aiRequirement.value = ''
  showAIModeling.value = true
}

async function doAIModeling() {
  if (!aiRequirement.value.trim()) {
    ElMessage.warning('请描述你的业务需求')
    return
  }
  aiLoading.value = true
  try {
    const res = await dataModelAPI.aiGenerate(aiRequirement.value)
    if (res?.success) {
      const data = res?.data
      ElMessage.success(`AI建模成功！生成 ${data?.models?.length || 0} 个数据模型`)
      showAIModeling.value = false
      loadData()
    } else {
      ElMessage.error(res?.message || 'AI建模失败')
    }
  } catch (e: any) {
    ElMessage.error('AI建模失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    aiLoading.value = false
  }
}

// 打开设计器
function openDesigner(m: any) {
  router.push(`/data-modeling/designer/${m.id}`)
}

// 建表
async function createTable(m: any) {
  try {
    await ElMessageBox.confirm(
      `确定要为「${m.title}」创建物理数据表吗？`,
      '创建数据表',
      { type: 'info' }
    )
    const res = await dataModelAPI.createTable(m.id)
    if (res?.success) {
      ElMessage.success('数据表创建成功')
      loadData()
    } else {
      ElMessage.error(res?.message || '建表失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('建表失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

// 生成模板
async function generateTemplate(m: any) {
  try {
    await ElMessageBox.confirm(
      `确定要从「${m.title}」生成 Kflower 模板吗？`,
      '生成模板',
      { type: 'info' }
    )
    const res = await dataModelAPI.generateTemplate(m.id)
    if (res?.success) {
      ElMessage.success('模板生成成功')
      loadData()
    } else {
      ElMessage.error(res?.message || '生成失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

// 跳转模板
function goToTemplate(m: any) {
  if (m.template_id) {
    router.push(`/form/${m.template_id}`)
  }
}

// 删除模型
async function deleteModel(m: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除数据模型「${m.title}」吗？删除后不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    const res = await dataModelAPI.deleteModel(m.id)
    if (res?.success) {
      ElMessage.success('删除成功')
      loadData()
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

// Kflower内部表
async function openKflowerCopy() {
  showKflowerCopy.value = true
  loadingKflowerTables.value = true
  try {
    const res = await dataModelAPI.listKflowerTables()
    if (res?.success) {
      kflowerTables.value = res?.data || []
    }
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.message || ''))
  } finally {
    loadingKflowerTables.value = false
  }
}

function doCopyKflowerTable(t: any) {
  copyingSourceTable.value = t.table_name
  copyTemplateName.value = t.template_name + ' (副本)'
  showCopyNameDialog.value = true
}

async function confirmCopyTable() {
  if (!copyTemplateName.value.trim()) {
    ElMessage.warning('请输入新模板名称')
    return
  }
  copying.value = true
  try {
    const res = await dataModelAPI.copyKflowerTable(
      copyingSourceTable.value,
      copyTemplateName.value
    )
    if (res?.success) {
      ElMessage.success('复制成功')
      showCopyNameDialog.value = false
      showKflowerCopy.value = false
      loadData()
    } else {
      ElMessage.error(res?.message || '复制失败')
    }
  } catch (e: any) {
    ElMessage.error('复制失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    copying.value = false
  }
}

// 数据库连接
function openConnectionDialog() {
  connectionForm.value = {
    name: '', db_type: 'mysql', host: '', port: 3306,
    database: '', username: '', password: '',
  }
  showConnectionDialog.value = true
}

async function testConnection() {
  testingConn.value = true
  try {
    // 先保存再测试
    const res = await dataModelAPI.createConnection(connectionForm.value)
    if (res?.success) {
      const connId = res?.data?.id
      if (connId) {
        const testRes = await dataModelAPI.testConnection(connId)
        if (testRes?.success) {
          ElMessage.success('连接测试成功')
        } else {
          ElMessage.warning('连接测试失败: ' + (testRes?.message || ''))
        }
      }
    }
  } catch (e: any) {
    ElMessage.error('测试失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    testingConn.value = false
  }
}

async function saveConnection() {
  if (!connectionForm.value.name) {
    ElMessage.warning('请输入连接名称')
    return
  }
  savingConn.value = true
  try {
    const res = await dataModelAPI.createConnection(connectionForm.value)
    if (res?.success) {
      ElMessage.success('连接保存成功')
      showConnectionDialog.value = false
      loadData()
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    savingConn.value = false
  }
}

// 辅助方法
function getSourceColor(type: string) {
  const map: Record<string, string> = {
    manual: 'var(--el-color-primary)',
    import_db: 'var(--el-color-success)',
    copy_kflower: 'var(--el-color-warning)',
    ai: 'var(--el-color-danger)',
  }
  return map[type] || 'var(--el-color-info)'
}

function getSourceIcon(type: string) {
  const map: Record<string, any> = {
    manual: SetUp,
    import_db: Connection,
    copy_kflower: CopyDocument,
    ai: MagicStick,
  }
  return map[type] || Coin
}

function getSourceTagType(type: string) {
  const map: Record<string, string> = {
    manual: '', import_db: 'success', copy_kflower: 'warning', ai: 'danger',
  }
  return map[type] || 'info'
}

function getSourceLabel(type: string) {
  const map: Record<string, string> = {
    manual: '手动创建', import_db: '数据库导入', copy_kflower: '复制内部表', ai: 'AI生成',
  }
  return map[type] || type
}

function formatTime(t: string | null) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  return d.toLocaleDateString()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.data-modeling-page {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.header-right {
  display: flex;
  gap: 8px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.model-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

.model-card {
  cursor: pointer;
  transition: all 0.2s;
}

.model-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.card-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.card-title {
  flex: 1;
  min-width: 0;
}

.card-title h4 {
  margin: 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-name {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: monospace;
}

.card-badges {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.card-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.card-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  display: flex;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.empty-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* AI建模 */
.ai-modeling-content {
  padding: 0 0 16px;
}

.ai-hint {
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.ai-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

/* Kflower表复制 */
.kflower-table-list {
  max-height: 400px;
  overflow-y: auto;
}

.kflower-table-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.kt-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.kt-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.kt-table {
  font-size: 12px;
  font-family: monospace;
  color: var(--el-text-color-secondary);
}
</style>
