<template>
  <div class="subform-table">
    <!-- 工具栏 -->
    <div class="subform-toolbar">
      <el-button type="primary" size="small" @click="addRow" v-if="!readonly">
        <el-icon><Plus /></el-icon> 添加行
      </el-button>
      <span v-if="summaryRow" class="summary-hint" style="margin-left: 16px; color: var(--el-text-color-secondary); font-size: 12px">
        自动汇总已开启
      </span>
    </div>

    <!-- 表格 -->
    <el-table
      :data="localRows"
      border
      size="small"
      class="subform-table-grid"
      show-summary
      :summary-method="summaryRow ? getSummary : undefined"
    >
      <el-table-column type="index" label="#" width="50" />
      <el-table-column
        v-for="col in columns"
        :key="col.name"
        :prop="col.name"
        :label="col.label"
        :min-width="120"
      >
        <template #header>
          <span>{{ col.label }}</span>
          <span v-if="col.formula" class="formula-badge" title="计算字段">∑</span>
        </template>
        <template #default="{ row, $index }">
          <!-- 公式字段：只读显示计算结果 -->
          <template v-if="col.formula">
            <span class="formula-cell" :class="{ 'formula-computing': computingRows.has($index) }">
              {{ formatValue(row[col.name], col) }}
            </span>
          </template>
          <!-- 普通可编辑字段 -->
          <template v-else>
            <!-- 文本类型 -->
            <el-input
              v-if="col.type === 'text' || col.type === 'textarea'"
              v-model="row[col.name]"
              size="small"
              :type="col.type === 'textarea' ? 'textarea' : 'text'"
              :rows="col.type === 'textarea' ? 2 : undefined"
              :disabled="readonly"
              @input="onCellChange($index)"
            />
            <!-- 数字/金额类型 -->
            <el-input-number
              v-else-if="col.type === 'number' || col.type === 'money'"
              v-model="row[col.name]"
              size="small"
              :precision="col.type === 'money' ? 2 : 0"
              :controls="false"
              :disabled="readonly"
              style="width: 100%"
              @change="onCellChange($index)"
            />
            <!-- 日期类型 -->
            <el-date-picker
              v-else-if="col.type === 'date'"
              v-model="row[col.name]"
              type="date"
              size="small"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              :disabled="readonly"
              @change="onCellChange($index)"
            />
            <!-- 选择类型 -->
            <el-select
              v-else-if="col.type === 'select' || col.type === 'radio'"
              v-model="row[col.name]"
              size="small"
              style="width: 100%"
              :disabled="readonly"
              @change="onCellChange($index)"
            >
              <el-option
                v-for="opt in (col.options || [])"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <!-- 开关类型 -->
            <el-switch
              v-else-if="col.type === 'switch'"
              v-model="row[col.name]"
              size="small"
              :disabled="readonly"
              @change="onCellChange($index)"
            />
            <!-- 其他默认文本 -->
            <el-input v-else v-model="row[col.name]" size="small" :disabled="readonly" @input="onCellChange($index)" />
          </template>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" v-if="!readonly">
        <template #default="{ $index }">
          <el-button type="danger" link size="small" @click="removeRow($index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, watch, computed, reactive } from 'vue'
import { Plus } from '@element-plus/icons-vue'

export interface SubformColumn {
  name: string
  label: string
  type: string
  options?: Array<{ label: string; value: any }>
  formula?: string          // 行内公式，如 "{单价} * {数量}"
  aggregation?: 'SUM' | 'AVG' | 'COUNT' | 'MIN' | 'MAX'  // 汇总方式（针对数字列）
  unit?: string             // 单位后缀
}

const props = withDefaults(defineProps<{
  modelValue: any[]
  columns: SubformColumn[]
  readonly?: boolean
  enableSummary?: boolean    // 是否显示汇总行
}>(), {
  readonly: false,
  enableSummary: true
})

const emit = defineEmits(['update:modelValue', 'change'])

const localRows = ref<any[]>([...(props.modelValue || [])])
const computingRows = reactive(new Set<number>())

// 是否有汇总列
const summaryRow = computed(() => {
  return props.enableSummary && props.columns.some(c => c.aggregation && (c.type === 'number' || c.type === 'money'))
})

// 获取数字列（用于汇总）
const aggColumns = computed(() => props.columns.filter(c => c.aggregation && (c.type === 'number' || c.type === 'money')))

// 获取公式列
const formulaColumns = computed(() => props.columns.filter(c => c.formula))

// ============ 行操作 ============

function addRow() {
  const newRow: any = {}
  props.columns.forEach(col => {
    if (col.type === 'number' || col.type === 'money') {
      newRow[col.name] = col.defaultValue ?? 0
    } else if (col.type === 'switch') {
      newRow[col.name] = false
    } else if (col.type === 'checkbox' || col.multiple) {
      newRow[col.name] = []
    } else {
      newRow[col.name] = col.defaultValue ?? ''
    }
  })
  localRows.value.push(newRow)
  // 新行立即计算公式
  computeRow(localRows.value.length - 1)
  emitChange()
}

function removeRow(index: number) {
  localRows.value.splice(index, 1)
  // 删除后重新计算所有公式行
  localRows.value.forEach((_, i) => computeRow(i))
  emitChange()
}

function emitChange() {
  emit('update:modelValue', localRows.value)
  emit('change', { rows: localRows.value, summary: computeSummary() })
}

// ============ 单元格变化触发公式重算 ============

function onCellChange(rowIndex: number) {
  computeRow(rowIndex)
  emitChange()
}

// ============ 公式计算引擎（纯前端，无 AST 依赖）============

function evaluateFormula(formula: string, context: Record<string, any>): any {
  if (!formula) return null
  try {
    // 替换字段引用 {字段名}
    let expr = formula
    const fieldPattern = /\{([^}]+)\}/g
    expr = expr.replace(fieldPattern, (_, fieldName) => {
      const val = context[fieldName]
      if (val === undefined || val === null) return '0'
      if (typeof val === 'string' && val.trim() === '') return '0'
      return JSON.stringify(val)
    })

    // 安全替换：移除可能的危险字符，只允许数学运算
    expr = expr.replace(/[^0-9+\-*/().%<>=!&|, ]/g, '')

    // eslint-disable-next-line no-new-func
    const fn = new Function(`return (${expr})`)
    const result = fn()
    return isNaN(result) || !isFinite(result) ? null : result
  } catch {
    return null
  }
}

function computeRow(rowIndex: number) {
  if (rowIndex < 0 || rowIndex >= localRows.value.length) return
  const row = localRows.value[rowIndex]

  formulaColumns.value.forEach(col => {
    if (!col.formula) return
    // 构建行内上下文（字段值 + thisRow 引用）
    const context: Record<string, any> = { ...row, thisRow: row }
    // 也把其他行数据作为 {row1.字段} 等引用（可选）
    localRows.value.forEach((r, i) => {
      if (i !== rowIndex) {
        Object.keys(r).forEach(k => {
          // 不覆盖当前行
        })
      }
    })
    const result = evaluateFormula(col.formula, context)
    if (result !== null) {
      row[col.name] = result
    }
  })
}

function computeAllFormulas() {
  computingRows.clear()
  localRows.value.forEach((_, i) => {
    computingRows.add(i)
    computeRow(i)
  })
  // 短暂显示计算中状态
  setTimeout(() => computingRows.clear(), 300)
}

// ============ 聚合汇总 ============

function computeSummary(): Record<string, any> {
  const summary: Record<string, any> = {}
  aggColumns.value.forEach(col => {
    const nums = localRows.value
      .map(r => parseFloat(r[col.name]))
      .filter(n => !isNaN(n))
    if (nums.length === 0) {
      summary[col.name] = '-'
      return
    }
    switch (col.aggregation) {
      case 'SUM':
        summary[col.name] = nums.reduce((a, b) => a + b, 0)
        break
      case 'AVG':
        summary[col.name] = nums.reduce((a, b) => a + b, 0) / nums.length
        break
      case 'COUNT':
        summary[col.name] = nums.length
        break
      case 'MIN':
        summary[col.name] = Math.min(...nums)
        break
      case 'MAX':
        summary[col.name] = Math.max(...nums)
        break
      default:
        summary[col.name] = nums.reduce((a, b) => a + b, 0)
    }
    if (col.unit && typeof summary[col.name] === 'number') {
      summary[col.name] = summary[col.name] + ' ' + col.unit
    }
  })
  return summary
}

function getSummary({ columns, data }: any): string[] {
  const summary: string[] = [''] // 第一个空列是 # 列
  const numColCount = columns.length - 2 // 去掉 # 列和操作列
  let aggColIndex = 0

  columns.forEach((col: any, i: number) => {
    if (i === 0) return // # 列
    // 找到对应的聚合列
    const colName = col.property
    const aggCol = aggColumns.value.find(c => c.name === colName)
    if (!aggCol) {
      summary.push('')
      return
    }
    const nums = data.map((row: any) => parseFloat(row[colName])).filter((n: number) => !isNaN(n))
    if (nums.length === 0) {
      summary.push('-')
      return
    }
    let val = 0
    switch (aggCol.aggregation) {
      case 'SUM': val = nums.reduce((a: number, b: number) => a + b, 0); break
      case 'AVG': val = nums.reduce((a: number, b: number) => a + b, 0) / nums.length; break
      case 'COUNT': val = nums.length; break
      case 'MIN': val = Math.min(...nums); break
      case 'MAX': val = Math.max(...nums); break
    }
    const formatted = Number.isInteger(val) ? val.toString() : val.toFixed(2)
    summary.push(`${aggCol.aggregation}(${aggCol.label}) = ${formatted}${aggCol.unit || ''}`)
  })

  return summary
}

// ============ 格式化显示 ============

function formatValue(value: any, col: SubformColumn): string {
  if (value === undefined || value === null || value === '') return '-'
  if (col.type === 'money' || col.type === 'number') {
    const num = parseFloat(value)
    if (isNaN(num)) return String(value)
    const formatted = Number.isInteger(num) ? num.toString() : num.toFixed(2)
    return col.unit ? `${formatted} ${col.unit}` : formatted
  }
  return String(value)
}

// ============ 监听外部数据变化 ============

watch(() => props.modelValue, (val) => {
  const newStr = JSON.stringify(val)
  const currStr = JSON.stringify(localRows.value)
  if (newStr !== currStr) {
    localRows.value = [...(val || [])]
    computeAllFormulas()
  }
}, { deep: true, immediate: false })

// 初始计算公式
computeAllFormulas()
</script>

<style scoped>
.subform-table {
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 8px;
  background: var(--el-fill-color-light);
}

.subform-toolbar {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.subform-table-grid :deep(.el-table__header-wrapper th) {
  background: var(--el-fill-color) !important;
}

.formula-badge {
  display: inline-block;
  margin-left: 4px;
  font-size: 10px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 0 4px;
  border-radius: 3px;
  cursor: help;
}

.formula-cell {
  color: var(--el-color-primary);
  font-weight: 500;
  padding: 0 4px;
  border-radius: 3px;
  background: var(--el-color-primary-light-9);
  min-height: 20px;
  display: block;
}

.formula-computing {
  opacity: 0.5;
}
</style>
