<template>
  <div class="matrix-input">
    <div class="matrix-header">
      <h3>{{ title }}</h3>
      <div class="matrix-actions">
        <el-button v-if="showAddRow" size="small" @click="addRow">
          <el-icon><Plus /></el-icon> 添加行
        </el-button>
        <el-button v-if="showAddCol" size="small" @click="addColumn">
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
                @click="removeColumn(colIdx)"
                style="margin-left: 4px;"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIdx) in rowHeaders" :key="rowIdx">
            <td class="row-header">
              {{ typeof row === 'object' ? row.label : row }}
              <el-button 
                v-if="showEditRow" 
                type="danger" 
                size="small" 
                text 
                @click="removeRow(rowIdx)"
                style="margin-left: 4px;"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </td>
            <td v-for="(col, colIdx) in colHeaders" :key="colIdx" class="data-cell">
              <el-input-number 
                v-model="matrixData[rowIdx][colIdx]" 
                :precision="2" 
                :step="100"
                controls-position="right"
                size="small"
                style="width: 100%;"
              />
            </td>
          </tr>
        </tbody>
        <tfoot v-if="showTotals">
          <tr>
            <td class="total-label">总计</td>
            <td v-for="(col, colIdx) in colHeaders" :key="colIdx" class="total-cell">
              {{ getColumnTotal(colIdx) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
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
  // 模型值（一维格式的数据数组）
  modelValue: {
    type: Array as PropType<any[]>,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'add-row', 'add-column', 'remove-row', 'remove-column'])

// 行表头
const rowHeaders = computed(() => props.rowOptions.map(opt => opt.label))

// 列表头
const colHeaders = computed(() => props.colOptions.map(opt => opt.label))

// 矩阵数据（二维数组）
const matrixData = ref<any[][]>([])

// 初始化矩阵数据
function initMatrixData() {
  const rows = rowHeaders.value.length
  const cols = colHeaders.value.length
  const data = Array(rows).fill(0).map(() => Array(cols).fill(''))
  
  // 从 modelValue 填充数据
  props.modelValue.forEach(item => {
    const rowIdx = rowHeaders.value.findIndex(h => h === item.row_dimension)
    const colIdx = colHeaders.value.findIndex(h => h === item.col_dimension)
    if (rowIdx >= 0 && colIdx >= 0) {
      data[rowIdx][colIdx] = item.value || ''
    }
  })
  
  matrixData.value = data
}

// 获取列总计
function getColumnTotal(colIdx: number) {
  const values = matrixData.value
    .map(row => parseFloat(row[colIdx]))
    .filter(v => !isNaN(v))
  
  if (values.length === 0) return '-'
  const sum = values.reduce((a, b) => a + b, 0)
  return sum.toFixed(2)
}

// 添加行
function addRow() {
  emit('add-row')
}

// 添加列
function addColumn() {
  emit('add-column')
}

// 删除行
function removeRow(rowIdx: number) {
  emit('remove-row', rowIdx)
}

// 删除列
function removeColumn(colIdx: number) {
  emit('remove-column', colIdx)
}

// 将矩阵数据转换为一维格式（用于提交）
function toOneDimFormat() {
  const result = []
  for (let i = 0; i < rowHeaders.value.length; i++) {
    for (let j = 0; j < colHeaders.value.length; j++) {
      result.push({
        row_dimension: props.rowOptions[i].value || props.rowOptions[i].label,
        col_dimension: props.colOptions[j].value || props.colOptions[j].label,
        value: matrixData.value[i][j] || null
      })
    }
  }
  return result
}

// 监听矩阵数据变化，触发更新
watch(matrixData, (newVal) => {
  const oneDimData = toOneDimFormat()
  emit('update:modelValue', oneDimData)
}, { deep: true })

onMounted(() => {
  initMatrixData()
})

// 暴露方法给父组件
defineExpose({
  toOneDimFormat,
  initMatrixData
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
</style>
