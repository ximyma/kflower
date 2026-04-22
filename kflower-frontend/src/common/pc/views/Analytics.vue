<template>
  <div class="analytics-page">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ summary.today_instances }}</div>
            <div class="stat-label">今日流程</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <el-icon :size="24"><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ summary.week_instances }}</div>
            <div class="stat-label">本周流程</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <el-icon :size="24"><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ efficiency.avg_processing_time_minutes || 0 }}</div>
            <div class="stat-label">平均处理时间(分)</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <el-icon :size="24"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ summary.active_users || 0 }}</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- AI分析助手 -->
    <el-card class="ai-card">
      <template #header>
        <div class="card-header">
          <span><el-icon><MagicStick /></el-icon> AI 智能分析</span>
          <el-tag type="success" size="small">在线</el-tag>
        </div>
      </template>
      
      <div class="ai-input-section">
        <el-input
          v-model="analysisQuery"
          placeholder="输入自然语言问题，AI 将自动分析数据并生成报告..."
          size="large"
          @keyup.enter="handleAnalyze"
        >
          <template #append>
            <el-button type="primary" @click="handleAnalyze" :loading="analyzing">
              <el-icon><MagicStick /></el-icon> 分析
            </el-button>
          </template>
        </el-input>
      </div>
      
      <!-- 快捷问题 -->
      <div class="quick-queries">
        <el-tag
          v-for="q in quickQueries"
          :key="q.text"
          @click="analysisQuery = q.text; handleAnalyze()"
          class="query-tag"
          :type="q.type"
        >
          {{ q.text }}
        </el-tag>
      </div>
      
      <!-- 分析结果 -->
      <div v-if="analysisResult" class="analysis-result">
        <el-card shadow="never">
          <div class="result-header">
            <span><el-icon><Document /></el-icon> 分析报告</span>
            <el-button size="small" @click="exportReport">
              <el-icon><Download /></el-icon> 导出
            </el-button>
          </div>
          <el-divider />
          <div class="result-content" v-html="analysisResult"></div>
        </el-card>
      </div>
    </el-card>

    <el-divider />

    <!-- 数据分析标签页 -->
    <el-tabs v-model="activeTab" class="analytics-tabs">
      <!-- 趋势分析 -->
      <el-tab-pane label="趋势分析" name="trend">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>📈 流程趋势（近6个月）</span>
              </template>
              <v-chart :option="lineOption" autoresize style="height: 300px;" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>💬 AI 对话趋势</span>
              </template>
              <v-chart :option="aiLineOption" autoresize style="height: 300px;" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 状态分布 -->
      <el-tab-pane label="状态分布" name="status">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>🥧 流程状态分布</span>
              </template>
              <v-chart :option="pieOption" autoresize style="height: 300px;" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>📊 模板分类统计</span>
              </template>
              <v-chart :option="categoryOption" autoresize style="height: 300px;" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 工作流性能 -->
      <el-tab-pane label="工作流性能" name="performance">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>⚡ 工作流性能分析</span>
              <div>
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  size="small"
                  @change="loadWorkflowPerformance"
                />
              </div>
            </div>
          </template>
          <el-table :data="workflowPerformance" stripe>
            <el-table-column prop="workflow_name" label="工作流名称" />
            <el-table-column prop="total" label="总实例" width="80" />
            <el-table-column prop="approved" label="已批准" width="80">
              <template #default="{ row }">
                <el-tag type="success" size="small">{{ row.approved }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="rejected" label="已拒绝" width="80">
              <template #default="{ row }">
                <el-tag type="danger" size="small">{{ row.rejected }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="running" label="进行中" width="80">
              <template #default="{ row }">
                <el-tag type="warning" size="small">{{ row.running }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="approval_rate" label="批准率" width="100">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.approval_rate" 
                  :color="row.approval_rate > 80 ? '#67C23A' : row.approval_rate > 50 ? '#E6A23C' : '#F56C6C'"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 用户活跃度 -->
      <el-tab-pane label="用户活跃度" name="activity">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-card shadow="hover">
              <template #header>
                <span>👥 用户活跃趋势</span>
              </template>
              <v-chart :option="activityOption" autoresize style="height: 300px;" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <span>🏆 活跃用户 TOP 10</span>
              </template>
              <el-table :data="topUsers" size="small">
                <el-table-column type="index" label="#" width="40" />
                <el-table-column prop="full_name" label="用户" />
                <el-table-column prop="activity_count" label="活跃度" width="80">
                  <template #default="{ row }">
                    <el-tag size="small">{{ row.activity_count }}</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 部门绩效 -->
      <el-tab-pane label="部门绩效" name="org">
        <el-card shadow="hover">
          <template #header>
            <span>🏢 部门绩效分析</span>
          </template>
          <el-table :data="orgPerformance" stripe>
            <el-table-column prop="organization" label="部门" />
            <el-table-column prop="total_instances" label="流程数" width="100" />
            <el-table-column prop="approved" label="已批准" width="100">
              <template #default="{ row }">
                <el-tag type="success" size="small">{{ row.approved }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="rejected" label="已拒绝" width="100">
              <template #default="{ row }">
                <el-tag type="danger" size="small">{{ row.rejected }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="active_users" label="活跃人数" width="100" />
            <el-table-column prop="approval_rate" label="批准率" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.approval_rate" 
                  :color="row.approval_rate > 80 ? '#67C23A' : row.approval_rate > 50 ? '#E6A23C' : '#F56C6C'"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 热门模板 -->
      <el-tab-pane label="热门模板" name="templates">
        <el-card shadow="hover">
          <template #header>
            <span>🔥 热门模板使用分析</span>
          </template>
          <v-chart :option="templateOption" autoresize style="height: 350px;" />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  MagicStick, Document, TrendCharts, Clock, User, Download
} from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent
} from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const activeTab = ref('trend')
const analysisQuery = ref('')
const analysisResult = ref('')
const analyzing = ref(false)
const dateRange = ref<[Date, Date] | null>(null)

// 数据
const chartData = ref<any>({
  monthly_workflow: [],
  workflow_status: [],
  ai_trend: [],
  template_category: []
})

const summary = reactive({
  today_instances: 0,
  week_instances: 0,
  active_users: 0
})

const efficiency = reactive({
  avg_processing_time_minutes: 0,
  ontime_completion_rate: 0
})

const workflowPerformance = ref<any[]>([])
const topUsers = ref<any[]>([])
const dailyActivity = ref<any[]>([])
const orgPerformance = ref<any[]>([])
const templateAnalytics = ref<any>({ hot_templates: [], category_stats: [] })

// 快捷查询
const quickQueries = [
  { text: '本月流程效率分析', type: 'primary' },
  { text: '各部门绩效对比', type: 'success' },
  { text: '用户活跃度趋势', type: 'warning' },
  { text: '热门模板排行', type: 'info' }
]

// 图表配置
const lineOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 50, right: 20, top: 30, bottom: 40 },
  xAxis: { type: 'category', data: chartData.value.monthly_workflow.map((d: any) => d.month), axisLabel: { color: '#666' } },
  yAxis: { type: 'value', axisLabel: { color: '#666' } },
  series: [{
    data: chartData.value.monthly_workflow.map((d: any) => d.count),
    type: 'line', smooth: true,
    areaStyle: { opacity: 0.2, color: '#409EFF' },
    lineStyle: { width: 3, color: '#409EFF' },
    itemStyle: { color: '#409EFF' }
  }]
}))

const pieOption = computed(() => {
  const statusLabels: Record<string, string> = { running: '进行中', approved: '已批准', rejected: '已拒绝', draft: '草稿', pending: '待处理' }
  const colors = ['#E6A23C', '#67C23A', '#F56C6C', '#909399', '#409EFF']
  return {
    tooltip: { trigger: 'item', backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
    legend: { bottom: 10, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
      data: chartData.value.workflow_status.map((d: any, i: number) => ({ 
        name: statusLabels[d.status] || d.status, 
        value: d.count, 
        itemStyle: { color: colors[i % colors.length] } 
      })),
      label: { fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  }
})

const aiLineOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 50, right: 20, top: 30, bottom: 40 },
  xAxis: { type: 'category', data: chartData.value.ai_trend.map((d: any) => d.month), axisLabel: { color: '#666' } },
  yAxis: { type: 'value', axisLabel: { color: '#666' } },
  series: [{
    data: chartData.value.ai_trend.map((d: any) => d.count),
    type: 'line', smooth: true,
    lineStyle: { width: 3, color: '#67C23A' },
    itemStyle: { color: '#67C23A' },
    areaStyle: { opacity: 0.2, color: '#67C23A' }
  }]
}))

const categoryOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 60, right: 20, top: 30, bottom: 50 },
  xAxis: { type: 'category', data: chartData.value.template_category.map((d: any) => d.category || '其他'), axisLabel: { color: '#666', rotate: 30 } },
  yAxis: { type: 'value', axisLabel: { color: '#666' } },
  series: [{
    type: 'bar',
    data: chartData.value.template_category.map((d: any) => d.count),
    itemStyle: { color: '#E6A23C', borderRadius: [4, 4, 0, 0] },
    barWidth: '50%'
  }]
}))

const activityOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  legend: { data: ['工作流用户', 'AI用户'], top: 5 },
  grid: { left: 50, right: 20, top: 50, bottom: 40 },
  xAxis: { type: 'category', data: dailyActivity.value.slice(-14).map((d: any) => d.date.slice(5)), axisLabel: { color: '#666' } },
  yAxis: { type: 'value', axisLabel: { color: '#666' } },
  series: [
    { name: '工作流用户', type: 'line', data: dailyActivity.value.slice(-14).map((d: any) => d.workflow_users), smooth: true, itemStyle: { color: '#409EFF' } },
    { name: 'AI用户', type: 'line', data: dailyActivity.value.slice(-14).map((d: any) => d.ai_users), smooth: true, itemStyle: { color: '#67C23A' } }
  ]
}))

const templateOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 150, right: 30, top: 20, bottom: 30 },
  xAxis: { type: 'value', axisLabel: { color: '#666' } },
  yAxis: { type: 'category', data: templateAnalytics.value.hot_templates.slice(0, 10).map((t: any) => t.name), axisLabel: { color: '#666' } },
  series: [{
    type: 'bar',
    data: templateAnalytics.value.hot_templates.slice(0, 10).map((t: any) => t.usage_count),
    itemStyle: { color: '#667eea', borderRadius: [0, 4, 4, 0] },
    barWidth: '60%'
  }]
}))

// 加载数据
async function loadOverview() {
  try {
    const res = await fetch('/api/v1/analytics/overview', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const json = await res.json()
      if (json.data) {
        chartData.value = json.data
        efficiency.avg_processing_time_minutes = json.data.efficiency?.avg_processing_time_minutes || 0
        efficiency.ontime_completion_rate = json.data.efficiency?.ontime_completion_rate || 0
        summary.active_users = json.data.active_users || 0
      }
    }
  } catch (e) {
    console.warn('加载概览数据失败', e)
  }
}

async function loadSummary() {
  try {
    const res = await fetch('/api/v1/analytics/dashboard-summary', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const json = await res.json()
      if (json.data) {
        summary.today_instances = json.data.today_instances || 0
        summary.week_instances = json.data.week_instances || 0
      }
    }
  } catch (e) {
    console.warn('加载摘要数据失败', e)
  }
}

async function loadWorkflowPerformance() {
  try {
    const params = new URLSearchParams()
    if (dateRange.value) {
      params.append('start_date', dateRange.value[0].toISOString().slice(0, 10))
      params.append('end_date', dateRange.value[1].toISOString().slice(0, 10))
    }
    const res = await fetch('/api/v1/analytics/workflow-performance?' + params, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const json = await res.json()
      workflowPerformance.value = json.data || []
    }
  } catch (e) {
    console.warn('加载工作流性能失败', e)
  }
}

async function loadUserActivity() {
  try {
    const res = await fetch('/api/v1/analytics/user-activity?days=30', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const json = await res.json()
      dailyActivity.value = json.data?.daily_activity || []
      topUsers.value = json.data?.top_users || []
    }
  } catch (e) {
    console.warn('加载用户活跃度失败', e)
  }
}

async function loadOrgPerformance() {
  try {
    const res = await fetch('/api/v1/analytics/org-performance', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const json = await res.json()
      orgPerformance.value = json.data || []
    }
  } catch (e) {
    console.warn('加载部门绩效失败', e)
  }
}

async function loadTemplateAnalytics() {
  try {
    const res = await fetch('/api/v1/analytics/template-analytics', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const json = await res.json()
      templateAnalytics.value = json.data || { hot_templates: [], category_stats: [] }
    }
  } catch (e) {
    console.warn('加载模板分析失败', e)
  }
}

async function handleAnalyze() {
  if (!analysisQuery.value.trim()) {
    ElMessage.warning('请输入分析问题')
    return
  }
  analyzing.value = true
  try {
    const res = await fetch('/api/v1/analytics/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + localStorage.getItem('access_token')
      },
      body: JSON.stringify({ question: analysisQuery.value })
    })
    if (res.ok) {
      const json = await res.json()
      analysisResult.value = json.answer || JSON.stringify(json.data, null, 2)
    } else {
      analysisResult.value = '<p style="color:#F56C6C;">AI 分析服务暂不可用，请检查 AI 配置</p>'
    }
  } catch (e) {
    analysisResult.value = '<p style="color:#F56C6C;">分析服务连接失败</p>'
  } finally {
    analyzing.value = false
  }
}

function exportReport() {
  const blob = new Blob([analysisResult.value], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `分析报告_${new Date().toISOString().slice(0, 10)}.html`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

onMounted(async () => {
  await Promise.all([
    loadOverview(),
    loadSummary(),
    loadWorkflowPerformance(),
    loadUserActivity(),
    loadOrgPerformance(),
    loadTemplateAnalytics()
  ])
})
</script>

<style scoped lang="scss">
.analytics-page {
  padding: 0;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
  
  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    margin-right: 16px;
  }
  
  .stat-content {
    .stat-value {
      font-size: 28px;
      font-weight: bold;
      color: #303133;
    }
    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }
  }
}

.ai-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: bold;
    }
  }
  
  .ai-input-section {
    margin-bottom: 16px;
  }
  
  .quick-queries {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    
    .query-tag {
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
    }
  }
  
  .analysis-result {
    margin-top: 20px;
    
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      span {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: bold;
        font-size: 15px;
      }
    }
    
    .result-content {
      line-height: 1.8;
      color: #303133;
    }
  }
}

.analytics-tabs {
  margin-top: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>