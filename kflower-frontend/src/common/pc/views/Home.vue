<template>
  <div class="home-page">
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in stats" :key="stat.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-title">{{ stat.title }}</p>
              <p class="stat-value">{{ stat.value }}</p>
            </div>
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="24"><component :is="stat.icon" /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :xs="24" :md="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI 智能助手</span>
              <el-tag type="success" size="small">在线</el-tag>
            </div>
          </template>
          <div class="ai-prompt-area">
            <div style="margin-bottom: 12px;">
              <el-select v-model="selectedModelId" placeholder="选择AI模型" style="width: 100%">
                <el-option v-for="model in aiStore.models" :key="model.modelId" :label="model.modelName || model.modelId" :value="model.modelId">
                  <span>{{ model.modelName || model.modelId }}</span>
                  <el-tag size="small" type="info" style="margin-left:8px">{{ model.provider }}</el-tag>
                </el-option>
              </el-select>
            </div>
            <el-input
              v-model="aiPrompt"
              type="textarea"
              :rows="3"
              placeholder="输入您的需求，例如：帮我设计一个采购审批流程，请输出字段定义格式（type/label/name）的json文件，不要输出任何其他文字："
            />
            <div style="margin-top: 12px; display: flex; gap: 8px; align-items: center;">
              <el-button type="primary" @click="handleAIPrompt" :loading="aiLoading">
                <el-icon><MagicStick /></el-icon>
                提交给AI
              </el-button>
              <el-button text @click="goToSettings">
                <el-icon><Setting /></el-icon>
                AI配置
              </el-button>
            </div>
          </div>
          <div class="ai-suggestions" style="margin-top: 16px;">
            <p class="suggestions-title">快捷指令</p>
            <div class="suggestion-tags">
              <el-tag
                v-for="s in suggestions"
                :key="s"
                class="suggestion-tag"
                @click="aiPrompt = s"
              >{{ s }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="8">
        <el-card>
          <template #header>
            <span>待办事项</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="todo in todos"
              :key="todo.id"
              :timestamp="todo.time"
              :type="todo.type"
              placement="top"
            >
              <el-card>
                <h4>{{ todo.title }}</h4>
                <p>{{ todo.content }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 16px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>最近动态</span>
          </template>
          <el-table :data="recentActivities" style="width: 100%" v-loading="loading">
            <el-table-column prop="time" label="时间" width="180" />
            <el-table-column prop="user" label="操作人" width="120" />
            <el-table-column prop="action" label="操作" />
            <el-table-column prop="target" label="对象" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'warning'">
                  {{ row.status === 'success' ? '成功' : row.status === 'warning' ? '进行中' : row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Setting } from '@element-plus/icons-vue'
import { useAIStore } from '@/common/store/ai'
import { dashboardAPI } from '@/common/api'
import { useRouter } from 'vue-router'

const aiStore = useAIStore()
const router = useRouter()
const aiPrompt = ref('')
const aiLoading = ref(false)
const loading = ref(false)
const selectedModelId = ref('')

// 初始化模型选择
function initModelSelection() {
  if (aiStore.currentModel) {
    selectedModelId.value = aiStore.currentModel.modelId
  }
}

// 跳转到AI设置
function goToSettings() {
  router.push('/settings?tab=ai')
}

const stats = ref([
  { title: '模板数量', value: '-', icon: 'Document', color: '#409EFF' },
  { title: '工作流数', value: '-', icon: 'Grid', color: '#67C23A' },
  { title: '知识文档', value: '-', icon: 'Folder', color: '#E6A23C' },
  { title: 'AI对话', value: '-', icon: 'ChatDotRound', color: '#F56C6C' }
])

const todos = ref([
  { id: 1, title: '审批采购申请', content: '张三 提交的 #1001', time: '2026-04-14 09:00', type: 'warning' },
  { id: 2, title: '更新知识库', content: '上传产品手册 v2.0', time: '2026-04-13 16:00', type: 'primary' },
  { id: 3, title: '工作流设计', content: '完成请假审批配置', time: '2026-04-13 10:00', type: 'success' }
])

const recentActivities = ref<any[]>([])

const suggestions = [
  '设计一个客户管理流程',
  '创建一个采购审批模板',
  '上传产品知识文档',
  '生成月度报表'
]

async function loadDashboard() {
  loading.value = true
  try {
    const res: any = await dashboardAPI.getStats()
    if (res && res.success !== false) {
      const data = res.data || {}
      stats.value = [
        { title: '模板数量', value: data.template_count ?? 0, icon: 'Document', color: '#409EFF' },
        { title: '工作流数', value: data.workflow_count ?? 0, icon: 'Grid', color: '#67C23A' },
        { title: '知识文档', value: data.knowledge_doc_count ?? 0, icon: 'Folder', color: '#E6A23C' },
        { title: 'AI对话', value: data.ai_chat_count ?? 0, icon: 'ChatDotRound', color: '#F56C6C' }
      ]
    }
  } catch { /* API not ready */ }
  try {
    const res2: any = await dashboardAPI.getRecentActivities(5)
    if (res2 && res2.success !== false) {
      recentActivities.value = (res2.data || []).map((a: any) => ({
        time: a.created_at ? new Date(a.created_at).toLocaleString() : '-',
        user: a.user_name || a.operator || '-',
        action: a.action || '-',
        target: a.target || '-',
        status: a.status || 'success'
      }))
    }
  } catch { /* API not ready */ }
  loading.value = false
}

async function handleAIPrompt() {
  if (!aiPrompt.value.trim()) { ElMessage.warning('请输入您的需求'); return }
  
  // 切换到选中的模型
  if (selectedModelId.value) {
    aiStore.setModel(selectedModelId.value)
  }
  
  const msg = aiPrompt.value
  aiPrompt.value = ''  // 立即清空输入框
  await aiStore.sendMessage(msg)
  aiStore.toggleChat()
}

function openAIChat() { aiStore.toggleChat() }

onMounted(() => {
  loadDashboard()
  initModelSelection()
})
</script>

<style scoped>
.home-page { padding: 0; }
.stat-card { margin-bottom: 16px; }
.stat-content { display: flex; justify-content: space-between; align-items: center; }
.stat-info .stat-title { color: #909399; font-size: 13px; margin-bottom: 8px; }
.stat-info .stat-value { font-size: 24px; font-weight: bold; color: #303133; }
.stat-icon { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.suggestions-title { color: #909399; font-size: 13px; margin-bottom: 8px; }
.suggestion-tag { margin-right: 8px; margin-bottom: 8px; cursor: pointer; }
</style>
