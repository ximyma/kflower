<template>
  <div class="app-dashboard">
    <div class="dashboard-header">
      <h2>{{ appData.name }} - 首页</h2>
      <div class="header-actions">
        <el-button size="small" @click="refreshAll" :loading="refreshing">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activePage" class="dashboard-tabs" v-if="pages.length > 1">
      <el-tab-pane
        v-for="(page, idx) in pages"
        :key="idx"
        :label="page.name"
        :name="String(idx)"
      />
    </el-tabs>

    <div class="dashboard-grid">
      <div v-if="currentWidgets.length === 0" class="empty-dashboard">
        <el-empty description="暂无仪表盘组件，请在应用设计中配置" />
      </div>

      <div
        v-for="widget in currentWidgets"
        :key="widget.i"
        class="dashboard-widget"
        :style="getWidgetStyle(widget)"
      >
        <!-- KPI 指标卡 -->
        <el-card v-if="widget.type === 'kpi'" shadow="hover" class="widget-card kpi-card">
          <div class="widget-title">{{ widget.title }}</div>
          <div class="kpi-body">
            <div class="kpi-value" v-loading="widgetLoading[widget.i]">
              {{ formatNumber(widgetData[widget.i]?.value) }}
            </div>
            <div class="kpi-label" v-if="widget.data_source?.aggregate">
              {{ aggregateLabel(widget.data_source.aggregate) }}
            </div>
          </div>
        </el-card>

        <!-- 数据列表 -->
        <el-card v-else-if="widget.type === 'table'" shadow="hover" class="widget-card table-card">
          <div class="widget-title">{{ widget.title }}</div>
          <div class="table-body" v-loading="widgetLoading[widget.i]">
            <el-table
              :data="(widgetData[widget.i]?.data || []).slice(0, widget.max_rows || 10)"
              size="small"
              border
              stripe
              style="width: 100%"
              max-height="400"
            >
              <el-table-column
                v-for="col in getTableColumns(widget, widgetData[widget.i])"
                :key="col.key"
                :prop="col.key"
                :label="col.label"
                :min-width="col.width || 100"
                show-overflow-tooltip
              />
            </el-table>
            <div v-if="widgetData[widget.i]?.count > (widget.max_rows || 10)" class="table-more">
              共 {{ widgetData[widget.i].count }} 条，显示前 {{ widget.max_rows || 10 }} 条
            </div>
          </div>
        </el-card>

        <!-- 统计图表（柱状图/饼图） -->
        <el-card v-else-if="widget.type === 'chart'" shadow="hover" class="widget-card chart-card">
          <div class="widget-title">{{ widget.title }}</div>
          <div class="chart-body" v-loading="widgetLoading[widget.i]">
            <div v-if="widgetData[widget.i]?.type === 'grouped'" class="chart-container">
              <div
                v-for="item in (widgetData[widget.i]?.data || [])"
                :key="item.name"
                class="chart-row"
              >
                <span class="chart-label">{{ item.name }}</span>
                <div class="chart-bar-track">
                  <div
                    class="chart-bar-fill"
                    :style="{ width: getBarWidth(item.value, widgetData[widget.i]) + '%' }"
                  />
                </div>
                <span class="chart-value">{{ formatNumber(item.value) }}</span>
              </div>
            </div>
            <div v-else-if="widgetData[widget.i]?.value !== undefined" class="kpi-simple">
              <div class="kpi-value">{{ formatNumber(widgetData[widget.i]?.value) }}</div>
              <div class="kpi-label">{{ widgetData[widget.i]?.label || widget.title }}</div>
            </div>
            <div v-else class="chart-empty">
              <el-empty description="暂无数据" :image-size="60" />
            </div>
          </div>
        </el-card>

        <!-- 快捷入口 -->
        <el-card v-else-if="widget.type === 'quick'" shadow="hover" class="widget-card quick-card">
          <div class="widget-title">{{ widget.title }}</div>
          <div class="quick-body">
            <div
              v-for="(item, idx) in (widget.quick_links || [])"
              :key="idx"
              class="quick-item"
              @click="navigateTo(item)"
            >
              <el-icon :size="24"><component :is="item.icon || 'Link'" /></el-icon>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </el-card>

        <!-- 富文本/说明 -->
        <el-card v-else-if="widget.type === 'text'" shadow="hover" class="widget-card text-card">
          <div class="widget-title">{{ widget.title }}</div>
          <div class="text-body" v-html="widget.content || ''" />
        </el-card>

        <!-- 待办/通知 -->
        <el-card v-else-if="widget.type === 'todo'" shadow="hover" class="widget-card todo-card">
          <div class="widget-title">{{ widget.title }}</div>
          <div class="todo-body" v-loading="widgetLoading[widget.i]">
            <div v-if="widgetData[widget.i]?.data?.length" class="todo-list">
              <div
                v-for="(item, idx) in widgetData[widget.i].data.slice(0, (widget.max_rows || 10))"
                :key="idx"
                class="todo-item"
              >
                <el-tag :type="getTodoStatusType(item)" size="small" class="todo-status">
                  {{ item.status || '待处理' }}
                </el-tag>
                <span class="todo-text">{{ item.title || item.name || JSON.stringify(item) }}</span>
              </div>
            </div>
            <div v-else class="todo-empty">暂无待办事项</div>
          </div>
        </el-card>

        <div v-if="widgetData[widget.i]?.error" class="widget-error">
          <el-alert :title="widgetData[widget.i].error" type="error" show-icon :closable="false" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'
import { templateAPI } from '@/common/api'

const route = useRoute()
const router = useRouter()

const props = defineProps<{
  appId: number
}>()

const resolvedAppId = computed(() => {
  const id = props.appId || Number(route.params.appId) || 0
  return id
})

const appData = ref<any>({ name: '应用' })
const pages = ref<any[]>([{ name: '首页', widgets: [] }])
const activePage = ref('0')
const widgetData = ref<Record<string, any>>({})
const fieldLabels = ref<Record<number, Record<string, string>>>({})
const widgetLoading = ref<Record<string, boolean>>({})
const refreshing = ref(false)
const templateFieldLabels = ref<Record<number, Record<string, string>>>({})

const currentWidgets = computed(() => {
  const idx = parseInt(activePage.value)
  return pages.value[idx]?.widgets || []
})

function getWidgetStyle(widget: any) {
  return { gridColumn: `span ${widget.width || 6}` }
}

function formatNumber(val: any) {
  if (val === undefined || val === null) return '0'
  if (typeof val === 'number') {
    return val.toLocaleString()
  }
  return String(val)
}

function aggregateLabel(agg: string) {
  const labels: Record<string, string> = {
    count: '总记录数',
    sum: '总和',
    avg: '平均值',
    max: '最大值',
    min: '最小值',
  }
  return labels[agg] || agg
}

function getBarWidth(value: number, data: any) {
  const max = Math.max(...(data?.data || []).map((d: any) => d.value || 0))
  if (max === 0) return 0
  return Math.round((value / max) * 100)
}

function getTableColumns(widget: any, data: any) {
  if (!data?.data?.length) return []
  const first = data.data[0]
  // 获取模板的字段标签映射（优先使用 fieldLabels API，其次用 templateFieldLabels 本地缓存）
  const templateId = widget.data_source?.template_id
  const labelMap = templateId 
    ? fieldLabels.value[templateId] || templateFieldLabels.value[templateId] || {}
    : {}
  
  // 系统字段列表
  const SYSTEM_FIELDS = new Set(['id', 'template_id', 'created_by', 'created_at', 'updated_at', 'deleted_at'])
  
  // Priority 1: widget.columns (configured columns)
  if (widget.columns?.length) {
    return widget.columns
      .filter((c: string) => !SYSTEM_FIELDS.has(c))
      .map((col: string) => ({ key: col, label: labelMap[col] || col }))
  }

  // Priority 2: 从 labelMap 中提取有中文映射的字段
  const labelKeys = Object.keys(labelMap).filter(k => !SYSTEM_FIELDS.has(k))
  if (labelKeys.length > 0) {
    return labelKeys.slice(0, 8).map(k => ({
      key: k,
      label: labelMap[k],
      width: k === 'id' ? 60 : undefined,
    }))
  }

  // Priority 3: 从数据字段推断
  const bizKeys = Object.keys(first).filter(k => !SYSTEM_FIELDS.has(k)).slice(0, 8)
  return bizKeys.map(k => ({
    key: k,
    label: labelMap[k] || k,
    width: k === 'id' ? 60 : undefined,
  }))
}

function getTodoStatusType(item: any) {
  const status = (item.status || '').toLowerCase()
  if (status === '待审批' || status === 'pending' || status === '待处理') return 'warning'
  if (status === '已完成' || status === 'completed' || status === '已通过') return 'success'
  if (status === '已拒绝' || status === 'rejected') return 'danger'
  return 'info'
}

function navigateTo(item: any) {
  if (item.route) {
    router.push(item.route)
  } else if (item.template_id) {
    router.push(`/app/${resolvedAppId.value}/form/${item.template_id}`)
  } else if (item.url) {
    window.open(item.url, '_blank')
  }
}

async function loadAppData() {
  try {
    const res: any = await appAPI.get(resolvedAppId.value)
    appData.value = res
  } catch (e: any) {
    console.error('加载应用失败:', e)
  }
}

async function loadTemplateFieldLabels(templateId: number) {
  if (templateFieldLabels.value[templateId]) {
    return
  }
  
  try {
    const res: any = await templateAPI.get(templateId)
    if (res.modules) {
      const fieldLabels: Record<string, string> = {}
      for (const mod of res.modules) {
        if (mod.fields) {
          for (const field of mod.fields) {
            fieldLabels[field.name] = field.label || field.name
          }
        }
      }
      templateFieldLabels.value[templateId] = fieldLabels
    }
  } catch (e) {
    console.error('获取模板字段定义失败:', e)
  }
}

async function loadDashboard() {
  try {
    const res: any = await appAPI.getDashboard(resolvedAppId.value)
    const config = res.data
    if (config && config.pages && config.pages.length > 0) {
      // 创建新的数组，确保响应式系统能检测到变化
      const newPages = JSON.parse(JSON.stringify(config.pages))
      
      // 收集所有需要加载字段定义的模板ID
      const templateIds = new Set<number>()
      
      for (const page of newPages) {
        for (const w of (page.widgets || [])) {
          if (w.data_source) {
            if (w.data_source.template_id) {
              templateIds.add(w.data_source.template_id)
            }
            if (w.data_source.date_field === undefined) w.data_source.date_field = 'created_at'
            if (w.data_source.filters === undefined) w.data_source.filters = []
            if (w.data_source.type === undefined) {
              w.data_source.type = w.type === 'table' ? 'query' : 'aggregation'
            }
            // chart 类型且有 group_by（非空）时，强制设为 grouped_aggregation
            if (w.type === 'chart' && w.group_by && w.group_by.length > 0) {
              w.data_source.type = 'grouped_aggregation'
              if (!w.data_source.group_by) w.data_source.group_by = w.group_by
              if (!w.data_source.aggregate) w.data_source.aggregate = w.aggregate || 'count'
            }
            if (w.data_source.max_rows === undefined) w.data_source.max_rows = 10
            if (w.data_source.order_by === undefined) w.data_source.order_by = '-created_at'
          }
        }
      }
      
      // 批量加载所有模板的字段定义
      await Promise.all([...templateIds].map(id => loadTemplateFieldLabels(id)))
      
      // 赋值新数组
      pages.value = newPages
    } else {
      pages.value = [{ name: '首页', widgets: [] }]
    }
  } catch (e) {
    console.error('加载仪表盘失败:', e)
    pages.value = [{ name: '首页', widgets: [] }]
  }
}

async function loadFieldLabels() {
  // Collect unique template_ids
  const tidSet = new Set<number>()
  for (const page of pages.value) {
    for (const w of (page.widgets || [])) {
      if (w.data_source?.template_id) tidSet.add(w.data_source.template_id)
    }
  }
  if (tidSet.size === 0) return

  try {
    const res = await appAPI.getFieldLabels([...tidSet])
    const labels = (res.data || {}) as Record<number, Record<string, string>>
    fieldLabels.value = labels
  } catch (e: any) {
    console.error('加载字段标签失败:', e)
  }
}

async function refreshWidgetData(widget: any) {
  if (!widget.data_source || !widget.data_source.template_id) {
    return
  }

  widgetLoading.value[widget.i] = true
  try {
    const res: any = await appAPI.getWidgetData(widget)
    widgetData.value[widget.i] = res.data || res
  } catch (e: any) {
    console.error('刷新组件数据失败:', widget.title, e)
    widgetData.value[widget.i] = { error: e.message }
  } finally {
    widgetLoading.value[widget.i] = false
  }
}

async function refreshAll() {
  refreshing.value = true
  for (const widget of currentWidgets.value) {
    await refreshWidgetData(widget)
  }
  refreshing.value = false
}

onMounted(async () => {
  await loadAppData()
  await loadDashboard()
  await loadFieldLabels()
  setTimeout(() => {
    currentWidgets.value.forEach(w => refreshWidgetData(w))
  }, 100)
})

watch(activePage, () => {
  setTimeout(() => {
    currentWidgets.value.forEach(w => refreshWidgetData(w))
  }, 200)
})

watch(pages, () => {
  setTimeout(async () => {
    await loadFieldLabels()
    currentWidgets.value.forEach(w => refreshWidgetData(w))
  }, 300)
})
</script>

<style scoped lang="scss">
.app-dashboard {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 20px;
    color: var(--el-text-color-primary);
  }
}

.dashboard-tabs {
  margin-bottom: 16px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}

.empty-dashboard {
  grid-column: 1 / -1;
  padding: 60px 0;
}

.dashboard-widget {
  min-height: 120px;
}

.widget-card {
  height: 100%;

  .widget-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-regular);
    margin-bottom: 12px;
  }
}

// KPI 卡片
.kpi-card {
  :deep(.el-card__body) {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 100%;
  }
}

.kpi-simple {
  text-align: center;
  padding: 16px;
  .kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--el-color-primary);
    line-height: 1.2;
  }
  .kpi-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }
}

.kpi-body {
  text-align: center;
  padding: 10px 0;
}

.kpi-value {
  font-size: 36px;
  font-weight: bold;
  color: var(--el-color-primary);
  line-height: 1.2;
}

.kpi-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

// 表格卡片
.table-body {
  min-height: 60px;
}

.table-more {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  padding: 8px 0;
}

// 图表卡片
.chart-body {
  min-height: 60px;
}

.chart-container {
  padding: 8px 0;
}

.chart-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.chart-label {
  width: 80px;
  font-size: 13px;
  text-align: right;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chart-bar-track {
  flex: 1;
  height: 20px;
  background: var(--el-fill-color);
  border-radius: 4px;
  overflow: hidden;
}

.chart-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--el-color-primary-light-3), var(--el-color-primary));
  border-radius: 4px;
  transition: width 0.5s ease;
}

.chart-value {
  width: 60px;
  font-size: 13px;
  font-weight: 500;
  text-align: right;
  flex-shrink: 0;
}

.single-value-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  gap: 6px;
}

.single-value-number {
  font-size: 36px;
  font-weight: 700;
  color: var(--el-color-primary);
  line-height: 1;
}

.single-value-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

// 快捷入口
.quick-body {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
  padding: 8px 0;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;

  &:hover {
    background: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
  }

  span {
    font-size: 12px;
    text-align: center;
  }
}

// 文本卡片
.text-body {
  padding: 8px 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

// 待办卡片
.todo-body {
  min-height: 60px;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-light);

  &:last-child {
    border-bottom: none;
  }
}

.todo-status {
  flex-shrink: 0;
}

.todo-text {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-empty {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 20px 0;
}

.widget-error {
  grid-column: 1 / -1;
  margin-top: 8px;
}
</style>
