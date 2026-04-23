<template>
  <div class="knowledge-config">
    <el-alert
      title="将知识库绑定到应用，AI 助手和表单可自动检索相关内容"
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    />

    <!-- 已绑定的知识库 -->
    <div class="bound-kbs">
      <h4>已绑定的知识库</h4>
      <el-table :data="boundKbs" border style="margin-bottom: 16px">
        <el-table-column prop="name" label="知识库名称" min-width="150" />
        <el-table-column prop="doc_count" label="文档数" width="100" align="center" />
        <el-table-column label="自动索引" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.auto_index" type="success" size="small">开启</el-tag>
            <el-tag v-else type="info" size="small">关闭</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="搜索范围" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ searchScopeLabel(row.search_scope) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="editKb(row)">配置</el-button>
            <el-button link type="danger" @click="unbindKb(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加知识库 -->
    <div class="add-kb">
      <h4>添加知识库</h4>
      <div class="add-form">
        <el-select
          v-model="newKbId"
          filterable
          placeholder="选择要绑定的知识库"
          style="width: 300px; margin-right: 12px"
        >
          <el-option
            v-for="kb in availableKbs"
            :key="kb.id"
            :label="kb.name"
            :value="kb.id"
          >
            <span>{{ kb.name }}</span>
            <span style="color: var(--el-text-color-secondary); font-size: 12px; margin-left: 8px">
              {{ kb.doc_count || 0 }} 文档
            </span>
          </el-option>
        </el-select>
        <el-button type="primary" @click="bindKb" :disabled="!newKbId">绑定</el-button>
      </div>
    </div>

    <!-- 配置对话框 -->
    <el-dialog v-model="dialogVisible" title="知识库配置" width="500px">
      <el-form :model="kbForm" label-width="100px">
        <el-form-item label="知识库名称">
          <el-input v-model="kbForm.name" disabled />
        </el-form-item>
        <el-form-item label="自动索引">
          <el-switch v-model="kbForm.auto_index" />
          <span style="margin-left: 8px; color: var(--el-text-color-secondary); font-size: 12px">
            新增文档时自动向量化和索引
          </span>
        </el-form-item>
        <el-form-item label="搜索范围">
          <el-select v-model="kbForm.search_scope" style="width: 100%">
            <el-option label="仅知识库" value="kb" />
            <el-option label="应用内" value="app" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="分块大小">
          <el-input-number
            v-model="kbForm.chunk_size"
            :min="100"
            :max="2000"
            :step="100"
          />
          <span style="margin-left: 8px; color: var(--el-text-color-secondary)">字符</span>
        </el-form-item>
        <el-form-item label="检索数量">
          <el-input-number
            v-model="kbForm.top_k"
            :min="1"
            :max="20"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKbConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appAPI } from '@/common/api/myApps'
import { knowledgeAPI } from '@/common/api'

const props = defineProps<{ appId: number }>()

// 数据
const allKbs = ref<any[]>([])
const boundKbIds = ref<number[]>([])
const kbConfigs = ref<Record<number, any>>({})
const newKbId = ref<number | null>(null)
const dialogVisible = ref(false)
const editingKb = ref<any>(null)

const kbForm = ref({
  name: '',
  auto_index: true,
  search_scope: 'app',
  chunk_size: 500,
  top_k: 5
})

// 计算属性
const boundKbs = computed(() => {
  return boundKbIds.value.map(id => {
    const kb = allKbs.value.find(k => k.id === id) || { id, name: `知识库 #${id}` }
    const config = kbConfigs.value[id] || {}
    return {
      ...kb,
      ...config,
      auto_index: config.auto_index ?? true,
      search_scope: config.search_scope || 'app',
      chunk_size: config.chunk_size || 500,
      top_k: config.top_k || 5
    }
  })
})

const availableKbs = computed(() => {
  return allKbs.value.filter(kb => !boundKbIds.value.includes(kb.id))
})

// 方法
function searchScopeLabel(scope: string) {
  const labels: Record<string, string> = {
    kb: '仅知识库',
    app: '应用内',
    all: '全部'
  }
  return labels[scope] || scope
}

async function loadKbs() {
  try {
    const res: any = await knowledgeAPI.listBases({ limit: 100 })
    allKbs.value = res.data || res || []
  } catch (e: any) {
    console.error('Load kbs failed', e)
  }
}

async function loadAppConfig() {
  try {
    const res: any = await appAPI.get(props.appId)
    const kbIds = res.knowledge_base_ids || []
    const kbConfig = res.knowledge_config || {}
    boundKbIds.value = kbIds
    kbConfigs.value = kbConfig
  } catch (e: any) {
    console.error('Load app config failed', e)
  }
}

async function bindKb() {
  if (!newKbId.value) return

  const kb = allKbs.value.find(k => k.id === newKbId.value)
  if (!kb) return

  if (!boundKbIds.value.includes(newKbId.value)) {
    boundKbIds.value.push(newKbId.value)
    kbConfigs.value[newKbId.value] = {
      auto_index: true,
      search_scope: 'app',
      chunk_size: 500,
      top_k: 5
    }
  }

  await saveConfig()
  newKbId.value = null
  ElMessage.success(`已绑定知识库：${kb.name}`)
}

async function unbindKb(row: any) {
  try {
    await ElMessageBox.confirm(`确定解绑知识库「${row.name}」？`, '确认解绑', { type: 'warning' })
    boundKbIds.value = boundKbIds.value.filter(id => id !== row.id)
    delete kbConfigs.value[row.id]
    await saveConfig()
    ElMessage.success('已解绑')
  } catch (e) {
    if (e !== 'cancel') console.error('Unbind failed', e)
  }
}

function editKb(row: any) {
  editingKb.value = row
  Object.assign(kbForm.value, {
    name: row.name,
    auto_index: row.auto_index,
    search_scope: row.search_scope || 'app',
    chunk_size: row.chunk_size || 500,
    top_k: row.top_k || 5
  })
  dialogVisible.value = true
}

async function saveKbConfig() {
  if (!editingKb.value) return

  kbConfigs.value[editingKb.value.id] = {
    auto_index: kbForm.value.auto_index,
    search_scope: kbForm.value.search_scope,
    chunk_size: kbForm.value.chunk_size,
    top_k: kbForm.value.top_k
  }

  await saveConfig()
  dialogVisible.value = false
  ElMessage.success('配置已保存')
}

async function saveConfig() {
  try {
    await appAPI.update(props.appId, {
      knowledge_base_ids: boundKbIds.value,
      knowledge_config: kbConfigs.value
    })
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  }
}

onMounted(async () => {
  await Promise.all([loadKbs(), loadAppConfig()])
})
</script>

<style scoped>
.knowledge-config {
  padding: 16px;
}

h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.add-form {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
