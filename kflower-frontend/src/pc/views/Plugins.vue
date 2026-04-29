<template>
  <div class="plugins-page">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>插件市场</h2>
        <span class="subtitle">管理系统插件与 AI 工具集</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
          安装插件
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row" v-if="stats">
      <div class="stat-card">
        <div class="stat-num">{{ stats.total }}</div>
        <div class="stat-label">全部插件</div>
      </div>
      <div class="stat-card enabled">
        <div class="stat-num">{{ stats.enabled }}</div>
        <div class="stat-label">已启用</div>
      </div>
      <div class="stat-card builtin">
        <div class="stat-num">{{ stats.builtin }}</div>
        <div class="stat-label">内置插件</div>
      </div>
      <div class="stat-card custom">
        <div class="stat-num">{{ stats.custom }}</div>
        <div class="stat-label">自定义</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-radio-group v-model="activeCategory" @change="loadPlugins">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="builtin">内置</el-radio-button>
        <el-radio-button label="ai_tool">AI 工具</el-radio-button>
        <el-radio-button label="custom">自定义</el-radio-button>
        <el-radio-button label="market">市场</el-radio-button>
      </el-radio-group>

      <el-input
        v-model="searchKeyword"
        placeholder="搜索插件名称、描述..."
        :prefix-icon="Search"
        clearable
        style="width: 260px; margin-left: 16px"
        @input="loadPlugins"
      />

      <el-select
        v-model="filterEnabled"
        placeholder="启用状态"
        clearable
        style="width: 120px; margin-left: 12px"
        @change="loadPlugins"
      >
        <el-option label="已启用" :value="true" />
        <el-option label="已禁用" :value="false" />
      </el-select>
    </div>

    <!-- 插件卡片列表 -->
    <div class="plugins-grid" v-loading="loading">
      <div
        v-for="plugin in plugins"
        :key="plugin.id"
        class="plugin-card"
        :class="{ disabled: !plugin.is_enabled }"
      >
        <!-- 卡片头部 -->
        <div class="card-header">
          <div class="plugin-icon" :class="`icon-${plugin.category}`">
            <el-icon :size="24">
              <component :is="getIconComponent(plugin.icon)" />
            </el-icon>
          </div>
          <div class="plugin-meta">
            <div class="plugin-name">{{ plugin.display_name }}</div>
            <div class="plugin-badges">
              <el-tag size="small" :type="getCategoryTagType(plugin.category)">
                {{ getCategoryLabel(plugin.category) }}
              </el-tag>
              <el-tag size="small" type="info" style="margin-left:4px">
                v{{ plugin.version }}
              </el-tag>
            </div>
          </div>
          <div class="card-actions">
            <el-switch
              v-model="plugin.is_enabled"
              :disabled="plugin.is_built_in"
              :title="plugin.is_built_in ? '内置插件不可禁用' : ''"
              @change="(val: boolean) => togglePlugin(plugin, val)"
            />
          </div>
        </div>

        <!-- 描述 -->
        <div class="plugin-desc">{{ plugin.description || '暂无描述' }}</div>

        <!-- AI工具详情 -->
        <div class="plugin-tool-info" v-if="plugin.category === 'ai_tool' && plugin.config?.tool_name">
          <el-tag size="small" effect="plain">工具: {{ plugin.config.tool_name }}</el-tag>
          <el-tag size="small" effect="plain" style="margin-left:4px">
            类型: {{ plugin.config.tool_type }}
          </el-tag>
        </div>

        <!-- 底部操作 -->
        <div class="card-footer">
          <span class="plugin-author" v-if="plugin.author">by {{ plugin.author }}</span>
          <div class="footer-btns">
            <el-button
              size="small"
              text
              :icon="Edit"
              @click="openEditDialog(plugin)"
            >
              配置
            </el-button>
            <el-button
              v-if="!plugin.is_built_in"
              size="small"
              text
              type="danger"
              :icon="Delete"
              @click="deletePlugin(plugin)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-if="!loading && plugins.length === 0" description="暂无插件" />
    </div>

    <!-- 安装/编辑插件对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingPlugin ? '编辑插件配置' : '安装插件'"
      width="640px"
      destroy-on-close
    >
      <el-form
        ref="pluginFormRef"
        :model="pluginForm"
        label-width="100px"
        :rules="pluginFormRules"
      >
        <el-form-item label="插件名称" prop="name" v-if="!editingPlugin">
          <el-input v-model="pluginForm.name" placeholder="英文标识，如 my-plugin" />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="pluginForm.display_name" placeholder="显示给用户的名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="pluginForm.description"
            type="textarea"
            :rows="3"
            placeholder="描述插件功能"
          />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="pluginForm.version" placeholder="1.0.0" style="width:160px" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="pluginForm.author" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="pluginForm.icon" placeholder="Element Plus 图标名，如 magic-stick" />
        </el-form-item>
        <el-form-item label="钩子代码">
          <el-select v-model="selectedHook" placeholder="选择要编辑的钩子" style="width:200px; margin-bottom:8px">
            <el-option
              v-for="h in hookEvents"
              :key="h.name"
              :label="h.display_name"
              :value="h.name"
            />
          </el-select>
          <el-input
            v-if="selectedHook"
            v-model="currentHookCode"
            type="textarea"
            :rows="8"
            placeholder="在此编写 Python 钩子代码..."
            style="font-family: monospace; font-size: 13px"
            @input="saveHookCode"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="savePlugin">
          {{ editingPlugin ? '保存' : '安装' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Edit, Delete,
  MagicStick, Bell, SetUp, DataAnalysis,
  Connection, VideoPlay, CopyDocument, Grid,
  Upload, DocumentAdd, Document
} from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = '/api/v1'

// ─── 响应式数据 ───────────────────────────────────────────────────────────────
const loading = ref(false)
const saving = ref(false)
const plugins = ref<any[]>([])
const stats = ref<any>(null)
const activeCategory = ref('')
const searchKeyword = ref('')
const filterEnabled = ref<boolean | null>(null)
const showCreateDialog = ref(false)
const editingPlugin = ref<any>(null)
const pluginFormRef = ref()
const selectedHook = ref('')
const currentHookCode = ref('')
const hookEvents = ref<any[]>([])

const pluginForm = reactive({
  name: '',
  display_name: '',
  description: '',
  version: '1.0.0',
  author: '',
  icon: 'puzzle-piece',
  hook_code: {} as Record<string, string>
})

const pluginFormRules = {
  name: [{ required: true, message: '请填写插件名称', trigger: 'blur' }],
  display_name: [{ required: true, message: '请填写显示名称', trigger: 'blur' }],
}

// ─── 加载数据 ─────────────────────────────────────────────────────────────────
const loadPlugins = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (activeCategory.value) params.category = activeCategory.value
    if (searchKeyword.value) params.search = searchKeyword.value
    if (filterEnabled.value !== null) params.is_enabled = filterEnabled.value

    const res = await axios.get(`${API_BASE}/plugins/`, { params })
    if (res.data.success) {
      plugins.value = res.data.data || []
    }
  } catch (e) {
    ElMessage.error('加载插件列表失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await axios.get(`${API_BASE}/plugins/stats/overview`)
    if (res.data.success) stats.value = res.data.data
  } catch {}
}

const loadHookEvents = async () => {
  try {
    const res = await axios.get(`${API_BASE}/plugins/builtin-events`)
    if (res.data.success) hookEvents.value = res.data.data || []
  } catch {}
}

// ─── 插件操作 ─────────────────────────────────────────────────────────────────
const togglePlugin = async (plugin: any, val: boolean) => {
  try {
    const action = val ? 'enable' : 'disable'
    const res = await axios.post(`${API_BASE}/plugins/${plugin.id}/${action}`)
    if (res.data.success) {
      ElMessage.success(res.data.message || `插件已${val ? '启用' : '禁用'}`)
      loadStats()
    } else {
      // 回滚
      plugin.is_enabled = !val
      ElMessage.warning(res.data.message || '操作失败')
    }
  } catch (e) {
    plugin.is_enabled = !val
    ElMessage.error('操作失败')
  }
}

const openEditDialog = (plugin: any) => {
  editingPlugin.value = plugin
  Object.assign(pluginForm, {
    name: plugin.name,
    display_name: plugin.display_name,
    description: plugin.description || '',
    version: plugin.version || '1.0.0',
    author: plugin.author || '',
    icon: plugin.icon || '',
    hook_code: { ...(plugin.hook_code || {}) }
  })
  selectedHook.value = ''
  currentHookCode.value = ''
  showCreateDialog.value = true
}

const saveHookCode = () => {
  if (selectedHook.value) {
    pluginForm.hook_code[selectedHook.value] = currentHookCode.value
  }
}

watch(selectedHook, (hook) => {
  currentHookCode.value = hook ? (pluginForm.hook_code[hook] || '') : ''
})

const savePlugin = async () => {
  await pluginFormRef.value?.validate()
  saving.value = true
  try {
    if (editingPlugin.value) {
      const res = await axios.put(
        `${API_BASE}/plugins/${editingPlugin.value.id}`,
        {
          display_name: pluginForm.display_name,
          description: pluginForm.description,
          version: pluginForm.version,
          author: pluginForm.author,
          icon: pluginForm.icon,
          hook_code: pluginForm.hook_code
        }
      )
      if (res.data.success) {
        ElMessage.success('保存成功')
        showCreateDialog.value = false
        loadPlugins()
      }
    } else {
      const res = await axios.post(`${API_BASE}/plugins/`, {
        name: pluginForm.name,
        display_name: pluginForm.display_name,
        description: pluginForm.description,
        version: pluginForm.version,
        author: pluginForm.author,
        icon: pluginForm.icon,
        hook_code: pluginForm.hook_code,
        install_type: 'local'
      })
      if (res.data.success) {
        ElMessage.success('插件安装成功')
        showCreateDialog.value = false
        loadPlugins()
        loadStats()
      }
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

const deletePlugin = async (plugin: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除插件「${plugin.display_name}」？此操作不可撤销。`,
      '删除确认',
      { type: 'warning' }
    )
    const res = await axios.delete(`${API_BASE}/plugins/${plugin.id}`)
    if (res.data.success) {
      ElMessage.success('删除成功')
      loadPlugins()
      loadStats()
    }
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

// ─── 辅助函数 ─────────────────────────────────────────────────────────────────
const getCategoryLabel = (cat: string) => {
  const map: Record<string, string> = {
    builtin: '内置',
    ai_tool: 'AI工具',
    custom: '自定义',
    market: '市场',
  }
  return map[cat] || cat
}

const getCategoryTagType = (cat: string) => {
  const map: Record<string, string> = {
    builtin: 'primary',
    ai_tool: 'success',
    custom: 'warning',
    market: 'info',
  }
  return map[cat] || ''
}

const getIconComponent = (icon: string) => {
  const map: Record<string, any> = {
    'magic-stick': MagicStick,
    'bell': Bell,
    'set-up': SetUp,
    'data-analysis': DataAnalysis,
    'connection': Connection,
    'video-play': VideoPlay,
    'copy-document': CopyDocument,
    'grid': Grid,
    'upload': Upload,
    'document-add': DocumentAdd,
    'document': Document,
    'search': Search,
  }
  return map[icon] || MagicStick
}

onMounted(() => {
  loadPlugins()
  loadStats()
  loadHookEvents()
})
</script>

<style scoped>
.plugins-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  color: #1a1a2e;
}

.subtitle {
  font-size: 13px;
  color: #909399;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 24px;
  min-width: 100px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.stat-card .stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
}

.stat-card.enabled .stat-num { color: #67c23a; }
.stat-card.builtin .stat-num { color: #909399; }
.stat-card.custom .stat-num  { color: #e6a23c; }

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

/* 插件卡片网格 */
.plugins-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.plugin-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s, transform 0.2s;
  border: 1px solid #ebeef5;
}

.plugin-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.plugin-card.disabled {
  opacity: 0.6;
  background: #fafafa;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.plugin-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ecf5ff;
  color: #409eff;
  flex-shrink: 0;
}

.plugin-icon.icon-ai_tool { background: #f0f9eb; color: #67c23a; }
.plugin-icon.icon-builtin { background: #ecf5ff; color: #409eff; }
.plugin-icon.icon-custom  { background: #fdf6ec; color: #e6a23c; }

.plugin-meta {
  flex: 1;
  min-width: 0;
}

.plugin-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-actions {
  flex-shrink: 0;
}

/* 描述 */
.plugin-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.plugin-tool-info {
  margin-bottom: 10px;
}

/* 底部 */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.plugin-author {
  font-size: 12px;
  color: #c0c4cc;
}

.footer-btns {
  display: flex;
  gap: 4px;
}
</style>
