<template>
  <div class="tools-panel">
    <div class="panel-header">
      <h3>可用工具</h3>
      <el-button type="primary" size="small" @click="loadTools" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <el-table :data="tools" style="width:100%" v-loading="loading" empty-text="暂无可用工具">
      <el-table-column prop="name" label="工具名称" width="160" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.category || '通用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enabled" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
            {{ row.enabled ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { aiAPI } from '@/common/api'

const tools = ref<any[]>([])
const loading = ref(false)

async function loadTools() {
  loading.value = true
  try {
    const res = await aiAPI.getAgentEngineTools()
    if (res?.data) tools.value = Array.isArray(res.data) ? res.data : []
  } catch { /* 静默 */ }
  loading.value = false
}

onMounted(() => loadTools())
</script>

<style scoped>
.tools-panel { padding: 4px 0; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { margin: 0; font-size: 16px; }
</style>
