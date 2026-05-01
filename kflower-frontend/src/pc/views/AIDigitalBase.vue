<template>
  <div class="ai-digital-base-page">
    <div class="page-header">
      <h2>🤖 AI数字底座</h2>
      <p class="subtitle">AI基础设施核心，提供模型管理、推理服务、向量化、RAG检索等基础能力</p>
    </div>

    <el-row :gutter="20" class="status-cards">
      <el-col :span="8">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">AI网关</span>
              <el-tag :type="digitalBaseStatus?.health?.ai_gateway ? 'success' : 'danger'">
                {{ digitalBaseStatus?.health?.ai_gateway ? '运行中' : '异常' }}
              </el-tag>
            </div>
          </template>
          <p v-if="digitalBaseStatus">当前提供商：{{ digitalBaseStatus.gateway.current_provider || '未配置' }}，已配置 {{ digitalBaseStatus.gateway.available_providers.length }} 个提供商</p>
          <p v-else>支持多种AI模型供应商：SiliconFlow、DeepSeek、智谱AI、阿里云百炼、OpenAI、Ollama等</p>
          <div class="card-footer">
            <el-button type="primary" size="small" @click="$router.push('/settings?tab=ai-models')">配置模型</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">模型管理</span>
              <el-tag :type="digitalBaseStatus?.health?.model_manager ? 'success' : 'warning'">
                {{ digitalBaseStatus?.health?.model_manager ? '已配置' : '未配置' }}
              </el-tag>
            </div>
          </template>
          <p v-if="digitalBaseStatus">共 {{ digitalBaseStatus.model_manager.total_models }} 个模型，覆盖 {{ digitalBaseStatus.model_manager.providers.length }} 个提供商</p>
          <p v-else>支持动态模型列表、多模型配置、完整参数管理</p>
          <div class="card-footer">
            <el-button type="info" size="small" @click="$router.push('/settings?tab=ai-models')">查看模型</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">推理服务</span>
              <el-tag :type="digitalBaseStatus?.health?.inference_service ? 'success' : 'warning'">
                {{ digitalBaseStatus?.health?.inference_service ? '运行中' : '未配置' }}
              </el-tag>
            </div>
          </template>
          <p v-if="digitalBaseStatus">提供 {{ digitalBaseStatus.inference_service.capabilities.length }} 种AI能力，包括文本补全、意图分析、模板生成等</p>
          <p v-else>提供统一的AI推理API，支持流式响应、参数调优、多模型负载均衡</p>
          <div class="card-footer">
            <el-button type="info" size="small" @click="testInference">测试接口</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="module-info">
      <template #header>
        <div class="card-header">
          <span>📊 服务状态</span>
        </div>
      </template>
      
      <el-table :data="serviceStatus" style="width:100%">
        <el-table-column prop="service" label="服务名称" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '运行中' ? 'success' : row.status === '未配置' ? 'info' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="endpoint" label="API端点" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="checkService(row)">检查</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="development-info" style="margin-top:20px">
      <template #header>
        <div class="card-header">
          <span>🚀 开发进展</span>
        </div>
      </template>
      <div class="progress-section">
        <div class="progress-item">
          <div class="progress-label">核心架构</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">多模型支持</div>
          <el-progress :percentage="90" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">向量化集成</div>
          <el-progress :percentage="75" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">RAG检索</div>
          <el-progress :percentage="60" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { aiAPI } from '@/common/api'

interface ServiceStatus {
  service: string
  status: string
  version: string
  endpoint: string
}

const loading = ref(false)
const digitalBaseStatus = ref<any>(null)
const serviceStatus = ref<ServiceStatus[]>([
  { service: '模型网关', status: '运行中', version: 'v1.0', endpoint: '/api/v1/ai/chat' },
  { service: 'Embedding服务', status: '已配置', version: 'v1.0', endpoint: '/api/v1/ai/embed' },
  { service: 'RAG检索', status: '已配置', version: 'v0.9', endpoint: '/api/v1/ai/rag' },
  { service: '对话管理', status: '运行中', version: 'v1.0', endpoint: '/api/v1/ai/conversations' },
  { service: '工具调用', status: '开发中', version: 'v0.8', endpoint: '/api/v1/ai/tools' },
])

onMounted(() => {
  loadDigitalBaseStatus()
})

async function loadDigitalBaseStatus() {
  loading.value = true
  try {
    const res = await aiAPI.getDigitalBaseStatus()
    if (res.success) {
      digitalBaseStatus.value = res.data
      updateServiceStatus(res.data)
    } else {
      ElMessage.error('获取数字底座状态失败')
    }
  } catch (error) {
    console.error('加载数字底座状态失败:', error)
    ElMessage.error('加载数字底座状态失败')
  } finally {
    loading.value = false
  }
}

function updateServiceStatus(statusData: any) {
  // 根据实际状态更新服务状态表格
  const newStatus: ServiceStatus[] = []
  if (statusData.gateway) {
    newStatus.push({
      service: 'AI网关',
      status: statusData.gateway.current_provider ? '运行中' : '未配置',
      version: 'v1.0',
      endpoint: '/api/v1/ai/chat'
    })
  }
  if (statusData.model_manager) {
    newStatus.push({
      service: '模型管理',
      status: statusData.model_manager.total_models > 0 ? '已配置' : '未配置',
      version: 'v1.0',
      endpoint: '/api/v1/system/ai-models'
    })
  }
  if (statusData.inference_service) {
    newStatus.push({
      service: '推理服务',
      status: statusData.inference_service.service_ready ? '运行中' : '未配置',
      version: 'v1.0',
      endpoint: '/api/v1/ai/chat'
    })
  }
  if (statusData.conversation_manager) {
    newStatus.push({
      service: '对话管理',
      status: '运行中',
      version: 'v1.0',
      endpoint: '/api/v1/ai/conversations'
    })
  }
  if (statusData.agent_orchestrator) {
    newStatus.push({
      service: '智能体编排',
      status: statusData.agent_orchestrator.available_agents.length > 0 ? '已配置' : '未配置',
      version: 'v0.9',
      endpoint: '/api/v1/agent/agents'
    })
  }
  serviceStatus.value = newStatus
}

function testInference() {
  ElMessage.info('测试请求已发送，查看控制台日志')
  // 实际调用API测试
  fetch('/api/v1/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'Hello', model: 'default' })
  }).catch(() => {})
}

function checkService(row: any) {
  ElMessage.info(`检查 ${row.service} 服务状态...`)
  // 这里可以调用具体的健康检查API
}
</script>

<style scoped>
.ai-digital-base-page {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 8px 0 0;
  color: #606266;
  font-size: 14px;
}

.status-cards {
  margin-bottom: 24px;
}

.status-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
}

.card-footer {
  margin-top: 16px;
  text-align: right;
}

.module-info, .development-info {
  border-radius: 8px;
}

.progress-section {
  padding: 8px 0;
}

.progress-item {
  margin-bottom: 20px;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}
</style>