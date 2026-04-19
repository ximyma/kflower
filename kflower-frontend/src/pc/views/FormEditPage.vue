<template>
  <div class="form-edit-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑数据' : '新增数据' }}</span>
          <el-button @click="goBack">返回</el-button>
        </div>
      </template>

      <el-form :model="formData" label-width="120px">
        <el-form-item
          v-for="field in formFields"
          :key="field.name"
          :label="field.label"
          :required="field.required"
        >
          <!-- 文本类型 -->
          <el-input
            v-if="field.type === 'text' || field.type === 'phone' || field.type === 'email'"
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
          />

          <!-- 数字类型 -->
          <el-input-number
            v-else-if="field.type === 'number' || field.type === 'money' || field.type === 'percent'"
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :precision="field.type === 'percent' ? 2 : 0"
          />

          <!-- 日期类型 -->
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="formData[field.name]"
            type="date"
            :placeholder="field.placeholder || `请选择${field.label}`"
            value-format="YYYY-MM-DD"
          />

          <!-- 下拉选择 -->
          <el-select
            v-else-if="field.type === 'select' || field.type === 'radio'"
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请选择${field.label}`"
            :multiple="field.type === 'checkbox'"
          >
            <el-option
              v-for="opt in field.options"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>

          <!-- 多行文本 -->
          <el-input
            v-else-if="field.type === 'textarea'"
            v-model="formData[field.name]"
            type="textarea"
            :rows="4"
            :placeholder="field.placeholder || `请输入${field.label}`"
          />

          <!-- 其他类型默认用文本 -->
          <el-input
            v-else
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveForm" :loading="saving">保存</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { templateAPI } from '@/common/api/index'

const route = useRoute()
const router = useRouter()

const appId = ref(Number(route.params.appId))
const templateId = ref(Number(route.params.templateId))
const dataId = computed(() => route.params.dataId ? Number(route.params.dataId) : null)

const isEdit = computed(() => !!dataId.value)
const formFields = ref<any[]>([])
const formData = ref<Record<string, any>>({})
const saving = ref(false)

// 加载模板
async function loadTemplate() {
  try {
    const res: any = await templateAPI.get(templateId.value)
    
    // 提取字段
    const modules = res.modules || []
    formFields.value = []
    for (const mod of modules) {
      if (mod.fields) {
        formFields.value.push(...mod.fields)
      }
    }

    // 初始化表单数据
    formFields.value.forEach((field: any) => {
      formData.value[field.name] = field.defaultValue || ''
    })

    // 如果是编辑，加载数据
    if (dataId.value) {
      await loadFormData()
    }
  } catch (e: any) {
    ElMessage.error('加载表单失败：' + (e.message || ''))
  }
}

// 加载表单数据
async function loadFormData() {
  if (!dataId.value) return
  try {
    const res: any = await templateAPI.getDataDetail(templateId.value, dataId.value)
    Object.keys(formData.value).forEach(key => {
      if (res[key] !== undefined) {
        formData.value[key] = res[key]
      }
    })
  } catch (e: any) {
    ElMessage.error('加载数据失败：' + (e.message || ''))
  }
}

// 保存表单
async function saveForm() {
  saving.value = true
  try {
    if (dataId.value) {
      await templateAPI.updateData(templateId.value, dataId.value, formData.value)
      ElMessage.success('更新成功')
    } else {
      await templateAPI.submitData(templateId.value, formData.value)
      ElMessage.success('创建成功')
    }
    goBack()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    saving.value = false
  }
}

// 返回
function goBack() {
  router.push(`/app/${appId.value}/form/${templateId.value}`)
}

// 监听路由变化，重新加载数据
watch(() => [route.params.templateId, route.params.dataId], ([newTemplateId, newDataId]) => {
  if (newTemplateId) {
    templateId.value = Number(newTemplateId)
    formData.value = {}
    formFields.value = []
    loadTemplate()
  }
})

onMounted(() => {
  loadTemplate()
})
</script>

<style scoped lang="scss">
.form-edit-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
