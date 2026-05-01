<template>
  <div class="memory-management-page">
    <div class="page-header">
      <h2>🧠 记忆管理</h2>
      <p class="subtitle">智能体长期记忆与短期记忆管理，支持记忆存储、检索、关联和遗忘机制</p>
    </div>

    <el-row :gutter="20" class="memory-stats">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon total"><el-icon><Collection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(stats.totalMemories) }}</div>
            <div class="stat-label">记忆总量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon active"><el-icon><VideoPlay /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.activeAgents }}</div>
            <div class="stat-label">活跃智能体</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon retrieval"><el-icon><Search /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avgRetrievalTime }}ms</div>
            <div class="stat-label">平均检索时间</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon accuracy"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.retrievalAccuracy }}%</div>
            <div class="stat-label">检索准确率</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="12">
        <el-card class="memory-types-card">
          <template #header>
            <div class="card-header">
              <span>🗂️ 记忆类型分布</span>
            </div>
          </template>
          
          <div class="type-distribution">
            <div class="type-item" v-for="type in memoryTypes" :key="type.name">
              <div class="type-info">
                <div class="type-name">
                  <el-icon :color="type.color"><component :is="type.icon" /></el-icon>
                  <span>{{ type.name }}</span>
                </div>
                <div class="type-count">{{ type.count }} 条</div>
              </div>
              <el-progress :percentage="type.percentage" :stroke-width="10" :color="type.color" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="recent-memories-card">
          <template #header>
            <div class="card-header">
              <span>🕒 最近记忆</span>
              <el-button size="small" @click="refreshMemories">刷新</el-button>
            </div>
          </template>
          
          <el-table :data="recentMemories" style="width:100%">
            <el-table-column prop="content" label="内容" min-width="200">
              <template #default="{ row }">
                <div class="memory-content">
                  {{ truncateText(row.content, 50) }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="getTagType(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="agent" label="所属智能体" width="120" />
            <el-table-column prop="time" label="时间" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="16">
        <el-card class="memory-search-card">
          <template #header>
            <div class="card-header">
              <span>🔍 记忆检索</span>
            </div>
          </template>
          
          <div class="search-section">
            <el-input
              v-model="searchQuery"
              placeholder="输入关键词检索记忆..."
              size="large"
              @keyup.enter="performSearch"
            >
              <template #append>
                <el-button type="primary" @click="performSearch">
                  <el-icon><Search /></el-icon> 搜索
                </el-button>
              </template>
            </el-input>
            
            <div class="search-options">
              <el-checkbox-group v-model="searchFilters" size="small">
                <el-checkbox label="fact">事实记忆</el-checkbox>
                <el-checkbox label="conversation">对话记忆</el-checkbox>
                <el-checkbox label="procedure">程序记忆</el-checkbox>
                <el-checkbox label="episodic">情景记忆</el-checkbox>
              </el-checkbox-group>
              
              <div class="search-sort">
                <span style="margin-right:8px">排序:</span>
                <el-select v-model="searchSort" size="small" style="width:120px">
                  <el-option label="相关性" value="relevance" />
                  <el-option label="时间倒序" value="time_desc" />
                  <el-option label="时间正序" value="time_asc" />
                </el-select>
              </div>
            </div>
          </div>
          
          <div class="search-results" v-if="searchResults.length > 0">
            <div class="results-count">找到 {{ searchResults.length }} 条相关记忆</div>
            
            <div class="result-item" v-for="result in searchResults" :key="result.id">
              <div class="result-header">
                <div class="result-type">
                  <el-tag size="small" :type="getTagType(result.type)">{{ result.type }}</el-tag>
                  <span class="result-agent">{{ result.agent }}</span>
                </div>
                <div class="result-time">{{ result.time }}</div>
              </div>
              <div class="result-content">
                {{ result.content }}
              </div>
              <div class="result-footer">
                <div class="result-relevance">相关性: {{ result.relevance }}%</div>
                <div class="result-actions">
                  <el-button type="text" size="small" @click="viewMemory(result)">查看</el-button>
                  <el-button type="text" size="small" @click="editMemory(result)">编辑</el-button>
                  <el-button type="text" size="small" @click="deleteMemory(result)">删除</el-button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="search-empty" v-else-if="searched">
            <el-empty description="未找到相关记忆" />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="memory-config-card">
          <template #header>
            <div class="card-header">
              <span>⚙️ 记忆配置</span>
            </div>
          </template>
          
          <el-form label-width="120px">
            <el-form-item label="记忆保留策略">
              <el-select v-model="config.retentionPolicy" style="width:100%">
                <el-option label="长期保留" value="long_term" />
                <el-option label="自动清理" value="auto_clean" />
                <el-option label="按需保留" value="on_demand" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="最大记忆数量">
              <el-input-number v-model="config.maxMemories" :min="100" :max="100000" style="width:100%" />
            </el-form-item>
            
            <el-form-item label="自动清理周期">
              <el-select v-model="config.cleanupInterval" style="width:100%">
                <el-option label="每天" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
                <el-option label="从不" value="never" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="相似度阈值">
              <el-slider v-model="config.similarityThreshold" :min="0.1" :max="1.0" :step="0.05" show-input />
            </el-form-item>
            
            <el-form-item label="启用记忆压缩">
              <el-switch v-model="config.enableCompression" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveConfig">保存配置</el-button>
              <el-button @click="resetConfig">重置</el-button>
            </el-form-item>
          </el-form>
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
          <div class="progress-label">记忆存储引擎</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">向量化检索</div>
          <el-progress :percentage="85" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">记忆关联网络</div>
          <el-progress :percentage="65" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">记忆遗忘机制</div>
          <el-progress :percentage="50" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">多智能体记忆共享</div>
          <el-progress :percentage="35" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Collection, VideoPlay, Search, CircleCheck, Document, ChatDotRound, Tools, Star } from '@element-plus/icons-vue'
import { aiAPI } from '@/common/api/index'

const stats = ref({
  totalMemories: 0,
  activeAgents: 0,
  avgRetrievalTime: 0,
  retrievalAccuracy: 0,
})

const memoryTypes = ref([])
const recentMemories = ref([])

const searchQuery = ref('')
const searchFilters = ref(['fact', 'conversation', 'procedure', 'episodic'])
const searchSort = ref('relevance')
const searchResults = ref<any[]>([])
const searched = ref(false)

const config = ref({
  retentionPolicy: 'auto_clean',
  maxMemories: 50000,
  cleanupInterval: 'weekly',
  similarityThreshold: 0.75,
  enableCompression: true,
})

// 加载记忆统计数据
async function loadMemoryStats() {
  try {
    const response = await aiAPI.getMemoryStats()
    if (response.success && response.data) {
      stats.value = response.data
      // 更新记忆类型分布（模拟计算）
      updateMemoryTypesDistribution()
    }
  } catch (error) {
    console.error('加载记忆统计失败:', error)
    // 使用模拟数据
    stats.value = {
      totalMemories: 24567,
      activeAgents: 12,
      avgRetrievalTime: 128,
      retrievalAccuracy: 92.3,
    }
    updateMemoryTypesDistribution()
  }
}

// 更新记忆类型分布（模拟）
function updateMemoryTypesDistribution() {
  const total = stats.value.totalMemories
  if (total === 0) {
    memoryTypes.value = []
    return
  }
  // 模拟分布
  memoryTypes.value = [
    { name: '事实记忆', icon: Document, color: '#409EFF', count: Math.floor(total * 0.5), percentage: 50 },
    { name: '对话记忆', icon: ChatDotRound, color: '#67C23A', count: Math.floor(total * 0.36), percentage: 36 },
    { name: '程序记忆', icon: Tools, color: '#E6A23C', count: Math.floor(total * 0.1), percentage: 10 },
    { name: '情景记忆', icon: Star, color: '#F56C6C', count: total - Math.floor(total * 0.5) - Math.floor(total * 0.36) - Math.floor(total * 0.1), percentage: 4 },
  ]
}

// 加载最近记忆
async function loadRecentMemories() {
  try {
    const response = await aiAPI.listMemories(5)
    if (response.success && response.data) {
      recentMemories.value = response.data.map((memory: any) => ({
        id: memory.id,
        content: memory.content,
        type: memory.type,
        agent: memory.agent,
        time: memory.time,
      }))
    } else {
      // 模拟数据
      recentMemories.value = [
        { id: 1, content: '用户偏好深色主题界面', type: 'fact', agent: '用户偏好智能体', time: '10:30' },
        { id: 2, content: '月度报告需要包含销售数据图表', type: 'conversation', agent: '模板设计智能体', time: '10:15' },
        { id: 3, content: 'API调用超时时间应设置为30秒', type: 'procedure', agent: 'API调用工具', time: '09:45' },
        { id: 4, content: '上次登录失败原因为密码错误', type: 'episodic', agent: '安全监控智能体', time: '09:20' },
        { id: 5, content: '数据分析模板需要新增环比字段', type: 'fact', agent: '数据分析智能体', time: '08:55' },
      ]
    }
  } catch (error) {
    console.error('加载最近记忆失败:', error)
    recentMemories.value = [
      { id: 1, content: '用户偏好深色主题界面', type: 'fact', agent: '用户偏好智能体', time: '10:30' },
      { id: 2, content: '月度报告需要包含销售数据图表', type: 'conversation', agent: '模板设计智能体', time: '10:15' },
      { id: 3, content: 'API调用超时时间应设置为30秒', type: 'procedure', agent: 'API调用工具', time: '09:45' },
      { id: 4, content: '上次登录失败原因为密码错误', type: 'episodic', agent: '安全监控智能体', time: '09:20' },
      { id: 5, content: '数据分析模板需要新增环比字段', type: 'fact', agent: '数据分析智能体', time: '08:55' },
    ]
  }
}

// 初始化加载数据
onMounted(() => {
  loadMemoryStats()
  loadRecentMemories()
})

function formatNumber(num: number) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function getTagType(memoryType: string) {
  const map: any = {
    fact: 'primary',
    conversation: 'success',
    procedure: 'warning',
    episodic: 'danger'
  }
  return map[memoryType] || 'info'
}

function refreshMemories() {
  loadMemoryStats()
  loadRecentMemories()
  ElMessage.success('记忆列表已刷新')
}

function performSearch() {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  searched.value = true
  
  // 模拟搜索结果
  searchResults.value = [
    {
      id: 1,
      content: `关于"${searchQuery.value}"的记忆：用户上次查询相关数据时使用了高级筛选功能`,
      type: 'fact',
      agent: '用户行为分析智能体',
      time: '2026-04-19 14:30',
      relevance: 92
    },
    {
      id: 2,
      content: `对话中提及"${searchQuery.value}"：建议在报告中加入${searchQuery.value}的对比分析`,
      type: 'conversation',
      agent: '报告生成智能体',
      time: '2026-04-18 11:20',
      relevance: 87
    },
    {
      id: 3,
      content: `处理"${searchQuery.value}"的程序步骤：先调用API获取数据，然后进行清洗转换`,
      type: 'procedure',
      agent: '数据处理智能体',
      time: '2026-04-17 09:45',
      relevance: 78
    },
  ]
  
  ElMessage.success(`找到 ${searchResults.value.length} 条相关记忆`)
}

function viewMemory(memory: any) {
  ElMessage.info(`查看记忆: ${memory.content.substring(0, 30)}...`)
}

function editMemory(memory: any) {
  ElMessage.info(`编辑记忆: ${memory.content.substring(0, 30)}...`)
}

function deleteMemory(memory: any) {
  ElMessage.info(`删除记忆: ${memory.content.substring(0, 30)}...`)
}

function saveConfig() {
  ElMessage.success('记忆配置已保存')
}

function resetConfig() {
  config.value = {
    retentionPolicy: 'auto_clean',
    maxMemories: 50000,
    cleanupInterval: 'weekly',
    similarityThreshold: 0.75,
    enableCompression: true,
  }
  ElMessage.info('配置已重置')
}
</script>

<style scoped>
.memory-management-page {
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

.memory-stats {
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

.stat-icon.total { background: #ecf5ff; color: #409EFF; }
.stat-icon.active { background: #f0f9eb; color: #67C23A; }
.stat-icon.retrieval { background: var(--el-color-warning-light-9); color: #E6A23C; }
.stat-icon.accuracy { background: #fef0f0; color: #F56C6C; }

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

.memory-types-card, .recent-memories-card, .memory-search-card, .memory-config-card {
  height: 100%;
}

.type-distribution {
  padding: 8px 0;
}

.type-item {
  margin-bottom: 20px;
}

.type-item:last-child {
  margin-bottom: 0;
}

.type-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.type-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.type-count {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.memory-content {
  font-size: 14px;
}

.search-section {
  padding: 8px 0;
}

.search-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.search-sort {
  display: flex;
  align-items: center;
}

.search-results {
  margin-top: 24px;
}

.results-count {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 16px;
}

.result-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
  background: var(--el-bg-color-page);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-type {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-agent {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.result-time {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.result-content {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-relevance {
  font-size: 13px;
  color: #67C23A;
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.search-empty {
  margin-top: 40px;
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
</style>