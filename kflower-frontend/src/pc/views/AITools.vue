<template>
  <div class="ai-tools-page">
    <div class="page-header">
      <h2>🛠️ AI工具集</h2>
      <p class="subtitle">为智能体提供丰富的能力扩展，包括数据查询、API调用、文件处理、代码执行等</p>
    </div>

    <div class="tools-filter">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索工具..."
        prefix-icon="Search"
        style="width:300px"
        clearable
      />
      <div class="filter-actions">
        <el-button-group>
          <el-button :type="activeCategory === 'all' ? 'primary' : ''" @click="setCategory('all')">全部</el-button>
          <el-button :type="activeCategory === 'data' ? 'primary' : ''" @click="setCategory('data')">数据操作</el-button>
          <el-button :type="activeCategory === 'api' ? 'primary' : ''" @click="setCategory('api')">API调用</el-button>
          <el-button :type="activeCategory === 'file' ? 'primary' : ''" @click="setCategory('file')">文件处理</el-button>
          <el-button :type="activeCategory === 'code' ? 'primary' : ''" @click="setCategory('code')">代码执行</el-button>
          <el-button :type="activeCategory === 'other' ? 'primary' : ''" @click="setCategory('other')">其他</el-button>
        </el-button-group>
      </div>
    </div>

    <el-row :gutter="20" class="tools-grid">
      <el-col
        v-for="tool in filteredTools"
        :key="tool.id"
        :span="6"
        style="margin-bottom:20px"
      >
        <el-card class="tool-card" :class="{ disabled: !tool.enabled }">
          <template #header>
            <div class="tool-header">
              <div class="tool-icon">
                <el-icon :size="24" :color="tool.enabled ? tool.color : '#909399'">
                  <component :is="tool.icon" />
                </el-icon>
              </div>
              <div class="tool-title">
                <h4>{{ tool.name }}</h4>
                <el-tag size="small" :type="tool.categoryTag">{{ tool.category }}</el-tag>
              </div>
              <div class="tool-actions">
                <el-switch v-model="tool.enabled" size="small" @change="toggleTool(tool)" />
              </div>
            </div>
          </template>
          
          <div class="tool-description">
            {{ tool.description }}
          </div>
          
          <div class="tool-meta">
            <div class="meta-item">
              <el-icon><Clock /></el-icon>
              <span>版本 {{ tool.version }}</span>
            </div>
            <div class="meta-item">
              <el-icon><User /></el-icon>
              <span>{{ tool.usageCount }} 次使用</span>
            </div>
          </div>
          
          <div class="tool-footer">
            <el-button type="primary" size="small" @click="testTool(tool)" :disabled="!tool.enabled">测试</el-button>
            <el-button type="info" size="small" @click="editTool(tool)">配置</el-button>
            <el-button type="text" size="small" @click="viewDocs(tool)">文档</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="tool-registration" style="margin-top:24px">
      <template #header>
        <div class="card-header">
          <span>➕ 工具注册</span>
        </div>
      </template>
      
      <el-form :model="newTool" label-width="100px" :inline="true">
        <el-form-item label="工具名称" required>
          <el-input v-model="newTool.name" placeholder="输入工具名称" style="width:200px" />
        </el-form-item>
        <el-form-item label="工具类型" required>
          <el-select v-model="newTool.category" placeholder="选择类型" style="width:150px">
            <el-option label="数据操作" value="data" />
            <el-option label="API调用" value="api" />
            <el-option label="文件处理" value="file" />
            <el-option label="代码执行" value="code" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具描述" required>
          <el-input v-model="newTool.description" placeholder="工具功能描述" style="width:300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="registerTool">注册新工具</el-button>
        </el-form-item>
      </el-form>
      
      <div class="registration-hint">
        <el-alert title="工具注册说明" type="info" :closable="false" show-icon>
          <p>1. 工具需要实现标准的接口规范</p>
          <p>2. 支持Python函数、HTTP API、命令行等多种形式</p>
          <p>3. 注册后需编写工具描述文档和参数说明</p>
        </el-alert>
      </div>
    </el-card>

    <el-card class="development-info" style="margin-top:24px">
      <template #header>
        <div class="card-header">
          <span>🚀 开发进展</span>
        </div>
      </template>
      <div class="progress-section">
        <div class="progress-item">
          <div class="progress-label">工具框架基础</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具注册与管理</div>
          <el-progress :percentage="85" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具描述语言</div>
          <el-progress :percentage="70" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具自动发现</div>
          <el-progress :percentage="50" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具市场</div>
          <el-progress :percentage="30" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Clock, User, DataBoard, Connection, Document, VideoPlay, Tools, Setting, ChatDotRound, Collection, Upload, Download, Edit, Delete } from '@element-plus/icons-vue'
import { aiAPI } from '@/common/api/index'

const searchKeyword = ref('')
const activeCategory = ref('all')

const tools = ref([])
const newTool = ref({
  name: '',
  category: 'data',
  description: ''
})

// 加载工具列表
async function loadTools() {
  try {
    const response = await aiAPI.getAgentEngineTools()
    if (response.success && response.data) {
      // 转换后端数据格式为前端所需格式
      tools.value = response.data.map((tool: any, index: number) => ({
        id: index + 1,
        name: tool.name,
        category: mapCategory(tool.category),
        categoryTag: getCategoryTag(mapCategory(tool.category)),
        icon: getIconForCategory(tool.category),
        color: getColorForCategory(tool.category),
        description: tool.description,
        version: 'v1.0',
        usageCount: tool.call_count || 0,
        enabled: tool.enabled !== false
      }))
    } else {
      // 如果API返回失败，使用模拟数据
      loadMockTools()
    }
  } catch (error) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载工具列表失败，请检查网络连接')
    loadMockTools()
  }
}

// 模拟数据（备用）
function loadMockTools() {
  tools.value = [
    { id: 1, name: 'SQL查询', category: 'data', categoryTag: 'primary', icon: DataBoard, color: '#409EFF', description: '执行SQL查询，支持多种数据库', version: 'v1.0', usageCount: 1245, enabled: true },
    { id: 2, name: 'API调用', category: 'api', categoryTag: 'success', icon: Connection, color: '#67C23A', description: '调用外部REST API，支持认证和参数化', version: 'v1.2', usageCount: 876, enabled: true },
    { id: 3, name: '文件读取', category: 'file', categoryTag: 'warning', icon: Document, color: '#E6A23C', description: '读取本地文件内容，支持多种格式', version: 'v1.1', usageCount: 543, enabled: true },
    { id: 4, name: 'Python执行', category: 'code', categoryTag: 'danger', icon: VideoPlay, color: '#F56C6C', description: '执行Python代码片段，沙箱环境', version: 'v0.9', usageCount: 321, enabled: false },
    { id: 5, name: '数据转换', category: 'data', categoryTag: 'primary', icon: Tools, color: '#409EFF', description: 'JSON/CSV/Excel格式转换', version: 'v1.0', usageCount: 654, enabled: true },
    { id: 6, name: '邮件发送', category: 'api', categoryTag: 'success', icon: Connection, color: '#67C23A', description: '发送电子邮件，支持附件', version: 'v1.1', usageCount: 234, enabled: true },
    { id: 7, name: 'OCR识别', category: 'file', categoryTag: 'warning', icon: Document, color: '#E6A23C', description: '图片文字识别，支持多语言', version: 'v0.8', usageCount: 123, enabled: false },
    { id: 8, name: '天气查询', category: 'api', categoryTag: 'success', icon: Connection, color: '#67C23A', description: '查询实时天气信息', version: 'v1.0', usageCount: 432, enabled: true },
    { id: 9, name: '文本摘要', category: 'data', categoryTag: 'primary', icon: DataBoard, color: '#409EFF', description: '自动生成文本摘要', version: 'v0.7', usageCount: 198, enabled: true },
    { id: 10, name: '代码生成', category: 'code', categoryTag: 'danger', icon: VideoPlay, color: '#F56C6C', description: '根据描述生成代码片段', version: 'v0.6', usageCount: 89, enabled: false },
    { id: 11, name: '文件上传', category: 'file', categoryTag: 'warning', icon: Upload, color: '#E6A23C', description: '上传文件到指定存储', version: 'v1.0', usageCount: 567, enabled: true },
    { id: 12, name: '数据验证', category: 'data', categoryTag: 'primary', icon: DataBoard, color: '#409EFF', description: '数据格式和完整性验证', version: 'v1.0', usageCount: 345, enabled: true },
  ]
}

// 映射后端分类到前端分类
function mapCategory(backendCategory: string): string {
  const mapping: Record<string, string> = {
    '网络': 'api',
    '工具': 'other',
    '生活': 'api',
    '语言': 'other',
    '数据': 'data',
    '可视化': 'data',
    'api': 'api',
    'data': 'data',
    'file': 'file',
    'code': 'code',
  }
  return mapping[backendCategory] || 'other'
}

// 根据分类获取图标
function getIconForCategory(category: string) {
  const iconMap: Record<string, any> = {
    'data': DataBoard,
    'api': Connection,
    'file': Document,
    'code': VideoPlay,
    'other': Tools
  }
  return iconMap[mapCategory(category)] || Tools
}

// 根据分类获取颜色
function getColorForCategory(category: string) {
  const colorMap: Record<string, string> = {
    'data': '#409EFF',
    'api': '#67C23A',
    'file': '#E6A23C',
    'code': '#F56C6C',
    'other': '#909399'
  }
  return colorMap[mapCategory(category)] || '#909399'
}

// 计算过滤后的工具列表
const filteredTools = computed(() => {
  let result = tools.value
  
  if (activeCategory.value !== 'all') {
    result = result.filter(tool => tool.category === activeCategory.value)
  }
  
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(tool => 
      tool.name.toLowerCase().includes(keyword) || 
      tool.description.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

// 初始化加载数据
onMounted(() => {
  loadTools()
})

function setCategory(category: string) {
  activeCategory.value = category
}

function toggleTool(tool: any) {
  ElMessage.success(`${tool.name} ${tool.enabled ? '已启用' : '已禁用'}`)
}

function testTool(tool: any) {
  ElMessage.info(`测试工具: ${tool.name}`)
}

function editTool(tool: any) {
  ElMessage.info(`配置工具: ${tool.name}`)
}

function viewDocs(tool: any) {
  ElMessage.info(`查看 ${tool.name} 的文档`)
}

function registerTool() {
  if (!newTool.value.name.trim() || !newTool.value.description.trim()) {
    ElMessage.warning('请填写工具名称和描述')
    return
  }
  
  const newId = tools.value.length + 1
  tools.value.push({
    id: newId,
    name: newTool.value.name,
    category: newTool.value.category,
    categoryTag: getCategoryTag(newTool.value.category),
    icon: Tools,
    color: '#909399',
    description: newTool.value.description,
    version: 'v1.0',
    usageCount: 0,
    enabled: true
  })
  
  ElMessage.success(`工具 "${newTool.value.name}" 已注册`)
  
  newTool.value = {
    name: '',
    category: 'data',
    description: ''
  }
}

function getCategoryTag(category: string) {
  const map: any = {
    data: 'primary',
    api: 'success',
    file: 'warning',
    code: 'danger',
    other: 'info'
  }
  return map[category] || 'info'
}
</script>

<style scoped>
.ai-tools-page {
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

.tools-filter {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.tools-grid {
  margin-bottom: 20px;
}

.tool-card {
  height: 100%;
  transition: all 0.3s;
}

.tool-card.disabled {
  opacity: 0.7;
  background: #fafafa;
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tool-icon {
  flex-shrink: 0;
}

.tool-title {
  flex: 1;
}

.tool-title h4 {
  margin: 0 0 4px;
  font-size: 16px;
}

.tool-actions {
  flex-shrink: 0;
}

.tool-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
  line-height: 1.5;
}

.tool-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 12px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tool-footer {
  display: flex;
  justify-content: space-between;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.registration-hint {
  margin-top: 16px;
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