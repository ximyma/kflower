<template>
  <div class="dashboard-designer">
    <div class="designer-toolbar">
      <el-button type="primary" @click="addPage">
        <el-icon><Plus /></el-icon> 添加页面
      </el-button>
      <el-button @click="saveDashboard" :loading="saving">保存配置</el-button>
      <el-button @click="previewMode = !previewMode">
        {{ previewMode ? '编辑模式' : '预览模式' }}
      </el-button>
      <el-button @click="refreshAll">刷新数据</el-button>
    </div>

    <el-tabs v-model="activePage" class="dashboard-tabs" @tab-change="onTabChange">
      <el-tab-pane
        v-for="(page, idx) in pages"
        :key="idx"
        :label="page.name"
        :name="String(idx)"
      >
        <template #label>
          <span class="page-tab">
            {{ page.name }}
            <el-icon v-if="pages.length > 1" @click.stop="removePage(idx)"><Close /></el-icon>
          </span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <div class="designer-canvas">
      <!-- 工具栏 -->
      <div class="widget-library" v-if="!previewMode">
        <h4>添加组件</h4>
        <div class="widget-list">
          <div
            v-for="widget in widgetTypes"
            :key="widget.type"
            class="widget-item"
            draggable="true"
            @dragstart="onDragStart($event, widget)"
          >
            <span>{{ widget.name }}</span>
          </div>
        </div>
      </div>

      <!-- 画布 -->
      <div
        class="canvas-area"
        @dragover.prevent
        @drop="onCanvasDrop"
      >
        <div v-if="currentWidgets.length === 0" class="empty-canvas">
          <p>从左侧拖拽组件到此处开始设计</p>
        </div>

        <div v-else class="widget-grid">
          <div
            v-for="widget in currentWidgets"
            :key="widget.i"
            class="widget-card"
            :style="getWidgetStyle(widget)"
          >
            <div class="widget-header">
              <span class="widget-title">{{ widget.title || widget.type }}</span>
              <div class="widget-actions" v-if="!previewMode">
                <el-button link @click="editWidget(widget)"><Edit /></el-button>
                <el-button link @click="removeWidget(widget)"><Delete /></el-button>
              </div>
            </div>
            <div class="widget-body">
              <div class="widget-loading" v-if="widgetLoading[widget.i]">
                <el-icon class="is-loading"><Loading /></el-icon>
              </div>
              <div v-else-if="widgetData[widget.i]" class="widget-content">
                <!-- KPI 卡片 -->
                <div v-if="widget.type === 'kpi'" class="kpi-display">
                  <div class="kpi-value">{{ formatNumber(widgetData[widget.i].value) }}</div>
                </div>
                <!-- 数据表格 -->
                <div v-else-if="widget.type === 'table'" class="table-display">
                  <el-table :data="widgetData[widget.i].data || []" size="small" border>
                    <el-table-column
                      v-for="(val, key) in (widgetData[widget.i].data?.[0] || {})"
                      :key="key"
                      :prop="String(key)"
                      :label="String(key)"
                    />
                  </el-table>
                </div>
                <!-- 图表 -->
                <div v-else class="chart-display">
                  <div v-if="widgetData[widget.i].type === 'grouped'">
                    <div
                      v-for="item in widgetData[widget.i].data || []"
                      :key="item.name"
                      class="chart-item"
                    >
                      <span class="chart-label">{{ item.name }}</span>
                      <span class="chart-value">{{ formatNumber(item.value) }}</span>
                      <div class="chart-bar">
                        <div
                          class="chart-bar-fill"
                          :style="{ width: getBarWidth(item.value, widgetData[widget.i]) + '%' }"
                        />
                      </div>
                    </div>
                  </div>
                  <div v-else class="kpi-simple">
                    {{ formatNumber(widgetData[widget.i].value) }}
                  </div>
                </div>
              </div>
              <div v-else class="widget-empty">暂无数据</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 组件配置对话框 -->
    <el-dialog v-model="widgetDialogVisible" title="配置组件" width="600px">
      <el-form :model="widgetForm" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="widgetForm.title" />
        </el-form-item>
        <el-form-item label="组件类型">
          <el-select v-model="widgetForm.type" style="width: 100%">
            <el-option label="KPI 指标卡" value="kpi" />
            <el-option label="数据列表" value="table" />
            <el-option label="统计图表" value="chart" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择模板" required>
          <el-select v-model="widgetForm.template_id" filterable placeholder="选择数据来源模板" style="width: 100%">
            <el-option
              v-for="tpl in templates"
              :key="tpl.id"
              :label="tpl.name"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="统计方式" v-if="widgetForm.type !== 'table'">
          <el-select v-model="widgetForm.aggregate" style="width: 100%">
            <el-option label="记录数" value="count" />
            <el-option label="求和" value="sum" />
            <el-option label="平均值" value="avg" />
            <el-option label="最大值" value="max" />
            <el-option label="最小值" value="min" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计字段" v-if="widgetForm.aggregate !== 'count'">
          <el-input v-model="widgetForm.field" placeholder="输入字段名" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-select v-model="widgetForm.date_range" clearable style="width: 100%">
            <el-option label="今天" value="today" />
            <el-option label="本周" value="week" />
            <el-option label="本月" value="month" />
            <el-option label="本年" value="year" />
          </el-select>
        </el-form-item>
        <el-form-item label="组件宽度">
          <el-slider v-model="widgetForm.width" :min="1" :max="12" :marks="{1:'1格', 6:'6格', 12:'12格'}" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="widgetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveWidgetConfig">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close, Edit, Delete, Loading } from '@element-plus/icons-vue'
import { appAPI } from '@/common/api/myApps'
import { templateAPI } from '@/common/api'

const props = defineProps<{ appId: number }>()

const pages = ref<any[]>([{ name: '首页', widgets: [] }])
const activePage = ref('0')
const previewMode = ref(false)
const saving = ref(false)
const templates = ref<any[]>([])
const widgetDialogVisible = ref(false)
const editingWidget = ref<any>(null)
const widgetData = ref<Record<string, any>>({})
const widgetLoading = ref<Record<string, boolean>>({})

const widgetTypes = [
  { type: 'kpi', name: '📊 KPI指标卡', defaultConfig: { title: 'KPI', type: 'kpi', aggregate: 'count', width: 3 } },
  { type: 'table', name: '📋 数据列表', defaultConfig: { title: '数据列表', type: 'table', width: 6 } },
  { type: 'chart', name: '📈 统计图表', defaultConfig: { title: '统计', type: 'chart', aggregate: 'count', width: 6 } },
]

const widgetForm = reactive({
  title: '',
  type: 'kpi',
  template_id: null as number | null,
  aggregate: 'count',
  field: '',
  date_range: '',
  width: 6
})

const currentWidgets = computed(() => {
  const idx = parseInt(activePage.value)
  return pages.value[idx]?.widgets || []
})

function getWidgetStyle(widget: any) {
  const width = widget.width || 4
  return {
    gridColumn: `span ${width}`,
    minHeight: '150px'
  }
}

function formatNumber(val: any) {
  if (val === undefined || val === null) return '0'
  if (typeof val === 'number') {
    return val.toLocaleString()
  }
  return String(val)
}

function getBarWidth(value: number, data: any) {
  const max = Math.max(...(data.data || []).map((d: any) => d.value))
  if (max === 0) return 0
  return Math.round((value / max) * 100)
}

function onDragStart(e: DragEvent, widget: any) {
  e.dataTransfer?.setData('widgetType', widget.type)
  e.dataTransfer?.setData('widgetConfig', JSON.stringify(widget.defaultConfig))
}

function onCanvasDrop(e: DragEvent) {
  if (previewMode.value) return
  const widgetType = e.dataTransfer?.getData('widgetType')
  if (!widgetType) return

  const defaultConfig = JSON.parse(e.dataTransfer?.getData('widgetConfig') || '{}')
  const newId = `w_${Date.now()}`

  const newWidget = {
    i: newId,
    ...defaultConfig,
    width: 6
  }

  pages.value[parseInt(activePage.value)].widgets.push(newWidget)
  refreshWidgetData(newWidget)
}

function editWidget(widget: any) {
  editingWidget.value = widget
  Object.assign(widgetForm, {
    title: widget.title || '',
    type: widget.type,
    template_id: widget.template_id,
    aggregate: widget.aggregate || 'count',
    field: widget.field || '',
    date_range: widget.date_range || '',
    width: widget.width || 6
  })
  widgetDialogVisible.value = true
}

function saveWidgetConfig() {
  if (!editingWidget.value) return
  if (!widgetForm.template_id) {
    ElMessage.warning('请选择数据来源模板')
    return
  }

  Object.assign(editingWidget.value, {
    title: widgetForm.title,
    type: widgetForm.type,
    template_id: widgetForm.template_id,
    aggregate: widgetForm.aggregate,
    field: widgetForm.field,
    date_range: widgetForm.date_range,
    width: widgetForm.width,
    data_source: {
      type: widgetForm.type === 'table' ? 'query' : 'aggregation',
      template_id: widgetForm.template_id,
      aggregate: widgetForm.aggregate,
      field: widgetForm.field,
      date_range: widgetForm.date_range
    }
  })

  widgetDialogVisible.value = false
  refreshWidgetData(editingWidget.value)
}

function removeWidget(widget: any) {
  const idx = currentWidgets.value.findIndex(w => w.i === widget.i)
  if (idx !== -1) {
    currentWidgets.value.splice(idx, 1)
    delete widgetData.value[widget.i]
  }
}

function addPage() {
  const newName = `页面 ${pages.value.length + 1}`
  pages.value.push({ name: newName, widgets: [] })
  activePage.value = String(pages.value.length - 1)
}

function removePage(idx: number) {
  if (pages.value.length <= 1) {
    ElMessage.warning('至少保留一个页面')
    return
  }
  pages.value.splice(idx, 1)
  activePage.value = '0'
}

function onTabChange() {
  currentWidgets.value.forEach(w => refreshWidgetData(w))
}

async function refreshWidgetData(widget: any) {
  if (!widget.data_source || !widget.data_source.template_id) return

  widgetLoading.value[widget.i] = true
  try {
    const res: any = await appAPI.getWidgetData(widget)
    widgetData.value[widget.i] = res.data || res
  } catch (e: any) {
    widgetData.value[widget.i] = { error: e.message }
  } finally {
    widgetLoading.value[widget.i] = false
  }
}

async function refreshAll() {
  for (const widget of currentWidgets.value) {
    await refreshWidgetData(widget)
  }
}

async function saveDashboard() {
  saving.value = true
  try {
    await appAPI.saveDashboard(props.appId, { pages: pages.value })
    ElMessage.success('仪表盘配置已保存')
  } catch (e: any) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function loadDashboard() {
  try {
    const res: any = await appAPI.getDashboard(props.appId)
    const config = res.data
    if (config && config.pages && config.pages.length > 0) {
      pages.value = config.pages
    }
  } catch (e) {
    console.error('Load dashboard failed', e)
  }
}

async function loadTemplates() {
  try {
    const res: any = await templateAPI.list({ limit: 100, is_published: true })
    templates.value = res.data || res || []
  } catch (e) {
    console.error('Load templates failed', e)
  }
}

onMounted(async () => {
  await loadTemplates()
  await loadDashboard()
  setTimeout(() => {
    currentWidgets.value.forEach(w => refreshWidgetData(w))
  }, 500)
})
</script>

<style scoped>
.dashboard-designer {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}
.designer-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.page-tab {
  display: flex;
  align-items: center;
  gap: 4px;
}
.designer-canvas {
  flex: 1;
  display: flex;
  gap: 16px;
  overflow: hidden;
}
.widget-library {
  width: 180px;
  flex-shrink: 0;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 12px;
}
.widget-library h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
}
.widget-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.widget-item {
  padding: 10px 12px;
  background: white;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  cursor: move;
  font-size: 13px;
}
.widget-item:hover {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.canvas-area {
  flex: 1;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
}
.empty-canvas {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--el-text-color-secondary);
}
.widget-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}
.widget-card {
  background: white;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-light);
}
.widget-title {
  font-weight: 500;
  font-size: 14px;
}
.widget-body {
  flex: 1;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.kpi-display {
  text-align: center;
}
.kpi-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--el-color-primary);
}
.chart-item {
  margin-bottom: 8px;
}
.chart-label {
  display: inline-block;
  width: 80px;
  font-size: 13px;
}
.chart-value {
  display: inline-block;
  width: 60px;
  text-align: right;
  margin-right: 8px;
  font-size: 13px;
  font-weight: 500;
}
.chart-bar {
  display: inline-block;
  width: 100px;
  height: 8px;
  background: var(--el-fill-color);
  border-radius: 4px;
  vertical-align: middle;
}
.chart-bar-fill {
  height: 100%;
  background: var(--el-color-primary);
  border-radius: 4px;
  transition: width 0.3s;
}
.table-display {
  width: 100%;
  max-height: 200px;
  overflow: auto;
}
</style>
