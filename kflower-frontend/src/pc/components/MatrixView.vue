<template>
  <div class="matrix-view">
    <div class="matrix-header">
      <h3>{{ title }}</h3>
      <div class="matrix-actions">
        <el-button size="small" @click="exportToExcel">
          <el-icon><Download /></el-icon> 导出Excel
        </el-button>
        <el-button size="small" @click="printMatrix">
          <el-icon><Printer /></el-icon> 打印
        </el-button>
      </div>
    </div>
    
    <div class="matrix-table-wrapper" ref="matrixTableRef">
      <table class="matrix-table" border="1" cellspacing="0" cellpadding="8">
        <thead>
          <tr>
            <th class="corner-header">{{ rowDimensionLabel }}</th>
            <th v-for="col in colHeaders" :key="col">{{ col }}</th>
            <th v-if="showActions" class="action-header">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rowHeaders" :key="row">
            <td class="row-header">{{ row }}</td>
            <td v-for="col in colHeaders" :key="col" class="data-cell">
              {{ getCellValue(row, col) }}
            </td>
            <td v-if="showActions" class="action-cell">
              <el-button type="danger" size="small" @click="deleteRow(row)">删除</el-button>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="showTotals">
          <tr>
            <td class="total-label">总计</td>
            <td v-for="col in colHeaders" :key="col" class="total-cell">
              {{ getColumnTotal(col) }}
            </td>
            <td v-if="showActions"></td>
          </tr>
        </tfoot>
      </table>
    </div>
    
    <div v-if="showAddRow || showAddCol" class="matrix-controls">
      <el-button v-if="showAddRow" @click="addRow">
        <el-icon><Plus /></el-icon> 添加行
      </el-button>
      <el-button v-if="showAddCol" @click="addColumn">
        <el-icon><Plus /></el-icon> 添加列
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { PropType } from 'vue'

const props = defineProps({
  // 数据数组（一维格式）
  data: {
    type: Array as PropType<any[]>,
    required: true
  },
  // 行维度字段名
  rowDimensionField: {
    type: String,
    required: true
  },
  // 列维度字段名
  colDimensionField: {
    type: String,
    required: true
  },
  // 数值字段名
  valueField: {
    type: String,
    required: true
  },
  // 标题
  title: {
    type: String,
    default: '矩阵视图'
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
  // 是否显示操作列
  showActions: {
    type: Boolean,
    default: false
  },
  // 是否显示总计行
  showTotals: {
    type: Boolean,
    default: false
  },
  // 是否允许添加行
  showAddRow: {
    type: Boolean,
    default: false
  },
  // 是否允许添加列
  showAddCol: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['add-row', 'add-column', 'delete-row'])

// 提取行表头
const rowHeaders = computed(() => {
  const set = new Set<string>()
  props.data.forEach(item => {
    const val = item[props.rowDimensionField]
    if (val) set.add(val)
  })
  return Array.from(set)
})

// 提取列表头
const colHeaders = computed(() => {
  const set = new Set<string>()
  props.data.forEach(item => {
    const val = item[props.colDimensionField]
    if (val) set.add(val)
  })
  return Array.from(set)
})

// 获取数据单元格的值
function getCellValue(row: string, col: string) {
  const item = props.data.find(d => 
    d[props.rowDimensionField] === row && 
    d[props.colDimensionField] === col
  )
  return item ? item[props.valueField] : '-'
}

// 计算列总计
function getColumnTotal(col: string) {
  const values = props.data
    .filter(d => d[props.colDimensionField] === col)
    .map(d => parseFloat(d[props.valueField]))
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
function deleteRow(row: string) {
  emit('delete-row', row)
}

// 导出Excel
async function exportToExcel() {
  try {
    const XLSX = await import('xlsx')
    const wsData = []
    
    // 表头
    wsData.push([props.rowDimensionLabel, ...colHeaders.value])
    
    // 数据行
    rowHeaders.value.forEach(row => {
      const rowData = [row]
      colHeaders.value.forEach(col => {
        rowData.push(getCellValue(row, col))
      })
      wsData.push(rowData)
    })
    
    const ws = XLSX.utils.aoa_to_sheet(wsData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
    XLSX.writeFile(wb, `${props.title}.xlsx`)
    
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error('导出失败：' + e.message)
  }
}

// 打印
function printMatrix() {
  const tableHtml = matrixTableRef.value?.innerHTML || ''
  const printWindow = window.open('', '_blank')
  if (printWindow) {
    printWindow.document.write(`
      <html>
        <head>
          <title>${props.title}</title>
          <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #f5f5f5; font-weight: bold; }
            .row-header { font-weight: bold; background-color: #fafafa; }
          </style>
        </head>
        <body>
          <h2>${props.title}</h2>
          ${tableHtml}
        </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.print()
  }
}

const matrixTableRef = ref<HTMLElement>()
</script>

<style scoped>
.matrix-view {
  width: 100%;
  overflow-x: auto;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.matrix-table-wrapper {
  margin: 16px 0;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.matrix-table th,
.matrix-table td {
  border: 1px solid #dcdfe6;
  padding: 10px 12px;
  text-align: center;
}

.matrix-table th {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #303133;
}

.corner-header {
  background-color: #e8eaf0;
}

.row-header {
  font-weight: 600;
  background-color: #fafbfc;
  text-align: left;
}

.data-cell {
  min-width: 80px;
}

.total-label {
  font-weight: 700;
  background-color: #f0f2f5;
}

.total-cell {
  font-weight: 600;
  background-color: #f8f9fa;
}

.matrix-controls {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
</style>
