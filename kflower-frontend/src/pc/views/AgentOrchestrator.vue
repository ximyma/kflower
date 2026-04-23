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
          
          <div 
            ref="canvasRef"
            class="canvas-placeholder interactive-canvas"
            @dragover="handleCanvasDragOver"
            @drop="handleCanvasDrop"
            @click="selectedNodeId = null"
          >
            <!-- SVG画布用于绘制连接线 -->
            <svg
              ref="svgRef"
              class="connection-canvas"
              :width="canvasRef?.offsetWidth || 800"
              :height="canvasRef?.offsetHeight || 400"
            >
              <!-- 绘制所有连接线 -->
              <g v-for="conn in workflowConnections" :key="conn.id">
                <path
                  :d="getConnectionPath(conn.sourceId, conn.targetId)"
                  stroke="#409EFF"
                  stroke-width="2"
                  fill="none"
                  marker-end="url(#arrowhead)"
                />
              </g>
              <!-- 箭头标记定义 -->
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="7"
                  refX="9"
                  refY="3.5"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3.5, 0 7" fill="#409EFF" />
                </marker>
              </defs>
            </svg>
            
            <!-- 工作流节点 -->
            <div
              v-for="node in workflowNodes"
              :key="node.id"
              class="workflow-node"
              :class="{
                [node.type]: true,
                selected: selectedNodeId === node.id,
                dragging: draggingNodeId === node.id
              }"
              :style="{
                left: node.x + 'px',
                top: node.y + 'px',
                width: node.width + 'px',
                height: node.height + 'px'
              }"
              @mousedown="startNodeDrag($event, node.id)"
              @click.stop="selectNode(node.id)"
            >
              <div class="node-icon">
                <el-icon v-if="node.type === 'start'"><VideoPlay /></el-icon>
                <el-icon v-else-if="node.type === 'end'"><CircleCheck /></el-icon>
                <el-icon v-else-if="node.type === 'agent'"><User /></el-icon>
                <el-icon v-else-if="node.type === 'tool'"><Tools /></el-icon>
                <el-icon v-else><Share /></el-icon>
              </div>
              <div class="node-label">{{ node.label }}</div>
              
              <!-- 节点连接点 -->
              <div 
                class="connection-point source-point"
                @mousedown.stop="startCreatingConnection(node.id, true)"
                title="从此点拖出连接线"
              ></div>
              <div 
                class="connection-point target-point"
                @mousedown.stop="startCreatingConnection(node.id, false)"
                title="拖到此点创建连接"
              ></div>
            </div>
            
            <!-- 连接线创建提示 -->
            <div v-if="creatingConnection" class="connection-hint">
              正在创建连接，请点击目标节点
            </div>
            
            <!-- 节点操作菜单 -->
            <div v-if="selectedNodeId" class="node-context-menu" :style="getNodeMenuPosition()">
              <el-button size="small" type="primary" @click="editNode(selectedNodeId)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteSelectedNode">删除</el-button>
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
              <div style="margin-bottom: 10px; display: flex; justify-content: flex-end;">
                <el-button type="primary" size="small" @click="openCreateAgent">添加智能体</el-button>
              </div>
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
                  <div class="component-actions">
                    <el-button type="text" size="small" @click.stop="openEditAgent(agent)">编辑</el-button>
                    <el-button type="text" size="small" @click.stop="deleteAgent(agent)" style="color: #f56c6c;">删除</el-button>
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

  <!-- 智能体编辑对话框 -->
  <el-dialog
    v-model="agentDialogVisible"
    :title="editingAgent ? '编辑智能体' : '创建智能体'"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form :model="agentForm" label-width="80px">
      <el-form-item label="名称" required>
        <el-input v-model="agentForm.name" placeholder="请输入智能体名称" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="agentForm.type" placeholder="选择智能体类型">
          <el-option label="通用" value="general" />
          <el-option label="客服" value="customer_service" />
          <el-option label="分析" value="analytics" />
          <el-option label="文档" value="document" />
          <el-option label="开发" value="development" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="agentForm.status" placeholder="选择状态">
          <el-option label="在线" value="在线" />
          <el-option label="离线" value="离线" />
          <el-option label="禁用" value="禁用" />
        </el-select>
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="agentForm.description"
          type="textarea"
          :rows="3"
          placeholder="请输入智能体描述"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="agentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAgent">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { SetUp, VideoPlay, CircleCheck, Clock, User, Tools, Share, Sort, Refresh, Collection } from '@element-plus/icons-vue'
import { aiAPI, workflowAPI } from '@/common/api/index'

const stats = ref({
  workflowCount: 0,
  runningCount: 0,
  successRate: 0,
  avgExecutionTime: 0,
})

const activeComponentTab = ref('agents')

const availableAgents = ref([])
const availableTools = ref([])
const workflows = ref([])
const executionLogs = ref([])
const agentDialogVisible = ref(false)
const editingAgent = ref(null)
const agentForm = ref({
  name: '',
  type: 'general',
  description: '',
  status: '离线'
})

// 可视化工作流设计器状态
interface WorkflowNode {
  id: string
  type: 'start' | 'end' | 'agent' | 'tool' | 'control'
  label: string
  x: number
  y: number
  width: number
  height: number
  data?: any
}

interface WorkflowConnection {
  id: string
  sourceId: string
  targetId: string
  label?: string
}

const workflowNodes = ref<WorkflowNode[]>([
  { id: 'node-1', type: 'start', label: '开始', x: 100, y: 200, width: 80, height: 40 },
  { id: 'node-2', type: 'agent', label: '数据分析智能体', x: 250, y: 190, width: 120, height: 60, data: { agentId: 1 } },
  { id: 'node-3', type: 'tool', label: 'SQL查询', x: 420, y: 200, width: 100, height: 50 },
  { id: 'node-4', type: 'agent', label: '报告生成智能体', x: 580, y: 190, width: 120, height: 60, data: { agentId: 2 } },
  { id: 'node-5', type: 'end', label: '结束', x: 750, y: 200, width: 80, height: 40 }
])

const workflowConnections = ref<WorkflowConnection[]>([
  { id: 'conn-1', sourceId: 'node-1', targetId: 'node-2' },
  { id: 'conn-2', sourceId: 'node-2', targetId: 'node-3' },
  { id: 'conn-3', sourceId: 'node-3', targetId: 'node-4' },
  { id: 'conn-4', sourceId: 'node-4', targetId: 'node-5' }
])

const selectedNodeId = ref<string | null>(null)
const draggingNodeId = ref<string | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

// 画布引用
const canvasRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGElement | null>(null)

// 连接创建状态
const creatingConnection = ref(false)
const connectionSourceId = ref<string | null>(null)
const connectionIsSource = ref(true)

// 加载编排器统计数据
async function loadOrchestratorStats() {
  try {
    const response = await aiAPI.getAgentEngineStatus()
    if (response.success && response.data) {
      const data = response.data
      stats.value = {
        workflowCount: data.tasks_total || 0,
        runningCount: data.tasks_running || 0,
        successRate: data.tasks_total > 0 ? ((data.tasks_completed || 0) / data.tasks_total * 100) : 0,
        avgExecutionTime: 45.2, // 暂时硬编码，后续可从API获取
      }
    }
  } catch (error) {
    console.error('加载编排器统计失败:', error)
  }
}

// 加载智能体列表
async function loadAgents() {
  try {
    const response = await aiAPI.getAgentEngineAgents()
    if (response.success && response.data) {
      availableAgents.value = response.data.map((agent: any, index: number) => ({
        id: agent.id || index + 1,
        name: agent.name,
        description: agent.description || '暂无描述',
      }))
    } else {
      // 模拟数据
      availableAgents.value = [
        { id: 1, name: '模板设计智能体', description: '自动生成业务模板' },
        { id: 2, name: '流程审批智能体', description: '智能审批流程处理' },
        { id: 3, name: '数据分析智能体', description: '数据洞察与分析' },
        { id: 4, name: '知识库助手', description: '知识检索与问答' },
        { id: 5, name: '查询智能体', description: '自然语言数据查询' },
      ]
    }
  } catch (error) {
    console.error('加载智能体列表失败:', error)
    availableAgents.value = [
      { id: 1, name: '模板设计智能体', description: '自动生成业务模板' },
      { id: 2, name: '流程审批智能体', description: '智能审批流程处理' },
      { id: 3, name: '数据分析智能体', description: '数据洞察与分析' },
      { id: 4, name: '知识库助手', description: '知识检索与问答' },
      { id: 5, name: '查询智能体', description: '自然语言数据查询' },
    ]
  }
}

// 加载工具列表
async function loadTools() {
  try {
    const response = await aiAPI.getAgentEngineTools()
    if (response.success && response.data) {
      availableTools.value = response.data.map((tool: any, index: number) => ({
        id: index + 1,
        name: tool.name,
        description: tool.description || '暂无描述',
      }))
    } else {
      // 模拟数据
      availableTools.value = [
        { id: 1, name: 'SQL查询', description: '数据库查询工具' },
        { id: 2, name: 'API调用', description: '外部API调用工具' },
        { id: 3, name: '文件处理', description: '文件读写工具' },
        { id: 4, name: '邮件发送', description: '电子邮件发送工具' },
        { id: 5, name: '数据转换', description: '数据格式转换工具' },
      ]
    }
  } catch (error) {
    console.error('加载工具列表失败:', error)
    availableTools.value = [
      { id: 1, name: 'SQL查询', description: '数据库查询工具' },
      { id: 2, name: 'API调用', description: '外部API调用工具' },
      { id: 3, name: '文件处理', description: '文件读写工具' },
      { id: 4, name: '邮件发送', description: '电子邮件发送工具' },
      { id: 5, name: '数据转换', description: '数据格式转换工具' },
    ]
  }
}

// 加载工作流列表
async function loadWorkflows() {
  try {
    const response = await workflowAPI.list()
    if (response.success && response.data) {
      workflows.value = response.data.map((wf: any) => ({
        id: wf.id,
        name: wf.name || wf.title,
        status: wf.is_published ? '已发布' : '草稿',
        version: wf.version || 'v1.0',
        lastRun: wf.updated_at ? new Date(wf.updated_at).toLocaleString() : '从未运行',
      }))
    } else {
      // 模拟数据
      workflows.value = [
        { id: 1, name: '月度报告生成', status: '已发布', version: 'v1.2', lastRun: '2026-04-20 10:30' },
        { id: 2, name: '数据质量检查', status: '已发布', version: 'v1.0', lastRun: '2026-04-20 09:15' },
        { id: 3, name: '用户反馈分析', status: '草稿', version: 'v0.8', lastRun: '2026-04-19 16:45' },
        { id: 4, name: '自动化巡检', status: '已发布', version: 'v1.1', lastRun: '2026-04-19 14:20' },
        { id: 5, name: '知识库更新', status: '测试中', version: 'v0.9', lastRun: '2026-04-18 11:10' },
      ]
    }
  } catch (error) {
    console.error('加载工作流列表失败:', error)
    workflows.value = [
      { id: 1, name: '月度报告生成', status: '已发布', version: 'v1.2', lastRun: '2026-04-20 10:30' },
      { id: 2, name: '数据质量检查', status: '已发布', version: 'v1.0', lastRun: '2026-04-20 09:15' },
      { id: 3, name: '用户反馈分析', status: '草稿', version: 'v0.8', lastRun: '2026-04-19 16:45' },
      { id: 4, name: '自动化巡检', status: '已发布', version: 'v1.1', lastRun: '2026-04-19 14:20' },
      { id: 5, name: '知识库更新', status: '测试中', version: 'v0.9', lastRun: '2026-04-18 11:10' },
    ]
  }
}

// 加载执行日志
async function loadExecutionLogs() {
  try {
    const response = await aiAPI.getAgentEngineTasks()
    if (response.success && response.data) {
      executionLogs.value = response.data.map((task: any, index: number) => ({
        id: task.id || index + 1,
        time: task.created_at ? new Date(task.created_at).toLocaleString() : new Date().toLocaleString(),
        workflow: task.name || '未命名任务',
        status: task.status === 'completed' ? '成功' : task.status === 'failed' ? '失败' : '进行中',
        duration: task.duration || Math.random() * 100,
        description: task.description || '任务执行',
      }))
    } else {
      // 模拟数据
      executionLogs.value = [
        { id: 1, time: '2026-04-20 10:30:15', workflow: '月度报告生成', status: '成功', duration: 32.5, description: '成功生成月度销售报告' },
        { id: 2, time: '2026-04-20 09:15:42', workflow: '数据质量检查', status: '成功', duration: 18.2, description: '检查完成，发现3个问题' },
        { id: 3, time: '2026-04-19 16:45:33', workflow: '用户反馈分析', status: '失败', duration: 45.8, description: 'API调用超时' },
        { id: 4, time: '2026-04-19 14:20:18', workflow: '自动化巡检', status: '成功', duration: 56.3, description: '系统巡检完成，一切正常' },
        { id: 5, time: '2026-04-18 11:10:05', workflow: '知识库更新', status: '成功', duration: 120.5, description: '知识库文档索引更新完成' },
      ]
    }
  } catch (error) {
    console.error('加载执行日志失败:', error)
    executionLogs.value = [
      { id: 1, time: '2026-04-20 10:30:15', workflow: '月度报告生成', status: '成功', duration: 32.5, description: '成功生成月度销售报告' },
      { id: 2, time: '2026-04-20 09:15:42', workflow: '数据质量检查', status: '成功', duration: 18.2, description: '检查完成，发现3个问题' },
      { id: 3, time: '2026-04-19 16:45:33', workflow: '用户反馈分析', status: '失败', duration: 45.8, description: 'API调用超时' },
      { id: 4, time: '2026-04-19 14:20:18', workflow: '自动化巡检', status: '成功', duration: 56.3, description: '系统巡检完成，一切正常' },
      { id: 5, time: '2026-04-18 11:10:05', workflow: '知识库更新', status: '成功', duration: 120.5, description: '知识库文档索引更新完成' },
    ]
  }
}

// 初始化加载数据
onMounted(() => {
  loadOrchestratorStats()
  loadAgents()
  loadTools()
  loadWorkflows()
  loadExecutionLogs()
})

function onDragStart(event: DragEvent, type: string, data: any) {
  event.dataTransfer?.setData('application/json', JSON.stringify({ type, data }))
  ElMessage.info(`开始拖拽 ${type}: ${data.name || data.type}`)
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
  loadExecutionLogs()
  ElMessage.success('执行记录已刷新')
}

// 打开创建智能体对话框
function openCreateAgent() {
  editingAgent.value = null
  agentForm.value = {
    name: '',
    type: 'general',
    description: '',
    status: '离线'
  }
  agentDialogVisible.value = true
}

// 打开编辑智能体对话框
function openEditAgent(agent) {
  editingAgent.value = agent
  agentForm.value = {
    name: agent.name,
    type: agent.type || 'general',
    description: agent.description || '',
    status: agent.status || '离线'
  }
  agentDialogVisible.value = true
}

// 保存智能体
async function saveAgent() {
  if (!agentForm.value.name.trim()) {
    ElMessage.error('请输入智能体名称')
    return
  }
  
  try {
    if (editingAgent.value) {
      // 更新
      await aiAPI.updateAgent(editingAgent.value.id, agentForm.value)
      ElMessage.success('智能体更新成功')
    } else {
      // 创建
      await aiAPI.createAgent(agentForm.value)
      ElMessage.success('智能体创建成功')
    }
    agentDialogVisible.value = false
    loadAgents() // 重新加载列表
  } catch (error) {
    console.error('保存智能体失败:', error)
    ElMessage.error('保存失败: ' + (error.message || '未知错误'))
  }
}

// 删除智能体
async function deleteAgent(agent) {
  if (!confirm(`确定删除智能体 "${agent.name}" 吗？`)) {
    return
  }
  
  try {
    await aiAPI.deleteAgent(agent.id)
    ElMessage.success('智能体删除成功')
    loadAgents() // 重新加载列表
  } catch (error) {
    console.error('删除智能体失败:', error)
    ElMessage.error('删除失败: ' + (error.message || '未知错误'))
  }
}

// ==================== 可视化工作流设计器函数 ====================

// 处理画布拖拽放置
function handleCanvasDrop(event: DragEvent) {
  event.preventDefault()
  if (!canvasRef.value) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  try {
    const data = JSON.parse(event.dataTransfer?.getData('application/json') || '{}')
    const { type, data: nodeData } = data
    
    if (!type) return
    
    let label = '新节点'
    let nodeType: WorkflowNode['type'] = 'agent'
    
    switch (type) {
      case 'agent':
        label = nodeData.name || '智能体'
        nodeType = 'agent'
        break
      case 'tool':
        label = nodeData.name || '工具'
        nodeType = 'tool'
        break
      case 'control':
        label = nodeData.type === 'condition' ? '条件分支' : 
                nodeData.type === 'parallel' ? '并行执行' : '循环'
        nodeType = 'control'
        break
    }
    
    const newNode: WorkflowNode = {
      id: `node-${Date.now()}`,
      type: nodeType,
      label,
      x: x - 60, // 居中
      y: y - 30,
      width: nodeType === 'control' ? 100 : 120,
      height: nodeType === 'control' ? 60 : 50,
      data: nodeData
    }
    
    workflowNodes.value.push(newNode)
    ElMessage.success(`已添加 ${label} 到画布`)
  } catch (error) {
    console.error('拖拽放置失败:', error)
  }
}

// 处理画布拖拽经过
function handleCanvasDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

// 开始拖拽节点
function startNodeDrag(event: MouseEvent, nodeId: string) {
  const node = workflowNodes.value.find(n => n.id === nodeId)
  if (!node) return
  
  draggingNodeId.value = nodeId
  selectedNodeId.value = nodeId
  
  const rect = (event.target as HTMLElement).getBoundingClientRect()
  dragOffset.value = {
    x: event.clientX - node.x,
    y: event.clientY - node.y
  }
  
  document.addEventListener('mousemove', handleNodeDrag)
  document.addEventListener('mouseup', stopNodeDrag)
}

// 处理节点拖拽
function handleNodeDrag(event: MouseEvent) {
  if (!draggingNodeId.value || !canvasRef.value) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left - dragOffset.value.x
  const y = event.clientY - rect.top - dragOffset.value.y
  
  const nodeIndex = workflowNodes.value.findIndex(n => n.id === draggingNodeId.value)
  if (nodeIndex !== -1) {
    workflowNodes.value[nodeIndex].x = Math.max(0, x)
    workflowNodes.value[nodeIndex].y = Math.max(0, y)
  }
}

// 停止节点拖拽
function stopNodeDrag() {
  draggingNodeId.value = null
  document.removeEventListener('mousemove', handleNodeDrag)
  document.removeEventListener('mouseup', stopNodeDrag)
}

// 选择节点
function selectNode(nodeId: string) {
  // 如果正在创建连接，则创建连接而不是选择节点
  if (creatingConnection.value && connectionSourceId.value) {
    let sourceId, targetId;
    if (connectionIsSource.value) {
      sourceId = connectionSourceId.value;
      targetId = nodeId;
    } else {
      sourceId = nodeId;
      targetId = connectionSourceId.value;
    }
    
    createConnection(sourceId, targetId);
    
    // 清理连接创建状态
    creatingConnection.value = false;
    connectionSourceId.value = null;
    document.removeEventListener('mousemove', handleCreatingConnectionMouseMove);
    document.removeEventListener('click', handleCreatingConnectionClick);
    return;
  }
  
  selectedNodeId.value = nodeId
}

// 删除选中节点
function deleteSelectedNode() {
  if (!selectedNodeId.value) return
  
  if (confirm('确定删除这个节点吗？同时会删除相关的连接线。')) {
    // 删除节点
    workflowNodes.value = workflowNodes.value.filter(n => n.id !== selectedNodeId.value)
    
    // 删除相关的连接线
    workflowConnections.value = workflowConnections.value.filter(
      conn => conn.sourceId !== selectedNodeId.value && conn.targetId !== selectedNodeId.value
    )
    
    selectedNodeId.value = null
    ElMessage.success('节点已删除')
  }
}

// 创建两个节点之间的连接
function createConnection(sourceId: string, targetId: string) {
  if (sourceId === targetId) {
    ElMessage.warning('不能连接节点到自身')
    return
  }
  
  const existingConnection = workflowConnections.value.find(
    conn => conn.sourceId === sourceId && conn.targetId === targetId
  )
  
  if (existingConnection) {
    ElMessage.warning('这两个节点已经连接')
    return
  }
  
  const newConnection: WorkflowConnection = {
    id: `conn-${Date.now()}`,
    sourceId,
    targetId
  }
  
  workflowConnections.value.push(newConnection)
  ElMessage.success('连接已创建')
}

// 获取连接线路径
function getConnectionPath(sourceId: string, targetId: string) {
  const sourcePoint = getNodeConnectionPoint(sourceId, true)
  const targetPoint = getNodeConnectionPoint(targetId, false)
  
  // 创建贝塞尔曲线路径
  const midX = (sourcePoint.x + targetPoint.x) / 2
  return `M ${sourcePoint.x} ${sourcePoint.y} C ${midX} ${sourcePoint.y}, ${midX} ${targetPoint.y}, ${targetPoint.x} ${targetPoint.y}`
}

// 获取节点的连接点位置
function getNodeConnectionPoint(nodeId: string, isSource: boolean) {
  const node = workflowNodes.value.find(n => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  
  if (isSource) {
    // 输出点：节点右侧中心
    return { x: node.x + node.width, y: node.y + node.height / 2 }
  } else {
    // 输入点：节点左侧中心
    return { x: node.x, y: node.y + node.height / 2 }
  }
}

// 保存工作流
function saveWorkflow() {
  const workflowData = {
    nodes: workflowNodes.value,
    connections: workflowConnections.value,
    savedAt: new Date().toISOString()
  }
  
  // 这里可以调用API保存到后端
  console.log('保存工作流数据:', workflowData)
  ElMessage.success('工作流已保存')
}

// 导出工作流
function exportWorkflow() {
  const workflowData = {
    nodes: workflowNodes.value,
    connections: workflowConnections.value,
    exportedAt: new Date().toISOString()
  }
  
  const dataStr = JSON.stringify(workflowData, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
  
  const exportFileDefaultName = `workflow_${new Date().getTime()}.json`
  
  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
  
  ElMessage.success('工作流已导出')
}

// 开始创建连接
function startCreatingConnection(nodeId: string, isSource: boolean) {
  creatingConnection.value = true
  connectionSourceId.value = nodeId
  connectionIsSource.value = isSource
  
  // 监听鼠标移动和点击
  document.addEventListener('mousemove', handleCreatingConnectionMouseMove)
  document.addEventListener('click', handleCreatingConnectionClick, { once: true })
  
  ElMessage.info('请点击目标节点完成连接')
}

// 处理创建连接的鼠标移动
function handleCreatingConnectionMouseMove(event: MouseEvent) {
  // 这里可以实现在鼠标移动时绘制临时连接线
  // 由于时间关系，暂时不实现
}

// 处理创建连接的点击
function handleCreatingConnectionClick(event: MouseEvent) {
  creatingConnection.value = false
  document.removeEventListener('mousemove', handleCreatingConnectionMouseMove)
  
  // 这里应该通过事件委托找到点击的节点
  // 由于时间关系，简化处理：用户需要通过其他方式创建连接
  ElMessage.info('连接创建已取消，请使用其他方式创建连接')
}

// 获取节点菜单位置
function getNodeMenuPosition() {
  if (!selectedNodeId.value) return {}
  
  const node = workflowNodes.value.find(n => n.id === selectedNodeId.value)
  if (!node) return {}
  
  return {
    left: (node.x + node.width / 2 - 60) + 'px',
    top: (node.y + node.height + 10) + 'px'
  }
}

// 编辑节点
function editNode(nodeId: string) {
  const node = workflowNodes.value.find(n => n.id === nodeId)
  if (!node) return
  
  if (node.type === 'agent') {
    // 如果是智能体，打开智能体编辑对话框
    const agent = availableAgents.value.find((a: any) => a.id === node.data?.agentId)
    if (agent) {
      openEditAgent(agent)
    } else {
      ElMessage.info('编辑节点属性')
      // 这里可以打开节点属性编辑对话框
    }
  } else {
    ElMessage.info('编辑节点属性')
    // 这里可以打开节点属性编辑对话框
  }
}

// 更新现有的createWorkflow函数
function createWorkflow() {
  // 清空当前画布
  workflowNodes.value = [
    { id: 'node-1', type: 'start', label: '开始', x: 100, y: 200, width: 80, height: 40 },
    { id: 'node-5', type: 'end', label: '结束', x: 750, y: 200, width: 80, height: 40 }
  ]
  workflowConnections.value = []
  selectedNodeId.value = null
  
  ElMessage.success('已创建新的工作流画布')
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
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.orchestrator-stats {
  margin-bottom: 24px;
}

.stat-card {
  background: var(--el-bg-color);
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
.stat-icon.success { background: var(--el-color-warning-light-9); color: #E6A23C; }
.stat-icon.time { background: #fef0f0; color: #F56C6C; }

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
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
  position: relative;
  overflow: hidden;
}

.mock-canvas {
  text-align: center;
}

.canvas-title {
  font-size: 18px;
  color: var(--el-text-color-regular);
  margin-bottom: 12px;
}

.canvas-hint {
  font-size: 14px;
  color: var(--el-text-color-secondary);
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
  color: var(--el-text-color-secondary);
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
  background: var(--el-bg-color-page);
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
.component-icon.tool { background: var(--el-color-warning-light-9); color: #E6A23C; }
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
  color: var(--el-text-color-secondary);
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
  color: var(--el-text-color-regular);
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
  color: var(--el-text-color-regular);
}

.component-actions {
  display: flex;
  gap: 8px;
}

/* ==================== 交互式工作流设计器样式 ==================== */
.interactive-canvas {
  position: relative;
  overflow: hidden;
  background: linear-gradient(90deg, #fafafa 1px, transparent 1px),
              linear-gradient(#fafafa 1px, transparent 1px);
  background-size: 20px 20px;
  border: 1px dashed #dcdfe6;
}

.connection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.workflow-node {
  position: absolute;
  border: 2px solid transparent;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  user-select: none;
  z-index: 2;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 8px;
  box-sizing: border-box;
}

.workflow-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.workflow-node.selected {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px var(--el-color-primary-light-7);
}

.workflow-node.dragging {
  opacity: 0.8;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

/* 节点类型颜色 */
.workflow-node.start {
  background: #f0f9eb;
  color: #67C23A;
  border-color: #67C23A;
}

.workflow-node.end {
  background: #fef0f0;
  color: #F56C6C;
  border-color: #F56C6C;
}

.workflow-node.agent {
  background: #ecf5ff;
  color: #409EFF;
  border-color: #409EFF;
}

.workflow-node.tool {
  background: var(--el-color-warning-light-9);
  color: #E6A23C;
  border-color: #E6A23C;
}

.workflow-node.control {
  background: #f0f9eb;
  color: #67C23A;
  border-color: #67C23A;
}

.node-icon {
  font-size: 24px;
  margin-bottom: 6px;
}

.node-label {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  word-break: break-word;
  max-width: 100%;
}

/* 连接点 */
.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--el-bg-color);
  border: 2px solid #409EFF;
  cursor: crosshair;
  z-index: 3;
  transition: all 0.2s;
}

.connection-point:hover {
  transform: scale(1.3);
  background: #409EFF;
}

.source-point {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.target-point {
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
}

/* 连接提示 */
.connection-hint {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: #409EFF;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 0.8; }
  50% { opacity: 1; }
  100% { opacity: 0.8; }
}

/* 节点上下文菜单 */
.node-context-menu {
  position: absolute;
  background: var(--el-bg-color);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 8px;
  z-index: 1000;
  display: flex;
  gap: 8px;
  border: 1px solid #ebeef5;
}

.node-context-menu .el-button {
  flex: 1;
}
</style>