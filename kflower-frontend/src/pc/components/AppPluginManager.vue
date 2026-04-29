<template>
  <div class="app-plugin-manager">
    <!-- Header -->
    <div class="apm-header">
      <h3>插件管理</h3>
      <el-button type="primary" size="small" @click="showBindDialog = true">
        <el-icon><Plus /></el-icon> 绑定插件
      </el-button>
    </div>

    <!-- Bound Plugins List -->
    <div v-if="loading" class="apm-loading">
      <el-icon class="is-loading"><Loading /></el-icon> 加载中...
    </div>
    <div v-else-if="boundPlugins.length === 0" class="apm-empty">
      <el-empty description="暂无绑定的插件" :image-size="60">
        <el-button type="primary" size="small" @click="showBindDialog = true">绑定插件</el-button>
      </el-empty>
    </div>
    <div v-else class="apm-list">
      <div v-for="bp in boundPlugins" :key="bp.id" class="apm-item">
        <div class="apm-item-icon">
          <el-icon size="24"><Box /></el-icon>
        </div>
        <div class="apm-item-info">
          <div class="apm-item-name">{{ bp.display_name }}</div>
          <div class="apm-item-meta">
            <el-tag size="small" type="info">{{ bp.version }}</el-tag>
            <span class="apm-item-hooks">钩子: {{ Object.keys(bp.hook_code || {}).join(', ') || '无' }}</span>
          </div>
        </div>
        <div class="apm-item-actions">
          <el-switch v-model="bp.is_enabled" @change="updateBinding(bp)" />
          <el-button size="small" @click="openConfigDialog(bp)">配置</el-button>
          <el-button size="small" type="danger" plain @click="unbindPlugin(bp)">解绑</el-button>
        </div>
      </div>
    </div>

    <!-- Bind Plugin Dialog -->
    <el-dialog v-model="showBindDialog" title="绑定插件" width="600px">
      <div class="bind-dialog">
        <el-input v-model="searchKeyword" placeholder="搜索插件..." clearable style="margin-bottom: 16px;">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <div v-if="availableLoading" class="bind-loading">
          <el-icon class="is-loading"><Loading /></el-icon> 加载中...
        </div>
        <div v-else-if="availablePlugins.length === 0" class="bind-empty">
          <el-empty description="没有可绑定的插件" :image-size="40" />
        </div>
        <div v-else class="bind-list">
          <div
            v-for="plugin in availablePlugins"
            :key="plugin.id"
            class="bind-item"
            :class="{ selected: selectedPlugin?.id === plugin.id }"
            @click="selectedPlugin = plugin"
          >
            <div class="bind-item-icon">
              <el-icon size="20"><Box /></el-icon>
            </div>
            <div class="bind-item-info">
              <div class="bind-item-name">{{ plugin.display_name }}</div>
              <div class="bind-item-desc">{{ plugin.description || '无描述' }}</div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedPlugin" :loading="binding" @click="bindPlugin">
          绑定
        </el-button>
      </template>
    </el-dialog>

    <!-- Config Dialog -->
    <el-dialog v-model="showConfigDialog" title="插件配置" width="500px">
      <div v-if="configPlugin" class="config-dialog">
        <div class="config-plugin-name">{{ configPlugin.display_name }}</div>
        <el-form label-position="top">
          <el-form-item label="插件配置 (JSON)">
            <el-input
              v-model="pluginConfigJson"
              type="textarea"
              :rows="6"
              placeholder='{"key": "value"}'
            />
          </el-form-item>
        </el-form>
        <div class="config-hooks">
          <div class="config-hooks-title">可用钩子:</div>
          <el-tag v-for="(code, hook) in configPlugin.hook_code" :key="hook" size="small" style="margin: 4px;">
            {{ hook }}
          </el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" :loading="configuring" @click="saveConfig">保存配置</el-button>
      </template>
    </el-dialog>

    <!-- Test Hook Dialog -->
    <el-dialog v-model="showTestDialog" title="测试钩子" width="600px">
      <div v-if="testPlugin" class="test-dialog">
        <div class="test-plugin-name">{{ testPlugin.display_name }}</div>
        <el-form label-position="top">
          <el-form-item label="选择钩子">
            <el-select v-model="testHookName" placeholder="选择要测试的钩子" style="width: 100%;">
              <el-option
                v-for="(code, hook) in testPlugin.hook_code"
                :key="hook"
                :label="hook"
                :value="hook"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="测试数据 (JSON)">
            <el-input
              v-model="testDataJson"
              type="textarea"
              :rows="4"
              placeholder='{"data": {}, "user_id": 1}'
            />
          </el-form-item>
        </el-form>
        <div v-if="testResult" class="test-result">
          <div class="test-result-title">执行结果:</div>
          <pre>{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTestDialog = false">关闭</el-button>
        <el-button type="primary" :loading="testing" @click="runTest">执行测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Loading, Box } from '@element-plus/icons-vue'
import * as appPluginApi from '../../common/api/appPlugin'

const props = defineProps<{
  appId: number
}>()

const loading = ref(false)
const boundPlugins = ref<any[]>([])
const showBindDialog = ref(false)
const showConfigDialog = ref(false)
const showTestDialog = ref(false)

const availablePlugins = ref<any[]>([])
const availableLoading = ref(false)
const selectedPlugin = ref<any>(null)
const binding = ref(false)

const searchKeyword = ref('')

const configPlugin = ref<any>(null)
const pluginConfigJson = ref('')
const configuring = ref(false)

const testPlugin = ref<any>(null)
const testHookName = ref('')
const testDataJson = ref('{}')
const testResult = ref<any>(null)
const testing = ref(false)

async function loadBoundPlugins() {
  loading.value = true
  try {
    const res = await appPluginApi.getAppPlugins(props.appId)
    boundPlugins.value = res.data || []
  } catch (e: any) {
    ElMessage.error('加载插件失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function loadAvailablePlugins() {
  availableLoading.value = true
  try {
    const res = await appPluginApi.getAvailablePluginsForApp(props.appId, {
      search: searchKeyword.value
    })
    availablePlugins.value = res.data || []
  } catch (e: any) {
    ElMessage.error('加载可用插件失败: ' + (e.message || '未知错误'))
  } finally {
    availableLoading.value = false
  }
}

async function bindPlugin() {
  if (!selectedPlugin.value) return

  binding.value = true
  try {
    await appPluginApi.bindPluginToApp(props.appId, selectedPlugin.value.id)
    ElMessage.success('插件绑定成功')
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
    await ElMessageBox.confirm(`确认解除插件「${plugin.display_name}」的绑定？`, '解绑确认', { type: 'warning' })
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
    ElMessage.success(plugin.is_enabled ? '插件已启用' : '插件已禁用')
  } catch (e: any) {
    ElMessage.error('更新失败: ' + (e.message || '未知错误'))
    plugin.is_enabled = !plugin.is_enabled
  }
}

function openConfigDialog(plugin: any) {
  configPlugin.value = plugin
  pluginConfigJson.value = JSON.stringify(plugin.config || {}, null, 2)
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
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    configuring.value = false
  }
}

function openTestDialog(plugin: any) {
  testPlugin.value = plugin
  testHookName.value = Object.keys(plugin.hook_code || {})[0] || ''
  testDataJson.value = JSON.stringify({
    data: { sample_field: 'test_value' },
    user_id: 1,
    app_id: props.appId
  }, null, 2)
  testResult.value = null
  showTestDialog.value = true
}

async function runTest() {
  if (!testPlugin.value || !testHookName.value) return

  testing.value = true
  try {
    let testData = {}
    if (testDataJson.value.trim()) {
      testData = JSON.parse(testDataJson.value)
    }
    const res = await appPluginApi.triggerAppPluginHook(props.appId, testHookName.value, testData)
    testResult.value = res.data
  } catch (e: any) {
    testResult.value = { error: e.message || '测试执行失败' }
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadBoundPlugins()
})

watch(showBindDialog, (val) => {
  if (val) {
    loadAvailablePlugins()
    selectedPlugin.value = null
  }
})

watch(searchKeyword, () => {
  loadAvailablePlugins()
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
  margin-bottom: 16px;
}

.apm-header h3 {
  margin: 0;
  font-size: 16px;
}

.apm-loading,
.apm-empty {
  padding: 40px;
  text-align: center;
}

.apm-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.apm-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  gap: 12px;
}

.apm-item-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 8px;
  color: #409eff;
}

.apm-item-info {
  flex: 1;
}

.apm-item-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.apm-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.apm-item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bind-dialog {
  max-height: 400px;
  overflow-y: auto;
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
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.bind-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.bind-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.bind-item-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 6px;
  margin-right: 12px;
  color: #409eff;
}

.bind-item-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.bind-item-desc {
  font-size: 12px;
  color: #909399;
}

.config-dialog {
  padding: 8px 0;
}

.config-plugin-name {
  font-weight: 500;
  margin-bottom: 16px;
  font-size: 16px;
}

.config-hooks {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.config-hooks-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.test-dialog {
  padding: 8px 0;
}

.test-plugin-name {
  font-weight: 500;
  margin-bottom: 16px;
  font-size: 16px;
}

.test-result {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.test-result-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.test-result pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>