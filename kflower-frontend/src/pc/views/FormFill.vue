<template>
  <div class="form-fill-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 错误状态 -->
    <el-result v-else-if="error" icon="error" :title="error" sub-title="请检查链接是否正确或联系管理员">
      <template #extra>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </template>
    </el-result>

    <!-- 表单内容 -->
    <template v-else>
      <!-- 表单头部 -->
      <div class="form-header">
        <h1 class="form-title">{{ template.name }}</h1>
        <p v-if="template.description" class="form-desc">{{ template.description }}</p>
      </div>

      <!-- 表单主体 -->
      <el-card class="form-card">
        <el-form ref="formRef" :model="formData" :rules="formRules" label-position="top">
          <div v-for="(mod, modIdx) in modules" :key="modIdx">
            <h3 v-if="modules.length > 1" class="module-title">{{ mod.label || mod.name }}</h3>
            <el-form-item
              v-for="field in mod.fields"
              :key="field.name"
              :label="field.label + (field.required ? ' *' : '')"
              :prop="field.name"
              :rules="buildFieldRules(field)"
            >
              <!-- 文本输入 -->
              <el-input
                v-if="['text','email','phone','url'].includes(field.type)"
                v-model="formData[field.name]"
                :placeholder="field.placeholder || '请输入' + field.label"
                :maxlength="field.maxLength"
                show-word-limit
              />

              <!-- 多行文本 -->
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="formData[field.name]"
                type="textarea"
                :rows="4"
                :placeholder="field.placeholder || '请输入' + field.label"
                :maxlength="field.maxLength"
                show-word-limit
              />

              <!-- 数字 -->
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="formData[field.name]"
                style="width:100%"
                :min="field.min"
                :max="field.max"
                :placeholder="field.placeholder || '请输入' + field.label"
              />

              <!-- 日期 -->
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="formData[field.name]"
                type="date"
                style="width:100%"
                :placeholder="field.placeholder || '请选择日期'"
                value-format="YYYY-MM-DD"
              />

              <!-- 日期时间 -->
              <el-date-picker
                v-else-if="field.type === 'datetime'"
                v-model="formData[field.name]"
                type="datetime"
                style="width:100%"
                :placeholder="field.placeholder || '请选择日期时间'"
                value-format="YYYY-MM-DD HH:mm:ss"
              />

              <!-- 时间 -->
              <el-time-picker
                v-else-if="field.type === 'time'"
                v-model="formData[field.name]"
                style="width:100%"
                :placeholder="field.placeholder || '请选择时间'"
                value-format="HH:mm:ss"
              />

              <!-- 日期范围 -->
              <el-date-picker
                v-else-if="field.type === 'daterange'"
                v-model="formData[field.name]"
                type="daterange"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width:100%"
                value-format="YYYY-MM-DD"
              />

              <!-- 下拉选择 -->
              <el-select
                v-else-if="field.type === 'select'"
                v-model="formData[field.name]"
                style="width:100%"
                :placeholder="field.placeholder || '请选择'"
                :multiple="field.multiple"
                collapse-tags
              >
                <el-option
                  v-for="opt in (field.options || [])"
                  :key="opt"
                  :label="opt"
                  :value="opt"
                />
              </el-select>

              <!-- 单选 -->
              <el-radio-group v-else-if="field.type === 'radio'" v-model="formData[field.name]">
                <el-radio v-for="opt in (field.options || [])" :key="opt" :label="opt">{{ opt }}</el-radio>
              </el-radio-group>

              <!-- 多选 -->
              <el-checkbox-group v-else-if="field.type === 'checkbox'" v-model="formData[field.name]">
                <el-checkbox v-for="opt in (field.options || [])" :key="opt" :label="opt">{{ opt }}</el-checkbox>
              </el-checkbox-group>

              <!-- 开关 -->
              <el-switch
                v-else-if="field.type === 'switch'"
                v-model="formData[field.name]"
                :active-text="field.activeText || '是'"
                :inactive-text="field.inactiveText || '否'"
              />

              <!-- 评分 -->
              <el-rate
                v-else-if="field.type === 'rate'"
                v-model="formData[field.name]"
                :max="field.max || 5"
                show-score
              />

              <!-- 滑块 -->
              <el-slider
                v-else-if="field.type === 'slider'"
                v-model="formData[field.name]"
                :min="field.min || 0"
                :max="field.max || 100"
                show-input
              />

              <!-- 邮箱 -->
              <el-input
                v-else-if="field.type === 'email'"
                v-model="formData[field.name]"
                type="email"
                :placeholder="field.placeholder || '请输入邮箱'"
              />

              <!-- 手机号 -->
              <el-input
                v-else-if="field.type === 'phone'"
                v-model="formData[field.name]"
                :placeholder="field.placeholder || '请输入手机号'"
              />

              <!-- 网址 -->
              <el-input
                v-else-if="field.type === 'url'"
                v-model="formData[field.name]"
                :placeholder="field.placeholder || '请输入网址'"
              />

              <!-- 密码 -->
              <el-input
                v-else-if="field.type === 'password'"
                v-model="formData[field.name]"
                type="password"
                show-password
                :placeholder="field.placeholder || '请输入密码'"
              />

              <!-- 金额 -->
              <el-input
                v-else-if="field.type === 'money'"
                v-model="formData[field.name]"
                :placeholder="field.placeholder || '请输入金额'"
              >
                <template #prepend>¥</template>
              </el-input>

              <!-- 颜色 -->
              <el-color-picker v-else-if="field.type === 'color'" v-model="formData[field.name]" />

              <!-- 文件上传 -->
              <el-upload
                v-else-if="field.type === 'file' || field.type === 'upload'"
                v-model:file-list="fileList[field.name]"
                :action="uploadUrl"
                :headers="uploadHeaders"
                :limit="field.limit || 5"
                :before-upload="(file) => beforeUpload(file, field)"
              >
                <el-button type="primary"><el-icon><Upload /></el-icon> 点击上传</el-button>
                <template #tip>
                  <div class="el-upload__tip">支持常见文件格式，单个文件不超过{{ field.maxSize || 10 }}MB</div>
                </template>
              </el-upload>

              <!-- 图片上传 -->
              <el-upload
                v-else-if="field.type === 'image'"
                v-model:file-list="fileList[field.name]"
                :action="uploadUrl"
                :headers="uploadHeaders"
                list-type="picture-card"
                :limit="field.limit || 3"
                accept="image/*"
                :before-upload="(file) => beforeUpload(file, field)"
              >
                <el-icon><Plus /></el-icon>
              </el-upload>

              <!-- 标签 -->
              <el-select
                v-else-if="field.type === 'tags'"
                v-model="formData[field.name]"
                multiple
                filterable
                allow-create
                default-first-option
                style="width:100%"
                :placeholder="field.placeholder || '输入标签后按回车'"
              />

              <!-- 分割线 -->
              <el-divider v-else-if="field.type === 'divider'" />

              <!-- 标题 -->
              <h4 v-else-if="field.type === 'title' || field.type === 'heading'" class="field-title">{{ field.label }}</h4>

              <!-- 说明文字 -->
              <p v-else-if="field.type === 'description'" class="field-desc">{{ field.content || field.label }}</p>

              <!-- 默认文本 -->
              <el-input
                v-else
                v-model="formData[field.name]"
                :placeholder="field.placeholder || '请输入' + field.label"
              />
            </el-form-item>
          </div>
        </el-form>

        <!-- 提交按钮 -->
        <div class="form-actions">
          <el-button type="primary" size="large" :loading="submitting" @click="submitForm">
            <el-icon><Check /></el-icon> 提交
          </el-button>
          <el-button size="large" @click="resetForm">重置</el-button>
        </div>
      </el-card>

      <!-- 底部信息 -->
      <div class="form-footer">
        <p>Powered by Kflower</p>
      </div>
    </template>

    <!-- 提交成功 -->
    <el-dialog v-model="showSuccess" title="提交成功" width="400px" :close-on-click-modal="false" :show-close="false">
      <el-result icon="success" title="提交成功" sub-title="您的数据已成功保存">
        <template #extra>
          <el-button type="primary" @click="goToDataList">查看数据</el-button>
          <el-button @click="fillAgain">继续填写</el-button>
        </template>
      </el-result>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Plus, Check } from '@element-plus/icons-vue'
import { templateAPI } from '../../common/api'
import { useUserStore } from '../../common/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态
const loading = ref(true)
const error = ref('')
const template = ref<any>({})
const modules = ref<any[]>([])
const formData = reactive<Record<string, any>>({})
const formRef = ref<any>(null)
const submitting = ref(false)
const showSuccess = ref(false)
const fileList = reactive<Record<string, any[]>>({})

// 上传配置
const uploadUrl = computed(() => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${baseURL}/upload`
})
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// 表单验证规则
const formRules = computed(() => {
  const rules: Record<string, any[]> = {}
  modules.value.forEach(mod => {
    mod.fields.forEach((field: any) => {
      if (field.required) {
        rules[field.name] = [
          { required: true, message: `请填写${field.label}`, trigger: 'change' }
        ]
      }
    })
  })
  return rules
})

// 构建字段验证规则
function buildFieldRules(field: any) {
  const rules: any[] = []
  if (field.required) {
    rules.push({ required: true, message: `请填写${field.label}`, trigger: 'change' })
  }
  if (field.type === 'email') {
    rules.push({ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' })
  }
  if (field.type === 'phone') {
    rules.push({
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号格式',
      trigger: 'blur'
    })
  }
  if (field.type === 'url') {
    rules.push({ type: 'url', message: '请输入正确的网址格式', trigger: 'blur' })
  }
  return rules
}

// 加载模板
async function loadTemplate() {
  const templateId = route.params.id as string
  if (!templateId) {
    error.value = '模板ID不能为空'
    loading.value = false
    return
  }

  try {
    const res: any = await templateAPI.get(parseInt(templateId))
    // 后端返回的直接是数据对象
    if (res.id) {
      template.value = res
      modules.value = res.modules || []

      // 初始化表单数据
      modules.value.forEach(mod => {
        mod.fields.forEach((field: any) => {
          // 根据类型设置默认值
          if (field.type === 'checkbox' || field.type === 'tags' || (field.type === 'select' && field.multiple)) {
            formData[field.name] = field.defaultValue || []
          } else if (field.type === 'switch') {
            formData[field.name] = field.defaultValue !== undefined ? field.defaultValue : false
          } else if (field.type === 'number') {
            formData[field.name] = field.defaultValue !== undefined ? Number(field.defaultValue) : undefined
          } else {
            formData[field.name] = field.defaultValue || ''
          }

          // 初始化文件列表
          if (field.type === 'file' || field.type === 'upload' || field.type === 'image') {
            fileList[field.name] = []
          }
        })
      })
    } else {
      error.value = res.message || '加载模板失败'
    }
  } catch (e: any) {
    error.value = e.message || '加载模板失败'
  } finally {
    loading.value = false
  }
}

// 上传前检查
function beforeUpload(file: File, field: any) {
  const maxSize = (field.maxSize || 10) * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`文件大小不能超过${field.maxSize || 10}MB`)
    return false
  }
  return true
}

// 提交表单
async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const templateId = route.params.id as string

    // 处理文件上传后的数据
    const submitData = { ...formData }
    Object.keys(fileList).forEach(key => {
      if (fileList[key] && fileList[key].length > 0) {
        submitData[key] = fileList[key].map((f: any) => f.response?.url || f.url).filter(Boolean)
      }
    })

    const res: any = await templateAPI.submitData(parseInt(templateId), { data: submitData })
    // 后端返回的是 TemplateDataResponse，直接包含 id 等字段
    if (res.id) {
      showSuccess.value = true
    } else {
      ElMessage.error(res.message || '提交失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
function resetForm() {
  ElMessageBox.confirm('确定要重置表单吗？已填写的内容将清空', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    formRef.value?.resetFields()
    // 重置文件列表
    Object.keys(fileList).forEach(key => {
      fileList[key] = []
    })
    ElMessage.success('表单已重置')
  }).catch(() => {})
}

// 跳转到数据列表
function goToDataList() {
  const templateId = route.params.id as string
  router.push(`/form/${templateId}/data`)
}

// 继续填写
function fillAgain() {
  showSuccess.value = false
  formRef.value?.resetFields()
  Object.keys(fileList).forEach(key => {
    fileList[key] = []
  })
}

onMounted(() => {
  loadTemplate()
})
</script>

<style scoped lang="scss">
.form-fill-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 40px 20px;
}

.loading-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
}

.form-header {
  text-align: center;
  margin-bottom: 30px;

  .form-title {
    font-size: 28px;
    font-weight: 600;
    color: #303133;
    margin: 0 0 12px;
  }

  .form-desc {
    font-size: 14px;
    color: #606266;
    margin: 0;
  }
}

.form-card {
  max-width: 800px;
  margin: 0 auto;
  border-radius: 8px;

  :deep(.el-card__body) {
    padding: 40px;
  }
}

.module-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;

  &:first-child {
    margin-top: 0;
  }
}

.field-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 16px 0 8px;
}

.field-desc {
  font-size: 14px;
  color: #606266;
  margin: 8px 0;
  line-height: 1.6;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.form-footer {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  color: #909399;
  font-size: 12px;
}

// 响应式
@media (max-width: 768px) {
  .form-fill-page {
    padding: 20px 16px;
  }

  .form-card {
    :deep(.el-card__body) {
      padding: 24px;
    }
  }

  .form-title {
    font-size: 22px;
  }
}
</style>
