<template>
  <div class="data-integration-page">
    <div class="page-header">
      <h2>🔗 数据集成</h2>
      <p class="subtitle">多源数据连接与集成，支持数据库、API、文件、消息队列等多种数据源</p>
    </div>

    <el-row :gutter="20" class="integration-stats">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon connections"><el-icon><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.connections }}</div>
            <div class="stat-label">数据连接</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon sources"><el-icon><DataBoard /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.dataSources }}</div>
            <div class="stat-label">数据源类型</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon sync"><el-icon><Refresh /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.syncTasks }}</div>
            <div class="stat-label">同步任务</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon health"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.healthRate }}%</div>
            <div class="stat-label">健康度</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="12">
        <el-card class="connections-card">
          <template #header>
            <div class="card-header">
              <span>🔌 数据连接管理</span>
              <el-button type="primary" size="small" @click="addConnection">新建连接</el-button>
            </div>
          </template>
          
          <el-table :data="connections" style="width:100%">
            <el-table-column prop="name" label="连接名称" width="150">
              <template #default="{ row }">
                <div class="connection-name">
                  <el-icon :color="getSourceColor(row.type)"><component :is="getSourceIcon(row.type)" /></el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="getSourceTag(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <div class="status-cell">
                  <el-tag :type="row.status === '正常' ? 'success' : row.status === '异常' ? 'danger' : 'warning'" size="small">{{ row.status }}</el-tag>
                  <el-icon v-if="row.status === '正常'" color="#67C23A"><CircleCheck /></el-icon>
                  <el-icon v-if="row.status === '异常'" color="#F56C6C"><CircleClose /></el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="lastSync" label="最后同步" width="120" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="testConnection(row)">测试</el-button>
                <el-button type="info" size="small" link @click="editConnection(row)">编辑</el-button>
                <el-button type="danger" size="small" link @click="deleteConnection(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="sync-tasks-card">
          <template #header>
            <div class="card-header">
              <span>🔄 同步任务</span>
              <el-button type="primary" size="small" @click="createSyncTask">创建任务</el-button>
            </div>
          </template>
          
          <el-table :data="syncTasks" style="width:100%">
            <el-table-column prop="name" label="任务名称" width="150" />
            <el-table-column prop="source" label="数据源" width="120" />
            <el-table-column prop="target" label="目标" width="120" />
            <el-table-column prop="schedule" label="调度" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.schedule }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="lastRun" label="最后运行" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '运行中' ? 'success' : row.status === '失败' ? 'danger' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="runTask(row)">运行</el-button>
                <el-button type="info" size="small" link @click="viewLogs(row)">日志</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="16">
        <el-card class="data-mapping-card">
          <template #header>
            <div class="card-header">
              <span>🗺️ 数据映射管理</span>
              <el-button type="primary" size="small" @click="createMapping">创建映射</el-button>
            </div>
          </template>
          
          <div class="mapping-editor">
            <div class="editor-placeholder">
              <div class="editor-title">数据映射编辑器</div>
              <div class="editor-hint">可视化字段映射关系，支持数据类型转换、格式处理、条件映射</div>
              <div class="mock-mapping">
                <div class="mapping-source">
                  <div class="mapping-title">源数据 (MySQL)</div>
                  <div class="mapping-fields">
                    <div class="field-item">user_id (int)</div>
                    <div class="field-item">user_name (varchar)</div>
                    <div class="field-item">email (varchar)</div>
                    <div class="field-item">created_at (datetime)</div>
                  </div>
                </div>
                <div class="mapping-arrow">→</div>
                <div class="mapping-transform">
                  <div class="transform-title">转换规则</div>
                  <div class="transform-rules">
                    <div class="rule-item">类型转换</div>
                    <div class="rule-item">格式处理</div>
                    <div class="rule-item">数据清洗</div>
                  </div>
                </div>
                <div class="mapping-arrow">→</div>
                <div class="mapping-target">
                  <div class="mapping-title">目标数据 (PostgreSQL)</div>
                  <div class="mapping-fields">
                    <div class="field-item">id (bigint)</div>
                    <div class="field-item">username (text)</div>
                    <div class="field-item">email_address (text)</div>
                    <div class="field-item">create_time (timestamptz)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="data-quality-card">
          <template #header>
            <div class="card-header">
              <span>📊 数据质量监控</span>
            </div>
          </template>
          
          <div class="quality-metrics">
            <div class="metric-item">
              <div class="metric-label">完整性</div>
              <el-progress :percentage="qualityMetrics.completeness" status="success" />
            </div>
            <div class="metric-item">
              <div class="metric-label">准确性</div>
              <el-progress :percentage="qualityMetrics.accuracy" status="success" />
            </div>
            <div class="metric-item">
              <div class="metric-label">一致性</div>
              <el-progress :percentage="qualityMetrics.consistency" status="warning" />
            </div>
            <div class="metric-item">
              <div class="metric-label">及时性</div>
              <el-progress :percentage="qualityMetrics.timeliness" status="success" />
            </div>
          </div>
          
          <el-divider />
          
          <div class="quality-issues">
            <div class="issues-title">数据问题</div>
            <div class="issue-item" v-for="issue in qualityIssues" :key="issue.id">
              <div class="issue-info">
                <div class="issue-name">{{ issue.name }}</div>
                <div class="issue-count">{{ issue.count }} 个</div>
              </div>
              <div class="issue-action">
                <el-button type="primary" size="small" @click="fixIssue(issue)">修复</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="development-info" style="margin-top:24px">
      <template #header>
        <div class="card-header">
          <span>🚀 开发进展</span>
        </div>
      </template>
      <div class="progress-section">
        <div class="progress-item">
          <div class="progress-label">多源数据连接器</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">数据同步引擎</div>
          <el-progress :percentage="85" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">可视化映射工具</div>
          <el-progress :percentage="70" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">数据质量监控</div>
          <el-progress :percentage="60" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">实时数据流</div>
          <el-progress :percentage="40" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, DataBoard, Refresh, CircleCheck, CircleClose, SetUp, Document, Folder, Cloudy, Service } from '@element-plus/icons-vue'

const stats = ref({
  connections: 8,
  dataSources: 6,
  syncTasks: 12,
  healthRate: 94.5,
})

const connections = ref([
  { id: 1, name: '主数据库', type: 'MySQL', status: '正常', lastSync: '2026-04-20 10:30' },
  { id: 2, name: '用户API', type: 'REST API', status: '正常', lastSync: '2026-04-20 10:15' },
  { id: 3, name: '文件存储', type: '文件系统', status: '正常', lastSync: '2026-04-20 09:45' },
  { id: 4, name: '消息队列', type: 'RabbitMQ', status: '异常', lastSync: '2026-04-19 16:20' },
  { id: 5, name: '数据仓库', type: 'ClickHouse', status: '正常', lastSync: '2026-04-19 14:30' },
  { id: 6, name: '外部服务', type: 'Web Service', status: '警告', lastSync: '2026-04-18 11:45' },
])

const syncTasks = ref([
  { id: 1, name: '用户数据同步', source: 'MySQL', target: '数据仓库', schedule: '每小时', lastRun: '2026-04-20 10:00', status: '运行中' },
  { id: 2, name: '日志收集', source: '文件系统', target: 'Elasticsearch', schedule: '实时', lastRun: '2026-04-20 09:45', status: '正常' },
  { id: 3, name: 'API数据拉取', source: '外部API', target: 'MySQL', schedule: '每天', lastRun: '2026-04-20 08:30', status: '失败' },
  { id: 4, name: '数据备份', source: '主数据库', target: '备份存储', schedule: '每周', lastRun: '2026-04-19 23:00', status: '正常' },
  { id: 5, name: '实时监控', source: '消息队列', target: '监控系统', schedule: '实时', lastRun: '2026-04-19 22:15', status: '警告' },
])

const qualityMetrics = ref({
  completeness: 96,
  accuracy: 94,
  consistency: 82,
  timeliness: 98,
})

const qualityIssues = ref([
  { id: 1, name: '缺失字段', count: 12 },
  { id: 2, name: '格式错误', count: 8 },
  { id: 3, name: '重复数据', count: 23 },
  { id: 4, name: '数据过期', count: 5 },
])

function getSourceIcon(type: string) {
  const map: any = {
    'MySQL': SetUp,
    'REST API': Connection,
    '文件系统': Document,
    'RabbitMQ': Cloudy,
    'ClickHouse': DataBoard,
    'Web Service': Service,
    'PostgreSQL': SetUp,
    'MongoDB': Folder,
  }
  return map[type] || SetUp
}

function getSourceColor(type: string) {
  const map: any = {
    'MySQL': '#409EFF',
    'REST API': '#67C23A',
    '文件系统': '#E6A23C',
    'RabbitMQ': '#F56C6C',
    'ClickHouse': '#909399',
    'Web Service': '#8E44AD',
  }
  return map[type] || '#409EFF'
}

function getSourceTag(type: string) {
  const map: any = {
    'MySQL': 'primary',
    'REST API': 'success',
    '文件系统': 'warning',
    'RabbitMQ': 'danger',
    'ClickHouse': 'info',
    'Web Service': 'info',
  }
  return map[type] || 'info'
}

function addConnection() {
  ElMessage.info('添加数据连接')
}

function testConnection(row: any) {
  ElMessage.info(`测试连接: ${row.name}`)
}

function editConnection(row: any) {
  ElMessage.info(`编辑连接: ${row.name}`)
}

function deleteConnection(row: any) {
  ElMessage.info(`删除连接: ${row.name}`)
}

function createSyncTask() {
  ElMessage.info('创建同步任务')
}

function runTask(row: any) {
  ElMessage.info(`运行任务: ${row.name}`)
}

function viewLogs(row: any) {
  ElMessage.info(`查看任务日志: ${row.name}`)
}

function createMapping() {
  ElMessage.info('创建数据映射')
}

function fixIssue(issue: any) {
  ElMessage.info(`修复问题: ${issue.name}`)
}
</script>

<style scoped>
.data-integration-page {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 8px 0 0;
  color: #606266;
  font-size: 14px;
}

.integration-stats {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.connections { background: #ecf5ff; color: #409EFF; }
.stat-icon.sources { background: #f0f9eb; color: #67C23A; }
.stat-icon.sync { background: #fdf6ec; color: #E6A23C; }
.stat-icon.health { background: #fef0f0; color: #F56C6C; }

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.connections-card, .sync-tasks-card, .data-mapping-card, .data-quality-card {
  height: 100%;
}

.connection-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mapping-editor {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 4px;
}

.editor-placeholder {
  text-align: center;
}

.editor-title {
  font-size: 18px;
  color: #606266;
  margin-bottom: 12px;
}

.editor-hint {
  font-size: 14px;
  color: #909399;
  margin-bottom: 24px;
}

.mock-mapping {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.mapping-source, .mapping-transform, .mapping-target {
  padding: 20px;
  border-radius: 8px;
  background: white;
  border: 2px solid #ebeef5;
  min-width: 180px;
}

.mapping-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.mapping-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-item {
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.transform-rules {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-item {
  padding: 6px 12px;
  background: #f0f9eb;
  border-radius: 4px;
  font-size: 13px;
  color: #67C23A;
}

.mapping-arrow {
  font-size: 24px;
  color: #909399;
}

.quality-metrics {
  padding: 8px 0;
}

.metric-item {
  margin-bottom: 16px;
}

.metric-item:last-child {
  margin-bottom: 0;
}

.metric-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.quality-issues {
  padding: 8px 0;
}

.issues-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.issue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.issue-item:last-child {
  border-bottom: none;
}

.issue-info {
  flex: 1;
}

.issue-name {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.issue-count {
  font-size: 12px;
  color: #909399;
}

.issue-action {
  flex-shrink: 0;
}

.development-info {
  border-radius: 8px;
}

.progress-section {
  padding: 8px 0;
}

.progress-item {
  margin-bottom: 20px;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}
</style>