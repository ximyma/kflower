<template>
  <div class="matrix-input">
    <div class="matrix-header">
      <h3>{{ title }}</h3>
      <div class="matrix-actions">
        <el-button v-if="showAddRow" size="small" @click="handleAddRow">
          <el-icon><Plus /></el-icon> 添加行
        </el-button>
        <el-button v-if="showAddCol" size="small" @click="handleAddColumn">
          <el-icon><Plus /></el-icon> 添加列
        </el-button>
      </div>
    </div>

    <div class="matrix-table-wrapper">
      <table class="matrix-table" border="1" cellspacing="0" cellpadding="4">
        <thead>
          <tr>
            <th class="corner-header">{{ rowDimensionLabel }}</th>
            <th v-for="(col, colIdx) in colHeaders" :key="colIdx">
              {{ col }}
              <el-button
                v-if="showEditCol"
                type="danger"
                size="small"
                text
                @click="handleRemoveColumn(colIdx)"
                style="margin-left: 4px;"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </th>
            <th v-if="showRowTotals && valueFieldType === 'number'" class="total-column-header">行合计</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIdx) in rowHeaders" :key="rowIdx">
            <td class="row-header">
              {{ row }}
              <el-button
                v-if="showEditRow"
                type="danger"
                size="small"
                text
                @click="handleRemoveRow(rowIdx)"
                style="margin-left: 4px;"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </td>
            <td v-for="(col, colIdx) in colHeaders" :key="colIdx" class="data-cell">
              <!-- 数字类型 -->
              <el-input-number
                v-if="valueFieldType === 'number' && cellData[rowIdx]"
                v-model="cellData[rowIdx][colIdx]"
                :precision="2"
                :step="100"
                controls-position="right"
                size="small"
                style="width: 100%;"
                placeholder="0"
              />
              <!-- 下拉类型 -->
              <el-select
                v-else-if="valueFieldType === 'select' && cellData[rowIdx]"
                v-model="cellData[rowIdx][colIdx]"
                size="small"
                style="width: 100%;"
                placeholder="请选择"
              >
                <el-option
                  v-for="opt in valueOptions"
                  :key="opt.value || opt"
                  :label="opt.label || opt"
                  :value="opt.value || opt"
                />
              </el-select>
              <!-- 文本类型 -->
              <el-input
                v-else-if="cellData[rowIdx]"
                v-model="cellData[rowIdx][colIdx]"
                size="small"
                style="width: 100%;"
                placeholder="请输入"
              />
              <!-- 数据未初始化占位 -->
              <span v-else class="loading-placeholder">加载中...</span>
            </td>
            <td v-if="showRowTotals && valueFieldType === 'number'" class="row-total-cell">
              {{ getRowTotal(rowIdx) }}
            </td>
          </tr>
        </tbody>
        <tfoot v-if="showTotals">
          <tr>
            <td class="total-label">总计</td>
            <td v-for="(col, colIdx) in colHeaders" :key="colIdx" class="total-cell">
              {{ getColumnTotal(colIdx) }}
            </td>
            <td v-if="showRowTotals && valueFieldType === 'number'" class="total-cell grand-total">
              {{ getGrandTotal() }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { PropType } from 'vue'

const props = defineProps({
  // 行维度选项（用于下拉选择或显示）
  rowOptions: {
    type: Array as PropType<{label: string, value: string}[]>,
    required: true
  },
  // 列维度选项（用于下拉选择或显示）
  colOptions: {
    type: Array as PropType<{label: string, value: string}[]>,
    required: true
  },
  // 标题
  title: {
    type: String,
    default: '矩阵数据录入'
  },
  // 行维度标签
  rowDimensionLabel: {
    type: String,
    default: '行维度'
  },
  // 列维度标签
  colDimensionLabel: {
    type: String,
    default: '列维度'
  },
  // 值字段类型：number, text, select
  valueFieldType: {
    type: String as PropType<'number' | 'text' | 'select'>,
    default: 'number'
  },
  // 值字段选项（当类型为select时使用）
  valueOptions: {
    type: Array as PropType<{label: string, value: string}[]>,
    default: () => []
  },
  // 是否显示添加行按钮
  showAddRow: {
    type: Boolean,
    default: true
  },
  // 是否显示添加列按钮
  showAddCol: {
    type: Boolean,
    default: true
  },
  // 是否显示删除行按钮
  showEditRow: {
    type: Boolean,
    default: true
  },
  // 是否显示删除列按钮
  showEditCol: {
    type: Boolean,
    default: true
  },
  // 是否显示总计行
  showTotals: {
    type: Boolean,
    default: true
  },
  // 是否显示行合计列
  showRowTotals: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['add-row', 'add-column', 'remove-row', 'remove-column'])

// 行表头（使用 label 作为标识符，与 setData/getData 保持一致）
const rowHeaders = computed(() => props.rowOptions.map(opt => typeof opt === 'object' ? opt.label : opt))

// 列表头
const colHeaders = computed(() => props.colOptions.map(opt => typeof opt === 'object' ? opt.label : opt))

// 单元格数据
const cellData = ref<any[][]>([])

// 防递归标志
let isInitializing = false

// 上一次的数据快照（用于在行列变化时保留数据）
let dataSnapshot: any[][] = []

// 初始化矩阵数据
function initData() {
  const rows = rowHeaders.value.length
  const cols = colHeaders.value.length

  if (rows === 0 || cols === 0) {
    console.warn('MatrixInput: rowOptions or colOptions is empty')
    cellData.value = []
    dataSnapshot = []
    return
  }

  isInitializing = true

  // 创建新矩阵
  const newData = Array(rows).fill(0).map(() => Array(cols).fill(null))

  // 尝试从快照恢复数据
  if (dataSnapshot.length > 0) {
    // 只在新增行列时保留现有数据，不匹配的新增行列用 null
    for (let i = 0; i < Math.min(rows, dataSnapshot.length); i++) {
      for (let j = 0; j < Math.min(cols, dataSnapshot[i]?.length || 0); j++) {
        newData[i][j] = dataSnapshot[i][j]
      }
    }
  }

  cellData.value = newData
  dataSnapshot = [...newData.map(row => [...row])]
  isInitializing = false
}

// 获取列总计
function getColumnTotal(colIdx: number) {
  if (!cellData.value || cellData.value.length === 0) return '-'
  const values = cellData.value
    .map(row => row[colIdx])
    .filter(v => v !== null && v !== undefined && v !== '')

  // 如果是数字类型，求和
  if (props.valueFieldType === 'number') {
    const nums = values.map(v => parseFloat(v)).filter(v => !isNaN(v))
    if (nums.length === 0) return '-'
    return nums.reduce((a, b) => a + b, 0).toFixed(2)
  }

  // 其他类型显示数量
  return values.length > 0 ? values.length : '-'
}

// 获取行合计
function getRowTotal(rowIdx: number) {
  if (!cellData.value || !cellData.value[rowIdx]) return '-'
  const values = cellData.value[rowIdx]
    .filter(v => v !== null && v !== undefined && v !== '')

  if (props.valueFieldType === 'number') {
    const nums = values.map(v => parseFloat(v)).filter(v => !isNaN(v))
    if (nums.length === 0) return '-'
    return nums.reduce((a, b) => a + b, 0).toFixed(2)
  }

  return values.length > 0 ? values.length : '-'
}

// 获取总计（所有单元格之和）
function getGrandTotal() {
  if (!cellData.value || cellData.value.length === 0) return '-'
  const allValues = cellData.value.flat()
    .filter(v => v !== null && v !== undefined && v !== '')
    .map(v => parseFloat(v))
    .filter(v => !isNaN(v))

  if (allValues.length === 0) return '-'
  return allValues.reduce((a, b) => a + b, 0).toFixed(2)
}

// 添加行
function handleAddRow() {
  emit('add-row')
}

// 添加列
function handleAddColumn() {
  emit('add-column')
}

// 删除行
function handleRemoveRow(rowIdx: number) {
  emit('remove-row', rowIdx)
}

// 删除列
function handleRemoveColumn(colIdx: number) {
  emit('remove-column', colIdx)
}

// 将矩阵数据转换为一维格式
function getData() {
  const result: any[] = []
  if (!cellData.value || cellData.value.length === 0) return result

  for (let i = 0; i < rowHeaders.value.length; i++) {
    for (let j = 0; j < colHeaders.value.length; j++) {
      const val = cellData.value[i]?.[j]
      // 只保存有值的单元格（保留数字和文本）
      if (val !== null && val !== undefined && val !== '') {
        const rowOpt = props.rowOptions[i]
        const colOpt = props.colOptions[j]
        result.push({
          row_dimension: typeof rowOpt === 'object' ? rowOpt.value || rowOpt.label : rowOpt,
          col_dimension: typeof colOpt === 'object' ? colOpt.value || colOpt.label : colOpt,
          value: props.valueFieldType === 'number' ? Number(val) : val
        })
      }
    }
  }
  return result
}

// 设置初始数据（用于编辑已有数据）
function setData(data: any[]) {
  const rows = rowHeaders.value.length
  const cols = colHeaders.value.length

  if (rows === 0 || cols === 0) {
    console.warn('MatrixInput.setData: rowOptions or colOptions is empty')
    return
  }

  isInitializing = true

  // 创建空矩阵
  const matrix = Array(rows).fill(0).map(() => Array(cols).fill(null))

  // 填充已有数据 - 使用 label 匹配
  if (data && data.length > 0) {
    data.forEach(item => {
      // 优先用 label 匹配（rowHeaders 就是从 label 生成的）
      let rowIdx = -1
      let colIdx = -1

      // 查找行
      for (let i = 0; i < props.rowOptions.length; i++) {
        const opt = props.rowOptions[i]
        const label = typeof opt === 'object' ? opt.label : opt
        const value = typeof opt === 'object' ? opt.value : opt
        if (label === item.row_dimension || value === item.row_dimension) {
          rowIdx = i
          break
        }
      }

      // 查找列
      for (let j = 0; j < props.colOptions.length; j++) {
        const opt = props.colOptions[j]
        const label = typeof opt === 'object' ? opt.label : opt
        const value = typeof opt === 'object' ? opt.value : opt
        if (label === item.col_dimension || value === item.col_dimension) {
          colIdx = j
          break
        }
      }

      if (rowIdx >= 0 && colIdx >= 0) {
        const val = item.value
        // 数字类型需要转换
        if (props.valueFieldType === 'number') {
          if (val !== null && val !== undefined && val !== '') {
            matrix[rowIdx][colIdx] = Number(val)
          }
        } else {
          matrix[rowIdx][colIdx] = val
        }
      }
    })
  }

  cellData.value = matrix
  dataSnapshot = [...matrix.map(row => [...row])]
  isInitializing = false
}

// 监听行列选项变化 - 保护现有数据
watch(
  [() => props.rowOptions, () => props.colOptions],
  () => {
    // 先保存当前数据快照
    if (cellData.value.length > 0) {
      dataSnapshot = [...cellData.value.map(row => [...row])]
    }
    // 再初始化（会从快照恢复数据）
    nextTick(() => {
      initData()
    })
  },
  { immediate: true, deep: true }
)

// 暴露方法给父组件
defineExpose({
  getData,
  setData
})

// 组件挂载时立即初始化数据（防止模板渲染时 cellData 仍为空）
onMounted(() => {
  nextTick(() => {
    if (cellData.value.length === 0) {
      initData()
    }
  })
})
</script>

<style scoped>
.matrix-input {
  width: 100%;
  overflow-x: auto;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.matrix-table-wrapper {
  margin: 12px 0;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid #dcdfe6;
  padding: 6px 8px;
  text-align: center;
  min-width: 80px;
}

.matrix-table th {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #303133;
}

.corner-header {
  background-color: #e8eaf0;
  min-width: 100px;
}

.row-header {
  font-weight: 600;
  background-color: #fafbfc;
  text-align: left;
  min-width: 100px;
}

.data-cell {
  min-width: 100px;
}

.total-label {
  font-weight: 700;
  background-color: #f0f2f5;
}

.total-cell {
  font-weight: 600;
  background-color: #f8f9fa;
}

.total-column-header {
  background-color: #e8eaf0;
  min-width: 80px;
}

.row-total-cell {
  font-weight: 600;
  background-color: #f8f9fa;
  color: #409eff;
}

.grand-total {
  color: #67c23a;
  font-size: 14px;
}
</style>
