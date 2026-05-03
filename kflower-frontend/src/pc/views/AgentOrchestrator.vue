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
              <span>🎨 工作流设计器 <span v-if="currentEditingWorkflow" style="color: #67C23A; font-size: 14px;">- {{ currentEditingWorkflow.name }}</span></span>
              <div class="canvas-actions">
                <el-button type="primary" size="small" @click="createWorkflow">新建工作流</el-button>
                <el-button size="small" type="success" @click="saveWorkflow">保存</el-button>
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
                    <el-button type="text" size="small" @click.stop="openChatWithAgent(agent)">聊天</el-button>
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
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="designWorkflow(row)">设计</el-button>
                <el-button type="warning" size="small" link @click="editWorkflow(row)">编辑</el-button>
                <el-button type="success" size="small" link @click="runWorkflow(row)">运行</el-button>
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

  <!-- 工作流创建/编辑对话框 -->
  <el-dialog
    v-model="workflowDialogVisible"
    :title="editingWorkflowId ? '编辑工作流' : '创建工作流'"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form :model="{}" label-width="90px">
      <el-form-item label="工作流名称" required>
        <el-input 
          v-model="currentWorkflowName" 
          placeholder="请输入工作流名称，如：月度报告生成"
          @keyup.enter="confirmCreateWorkflow"
        />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="currentWorkflowDescription"
          type="textarea"
          :rows="3"
          placeholder="请输入工作流描述（可选）"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="workflowDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="confirmCreateWorkflow">
        {{ editingWorkflowId ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>

  <!-- 智能体聊天对话框 -->
  <el-dialog
    v-model="chatDialogVisible"
    :title="currentChatAgent ? '与 ' + currentChatAgent.name + ' 对话' : '智能体聊天'"
    width="700px"
    :close-on-click-modal="false"
  >
    <div class="chat-container">
      <div class="chat-model-selector">
        <el-select
          v-model="selectedModel"
          placeholder="选择AI模型"
          size="small"
          style="width: 200px;"
          popper-class="model-select-dropdown"
          :teleported="true"
        >
          <el-option
            v-for="model in availableModels"
            :key="model.id"
            :label="model.name"
            :value="model.id"
          />
        </el-select>
        <span class="model-tip" v-if="!selectedModel">请选择AI模型进行对话</span>
      </div>
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="chatMessages.length === 0" class="chat-empty">
          <el-icon size="48" color="#909399"><ChatDotRound /></el-icon>
          <p>开始和 {{ currentChatAgent?.name }} 对话吧</p>
          <p class="chat-tip">可以询问关于 {{ currentChatAgent?.description || '相关业务' }} 的问题</p>
        </div>
        <div
          v-for="(msg, index) in chatMessages"
          :key="index"
          class="chat-message"
          :class="msg.role"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" size="20"><User /></el-icon>
            <el-icon v-else size="20"><MagicStick /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text">{{ msg.content }}</div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
        <div v-if="chatLoading" class="chat-message assistant">
          <div class="message-avatar">
            <el-icon size="20"><MagicStick /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text loading">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input-area">
        <el-input
          v-model="chatInput"
          placeholder="输入消息..."
          @keyup.enter="sendChatMessage"
          :disabled="chatLoading || !selectedModel"
        >
          <template #append>
            <el-button @click="sendChatMessage" :disabled="chatLoading || !chatInput.trim() || !selectedModel">
              <el-icon><Promotion /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
  </el-dialog>

  <!-- 智能体编辑对话框 -->
  <el-dialog
    v-model="agentDialogVisible"
    :title="editingAgent ? '编辑智能体' : '创建智能体'"
    width="700px"
    :close-on-click-modal="false"
  >
    <el-tabs v-model="agentTabActive" class="agent-config-tabs">
      <el-tab-pane label="基本信息" name="basic">
        <el-form :model="agentForm" label-width="90px" style="margin-top: 16px">
          <el-form-item label="名称" required>
            <el-input v-model="agentForm.name" placeholder="请输入智能体名称" />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="agentForm.type" placeholder="选择智能体类型" style="width: 100%">
              <el-option label="通用" value="general" />
              <el-option label="客服" value="customer_service" />
              <el-option label="分析" value="analytics" />
              <el-option label="文档" value="document" />
              <el-option label="开发" value="development" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="agentForm.status" placeholder="选择状态" style="width: 100%">
              <el-option label="在线" value="在线" />
              <el-option label="离线" value="离线" />
              <el-option label="禁用" value="禁用" />
            </el-select>
          </el-form-item>
          <el-form-item label="作用域">
            <el-select v-model="agentForm.scope" placeholder="选择作用域" style="width: 100%">
              <el-option label="全局（所有应用可用）" value="global" />
              <el-option label="应用专用" value="app" />
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
      </el-tab-pane>
      
      <el-tab-pane label="模块绑定" name="bindings">
        <div class="binding-section" style="margin-top: 16px">
          <!-- 模板绑定 -->
          <div class="binding-item">
            <div class="binding-header">
              <el-icon><Document /></el-icon>
              <span>绑定模板</span>
              <el-tag size="small" type="info">可选</el-tag>
            </div>
            <div class="binding-desc">绑定后可处理指定模板的表单数据</div>
            <el-select
              v-model="agentForm.template_ids"
              multiple
              placeholder="选择绑定的模板"
              style="width: 100%"
              clearable
            >
              <el-option
                v-for="tpl in availableTemplates"
                :key="tpl.id"
                :label="tpl.name"
                :value="tpl.id"
              />
            </el-select>
          </div>
          
          <!-- 知识库绑定 -->
          <div class="binding-item">
            <div class="binding-header">
              <el-icon><Reading /></el-icon>
              <span>绑定知识库</span>
              <el-tag size="small" type="info">可选</el-tag>
            </div>
            <div class="binding-desc">绑定后智能体可检索知识库内容回答问题</div>
            <el-select
              v-model="agentForm.knowledge_base_ids"
              multiple
              placeholder="选择绑定的知识库"
              style="width: 100%"
              clearable
            >
              <el-option
                v-for="kb in availableKnowledgeBases"
                :key="kb.id"
                :label="kb.name"
                :value="kb.id"
              />
            </el-select>
          </div>
          
          <!-- 工作流绑定 -->
          <div class="binding-item">
            <div class="binding-header">
              <el-icon><Connection /></el-icon>
              <span>绑定工作流</span>
              <el-tag size="small" type="info">可选</el-tag>
            </div>
            <div class="binding-desc">绑定后智能体可触发和管理指定工作流</div>
            <el-select
              v-model="agentForm.workflow_ids"
              multiple
              placeholder="选择绑定的工作流"
              style="width: 100%"
              clearable
            >
              <el-option
                v-for="wf in availableWorkflows"
                :key="wf.id"
                :label="wf.name"
                :value="wf.id"
              />
            </el-select>
          </div>
          
          <!-- 插件绑定 -->
          <div class="binding-item">
            <div class="binding-header">
              <el-icon><Grid /></el-icon>
              <span>绑定插件</span>
              <el-tag size="small" type="info">可选</el-tag>
            </div>
            <div class="binding-desc">绑定后智能体可调用指定插件扩展功能</div>
            <el-select
              v-model="agentForm.plugin_ids"
              multiple
              placeholder="选择绑定的插件"
              style="width: 100%"
              clearable
            >
              <el-option
                v-for="plugin in availablePlugins"
                :key="plugin.id"
                :label="plugin.name"
                :value="plugin.id"
              />
            </el-select>
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="系统配置" name="config">
        <div style="margin-top: 16px">
          <el-form-item label="系统提示词">
            <div class="system-prompt-tip">定义智能体的角色、能力范围和行为规则</div>
            <div class="prompt-actions">
              <el-button-group>
                <el-button size="small" @click="insertExamplePrompt" :disabled="generatingPrompt">
                  <el-icon><Document /></el-icon> 插入示例
                </el-button>
                <el-button size="small" type="primary" @click="generatePromptWithAI" :loading="generatingPrompt">
                  <el-icon><MagicStick /></el-icon> AI 生成提示词
                </el-button>
              </el-button-group>
              <el-dropdown @command="handleExampleSelect" trigger="click" style="margin-left: 8px;">
                <el-button size="small">
                  快捷模板 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="customer">客服助手</el-dropdown-item>
                    <el-dropdown-item command="doc">文档助手</el-dropdown-item>
                    <el-dropdown-item command="data">数据分析助手</el-dropdown-item>
                    <el-dropdown-item command="code">代码助手</el-dropdown-item>
                    <el-dropdown-item command="hr">HR助手</el-dropdown-item>
                    <el-dropdown-item command="finance">财务助手</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <el-input
              v-model="agentForm.system_prompt"
              type="textarea"
              :rows="10"
              placeholder="你是一个专业的XXX助手，可以帮助用户完成XXX任务。请注意：
1. 保持专业和礼貌
2. 如果不确定，请如实说明
3. 优先使用绑定的知识库内容回答问题"
              :disabled="generatingPrompt"
            />
            <div class="prompt-hint" v-if="generatingPrompt">
              <el-icon class="is-loading"><Loading /></el-icon> 正在使用 AI 生成提示词，请稍候...
            </div>
          </el-form-item>
          
          <el-form-item label="可见应用">
            <div class="system-prompt-tip">设置智能体在哪些应用中可见（留空表示所有应用）</div>
            <el-select
              v-model="agentForm.visible_apps"
              multiple
              placeholder="选择可见的应用"
              style="width: 100%"
              clearable
              filterable
            >
              <el-option
                v-for="app in availableApps"
                :key="app.id"
                :label="app.name"
                :value="app.id"
              />
            </el-select>
          </el-form-item>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="agentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAgent" :loading="savingAgent">保存</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { SetUp, VideoPlay, CircleCheck, Clock, User, Tools, Share, Sort, Refresh, Collection, Document, Reading, Connection, Grid, ChatDotRound, MagicStick, Promotion, ArrowDown, Loading } from '@element-plus/icons-vue'
import { aiAPI, workflowAPI, templateAPI } from '@/common/api/index'
import appAPI from '@/common/api/myApps'

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
const savingAgent = ref(false)
const agentTabActive = ref('basic')

// 新增：模块绑定选项列表
const availableTemplates = ref<any[]>([])
const availableKnowledgeBases = ref<any[]>([])
const availableWorkflows = ref<any[]>([])
const availablePlugins = ref<any[]>([])
const availableApps = ref<any[]>([])

// 智能体聊天对话框
const chatDialogVisible = ref(false)
const currentChatAgent = ref<any>(null)
const chatMessages = ref<Array<{role: string, content: string, time: string}>>([])
const chatInput = ref('')
const chatLoading = ref(false)

// 模型选择
const availableModels = ref<any[]>([])
const selectedModel = ref<string | null>(null)

// 提示词生成
const generatingPrompt = ref(false)

// 示例提示词模板
const promptTemplates = {
  customer: `你是一个专业的客户服务助手，名为"XX助手"。

## 你的职责
- 热情、耐心地解答客户的咨询问题
- 快速准确地提供产品/服务相关信息
- 积极倾听客户需求，提供个性化建议
- 妥善处理客户投诉和售后问题

## 行为准则
1. 保持专业、友好、礼貌的服务态度
2. 回答要准确、简洁、有条理
3. 遇到无法解决的问题时，及时转接相关人员
4. 保护客户隐私，不泄露敏感信息
5. 定期学习产品知识，提升专业能力

## 常用回复模板
- 问候：您好！我是您的专属客服助手，很高兴为您服务。
- 感谢：感谢您的信任，我会尽快为您处理。
- 结束：请问还有其他可以帮到您的吗？`,

  doc: `你是一个专业的文档助手，名为"XX助手"。

## 你的职责
- 帮助用户撰写各类文档（报告、方案、总结等）
- 检查文档格式和内容的规范性
- 提供文档模板和写作建议
- 优化文档结构和表达

## 行为准则
1. 语言表达要准确、流畅、专业
2. 注重文档的逻辑性和条理性
3. 根据不同场景调整写作风格
4. 主动提出改进建议
5. 严格保密文档内容

## 文档类型
- 工作报告、周报、月报
- 项目方案、实施计划
- 会议纪要、商务函件
- 产品手册、操作指南`,

  data: `你是一个专业的数据分析助手，名为"XX助手"。

## 你的职责
- 解读数据，发现规律和趋势
- 生成数据分析报告和可视化建议
- 回答数据相关问题
- 提供业务洞察和建议

## 分析维度
1. 描述性分析：发生了什么
2. 诊断性分析：为什么发生
3. 预测性分析：将要发生什么
4. 规范性分析：应该怎么做

## 注意事项
- 数据说话，用事实支撑结论
- 图表配合，增强可读性
- 深入浅出，复杂问题简单化
- 注意数据的时效性和局限性`,

  code: `你是一个专业的代码助手，名为"XX助手"。

## 你的职责
- 帮助编写、调试和优化代码
- 解释代码逻辑和实现原理
- 提供技术方案和最佳实践
- Code Review 和质量把控

## 技术栈
- 前端：Vue.js, React, TypeScript
- 后端：Python(FastAPI), Node.js, Java
- 数据库：MySQL, PostgreSQL, Redis
- DevOps：Docker, Git, CI/CD

## 行为准则
1. 代码要规范、可读、可维护
2. 遵循 SOLID 原则和设计模式
3. 注意安全性和性能优化
4. 写好注释和文档
5. 注重测试覆盖

## 输出格式
- 代码片段：标注语言和用途
- 问题分析：原因 + 解决方案
- 技术方案：优缺点对比`,

  hr: `你是一个专业的HR助手，名为"XX助手"。

## 你的职责
- 解答员工关于人事政策的咨询
- 协助招聘流程和面试安排
- 办理入职、离职、转正等手续
- 提供绩效考核和培训发展建议

## 业务范围
1. 招聘管理：职位发布、简历筛选、面试安排
2. 员工关系：入职转正、晋升调动、离职结算
3. 薪酬福利：工资核算、社保公积金、绩效考核
4. 培训发展：培训计划、技能提升、职业规划

## 行为准则
- 政策解读要准确、清晰
- 流程说明要详细、可操作
- 保护员工隐私和信息安全
- 提供人性化、专业化的服务`,

  finance: `你是一个专业的财务助手，名为"XX助手"。

## 你的职责
- 解答财务相关的专业问题
- 提供财务分析和报表解读
- 协助预算编制和成本控制
- 解读财税政策和法规

## 业务领域
1. 会计核算：凭证编制、账务处理、报表生成
2. 财务管理：预算编制、资金管理、成本分析
3. 税务筹划：纳税申报、税务筹划、优惠政策
4. 审计合规：内控建设、合规检查、风险防范

## 注意事项
- 遵循会计准则和税法规定
- 数据准确，计算严谨
- 提供专业的分析和合理的建议
- 注重合规性和风险控制`
}

const agentForm = ref({
  name: '',
  type: 'general',
  description: '',
  status: '离线',
  scope: 'global',
  // 模块绑定
  template_ids: [] as number[],
  knowledge_base_ids: [] as number[],
  workflow_ids: [] as number[],
  plugin_ids: [] as number[],
  // 系统配置
  system_prompt: '',
  visible_apps: [] as number[],
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

// 工作流创建对话框
const workflowDialogVisible = ref(false)
const currentWorkflowName = ref('')
const currentWorkflowDescription = ref('')  // 新增：保存描述
const editingWorkflowId = ref<number | null>(null)
const currentEditingWorkflow = ref<any>(null)  // 当前正在设计的工作流

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
      availableAgents.value = response.data.map((agent: any) => ({
        id: agent.id,
        name: agent.name,
        description: agent.description || '暂无描述',
        type: agent.type || 'general',
        status: agent.status || '离线',
        scope: agent.scope || 'global',
        template_ids: agent.template_ids || [],
        knowledge_base_ids: agent.knowledge_base_ids || [],
        workflow_ids: agent.workflow_ids || [],
        plugin_ids: agent.plugin_ids || [],
        system_prompt: agent.system_prompt || '',
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
  // 加载模块绑定选项
  loadModuleOptions()
})

// 加载模块绑定选项（模板、知识库、工作流、插件、应用）
async function loadModuleOptions() {
  // 加载模板列表
  try {
    const tplRes = await templateAPI.list({ limit: 100 })
    availableTemplates.value = Array.isArray(tplRes) ? tplRes : (tplRes.data || [])
  } catch (e) {
    console.error('加载模板列表失败', e)
  }
  
  // 加载知识库列表 - 修正 API 路径
  try {
    const kbRes = await fetch('/api/v1/knowledge/bases', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())
    availableKnowledgeBases.value = Array.isArray(kbRes) ? kbRes : (kbRes.data || [])
  } catch (e) {
    console.error('加载知识库列表失败', e)
  }
  
  // 加载工作流列表
  try {
    const wfRes = await workflowAPI.list()
    availableWorkflows.value = Array.isArray(wfRes) ? wfRes : (wfRes.data || [])
  } catch (e) {
    console.error('加载工作流列表失败', e)
  }
  
  // 加载应用列表
  try {
    const appRes = await appAPI.list()
    availableApps.value = Array.isArray(appRes) ? appRes : (appRes.data || [])
  } catch (e) {
    console.error('加载应用列表失败', e)
  }
  
  // 加载插件列表（系统插件）- 修正 API 路径
  try {
    const pluginRes = await fetch('/api/v1/plugins/', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())
    availablePlugins.value = pluginRes.success ? pluginRes.data : (Array.isArray(pluginRes) ? pluginRes : (pluginRes.data || []))
  } catch (e) {
    console.error('加载插件列表失败', e)
  }
}

function onDragStart(event: DragEvent, type: string, data: any) {
  event.dataTransfer?.setData('application/json', JSON.stringify({ type, data }))
  ElMessage.info(`开始拖拽 ${type}: ${data.name || data.type}`)
}

function runWorkflow(row: any) {
  ElMessage.info(`运行工作流: ${row.name}`)
}

function viewLogs(row: any) {
  ElMessage.info(`查看工作流日志: ${row.name}`)
}

function deleteWorkflow(row: any) {
  const idx = workflows.value.findIndex(w => w.id === row.id)
  if (idx !== -1) {
    workflows.value.splice(idx, 1)
    ElMessage.success(`已删除工作流「${row.name}」`)
  }
}

// 打开智能体聊天对话框
async function openChatWithAgent(agent: any) {
  currentChatAgent.value = agent
  chatMessages.value = []
  chatInput.value = ''
  chatDialogVisible.value = true
  // 加载模型列表
  await loadAvailableModels()
}

// 发送聊天消息
async function sendChatMessage() {
  if (!chatInput.value.trim() || chatLoading.value || !selectedModel.value) return
  
  const userMessage = chatInput.value.trim()
  chatInput.value = ''
  
  // 添加用户消息
  chatMessages.value.push({
    role: 'user',
    content: userMessage,
    time: new Date().toLocaleTimeString()
  })
  
  chatLoading.value = true
  
  try {
    // 调用真实的 AI 模型 API
    const response = await fetch('/api/v1/ai/agent-engine/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        agent_id: currentChatAgent.value?.id,
        message: userMessage,
        model: selectedModel.value,
        history: chatMessages.value.slice(0, -1).map(m => ({
          role: m.role,
          content: m.content
        }))
      })
    })
    
    const data = await response.json()
    
    if (data.success && data.response) {
      chatMessages.value.push({
        role: 'assistant',
        content: data.response,
        time: new Date().toLocaleTimeString()
      })
    } else if (data.detail) {
      // API 返回错误信息
      chatMessages.value.push({
        role: 'assistant',
        content: '抱歉，' + (data.detail || 'AI 服务暂时不可用，请检查 AI 数字底座配置'),
        time: new Date().toLocaleTimeString()
      })
    } else {
      chatMessages.value.push({
        role: 'assistant',
        content: '抱歉，AI 服务暂时不可用，请检查 AI 数字底座配置',
        time: new Date().toLocaleTimeString()
      })
    }
  } catch (error: any) {
    console.error('发送消息失败:', error)
    chatMessages.value.push({
      role: 'assistant',
      content: '抱歉，AI 服务暂时不可用，请检查 AI 数字底座配置。错误信息: ' + (error.message || '网络错误'),
      time: new Date().toLocaleTimeString()
    })
  } finally {
    chatLoading.value = false
  }
}

// 加载可用模型列表
async function loadAvailableModels() {
  try {
    // 从 AI 数字底座获取模型列表 - 修正 API 路径
    const res = await fetch('/api/v1/ai/digital-base/models/available', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    const data = await res.json()
    if (data.success && data.data) {
      // 兼容不同格式的模型数据
      const models = data.data
      if (Array.isArray(models)) {
        availableModels.value = models.map((m: any) => ({
          id: m.id || m.model || m.name,
          name: m.name || m.model || m.id,
          provider: m.provider || ''
        }))
      } else if (typeof models === 'object') {
        // 如果是按 provider 分组的格式
        const allModels: any[] = []
        for (const [provider, modelList] of Object.entries(models)) {
          if (Array.isArray(modelList)) {
            for (const m of modelList) {
              allModels.push({
                id: m.id || m.model || m.name,
                name: `${provider}: ${m.name || m.model || m.id}`,
                provider: provider
              })
            }
          }
        }
        availableModels.value = allModels
      }
      // 默认选择第一个模型
      if (availableModels.value.length > 0 && !selectedModel.value) {
        selectedModel.value = availableModels.value[0].id
      }
    } else if (data.data) {
      // 尝试直接使用 data.data
      const models = data.data
      if (Array.isArray(models)) {
        availableModels.value = models.map((m: any) => ({
          id: m.id || m.model || m.name,
          name: m.name || m.model || m.id,
          provider: m.provider || ''
        }))
      }
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    // 使用默认模型列表
    availableModels.value = [
      { id: 'qwen-turbo', name: '通义千问 Turbo', provider: 'aliyun' },
      { id: 'qwen-plus', name: '通义千问 Plus', provider: 'aliyun' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'openai' },
      { id: 'gpt-4', name: 'GPT-4', provider: 'openai' },
    ]
  }
}

function refreshLogs() {
  loadExecutionLogs()
  ElMessage.success('执行记录已刷新')
}

// 打开创建智能体对话框
function openCreateAgent() {
  editingAgent.value = null
  agentTabActive.value = 'basic'
  agentForm.value = {
    name: '',
    type: 'general',
    description: '',
    status: '离线',
    scope: 'global',
    template_ids: [],
    knowledge_base_ids: [],
    workflow_ids: [],
    plugin_ids: [],
    system_prompt: '',
    visible_apps: [],
  }
  agentDialogVisible.value = true
}

// 打开编辑智能体对话框
function openEditAgent(agent) {
  editingAgent.value = agent
  agentTabActive.value = 'basic'
  // 解析绑定的 IDs（从 agent 对象中获取）
  const agentData = agent as any
  agentForm.value = {
    name: agentData.name,
    type: agentData.type || 'general',
    description: agentData.description || '',
    status: agentData.status || '离线',
    scope: agentData.scope || 'global',
    template_ids: parseJsonArray(agentData.template_ids),
    knowledge_base_ids: parseJsonArray(agentData.knowledge_base_ids),
    workflow_ids: parseJsonArray(agentData.workflow_ids),
    plugin_ids: parseJsonArray(agentData.plugin_ids),
    system_prompt: agentData.system_prompt || '',
    visible_apps: parseJsonArray(agentData.visible_apps),
  }
  agentDialogVisible.value = true
}

// 解析 JSON 数组（兼容字符串和数组格式）
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

// 保存智能体
async function saveAgent() {
  if (!agentForm.value.name.trim()) {
    ElMessage.error('请输入智能体名称')
    return
  }
  
  savingAgent.value = true
  
  try {
    // 构建提交数据
    const submitData = {
      name: agentForm.value.name,
      type: agentForm.value.type,
      description: agentForm.value.description,
      status: agentForm.value.status,
      scope: agentForm.value.scope,
      template_ids: agentForm.value.template_ids,
      knowledge_base_ids: agentForm.value.knowledge_base_ids,
      workflow_ids: agentForm.value.workflow_ids,
      plugin_ids: agentForm.value.plugin_ids,
      system_prompt: agentForm.value.system_prompt,
      visible_apps: agentForm.value.visible_apps,
    }
    
    if (editingAgent.value) {
      // 更新
      await aiAPI.updateAgent(editingAgent.value.id, submitData)
      ElMessage.success('智能体更新成功')
    } else {
      // 创建
      await aiAPI.createAgent(submitData)
      ElMessage.success('智能体创建成功')
    }
    agentDialogVisible.value = false
    loadAgents() // 重新加载列表
  } catch (error: any) {
    console.error('保存智能体失败:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || '未知错误'
    ElMessage.error('保存失败: ' + errorMsg)
  } finally {
    savingAgent.value = false
  }
}

// ==================== 提示词辅助函数 ====================

// 插入示例提示词
function insertExamplePrompt() {
  // 根据智能体类型选择合适的模板
  const typeMap: Record<string, string> = {
    'general': 'customer',
    '客服': 'customer',
    'customer_service': 'customer',
    '文档': 'doc',
    'document': 'doc',
    '分析': 'data',
    'analytics': 'data',
    '开发': 'code',
    'development': 'code',
    'hr': 'hr',
    '财务': 'finance',
    'finance': 'finance'
  }
  
  const templateKey = typeMap[agentForm.value.type] || 'customer'
  const template = promptTemplates[templateKey]
  
  // 如果当前有内容，先确认是否替换
  if (agentForm.value.system_prompt && agentForm.value.system_prompt.trim()) {
    ElMessageBox.confirm('当前提示词将被替换，是否继续？', '确认', {
      confirmButtonText: '替换',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      agentForm.value.system_prompt = template
      ElMessage.success('已插入示例提示词')
    }).catch(() => {})
  } else {
    agentForm.value.system_prompt = template
    ElMessage.success('已插入示例提示词')
  }
}

// 处理快捷模板选择
function handleExampleSelect(command: string) {
  const template = promptTemplates[command]
  if (template) {
    // 如果当前有内容，先确认是否替换
    if (agentForm.value.system_prompt && agentForm.value.system_prompt.trim()) {
      ElMessageBox.confirm('当前提示词将被替换，是否继续？', '确认', {
        confirmButtonText: '替换',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        agentForm.value.system_prompt = template
        const names: Record<string, string> = {
          customer: '客服助手',
          doc: '文档助手',
          data: '数据分析助手',
          code: '代码助手',
          hr: 'HR助手',
          finance: '财务助手'
        }
        // 替换模板中的 XX 为智能体名称
        agentForm.value.system_prompt = template.replace(/XX/g, agentForm.value.name || names[command] || '助手')
        ElMessage.success('已应用快捷模板')
      }).catch(() => {})
    } else {
      const names: Record<string, string> = {
        customer: '客服助手',
        doc: '文档助手',
        data: '数据分析助手',
        code: '代码助手',
        hr: 'HR助手',
        finance: '财务助手'
      }
      agentForm.value.system_prompt = template.replace(/XX/g, agentForm.value.name || names[command] || '助手')
      ElMessage.success('已应用快捷模板')
    }
  }
}

// 使用 AI 生成提示词
async function generatePromptWithAI() {
  if (!agentForm.value.name.trim()) {
    ElMessage.error('请先输入智能体名称')
    return
  }
  
  generatingPrompt.value = true
  
  try {
    // 构建生成提示词的请求
    const agentName = agentForm.value.name
    const agentType = agentForm.value.type
    const description = agentForm.value.description || '通用助手'
    const boundTemplates = availableTemplates.value.filter((t: any) => 
      agentForm.value.template_ids.includes(t.id)
    ).map((t: any) => t.name).join('、')
    const boundKnowledge = availableKnowledgeBases.value.filter((kb: any) => 
      agentForm.value.knowledge_base_ids.includes(kb.id)
    ).map((kb: any) => kb.name).join('、')
    
    const contextInfo = `
## 智能体信息
- 名称：${agentName}
- 类型：${agentType}
- 描述：${description}
${boundTemplates ? `- 处理的表单：${boundTemplates}` : ''}
${boundKnowledge ? `- 关联知识库：${boundKnowledge}` : ''}
`.trim()
    
    const prompt = `请为以下智能体生成一个专业的系统提示词。

${contextInfo}

要求：
1. 详细定义智能体的角色定位和能力范围
2. 明确智能体的行为准则和服务标准
3. 提供常用回复模板或工作流程
4. 包含处理边界情况和注意事项
5. 格式规范，使用 Markdown 结构化输出

请直接输出提示词内容，不要额外的解释。`

    // 调用 AI 生成
    const response = await fetch('/api/v1/ai/agent-engine/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        agent_id: null,
        message: prompt,
        model: selectedModel.value || 'qwen-turbo',
        history: []
      })
    })
    
    const data = await response.json()
    
    if (data.success && data.response) {
      agentForm.value.system_prompt = data.response
      ElMessage.success('提示词生成成功！请根据实际情况进行调整')
    } else {
      throw new Error(data.detail || '生成失败')
    }
  } catch (error: any) {
    console.error('生成提示词失败:', error)
    ElMessage.error('生成失败：' + (error.message || '请检查 AI 配置'))
    
    // 回退到示例模板
    ElMessage.info('将为您插入示例提示词作为参考')
    insertExamplePrompt()
  } finally {
    generatingPrompt.value = false
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

// 开始创建连接
function startCreatingConnection(nodeId: string, isSource: boolean) {
  // 阻止默认行为和事件冒泡
  event?.stopPropagation()
  event?.preventDefault()

  creatingConnection.value = true
  connectionSourceId.value = nodeId
  connectionIsSource.value = isSource

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
  editingWorkflowId.value = null
  currentWorkflowName.value = ''
  currentWorkflowDescription.value = ''
  currentEditingWorkflow.value = null
  workflowDialogVisible.value = true
}

// 确认创建工作流
function confirmCreateWorkflow() {
  if (!currentWorkflowName.value.trim()) {
    ElMessage.error('请输入工作流名称')
    return
  }

  // 创建新工作流数据
  const newWorkflow: any = {
    id: Date.now(),
    name: currentWorkflowName.value.trim(),
    description: currentWorkflowDescription.value.trim(),
    status: '草稿',
    version: 'v1.0',
    lastRun: '从未运行',
    nodes: [
      { id: 'node-1', type: 'start', label: '开始', x: 100, y: 200, width: 80, height: 40 },
      { id: 'node-5', type: 'end', label: '结束', x: 750, y: 200, width: 80, height: 40 }
    ],
    connections: []
  }

  // 添加到工作流列表
  workflows.value.unshift(newWorkflow)

  // 自动进入设计模式
  designWorkflow(newWorkflow)

  workflowDialogVisible.value = false
  ElMessage.success(`已创建工作流「${currentWorkflowName.value}」`)
}

// 设计工作流 - 加载工作流到画布
function designWorkflow(row: any) {
  currentEditingWorkflow.value = row

  // 查找完整的工作流数据
  const workflowData = workflows.value.find((w: any) => w.id === row.id)

  if (workflowData && workflowData.nodes && workflowData.nodes.length > 0) {
    // 加载已有节点和连接
    workflowNodes.value = [...workflowData.nodes]
    workflowConnections.value = [...(workflowData.connections || [])]
  } else {
    // 空工作流，只保留开始和结束节点
    workflowNodes.value = [
      { id: 'node-1', type: 'start', label: '开始', x: 100, y: 200, width: 80, height: 40 },
      { id: 'node-5', type: 'end', label: '结束', x: 750, y: 200, width: 80, height: 40 }
    ]
    workflowConnections.value = []
  }

  selectedNodeId.value = null
  ElMessage.success(`正在编辑工作流「${row.name}」`)
}

// 编辑工作流
function editWorkflow(row: any) {
  editingWorkflowId.value = row.id
  currentWorkflowName.value = row.name
  currentWorkflowDescription.value = row.description || ''
  workflowDialogVisible.value = true
}

// 保存工作流
function saveWorkflow() {
  if (!currentEditingWorkflow.value) {
    ElMessage.warning('请先选择要保存的工作流，或创建新工作流')
    return
  }

  const workflowData = {
    id: currentEditingWorkflow.value.id,
    name: currentEditingWorkflow.value.name,
    description: currentEditingWorkflow.value.description || '',
    nodes: workflowNodes.value,
    connections: workflowConnections.value,
    savedAt: new Date().toISOString()
  }

  // 更新列表中的工作流
  const idx = workflows.value.findIndex((w: any) => w.id === currentEditingWorkflow.value.id)
  if (idx !== -1) {
    workflows.value[idx] = { ...workflows.value[idx], ...workflowData }
  }

  ElMessage.success(`工作流「${currentEditingWorkflow.value.name}」已保存`)
}

// 导出工作流
function exportWorkflow() {
  if (!currentEditingWorkflow.value) {
    ElMessage.warning('请先选择要导出的工作流')
    return
  }

  const workflowData = {
    name: currentEditingWorkflow.value.name,
    description: currentEditingWorkflow.value.description || '',
    nodes: workflowNodes.value,
    connections: workflowConnections.value,
    exportedAt: new Date().toISOString(),
    version: '1.0'
  }

  const dataStr = JSON.stringify(workflowData, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)

  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', `workflow_${currentEditingWorkflow.value.name}_${Date.now()}.json`)
  linkElement.click()

  ElMessage.success('工作流已导出')
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
  height: 400px;
}

.components-list {
  max-height: 350px;
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

/* 智能体配置对话框样式 */
.agent-config-tabs {
  min-height: 400px;
}

.binding-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.binding-item {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.binding-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.binding-header .el-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.binding-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.system-prompt-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.prompt-actions {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.prompt-hint {
  font-size: 12px;
  color: var(--el-color-primary);
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 聊天对话框样式 */
.chat-container {
  height: 450px;
  display: flex;
  flex-direction: column;
}

.chat-model-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.model-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  margin-bottom: 12px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
}

.chat-empty p {
  margin: 8px 0 0;
}

.chat-empty .chat-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-message.user .message-avatar {
  background: #409EFF;
  color: white;
}

.chat-message.assistant .message-avatar {
  background: #67C23A;
  color: white;
}

.message-content {
  max-width: 75%;
}

.chat-message.user .message-content {
  text-align: right;
}

.message-text {
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-message.user .message-text {
  background: #409EFF;
  color: white;
  border-bottom-right-radius: 2px;
}

.chat-message.assistant .message-text {
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  border-bottom-left-radius: 2px;
}

.message-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}

.chat-message.user .message-time {
  text-align: right;
}

.message-text.loading {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
}

.message-text.loading .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--el-text-color-secondary);
  animation: bounce 1.4s infinite ease-in-out both;
}

.message-text.loading .dot:nth-child(1) { animation-delay: -0.32s; }
.message-text.loading .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  display: flex;
  gap: 8px;
}

.chat-input-area .el-input {
  flex: 1;
}

/* 模型下拉框样式 - 确保显示在下拉框下方 */
.model-select-dropdown {
  z-index: 3000 !important;
}

.model-select-dropdown .el-select-dropdown__item {
  padding: 8px 20px;
}

.model-select-dropdown .el-select-dropdown__item.selected {
  font-weight: 600;
  color: var(--el-color-primary);
}
</style>

<!-- 非scoped 样式，确保下拉框无论渲染到哪里都能正确显示 -->
<style>
.model-select-dropdown {
  z-index: 10000 !important;
}

.model-select-dropdown .el-select-dropdown__item {
  padding: 8px 20px !important;
  font-size: 14px;
}

.model-select-dropdown .el-select-dropdown__item.selected {
  font-weight: 600 !important;
  color: var(--el-color-primary) !important;
  background-color: var(--el-color-primary-light-9) !important;
}

.model-select-dropdown .el-select-dropdown__item:hover {
  background-color: var(--el-fill-color-light) !important;
}

/* 确保对话框内的下拉框不会被遮挡 */
.el-dialog .el-select__popper {
  z-index: 10000 !important;
}
</style>