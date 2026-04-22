<template>
  <div class="analytics-page">
    <el-card>
      <template #header>
        <span>📊 决策分析</span>
      </template>
      
      <!-- AI分析助手 -->
      <div class="ai-analysis">
        <el-alert
          title="AI 智能分析"
          description="使用自然语言查询数据，AI将自动分析并生成可视化图表"
          type="success"
          :closable="false"
          show-icon
        />
        
        <div class="analysis-input">
          <el-input
            v-model="analysisQuery"
            placeholder="例如：分析本月销售趋势，找出增长最快的地区"
            size="large"
          >
            <template #append>
              <el-button @click="handleAnalyze" :loading="loading">
                <el-icon><MagicStick /></el-icon>
                分析
              </el-button>
            </template>
          </el-input>
        </div>
        
        <div v-if="analysisResult" class="analysis-result">
          <el-card>
            <template #header>
              <span>💡 分析结果</span>
            </template>
            <div v-html="analysisResult"></div>
          </el-card>
        </div>
        
        <!-- 快捷问题 -->
        <div class="quick-queries">
          <p>快捷查询：</p>
          <el-tag
            v-for="q in quickQueries"
            :key="q"
            @click="analysisQuery = q"
            class="query-tag"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 数据概览 4宫格图表 -->
      <div class="charts-grid">
        <!-- 月度流程趋势 -->
        <div class="chart-card">
          <h3>📈 月度流程趋势</h3>
          <v-chart :option="lineOption" autoresize style="height: 220px;" />
        </div>
        
        <!-- 流程状态分布 -->
        <div class="chart-card">
          <h3>🥧 流程状态分布</h3>
          <v-chart :option="pieOption" autoresize style="height: 220px;" />
        </div>
        
        <!-- AI对话趋势 -->
        <div class="chart-card">
          <h3>💬 AI对话趋势</h3>
          <v-chart :option="aiLineOption" autoresize style="height: 220px;" />
        </div>
        
        <!-- 模板分类统计 -->
        <div class="chart-card">
          <h3>📚 模板分类统计</h3>
          <v-chart :option="categoryOption" autoresize style="height: 220px;" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const analysisQuery = ref('')
const analysisResult = ref('')
const loading = ref(false)

// 图表数据
const chartData = ref<any>({
  monthly_workflow: [] as { month: string; count: number }[],
  workflow_status: [] as { status: string; count: number }[],
  knowledge_base: [] as { name: string; doc_count: number }[],
  ai_trend: [] as { month: string; count: number }[],
  template_category: [] as { category: string; count: number }[]
})

// 折线图配置
const lineOption = computed(() => ({
  title: { text: '', left: 'center', textStyle: { fontSize: 13, fontWeight: 'bold' as const } },
  tooltip: { trigger: 'axis' as const, backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 40, right: 20, top: 10, bottom: 30 },
  xAxis: {
    type: 'category' as const,
    data: chartData.value.monthly_workflow.map((d) => d.month),
    axisLabel: { fontSize: 10, color: '#666' }
  },
  yAxis: { type: 'value' as const, axisLabel: { fontSize: 10, color: '#666' } },
  series: [{
    data: chartData.value.monthly_workflow.map((d) => d.count),
    type: 'line' as const,
    smooth: true,
    areaStyle: { opacity: 0.15 },
    lineStyle: { width: 2 },
    itemStyle: { color: '#409EFF' },
    emphasis: { focus: 'series' as const }
  }]
}))

// 饼图配置
const pieOption = computed(() => {
  const statusLabels: Record<string, string> = {
    running: '进行中', approved: '已批准', rejected: '已拒绝', draft: '草稿', pending: '待处理'
  }
  const colors = ['#E6A23C', '#67C23A', '#F56C6C', '#909399', '#409EFF']
  return {
    title: { text: '', left: 'center', textStyle: { fontSize: 13, fontWeight: 'bold' as const } },
    tooltip: { trigger: 'item' as const, backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
    legend: { bottom: 5, textStyle: { fontSize: 11, color: '#666' } },
    series: [{
      type: 'pie' as const,
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      data: chartData.value.workflow_status.map((d, i) => ({
        name: statusLabels[d.status] || d.status,
        value: d.count,
        itemStyle: { color: colors[i % colors.length] }
      })),
      label: { fontSize: 10, color: '#666' },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
      }
    }]
  }
})

// AI对话趋势
const aiLineOption = computed(() => ({
  title: { text: '', left: 'center', textStyle: { fontSize: 13, fontWeight: 'bold' as const } },
  tooltip: { trigger: 'axis' as const, backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 40, right: 20, top: 10, bottom: 30 },
  xAxis: {
    type: 'category' as const,
    data: chartData.value.ai_trend.map((d) => d.month),
    axisLabel: { fontSize: 10, color: '#666' }
  },
  yAxis: { type: 'value' as const, axisLabel: { fontSize: 10, color: '#666' } },
  series: [{
    data: chartData.value.ai_trend.map((d) => d.count),
    type: 'line' as const,
    smooth: true,
    lineStyle: { width: 2, color: '#67C23A' },
    itemStyle: { color: '#67C23A' },
    areaStyle: { opacity: 0.1, color: '#67C23A' },
    emphasis: { focus: 'series' as const }
  }]
}))

// 模板分类柱状图
const categoryOption = computed(() => ({
  title: { text: '', left: 'center', textStyle: { fontSize: 13, fontWeight: 'bold' as const } },
  tooltip: { trigger: 'axis' as const, backgroundColor: 'rgba(50,50,50,0.9)', borderColor: '#333', textStyle: { color: '#fff' } },
  grid: { left: 50, right: 20, top: 10, bottom: 30 },
  xAxis: {
    type: 'category' as const,
    data: chartData.value.template_category.map((d) => d.category || '其他'),
    axisLabel: { fontSize: 10, color: '#666', rotate: 30 }
  },
  yAxis: { type: 'value' as const, axisLabel: { fontSize: 10, color: '#666' } },
  series: [{
    type: 'bar' as const,
    data: chartData.value.template_category.map((d) => d.count),
    itemStyle: { color: '#E6A23C', borderRadius: [4, 4, 0, 0] },
    barWidth: '50%',
    emphasis: { focus: 'series' as const }
  }]
}))

async function loadAnalytics() {
  try {
    const res = await fetch('/api/v1/analytics/overview', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    if (res.ok) {
      const json = await res.json()
      if (json.success !== false) {
        chartData.value = json.data || {}
      }
    }
  } catch {
    console.warn('Analytics API not available yet')
  }
}

async function handleAnalyze() {
  if (!analysisQuery.value.trim()) {
    ElMessage.warning('请输入分析问题')
    return
  }
  loading.value = true
  analysisResult.value = ''
  try {
    const res = await fetch('/api/v1/analytics/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ question: analysisQuery.value })
    })
    if (res.ok) {
      const json = await res.json()
      analysisResult.value = json.answer || JSON.stringify(json.data || json, null, 2)
      ElMessage.success('分析完成')
    } else {
      analysisResult.value = '<p>AI 分析服务暂不可用，请检查 AI 配置</p>'
    }
  } catch {
    analysisResult.value = '<p>分析服务连接失败，请确保后端服务运行正常</p>'
  } finally {
    loading.value = false
  }
}

const quickQueries = [
  '本月销售总额',
  '各地区销售对比',
  '库存周转分析',
  '客户增长趋势'
]

onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.analytics-page {
  padding: 0;
}

.ai-analysis {
  margin-bottom: 24px;
}

.analysis-input {
  margin-top: 16px;
}

.analysis-result {
  margin-top: 16px;
}

.quick-queries {
  margin-top: 16px;
}

.quick-queries p {
  color: #909399;
  margin-bottom: 8px;
  font-size: 13px;
}

.query-tag {
  margin-right: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-card {
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  transition: box-shadow 0.3s;
}

.chart-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.chart-card h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
