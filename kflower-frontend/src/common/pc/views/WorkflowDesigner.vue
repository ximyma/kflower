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
          <el-form label-width="80px">
            <el-form-item label="节点名称">
              <el-input v-model="selectedNodeData.name" />
            </el-form-item>
            <el-form-item label="节点描述">
              <el-input v-model="selectedNodeData.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="执行人">
              <el-select v-model="selectedNodeData.assignee" placeholder="选择执行人">
                <el-option label="发起人" value="initiator" />
                <el-option label="部门主管" value="manager" />
                <el-option label="指定人员" value="assignee" />
              </el-select>
            </el-form-item>
            <el-form-item label="条件设置" v-if="selectedNodeData.type === 'condition'">
              <el-input v-model="selectedNodeData.condition" placeholder="如: amount > 1000" />
            </el-form-item>
          </el-form>
          
          <el-divider />
          
          <el-button type="danger" @click="deleteNode">删除节点</el-button>
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
  Check, CircleCheck, View, User, OfficeBuilding,
  Check as CheckIcon, Close, Timer, Connection
} from '@element-plus/icons-vue'

interface WorkflowNode {
  id: string
  type: string
  name: string
  description?: string
  x: number
  y: number
  assignee?: string
  condition?: string
}

interface Connection {
  id: string
  from: string
  to: string
  path: string
}

const route = useRoute()
const router = useRouter()
const workflowId = route.params.id as string
const workflowName = ref('新建流程')

const canvasRef = ref<HTMLElement>()
const connectionsSvg = ref<SVGSVGElement>()

// 节点类型
const nodeTypes = [
  { type: 'start', name: '开始节点', icon: 'CircleCheck' },
  { type: 'task', name: '审批任务', icon: 'User' },
  { type: 'condition', name: '条件分支', icon: 'Connection' },
  { type: 'parallel', name: '并行分支', icon: 'OfficeBuilding' },
  { type: 'end', name: '结束节点', icon: 'Close' }
]

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

// 获取节点图标
const getNodeIcon = (type: string) => {
  const icons: Record<string, string> = {
    start: 'CircleCheck',
    task: 'User',
    condition: 'Connection',
    parallel: 'OfficeBuilding',
    end: 'Close'
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
    // TODO: 调用API保存
    ElMessage.success('流程保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
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
</style>
