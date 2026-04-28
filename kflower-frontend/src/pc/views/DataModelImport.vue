<template>
  <div class="data-model-import-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.push('/data-modeling')">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h2>📥 导入数据库表</h2>
      </div>
    </div>

    <!-- 步骤条 -->
    <div class="steps-bar">
      <el-steps :active="step" align-center>
        <el-step title="选择连接" />
        <el-step title="选择数据表" />
        <el-step title="确认导入" />
      </el-steps>
    </div>

    <!-- Step 1: 选择/创建连接 -->
    <div v-if="step === 0" class="step-content">
      <div class="connections-section">
        <div class="section-header">
          <h3>数据库连接</h3>
          <el-button type="primary" size="small" @click="showNewConnForm = !showNewConnForm">
            <el-icon><Plus /></el-icon> 新建连接
          </el-button>
        </div>

        <!-- 已有连接列表 -->
        <div v-if="connections.length > 0" class="conn-list">
          <div
            v-for="c in connections"
            :key="c.id"
            class="conn-card"
            :class="{ active: selectedConnId === c.id }"
            @click="selectConnection(c)"
          >
            <div class="conn-icon" :style="{ background: getDbTypeColor(c.db_type) }">
              {{ c.db_type.charAt(0).toUpperCase() }}
            </div>
            <div class="conn-info">
              <div class="conn-name">{{ c.name }}</div>
              <div class="conn-meta">{{ c.db_type }} · {{ c.host || c.database }}</div>
            </div>
            <div class="conn-status">
              <el-tag v-if="c.is_active" type="success" size="small">活跃</el-tag>
              <el-tag v-else type="info" size="small">未测试</el-tag>
            </div>
          </div>
        </div>

        <!-- 新建连接表单 -->
        <el-card v-if="showNewConnForm" class="new-conn-card" shadow="never">
          <h4>新建数据库连接</h4>
          <el-form :model="newConnForm" label-width="100px" size="small">
            <el-form-item label="连接名称" required>
              <el-input v-model="newConnForm.name" placeholder="如：公司ERP库" />
            </el-form-item>
            <el-form-item label="数据库类型" required>
              <el-select v-model="newConnForm.db_type" style="width:100%">
                <el-option label="MySQL" value="mysql" />
                <el-option label="PostgreSQL" value="postgresql" />
                <el-option label="SQLite" value="sqlite" />
              </el-select>
            </el-form-item>
            <template v-if="newConnForm.db_type !== 'sqlite'">
              <el-form-item label="主机地址" required>
                <el-input v-model="newConnForm.host" placeholder="192.168.1.100" />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number v-model="newConnForm.port" :min="1" :max="65535" />
              </el-form-item>
            </template>
            <el-form-item :label="newConnForm.db_type === 'sqlite' ? '文件路径' : '数据库名'" required>
              <el-input v-model="newConnForm.database" :placeholder="newConnForm.db_type === 'sqlite' ? 'C:/data/mydb.sqlite' : 'company_db'" />
            </el-form-item>
            <template v-if="newConnForm.db_type !== 'sqlite'">
              <el-form-item label="用户名">
                <el-input v-model="newConnForm.username" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="newConnForm.password" type="password" show-password />
              </el-form-item>
            </template>
            <el-form-item>
              <el-button @click="testNewConn" :loading="testingNew">测试连接</el-button>
              <el-button type="primary" @click="saveNewConn" :loading="savingNew">保存并选择</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <div class="step-actions">
          <el-button type="primary" :disabled="!selectedConnId" @click="goToStep(1)">
            下一步 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Step 2: 选择数据表 -->
    <div v-if="step === 1" class="step-content">
      <div class="tables-section" v-loading="loadingTables">
        <div class="section-header">
          <h3>选择要导入的数据表</h3>
          <el-input v-model="tableSearch" placeholder="搜索表名..." style="width:220px" clearable size="small">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>

        <el-empty v-if="externalTables.length === 0 && !loadingTables" description="未发现数据表" />

        <el-table
          v-else
          :data="filteredTables"
          @selection-change="onTableSelection"
          style="width:100%"
          size="small"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="name" label="表名" min-width="160">
            <template #default="{ row }">
              <span style="font-family:monospace;font-weight:600">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="注释" min-width="200">
            <template #default="{ row }">
              {{ row.comment || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="row_count" label="行数" width="100" align="right" />
          <el-table-column label="预览结构" width="100" align="center">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="previewSchema(row.name)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="step-actions">
          <el-button @click="goToStep(0)">
            <el-icon><ArrowLeft /></el-icon> 上一步
          </el-button>
          <el-button type="primary" :disabled="selectedTables.length === 0" @click="goToStep(2)">
            下一步 (已选 {{ selectedTables.length }} 表) <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Step 3: 确认导入 -->
    <div v-if="step === 2" class="step-content">
      <div class="confirm-section">
        <h3>确认导入</h3>
        <p class="confirm-hint">以下数据表将被导入为数据模型，可后续生成 Kflower 模板</p>

        <div class="confirm-tables">
          <el-card v-for="t in selectedTables" :key="t.name" shadow="never" class="confirm-card">
            <div class="confirm-card-header">
              <span class="cc-name">{{ t.name }}</span>
              <el-tag size="small">{{ t.row_count }} 行</el-tag>
              <el-tag v-if="t.comment" size="small" type="info">{{ t.comment }}</el-tag>
            </div>
          </el-card>
        </div>

        <div class="step-actions">
          <el-button @click="goToStep(1)">
            <el-icon><ArrowLeft /></el-icon> 上一步
          </el-button>
          <el-button type="primary" @click="doImport" :loading="importing">
            <el-icon><Upload /></el-icon> 确认导入 ({{ selectedTables.length }} 个表)
          </el-button>
        </div>
      </div>
    </div>

    <!-- 表结构预览对话框 -->
    <el-dialog v-model="showSchemaDialog" :title="'表结构: ' + previewTableName" width="640px">
      <div v-loading="loadingSchema">
        <el-table :data="schemaColumns" size="small" style="width:100%">
          <el-table-column prop="name" label="字段名" width="140">
            <template #default="{ row }">
              <span style="font-family:monospace">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="db_type" label="类型" width="120" />
          <el-table-column prop="is_primary_key" label="主键" width="60" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.is_primary_key" color="var(--el-color-danger)"><Star /></el-icon>
            </template>
          </el-table-column>
          <el-table-column prop="nullable" label="可空" width="60" align="center">
            <template #default="{ row }">
              {{ row.nullable ? '✓' : '✗' }}
            </template>
          </el-table-column>
          <el-table-column prop="ui_type" label="UI控件" width="100" />
          <el-table-column prop="title" label="显示名" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, ArrowRight, Plus, Search, Upload, Star
} from '@element-plus/icons-vue'
import { dataModelAPI } from '../../common/api'

const router = useRouter()

const step = ref(0)

// Step 1: 连接
const connections = ref<any[]>([])
const selectedConnId = ref<number | null>(null)
const showNewConnForm = ref(false)
const testingNew = ref(false)
const savingNew = ref(false)
const newConnForm = ref({
  name: '', db_type: 'mysql', host: '', port: 3306,
  database: '', username: '', password: '',
})

// Step 2: 表列表
const loadingTables = ref(false)
const externalTables = ref<any[]>([])
const selectedTables = ref<any[]>([])
const tableSearch = ref('')

const filteredTables = computed(() => {
  if (!tableSearch.value) return externalTables.value
  const kw = tableSearch.value.toLowerCase()
  return externalTables.value.filter(t =>
    t.name.toLowerCase().includes(kw) || (t.comment || '').toLowerCase().includes(kw)
  )
})

// Step 3: 导入
const importing = ref(false)

// Schema预览
const showSchemaDialog = ref(false)
const previewTableName = ref('')
const schemaColumns = ref<any[]>([])
const loadingSchema = ref(false)

// 加载连接列表
async function loadConnections() {
  try {
    const res = await dataModelAPI.listConnections()
    if (res?.success) {
      connections.value = res?.data || []
    }
  } catch { /* ignore */ }
}

function selectConnection(c: any) {
  selectedConnId.value = c.id
}

// 新建连接
async function testNewConn() {
  testingNew.value = true
  try {
    const res = await dataModelAPI.createConnection(newConnForm.value)
    if (res?.success) {
      const connId = res?.data?.id
      if (connId) {
        const testRes = await dataModelAPI.testConnection(connId)
        if (testRes?.success) {
          ElMessage.success('连接测试成功')
        } else {
          ElMessage.warning('连接失败: ' + (testRes?.message || ''))
        }
      }
    }
  } catch (e: any) {
    ElMessage.error('测试失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    testingNew.value = false
  }
}

async function saveNewConn() {
  if (!newConnForm.value.name || !newConnForm.value.db_type) {
    ElMessage.warning('请填写必要信息')
    return
  }
  savingNew.value = true
  try {
    const res = await dataModelAPI.createConnection(newConnForm.value)
    if (res?.success) {
      ElMessage.success('连接保存成功')
      const connId = res?.data?.id
      await loadConnections()
      if (connId) {
        selectedConnId.value = connId
      }
      showNewConnForm.value = false
      newConnForm.value = {
        name: '', db_type: 'mysql', host: '', port: 3306,
        database: '', username: '', password: '',
      }
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    savingNew.value = false
  }
}

// 步骤切换
async function goToStep(s: number) {
  if (s === 1 && selectedConnId.value && step.value === 0) {
    // 加载外部表列表
    loadingTables.value = true
    try {
      const res = await dataModelAPI.listExternalTables(selectedConnId.value)
      if (res?.success) {
        externalTables.value = res?.data || []
      }
    } catch (e: any) {
      ElMessage.error('获取表列表失败: ' + (e.response?.data?.detail || e.message))
      return
    } finally {
      loadingTables.value = false
    }
  }
  step.value = s
}

function onTableSelection(rows: any[]) {
  selectedTables.value = rows
}

// Schema预览
async function previewSchema(tableName: string) {
  if (!selectedConnId.value) return
  previewTableName.value = tableName
  showSchemaDialog.value = true
  loadingSchema.value = true
  try {
    const res = await dataModelAPI.getExternalTableSchema(selectedConnId.value, tableName)
    if (res?.success) {
      schemaColumns.value = res?.data?.columns || []
    }
  } catch (e: any) {
    ElMessage.error('获取表结构失败')
  } finally {
    loadingSchema.value = false
  }
}

// 确认导入
async function doImport() {
  if (!selectedConnId.value || selectedTables.value.length === 0) return
  importing.value = true
  try {
    const tableNames = selectedTables.value.map(t => t.name)
    const res = await dataModelAPI.importExternalTables(selectedConnId.value, tableNames)
    if (res?.success) {
      ElMessage.success(`成功导入 ${selectedTables.value.length} 个数据表`)
      router.push('/data-modeling')
    } else {
      ElMessage.error(res?.message || '导入失败')
    }
  } catch (e: any) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

// 辅助
function getDbTypeColor(type: string) {
  const map: Record<string, string> = { mysql: '#00758f', postgresql: '#336791', sqlite: '#044a64' }
  return map[type] || '#409eff'
}

onMounted(() => {
  loadConnections()
})
</script>

<style scoped>
.data-model-import-page {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
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
  color: var(--el-text-color-primary);
}

.steps-bar {
  max-width: 600px;
  margin: 0 auto 24px;
}

.step-content {
  max-width: 900px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  color: var(--el-text-color-primary);
}

/* 连接列表 */
.conn-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.conn-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--el-bg-color);
  border: 2px solid var(--el-border-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.conn-card:hover {
  border-color: var(--el-color-primary-light-5);
}

.conn-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.conn-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}

.conn-info {
  flex: 1;
  min-width: 0;
}

.conn-name {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.conn-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.new-conn-card {
  margin-bottom: 16px;
}

.new-conn-card h4 {
  margin: 0 0 16px;
  color: var(--el-text-color-primary);
}

/* 表格区域 */
.tables-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-light);
}

/* 确认区域 */
.confirm-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 24px;
  border: 1px solid var(--el-border-color-light);
}

.confirm-hint {
  color: var(--el-text-color-secondary);
  margin-bottom: 16px;
}

.confirm-tables {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.confirm-card {
  margin: 0;
}

.confirm-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cc-name {
  font-family: monospace;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 步骤操作 */
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
