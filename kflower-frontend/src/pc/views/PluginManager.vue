<template>
  <div class="plugin-manager">
    <!-- Header -->
    <div class="pm-header">
      <div class="pm-title">
        <h2>插件管理</h2>
        <p class="pm-subtitle">{{ stats.total }} 个插件，{{ stats.enabled }} 个已启用，{{ stats.builtin }} 个内置</p>
      </div>
      <el-button type="primary" @click="goToDesigner">
        <el-icon><Plus /></el-icon> 可视化设计
      </el-button>
    </div>

    <!-- Stats Cards -->
    <div class="pm-stats">
      <div class="stat-card">
        <div class="stat-icon icon-primary">
          <el-icon size="22"><Box /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">全部插件</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-success">
          <el-icon size="22"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.enabled }}</div>
          <div class="stat-label">已启用</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-danger">
          <el-icon size="22"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.disabled }}</div>
          <div class="stat-label">已禁用</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-warning">
          <el-icon size="22"><Star /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.builtin }}</div>
          <div class="stat-label">内置插件</div>
        </div>
      </div>
    </div>

    <!-- Filter & Search -->
    <div class="pm-toolbar">
      <el-tabs v-model="activeTab" @tab-change="loadPlugins">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="内置" name="builtin" />
        <el-tab-pane label="自定义" name="custom" />
      </el-tabs>
      <el-input v-model="search" placeholder="搜索插件..." clearable style="width: 240px;">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <!-- Plugin List -->
    <div v-if="loading" class="pm-loading">
      <el-icon class="is-loading"><Loading /></el-icon> 加载中...
    </div>
    <div v-else-if="filteredPlugins.length === 0" class="pm-empty">
      <el-empty description="暂无插件" :image-size="80" />
    </div>
    <div v-else class="pm-grid">
      <div v-for="plugin in filteredPlugins" :key="plugin.id" class="plugin-card">
        <div class="plugin-card-header">
          <div class="plugin-icon">
            <el-icon size="24"><Box /></el-icon>
          </div>
          <div class="plugin-info">
            <div class="plugin-name">{{ plugin.display_name || plugin.name }}</div>
            <div class="plugin-type">
              <el-tag v-if="plugin.is_built_in" type="warning" size="small">内置</el-tag>
              <el-tag v-else type="info" size="small">自定义</el-tag>
              <el-tag :type="plugin.is_enabled ? 'success' : 'info'" size="small" style="margin-left: 4px;">
                {{ plugin.is_enabled ? '已启用' : '已禁用' }}
              </el-tag>
            </div>
          </div>
        </div>
        <div class="plugin-card-body">
          <div class="plugin-hooks">
            <span class="hooks-label">钩子事件：</span>
            <el-tag v-for="hook in (plugin.hook_events || []).slice(0, 3)" :key="hook" size="small" style="margin: 2px;">
              {{ hook }}
            </el-tag>
            <span v-if="(plugin.hook_events || []).length > 3" style="color: var(--el-text-color-secondary); font-size: 12px;">
              +{{ plugin.hook_events.length - 3 }}
            </span>
            <span v-if="!(plugin.hook_events || []).length" style="color: var(--el-text-color-secondary); font-size: 12px;">
              无
            </span>
          </div>
          <div class="plugin-desc">{{ plugin.description || '暂无描述' }}</div>
          <div class="plugin-meta">
            <span>ID: {{ plugin.id }}</span>
            <span>{{ plugin.created_at ? formatDate(plugin.created_at) : '-' }}</span>
          </div>
        </div>
        <div class="plugin-card-actions">
          <el-button size="small" @click="openDetailDialog(plugin)">详情</el-button>
          <el-button v-if="!plugin.is_built_in" size="small" type="primary" plain @click="openEditDialog(plugin)">设计</el-button>
          <el-button v-if="!plugin.is_built_in" size="small" :type="plugin.is_enabled ? 'warning' : 'success'" @click="togglePlugin(plugin)">
            {{ plugin.is_enabled ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" type="info" plain @click="openHookTestDialog(plugin)">测试钩子</el-button>
          <el-button v-if="!plugin.is_built_in" size="small" type="danger" plain @click="deletePlugin(plugin)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- Hook Events Reference -->
    <div class="pm-hooks-ref">
      <div class="hooks-ref-header" @click="hooksRefExpanded = !hooksRefExpanded">
        <span>📌 可用钩子事件参考</span>
        <el-icon><ArrowDown /></el-icon>
      </div>
      <div v-show="hooksRefExpanded" class="hooks-ref-body">
        <div class="hook-item" v-for="evt in builtinEvents" :key="evt.code">
          <div class="hook-code">{{ evt.code }}</div>
          <div class="hook-desc">{{ evt.description }}</div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '创建插件' : '编辑插件'" width="640px" destroy-on-close>
      <el-form :model="form" label-width="100px" class="plugin-form">
        <el-form-item label="插件名称" required>
          <el-input v-model="form.name" placeholder="如：CRM联系人同步" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="插件描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述插件功能..." />
        </el-form-item>
        <el-form-item label="钩子事件">
          <el-select v-model="form.hook_events" multiple placeholder="选择触发时机" style="width: 100%;">
            <el-option v-for="evt in builtinEvents" :key="evt.code" :label="evt.code" :value="evt.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="代码片段">
          <el-input v-model="form.code_snippet" type="textarea" :rows="6" placeholder="def on_event(ctx):&#10;    # 你的代码&#10;    return {'result': 'ok'}" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitPlugin">
          {{ dialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="插件详情" width="560px" destroy-on-close>
      <div v-if="selectedPlugin" class="plugin-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ selectedPlugin.name }}</el-descriptions-item>
          <el-descriptions-item label="ID">{{ selectedPlugin.id }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="selectedPlugin.is_built_in ? 'warning' : 'info'" size="small">
              {{ selectedPlugin.is_built_in ? '内置' : '自定义' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedPlugin.is_enabled ? 'success' : 'info'" size="small">
              {{ selectedPlugin.is_enabled ? '已启用' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ selectedPlugin.created_at ? formatDate(selectedPlugin.created_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedPlugin.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="钩子事件" :span="2">
            <div class="detail-hooks">
              <el-tag v-for="h in (selectedPlugin.hook_events || [])" :key="h" size="small" style="margin: 2px;">{{ h }}</el-tag>
              <span v-if="!(selectedPlugin.hook_events || []).length">无</span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="代码" :span="2">
            <pre class="code-block">{{ selectedPlugin.code_snippet || '无' }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- Hook Test Dialog -->
    <el-dialog v-model="hookTestVisible" title="测试钩子" width="600px" destroy-on-close>
      <el-form :model="hookForm" label-width="100px">
        <el-form-item label="选择事件">
          <el-select v-model="hookForm.event" placeholder="选择钩子事件" style="width: 100%;">
            <el-option v-for="evt in builtinEvents" :key="evt.code" :label="evt.code" :value="evt.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试代码">
          <el-input v-model="hookForm.code_snippet" type="textarea" :rows="6" placeholder="def on_event(ctx):&#10;    # 你的代码&#10;    return {'result': 'ok'}" />
        </el-form-item>
        <el-form-item label="测试数据">
          <el-input v-model="hookForm.payload_json" type="textarea" :rows="3" placeholder='{"key": "value"}' />
        </el-form-item>
      </el-form>
      <div v-if="hookTestResult" class="hook-test-result">
        <el-divider content-position="left">测试结果</el-divider>
        <pre class="code-block">{{ hookTestResult }}</pre>
      </div>
      <template #footer>
        <el-button @click="hookTestVisible = false">关闭</el-button>
        <el-button type="primary" :loading="hookTesting" @click="runHookTest">执行测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Box, CircleCheck, CircleClose, Star, Loading, ArrowDown } from '@element-plus/icons-vue'
import api from "../../common/api/index"

const router = useRouter()

const API_BASE = "/plugins"

const plugins = ref<any[]>([])
const loading = ref(false)
const search = ref("")
const activeTab = ref("all")
const stats = ref({ total: 0, enabled: 0, disabled: 0, builtin: 0 })
const builtinEvents = ref<any[]>([])
const hooksRefExpanded = ref(true)

const dialogVisible = ref(false)
const detailVisible = ref(false)
const hookTestVisible = ref(false)
const dialogMode = ref<"create"|"edit">("create")
const submitting = ref(false)
const hookTesting = ref(false)
const selectedPlugin = ref<any>(null)
const hookTestResult = ref("")

const form = ref({
  name: "",
  description: "",
  hook_events: [] as string[],
  code_snippet: `def on_event(ctx):
    # ctx: {event, payload, app, user, data}
    return {result: 'ok'}`,
  enabled: true
})

const hookForm = ref({
  event: "",
  code_snippet: "",
  payload_json: "{}"
})

const filteredPlugins = computed(() => {
  if (!search.value) return plugins.value
  const q = search.value.toLowerCase()
  return plugins.value.filter(p =>
    p.name?.toLowerCase().includes(q) ||
    p.description?.toLowerCase().includes(q) ||
    (p.hook_events || []).some((h: string) => h.toLowerCase().includes(q))
  )
})

async function loadPlugins() {
  loading.value = true
  try {
    const params: any = {}
    if (activeTab.value === "builtin") params.is_builtin = true
    if (activeTab.value === "custom") params.is_builtin = false
    console.log('[PluginManager] Request URL:', API_BASE + "/")
    console.log('[PluginManager] Request params:', params)
    console.log('[PluginManager] Token exists:', !!localStorage.getItem('access_token'))
    const res = await api.get(API_BASE + "/", { params })
    console.log('[PluginManager] Response:', res)
    if (res.success && Array.isArray(res.data)) {
      plugins.value = res.data
      calcStats()
      ElMessage.success(`成功加载 ${plugins.value.length} 个插件`)
    } else {
      plugins.value = []
      ElMessage.warning('返回数据格式不正确')
    }
  } catch (e: any) {
    console.error('[PluginManager] Error:', e)
    console.error('[PluginManager] Error response:', e.response)
    const status = e.response?.status
    const detail = e.response?.data?.detail || e.response?.data?.message
    let msg = "加载插件失败"
    if (status === 401) {
      msg = '登录已过期，请重新登录'
    } else if (status === 403) {
      msg = '没有权限访问插件管理'
    } else if (status === 404) {
      msg = 'API接口不存在'
    } else if (detail) {
      msg = '加载插件失败: ' + detail
    }
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await api.get(API_BASE + "/stats/overview")
    stats.value = res.success ? res.data : {}
  } catch {}
}

async function loadBuiltinEvents() {
  try {
    const res = await api.get(API_BASE + "/builtin-events")
    builtinEvents.value = res.success && Array.isArray(res.data) ? res.data : []
  } catch {}
}

function calcStats() {
  stats.value.total = plugins.value.length
  stats.value.enabled = plugins.value.filter(p => p.is_enabled).length
  stats.value.disabled = plugins.value.filter(p => !p.is_enabled).length
  stats.value.builtin = plugins.value.filter(p => p.is_built_in).length
}

function goToDesigner() {
  router.push('/plugin-designer')
}

function openEditDialog(plugin: any) {
  router.push(`/plugin-designer/${plugin.id}`)
}

async function submitPlugin() {
  if (!form.value.name?.trim()) {
    ElMessage.warning("请输入插件名称")
    return
  }
  submitting.value = true
  try {
    if (dialogMode.value === "create") {
      const res = await api.post(API_BASE + "/", {
        name: form.value.name,
        display_name: form.value.name,
        description: form.value.description,
        hook_code: form.value.hook_events?.length ? { [form.value.hook_events[0]]: form.value.code_snippet } : {},
        is_enabled: form.value.enabled
      })
      if (res.success) {
        ElMessage.success("插件创建成功")
      }
    } else {
      const res = await api.put(API_BASE + "/" + selectedPlugin.value.id, {
        description: form.value.description,
        hook_code: form.value.hook_events?.length ? { [form.value.hook_events[0]]: form.value.code_snippet } : {},
        is_enabled: form.value.enabled
      })
      if (res.success) {
        ElMessage.success("插件更新成功")
      }
    }
    dialogVisible.value = false
    await loadPlugins()
    await loadStats()
  } catch (e: any) {
    ElMessage.error((e.response?.data?.detail || e.response?.data?.message) || "操作失败: " + (e.message || "未知错误"))
  } finally {
    submitting.value = false
  }
}

function openDetailDialog(plugin: any) {
  selectedPlugin.value = plugin
  detailVisible.value = true
}

async function togglePlugin(plugin: any) {
  try {
    let res
    if (plugin.is_enabled) {
      res = await api.post(API_BASE + "/" + plugin.id + "/disable")
    } else {
      res = await api.post(API_BASE + "/" + plugin.id + "/enable")
    }
    if (res.success) {
      ElMessage.success(plugin.is_enabled ? "插件已禁用" : "插件已启用")
    } else {
      ElMessage.error(res.message || "操作失败")
    }
    await loadPlugins()
    await loadStats()
  } catch (e: any) {
    ElMessage.error("操作失败: " + (e.response?.data?.detail || e.response?.data?.message || e.message))
  }
}

async function deletePlugin(plugin: any) {
  try {
    await ElMessageBox.confirm(`确认删除插件「${plugin.display_name || plugin.name}」？此操作不可恢复。`, "删除确认", {
      type: "warning"
    })
    const res = await api.delete(API_BASE + "/" + plugin.id)
    if (res.success) {
      ElMessage.success("插件已删除")
      await loadPlugins()
      await loadStats()
    } else {
      ElMessage.error(res.message || "删除失败")
    }
  } catch (e: any) {
    if (e !== "cancel") ElMessage.error("删除失败: " + (e.response?.data?.detail || e.response?.data?.message || e.message))
  }
}

function openHookTestDialog(plugin: any) {
  selectedPlugin.value = plugin
  hookForm.value.event = plugin.hook_events?.[0] || "after_form_submit"
  hookForm.value.code_snippet = plugin.code_snippet || `def on_event(ctx):
    return {result: 'ok'}`
  hookForm.value.payload_json = "{}"
  hookTestResult.value = ""
  hookTestVisible.value = true
}

async function runHookTest() {
  hookTesting.value = true
  hookTestResult.value = ""
  try {
    let payload = {}
    try { payload = JSON.parse(hookForm.value.payload_json) } catch {}
    const res = await api.post(API_BASE + "/test-hook", {
      code_snippet: hookForm.value.code_snippet,
      event: hookForm.value.event,
      payload
    })
    if (res.success) {
      const data = res.data
      hookTestResult.value = JSON.stringify({
        success: data.success,
        output: data.output,
        duration_ms: data.duration_ms + "ms",
        logs: data.logs || []
      }, null, 2)
    } else {
      hookTestResult.value = "错误: " + (res.message || "测试失败")
    }
  } catch (e: any) {
    hookTestResult.value = "错误: " + (e.response?.data?.detail || e.response?.data?.message || e.message)
  } finally {
    hookTesting.value = false
  }
}

function formatDate(str: string) {
  if (!str) return "-"
  try {
    return new Date(str).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })
  } catch { return str }
}

onMounted(() => {
  loadPlugins()
  loadStats()
  loadBuiltinEvents()
})
</script>

<style scoped>
.plugin-manager {
  padding: 24px;
  min-height: 100%;
}
.pm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.pm-title h2 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.pm-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.pm-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-primary { background: var(--el-color-primary-light-9); color: var(--el-color-primary); }
.icon-success { background: var(--el-color-success-light-9); color: var(--el-color-success); }
.icon-danger { background: var(--el-color-danger-light-9); color: var(--el-color-danger); }
.icon-warning { background: var(--el-color-warning-light-9); color: var(--el-color-warning); }
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
}
.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.pm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}
.pm-loading {
  text-align: center;
  padding: 60px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.pm-empty {
  padding: 40px 0;
}
.pm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.plugin-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.plugin-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.plugin-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.plugin-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.plugin-info {
  flex: 1;
  min-width: 0;
}
.plugin-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.plugin-type {
  display: flex;
  align-items: center;
  margin-top: 4px;
}
.plugin-card-body {
  flex: 1;
}
.plugin-hooks {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
  margin-bottom: 6px;
}
.hooks-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}
.plugin-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 6px;
}
.plugin-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}
.plugin-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border-top: 1px solid var(--el-border-color-extra-light);
  padding-top: 10px;
}
.pm-hooks-ref {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  overflow: hidden;
}
.hooks-ref-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: var(--el-text-color-primary);
  background: var(--el-fill-color-light);
}
.hooks-ref-body {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
  padding: 14px 18px;
}
.hook-item {
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-extra-light);
  border-radius: 8px;
  padding: 10px 12px;
}
.hook-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  font-family: monospace;
  margin-bottom: 4px;
}
.hook-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.plugin-detail {
  padding: 4px 0;
}
.detail-hooks {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.code-block {
  background: var(--el-fill-color-dark);
  color: var(--el-text-color-primary);
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-family: "Consolas", "Monaco", monospace;
  overflow-x: auto;
  margin: 4px 0 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
.hook-test-result {
  margin-top: 12px;
}
@media (max-width: 768px) {
  .pm-stats { grid-template-columns: repeat(2, 1fr); }
  .pm-grid { grid-template-columns: 1fr; }
}
</style>
