<template>
  <div class="subform-table">
    <div class="subform-toolbar">
      <el-button type="primary" size="small" @click="addRow" v-if="!readonly">
        <el-icon><Plus /></el-icon> 添加行
      </el-button>
    </div>
    <el-table :data="localRows" border size="small" class="subform-table-grid">
      <el-table-column type="index" label="#" width="50" />
      <el-table-column
        v-for="col in columns"
        :key="col.name"
        :prop="col.name"
        :label="col.label"
        :min-width="120"
      >
        <template #default="{ row }">
          <!-- 文本类型 -->
          <el-input
            v-if="col.type === 'text' || col.type === 'textarea'"
            v-model="row[col.name]"
            size="small"
            :type="col.type === 'textarea' ? 'textarea' : 'text'"
            :rows="col.type === 'textarea' ? 2 : undefined"
            :disabled="readonly"
          />
          <!-- 数字类型 -->
          <el-input-number
            v-else-if="col.type === 'number' || col.type === 'money'"
            v-model="row[col.name]"
            size="small"
            :precision="col.type === 'money' ? 2 : 0"
            :controls="false"
            :disabled="readonly"
            style="width: 100%"
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
          />
          <!-- 选择类型 -->
          <el-select
            v-else-if="col.type === 'select' || col.type === 'radio'"
            v-model="row[col.name]"
            size="small"
            style="width: 100%"
            :disabled="readonly"
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
          />
          <!-- 其他类型默认文本 -->
          <el-input v-else v-model="row[col.name]" size="small" :disabled="readonly" />
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
import { ref, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'

export interface SubformColumn {
  name: string
  label: string
  type: string
  options?: Array<{ label: string; value: any }>
}

const props = withDefaults(defineProps<{
  modelValue: any[]
  columns: SubformColumn[]
  readonly?: boolean
}>(), {
  readonly: false
})

const emit = defineEmits(['update:modelValue'])

const localRows = ref<any[]>([...(props.modelValue || [])])

function addRow() {
  const newRow: any = {}
  props.columns.forEach(col => {
    if (col.type === 'number' || col.type === 'money') {
      newRow[col.name] = 0
    } else if (col.type === 'switch') {
      newRow[col.name] = false
    } else {
      newRow[col.name] = ''
    }
  })
  localRows.value.push(newRow)
  emitChange()
}

function removeRow(index: number) {
  localRows.value.splice(index, 1)
  emitChange()
}

function emitChange() {
  emit('update:modelValue', localRows.value)
}

watch(() => props.modelValue, (val) => {
  if (JSON.stringify(val) !== JSON.stringify(localRows.value)) {
    localRows.value = [...(val || [])]
  }
}, { deep: true })
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
}
.subform-table-grid :deep(.el-table__header-wrapper th) {
  background: var(--el-fill-color) !important;
}
</style>
