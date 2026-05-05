<template>
  <div class="app-form-edit">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-left" @click="goBack">
        <el-icon :size="22"><ArrowLeft /></el-icon>
      </div>
      <div class="nav-title">{{ isEditing ? '编辑数据' : '新增数据' }}</div>
      <div class="nav-right">
        <el-button type="primary" size="small" round @click="saveData" :loading="saving">
          保存
        </el-button>
      </div>
    </div>

    <div class="page-content" v-loading="loading">
      <div class="form-container">
        <!-- 模板名称 -->
        <div class="template-name">{{ templateData.name }}</div>

        <!-- 动态表单 -->
        <el-form :model="formData" label-position="top" size="large">
          <el-form-item
            v-for="field in formFields"
            :key="field.name"
            :label="field.label"
            :required="field.required"
          >
            <!-- 文本输入 -->
            <el-input
              v-if="field.type === 'text' || field.type === 'string'"
              v-model="formData[field.name]"
              :placeholder="field.placeholder || `请输入${field.label}`"
            />

            <!-- 数字输入 -->
            <el-input-number
              v-else-if="field.type === 'number' || field.type === 'int' || field.type === 'float'"
              v-model="formData[field.name]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              controls-position="right"
              style="width: 100%"
            />

            <!-- 多行文本 -->
            <el-input
              v-else-if="field.type === 'textarea' || field.type === 'text_area'"
              v-model="formData[field.name]"
              type="textarea"
              :rows="4"
              :placeholder="field.placeholder || `请输入${field.label}`"
            />

            <!-- 日期选择 -->
            <el-date-picker
              v-else-if="field.type === 'date'"
              v-model="formData[field.name]"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />

            <!-- 日期时间选择 -->
            <el-date-picker
              v-else-if="field.type === 'datetime'"
              v-model="formData[field.name]"
              type="datetime"
              placeholder="选择日期时间"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 100%"
            />

            <!-- 下拉选择 -->
            <el-select
              v-else-if="field.type === 'select' || field.type === 'enum'"
              v-model="formData[field.name]"
              :placeholder="field.placeholder || `请选择${field.label}`"
              style="width: 100%"
            >
              <el-option
                v-for="opt in (field.options || [])"
                :key="opt.value || opt"
                :label="opt.label || opt"
                :value="opt.value || opt"
              />
            </el-select>

            <!-- 复选框 -->
            <el-checkbox
              v-else-if="field.type === 'boolean' || field.type === 'bool'"
              v-model="formData[field.name]"
            >
              {{ field.label }}
            </el-checkbox>

            <!-- 默认文本输入 -->
            <el-input
              v-else
              v-model="formData[field.name]"
              :placeholder="field.placeholder || `请输入${field.label}`"
            />
          </el-form-item>
        </el-form>

        <!-- 删除按钮（编辑模式下显示） -->
        <div v-if="isEditing" class="delete-section">
          <el-button type="danger" plain @click="deleteData" class="delete-btn">
            <el-icon><Delete /></el-icon>删除此数据
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { templateAPI } from '../../common/api'

const router = useRouter()
const route = useRoute()
const appId = Number(route.params.appId)
const templateId = Number(route.params.templateId)
const dataId = route.params.dataId ? Number(route.params.dataId) : null

const isEditing = computed(() => !!dataId)

const loading = ref(false)
const saving = ref(false)
const templateData = ref<any>({})
const formData = ref<any>({})
const formFields = ref<any[]>([])

function goBack() {
  router.push({ name: 'AppFormListPage', params: { appId, templateId: String(templateId) } })
}

async function saveData() {
  saving.value = true
  try {
    if (isEditing.value) {
      await templateAPI.updateData(templateId, dataId, formData.value)
      ElMessage.success('更新成功')
    } else {
      await templateAPI.submitData(templateId, formData.value)
      ElMessage.success('创建成功')
    }
    goBack()
  } catch (error: any) {
    console.error('[AppFormEdit] 保存失败:', error)
    ElMessage.error(error?.response?.data?.detail || error?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteData() {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条数据吗？删除后无法恢复。',
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await templateAPI.deleteData(templateId, dataId)
    ElMessage.success('删除成功')
    goBack()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('[AppFormEdit] 删除失败:', error)
      ElMessage.error(error?.response?.data?.detail || error?.message || '删除失败')
    }
  }
}

async function loadData() {
  loading.value = true
  try {
    // 加载模板详情
    const tmpl = await templateAPI.get(templateId)
    templateData.value = tmpl

    // 提取表单字段
    const fields = extractFields(tmpl)
    formFields.value = fields

    // 初始化表单数据
    fields.forEach(f => {
      if (!(f.name in formData.value)) {
        formData.value[f.name] = f.defaultValue || null
      }
    })

    // 如果是编辑模式，加载数据详情
    if (isEditing.value) {
      const res = await templateAPI.getDataDetail(templateId, dataId)
      // 后端返回数据在 config.data 里面
      const mainData = res.config?.data || res.data || res
      formData.value = { ...formData.value, ...mainData }
      console.log('[AppFormEdit] 加载数据详情:', res, mainData)
    }

    console.log('[AppFormEdit] 加载成功:', {
      template: tmpl.name,
      fields: fields.length,
      data: isEditing.value ? '已加载' : '新增模式'
    })
  } catch (error) {
    console.error('[AppFormEdit] 加载失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function extractFields(template: any): any[] {
  const fields: any[] = []
  const modules = template.modules || []

  // 支持 modules 是 JSON 字符串或数组
  let modulesList = modules
  if (typeof modules === 'string') {
    try {
      modulesList = JSON.parse(modules)
    } catch (e) {
      modulesList = []
    }
  }

  for (const mod of modulesList) {
    if (mod.fields && Array.isArray(mod.fields)) {
      for (const field of mod.fields) {
        // 跳过系统字段
        if (['id', 'created_at', 'updated_at', 'creator_id', 'app_id', 'template_id'].includes(field.name)) {
          continue
        }

        fields.push({
          name: field.name,
          label: field.label || field.name,
          type: field.type || 'text',
          required: field.required || false,
          placeholder: field.placeholder || '',
          options: field.options || [],
          defaultValue: field.default_value || field.defaultValue || null
        })
      }
    }
  }

  return fields
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.app-form-edit {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 20px;
}

/* 顶部导航 */
.nav-bar {
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.nav-title {
  flex: 1;
  font-size: 17px;
  font-weight: 600;
  text-align: center;
  padding-right: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-right {
  padding-right: 8px;
}

.nav-right :deep(.el-button) {
  padding: 6px 16px;
  font-size: 13px;
}

.page-content {
  padding: 16px;
}

.form-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #f0f0f0;
}

.template-name {
  font-size: 14px;
  color: #909399;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.form-container :deep(.el-form-item) {
  margin-bottom: 18px;
}

.form-container :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

.delete-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.delete-btn {
  width: 100%;
  border: 1px solid #f56c6c;
  color: #f56c6c;
  padding: 12px 0;
}
</style>
