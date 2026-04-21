<template>
  <div class="app-agents">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>我的智能体</h2>
      <el-button type="primary" size="small" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 创建智能体
      </el-button>
    </div>
    
    <!-- 状态概览 -->
    <div class="stats-cards">
      <div class="stat-item">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.active }}</div>
        <div class="stat-label">运行中</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.tasks }}</div>
        <div class="stat-label">任务数</div>
      </div>
    </div>
    
    <!-- 智能体列表 -->
    <div class="agent-list" v-loading="loading">
      <div v-if="agents.length === 0 && !loading" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Cpu /></el-icon>
        <p>暂无智能体</p>
        <el-button type="primary" size="small" @click="showCreateDialog = true">创建第一个智能体</el-button>
      </div>
      
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="agent-item"
        @click="viewAgent(agent)"
      >
        <div class="agent-avatar" :style="{ background: getAgentColor(agent.id) }">
          <el-icon :size="24"><component :is="agent.icon || 'Cpu'" /></el-icon>
        </div>
        <div class="agent-info">
          <h3>{{ agent.name }}</h3>
          <p class="agent-type">{{ agent.type || '通用智能体' }}</p>
          <div class="agent-status">
            <el-tag size="small" :type="agent.status === 'active' ? 'success' : 'info'">
              {{ agent.status === 'active' ? '运行中' : '未启用' }}
            </el-tag>
          </div>
        </div>
        <div class="agent-actions">
          <el-switch
            v-model="agent.enabled"
            size="small"
            @click.stop
            @change="toggleAgent(agent)"
          />
          <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, agent)">
            <el-icon :size="20" color="#909399"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="chat">对话</el-dropdown-item>
                <el-dropdown-item command="edit">编辑</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
    
    <!-- 创建智能体对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建智能体" width="90%" :close-on-click-modal="false">
      <el-form :model="newAgent" label-position="top">
        <el-form-item label="智能体名称" required>
          <el-input v-model="newAgent.name" placeholder="请输入智能体名称" />
        </el-form-item>
        <el-form-item label="智能体类型">
          <el-select v-model="newAgent.type" placeholder="选择类型" style="width: 100%">
            <el-option label="对话助手" value="chat" />
            <el-option label="任务执行" value="task" />
            <el-option label="数据分析" value="analysis" />
            <el-option label="文档处理" value="document" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newAgent.description" type="textarea" :rows="2" placeholder="智能体描述（可选）" />
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input v-model="newAgent.system_prompt" type="textarea" :rows="3" placeholder="定义智能体的行为和能力" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Cpu, MoreFilled } from '@element-plus/icons-vue'
import { aiAPI } from '../../common/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const creating = ref(false)
const agents = ref<any[]>([])
const showCreateDialog = ref(false)

const stats = ref({
  total: 0,
  active: 0,
  tasks: 0
})

const newAgent = ref({
  name: '',
  type: 'chat',
  description: '',
  system_prompt: ''
})

function getAgentColor(id: number) {
  const colors = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  ]
  return colors[id % colors.length]
}

async function loadAgents() {
  loading.value = true
  try {
    const res = await aiAPI.getAgentEngineAgents()
    agents.value = res.agents || res || []
    stats.value.total = agents.value.length
    stats.value.active = agents.value.filter(a => a.status === 'active').length
  } catch (error) {
    console.error('加载智能体失败:', error)
    // 使用模拟数据
    agents.value = [
      { id: 1, name: '文档助手', type: '文档处理', status: 'active', enabled: true },
      { id: 2, name: '数据分析师', type: '数据分析', status: 'inactive', enabled: false }
    ]
    stats.value = { total: 2, active: 1, tasks: 5 }
  } finally {
    loading.value = false
  }
}

function viewAgent(agent: any) {
  ElMessageBox.confirm('智能体详情需要在电脑端查看和管理。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).catch(() => {})
}

async function toggleAgent(agent: any) {
  try {
    if (agent.enabled) {
      await aiAPI.updateAgent(agent.id, { status: 'active' })
      ElMessage.success('已启用')
    } else {
      await aiAPI.updateAgent(agent.id, { status: 'inactive' })
      ElMessage.success('已禁用')
    }
    loadAgents()
  } catch (error) {
    ElMessage.error('操作失败')
    agent.enabled = !agent.enabled // 回滚
  }
}

async function handleCommand(command: string, agent: any) {
  switch (command) {
    case 'chat':
      // 跳转到聊天
      break
    case 'edit':
      viewAgent(agent)
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(`确定要删除智能体"${agent.name}"吗？`, '删除确认', { type: 'warning' })
        await aiAPI.deleteAgent(agent.id)
        ElMessage.success('删除成功')
        loadAgents()
      } catch (e: any) {
        if (e !== 'cancel') ElMessage.error('删除失败')
      }
      break
  }
}

async function handleCreate() {
  if (!newAgent.value.name.trim()) {
    ElMessage.warning('请输入智能体名称')
    return
  }
  
  creating.value = true
  try {
    await aiAPI.createAgent({
      name: newAgent.value.name,
      type: newAgent.value.type,
      description: newAgent.value.description,
      system_prompt: newAgent.value.system_prompt
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newAgent.value = { name: '', type: 'chat', description: '', system_prompt: '' }
    loadAgents()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.app-agents {
  padding-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stat-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state p {
  margin: 16px 0;
}

.agent-item {
  background: white;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.agent-item:active {
  transform: scale(0.98);
}

.agent-avatar {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-info h3 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
}

.agent-type {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.agent-status {
  display: flex;
  align-items: center;
}

.agent-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
</style>
