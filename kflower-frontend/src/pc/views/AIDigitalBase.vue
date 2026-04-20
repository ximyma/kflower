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
              <span class="card-title">模型管理</span>
              <el-tag type="success">已启用</el-tag>
            </div>
          </template>
          <p>支持多种AI模型供应商：SiliconFlow、DeepSeek、智谱AI、阿里云百炼、OpenAI、Ollama等</p>
          <div class="card-footer">
            <el-button type="primary" size="small" @click="$router.push('/settings?tab=ai-models')">配置模型</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">推理服务</span>
              <el-tag type="success">运行中</el-tag>
            </div>
          </template>
          <p>提供统一的AI推理API，支持流式响应、参数调优、多模型负载均衡</p>
          <div class="card-footer">
            <el-button type="info" size="small" @click="testInference">测试接口</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">向量化服务</span>
              <el-tag type="warning">部分配置</el-tag>
            </div>
          </template>
          <p>Embedding模型管理，支持本地模型和API模型，为RAG检索提供向量化能力</p>
          <div class="card-footer">
            <el-button type="primary" size="small" @click="$router.push('/settings?tab=embedding')">配置Embedding</el-button>
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
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const serviceStatus = ref([
  { service: '模型网关', status: '运行中', version: 'v1.0', endpoint: '/api/v1/ai/chat' },
  { service: 'Embedding服务', status: '已配置', version: 'v1.0', endpoint: '/api/v1/ai/embed' },
  { service: 'RAG检索', status: '已配置', version: 'v0.9', endpoint: '/api/v1/ai/rag' },
  { service: '对话管理', status: '运行中', version: 'v1.0', endpoint: '/api/v1/ai/conversations' },
  { service: '工具调用', status: '开发中', version: 'v0.8', endpoint: '/api/v1/ai/tools' },
])

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