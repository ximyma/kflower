<template>
  <div class="plugin-market">
    <!-- Header -->
    <div class="pm-header">
      <div class="pm-title">
        <h2>插件市场</h2>
        <p class="pm-subtitle">发现和安装插件，扩展您的系统功能</p>
      </div>
    </div>

    <!-- Filter & Search -->
    <div class="pm-toolbar">
      <div class="search-box">
        <el-input v-model="searchKeyword" placeholder="搜索插件..." clearable>
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
      <div class="filter-tabs">
        <el-tabs v-model="activeCategory" @tab-change="loadPlugins">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="AI工具" name="ai_tool" />
          <el-tab-pane label="集成" name="integration" />
          <el-tab-pane label="工作流" name="workflow" />
          <el-tab-pane label="数据处理" name="data" />
          <el-tab-pane label="自定义" name="custom" />
        </el-tabs>
      </div>
    </div>

    <!-- Stats -->
    <div class="pm-stats">
      <div class="stat-item">
        <span class="stat-value">{{ stats.total }}</span>
        <span class="stat-label">全部插件</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.installed }}</span>
        <span class="stat-label">已安装</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.enabled }}</span>
        <span class="stat-label">已启用</span>
      </div>
    </div>

    <!-- Plugin Grid -->
    <div v-if="loading" class="pm-loading">
      <el-icon class="is-loading"><Loading /></el-icon> 加载中...
    </div>
    <div v-else-if="plugins.length === 0" class="pm-empty">
      <el-empty description="暂无插件" :image-size="80" />
    </div>
    <div v-else class="pm-grid">
      <div v-for="plugin in plugins" :key="plugin.id" class="plugin-card">
        <div class="plugin-card-header">
          <div class="plugin-icon" :class="plugin.category">
            <span>{{ getIconEmoji(plugin.icon) }}</span>
          </div>
          <div class="plugin-info">
            <div class="plugin-name">{{ plugin.display_name }}</div>
            <div class="plugin-category">
              <el-tag size="small" :type="getCategoryType(plugin.category)">
                {{ getCategoryLabel(plugin.category) }}
              </el-tag>
              <el-tag v-if="plugin.is_built_in" size="small" type="warning">内置</el-tag>
            </div>
          </div>
          <div class="plugin-status">
            <el-tag v-if="plugin.is_installed" :type="plugin.is_enabled ? 'success' : 'info'">
              {{ plugin.is_enabled ? '已启用' : '已安装' }}
            </el-tag>
          </div>
        </div>
        
        <div class="plugin-card-body">
          <p class="plugin-description">{{ plugin.description || '暂无描述' }}</p>
          <div class="plugin-meta">
            <span class="meta-item">
              <el-icon size="14"><User /></el-icon>
              {{ plugin.author || '未知' }}
            </span>
            <span class="meta-item">
              <el-icon size="14"><Box /></el-icon>
              {{ plugin.version || '1.0.0' }}
            </span>
          </div>
          <div class="plugin-hooks">
            <span class="hooks-label">钩子:</span>
            <span v-for="hook in (plugin.hook_events || []).slice(0, 3)" :key="hook" class="hook-tag">
              {{ hook }}
            </span>
            <span v-if="(plugin.hook_events || []).length > 3" class="hook-more">
              +{{ (plugin.hook_events || []).length - 3 }}
            </span>
          </div>
        </div>

        <div class="plugin-card-footer">
          <div class="plugin-score">
            <el-rate disabled :model-value="plugin.score || 0" show-score text-color="#ff9900" />
            <span class="score-text">({{ plugin.download_count || 0 }}次下载)</span>
          </div>
          <div class="plugin-actions">
            <el-button v-if="!plugin.is_installed" size="small" type="primary" @click="installPlugin(plugin)">
              <el-icon><Download /></el-icon> 安装
            </el-button>
            <el-button v-else-if="!plugin.is_enabled" size="small" type="success" @click="enablePlugin(plugin)">
                <el-icon><Check /></el-icon> 启用
              </el-button>
            <el-button v-else size="small" type="warning" @click="disablePlugin(plugin)">
              <el-icon><CircleClose /></el-icon> 禁用
            </el-button>
            <el-button size="small" @click="openDetail(plugin)">详情</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetailDialog" :title="selectedPlugin?.display_name || '插件详情'" width="600px">
      <div v-if="selectedPlugin" class="detail-content">
        <div class="detail-header">
          <div class="detail-icon" :class="selectedPlugin.category">
            <span>{{ getIconEmoji(selectedPlugin.icon) }}</span>
          </div>
          <div class="detail-info">
            <h3>{{ selectedPlugin.display_name }}</h3>
            <div class="detail-tags">
              <el-tag :type="getCategoryType(selectedPlugin.category)">
                {{ getCategoryLabel(selectedPlugin.category) }}
              </el-tag>
              <el-tag v-if="selectedPlugin.is_built_in" type="warning">内置</el-tag>
              <el-tag :type="selectedPlugin.is_enabled ? 'success' : 'info'">
                {{ selectedPlugin.is_enabled ? '已启用' : '已禁用' }}
              </el-tag>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="detail-section">
          <h4>插件描述</h4>
          <p>{{ selectedPlugin.description || '暂无描述' }}</p>
        </div>

        <div class="detail-section">
          <h4>技术信息</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="版本">{{ selectedPlugin.version || '1.0.0' }}</el-descriptions-item>
            <el-descriptions-item label="作者">{{ selectedPlugin.author || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ getCategoryLabel(selectedPlugin.category) }}</el-descriptions-item>
            <el-descriptions-item label="下载量">{{ selectedPlugin.download_count || 0 }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-section">
          <h4>支持的钩子事件</h4>
          <div class="hooks-list">
            <el-tag v-for="hook in (selectedPlugin.hook_events || [])" :key="hook" size="small">
              {{ hook }}
            </el-tag>
            <span v-if="!(selectedPlugin.hook_events || []).length">无</span>
          </div>
        </div>

        <div class="detail-section">
          <h4>配置参数</h4>
          <pre class="config-json">{{ JSON.stringify(selectedPlugin.config || {}, null, 2) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button v-if="selectedPlugin?.is_installed" :type="selectedPlugin?.is_enabled ? 'warning' : 'success'" @click="togglePlugin(selectedPlugin)">
          {{ selectedPlugin?.is_enabled ? '禁用' : '启用' }}
        </el-button>
        <el-button v-else type="primary" :loading="installing" @click="installPlugin(selectedPlugin)">安装</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Loading, User, Box, Download, Check, CircleClose } from '@element-plus/icons-vue'
import api from '../../common/api/index'

const searchKeyword = ref('')
const activeCategory = ref('all')
const loading = ref(false)
const plugins = ref<any[]>([])
const installing = ref(false)

const stats = reactive({
  total: 0,
  installed: 0,
  enabled: 0
})

const selectedPlugin = ref<any>(null)
const showDetailDialog = ref(false)

const iconEmojis: Record<string, string> = {
  'settings': '⚙️',
  'plug': '🔌',
  'puzzle-piece': '🧩',
  'box': '📦',
  'zap': '⚡',
  'bell': '🔔',
  'bar-chart': '📊',
  'wrench': '🔧'
}

const categoryLabels: Record<string, string> = {
  'custom': '自定义',
  'ai_tool': 'AI工具',
  'integration': '集成',
  'workflow': '工作流',
  'data': '数据处理',
  'builtin': '内置'
}

const categoryTypes: Record<string, string> = {
  'custom': 'info',
  'ai_tool': 'primary',
  'integration': 'success',
  'workflow': 'warning',
  'data': 'danger',
  'builtin': 'warning'
}

function getIconEmoji(icon: string) {
  return iconEmojis[icon] || '🧩'
}

function getCategoryLabel(category: string) {
  return categoryLabels[category] || category
}

function getCategoryType(category: string) {
  return categoryTypes[category] || 'info'
}

async function loadPlugins() {
  loading.value = true
  try {
    const params: any = {}
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (activeCategory.value !== 'all') {
      params.category = activeCategory.value
    }
    const res = await api.get('/plugins/', { params })
    if (res.success) {
      plugins.value = res.data || []
      calcStats()
    }
  } catch (e: any) {
    ElMessage.error('加载插件失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function calcStats() {
  stats.total = plugins.value.length
  stats.installed = plugins.value.filter(p => p.is_installed).length
  stats.enabled = plugins.value.filter(p => p.is_enabled).length
}

function openDetail(plugin: any) {
  selectedPlugin.value = plugin
  showDetailDialog.value = true
}

async function installPlugin(plugin: any) {
  installing.value = true
  try {
    await api.post(`/plugins/${plugin.id}/install`)
    ElMessage.success('插件安装成功')
    plugin.is_installed = true
    plugin.is_enabled = true
    calcStats()
    showDetailDialog.value = false
  } catch (e: any) {
    ElMessage.error('安装失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally {
    installing.value = false
  }
}

async function enablePlugin(plugin: any) {
  try {
    await api.post(`/plugins/${plugin.id}/enable`)
    ElMessage.success('插件已启用')
    plugin.is_enabled = true
    calcStats()
  } catch (e: any) {
    ElMessage.error('启用失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function disablePlugin(plugin: any) {
  try {
    await api.post(`/plugins/${plugin.id}/disable`)
    ElMessage.success('插件已禁用')
    plugin.is_enabled = false
    calcStats()
  } catch (e: any) {
    ElMessage.error('禁用失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  }
}

async function togglePlugin(plugin: any) {
  if (plugin.is_enabled) {
    await disablePlugin(plugin)
  } else {
    await enablePlugin(plugin)
  }
}

onMounted(() => {
  loadPlugins()
})
</script>

<style scoped>
.plugin-market {
  padding: 24px;
  min-height: 100%;
}

.pm-header {
  margin-bottom: 24px;
}

.pm-title h2 {
  margin: 0;
  font-size: 20px;
}

.pm-subtitle {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.pm-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
}

.search-box {
  width: 300px;
}

.filter-tabs {
  flex: 1;
}

.pm-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.pm-loading {
  text-align: center;
  padding: 60px;
}

.pm-empty {
  padding: 40px;
}

.pm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.plugin-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.plugin-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.plugin-card-header {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.plugin-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: var(--el-color-primary-light-9);
}

.plugin-icon.ai_tool { background: #f0f5ff; }
.plugin-icon.integration { background: #f0fdf4; }
.plugin-icon.workflow { background: #fffbeb; }
.plugin-icon.data { background: #fef2f2; }

.plugin-info {
  flex: 1;
}

.plugin-name {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
}

.plugin-category {
  display: flex;
  gap: 6px;
}

.plugin-status {
  margin-left: auto;
}

.plugin-card-body {
  padding: 0 16px;
}

.plugin-description {
  margin: 0 0 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.plugin-hooks {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.hooks-label {
  font-size: 12px;
  color: #909399;
}

.hook-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
}

.hook-more {
  font-size: 12px;
  color: #909399;
}

.plugin-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #f2f6fc;
}

.plugin-score {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-text {
  font-size: 12px;
  color: #909399;
}

.plugin-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  padding: 8px 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.detail-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: var(--el-color-primary-light-9);
}

.detail-icon.ai_tool { background: #f0f5ff; }
.detail-icon.integration { background: #f0fdf4; }
.detail-icon.workflow { background: #fffbeb; }
.detail-icon.data { background: #fef2f2; }

.detail-info h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.detail-tags {
  display: flex;
  gap: 8px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 500;
}

.detail-section p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.hooks-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.config-json {
  background: #1f2937;
  color: #e5e7eb;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .pm-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box {
    width: 100%;
  }
  .pm-grid {
    grid-template-columns: 1fr;
  }
}
</style>