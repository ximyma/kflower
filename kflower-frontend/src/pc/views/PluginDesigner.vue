<template>
  <div class="plugin-designer">
    <!-- Header -->
    <div class="pd-header">
      <div class="pd-title">
        <h2>插件可视化设计器</h2>
        <p class="pd-subtitle">创建和编辑自定义插件</p>
      </div>
      <div class="pd-actions">
        <el-button size="small" @click="resetForm">重置</el-button>
        <el-button size="small" type="primary" :loading="saving" @click="savePlugin">
          {{ editMode ? '保存修改' : '创建插件' }}
        </el-button>
      </div>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="pd-tabs">
      <el-tab-pane label="基本信息" name="basic">
        <div class="tab-content">
          <el-form :model="form" label-width="120px" class="basic-form">
            <el-form-item label="插件标识" required>
              <el-input v-model="form.name" :disabled="editMode" placeholder="如: my-custom-plugin" />
            </el-form-item>
            <el-form-item label="显示名称" required>
              <el-input v-model="form.display_name" placeholder="如: 我的自定义插件" />
            </el-form-item>
            <el-form-item label="插件描述">
              <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述插件的功能..." />
            </el-form-item>
            <el-form-item label="版本号">
              <el-input v-model="form.version" placeholder="1.0.0" />
            </el-form-item>
            <el-form-item label="作者">
              <el-input v-model="form.author" placeholder="作者名称或邮箱" />
            </el-form-item>
            <el-form-item label="图标">
              <el-select v-model="form.icon" placeholder="选择图标">
                <el-option label="⚙️ 设置" value="settings" />
                <el-option label="🔌 插头" value="plug" />
                <el-option label="🧩 拼图" value="puzzle-piece" />
                <el-option label="📦 盒子" value="box" />
                <el-option label="⚡ 闪电" value="zap" />
                <el-option label="🔔 通知" value="bell" />
                <el-option label="📊 图表" value="bar-chart" />
                <el-option label="🔧 工具" value="wrench" />
              </el-select>
            </el-form-item>
            <el-form-item label="分类">
              <el-select v-model="form.category" placeholder="选择分类">
                <el-option label="自定义" value="custom" />
                <el-option label="AI工具" value="ai_tool" />
                <el-option label="集成" value="integration" />
                <el-option label="工作流" value="workflow" />
                <el-option label="数据处理" value="data" />
              </el-select>
            </el-form-item>
            <el-form-item label="启用状态">
              <el-switch v-model="form.is_enabled" />
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="钩子函数" name="hooks">
        <div class="tab-content">
          <div class="hooks-header">
            <span>选择钩子事件</span>
            <el-button type="primary" size="small" @click="addHook">
              <el-icon><Plus /></el-icon> 添加钩子
            </el-button>
          </div>

          <div v-if="hooks.length === 0" class="hooks-empty">
            <el-empty description="暂无钩子函数" :image-size="60">
              <el-button type="primary" size="small" @click="addHook">添加钩子</el-button>
            </el-empty>
          </div>

          <div v-else class="hooks-list">
            <div v-for="(hook, index) in hooks" :key="index" class="hook-card">
              <div class="hook-header">
                <el-select v-model="hook.event" placeholder="选择事件" style="width: 200px;">
                  <el-option v-for="evt in availableEvents" :key="evt.code" :label="evt.code" :value="evt.code" />
                </el-select>
                <div class="hook-actions">
                  <el-button size="small" @click="copyHook(index)">复制</el-button>
                  <el-button size="small" type="danger" plain @click="removeHook(index)">删除</el-button>
                </div>
              </div>
              <div class="hook-desc">{{ getEventDescription(hook.event) }}</div>
              <div class="hook-code-editor">
                <div class="code-header">
                  <span>Python 代码</span>
                  <el-button size="mini" @click="loadHookTemplate(index)">加载模板</el-button>
                </div>
                <textarea
                  v-model="hook.code"
                  class="code-textarea"
                  placeholder="def on_event(ctx):&#10;    # ctx: {event, payload, app, user, data}&#10;    return {'result': 'ok'}"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="配置参数" name="config">
        <div class="tab-content">
          <div class="config-intro">
            <p>为插件定义可配置的参数，用户在使用插件时可以自定义这些值。</p>
          </div>
          <div class="config-header">
            <span>配置参数列表</span>
            <el-button type="primary" size="small" @click="addConfigItem">
              <el-icon><Plus /></el-icon> 添加参数
            </el-button>
          </div>

          <div v-if="configItems.length === 0" class="config-empty">
            <el-empty description="暂无配置参数" :image-size="60">
              <el-button type="primary" size="small" @click="addConfigItem">添加参数</el-button>
            </el-empty>
          </div>

          <div v-else class="config-list">
            <div v-for="(item, index) in configItems" :key="index" class="config-card">
              <el-form :model="item" label-width="100px" class="config-form">
                <div class="config-row">
                  <el-form-item label="参数名">
                    <el-input v-model="item.key" placeholder="参数键名" />
                  </el-form-item>
                  <el-form-item label="显示名称">
                    <el-input v-model="item.label" placeholder="显示名称" />
                  </el-form-item>
                  <el-form-item label="类型">
                    <el-select v-model="item.type" style="width: 120px;">
                      <el-option label="字符串" value="string" />
                      <el-option label="数字" value="number" />
                      <el-option label="布尔" value="boolean" />
                      <el-option label="选择" value="select" />
                      <el-option label="文本" value="textarea" />
                    </el-select>
                  </el-form-item>
                  <el-button size="small" type="danger" plain @click="removeConfigItem(index)">删除</el-button>
                </div>
                <el-form-item label="默认值">
                  <el-input v-model="item.default" placeholder="默认值" />
                </el-form-item>
                <el-form-item label="选项值" v-if="item.type === 'select'">
                  <el-input v-model="item.options" placeholder="选项1,选项2,选项3" />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input v-model="item.description" type="textarea" :rows="2" placeholder="参数说明..." />
                </el-form-item>
              </el-form>
            </div>
          </div>

          <div class="config-preview">
            <div class="preview-header">配置 JSON 预览</div>
            <pre class="preview-code">{{ getConfigSchema() }}</pre>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="测试调试" name="test">
        <div class="tab-content">
          <div class="test-section">
            <div class="test-header">
              <span>选择要测试的钩子</span>
              <el-select v-model="testHookIndex" style="width: 200px;" :disabled="hooks.length === 0">
                <el-option v-for="(hook, index) in hooks" :key="index" :label="hook.event" :value="index" />
              </el-select>
            </div>

            <div class="test-data">
              <div class="test-data-header">测试数据 (JSON)</div>
              <textarea
                v-model="testDataJson"
                class="test-data-textarea"
                placeholder='{"event": "after_form_submit", "payload": {"field1": "value1"}}'
              ></textarea>
            </div>

            <div class="test-actions">
              <el-button type="primary" :loading="testing" @click="runTest" :disabled="hooks.length === 0">
                <el-icon><VideoPlay /></el-icon> 执行测试
              </el-button>
            </div>

            <div v-if="testResult" class="test-result">
              <div class="result-header">
                <span>测试结果</span>
                <el-tag :type="testResult.success ? 'success' : 'danger'">
                  {{ testResult.success ? '成功' : '失败' }}
                </el-tag>
              </div>
              <pre class="result-content">{{ JSON.stringify(testResult, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, VideoPlay } from '@element-plus/icons-vue'
import api from '../../common/api/index'

const editMode = ref(false)
const saving = ref(false)
const testing = ref(false)
const activeTab = ref('basic')

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  version: '1.0.0',
  author: '',
  icon: 'puzzle-piece',
  category: 'custom',
  is_enabled: true
})

const hooks = ref<any[]>([])
const configItems = ref<any[]>([])

const testHookIndex = ref(0)
const testDataJson = ref('{}')
const testResult = ref<any>(null)

const availableEvents = ref([
  { code: 'before_form_render', description: '表单渲染前 - 在表单加载渲染之前执行' },
  { code: 'after_form_submit', description: '表单提交后 - 数据保存成功后执行' },
  { code: 'before_form_submit', description: '表单提交前 - 数据保存之前执行' },
  { code: 'after_data_delete', description: '数据删除后 - 数据删除成功后执行' },
  { code: 'on_list_load', description: '列表加载时 - 列表数据加载时执行' },
  { code: 'on_field_change', description: '字段值变更时 - 字段值变化时触发' },
  { code: 'on_cron_schedule', description: '定时任务 - 按cron表达式定时执行' },
  { code: 'on_api_called', description: 'API调用时 - 模板API被外部调用时触发' }
])

const hookTemplates: Record<string, string> = {
  'before_form_render': `def on_event(ctx):
    \"\"\"表单渲染前钩子\"\"\"
    # 获取字段列表
    fields = ctx.get('fields', [])
    
    # 示例：动态添加字段
    # new_field = {
    #     'name': 'calculated_field',
    #     'label': '计算字段',
    #     'type': 'text',
    #     'value': '自动计算'
    # }
    # fields.append(new_field)
    
    return {'result': 'ok', 'fields': fields}`,
  
  'after_form_submit': `def on_event(ctx):
    \"\"\"表单提交后钩子\"\"\"
    # 获取提交的数据
    data = ctx.get('data', {})
    user = ctx.get('user', {})
    
    # 示例：发送通知
    # ctx.send_notification(
    #     user_id=user.get('id'),
    #     title='数据已提交',
    #     content=f'您提交了数据: {data}'
    # )
    
    return {'result': 'ok', 'processed': True}`,
  
  'before_form_submit': `def on_event(ctx):
    \"\"\"表单提交前钩子\"\"\"
    # 获取提交的数据
    data = ctx.get('data', {})
    
    # 示例：数据验证
    # if not data.get('required_field'):
    #     return {'result': 'error', 'message': '必填字段不能为空'}
    
    # 示例：修改数据
    # data['modified_at'] = datetime.now().isoformat()
    
    return {'result': 'ok', 'data': data}`,
  
  'after_data_delete': `def on_event(ctx):
    \"\"\"数据删除后钩子\"\"\"
    # 获取被删除的数据
    deleted_data = ctx.get('data', {})
    
    # 示例：记录日志
    # ctx.log(f'数据已删除: {deleted_data}')
    
    return {'result': 'ok'}`,
  
  'on_list_load': `def on_event(ctx):
    \"\"\"列表加载时钩子\"\"\"
    # 获取筛选条件
    filters = ctx.get('filters', {})
    
    # 示例：添加额外筛选
    # filters['extra_condition'] = 'value'
    
    return {'result': 'ok', 'filters': filters}`,
  
  'on_field_change': `def on_event(ctx):
    \"\"\"字段值变更时钩子\"\"\"
    field_name = ctx.get('field')
    field_value = ctx.get('value')
    
    # 示例：联动计算
    # if field_name == 'category':
    #     ctx.set_field('subcategory', '')
    
    return {'result': 'ok'}`,
  
  'on_cron_schedule': `def on_event(ctx):
    \"\"\"定时任务钩子\"\"\"
    # 获取定时配置
    cron = ctx.get('cron', '')
    
    # 示例：执行定时任务
    # ctx.log(f'定时任务执行: {cron}')
    
    return {'result': 'ok'}`,
  
  'on_api_called': `def on_event(ctx):
    \"\"\"API调用时钩子\"\"\"
    path = ctx.get('path')
    method = ctx.get('method')
    
    # 示例：记录API调用
    # ctx.log(f'API调用: {method} {path}')
    
    return {'result': 'ok'}`
}

function getEventDescription(eventCode: string) {
  const event = availableEvents.value.find(e => e.code === eventCode)
  return event?.description || '未知事件'
}

function addHook() {
  hooks.value.push({
    event: 'after_form_submit',
    code: ''
  })
}

function removeHook(index: number) {
  hooks.value.splice(index, 1)
}

function copyHook(index: number) {
  const hook = { ...hooks.value[index] }
  hooks.value.splice(index + 1, 0, hook)
}

function loadHookTemplate(index: number) {
  const hook = hooks.value[index]
  if (hook.event && hookTemplates[hook.event]) {
    hook.code = hookTemplates[hook.event]
  }
}

function addConfigItem() {
  configItems.value.push({
    key: '',
    label: '',
    type: 'string',
    default: '',
    options: '',
    description: ''
  })
}

function removeConfigItem(index: number) {
  configItems.value.splice(index, 1)
}

function getConfigSchema() {
  const schema: Record<string, any> = {
    type: 'object',
    properties: {},
    required: []
  }
  
  configItems.value.forEach(item => {
    if (!item.key) return
    schema.properties[item.key] = {
      type: item.type === 'number' ? 'number' : item.type === 'boolean' ? 'boolean' : 'string',
      title: item.label || item.key,
      description: item.description || '',
      default: item.type === 'number' ? (Number(item.default) || 0) : 
               item.type === 'boolean' ? (item.default === 'true' || item.default === true) : 
               item.default || ''
    }
    if (item.type === 'select' && item.options) {
      schema.properties[item.key].enum = item.options.split(',').map((o: string) => o.trim())
    }
  })
  
  return JSON.stringify(schema, null, 2)
}

function resetForm() {
  form.name = ''
  form.display_name = ''
  form.description = ''
  form.version = '1.0.0'
  form.author = ''
  form.icon = 'puzzle-piece'
  form.category = 'custom'
  form.is_enabled = true
  hooks.value = []
  configItems.value = []
  editMode.value = false
}

async function savePlugin() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入插件标识')
    return
  }
  if (!form.display_name.trim()) {
    ElMessage.warning('请输入显示名称')
    return
  }

  saving.value = true
  try {
    const hookCode: Record<string, string> = {}
    hooks.value.forEach(hook => {
      if (hook.event && hook.code) {
        hookCode[hook.event] = hook.code
      }
    })

    const configSchema = JSON.parse(getConfigSchema())

    const pluginData = {
      name: form.name,
      display_name: form.display_name,
      description: form.description,
      version: form.version,
      author: form.author,
      icon: form.icon,
      category: form.category,
      is_enabled: form.is_enabled,
      hook_code: hookCode,
      config: configSchema
    }

    if (editMode.value) {
      await api.put(`/plugins/${form.name}`, pluginData)
      ElMessage.success('插件更新成功')
    } else {
      await api.post('/plugins/', pluginData)
      ElMessage.success('插件创建成功')
      resetForm()
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function runTest() {
  if (hooks.value.length === 0) return

  testing.value = true
  try {
    const hook = hooks.value[testHookIndex.value]
    let testData = {}
    if (testDataJson.value.trim()) {
      testData = JSON.parse(testDataJson.value)
    }

    const res = await api.post('/plugins/test-hook', {
      code_snippet: hook.code,
      event: hook.event,
      payload: testData
    })

    testResult.value = res.data
  } catch (e: any) {
    testResult.value = {
      success: false,
      error: e.response?.data?.detail || e.message || '测试失败'
    }
  } finally {
    testing.value = false
  }
}

async function loadPluginData(pluginId: string) {
  try {
    const res = await api.get(`/plugins/${pluginId}`)
    if (res.success && res.data) {
      const plugin = res.data
      form.name = plugin.name || ''
      form.display_name = plugin.display_name || ''
      form.description = plugin.description || ''
      form.version = plugin.version || '1.0.0'
      form.author = plugin.author || ''
      form.icon = plugin.icon || 'puzzle-piece'
      form.category = plugin.category || 'custom'
      form.is_enabled = plugin.is_enabled !== undefined ? plugin.is_enabled : true
      
      // 加载钩子函数
      hooks.value = []
      if (plugin.hook_code && typeof plugin.hook_code === 'object') {
        for (const [event, code] of Object.entries(plugin.hook_code)) {
          hooks.value.push({
            event,
            code: code as string
          })
        }
      } else if (plugin.hook_events && plugin.code_snippet) {
        hooks.value.push({
          event: plugin.hook_events[0] || 'after_form_submit',
          code: plugin.code_snippet
        })
      }
      
      // 加载配置参数
      if (plugin.config && plugin.config.properties) {
        configItems.value = []
        for (const [key, prop] of Object.entries(plugin.config.properties)) {
          const p = prop as any
          configItems.value.push({
            key,
            label: p.title || key,
            type: p.type === 'number' ? 'number' : p.type === 'boolean' ? 'boolean' : 'string',
            default: String(p.default !== undefined ? p.default : ''),
            options: p.enum ? (p.enum as string[]).join(',') : '',
            description: p.description || ''
          })
        }
      }
    }
  } catch (e: any) {
    ElMessage.error('加载插件数据失败: ' + (e.message || '未知错误'))
  }
}

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  const pluginId = params.get('id')
  if (pluginId) {
    editMode.value = true
    loadPluginData(pluginId)
  }
})
</script>

<style scoped>
.plugin-designer {
  padding: 24px;
  min-height: 100%;
}

.pd-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.pd-title h2 {
  margin: 0;
  font-size: 20px;
}

.pd-subtitle {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.pd-actions {
  display: flex;
  gap: 8px;
}

.pd-tabs {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.tab-content {
  padding: 20px;
}

.basic-form {
  max-width: 600px;
}

.hooks-header,
.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
}

.hooks-empty,
.config-empty {
  padding: 40px;
  text-align: center;
}

.hooks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hook-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.hook-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.hook-actions {
  display: flex;
  gap: 8px;
}

.hook-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.hook-code-editor {
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-size: 13px;
}

.code-textarea {
  width: 100%;
  min-height: 200px;
  padding: 12px;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 13px;
  line-height: 1.5;
  border: none;
  resize: vertical;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.config-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.config-intro {
  margin-bottom: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 6px;
  color: #67c23a;
  font-size: 13px;
}

.config-preview {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.preview-header {
  font-weight: 500;
  margin-bottom: 12px;
}

.preview-code {
  background: #1f2937;
  color: #e5e7eb;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.test-section {
  max-width: 800px;
}

.test-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-weight: 500;
}

.test-data {
  margin-bottom: 16px;
}

.test-data-header {
  margin-bottom: 8px;
  font-weight: 500;
}

.test-data-textarea {
  width: 100%;
  min-height: 150px;
  padding: 12px;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 13px;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  resize: vertical;
}

.test-actions {
  margin-bottom: 24px;
}

.test-result {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
}

.result-content {
  background: #fff;
  padding: 12px;
  border-radius: 6px;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
}
</style>