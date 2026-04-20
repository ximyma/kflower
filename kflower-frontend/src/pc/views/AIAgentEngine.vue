<template>
  <div class="ai-agent-engine-page">
    <div class="page-header">
      <h2>🧠 AI智能体引擎</h2>
      <p class="subtitle">多智能体协作框架，支持任务规划、工具调用、记忆管理、协同执行</p>
    </div>

    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon agent"><el-icon><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">12</div>
            <div class="stat-label">智能体数量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon task"><el-icon><List /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">156</div>
            <div class="stat-label">任务执行</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon tool"><el-icon><Tools /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">8</div>
            <div class="stat-label">可用工具</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon memory"><el-icon><Collection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">2.4K</div>
            <div class="stat-label">记忆条目</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="12">
        <el-card class="module-card">
          <template #header>
            <div class="card-header">
              <span>🤖 智能体列表</span>
              <el-button type="primary" size="small" @click="createAgent">创建智能体</el-button>
            </div>
          </template>
          
          <el-table :data="agents" style="width:100%">
            <el-table-column prop="name" label="名称" width="150">
              <template #default="{ row }">
                <div class="agent-name">
                  <el-icon><Avatar /></el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '在线' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tasks" label="任务数" width="80" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="manageAgent(row)">管理</el-button>
                <el-button type="info" size="small" link @click="viewLogs(row)">日志</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="module-card">
          <template #header>
            <div class="card-header">
              <span>🛠️ 工具库</span>
              <el-button type="primary" size="small" @click="addTool">添加工具</el-button>
            </div>
          </template>
          
          <el-table :data="tools" style="width:100%">
            <el-table-column prop="name" label="工具名称" width="180" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" size="small" @change="toggleTool(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="module-card" style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>📋 最近任务</span>
            </div>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="task in recentTasks"
              :key="task.id"
              :timestamp="task.time"
              :type="task.status === '成功' ? 'success' : task.status === '失败' ? 'danger' : 'primary'"
            >
              <div class="task-item">
                <span class="task-title">{{ task.title }}</span>
                <el-tag size="small">{{ task.agent }}</el-tag>
              </div>
            </el-timeline-item>
          </el-timeline>
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
          <div class="progress-label">智能体基础框架</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">任务规划器</div>
          <el-progress :percentage="85" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具调用系统</div>
          <el-progress :percentage="70" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">多智能体协作</div>
          <el-progress :percentage="45" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">记忆管理系统</div>
          <el-progress :percentage="60" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, List, Tools, Collection, Avatar } from '@element-plus/icons-vue'

const agents = ref([
  { id: 1, name: '模板设计智能体', type: '专业', status: '在线', tasks: 42 },
  { id: 2, name: '流程审批智能体', type: '专业', status: '在线', tasks: 28 },
  { id: 3, name: '数据分析智能体', type: '专业', status: '在线', tasks: 35 },
  { id: 4, name: '知识库助手', type: '通用', status: '离线', tasks: 12 },
  { id: 5, name: '查询智能体', type: '通用', status: '在线', tasks: 51 },
])

const tools = ref([
  { id: 1, name: 'SQL查询', description: '执行数据库查询操作', enabled: true },
  { id: 2, name: 'API调用', description: '调用外部REST API', enabled: true },
  { id: 3, name: '文件读取', description: '读取本地文件内容', enabled: true },
  { id: 4, name: '数据转换', description: 'JSON/CSV格式转换', enabled: false },
  { id: 5, name: '邮件发送', description: '发送电子邮件', enabled: true },
  { id: 6, name: '代码执行', description: '执行Python代码片段', enabled: false },
])

const recentTasks = ref([
  { id: 1, time: '2026-04-20 13:30', title: '生成月度报告模板', agent: '模板设计智能体', status: '成功' },
  { id: 2, time: '2026-04-20 13:15', title: '审批采购流程', agent: '流程审批智能体', status: '成功' },
  { id: 3, time: '2026-04-20 13:00', title: '分析销售趋势', agent: '数据分析智能体', status: '成功' },
  { id: 4, time: '2026-04-20 12:45', title: '知识库文档索引', agent: '知识库助手', status: '失败' },
  { id: 5, time: '2026-04-20 12:30', title: '用户查询处理', agent: '查询智能体', status: '成功' },
])

function createAgent() {
  ElMessage.info('创建智能体功能开发中')
}

function manageAgent(row: any) {
  ElMessage.info(`管理智能体: ${row.name}`)
}

function viewLogs(row: any) {
  ElMessage.info(`查看 ${row.name} 的日志`)
}

function addTool() {
  ElMessage.info('添加工具功能开发中')
}

function toggleTool(row: any) {
  ElMessage.success(`${row.name} ${row.enabled ? '已启用' : '已禁用'}`)
}
</script>

<style scoped>
.ai-agent-engine-page {
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

.overview-cards {
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

.stat-icon.agent { background: #ecf5ff; color: #409EFF; }
.stat-icon.task { background: #f0f9eb; color: #67C23A; }
.stat-icon.tool { background: #fdf6ec; color: #E6A23C; }
.stat-icon.memory { background: #fef0f0; color: #F56C6C; }

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

.module-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-title {
  font-size: 14px;
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