<template>
  <div class="mobile-workflow-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </div>
      <div class="header-title">{{ workflowName || '新建流程' }}</div>
      <div class="header-right">
        <el-button type="primary" size="small" @click="saveWorkflow" :loading="saving">
          保存
        </el-button>
      </div>
    </div>

    <!-- 流程信息 -->
    <div class="workflow-info-section">
      <el-input v-model="workflowName" placeholder="流程名称" size="large" />
      <div class="workflow-type-select">
        <el-select v-model="workflowType" placeholder="流程类型" style="width: 100%">
          <el-option label="审批流程" value="approval" />
          <el-option label="填写流程" value="form" />
          <el-option label="通知流程" value="notification" />
        </el-select>
      </div>
      <el-input
        v-model="workflowDescription"
        type="textarea"
        :rows="2"
        placeholder="流程描述（可选）"
        style="margin-top: 12px"
      />
    </div>

    <!-- 流程节点列表 -->
    <div class="nodes-section">
      <div class="section-header">
        <span class="section-title">流程节点</span>
        <span class="node-count">{{ nodes.length }} 个节点</span>
      </div>

      <div v-if="nodes.length === 0" class="empty-nodes">
        <el-icon :size="48" color="#c0c4cc"><Connection /></el-icon>
        <p>暂无流程节点</p>
        <p class="tip">点击下方按钮添加节点</p>
      </div>

      <div v-else class="node-list">
        <div v-for="(node, index) in nodes" :key="index" class="node-item">
          <div class="node-index">{{ index + 1 }}</div>
          <div class="node-info">
            <div class="node-name">{{ node.name || '未命名节点' }}</div>
            <div class="node-meta">
              <el-tag size="small" :type="getNodeTypeColor(node.type)">
                {{ getNodeTypeLabel(node.type) }}
              </el-tag>
            </div>
          </div>
          <div class="node-actions">
            <el-icon @click="editNode(index)"><Edit /></el-icon>
            <el-icon @click="deleteNode(index)"><Delete /></el-icon>
          </div>
        </div>

        <!-- 连接线指示 -->
        <div class="connection-indicator" v-if="nodes.length > 1">
          <div class="connection-line"></div>
          <span class="connection-text">{{ nodes.length - 1 }} 个连接</span>
        </div>
      </div>
    </div>

    <!-- 添加节点按钮 -->
    <div class="add-node-section">
      <div class="quick-add-buttons">
        <el-button @click="addNode('start')" plain size="small">
          <el-icon><VideoPlay /></el-icon> 开始
        </el-button>
        <el-button @click="addNode('approval')" type="primary" plain size="small">
          <el-icon><User /></el-icon> 审批节点
        </el-button>
        <el-button @click="addNode('condition')" type="warning" plain size="small">
          <el-icon><Connection /></el-icon> 条件节点
        </el-button>
        <el-button @click="addNode('end')" plain size="small">
          <el-icon><VideoPause /></el-icon> 结束
        </el-button>
      </div>
      <el-button type="primary" style="width: 100%; margin-top: 12px" @click="showNodeDialog">
        <el-icon><Plus /></el-icon> 添加更多节点
      </el-button>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-actions">
      <el-button @click="previewWorkflow">
        <el-icon><View /></el-icon> 预览
      </el-button>
      <el-button type="success" @click="publishWorkflow" :loading="publishing">
        <el-icon><Promotion /></el-icon> {{ workflowData?.is_active ? '已启用' : '启用流程' }}
      </el-button>
    </div>

    <!-- 添加/编辑节点对话框 -->
    <el-dialog
      v-model="showNodeDialogRef"
      :title="editingNodeIndex >= 0 ? '编辑节点' : '添加节点'"
      width="90%"
      :close-on-click-modal="false"
    >
      <el-form :model="nodeForm" label-position="top">
        <el-form-item label="节点名称" required>
          <el-input v-model="nodeForm.name" placeholder="请输入节点名称" />
        </el-form-item>
        <el-form-item label="节点类型" required>
          <el-select v-model="nodeForm.type" placeholder="选择节点类型" style="width: 100%">
            <el-option label="开始节点" value="start" />
            <el-option label="审批节点" value="approval" />
            <el-option label="条件节点" value="condition" />
            <el-option label="填写节点" value="form" />
            <el-option label="通知节点" value="notification" />
            <el-option label="结束节点" value="end" />
          </el-select>
        </el-form-item>

        <!-- 审批节点配置 -->
        <template v-if="nodeForm.type === 'approval'">
          <el-form-item label="审批人类型">
            <el-select v-model="nodeForm.config.approverType" style="width: 100%">
              <el-option label="指定人员" value="user" />
              <el-option label="部门负责人" value="dept_leader" />
              <el-option label="发起人自选" value="self_select" />
            </el-select>
          </el-form-item>
          <el-form-item label="指定审批人" v-if="nodeForm.config.approverType === 'user'">
            <el-input v-model="nodeForm.config.approverName" placeholder="请输入审批人姓名" />
          </el-form-item>
        </template>

        <!-- 条件节点配置 -->
        <template v-if="nodeForm.type === 'condition'">
          <el-form-item label="条件表达式">
            <el-input
              v-model="nodeForm.config.expression"
              type="textarea"
              :rows="2"
              placeholder="如: field == 'value'"
            />
          </el-form-item>
        </template>

        <!-- 通知节点配置 -->
        <template v-if="nodeForm.type === 'notification'">
          <el-form-item label="通知内容">
            <el-input
              v-model="nodeForm.config.message"
              type="textarea"
              :rows="2"
              placeholder="请输入通知内容"
            />
          </el-form-item>
        </template>

        <el-form-item label="节点描述">
          <el-input
            v-model="nodeForm.description"
            type="textarea"
            :rows="2"
            placeholder="节点说明（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNodeDialogRef = false">取消</el-button>
        <el-button type="primary" @click="saveNode">确定</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreview" title="流程预览" width="95%">
      <div class="preview-workflow">
        <div v-for="(node, index) in nodes" :key="index" class="preview-node">
          <div class="preview-node-content">
            <div class="preview-node-index">{{ index + 1 }}</div>
            <div class="preview-node-info">
              <div class="preview-node-name">{{ node.name }}</div>
              <el-tag size="small" :type="getNodeTypeColor(node.type)">
                {{ getNodeTypeLabel(node.type) }}
              </el-tag>
            </div>
          </div>
          <div v-if="index < nodes.length - 1" class="preview-connector">
            <div class="connector-line"></div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Plus, Edit, Delete, Connection, View, Promotion,
  VideoPlay, VideoPause, User
} from '@element-plus/icons-vue'
import { workflowAPI } from '../../common/api'

const route = useRoute()
const router = useRouter()

const workflowId = computed(() => route.params.id ? Number(route.params.id) : null)
const workflowName = ref('')
const workflowType = ref('approval')
const workflowDescription = ref('')
const workflowData = ref<any>(null)
const nodes = ref<any[]>([])
const saving = ref(false)
const publishing = ref(false)
const showNodeDialogRef = ref(false)
const showPreview = ref(false)
const editingNodeIndex = ref(-1)

const nodeForm = ref({
  name: '',
  type: 'approval',
  description: '',
  config: {
    approverType: 'user',
    approverName: '',
    expression: '',
    message: ''
  }
})

function goBack() {
  router.back()
}

async function loadWorkflow() {
  if (!workflowId.value) {
    // 新建流程，添加默认开始和结束节点
    nodes.value = [
      { id: 1, name: '开始', type: 'start', config: {} },
      { id: 2, name: '结束', type: 'end', config: {} }
    ]
    return
  }

  try {
    const res = await workflowAPI.get(workflowId.value)
    workflowData.value = res
    workflowName.value = res.name || ''
    workflowType.value = res.type || 'approval'
    workflowDescription.value = res.description || ''

    // 解析 nodes
    if (res.nodes && res.nodes.length > 0) {
      nodes.value = res.nodes
    }
  } catch (error) {
    console.error('加载流程失败:', error)
  }
}

async function saveWorkflow() {
  if (!workflowName.value.trim()) {
    ElMessage.warning('请输入流程名称')
    return
  }

  saving.value = true
  try {
    const data = {
      name: workflowName.value,
      type: workflowType.value,
      description: workflowDescription.value,
      nodes: nodes.value.map((n, i) => ({
        ...n,
        position: i
      }))
    }

    if (workflowId.value) {
      await workflowAPI.update(workflowId.value, data)
      ElMessage.success('保存成功')
    } else {
      const res = await workflowAPI.create(data)
      ElMessage.success('创建成功')
      router.replace(`/app/workflow-designer/${res.id}`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function publishWorkflow() {
  if (!workflowId.value) {
    ElMessage.warning('请先保存流程')
    return
  }

  publishing.value = true
  try {
    await workflowAPI.enable(workflowId.value)
    workflowData.value.is_active = true
    ElMessage.success('流程已启用')
  } catch (error: any) {
    ElMessage.error(error.message || '启用失败')
  } finally {
    publishing.value = false
  }
}

function previewWorkflow() {
  if (nodes.value.length < 2) {
    ElMessage.warning('流程至少需要开始和结束节点')
    return
  }
  showPreview.value = true
}

function addNode(type: string) {
  editingNodeIndex.value = -1
  const typeLabels: Record<string, string> = {
    start: '开始节点',
    approval: '审批节点',
    condition: '条件节点',
    end: '结束节点'
  }
  nodeForm.value = {
    name: typeLabels[type] || '新节点',
    type: type,
    description: '',
    config: {
      approverType: 'user',
      approverName: '',
      expression: '',
      message: ''
    }
  }

  // 在倒数第二个位置插入（结束节点之前）
  const endIndex = nodes.value.findIndex(n => n.type === 'end')
  if (endIndex >= 0) {
    nodes.value.splice(endIndex, 0, {
      id: Date.now(),
      ...nodeForm.value
    })
  } else {
    nodes.value.push({
      id: Date.now(),
      ...nodeForm.value
    })
  }
  ElMessage.success('已添加节点')
}

function showNodeDialog() {
  editingNodeIndex.value = -1
  nodeForm.value = {
    name: '',
    type: 'approval',
    description: '',
    config: {
      approverType: 'user',
      approverName: '',
      expression: '',
      message: ''
    }
  }
  showNodeDialogRef.value = true
}

function editNode(index: number) {
  editingNodeIndex.value = index
  const node = nodes.value[index]
  nodeForm.value = {
    name: node.name || '',
    type: node.type || 'approval',
    description: node.description || '',
    config: {
      approverType: node.config?.approverType || 'user',
      approverName: node.config?.approverName || '',
      expression: node.config?.expression || '',
      message: node.config?.message || ''
    }
  }
  showNodeDialogRef.value = true
}

function deleteNode(index: number) {
  const node = nodes.value[index]
  if (node.type === 'start' || node.type === 'end') {
    ElMessage.warning('不能删除开始和结束节点')
    return
  }
  nodes.value.splice(index, 1)
  ElMessage.success('已删除节点')
}

function saveNode() {
  if (!nodeForm.value.name.trim()) {
    ElMessage.warning('请输入节点名称')
    return
  }

  if (editingNodeIndex.value >= 0) {
    nodes.value[editingNodeIndex.value] = {
      id: nodes.value[editingNodeIndex.value].id,
      ...nodeForm.value
    }
    ElMessage.success('节点已更新')
  }

  showNodeDialogRef.value = false
}

function getNodeTypeLabel(type: string) {
  const labels: Record<string, string> = {
    start: '开始',
    approval: '审批',
    condition: '条件',
    form: '填写',
    notification: '通知',
    end: '结束'
  }
  return labels[type] || type
}

function getNodeTypeColor(type: string) {
  const colors: Record<string, string> = {
    start: 'success',
    approval: 'primary',
    condition: 'warning',
    form: 'info',
    notification: '',
    end: 'danger'
  }
  return colors[type] || 'info'
}

onMounted(() => {
  loadWorkflow()
})
</script>

<style scoped>
.mobile-workflow-designer {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 120px;
}

.designer-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409EFF;
  cursor: pointer;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right {
  display: flex;
  gap: 8px;
}

.workflow-info-section {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
}

.workflow-type-select {
  margin-top: 12px;
}

.nodes-section {
  background: white;
  padding: 16px;
  min-height: 300px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
}

.node-count {
  font-size: 12px;
  color: #909399;
}

.empty-nodes {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-nodes p {
  margin: 12px 0 0;
}

.empty-nodes .tip {
  font-size: 12px;
  color: #c0c4cc;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #eee;
}

.node-index {
  width: 28px;
  height: 28px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.node-info {
  flex: 1;
}

.node-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.node-meta {
  display: flex;
  gap: 8px;
}

.node-actions {
  display: flex;
  gap: 12px;
  color: #909399;
}

.node-actions .el-icon {
  cursor: pointer;
  font-size: 18px;
}

.node-actions .el-icon:hover {
  color: #409EFF;
}

.connection-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
}

.connection-line {
  width: 2px;
  height: 20px;
  background: #dcdfe6;
}

.connection-text {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 8px;
}

.add-node-section {
  padding: 16px;
  background: white;
  margin-top: 12px;
}

.quick-add-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.bottom-actions {
  position: fixed;
  bottom: 60px;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 99;
}

.bottom-actions .el-button {
  flex: 1;
}

.preview-workflow {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-node {
  width: 100%;
  max-width: 280px;
}

.preview-node-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e6e6e6;
  border-radius: 8px;
}

.preview-node-index {
  width: 24px;
  height: 24px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
}

.preview-node-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-node-name {
  font-size: 14px;
  color: #303133;
}

.preview-connector {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.connector-line {
  width: 2px;
  height: 24px;
  background: #dcdfe6;
  position: relative;
}

.connector-line::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 6px solid #dcdfe6;
}
</style>
