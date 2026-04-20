<template>
  <div class="agent-orchestrator-page">
    <div class="page-header">
      <h2>🎭 智能体编排器</h2>
      <p class="subtitle">可视化智能体工作流编排，支持条件分支、并行执行、结果聚合等复杂场景</p>
    </div>

    <el-row :gutter="20" class="orchestrator-stats">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon workflow"><el-icon><SetUp /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.workflowCount }}</div>
            <div class="stat-label">工作流数量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon running"><el-icon><VideoPlay /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.runningCount }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon success"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.successRate }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon time"><el-icon><Clock /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avgExecutionTime }}s</div>
            <div class="stat-label">平均执行时间</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="16">
        <el-card class="workflow-canvas-card">
          <template #header>
            <div class="card-header">
              <span>🎨 工作流设计器</span>
              <div class="canvas-actions">
                <el-button type="primary" size="small" @click="createWorkflow">新建工作流</el-button>
                <el-button size="small" @click="saveWorkflow">保存</el-button>
                <el-button size="small" @click="exportWorkflow">导出</el-button>
              </div>
            </div>
          </template>
          
          <div class="canvas-placeholder">
            <div class="mock-canvas">
              <div class="canvas-title">可视化工作流设计器</div>
              <div class="canvas-hint">拖拽智能体和工具到画布，连接节点创建工作流</div>
              <div class="mock-nodes">
                <div class="mock-node start">开始</div>
                <div class="mock-arrow">→</div>
                <div class="mock-node agent">数据分析智能体</div>
                <div class="mock-arrow">→</div>
                <div class="mock-node tool">SQL查询</div>
                <div class="mock-arrow">→</div>
                <div class="mock-node agent">报告生成智能体</div>
                <div class="mock-arrow">→</div>
                <div class="mock-node end">结束</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="components-panel">
          <template #header>
            <div class="card-header">
              <span>🧩 组件库</span>
            </div>
          </template>
          
          <el-tabs v-model="activeComponentTab" class="component-tabs">
            <el-tab-pane label="智能体" name="agents">
              <div class="components-list">
                <div
                  v-for="agent in availableAgents"
                  :key="agent.id"
                  class="component-item"
                  draggable="true"
                  @dragstart="onDragStart($event, 'agent', agent)"
                >
                  <div class="component-icon agent"><el-icon><User /></el-icon></div>
                  <div class="component-info">
                    <div class="component-name">{{ agent.name }}</div>
                    <div class="component-desc">{{ agent.description }}</div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="工具" name="tools">
              <div class="components-list">
                <div
                  v-for="tool in availableTools"
                  :key="tool.id"
                  class="component-item"
                  draggable="true"
                  @dragstart="onDragStart($event, 'tool', tool)"
                >
                  <div class="component-icon tool"><el-icon><Tools /></el-icon></div>
                  <div class="component-info">
                    <div class="component-name">{{ tool.name }}</div>
                    <div class="component-desc">{{ tool.description }}</div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="控制" name="controls">
              <div class="components-list">
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'control', {type: 'condition'})">
                  <div class="component-icon control"><el-icon><Share /></el-icon></div>
                  <div class="component-info">
                    <div class="component-name">条件分支</div>
                    <div class="component-desc">根据条件执行不同分支</div>
                  </div>
                </div>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'control', {type: 'parallel'})">
                  <div class="component-icon control"><el-icon><Sort /></el-icon></div>
                  <div class="component-info">
                    <div class="component-name">并行执行</div>
                    <div class="component-desc">同时执行多个任务</div>
                  </div>
                </div>
                <div class="component-item" draggable="true" @dragstart="onDragStart($event, 'control', {type: 'loop'})">
                  <div class="component-icon control"><el-icon><Refresh /></el-icon></div>
                  <div class="component-info">
                    <div class="component-name">循环</div>
                    <div class="component-desc">重复执行直到条件满足</div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="12">
        <el-card class="workflow-list-card">
          <template #header>
            <div class="card-header">
              <span>📋 工作流列表</span>
              <el-button type="primary" size="small" @click="createWorkflow">新建</el-button>
            </div>
          </template>
          
          <el-table :data="workflows" style="width:100%">
            <el-table-column prop="name" label="名称" width="180">
              <template #default="{ row }">
                <div class="workflow-name">
                  <el-icon><Collection /></el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '已发布' ? 'success' : row.status === '草稿' ? 'info' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="version" label="版本" width="80" />
            <el-table-column prop="lastRun" label="最后运行" width="150" />
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="editWorkflow(row)">编辑</el-button>
                <el-button type="success" size="small" link @click="runWorkflow(row)">运行</el-button>
                <el-button type="info" size="small" link @click="viewLogs(row)">日志</el-button>
                <el-button type="danger" size="small" link @click="deleteWorkflow(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="execution-log-card">
          <template #header>
            <div class="card-header">
              <span>📝 最近执行记录</span>
              <el-button size="small" @click="refreshLogs">刷新</el-button>
            </div>
          </template>
          
          <el-timeline>
            <el-timeline-item
              v-for="log in executionLogs"
              :key="log.id"
              :timestamp="log.time"
              :type="log.status === '成功' ? 'success' : log.status === '失败' ? 'danger' : 'primary'"
              placement="top"
            >
              <div class="log-item">
                <div class="log-header">
                  <span class="log-workflow">{{ log.workflow }}</span>
                  <el-tag size="small">{{ log.duration }}s</el-tag>
                </div>
                <div class="log-desc">{{ log.description }}</div>
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
          <div class="progress-label">工作流引擎基础</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">可视化设计器</div>
          <el-progress :percentage="75" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">条件分支与循环</div>
          <el-progress :percentage="65" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">并行执行与同步</div>
          <el-progress :percentage="50" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工作流版本管理</div>
          <el-progress :percentage="40" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { SetUp, VideoPlay, CircleCheck, Clock, User, Tools, Share, Sort, Refresh, Collection } from '@element-plus/icons-vue'

const stats = ref({
  workflowCount: 24,
  runningCount: 3,
  successRate: 92.5,
  avgExecutionTime: 45.2,
})

const activeComponentTab = ref('agents')

const availableAgents = ref([
  { id: 1, name: '模板设计智能体', description: '自动生成业务模板' },
  { id: 2, name: '流程审批智能体', description: '智能审批流程处理' },
  { id: 3, name: '数据分析智能体', description: '数据洞察与分析' },
  { id: 4, name: '知识库助手', description: '知识检索与问答' },
  { id: 5, name: '查询智能体', description: '自然语言数据查询' },
])

const availableTools = ref([
  { id: 1, name: 'SQL查询', description: '数据库查询工具' },
  { id: 2, name: 'API调用', description: '外部API调用工具' },
  { id: 3, name: '文件处理', description: '文件读写工具' },
  { id: 4, name: '邮件发送', description: '电子邮件发送工具' },
  { id: 5, name: '数据转换', description: '数据格式转换工具' },
])

const workflows = ref([
  { id: 1, name: '月度报告生成', status: '已发布', version: 'v1.2', lastRun: '2026-04-20 10:30' },
  { id: 2, name: '数据质量检查', status: '已发布', version: 'v1.0', lastRun: '2026-04-20 09:15' },
  { id: 3, name: '用户反馈分析', status: '草稿', version: 'v0.8', lastRun: '2026-04-19 16:45' },
  { id: 4, name: '自动化巡检', status: '已发布', version: 'v1.1', lastRun: '2026-04-19 14:20' },
  { id: 5, name: '知识库更新', status: '测试中', version: 'v0.9', lastRun: '2026-04-18 11:10' },
])

const executionLogs = ref([
  { id: 1, time: '2026-04-20 10:30:15', workflow: '月度报告生成', status: '成功', duration: 32.5, description: '成功生成月度销售报告' },
  { id: 2, time: '2026-04-20 09:15:42', workflow: '数据质量检查', status: '成功', duration: 18.2, description: '检查完成，发现3个问题' },
  { id: 3, time: '2026-04-19 16:45:33', workflow: '用户反馈分析', status: '失败', duration: 45.8, description: 'API调用超时' },
  { id: 4, time: '2026-04-19 14:20:18', workflow: '自动化巡检', status: '成功', duration: 56.3, description: '系统巡检完成，一切正常' },
  { id: 5, time: '2026-04-18 11:10:05', workflow: '知识库更新', status: '成功', duration: 120.5, description: '知识库文档索引更新完成' },
])

function onDragStart(event: DragEvent, type: string, data: any) {
  event.dataTransfer?.setData('application/json', JSON.stringify({ type, data }))
  ElMessage.info(`开始拖拽 ${type}: ${data.name || data.type}`)
}

function createWorkflow() {
  ElMessage.info('创建新工作流')
}

function saveWorkflow() {
  ElMessage.success('工作流已保存')
}

function exportWorkflow() {
  ElMessage.info('导出工作流')
}

function editWorkflow(row: any) {
  ElMessage.info(`编辑工作流: ${row.name}`)
}

function runWorkflow(row: any) {
  ElMessage.info(`运行工作流: ${row.name}`)
}

function viewLogs(row: any) {
  ElMessage.info(`查看工作流日志: ${row.name}`)
}

function deleteWorkflow(row: any) {
  ElMessage.info(`删除工作流: ${row.name}`)
}

function refreshLogs() {
  ElMessage.info('刷新执行记录')
}
</script>

<style scoped>
.agent-orchestrator-page {
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

.orchestrator-stats {
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

.stat-icon.workflow { background: #ecf5ff; color: #409EFF; }
.stat-icon.running { background: #f0f9eb; color: #67C23A; }
.stat-icon.success { background: #fdf6ec; color: #E6A23C; }
.stat-icon.time { background: #fef0f0; color: #F56C6C; }

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

.canvas-actions {
  display: flex;
  gap: 8px;
}

.workflow-canvas-card, .components-panel, .workflow-list-card, .execution-log-card {
  height: 100%;
}

.canvas-placeholder {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 4px;
}

.mock-canvas {
  text-align: center;
}

.canvas-title {
  font-size: 18px;
  color: #606266;
  margin-bottom: 12px;
}

.canvas-hint {
  font-size: 14px;
  color: #909399;
  margin-bottom: 24px;
}

.mock-nodes {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.mock-node {
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 500;
  color: white;
}

.mock-node.start { background: #67C23A; }
.mock-node.agent { background: #409EFF; }
.mock-node.tool { background: #E6A23C; }
.mock-node.end { background: #909399; }

.mock-arrow {
  color: #909399;
  font-size: 20px;
}

.component-tabs {
  height: 300px;
}

.components-list {
  max-height: 250px;
  overflow-y: auto;
}

.component-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  cursor: move;
  transition: background 0.2s;
}

.component-item:hover {
  background: #f5f7fa;
}

.component-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.component-icon.agent { background: #ecf5ff; color: #409EFF; }
.component-icon.tool { background: #fdf6ec; color: #E6A23C; }
.component-icon.control { background: #f0f9eb; color: #67C23A; }

.component-info {
  flex: 1;
}

.component-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.component-desc {
  font-size: 12px;
  color: #909399;
}

.workflow-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-item {
  padding: 8px 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.log-workflow {
  font-weight: 500;
}

.log-desc {
  font-size: 13px;
  color: #606266;
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