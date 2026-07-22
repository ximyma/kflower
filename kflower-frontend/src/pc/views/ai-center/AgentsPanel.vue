<template>
  <div class="agents-panel">
    <div class="panel-header">
      <h3>智能体列表</h3>
      <el-button type="primary" size="small" @click="showDialog = true">
        <el-icon><Plus /></el-icon> 新建
      </el-button>
    </div>

    <el-table :data="agents" style="width:100%" v-loading="loading" empty-text="暂无智能体">
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.type || 'general' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === '在线' ? 'success' : 'info'" size="small">
            {{ row.status || '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button type="primary" size="small" link @click="toggleStatus(row)">
            {{ row.status === '在线' ? '停用' : '启用' }}
          </el-button>
          <el-button type="danger" size="small" link @click="deleteAgent(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建对话框 -->
    <el-dialog v-model="showDialog" title="新建智能体" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="智能体名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="通用助手" value="general" />
            <el-option label="数据分析" value="analytics" />
            <el-option label="模板设计" value="template" />
            <el-option label="工作流" value="workflow" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="在线">在线</el-radio>
            <el-radio value="离线">离线</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="createAgent" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { aiAPI } from '@/common/api'

const agents = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const creating = ref(false)
const form = ref({ name: '', type: 'general', description: '', status: '在线' })

async function loadAgents() {
  loading.value = true
  try {
    const res = await aiAPI.getAgentEngineAgents()
    if (res?.data) agents.value = Array.isArray(res.data) ? res.data : []
  } catch { /* 静默 */ }
  loading.value = false
}

async function createAgent() {
  if (!form.value.name) { ElMessage.warning('请输入名称'); return }
  creating.value = true
  try {
    await aiAPI.createAgent(form.value)
    ElMessage.success('创建成功')
    showDialog.value = false
    form.value = { name: '', type: 'general', description: '', status: '在线' }
    await loadAgents()
  } catch (e: any) { ElMessage.error(e?.message || '创建失败') }
  creating.value = false
}

async function toggleStatus(row: any) {
  const newStatus = row.status === '在线' ? '离线' : '在线'
  try {
    await aiAPI.updateAgent(row.id, { status: newStatus })
    ElMessage.success('状态已更新')
    await loadAgents()
  } catch (e: any) { ElMessage.error(e?.message || '操作失败') }
}

async function deleteAgent(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除智能体「${row.name}」？`, '确认删除', { type: 'warning' })
    await aiAPI.deleteAgent(row.id)
    ElMessage.success('删除成功')
    await loadAgents()
  } catch { /* 取消 */ }
}

onMounted(() => loadAgents())
</script>

<style scoped>
.agents-panel { padding: 4px 0; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { margin: 0; font-size: 16px; }
</style>
