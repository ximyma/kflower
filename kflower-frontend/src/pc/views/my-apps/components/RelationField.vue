<template>
  <div class="relation-field">
    <el-select
      v-model="localValue"
      :placeholder="placeholder || '请选择'"
      :disabled="disabled"
      :clearable="clearable"
      filterable
      remote
      :remote-method="searchRemote"
      :loading="searchLoading"
      style="width: 100%"
      @change="handleChange"
    >
      <el-option
        v-for="item in options"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { templateAPI } from '@/common/api'

const props = withDefaults(defineProps<{
  modelValue?: number | null
  targetTemplateId?: number
  displayField?: string
  placeholder?: string
  disabled?: boolean
  clearable?: boolean
}>(), {
  modelValue: null,
  targetTemplateId: undefined,
  displayField: 'name',
  disabled: false,
  clearable: true
})

const emit = defineEmits(['update:modelValue', 'change'])

const localValue = ref(props.modelValue)
const options = ref<Array<{ value: number; label: string }>>([])
const searchLoading = ref(false)

async function searchRemote(query: string) {
  if (!props.targetTemplateId) return
  searchLoading.value = true
  try {
    const res: any = await templateAPI.getData(props.targetTemplateId, {
      search: query,
      limit: 20
    })
    const items = Array.isArray(res) ? res : (res.items || [])
    options.value = items.map((item: any) => ({
      value: item.id,
      label: String(item[props.displayField] || item.id)
    }))
  } catch (e) {
    console.error('Search failed', e)
  } finally {
    searchLoading.value = false
  }
}

function handleChange(val: number | null) {
  emit('update:modelValue', val)
  emit('change', val)
}

watch(() => props.modelValue, (val) => {
  if (val !== localValue.value) {
    localValue.value = val
  }
})

onMounted(() => {
  if (props.targetTemplateId) {
    searchRemote('')
  }
})
</script>
