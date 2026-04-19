<template>
  <div class="plugin-editor">
    <div class="toolbar">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建插件
      </el-button>
      <el-button @click="loadSnippets">
        <el-icon><Collection /></el-icon> 代码片段库
      </el-button>
    </div>

    <el-table :data="plugins" v-loading="loading" border stripe>
      <el-table-column prop="name" label="插件名称" min-width="150" />
      <el-table-column prop="trigger_event" label="触发事件" width="140">
        <template #default="{ row }">
          <el-tag :type="getEventType(row.trigger_event)">{{ row.trigger_event }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_template_id" label="目标模板" width="150">
        <template #default="{ row }">
          {{ getTemplateName(row.target_template_id) || '全部模板' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_enabled" label="状态" width="80">
        <template #default="{ row }">
          <el-switch v-model="row.is_enabled" @change="togglePlugin(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="editPlugin(row)">编辑</el-button>
          <el-button type="success" link @click="testPlugin(row)">测试</el-button>
          <el-button type="danger" link @click="deletePlugin(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingPlugin ? '编辑插件' : '新建插件'"
      width="900px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="插件名称" required>
          <el-input v-model="form.name" placeholder="如：自动计算合计" />
        </el-form-item>
        <el-form-item label="触发事件">
          <el-select v-model="form.trigger_event" style="width: 100%">
            <el-option label="保存前 (before_save)" value="before_save" />
            <el-option label="保存后 (after_save)" value="after_save" />
            <el-option label="删除前 (before_delete)" value="before_delete" />
            <el-option label="删除后 (after_delete)" value="after_delete" />
            <el-option label="加载时 (on_load)" value="on_load" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标模板">
          <el-select v-model="form.target_template_id" clearable placeholder="留空表示应用于全部模板" style="width: 100%">
            <el-option
              v-for="tpl in templates"
              :key="tpl.id"
              :label="tpl.name"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="插件代码" required>
          <el-input
            v-model="form.script_code"
            type="textarea"
            :rows="15"
            placeholder="在此编写Python代码。可使用 context.data, context.db, context.user_id 等变量。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlugin" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog v-model="testDialogVisible" title="测试结果" width="600px">
      <el-alert
        :type="testResult.success ? 'success' : 'error'"
        :closable="false"
        show-icon
      >
        <template #title>
          {{ testResult.success ? '✓ 执行成功' : '✗ 执行失败' }}
        </template>
      </el-alert>
      <div v-if="testResult.error" class="test-error">
        <h4>错误信息：</h4>
        <pre>{{ testResult.error }}</pre>
      </div>
      <div v-if="testResult.output !== undefined" class="test-output">
        <h4>输出结果：</h4>
        <pre>{{ JSON.stringify(testResult.output, null, 2) }}</pre>
      </div>
    </el-dialog>

    <!-- 代码片段对话框 -->
    <el-dialog v-model="snippetDialogVisible" title="代码片段库" width="700px">
      <el-table :data="snippets" border>
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="trigger" label="触发事件" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ row.trigger }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="useSnippet(row)">使用</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Collection } from '@element-plus/icons-vue'
import { appAPI } from '@/common/api/myApps'
import { templateAPI } from '@/common/api'

const props = defineProps<{
  appId: number
}>()

const plugins = ref<any[]>([])
const templates = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingPlugin = ref<any>(null)
const saving = ref(false)
const testDialogVisible = ref(false)
const testResult = ref<any>({})
const snippetDialogVisible = ref(false)
const snippets = ref<any[]>([])

const form = reactive({
  name: '',
  trigger_event: 'after_save',
  target_template_id: null as number | null,
  script_code: `# 在此编写 Python 代码
# 可用的上下文变量:
#   context.data      - 当前操作的数据
#   context.old_data  - 更新前的数据（仅更新/删除时）
#   context.user_id   - 当前用户ID
#   context.template_id - 当前模板ID
# 可用的方法:
#   context.update_record(template_id, record_id, data)  - 更新记录
#   context.create_record(template_id, data)            - 创建记录
#   context.query_records(template_id, filters, limit)  - 查询记录
#   context.send_notification(user_id, title, content) - 发送通知
#   context.log(message)                               - 记录日志

def after_save(context):
    context.log("插件执行成功")
`
})

function getEventType(event: string) {
  const types: Record<string, string> = {
    before_save: 'warning',
    after_save: 'success',
    before_delete: 'danger',
    after_delete: 'info',
    on_load: 'primary'
  }
  return types[event] || 'info'
}

async function loadPlugins() {
  loading.value = true
  try {
    const res: any = await appAPI.listPlugins(props.appId)
    plugins.value = res.data || res || []
  } catch (e: any) {
    ElMessage.error('加载插件失败')
  } finally {
    loading.value = false
  }
}

async function loadTemplates() {
  try {
    const res: any = await templateAPI.list({ limit: 100, is_published: true })
    templates.value = res.data || res || []
  } catch (e) {
    console.error('Load templates failed', e)
  }
}

function getTemplateName(id: number | null) {
  if (!id) return null
  const tpl = templates.value.find(t => t.id === id)
  return tpl?.name
}

async function loadSnippets() {
  try {
    const res: any = await appAPI.getSnippets()
    snippets.value = res.data || []
    snippetDialogVisible.value = true
  } catch (e) {
    ElMessage.error('加载代码片段失败')
  }
}

function useSnippet(snippet: any) {
  form.script_code = snippet.code
  form.trigger_event = snippet.trigger
  snippetDialogVisible.value = false
  ElMessage.success(`已加载代码片段：${snippet.name}`)
}

function openCreateDialog() {
  editingPlugin.value = null
  Object.assign(form, {
    name: '',
    trigger_event: 'after_save',
    target_template_id: null,
    script_code: `# 在此编写 Python 代码

def after_save(context):
    context.log("插件执行成功")
`
  })
  dialogVisible.value = true
}

function editPlugin(row: any) {
  editingPlugin.value = row
  Object.assign(form, {
    name: row.name,
    trigger_event: row.trigger_event,
    target_template_id: row.target_template_id,
    script_code: row.script_code
  })
  dialogVisible.value = true
}

async function savePlugin() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写插件名称')
    return
  }
  if (!form.script_code.trim()) {
    ElMessage.warning('请编写插件代码')
    return
  }
  saving.value = true
  try {
    if (editingPlugin.value) {
      await appAPI.updatePlugin(editingPlugin.value.id, form)
      ElMessage.success('更新成功')
    } else {
      await appAPI.addPlugin(props.appId, form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadPlugins()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function togglePlugin(row: any) {
  try {
    await appAPI.updatePlugin(row.id, { is_enabled: row.is_enabled })
    ElMessage.success(row.is_enabled ? '已启用' : '已禁用')
  } catch (e) {
    row.is_enabled = !row.is_enabled
    ElMessage.error('更新失败')
  }
}

async function testPlugin(row: any) {
  testResult.value = { success: false, error: '测试中...' }
  testDialogVisible.value = true
  try {
    const res: any = await appAPI.testPlugin(row.id, {
      mock_data: { id: 1, name: '测试数据' }
    })
    testResult.value = res.data || res
  } catch (e: any) {
    testResult.value = { success: false, error: e.message }
  }
}

async function deletePlugin(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除插件「${row.name}」吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await appAPI.deletePlugin(row.id)
    ElMessage.success('删除成功')
    await loadPlugins()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadPlugins()
  loadTemplates()
})
</script>

<style scoped>
.plugin-editor {
  padding: 16px;
}
.toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}
.test-error,
.test-output {
  margin-top: 16px;
}
.test-error pre,
.test-output pre {
  background: var(--el-fill-color);
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
}
</style>
