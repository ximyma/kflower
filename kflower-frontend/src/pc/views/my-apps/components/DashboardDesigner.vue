<template>
  <div class="dashboard-designer">
    <div class="designer-toolbar">
      <el-button type="primary" @click="addPage"><el-icon><Plus /></el-icon> 添加页面</el-button>
      <el-button @click="saveDashboard" :loading="saving"><el-icon><Check /></el-icon> 保存配置</el-button>
      <el-button @click="previewMode = !previewMode">{{ previewMode ? '✏️ 编辑模式' : '👁️ 预览模式' }}</el-button>
      <el-button @click="refreshAll" :disabled="previewMode">刷新数据</el-button>
      <el-button @click="showImportDialog = true" v-if="!previewMode"><el-icon><Upload /></el-icon> 导入</el-button>
      <el-button @click="exportConfig" v-if="!previewMode"><el-icon><Download /></el-icon> 导出</el-button>
    </div>

    <el-tabs v-model="activePage" class="dashboard-tabs" @tab-change="onTabChange">
      <el-tab-pane v-for="(page, idx) in pages" :key="idx" :label="page.name" :name="String(idx)">
        <template #label>
          <span class="page-tab" v-if="!previewMode">
            <el-icon @click.stop="renamePage(idx)"><Edit /></el-icon> {{ page.name }}
            <el-icon v-if="pages.length > 1" @click.stop="removePage(idx)"><Close /></el-icon>
          </span>
          <span v-else>{{ page.name }}</span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <div class="designer-canvas">
      <!-- 左侧：组件库 -->
      <div class="widget-library" v-if="!previewMode">
        <h4>📦 组件库</h4>
        <div class="widget-list">
          <div v-for="wt in widgetTypes" :key="wt.type" class="widget-item" draggable="true"
               @dragstart="onDragStart($event, wt)" @click="addWidgetByClick(wt)">
            <span class="widget-item-icon">{{ wt.icon }}</span>
            <div class="widget-item-info">
              <span class="widget-item-name">{{ wt.name }}</span>
              <span class="widget-item-desc">{{ wt.desc }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：画布 -->
      <div class="canvas-area" @dragover.prevent @drop="onCanvasDrop">
        <div v-if="currentWidgets.length === 0" class="empty-canvas">
          <el-empty description="从左侧拖拽组件到此处开始设计" :image-size="80" />
        </div>
        <div v-else class="widget-grid">
          <div v-for="widget in currentWidgets" :key="widget.i" class="widget-card"
               :class="{ 'widget-selected': selectedWidget?.i === widget.i }"
               :style="getWidgetStyle(widget)" @click="selectWidget(widget)">
            <div class="widget-header">
              <div class="widget-header-left">
                <span class="widget-type-badge">{{ getWidgetTypeInfo(widget.type)?.icon }}</span>
                <span class="widget-title">{{ widget.title || widget.type }}</span>
              </div>
              <div class="widget-actions" v-if="!previewMode">
                <el-tooltip content="复制">
                  <el-button link size="small" @click.stop="duplicateWidget(widget)"><el-icon><CopyDocument /></el-icon></el-button>
                </el-tooltip>
                <el-tooltip content="删除">
                  <el-button link size="small" type="danger" @click.stop="removeWidget(widget)"><el-icon><Delete /></el-icon></el-button>
                </el-tooltip>
              </div>
            </div>
            <div class="widget-body">
              <div class="widget-loading" v-if="widgetLoading[widget.i]"><el-icon class="is-loading" :size="24"><Loading /></el-icon></div>
              <div v-else-if="widgetData[widget.i] && !widgetData[widget.i].error" class="widget-content">
                <div v-if="widget.type === 'kpi'" class="kpi-display">
                  <div class="kpi-value">{{ formatNumber(widgetData[widget.i].value) }}</div>
                  <div class="kpi-label" v-if="widget.data_source?.aggregate">{{ aggregateLabel(widget.data_source.aggregate) }}</div>
                </div>
                <div v-else-if="widget.type === 'table'" class="table-display">
                  <el-table :data="(widgetData[widget.i].data || []).slice(0,5)" size="small" border>
                    <el-table-column v-for="(val,key) in (widgetData[widget.i].data?.[0]||{})" :key="key" :prop="String(key)" :label="String(key)" :min-width="80" />
                  </el-table>
                </div>
                <div v-else-if="widget.type === 'chart'" class="chart-display">
                  <div v-if="widgetData[widget.i].type==='grouped'">
                    <div v-for="item in (widgetData[widget.i].data||[]).slice(0,5)" :key="item.name" class="chart-item">
                      <span class="chart-label">{{ item.name }}</span>
                      <div class="chart-bar-track"><div class="chart-bar-fill" :style="{width:getBarWidth(item.value,widgetData[widget.i])+'%'}" /></div>
                      <span class="chart-value">{{ formatNumber(item.value) }}</span>
                    </div>
                  </div>
                  <div v-else class="kpi-simple">{{ formatNumber(widgetData[widget.i].value) }}</div>
                </div>
                <div v-else-if="widget.type==='quick'" class="quick-display">
                  <div class="quick-items"><div v-for="(item,idx) in (widget.quick_links||[]).slice(0,4)" :key="idx" class="quick-item"><el-icon><Link /></el-icon><span>{{ item.label }}</span></div></div>
                </div>
                <div v-else-if="widget.type==='text'" class="text-display"><p>{{ (widget.content||'').substring(0,50) }}{{ (widget.content||'').length>50?'...':'' }}</p></div>
                <div v-else-if="widget.type==='todo'" class="todo-display"><div class="todo-count">{{ widgetData[widget.i]?.data?.length||0 }} 项</div></div>
              </div>
              <div v-else-if="widgetData[widget.i]?.error" class="widget-error-text"><el-icon><WarningFilled /></el-icon> {{ widgetData[widget.i].error }}</div>
              <div v-else class="widget-empty">暂无数据</div>
            </div>
            <div class="widget-footer" v-if="!previewMode">
              <el-button link size="small" @click.stop="editWidget(widget)"><el-icon><Setting /></el-icon> 配置</el-button>
              <el-button link size="small" @click.stop="moveWidget(widget,-1)" :disabled="isFirstWidget(widget)"><el-icon><ArrowLeft /></el-icon></el-button>
              <el-button link size="small" @click.stop="moveWidget(widget,1)" :disabled="isLastWidget(widget)"><el-icon><ArrowRight /></el-icon></el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：属性面板 -->
      <div class="property-panel" v-if="!previewMode && selectedWidget">
        <h4>⚙️ 组件属性</h4>
        <el-form :model="propForm" label-position="top" size="small" class="prop-form">
          <el-divider content-position="left">基本设置</el-divider>
          <el-form-item label="标题"><el-input v-model="propForm.title" @change="applyPropChange" /></el-form-item>
          <el-form-item label="组件类型">
            <el-select v-model="propForm.type" style="width:100%" @change="onTypeChange">
              <el-option v-for="wt in widgetTypes" :key="wt.type" :label="wt.name" :value="wt.type" />
            </el-select>
          </el-form-item>
          <el-form-item label="宽度（1-12格）">
            <el-slider v-model="propForm.width" :min="1" :max="12" :marks="{1:'1',3:'3',6:'6',9:'9',12:'12'}" show-stops @change="applyPropChange" />
          </el-form-item>

          <el-divider content-position="left">数据源</el-divider>
          <el-form-item label="数据来源模板">
            <el-select v-model="propForm.template_id" filterable clearable style="width:100%" @change="applyPropChange">
              <el-option v-for="tpl in templates" :key="tpl.id" :label="tpl.name" :value="tpl.id" />
            </el-select>
          </el-form-item>

          <template v-if="propForm.type!=='table'&&propForm.type!=='quick'&&propForm.type!=='text'&&propForm.template_id">
            <el-form-item label="统计方式">
              <el-select v-model="propForm.aggregate" style="width:100%" @change="applyPropChange">
                <el-option label="记录数 (COUNT)" value="count" /><el-option label="求和 (SUM)" value="sum" />
                <el-option label="平均值 (AVG)" value="avg" /><el-option label="最大值 (MAX)" value="max" /><el-option label="最小值 (MIN)" value="min" />
              </el-select>
            </el-form-item>
            <el-form-item label="统计字段" v-if="propForm.aggregate!=='count'"><el-input v-model="propForm.field" placeholder="输入字段名" @change="applyPropChange" /></el-form-item>
            <el-form-item label="分组字段" v-if="propForm.type==='chart'"><el-input v-model="propForm.group_by" placeholder="按此字段分组" @change="applyPropChange" /></el-form-item>
          </template>

          <template v-if="propForm.type==='table'&&propForm.template_id">
            <el-form-item label="最大显示行数"><el-input-number v-model="propForm.max_rows" :min="5" :max="100" :step="5" @change="applyPropChange" /></el-form-item>
            <el-form-item label="排序字段">
              <el-input v-model="propForm.order_by" placeholder="如: -created_at" @change="applyPropChange">
                <template #append><el-tooltip content="加前缀 - 表示降序" placement="top"><el-icon><QuestionFilled /></el-icon></el-tooltip></template>
              </el-input>
            </el-form-item>
          </template>

          <el-divider content-position="left">筛选条件</el-divider>
          <el-form-item label="日期范围">
            <el-select v-model="propForm.date_range" clearable style="width:100%" @change="applyPropChange">
              <el-option label="不限" value="" /><el-option label="今天" value="today" /><el-option label="本周" value="week" />
              <el-option label="本月" value="month" /><el-option label="本年" value="year" />
            </el-select>
          </el-form-item>
          <el-form-item label="自定义筛选">
            <div class="filters-container">
              <div v-for="(f,idx) in propForm.filters" :key="idx" class="filter-row">
                <el-input v-model="f.field" placeholder="字段名" style="width:100px" @change="applyPropChange" />
                <el-select v-model="f.op" style="width:70px" @change="applyPropChange">
                  <el-option label="=" value="=" /><el-option label=">" value=">" /><el-option label="<" value="<" />
                  <el-option label=">=" value=">=" /><el-option label="<=" value="<=" /><el-option label="LIKE" value="like" />
                </el-select>
                <el-input v-model="f.value" placeholder="值" style="width:100px" @change="applyPropChange" />
                <el-button link type="danger" @click="removeFilter(idx)"><el-icon><Delete /></el-icon></el-button>
              </div>
              <el-button size="small" @click="addFilter"><el-icon><Plus /></el-icon> 添加筛选</el-button>
            </div>
          </el-form-item>

          <template v-if="propForm.type==='quick'">
            <el-divider content-position="left">快捷入口</el-divider>
            <div class="quick-links-editor">
              <div v-for="(link,idx) in propForm.quick_links" :key="idx" class="quick-link-row">
                <el-input v-model="link.label" placeholder="名称" style="width:100px" @change="applyPropChange" />
                <el-input v-model="link.icon" placeholder="图标" style="width:80px" @change="applyPropChange" />
                <el-input v-model="link.route" placeholder="路由" style="width:120px" @change="applyPropChange" />
                <el-button link type="danger" @click="removeQuickLink(idx)"><el-icon><Delete /></el-icon></el-button>
              </div>
              <el-button size="small" @click="addQuickLink"><el-icon><Plus /></el-icon> 添加入口</el-button>
            </div>
          </template>

          <template v-if="propForm.type==='text'">
            <el-divider content-position="left">内容</el-divider>
            <el-form-item label="文本内容"><el-input v-model="propForm.content" type="textarea" :rows="6" placeholder="支持 HTML 格式" @change="applyPropChange" /></el-form-item>
          </template>
        </el-form>
      </div>
    </div>

    <!-- 快速配置对话框 -->
    <el-dialog v-model="widgetDialogVisible" title="快速配置组件" width="500px">
      <el-form :model="widgetForm" label-width="100px">
        <el-form-item label="标题"><el-input v-model="widgetForm.title" /></el-form-item>
        <el-form-item label="组件类型">
          <el-select v-model="widgetForm.type" style="width:100%">
            <el-option v-for="wt in widgetTypes" :key="wt.type" :label="wt.name" :value="wt.type" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择模板" required>
          <el-select v-model="widgetForm.template_id" filterable placeholder="选择数据来源模板" style="width:100%">
            <el-option v-for="tpl in templates" :key="tpl.id" :label="tpl.name" :value="tpl.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计方式" v-if="widgetForm.type!=='table'&&widgetForm.type!=='quick'&&widgetForm.type!=='text'">
          <el-select v-model="widgetForm.aggregate" style="width:100%">
            <el-option label="记录数" value="count" /><el-option label="求和" value="sum" />
            <el-option label="平均值" value="avg" /><el-option label="最大值" value="max" /><el-option label="最小值" value="min" />
          </el-select>
        </el-form-item>
        <el-form-item label="统计字段" v-if="widgetForm.aggregate!=='count'&&widgetForm.type!=='table'&&widgetForm.type!=='quick'&&widgetForm.type!=='text'">
          <el-input v-model="widgetForm.field" placeholder="输入字段名" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-select v-model="widgetForm.date_range" clearable style="width:100%">
            <el-option label="不限" value="" /><el-option label="今天" value="today" /><el-option label="本周" value="week" />
            <el-option label="本月" value="month" /><el-option label="本年" value="year" />
          </el-select>
        </el-form-item>
        <el-form-item label="组件宽度">
          <el-slider v-model="widgetForm.width" :min="1" :max="12" :marks="{1:'1格',6:'6格',12:'12格'}" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="widgetDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="saveWidgetConfig">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="renameDialogVisible" title="重命名页面" width="350px">
      <el-input v-model="renameValue" placeholder="页面名称" @keyup.enter="confirmRename" />
      <template #footer>
        <el-button @click="renameDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showImportDialog" title="导入仪表盘配置" width="500px">
      <el-alert title="粘贴 JSON 配置" type="info" description="将之前导出的仪表盘配置 JSON 粘贴到下方文本框中" show-icon :closable="false" style="margin-bottom:12px" />
      <el-input v-model="importJson" type="textarea" :rows="10" placeholder='{"pages": [{"name": "首页", "widgets": [...]}]}' />
      <template #footer>
        <el-button @click="showImportDialog=false">取消</el-button>
        <el-button type="primary" @click="importConfig">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Close, Edit, Delete, Loading, Check, CopyDocument, Setting, ArrowLeft, ArrowRight, WarningFilled, QuestionFilled, Upload, Download, Link } from '@element-plus/icons-vue'
import { appAPI } from '@/common/api/myApps'
import { templateAPI } from '@/common/api'

const props = defineProps<{ appId: number }>()
const route = useRoute()

// 确保 appId 有效：优先使用 props，fallback 到路由参数
const resolvedAppId = computed(() => props.appId || Number(route.params.appId) || 0)

const widgetTypes = [
  { type: 'kpi', icon: '📊', name: 'KPI指标卡', desc: '显示单个聚合数值', defaultConfig: { title: 'KPI', type: 'kpi', aggregate: 'count', width: 3 } },
  { type: 'table', icon: '📋', name: '数据列表', desc: '展示数据表格', defaultConfig: { title: '数据列表', type: 'table', width: 6, max_rows: 10, order_by: '-created_at' } },
  { type: 'chart', icon: '📈', name: '统计图表', desc: '分组统计柱状图', defaultConfig: { title: '统计', type: 'chart', aggregate: 'count', width: 6, group_by: '' } },
  { type: 'quick', icon: '🔗', name: '快捷入口', desc: '快速导航链接', defaultConfig: { title: '快捷入口', type: 'quick', width: 4, quick_links: [] } },
  { type: 'text', icon: '📝', name: '文本说明', desc: '富文本/说明内容', defaultConfig: { title: '说明', type: 'text', width: 6, content: '请输入内容...' } },
  { type: 'todo', icon: '📌', name: '待办事项', desc: '待审批/待处理列表', defaultConfig: { title: '待办事项', type: 'todo', width: 6, max_rows: 10 } },
]

const pages = ref<any[]>([{ name: '首页', widgets: [] }])
const activePage = ref('0')
const previewMode = ref(false)
const saving = ref(false)
const templates = ref<any[]>([])
const widgetDialogVisible = ref(false)
const editingWidget = ref<any>(null)
const selectedWidget = ref<any>(null)
const widgetData = ref<Record<string, any>>({})
const widgetLoading = ref<Record<string, boolean>>({})
const renameDialogVisible = ref(false)
const renameTargetIdx = ref(-1)
const renameValue = ref('')
const showImportDialog = ref(false)
const importJson = ref('')

const propForm = reactive({
  title: '', type: 'kpi', template_id: null as number | null,
  aggregate: 'count', field: '', group_by: '', date_range: '', width: 6,
  max_rows: 10, order_by: '-created_at', filters: [] as any[],
  quick_links: [] as any[], content: '',
})

const widgetForm = reactive({
  title: '', type: 'kpi', template_id: null as number | null,
  aggregate: 'count', field: '', date_range: '', width: 6,
})

const currentWidgets = computed(() => {
  const idx = parseInt(activePage.value)
  return pages.value[idx]?.widgets || []
})

function getWidgetTypeInfo(type: string) { return widgetTypes.find(w => w.type === type) }
function getWidgetStyle(w: any) { return { gridColumn: `span ${w.width || 4}`, minHeight: '150px' } }
function formatNumber(val: any) {
  if (val === undefined || val === null) return '0'
  return typeof val === 'number' ? val.toLocaleString() : String(val)
}
function aggregateLabel(agg: string) {
  const m: Record<string, string> = { count: '总记录数', sum: '总和', avg: '平均值', max: '最大值', min: '最小值' }
  return m[agg] || agg
}
function getBarWidth(value: number, data: any) {
  const max = Math.max(...(data?.data || []).map((d: any) => d.value || 0))
  return max === 0 ? 0 : Math.round((value / max) * 100)
}
function isFirstWidget(w: any) { const list = currentWidgets.value; return !list.length || list[0].i === w.i }
function isLastWidget(w: any) { const list = currentWidgets.value; return !list.length || list[list.length - 1].i === w.i }

function onDragStart(e: DragEvent, wt: any) {
  e.dataTransfer?.setData('widgetType', wt.type)
  e.dataTransfer?.setData('widgetConfig', JSON.stringify(wt.defaultConfig))
}
function onCanvasDrop(e: DragEvent) {
  if (previewMode.value) return
  const wt = e.dataTransfer?.getData('widgetType')
  if (!wt) return
  addWidgetToPage(JSON.parse(e.dataTransfer?.getData('widgetConfig') || '{}'))
}
function addWidgetByClick(wt: any) {
  if (previewMode.value) return
  addWidgetToPage({ ...wt.defaultConfig })
}
function addWidgetToPage(config: any) {
  const newId = `w_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`
  const nw: any = { i: newId, ...config, width: config.width || 6 }
  if (config.template_id) {
    nw.data_source = {
      type: config.type === 'table' ? 'query' : (config.type === 'chart' && config.group_by ? 'grouped_aggregation' : 'aggregation'),
      template_id: config.template_id,
      aggregate: config.aggregate,
      field: config.field,
      date_range: config.date_range,
      group_by: config.group_by,
      order_by: config.order_by,
      max_rows: config.max_rows,
      date_field: 'created_at',
      filters: [],
    }
  }
  pages.value[parseInt(activePage.value)].widgets.push(nw)
  selectWidget(nw)
  refreshWidgetData(nw)
}
function duplicateWidget(w: any) {
  const cloned = JSON.parse(JSON.stringify(w))
  cloned.i = `w_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`
  cloned.title = w.title + ' (副本)'
  pages.value[parseInt(activePage.value)].widgets.push(cloned)
  selectWidget(cloned)
  refreshWidgetData(cloned)
}
function removeWidget(w: any) {
  const idx = currentWidgets.value.findIndex(x => x.i === w.i)
  if (idx !== -1) {
    currentWidgets.value.splice(idx, 1)
    delete widgetData.value[w.i]
    if (selectedWidget.value?.i === w.i) selectedWidget.value = null
  }
}
function moveWidget(w: any, dir: number) {
  const list = currentWidgets.value
  const idx = list.findIndex(x => x.i === w.i)
  if (idx === -1) return
  const t = idx + dir
  if (t < 0 || t >= list.length) return
  const tmp = list[idx]; list[idx] = list[t]; list[t] = tmp
}
function selectWidget(w: any) { selectedWidget.value = w; syncPropForm(w) }
function syncPropForm(w: any) {
  propForm.title = w.title || ''
  propForm.type = w.type
  propForm.template_id = w.template_id || w.data_source?.template_id || null
  propForm.aggregate = w.aggregate || w.data_source?.aggregate || 'count'
  propForm.field = w.field || w.data_source?.field || ''
  propForm.group_by = w.group_by || w.data_source?.group_by || ''
  propForm.date_range = w.date_range || w.data_source?.date_range || ''
  propForm.width = w.width || 6
  propForm.max_rows = w.max_rows || w.data_source?.max_rows || 10
  propForm.order_by = w.order_by || w.data_source?.order_by || '-created_at'
  propForm.filters = w.filters || w.data_source?.filters || []
  propForm.quick_links = w.quick_links || []
  propForm.content = w.content || ''
}
function applyPropChange() {
  if (!selectedWidget.value) return
  const w = selectedWidget.value
  // 同步顶层属性（保持 widget 对象扁平兼容性）
  Object.assign(w, {
    title: propForm.title, type: propForm.type, template_id: propForm.template_id,
    aggregate: propForm.aggregate, field: propForm.field, group_by: propForm.group_by,
    date_range: propForm.date_range, width: propForm.width, max_rows: propForm.max_rows,
    order_by: propForm.order_by, filters: [...propForm.filters],
    quick_links: [...propForm.quick_links], content: propForm.content,
  })
  // 同步 data_source（后端实际读取的配置对象）
  if (propForm.template_id) {
    const dsType = propForm.type === 'table' ? 'query'
      : (propForm.type === 'chart' && propForm.group_by ? 'grouped_aggregation' : 'aggregation')
    w.data_source = {
      type: dsType,
      template_id: propForm.template_id,
      aggregate: propForm.aggregate,
      field: propForm.field,
      date_range: propForm.date_range,
      group_by: propForm.group_by,
      order_by: propForm.order_by,
      max_rows: propForm.max_rows,
      filters: [...propForm.filters],
      date_field: 'created_at',
    }
  } else {
    w.data_source = undefined
  }
  refreshWidgetData(w)
}
function onTypeChange(newType: string) {
  if (newType === 'quick') {
    propForm.template_id = null
    if (!propForm.quick_links?.length) propForm.quick_links = [{ label: '示例入口', icon: 'Link', route: '' }]
  } else if (newType === 'text') {
    propForm.template_id = null
    propForm.content = propForm.content || '请输入内容...'
  }
  applyPropChange()
}
function editWidget(w: any) {
  editingWidget.value = w
  Object.assign(widgetForm, {
    title: w.title || '', type: w.type,
    template_id: w.template_id || w.data_source?.template_id || null,
    aggregate: w.aggregate || w.data_source?.aggregate || 'count',
    field: w.field || w.data_source?.field || '',
    date_range: w.date_range || w.data_source?.date_range || '', width: w.width || 6,
  })
  widgetDialogVisible.value = true
}
function saveWidgetConfig() {
  if (!editingWidget.value) return
  const w = editingWidget.value
  const dsType = widgetForm.type === 'table' ? 'query'
    : (widgetForm.type === 'chart' && widgetForm.group_by ? 'grouped_aggregation' : 'aggregation')
  const ds = widgetForm.template_id ? {
    type: dsType,
    template_id: widgetForm.template_id,
    aggregate: widgetForm.aggregate,
    field: widgetForm.field,
    date_range: widgetForm.date_range,
    group_by: widgetForm.group_by,
    order_by: widgetForm.order_by,
    max_rows: widgetForm.max_rows,
    filters: [],
    date_field: 'created_at',
  } : undefined
  Object.assign(w, {
    title: widgetForm.title, type: widgetForm.type, template_id: widgetForm.template_id,
    aggregate: widgetForm.aggregate, field: widgetForm.field,
    group_by: widgetForm.group_by,
    date_range: widgetForm.date_range, width: widgetForm.width,
    max_rows: widgetForm.max_rows, order_by: widgetForm.order_by,
    data_source: ds,
  })
  widgetDialogVisible.value = false
  syncPropForm(w)
  refreshWidgetData(w)
}

function addPage() { pages.value.push({ name: `页面 ${pages.value.length + 1}`, widgets: [] }); activePage.value = String(pages.value.length - 1) }
function removePage(idx: number) { if (pages.value.length <= 1) { ElMessage.warning('至少保留一个页面'); return } pages.value.splice(idx, 1); activePage.value = '0' }
function renamePage(idx: number) { renameTargetIdx.value = idx; renameValue.value = pages.value[idx]?.name || ''; renameDialogVisible.value = true }
function confirmRename() { if (renameValue.value.trim()) pages.value[renameTargetIdx.value].name = renameValue.value.trim(); renameDialogVisible.value = false }
function onTabChange() { selectedWidget.value = null; currentWidgets.value.forEach(w => refreshWidgetData(w)) }
function addFilter() { propForm.filters.push({ field: '', op: '=', value: '' }) }
function removeFilter(idx: number) { propForm.filters.splice(idx, 1); applyPropChange() }
function addQuickLink() { propForm.quick_links.push({ label: '', icon: 'Link', route: '' }) }
function removeQuickLink(idx: number) { propForm.quick_links.splice(idx, 1); applyPropChange() }

function exportConfig() {
  const blob = new Blob([JSON.stringify({ pages: pages.value }, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `dashboard_${resolvedAppId.value}.json`; a.click()
  URL.revokeObjectURL(url)
}
function importConfig() {
  try {
    const config = JSON.parse(importJson.value)
    if (!config.pages || !Array.isArray(config.pages)) { ElMessage.warning('配置格式不正确'); return }
    pages.value = config.pages; activePage.value = '0'; selectedWidget.value = null
    showImportDialog.value = false; importJson.value = ''
    ElMessage.success('导入成功')
  } catch (e: any) { ElMessage.error('JSON 解析失败：' + e.message) }
}

async function refreshWidgetData(widget: any) {
  if (!widget.data_source || !widget.data_source.template_id) return
  widgetLoading.value[widget.i] = true
  try {
    const res: any = await appAPI.getWidgetData(widget)
    widgetData.value[widget.i] = res.data || res
  } catch (e: any) { widgetData.value[widget.i] = { error: e.message } }
  finally { widgetLoading.value[widget.i] = false }
}
async function refreshAll() { for (const w of currentWidgets.value) await refreshWidgetData(w) }

async function saveDashboard() {
  saving.value = true
  try { await appAPI.saveDashboard(resolvedAppId.value, { pages: pages.value }); ElMessage.success('仪表盘配置已保存') }
  catch (e: any) { ElMessage.error('保存失败：' + (e.message || '')) }
  finally { saving.value = false }
}
async function loadDashboard() {
  try {
    const res: any = await appAPI.getDashboard(resolvedAppId.value)
    const config = res.data
    if (config && config.pages && config.pages.length > 0) {
      pages.value = config.pages
      // 补充 data_source 默认字段（兼容旧配置）
      for (const page of pages.value) {
        for (const w of (page.widgets || [])) {
          if (w.data_source) {
            if (w.data_source.date_field === undefined) w.data_source.date_field = 'created_at'
            if (w.data_source.filters === undefined) w.data_source.filters = []
            if (w.data_source.type === undefined) {
              w.data_source.type = w.type === 'table' ? 'query' : 'aggregation'
            }
          }
        }
      }
    }
  } catch (e) { console.error('Load dashboard failed', e) }
}
async function loadTemplates() {
  try { const res: any = await templateAPI.list({ limit: 100, is_published: true }); templates.value = res.data || res || [] }
  catch (e) { console.error('Load templates failed', e) }
}

onMounted(async () => {
  await loadTemplates()
  await loadDashboard()
  setTimeout(() => currentWidgets.value.forEach(w => refreshWidgetData(w)), 500)
})
</script>

<style scoped>
.dashboard-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.designer-toolbar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.dashboard-tabs {
  flex-shrink: 0;
  background: #fff;
  padding: 0 16px;
}

.page-tab {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}
.page-tab .el-icon {
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.page-tab .el-icon:hover {
  opacity: 1;
  color: #409eff;
}

.designer-canvas {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.widget-library {
  width: 200px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  padding: 12px;
  overflow-y: auto;
}
.widget-library h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #303133;
}

.widget-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.widget-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
  background: #fafafa;
}
.widget-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.widget-item:active {
  cursor: grabbing;
}
.widget-item-icon {
  font-size: 24px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #f0f2f5;
  flex-shrink: 0;
}
.widget-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.widget-item-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}
.widget-item-desc {
  font-size: 11px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.canvas-area {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: #f5f7fa;
}

.empty-canvas {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.widget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.widget-card {
  background: #fff;
  border-radius: 8px;
  border: 2px solid transparent;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  min-height: 180px;
  position: relative;
}
.widget-card:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.widget-card.widget-selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64,158,255,0.2);
}

.widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.widget-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}
.widget-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
.widget-card:hover .widget-actions {
  opacity: 1;
}
.widget-actions .el-button {
  padding: 4px;
  font-size: 12px;
}

.widget-body {
  flex: 1;
  padding: 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100px;
}

.widget-footer {
  flex-shrink: 0;
  padding: 6px 12px;
  border-top: 1px solid #f0f0f0;
  font-size: 11px;
  color: #909399;
  text-align: right;
}

.property-panel {
  width: 320px;
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  padding: 12px;
  overflow-y: auto;
}
.property-panel h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.prop-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.prop-form .el-form-item {
  margin-bottom: 0;
}
.prop-form .el-form-item__label {
  font-size: 12px;
  color: #606266;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.filter-row .el-input {
  flex: 1;
}

.quick-link-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.kpi-display {
  text-align: center;
  padding: 16px;
}
.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
  line-height: 1.2;
}
.kpi-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.kpi-sub {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 2px;
}

.chart-display {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-display {
  width: 100%;
  overflow-x: auto;
}
.table-display .el-table {
  font-size: 12px;
}

.quick-display {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px;
  justify-content: center;
}
.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}
.quick-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.quick-item-icon {
  font-size: 24px;
}
.quick-item-label {
  font-size: 12px;
  color: #606266;
}

.text-display {
  padding: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  width: 100%;
}

.todo-display {
  width: 100%;
}
.todo-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}
.todo-item:last-child {
  border-bottom: none;
}
.todo-item .todo-text {
  flex: 1;
  color: #303133;
}
.todo-item .todo-text.done {
  text-decoration: line-through;
  color: #c0c4cc;
}
.todo-item .todo-tag {
  flex-shrink: 0;
}

.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 100px;
}

.error-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: #f56c6c;
  font-size: 12px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .widget-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
  .property-panel {
    width: 280px;
  }
}
@media (max-width: 900px) {
  .widget-library {
    width: 160px;
  }
  .property-panel {
    width: 240px;
  }
}
</style>