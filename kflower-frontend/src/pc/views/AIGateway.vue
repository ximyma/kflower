<template>
  <div class="ai-gateway-page">
    <div class="page-header">
      <h2>🌐 AI网关</h2>
      <p class="subtitle">统一AI服务入口，提供请求路由、负载均衡、限流熔断、监控审计等功能</p>
    </div>

    <el-row :gutter="20" class="gateway-stats">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ formatNumber(stats.totalRequests) }}</div>
            <div class="stat-label">总请求量</div>
            <div class="stat-trend">今日 +{{ stats.todayRequests }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.avgLatency }}ms</div>
            <div class="stat-label">平均延迟</div>
            <div class="stat-trend">较昨日 {{ stats.latencyTrend > 0 ? '+' : '' }}{{ stats.latencyTrend }}ms</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.successRate }}%</div>
            <div class="stat-label">成功率</div>
            <div class="stat-trend">错误率 {{ (100 - stats.successRate).toFixed(1) }}%</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="16">
        <el-card class="traffic-card">
          <template #header>
            <div class="card-header">
              <span>📈 请求流量（最近24小时）</span>
              <div class="time-range">
                <el-radio-group v-model="timeRange" size="small">
                  <el-radio-button label="1h">1小时</el-radio-button>
                  <el-radio-button label="24h">24小时</el-radio-button>
                  <el-radio-button label="7d">7天</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="chart-placeholder">
            <div class="mock-chart">
              <div class="chart-title">请求量趋势图</div>
              <div class="chart-hint">实际图表需要接入监控系统</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="endpoint-card">
          <template #header>
            <div class="card-header">
              <span>🔗 服务端点</span>
            </div>
          </template>
          <el-table :data="endpoints" style="width:100%">
            <el-table-column prop="path" label="路径" width="180">
              <template #default="{ row }">
                <code class="path-code">{{ row.path }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="method" label="方法" width="80">
              <template #default="{ row }">
                <el-tag :type="row.method === 'POST' ? 'success' : 'primary'" size="small">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === '正常' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="12">
        <el-card class="model-routing-card">
          <template #header>
            <div class="card-header">
              <span>🔄 模型路由策略</span>
              <el-button type="primary" size="small" @click="editRouting">编辑策略</el-button>
            </div>
          </template>
          
          <el-table :data="routingStrategies" style="width:100%">
            <el-table-column prop="pattern" label="匹配模式" width="200">
              <template #default="{ row }">
                <code>{{ row.pattern }}</code>
              </template>
            </el-table-column>
            <el-table-column prop="model" label="目标模型" width="150" />
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.priority }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" size="small" @change="toggleStrategy(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="rate-limit-card">
          <template #header>
            <div class="card-header">
              <span>🚦 限流配置</span>
              <el-button type="primary" size="small" @click="addRateLimit">添加规则</el-button>
            </div>
          </template>
          
          <el-table :data="rateLimits" style="width:100%">
            <el-table-column prop="scope" label="作用域" width="120">
              <template #default="{ row }">
                <el-tag :type="row.scope === '用户' ? 'primary' : row.scope === 'IP' ? 'success' : 'warning'" size="small">{{ row.scope }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="limit" label="限制" width="100">
              <template #default="{ row }">
                {{ row.limit }}/{{ row.unit }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" size="small" @change="toggleRateLimit(row)" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="development-info" style="margin-top:24px">
      <template #header>
        <div class="card-header">
          <span>🚀 开发进展</span>
        </div>
      </template>
      <div class="progress-section">
        <div class="progress-item">
          <div class="progress-label">统一API网关</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">请求路由与负载均衡</div>
          <el-progress :percentage="90" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">限流熔断机制</div>
          <el-progress :percentage="70" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">监控与审计日志</div>
          <el-progress :percentage="60" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">模型故障转移</div>
          <el-progress :percentage="40" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { aiAPI } from '@/common/api/index'

const timeRange = ref('24h')

const stats = ref({
  totalRequests: 0,
  todayRequests: 0,
  avgLatency: 0,
  latencyTrend: 0,
  successRate: 0,
})

const endpoints = ref([])
const routingStrategies = ref([])
const rateLimits = ref([])

// 加载网关统计数据
async function loadGatewayStats() {
  try {
    const response = await aiAPI.getGatewayStats()
    if (response.success && response.data) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('加载网关统计失败:', error)
    ElMessage.error('加载网关统计失败，请检查网络连接')
  }
}

// 加载端点数据
async function loadEndpoints() {
  // TODO: 调用真实API获取端点列表
  // 暂时保留模拟数据
  endpoints.value = [
    { path: '/api/v1/ai/chat', method: 'POST', status: '正常' },
    { path: '/api/v1/ai/embed', method: 'POST', status: '正常' },
    { path: '/api/v1/ai/rag', method: 'POST', status: '正常' },
    { path: '/api/v1/ai/conversations', method: 'GET', status: '正常' },
    { path: '/api/v1/ai/tools', method: 'POST', status: '正常' },
    { path: '/api/v1/ai/models', method: 'GET', status: '正常' },
  ]
}

// 加载路由策略
async function loadRoutingStrategies() {
  // TODO: 调用真实API获取路由策略
  routingStrategies.value = [
    { pattern: '/chat/general', model: 'gpt-4', priority: 1, enabled: true },
    { pattern: '/chat/code', model: 'deepseek-coder', priority: 1, enabled: true },
    { pattern: '/chat/chinese', model: 'qwen-plus', priority: 2, enabled: true },
    { pattern: '/chat/fast', model: 'gpt-3.5-turbo', priority: 3, enabled: false },
    { pattern: '/embed/*', model: 'text-embedding-v2', priority: 1, enabled: true },
  ]
}

// 加载限流配置
async function loadRateLimits() {
  // TODO: 调用真实API获取限流配置
  rateLimits.value = [
    { scope: '用户', limit: 100, unit: '分钟', description: '普通用户聊天频率限制', enabled: true },
    { scope: '用户', limit: 1000, unit: '天', description: '每日总请求限制', enabled: true },
    { scope: 'IP', limit: 50, unit: '秒', description: 'IP防刷限制', enabled: true },
    { scope: '应用', limit: 500, unit: '分钟', description: '应用级限制', enabled: false },
  ]
}

// 初始化加载数据
onMounted(() => {
  loadGatewayStats()
  loadEndpoints()
  loadRoutingStrategies()
  loadRateLimits()
})

function formatNumber(num: number) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function editRouting() {
  ElMessage.info('编辑路由策略功能开发中')
}

function toggleStrategy(row: any) {
  ElMessage.success(`${row.pattern} ${row.enabled ? '已启用' : '已禁用'}`)
}

function addRateLimit() {
  ElMessage.info('添加限流规则功能开发中')
}

function toggleRateLimit(row: any) {
  ElMessage.success(`${row.description} ${row.enabled ? '已启用' : '已禁用'}`)
}
</script>

<style scoped>
.ai-gateway-page {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.gateway-stats {
  margin-bottom: 24px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  text-align: center;
  padding: 16px 0;
}

.stat-number {
  font-size: 32px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
  color: #67C23A;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-range {
  margin-left: auto;
}

.traffic-card, .endpoint-card, .model-routing-card, .rate-limit-card {
  height: 100%;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
  border-radius: 4px;
}

.mock-chart {
  text-align: center;
}

.chart-title {
  font-size: 16px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.chart-hint {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.path-code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  background: var(--el-bg-color-page);
  padding: 2px 6px;
  border-radius: 3px;
}

.development-info {
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
  color: var(--el-text-color-regular);
}
</style>