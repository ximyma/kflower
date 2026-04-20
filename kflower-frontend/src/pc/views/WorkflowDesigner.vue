<template>
  <div class="workflow-designer">
    <div class="designer-header">
      <el-page-header :title="workflowName" @back="goBack">
        <template #content>
          <div class="header-actions">
            <el-button type="primary" @click="saveWorkflow">
              <el-icon><Check /></el-icon> 保存
            </el-button>
            <el-button @click="validateWorkflow">
              <el-icon><CircleCheck /></el-icon> 验证
            </el-button>
            <el-button @click="previewWorkflow">
              <el-icon><View /></el-icon> 预览
            </el-button>
          </div>
        </template>
      </el-page-header>
    </div>
    
    <div class="designer-body">
      <!-- 左侧工具栏 -->
      <div class="toolbox">
        <h4>流程节点</h4>
        <div class="node-list">
          <div
            v-for="node in nodeTypes"
            :key="node.type"
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <el-icon :size="20"><component :is="node.icon" /></el-icon>
            <span>{{ node.name }}</span>
          </div>
        </div>
      </div>
      
      <!-- 中间画布 -->
      <div
        class="canvas"
        ref="canvasRef"
        @dragover.prevent
        @drop="handleDrop"
        @click="deselectNode"
      >
        <svg class="connections" ref="connectionsSvg">
          <path
            v-for="conn in connections"
            :key="conn.id"
            :d="conn.path"
            class="connection-line"
            :class="{ selected: selectedConnection === conn.id }"
            @click.stop="selectConnection(conn.id)"
          />
          <!-- 连线预览 -->
          <path
            v-if="isConnecting && connectionStart && previewPath"
            :d="previewPath"
            class="connection-line preview"
          />
        </svg>
        
        <div
          v-for="node in nodes"
          :key="node.id"
          class="workflow-node"
          :class="{ selected: selectedNode === node.id }"
          :style="{ left: node.x + 'px', top: node.y + 'px' }"
          @mousedown="startDrag($event, node)"
          @click.stop="selectNode(node.id)"
        >
          <div class="node-header" :class="node.type">
            <el-icon><component :is="getNodeIcon(node.type)" /></el-icon>
            <span>{{ node.name }}</span>
          </div>
          <div class="node-body">
            <p>{{ node.description || '暂无描述' }}</p>
          </div>
          <div class="node-ports">
            <div class="input-ports">
              <div
                class="port input"
                @mousedown.stop="startConnection($event, node.id, 'input')"
              />
            </div>
            <div class="output-ports">
              <div
                class="port output"
                @mousedown.stop="startConnection($event, node.id, 'output')"
              />
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧属性面板 -->
      <div class="properties">
        <h4>属性配置</h4>
        <div v-if="selectedNodeData" class="property-form">
          <el-tabs v-model="activePropertyTab">
            <el-tab-pane label="基本属性" name="basic">
              <el-form label-width="100px">
                <el-form-item label="节点名称">
                  <el-input v-model="selectedNodeData.name" />
                </el-form-item>
                <el-form-item label="节点描述">
                  <el-input v-model="selectedNodeData.description" type="textarea" :rows="2" />
                </el-form-item>
                <!-- 表单模板绑定 -->
                <el-form-item label="绑定表单" v-if="['approval', 'task', 'cc', 'data_fill', 'trigger', 'data_change'].includes(selectedNodeData.type)">
                  <el-select
                    v-model="nodeConfig.form_template_id"
                    placeholder="选择表单模板"
                    filterable
                    style="width: 100%"
                    @change="handleTemplateChange"
                  >
                    <el-option label="不绑定表单" :value="undefined" />
                    <el-option
                      v-for="template in templates"
                      :key="template.id"
                      :label="`${template.name} (ID: ${template.id})`"
                      :value="template.id"
                    />
                  </el-select>
                  <div class="form-tip">选择此节点操作的表单模板</div>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 审批节点配置 - 斑斑低代码平台标准 -->
            <el-tab-pane label="审批配置" name="approval" v-if="['approval', 'task', 'cc'].includes(selectedNodeData.type)">
              <el-form label-width="120px">
                <!-- 审批类型 -->
                <el-form-item label="审批类型">
                  <el-select v-model="nodeConfig.approval_type" placeholder="选择审批类型">
                    <el-option label="自动通过" value="auto_approve" />
                    <el-option label="自动拒绝" value="auto_reject" />
                    <el-option label="人工审批" value="manual" />
                  </el-select>
                </el-form-item>
                
                <!-- 人工审批配置 -->
                <template v-if="nodeConfig.approval_type === 'manual'">
                  <!-- 审批方式 -->
                  <el-form-item label="审批方式">
                    <el-select v-model="nodeConfig.approval_mode" placeholder="选择审批方式">
                      <el-option label="常规审批" value="regular" />
                      <el-option label="逐级审批" value="hierarchical" />
                    </el-select>
                  </el-form-item>
                  
                  <!-- 人员选择 -->
                  <el-form-item label="审批人来源">
                    <el-select v-model="nodeConfig.assignee_source" placeholder="选择审批人来源">
                      <el-option label="提交人自己" value="submitter" />
                      <el-option label="指定成员/角色" value="specified" />
                      <el-option label="部门主管" value="department_manager" />
                      <el-option label="表单内成员字段" value="form_member_field" />
                      <el-option label="表单内部门字段" value="form_department_field" />
                    </el-select>
                  </el-form-item>
                  
                  <!-- 根据选择显示不同的配置 -->
                  <template v-if="nodeConfig.assignee_source === 'specified'">
                    <el-form-item label="选择审批人">
                      <el-select
                        v-model="nodeConfig.assignee_value"
                        multiple
                        placeholder="选择用户或角色"
                        filterable
                        style="width: 100%"
                      >
                        <el-option-group label="用户">
                          <el-option
                            v-for="user in users"
                            :key="`user-${user.id}`"
                            :label="`${user.full_name || user.username} (${user.username})`"
                            :value="`user:${user.id}`"
                          />
                        </el-option-group>
                        <el-option-group label="角色">
                          <el-option
                            v-for="role in roles"
                            :key="`role-${role.id}`"
                            :label="role.name"
                            :value="`role:${role.id}`"
                          />
                        </el-option-group>
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="多人审批方式" v-if="nodeConfig.assignee_value && nodeConfig.assignee_value.length > 1">
                      <el-select v-model="nodeConfig.multi_person_mode" placeholder="选择审批方式">
                        <el-option label="会签（需所有人同意）" value="all" />
                        <el-option label="或签（一人同意即可）" value="any" />
                        <el-option label="依次审批（按顺序）" value="sequential" />
                      </el-select>
                    </el-form-item>
                  </template>
                  
                  <template v-if="nodeConfig.assignee_source === 'form_member_field' || nodeConfig.assignee_source === 'form_department_field'">
                    <el-form-item label="表单字段">
                      <el-select
                        v-model="nodeConfig.assignee_value"
                        placeholder="选择表单字段"
                        style="width: 100%"
                      >
                        <el-option label="请先选择表单模板" value="" disabled v-if="!nodeConfig.form_template_id" />
                        <el-option 
                          v-for="field in getTemplateFields(nodeConfig.form_template_id)"
                          :key="field.name"
                          :label="`${field.label || field.name} (${field.name})`"
                          :value="field.name"
                        />
                      </el-select>
                    </el-form-item>
                  </template>
                  
                  <!-- 部门主管配置 -->
                  <template v-if="nodeConfig.assignee_source === 'department_manager'">
                    <el-form-item label="主管级别">
                      <el-select v-model="nodeConfig.assignee_value" placeholder="选择主管级别">
                        <el-option label="直接主管" value="direct" />
                        <el-option label="二级主管" value="level2" />
                        <el-option label="三级主管" value="level3" />
                        <el-option label="顶级主管" value="top" />
                      </el-select>
                    </el-form-item>
                  </template>
                  
                  <!-- 操作权限 -->
                  <el-form-item label="允许转交">
                    <el-switch v-model="nodeConfig.allow_transfer" />
                  </el-form-item>
                  
                  <el-form-item label="必须填写意见">
                    <el-switch v-model="nodeConfig.require_comment" />
                  </el-form-item>
                </template>
                
                <!-- 超时设置 -->
                <el-form-item label="超时时间(小时)">
                  <el-input-number v-model="nodeConfig.timeout_hours" :min="0" :step="1" />
                </el-form-item>
                
                <el-form-item label="超时动作">
                  <el-select v-model="nodeConfig.timeout_action" placeholder="选择超时动作">
                    <el-option label="通知管理员" value="notify" />
                    <el-option label="自动通过" value="auto_approve" />
                    <el-option label="自动拒绝" value="auto_reject" />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 表单权限配置 -->
            <el-tab-pane label="表单权限" name="form_permissions" v-if="nodeConfig.form_template_id && ['approval', 'task', 'cc', 'data_fill'].includes(selectedNodeData.type)">
              <div class="permission-container">
                <div class="permission-header">
                  <span>字段权限控制</span>
                  <el-button type="primary" size="small" @click="setAllPermissions('editable')">全部可编辑</el-button>
                  <el-button size="small" @click="setAllPermissions('visible')">全部仅可见</el-button>
                  <el-button type="danger" size="small" @click="setAllPermissions('hidden')">全部隐藏</el-button>
                </div>
                <el-table :data="getTemplateFields(nodeConfig.form_template_id)" border style="width: 100%">
                  <el-table-column prop="label" label="字段名称" width="150" />
                  <el-table-column prop="type" label="字段类型" width="100" />
                  <el-table-column label="权限" width="200">
                    <template #default="{ row }">
                      <el-select 
                        v-model="nodeConfig.field_permissions[row.name]" 
                        size="small"
                        style="width: 100%"
                      >
                        <el-option label="可编辑" value="editable" />
                        <el-option label="仅可见" value="visible" />
                        <el-option label="隐藏" value="hidden" />
                      </el-select>
                    </template>
                  </el-table-column>
                  <el-table-column label="说明" min-width="150">
                    <template #default="{ row }">
                      <span v-if="nodeConfig.field_permissions[row.name] === 'editable'">用户可查看和修改此字段</span>
                      <span v-else-if="nodeConfig.field_permissions[row.name] === 'visible'">用户只能查看，不能修改</span>
                      <span v-else>用户无法看到此字段</span>
                    </template>
                  </el-table-column>
                </el-table>
                <div class="permission-tip">
                  <p>📌 <strong>权限说明：</strong></p>
                  <p>• <strong>可编辑</strong>：用户可查看和修改此字段</p>
                  <p>• <strong>仅可见</strong>：用户只能查看，不能修改（适用于审批时查看原始数据）</p>
                  <p>• <strong>隐藏</strong>：用户无法看到此字段（适用于敏感信息）</p>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 条件节点配置 - 斑斑低代码平台标准 -->
            <el-tab-pane label="条件配置" name="condition" v-if="selectedNodeData.type === 'condition'">
              <el-form label-width="120px">
                <!-- 数据源表单 -->
                <el-form-item label="数据源表单">
                  <div class="data-source-list">
                    <div v-if="!nodeConfig.data_sources || nodeConfig.data_sources.length === 0" class="empty-data-sources">
                      未添加数据源，默认使用当前表单数据
                    </div>
                    <div v-else class="data-source-items">
                      <div v-for="(source, index) in nodeConfig.data_sources" :key="index" class="data-source-item">
                        <div class="source-header">
                          <span>数据源 {{index + 1}}</span>
                          <el-button type="danger" size="small" link @click="removeDataSource(index)">删除</el-button>
                        </div>
                        <div class="source-content">
                          <el-select
                            v-model="source.template_id"
                            placeholder="选择表单模板"
                            style="width: 100%; margin-bottom: 8px;"
                            @change="updateDataSourceFilters(index)"
                          >
                            <el-option
                              v-for="template in templates"
                              :key="template.id"
                              :label="`${template.name} (ID: ${template.id})`"
                              :value="template.id"
                            />
                          </el-select>
                          <el-input
                            v-model="source.alias"
                            placeholder="别名（可选）"
                            size="small"
                            style="margin-bottom: 8px;"
                          />
                          <div class="filter-conditions">
                            <div v-for="(filter, filterIndex) in source.filter_conditions" :key="filterIndex" class="filter-item">
                              <el-select v-model="filter.field" placeholder="字段" size="small" style="width: 120px;">
                                <el-option
                                  v-for="field in getTemplateFields(source.template_id)"
                                  :key="field.name"
                                  :label="field.label"
                                  :value="field.name"
                                />
                              </el-select>
                              <el-select v-model="filter.operator" placeholder="操作符" size="small" style="width: 100px; margin: 0 8px;">
                                <el-option label="等于" value="eq" />
                                <el-option label="不等于" value="ne" />
                                <el-option label="大于" value="gt" />
                                <el-option label="小于" value="lt" />
                                <el-option label="包含" value="contains" />
                                <el-option label="为空" value="is_null" />
                              </el-select>
                              <el-input v-model="filter.value" placeholder="值" size="small" style="width: 100px;" />
                              <el-button type="danger" size="small" link @click="removeFilterCondition(index, filterIndex)">删除</el-button>
                            </div>
                            <el-button size="small" @click="addFilterCondition(index)">添加筛选条件</el-button>
                          </div>
                        </div>
                      </div>
                    </div>
                    <el-button type="primary" size="small" @click="addDataSource">添加数据源</el-button>
                  </div>
                </el-form-item>
                
                <!-- 条件表达式 -->
                <el-form-item label="条件表达式">
                  <el-input 
                    v-model="nodeConfig.expression" 
                    type="textarea" 
                    :rows="3" 
                    placeholder="如: {{current.amount}} > 1000 AND {{source1.status}} == 'approved'"
                  />
                  <div class="form-tip">
                    <p>📌 <strong>表达式语法：</strong></p>
                    <p>• 当前表单字段：<code>{{current.字段名}}</code></p>
                    <p>• 数据源字段：<code>{{数据源别名.字段名}}</code> 或 <code>{{数据源索引.字段名}}</code></p>
                    <p>• 支持运算符：<code>==, !=, >, <, >=, <=, AND, OR, NOT</code></p>
                    <p>• 示例：<code>{{current.amount}} > 1000 AND {{source1.approver_id}} == {{current.manager_id}}</code></p>
                  </div>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 数据变更节点配置 -->
            <el-tab-pane label="数据操作" name="data_change" v-if="selectedNodeData.type === 'data_change'">
              <el-form label-width="100px">
                <el-form-item label="操作类型">
                  <el-select v-model="nodeConfig.action" placeholder="选择操作">
                    <el-option label="新增数据" value="create" />
                    <el-option label="更新数据" value="update" />
                    <el-option label="删除数据" value="delete" />
                  </el-select>
                </el-form-item>
                <el-form-item label="目标模板ID">
                  <el-input-number v-model="nodeConfig.target_template_id" :min="1" :step="1" />
                </el-form-item>
                <el-form-item label="数据映射">
                  <div v-for="(value, key) in nodeConfig.data_mapping || {}" :key="key" class="mapping-item">
                    <el-input v-model="nodeConfig.data_mapping[key]" :placeholder="`字段: ${key}`" size="small" style="margin-bottom: 5px;" />
                  </div>
                  <el-button size="small" @click="addDataMapping">添加映射</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 插件节点配置 -->
            <el-tab-pane label="插件配置" name="plugin" v-if="selectedNodeData.type === 'trigger'">
              <el-form label-width="100px">
                <el-form-item label="插件ID">
                  <el-input v-model="nodeConfig.plugin_id" placeholder="输入插件ID" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 延迟节点配置 -->
            <el-tab-pane label="延迟配置" name="delay" v-if="selectedNodeData.type === 'delay'">
              <el-form label-width="100px">
                <el-form-item label="延迟时间(秒)">
                  <el-input-number v-model="nodeConfig.delay_seconds" :min="0" :step="1" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 子流程配置 -->
            <el-tab-pane label="子流程" name="subprocess" v-if="selectedNodeData.type === 'sub_process'">
              <el-form label-width="100px">
                <el-form-item label="子流程ID">
                  <el-input-number v-model="nodeConfig.sub_workflow_id" :min="1" :step="1" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 插件配置（通用） -->
            <el-tab-pane label="插件" name="plugins" v-if="['approval', 'task', 'data_change', 'trigger'].includes(selectedNodeData.type)">
              <el-form label-width="100px">
                <el-form-item label="前置插件">
                  <el-input v-model="nodeConfig.plugins.before" placeholder="插件ID" />
                </el-form-item>
                <el-form-item label="后置插件">
                  <el-input v-model="nodeConfig.plugins.after" placeholder="插件ID" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
          
          <el-divider />
          
          <div class="property-actions">
            <el-button type="danger" @click="deleteNode">删除节点</el-button>
            <el-button type="primary" @click="saveNodeConfig">保存配置</el-button>
          </div>
        </div>
        <div v-else class="empty-properties">
          <el-empty description="请选择节点进行配置" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check, CircleCheck, View, UserFilled, Document, Message, Edit,
  Connection, Share, Sort, SetUp, MagicStick, Refresh, Timer, VideoPlay
} from '@element-plus/icons-vue'
import { templateAPI, userAPI, workflowAPI } from '../../common/api'

interface WorkflowNode {
  id: string
  type: string
  name: string
  description?: string
  x: number
  y: number
  config?: {
    // 斑斑低代码平台标准配置
    // 通用配置
    form_template_id?: number  // 绑定的表单模板ID
    field_permissions?: Record<string, 'visible' | 'editable' | 'hidden'>  // 字段权限
    
    // 触发节点配置
    trigger_type?: 'data_change' | 'timer'  // 触发类型：数据变化或定时触发
    change_types?: ('create' | 'update' | 'delete')[]  // 数据变化类型
    
    // 审批/办理/抄送节点配置
    approval_type?: 'auto_approve' | 'auto_reject' | 'manual'  // 审批类型：自动通过、自动拒绝、人工审批
    approval_mode?: 'regular' | 'hierarchical'  // 审批方式：常规审批、逐级审批
    assignee_source?: 'submitter' | 'specified' | 'department_manager' | 'form_member_field' | 'form_department_field'  // 人员选择来源
    assignee_value?: string | number | number[]  // 人员选择值：用户ID、角色ID、字段名等
    multi_person_mode?: 'all' | 'any' | 'sequential'  // 多人处理方式：会签、或签、依次处理
    allow_transfer?: boolean  // 是否允许转交
    require_comment?: boolean  // 是否必须填写意见
    timeout_hours?: number  // 超时时间（小时）
    timeout_action?: 'notify' | 'auto_approve' | 'auto_reject'  // 超时动作
    
    // 条件节点配置
    expression?: string  // 条件表达式
    
    // 数据操作节点配置
    operation_type?: 'create' | 'update' | 'delete'  // 数据操作类型
    target_template_id?: number  // 目标表单模板ID
    data_mapping?: Record<string, string>  // 数据映射
    filter_conditions?: any[]  // 筛选条件
    
    // 数据源配置（用于条件判断和数据操作）
    data_sources?: Array<{
      template_id: number
      alias?: string
      filter_conditions?: any[]
    }>
    
    // 延迟节点配置
    delay_seconds?: number
    
    // 子流程配置
    sub_workflow_id?: number
    
    // 插件配置
    plugin_id?: string
    plugins?: {
      before?: string
      after?: string
    }
  }
}

interface Connection {
  id: string
  from: string
  to: string
  path: string
  label?: string  // 条件表达式
}

const route = useRoute()
const router = useRouter()
const workflowId = route.params.id as string
const workflowName = ref('新建流程')

// 模板列表 - 用于绑定表单
const templates = ref<any[]>([])
const loadingTemplates = ref(false)

// 用户列表 - 用于人员选择
const users = ref<any[]>([])
const loadingUsers = ref(false)

// 角色列表 - 用于人员选择
const roles = ref<any[]>([])
const loadingRoles = ref(false)

const canvasRef = ref<HTMLElement>()
const connectionsSvg = ref<SVGSVGElement>()

// 节点类型 - 根据dd4chat.txt方案支持12种节点类型
const nodeTypes = [
  { type: 'start', name: '开始节点', icon: 'VideoPlay', color: '#67C23A' },
  { type: 'end', name: '结束节点', icon: 'CircleCheck', color: '#F56C6C' },
  { type: 'approval', name: '审批节点', icon: 'UserFilled', color: '#409EFF' },
  { type: 'task', name: '办理节点', icon: 'Document', color: '#E6A23C' },
  { type: 'cc', name: '抄送节点', icon: 'Message', color: '#909399' },
  { type: 'data_fill', name: '数据填报', icon: 'Edit', color: '#8A2BE2' },
  { type: 'condition', name: '条件分支', icon: 'Connection', color: '#67C23A' },
  { type: 'parallel', name: '并行分叉', icon: 'Share', color: '#E6A23C' },
  { type: 'parallel_join', name: '并行汇合', icon: 'Sort', color: '#E6A23C' },
  { type: 'sub_process', name: '子流程', icon: 'SetUp', color: '#409EFF' },
  { type: 'trigger', name: '触发节点', icon: 'MagicStick', color: '#8A2BE2' },
  { type: 'data_change', name: '数据变更', icon: 'Refresh', color: '#67C23A' },
  { type: 'delay', name: '延迟节点', icon: 'Timer', color: '#909399' }
]

// 加载模板列表
const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await templateAPI.list({ limit: 100 })
    if (res && Array.isArray(res)) {
      templates.value = res
    } else if (res?.data && Array.isArray(res.data)) {
      templates.value = res.data
    }
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    loadingTemplates.value = false
  }
}

// 加载用户列表
const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const res = await userAPI.list({ limit: 200 })
    if (res && Array.isArray(res)) {
      users.value = res
    } else if (res?.data && Array.isArray(res.data)) {
      users.value = res.data
    }
  } catch (error) {
    console.error('加载用户失败:', error)
    ElMessage.error('加载用户失败')
  } finally {
    loadingUsers.value = false
  }
}

// 加载角色列表（TODO: 需要角色API）
const loadRoles = async () => {
  loadingRoles.value = true
  try {
    // 暂时使用模拟数据
    roles.value = [
      { id: 1, name: '管理员', code: 'admin' },
      { id: 2, name: '普通用户', code: 'user' },
      { id: 3, name: '部门经理', code: 'manager' },
      { id: 4, name: '人事专员', code: 'hr' }
    ]
  } catch (error) {
    console.error('加载角色失败:', error)
  } finally {
    loadingRoles.value = false
  }
}

// 初始化加载数据
const initData = async () => {
  loadTemplates()
  loadUsers()
  loadRoles()
  
  // 如果提供了工作流ID，则加载现有工作流
  if (workflowId && workflowId !== 'new') {
    await loadWorkflow(parseInt(workflowId))
  }
}

// 加载现有工作流
const loadWorkflow = async (id: number) => {
  try {
    const response = await workflowAPI.get(id)
    const workflow = response
    
    workflowName.value = workflow.name
    
    // 加载节点数据
    if (workflow.nodes && Array.isArray(workflow.nodes)) {
      nodes.value = workflow.nodes.map((node: any) => ({
        id: node.id,
        type: node.type,
        name: node.name,
        x: 100, // 默认位置，实际应该从node_definitions或config中获取
        y: 200,
        description: node.description || '',
        config: node.config || {}
      }))
    }
    
    // 加载连线数据
    if (workflow.edges && Array.isArray(workflow.edges)) {
      connections.value = workflow.edges.map((edge: any) => ({
        id: edge.id || `conn-${edge.source}-${edge.target}`,
        from: edge.source,
        to: edge.target,
        path: '', // 路径会在updateConnections中生成
        label: edge.label || ''
      }))
      updateConnections()
    }
    
    // 如果有node_definitions，可以更新节点配置
    if (workflow.node_definitions && Array.isArray(workflow.node_definitions)) {
      workflow.node_definitions.forEach((nodeDef: any) => {
        const node = nodes.value.find(n => n.id === nodeDef.id)
        if (node && nodeDef.config) {
          node.config = { ...node.config, ...nodeDef.config }
        }
      })
    }
    
    ElMessage.success('工作流加载成功')
  } catch (error: any) {
    console.error('加载工作流失败:', error)
    ElMessage.error(`加载失败: ${error.message || '未知错误'}`)
  }
}

// 节点数据
const nodes = ref<WorkflowNode[]>([
  { id: 'start-1', type: 'start', name: '开始', x: 100, y: 200, description: '流程开始' }
])

// 连接线数据
const connections = ref<Connection[]>([])

// 选中状态
const selectedNode = ref<string | null>(null)
const selectedConnection = ref<string | null>(null)

// 拖拽状态
const isDragging = ref(false)
const dragNode = ref<WorkflowNode | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

// 连线状态
const isConnecting = ref(false)
const connectionStart = ref<{ nodeId: string; type: string } | null>(null)
const previewPath = ref('')
const mousePosition = ref({ x: 0, y: 0 })

// 计算选中的节点数据
const selectedNodeData = computed(() => {
  if (!selectedNode.value) return null
  return nodes.value.find(n => n.id === selectedNode.value) || null
})

// 确保节点配置存在
const nodeConfig = computed(() => {
  if (!selectedNodeData.value) return {}
  if (!selectedNodeData.value.config) {
    selectedNodeData.value.config = {}
  }
  // 确保 plugins 对象存在
  if (!selectedNodeData.value.config.plugins) {
    selectedNodeData.value.config.plugins = { before: '', after: '' }
  }
  return selectedNodeData.value.config
})

// 属性面板活动标签
const activePropertyTab = ref('basic')

// 辅助函数
const getAssigneePlaceholder = (type: string) => {
  const placeholders: Record<string, string> = {
    user: '用户ID',
    role: '角色ID',
    expression: '如: {{applicant.manager_id}}',
    form_field: '表单字段名'
  }
  return placeholders[type] || '请输入'
}

// 获取模板字段
const getTemplateFields = (templateId?: number) => {
  if (!templateId) return []
  const template = templates.value.find(t => t.id === templateId)
  if (!template || !template.modules) return []
  
  const fields: Array<{name: string, label: string, type: string}> = []
  template.modules.forEach((module: any) => {
    if (module.fields && Array.isArray(module.fields)) {
      module.fields.forEach((field: any) => {
        fields.push({
          name: field.name || field.field,
          label: field.label || field.name || field.field,
          type: field.type || 'text'
        })
      })
    }
  })
  return fields
}

// 处理模板变更
const handleTemplateChange = (templateId?: number) => {
  if (!templateId) {
    // 清空字段权限
    if (nodeConfig.value.field_permissions) {
      nodeConfig.value.field_permissions = {}
    }
    return
  }
  
  // 初始化字段权限
  const fields = getTemplateFields(templateId)
  if (!nodeConfig.value.field_permissions) {
    nodeConfig.value.field_permissions = {}
  }
  
  // 为新增字段设置默认权限（可见且可编辑）
  fields.forEach(field => {
    if (!nodeConfig.value.field_permissions![field.name]) {
      nodeConfig.value.field_permissions![field.name] = 'editable'
    }
  })
}

// 设置所有字段权限
const setAllPermissions = (permission: 'editable' | 'visible' | 'hidden') => {
  if (!nodeConfig.value.field_permissions) {
    nodeConfig.value.field_permissions = {}
  }
  
  const fields = getTemplateFields(nodeConfig.value.form_template_id)
  fields.forEach(field => {
    nodeConfig.value.field_permissions![field.name] = permission
  })
  
  ElMessage.success(`已设置所有字段为${permission === 'editable' ? '可编辑' : permission === 'visible' ? '仅可见' : '隐藏'}`)
}

// 数据源表单管理
const addDataSource = () => {
  if (!nodeConfig.value.data_sources) {
    nodeConfig.value.data_sources = []
  }
  
  nodeConfig.value.data_sources.push({
    template_id: templates.value[0]?.id || 0,
    alias: `source${nodeConfig.value.data_sources.length + 1}`,
    filter_conditions: []
  })
}

const removeDataSource = (index: number) => {
  if (nodeConfig.value.data_sources) {
    nodeConfig.value.data_sources.splice(index, 1)
  }
}

const addFilterCondition = (sourceIndex: number) => {
  if (!nodeConfig.value.data_sources || !nodeConfig.value.data_sources[sourceIndex]) return
  
  if (!nodeConfig.value.data_sources[sourceIndex].filter_conditions) {
    nodeConfig.value.data_sources[sourceIndex].filter_conditions = []
  }
  
  nodeConfig.value.data_sources[sourceIndex].filter_conditions!.push({
    field: '',
    operator: 'eq',
    value: ''
  })
}

const removeFilterCondition = (sourceIndex: number, filterIndex: number) => {
  if (!nodeConfig.value.data_sources || !nodeConfig.value.data_sources[sourceIndex] || 
      !nodeConfig.value.data_sources[sourceIndex].filter_conditions) return
  
  nodeConfig.value.data_sources[sourceIndex].filter_conditions!.splice(filterIndex, 1)
}

const updateDataSourceFilters = (sourceIndex: number) => {
  // 当数据源模板变更时，清空筛选条件
  if (nodeConfig.value.data_sources && nodeConfig.value.data_sources[sourceIndex]) {
    nodeConfig.value.data_sources[sourceIndex].filter_conditions = []
  }
}

// 添加数据映射
const addDataMapping = () => {
  if (!nodeConfig.value.data_mapping) {
    nodeConfig.value.data_mapping = {}
  }
  const key = `field_${Object.keys(nodeConfig.value.data_mapping).length + 1}`
  nodeConfig.value.data_mapping[key] = '{{value}}'
}

// 保存节点配置
const saveNodeConfig = () => {
  ElMessage.success('配置已保存')
}

// 获取节点图标
const getNodeIcon = (type: string) => {
  const icons: Record<string, string> = {
    start: 'VideoPlay',
    end: 'CircleCheck',
    approval: 'UserFilled',
    task: 'Document',
    cc: 'Message',
    data_fill: 'Edit',
    condition: 'Connection',
    parallel: 'Share',
    parallel_join: 'Sort',
    sub_process: 'SetUp',
    trigger: 'MagicStick',
    data_change: 'Refresh',
    delay: 'Timer'
  }
  return icons[type] || 'CircleCheck'
}

// 返回列表
const goBack = () => {
  router.push('/workflows')
}

// 拖拽开始
const handleDragStart = (e: DragEvent, nodeType: any) => {
  e.dataTransfer?.setData('nodeType', JSON.stringify(nodeType))
}

// 放置节点
const handleDrop = (e: DragEvent) => {
  const data = e.dataTransfer?.getData('nodeType')
  if (!data) return
  
  const nodeType = JSON.parse(data)
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left - 75
  const y = e.clientY - rect.top - 30
  
  const newNode: WorkflowNode = {
    id: `${nodeType.type}-${Date.now()}`,
    type: nodeType.type,
    name: nodeType.name,
    description: '',
    x: Math.max(0, x),
    y: Math.max(0, y)
  }
  
  // 根据节点类型设置默认配置 - 斑斑低代码平台标准
  if (['approval', 'task', 'cc'].includes(nodeType.type)) {
    newNode.config = {
      approval_type: 'manual',  // 默认人工审批
      approval_mode: 'regular',  // 默认常规审批
      assignee_source: 'specified',  // 默认指定成员
      assignee_value: [],  // 默认空数组
      multi_person_mode: 'any',  // 默认或签
      allow_transfer: false,  // 默认不允许转交
      require_comment: false,  // 默认不需要填写意见
      timeout_hours: 72,  // 默认72小时超时
      timeout_action: 'notify'  // 默认通知
    }
  } else if (nodeType.type === 'condition') {
    newNode.config = {
      expression: '{{status}} == "approved"'
    }
  } else if (nodeType.type === 'trigger') {
    newNode.config = {
      trigger_type: 'data_change',  // 默认数据变化触发
      change_types: ['create', 'update', 'delete']  // 默认监听所有变化
    }
  } else if (nodeType.type === 'data_change') {
    newNode.config = {
      operation_type: 'update',  // 默认更新操作
      data_mapping: {},  // 空数据映射
      filter_conditions: []  // 空筛选条件
    }
  } else if (nodeType.type === 'delay') {
    newNode.config = {
      delay_seconds: 3600  // 默认1小时
    }
  } else if (nodeType.type === 'sub_process') {
    newNode.config = {
      sub_workflow_id: 0  // 默认未选择子流程
    }
  } else if (nodeType.type === 'data_fill') {
    newNode.config = {
      assignee_source: 'submitter',  // 默认提交人自己
      field_permissions: {}  // 空字段权限
    }
  }
  
  nodes.value.push(newNode)
  ElMessage.success('添加节点成功')
}

// 开始拖拽节点
const startDrag = (e: MouseEvent, node: WorkflowNode) => {
  isDragging.value = true
  dragNode.value = node
  dragOffset.value = {
    x: e.clientX - node.x,
    y: e.clientY - node.y
  }
}

// 选择节点
const selectNode = (nodeId: string) => {
  selectedNode.value = nodeId
  selectedConnection.value = null
}

// 取消选择
const deselectNode = () => {
  selectedNode.value = null
  selectedConnection.value = null
}

// 选择连接线
const selectConnection = (connId: string) => {
  selectedConnection.value = connId
  selectedNode.value = null
}

// 开始连线
const startConnection = (e: MouseEvent, nodeId: string, type: string) => {
  e.stopPropagation()
  isConnecting.value = true
  connectionStart.value = { nodeId, type }
  mousePosition.value = { x: e.clientX, y: e.clientY }
  updatePreviewPath()
}

// 更新预览路径
const updatePreviewPath = () => {
  if (!isConnecting.value || !connectionStart.value) return
  
  const startNode = nodes.value.find(n => n.id === connectionStart.value!.nodeId)
  if (!startNode) return
  
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const startX = startNode.x + 150
  const startY = startNode.y + 30
  const endX = mousePosition.value.x - rect.left
  const endY = mousePosition.value.y - rect.top
  
  const midX = (startX + endX) / 2
  
  previewPath.value = `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`
}

// 创建连接
const createConnection = (e: MouseEvent) => {
  if (!connectionStart.value) return
  
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  // 找到鼠标点击的节点
  const targetNode = nodes.value.find(node => {
    return mouseX >= node.x && mouseX <= node.x + 150 && 
           mouseY >= node.y && mouseY <= node.y + 80
  })
  
  if (targetNode && targetNode.id !== connectionStart.value.nodeId) {
    // 检查是否已存在相同连接
    const existingConnection = connections.value.find(
      conn => conn.from === connectionStart.value!.nodeId && conn.to === targetNode.id
    )
    
    if (!existingConnection) {
      const newConnection: Connection = {
        id: `conn-${Date.now()}`,
        from: connectionStart.value.nodeId,
        to: targetNode.id,
        path: generatePath(
          nodes.value.find(n => n.id === connectionStart.value!.nodeId)!,
          targetNode
        )
      }
      connections.value.push(newConnection)
      ElMessage.success('连接成功')
    } else {
      ElMessage.warning('该连接已存在')
    }
  }
}

// 删除节点
const deleteNode = () => {
  if (!selectedNode.value) return
  
  ElMessageBox.confirm('确定删除该节点吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    nodes.value = nodes.value.filter(n => n.id !== selectedNode.value)
    connections.value = connections.value.filter(
      c => c.from !== selectedNode.value && c.to !== selectedNode.value
    )
    selectedNode.value = null
    ElMessage.success('删除成功')
  })
}

// 保存流程
const saveWorkflow = async () => {
  try {
    // 验证流程
    const errors: string[] = []
    
    // 检查开始节点
    const startNodes = nodes.value.filter(n => n.type === 'start')
    if (startNodes.length === 0) {
      errors.push('缺少开始节点')
    } else if (startNodes.length > 1) {
      errors.push('只能有一个开始节点')
    }
    
    // 检查结束节点
    const endNodes = nodes.value.filter(n => n.type === 'end')
    if (endNodes.length === 0) {
      errors.push('缺少结束节点')
    }
    
    if (errors.length > 0) {
      ElMessageBox.alert(errors.join('<br>'), '验证失败', {
        dangerouslyUseHTMLString: true,
        type: 'error'
      })
      return
    }
    
    // 构建API请求数据
    const workflowData = {
      name: workflowName.value,
      description: `流程设计 ${new Date().toLocaleDateString()}`,
      flow_type: 'normal',
      nodes: nodes.value.map(node => ({
        id: node.id,
        type: node.type,
        name: node.name,
        config: node.config || {}
      })),
      edges: connections.value.map(conn => ({
        id: conn.id,
        source: conn.from,
        target: conn.to,
        label: conn.label || '',
        condition: {} // 可以从conn.label解析条件
      })),
      // 斑斑低代码平台扩展字段
      node_definitions: nodes.value.map(node => ({
        id: node.id,
        type: node.type,
        name: node.name,
        config: node.config || {}
      })),
      edge_definitions: connections.value.map(conn => ({
        id: conn.id,
        source: conn.from,
        target: conn.to,
        label: conn.label || '',
        condition: {} // 条件定义
      })),
      variables: {},
      form_template_id: findPrimaryFormTemplateId()
    }
    
    // 调用API保存
    if (workflowId && workflowId !== 'new') {
      await workflowAPI.update(parseInt(workflowId), workflowData)
      ElMessage.success('流程更新成功')
    } else {
      const response = await workflowAPI.create(workflowData)
      // 更新路由ID
      router.push(`/workflows/design/${response.id}`)
      ElMessage.success('流程创建成功')
    }
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`)
  }
}

// 查找主表单模板ID
const findPrimaryFormTemplateId = () => {
  // 首先查找开始节点后的第一个审批/办理节点
  const approvalNode = nodes.value.find(node => 
    ['approval', 'task', 'data_fill'].includes(node.type) && 
    node.config?.form_template_id
  )
  if (approvalNode?.config?.form_template_id) {
    return approvalNode.config.form_template_id
  }
  
  // 否则查找第一个有表单模板的节点
  const formNode = nodes.value.find(node => node.config?.form_template_id)
  return formNode?.config?.form_template_id || null
}

// 验证流程
const validateWorkflow = () => {
  const errors: string[] = []
  
  // 检查开始节点
  const startNodes = nodes.value.filter(n => n.type === 'start')
  if (startNodes.length === 0) {
    errors.push('缺少开始节点')
  } else if (startNodes.length > 1) {
    errors.push('只能有一个开始节点')
  }
  
  // 检查结束节点
  const endNodes = nodes.value.filter(n => n.type === 'end')
  if (endNodes.length === 0) {
    errors.push('缺少结束节点')
  }
  
  // 检查孤立节点
  const connectedNodes = new Set<string>()
  connections.value.forEach(conn => {
    connectedNodes.add(conn.from)
    connectedNodes.add(conn.to)
  })
  
  nodes.value.forEach(node => {
    if (!connectedNodes.has(node.id) && node.type !== 'start') {
      errors.push(`节点 "${node.name}" 未连接`)
    }
  })
  
  if (errors.length > 0) {
    ElMessageBox.alert(errors.join('<br>'), '验证失败', {
      dangerouslyUseHTMLString: true,
      type: 'error'
    })
  } else {
    ElMessage.success('流程验证通过')
  }
}

// 预览流程
const previewWorkflow = () => {
  ElMessageBox.alert('流程预览功能开发中...', '提示')
}

// 更新连接线
const updateConnections = () => {
  connections.value.forEach(conn => {
    const fromNode = nodes.value.find(n => n.id === conn.from)
    const toNode = nodes.value.find(n => n.id === conn.to)
    if (fromNode && toNode) {
      conn.path = generatePath(fromNode, toNode)
    }
  })
}

// 生成路径
const generatePath = (from: WorkflowNode, to: WorkflowNode) => {
  const startX = from.x + 150
  const startY = from.y + 30
  const endX = to.x
  const endY = to.y + 30
  
  const midX = (startX + endX) / 2
  
  return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`
}

// 全局鼠标事件
const handleMouseMove = (e: MouseEvent) => {
  if (isDragging.value && dragNode.value) {
    dragNode.value.x = e.clientX - dragOffset.value.x
    dragNode.value.y = e.clientY - dragOffset.value.y
    updateConnections()
  } else if (isConnecting.value && connectionStart.value) {
    // 更新鼠标位置
    mousePosition.value = { x: e.clientX, y: e.clientY }
    // 更新预览路径
    updatePreviewPath()
  }
}

const handleMouseUp = (e: MouseEvent) => {
  if (isDragging.value) {
    isDragging.value = false
    dragNode.value = null
  } else if (isConnecting.value && connectionStart.value) {
    // 尝试创建连接
    createConnection(e)
  }
  isConnecting.value = false
  connectionStart.value = null
  previewPath.value = ''
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  initData()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped lang="scss">
.workflow-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.designer-header {
  padding: 16px;
  border-bottom: 1px solid #e6e6e6;
  background: white;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.designer-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.toolbox {
  width: 200px;
  background: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  padding: 16px;
  
  h4 {
    margin-bottom: 16px;
  }
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
  }
}

.canvas {
  flex: 1;
  position: relative;
  background: #fafafa;
  background-image: 
    linear-gradient(#e6e6e6 1px, transparent 1px),
    linear-gradient(90deg, #e6e6e6 1px, transparent 1px);
  background-size: 20px 20px;
  overflow: hidden;
}

.connections {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: all;
}

.connection-line {
  fill: none;
  stroke: #909399;
  stroke-width: 2;
  pointer-events: stroke;
  cursor: pointer;
  
  &:hover, &.selected {
    stroke: #409eff;
    stroke-width: 3;
  }
  
  &.preview {
    stroke: #409eff;
    stroke-width: 2;
    stroke-dasharray: 5,5;
  }
}

.workflow-node {
  position: absolute;
  width: 150px;
  background: white;
  border: 2px solid #dcdfe6;
  border-radius: 4px;
  cursor: move;
  user-select: none;
  
  &.selected {
    border-color: #409eff;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
  }
  
  .node-header {
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: bold;
    border-bottom: 1px solid #e6e6e6;
    
    &.start { background: #67c23a; color: white; }
    &.task { background: #409eff; color: white; }
    &.condition { background: #e6a23c; color: white; }
    &.parallel { background: #909399; color: white; }
    &.end { background: #f56c6c; color: white; }
  }
  
  .node-body {
    padding: 8px 12px;
    font-size: 12px;
    color: #606266;
    min-height: 40px;
  }
  
  .node-ports {
    position: relative;
    height: 20px;
    
    .port {
      position: absolute;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #909399;
      cursor: crosshair;
      
      &:hover {
        background: #409eff;
        transform: scale(1.2);
      }
      
      &.input {
        left: -6px;
        top: 4px;
      }
      
      &.output {
        right: -6px;
        top: 4px;
      }
    }
  }
}

.properties {
  width: 300px;
  background: #f5f7fa;
  border-left: 1px solid #e6e6e6;
  padding: 16px;
  overflow-y: auto;
  
  h4 {
    margin-bottom: 16px;
  }
}

.empty-properties {
  padding: 40px 0;
}

.property-form {
  :deep(.el-tabs) {
    .el-tabs__nav-wrap::after {
      display: none;
    }
  }
  
  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
  
  .mapping-item {
    margin-bottom: 8px;
  }
  
  .property-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
  }
}

// 权限配置样式
.permission-container {
  padding: 10px;
  
  .permission-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e6e6e6;
    
    span {
      font-weight: bold;
      font-size: 14px;
    }
    
    .el-button {
      margin-left: 8px;
    }
  }
  
  .permission-tip {
    margin-top: 20px;
    padding: 12px;
    background: #f0f9ff;
    border-radius: 4px;
    border-left: 4px solid #409eff;
    
    p {
      margin: 4px 0;
      font-size: 12px;
      color: #606266;
      
      strong {
        color: #303133;
      }
    }
  }
}

// 数据源配置样式
.data-source-list {
  .empty-data-sources {
    padding: 16px;
    text-align: center;
    color: #909399;
    background: #f5f7fa;
    border-radius: 4px;
    margin-bottom: 12px;
  }
  
  .data-source-items {
    margin-bottom: 16px;
  }
  
  .data-source-item {
    padding: 12px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    margin-bottom: 12px;
    background: white;
    
    .source-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #f0f0f0;
      
      span {
        font-weight: bold;
        font-size: 13px;
      }
    }
    
    .source-content {
      .filter-conditions {
        margin-top: 12px;
        
        .filter-item {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
          padding: 8px;
          background: #f9f9f9;
          border-radius: 4px;
        }
      }
    }
  }
}
</style>
