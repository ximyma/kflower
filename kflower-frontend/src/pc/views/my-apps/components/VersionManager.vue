<template>
  <div class="version-manager">
    <div class="toolbar">
      <el-button type="primary" @click="createVersion" :loading="creating">
        <el-icon><Plus /></el-icon> 创建版本快照
      </el-button>
      <el-alert
        title="版本快照保存应用的完整状态，包括菜单、关系、插件配置，可随时恢复"
        type="info"
        :closable="false"
        style="flex: 1; margin-left: 16px;"
      />
    </div>

    <!-- 版本列表 -->
    <el-table :data="versions" v-loading="loading" border stripe>
      <el-table-column prop="version" label="版本号" width="100">
        <template #default="{ row }">
          <el-tag>v{{ row.version }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="版本说明" min-width="200">
        <template #default="{ row }">
          {{ row.description || '无说明' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_by_name" label="创建人" width="120" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="restoreVersion(row)" :loading="restoring === row.id">
            恢复
          </el-button>
          <el-button type="info" link @click="previewVersion(row)">
            预览
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建版本对话框 -->
    <el-dialog v-model="dialogVisible" title="创建版本快照" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="版本说明" required>
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="描述本次版本的变更内容，如：新增审批流程、优化表单布局等"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreateVersion" :loading="creating">确定</el-button>
      </template>
    </el-dialog>

    <!-- 版本预览对话框 -->
    <el-dialog v-model="previewVisible" title="版本快照预览" width="600px">
      <div v-if="previewData" class="preview-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="版本">{{ previewData.version }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(previewData.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="说明">{{ previewData.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="菜单数量">{{ previewData.snapshot?.menus?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="关系数量">{{ previewData.snapshot?.relations?.length || 0 }}</el-descriptions-item>
          <el-descriptions-item label="插件数量">{{ previewData.snapshot?.plugins?.length || 0 }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>快照详情</el-divider>

        <el-tabs>
          <el-tab-pane label="菜单">
            <pre class="snapshot-code">{{ JSON.stringify(previewData.snapshot?.menus || [], null, 2) }}</pre>
          </el-tab-pane>
          <el-tab-pane label="关系">
            <pre class="snapshot-code">{{ JSON.stringify(previewData.snapshot?.relations || [], null, 2) }}</pre>
          </el-tab-pane>
          <el-tab-pane label="插件">
            <pre class="snapshot-code">{{ JSON.stringify(previewData.snapshot?.plugins || [], null, 2) }}</pre>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'

const props = defineProps<{
  appId: number
}>()

const versions = ref<any[]>([])
const loading = ref(false)
const creating = ref(false)
const restoring = ref<number | null>(null)
const dialogVisible = ref(false)
const previewVisible = ref(false)
const previewData = ref<any>(null)

const form = ref({
  description: ''
})

// 加载版本列表
async function loadVersions() {
  loading.value = true
  try {
    const res: any = await appAPI.listVersions(props.appId)
    versions.value = res || []
  } catch (e: any) {
    ElMessage.error('加载版本失败：' + (e.message || ''))
  } finally {
    loading.value = false
  }
}

// 创建版本
function createVersion() {
  form.value.description = ''
  dialogVisible.value = true
}

// 确认创建版本
async function confirmCreateVersion() {
  if (!form.value.description) {
    ElMessage.warning('请输入版本说明')
    return
  }

  creating.value = true
  try {
    await appAPI.createVersion(props.appId, {
      description: form.value.description
    })
    ElMessage.success('版本快照创建成功')
    dialogVisible.value = false
    loadVersions()
  } catch (e: any) {
    ElMessage.error('创建失败：' + (e.message || ''))
  } finally {
    creating.value = false
  }
}

// 恢复版本
async function restoreVersion(version: any) {
  try {
    await ElMessageBox.confirm(
      `确定恢复到版本 v${version.version} 吗？当前未保存的更改将丢失。`,
      '恢复版本',
      { type: 'warning' }
    )

    restoring.value = version.id
    await appAPI.restoreVersion(props.appId, version.id)
    ElMessage.success('已恢复到版本 v' + version.version)
    // 通知父组件刷新
    emit('restored')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('恢复失败：' + (e.message || ''))
    }
  } finally {
    restoring.value = null
  }
}

// 预览版本
async function previewVersion(version: any) {
  previewData.value = version
  previewVisible.value = true
}

// 格式化日期
function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const emit = defineEmits(['restored'])

onMounted(() => {
  loadVersions()
})
</script>

<style scoped lang="scss">
.version-manager {
  padding: 20px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.preview-content {
  .snapshot-code {
    max-height: 300px;
    overflow: auto;
    background: var(--el-fill-color-light);
    padding: 12px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
