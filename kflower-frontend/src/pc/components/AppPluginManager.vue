<template>
  <div class="app-plugin-manager">
    <!-- Header -->
    <div class="apm-header">
      <div class="apm-header-left">
        <h3>系统插件</h3>
        <el-tag type="info" size="small">{{ boundPlugins.length }} 个已绑定</el-tag>
      </div>
      <el-button type="primary" size="small" @click="openBindDialog">
        <el-icon><Plus /></el-icon> 绑定插件
      </el-button>
    </div>

    <!-- Bound Plugins List -->
    <div v-if="loading" class="apm-loading">
      <el-icon class="is-loading"><Loading /></el-icon> 加载中...
    </div>
    <div v-else-if="boundPlugins.length === 0" class="apm-empty">
      <el-empty description="暂无绑定的系统插件" :image-size="80">
        <template #description>
          <p style="color: #909399; margin-bottom: 12px;">绑定系统插件可以为应用添加计算、通知、审批等高级功能</p>
        </template>
        <el-button type="primary" size="small" @click="openBindDialog">立即绑定插件</el-button>
      </el-empty>
    </div>
    <div v-else class="apm-list">
      <div v-for="bp in boundPlugins" :key="bp.id" class="apm-item">
        <div class="apm-item-icon" :style="{ background: getCategoryColor(bp.category) }">
          <el-icon size="22" color="#fff">
            <component :is="getCategoryIcon(bp.category)" />
          </el-icon>
        </div>
        <div class="apm-item-info">
          <div class="apm-item-name">{{ bp.display_name }}</div>
          <div class="apm-item-meta">
            <el-tag size="small" :type="getCategoryTagType(bp.category)">{{ getCategoryLabel(bp.category) }}</el-tag>
            <el-tag size="small" type="info" v-if="bp.version">v{{ bp.version }}</el-tag>
            <span class="apm-item-hooks" v-if="Object.keys(bp.hook_code || {}).length > 0">
              钩子: {{ Object.keys(bp.hook_code).slice(0, 3).join(', ') }}{{ Object.keys(bp.hook_code).length > 3 ? '...' : '' }}
            </span>
          </div>
          <div class="apm-item-desc" v-if="bp.description">{{ bp.description }}</div>
        </div>
        <div class="apm-item-actions">
          <el-tooltip :content="bp.is_enabled ? '点击禁用' : '点击启用'" placement="top">
            <el-switch v-model="bp.is_enabled" @change="updateBinding(bp)" />
          </el-tooltip>
          <el-button size="small" plain @click="openConfigDialog(bp)">
            <el-icon><Setting /></el-icon>
          </el-button>
          <el-button size="small" type="danger" plain @click="unbindPlugin(bp)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Bind Plugin Dialog -->
    <el-dialog v-model="showBindDialog" title="绑定系统插件" width="680px" @open="loadAvailablePlugins">
      <div class="bind-dialog">
        <div class="bind-toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索插件名称或描述..."
            clearable
            style="width: 240px;"
            @input="debouncedSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="filterCategory" placeholder="全部分类" clearable style="width: 150px;" @change="loadAvailablePlugins">
            <el-option label="全部分类" value="" />
            <el-option label="内置插件" value="builtin" />
            <el-option label="AI 工具" value="ai_tool" />
            <el-option label="自定义插件" value="custom" />
          </el-select>
          <el-tag type="info" size="small">{{ availablePlugins.length }} 个可用</el-tag>
        </div>

        <div v-if="availableLoading" class="bind-loading">
          <el-icon class="is-loading"><Loading /></el-icon> 加载中...
        </div>
        <div v-else-if="availablePlugins.length === 0" class="bind-empty">
          <el-empty description="没有可绑定的插件" :image-size="60">
            <template #description>
              <p style="color: #909399;">
                {{ searchKeyword ? '没有匹配的插件，请更改搜索关键词' : '所有系统插件已绑定，或插件库为空' }}
              </p>
            </template>
          </el-empty>
        </div>
        <div v-else class="bind-list">
          <div
            v-for="plugin in availablePlugins"
            :key="plugin.id"
            class="bind-item"
            :class="{ selected: selectedPlugin?.id === plugin.id }"
            @click="selectedPlugin = plugin"
          >
            <div class="bind-item-icon" :style="{ background: getCategoryColor(plugin.category) }">
              <el-icon size="18" color="#fff">
                <component :is="getCategoryIcon(plugin.category)" />
              </el-icon>
            </div>
            <div class="bind-item-info">
              <div class="bind-item-header">
                <span class="bind-item-name">{{ plugin.display_name }}</span>
                <el-tag size="small" :type="getCategoryTagType(plugin.category)">{{ getCategoryLabel(plugin.category) }}</el-tag>
                <el-tag size="small" type="info" v-if="plugin.version">v{{ plugin.version }}</el-tag>
              </div>
              <div class="bind-item-desc">{{ plugin.description || '暂无描述' }}</div>
              <div class="bind-item-hooks" v-if="Object.keys(plugin.hook_code || {}).length > 0">
                <span>钩子事件：</span>
                <el-tag
                  v-for="hook in Object.keys(plugin.hook_code).slice(0, 4)"
                  :key="hook"
                  size="small"
                  style="margin: 2px;"
                >{{ hook }}</el-tag>
                <span v-if="Object.keys(plugin.hook_code).length > 4" style="font-size: 12px; color: #909399;">
                  +{{ Object.keys(plugin.hook_code).length - 4 }} 个
                </span>
              </div>
            </div>
            <div class="bind-item-check" v-if="selectedPlugin?.id === plugin.id">
              <el-icon color="#409eff" size="20"><Select /></el-icon>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedPlugin" :loading="binding" @click="bindPlugin">
          {{ selectedPlugin ? `绑定「${selectedPlugin.display_name}」` : '请先选择插件' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Config Dialog -->
    <el-dialog v-model="showConfigDialog" :title="`配置插件：${configPlugin?.display_name}`" width="520px">
      <div v-if="configPlugin" class="config-dialog">
        <el-alert
          v-if="configPlugin.description"
          :title="configPlugin.description"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />
        <el-form label-position="top">
          <el-form-item label="插件配置（JSON 格式）">
            <el-input
              v-model="pluginConfigJson"
              type="textarea"
              :rows="8"
              placeholder='{"key": "value"}'
              style="font-family: monospace;"
            />
          </el-form-item>
        </el-form>
        <div class="config-hooks" v-if="Object.keys(configPlugin.hook_code || {}).length > 0">
          <div class="config-hooks-title">支持的钩子事件：</div>
          <el-tag
            v-for="(code, hook) in configPlugin.hook_code"
            :key="hook"
            size="small"
            style="margin: 4px;"
          >{{ hook }}</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" :loading="configuring" @click="saveConfig">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Loading, Setting, Delete, Select,
  Lightning, Bell, DataAnalysis, Cpu, Tools
} from '@element-plus/icons-vue'
import * as appPluginApi from '../../common/api/appPlugin'

const props = defineProps<{
  appId: number
}>()

const loading = ref(false)
const boundPlugins = ref<any[]>([])
const showBindDialog = ref(false)
const showConfigDialog = ref(false)

const availablePlugins = ref<any[]>([])
const availableLoading = ref(false)
const selectedPlugin = ref<any>(null)
const binding = ref(false)

const searchKeyword = ref('')
const filterCategory = ref('')

const configPlugin = ref<any>(null)
const pluginConfigJson = ref('')
const configuring = ref(false)

// 分类相关工具函数
function getCategoryLabel(category: string): string {
  const map: Record<string, string> = {
    builtin: '内置',
    ai_tool: 'AI工具',
    custom: '自定义',
    workflow: '工作流',
    notification: '通知',
    report: '报表',
  }
  return map[category] || category || '其他'
}

function getCategoryTagType(category: string): string {
  const map: Record<string, string> = {
    builtin: 'success',
    ai_tool: 'warning',
    custom: 'primary',
    workflow: 'danger',
  }
  return map[category] || 'info'
}

function getCategoryColor(category: string): string {
  const map: Record<string, string> = {
    builtin: '#67c23a',
    ai_tool: '#e6a23c',
    custom: '#409eff',
    workflow: '#f56c6c',
    notification: '#909399',
  }
  return map[category] || '#909399'
}

function getCategoryIcon(category: string): any {
  const map: Record<string, any> = {
    builtin: Lightning,
    ai_tool: Cpu,
    custom: Tools,
    workflow: DataAnalysis,
    notification: Bell,
  }
  return map[category] || Tools
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadAvailablePlugins()
  }, 300)
}

async function loadBoundPlugins() {
  loading.value = true
  try {
    const res = await appPluginApi.getAppPlugins(props.appId)
    boundPlugins.value = (res as any).data || []
  } catch (e: any) {
    ElMessage.error('加载插件失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function loadAvailablePlugins() {
  availableLoading.value = true
  try {
    const params: any = {}
    if (searchKeyword.value) params.search = searchKeyword.value
    if (filterCategory.value) params.category = filterCategory.value

    const res = await appPluginApi.getAvailablePluginsForApp(props.appId, params)
    availablePlugins.value = (res as any).data || []
  } catch (e: any) {
    ElMessage.error('加载可用插件失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally {
    availableLoading.value = false
  }
}

function openBindDialog() {
  selectedPlugin.value = null
  searchKeyword.value = ''
  filterCategory.value = ''
  showBindDialog.value = true
}

async function bindPlugin() {
  if (!selectedPlugin.value) return

  binding.value = true
  try {
    await appPluginApi.bindPluginToApp(props.appId, selectedPlugin.value.id)
    ElMessage.success(`插件「${selectedPlugin.value.display_name}」绑定成功`)
    showBindDialog.value = false
    selectedPlugin.value = null
    await loadBoundPlugins()
  } catch (e: any) {
    ElMessage.error('绑定失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally {
    binding.value = false
  }
}

async function unbindPlugin(plugin: any) {
  try {
    await ElMessageBox.confirm(
      `确认解除插件「${plugin.display_name}」的绑定？解绑后该插件功能将不再对此应用生效。`,
      '解绑确认',
      { type: 'warning', confirmButtonText: '确认解绑', cancelButtonText: '取消' }
    )
    await appPluginApi.unbindAppPlugin(props.appId, plugin.id)
    ElMessage.success('已解除绑定')
    await loadBoundPlugins()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('解绑失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    }
  }
}

async function updateBinding(plugin: any) {
  try {
    await appPluginApi.updateAppPluginBinding(props.appId, plugin.id, {
      is_enabled: plugin.is_enabled
    })
    ElMessage.success(plugin.is_enabled ? `插件「${plugin.display_name}」已启用` : `插件「${plugin.display_name}」已禁用`)
  } catch (e: any) {
    ElMessage.error('更新失败: ' + (e.message || '未知错误'))
    plugin.is_enabled = !plugin.is_enabled
  }
}

function openConfigDialog(plugin: any) {
  configPlugin.value = plugin
  try {
    pluginConfigJson.value = JSON.stringify(plugin.config || {}, null, 2)
  } catch {
    pluginConfigJson.value = '{}'
  }
  showConfigDialog.value = true
}

async function saveConfig() {
  if (!configPlugin.value) return

  configuring.value = true
  try {
    let config = {}
    if (pluginConfigJson.value.trim()) {
      config = JSON.parse(pluginConfigJson.value)
    }
    await appPluginApi.updateAppPluginBinding(props.appId, configPlugin.value.id, { config })
    ElMessage.success('配置已保存')
    showConfigDialog.value = false
    await loadBoundPlugins()
  } catch (e: any) {
    if (e instanceof SyntaxError) {
      ElMessage.error('JSON 格式错误，请检查配置内容')
    } else {
      ElMessage.error('保存失败: ' + (e.message || '未知错误'))
    }
  } finally {
    configuring.value = false
  }
}

onMounted(() => {
  loadBoundPlugins()
})
</script>

<style scoped>
.app-plugin-manager {
  padding: 16px;
}

.apm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.apm-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.apm-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.apm-loading,
.apm-empty {
  padding: 40px;
  text-align: center;
}

.apm-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.apm-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: #f8f9fa;
  border: 1px solid #e8eaed;
  border-radius: 10px;
  gap: 14px;
  transition: box-shadow 0.2s;
}

.apm-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.apm-item-icon {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.apm-item-info {
  flex: 1;
  min-width: 0;
}

.apm-item-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
  color: #303133;
}

.apm-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.apm-item-hooks {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.apm-item-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.apm-item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* Bind Dialog */
.bind-dialog {
  max-height: 480px;
  overflow-y: auto;
}

.bind-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.bind-loading,
.bind-empty {
  padding: 40px;
  text-align: center;
}

.bind-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bind-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 14px;
  border: 2px solid #e4e7ed;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 12px;
}

.bind-item:hover {
  border-color: #c6e2ff;
  background: #f0f7ff;
}

.bind-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.bind-item-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin-top: 2px;
}

.bind-item-info {
  flex: 1;
  min-width: 0;
}

.bind-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.bind-item-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.bind-item-desc {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
}

.bind-item-hooks {
  font-size: 12px;
  color: #909399;
}

.bind-item-check {
  display: flex;
  align-items: center;
  padding-top: 4px;
}

/* Config Dialog */
.config-dialog {
  padding: 4px 0;
}

.config-hooks {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.config-hooks-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}
</style>
