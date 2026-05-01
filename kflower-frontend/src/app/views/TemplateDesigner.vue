<template>
  <div class="mobile-template-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </div>
      <div class="header-title">{{ templateName || '新建模板' }}</div>
      <div class="header-right">
        <el-button type="primary" size="small" @click="saveTemplate" :loading="saving">
          保存
        </el-button>
      </div>
    </div>

    <!-- 模板信息 -->
    <div class="template-info-section">
      <el-input v-model="templateName" placeholder="模板名称" size="large" />
      <div class="category-select">
        <el-select v-model="templateCategory" placeholder="选择分类" style="width: 100%">
          <el-option label="办公表单" value="office" />
          <el-option label="业务流程" value="business" />
          <el-option label="数据采集" value="data" />
          <el-option label="调查问卷" value="survey" />
          <el-option label="其他" value="other" />
        </el-select>
      </div>
    </div>

    <!-- 字段列表 -->
    <div class="fields-section">
      <div class="section-header">
        <span class="section-title">字段管理</span>
        <span class="field-count">{{ fields.length }} 个字段</span>
      </div>

      <div v-if="fields.length === 0" class="empty-fields">
        <el-icon :size="48" color="#c0c4cc"><List /></el-icon>
        <p>暂无字段</p>
        <p class="tip">点击下方按钮添加字段</p>
      </div>

      <div v-else class="field-list">
        <div v-for="(field, index) in fields" :key="index" class="field-item">
          <div class="field-drag">
            <el-icon><Rank /></el-icon>
          </div>
          <div class="field-info">
            <div class="field-name">{{ field.name }}</div>
            <div class="field-meta">
              <el-tag size="small">{{ fieldTypeLabels[field.type] || field.type }}</el-tag>
              <span v-if="field.required" class="required-tag">必填</span>
            </div>
          </div>
          <div class="field-actions">
            <el-icon @click="editField(index)"><Edit /></el-icon>
            <el-icon @click="deleteField(index)"><Delete /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加字段按钮 -->
    <div class="add-field-section">
      <el-button type="primary" plain style="width: 100%" @click="showAddFieldDialog">
        <el-icon><Plus /></el-icon> 添加字段
      </el-button>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-actions">
      <el-button @click="previewTemplate">
        <el-icon><View /></el-icon> 预览
      </el-button>
      <el-button type="success" @click="publishTemplate" :loading="publishing">
        <el-icon><Promotion /></el-icon> {{ templateData?.is_published ? '已发布' : '发布' }}
      </el-button>
    </div>

    <!-- 添加/编辑字段对话框 -->
    <el-dialog
      v-model="showFieldDialog"
      :title="editingFieldIndex >= 0 ? '编辑字段' : '添加字段'"
      width="90%"
      :close-on-click-modal="false"
    >
      <el-form :model="fieldForm" label-position="top">
        <el-form-item label="字段名称" required>
          <el-input v-model="fieldForm.name" placeholder="请输入字段名称" />
        </el-form-item>
        <el-form-item label="字段类型" required>
          <el-select v-model="fieldForm.type" placeholder="选择字段类型" style="width: 100%">
            <el-option
              v-for="(label, value) in fieldTypeLabels"
              :key="value"
              :label="label"
              :value="value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="占位提示">
          <el-input v-model="fieldForm.placeholder" placeholder="请输入占位提示" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="fieldForm.required">设为必填字段</el-checkbox>
        </el-form-item>
        <el-form-item label="选项（多选/单选时填写）">
          <el-input
            v-model="fieldForm.options"
            type="textarea"
            :rows="2"
            placeholder="选项之间用逗号分隔，如：选项1,选项2,选项3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFieldDialog = false">取消</el-button>
        <el-button type="primary" @click="saveField">确定</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreview" title="模板预览" width="95%" fullscreen>
      <div class="preview-form">
        <div v-for="(field, index) in fields" :key="index" class="preview-field">
          <label>
            {{ field.name }}
            <span v-if="field.required" class="required-star">*</span>
          </label>
          <el-input
            v-if="field.type === 'text'"
            :placeholder="field.placeholder || '请输入'"
            disabled
          />
          <el-input
            v-else-if="field.type === 'textarea'"
            type="textarea"
            :placeholder="field.placeholder || '请输入'"
            disabled
          />
          <el-input
            v-else-if="field.type === 'number'"
            type="number"
            :placeholder="field.placeholder || '请输入数字'"
            disabled
          />
          <el-select
            v-else-if="field.type === 'select'"
            :placeholder="field.placeholder || '请选择'"
            disabled
            style="width: 100%"
          >
            <el-option
              v-for="opt in (field.options || '').split(',')"
              :key="opt"
              :label="opt.trim()"
              :value="opt.trim()"
            />
          </el-select>
          <el-radio-group v-else-if="field.type === 'radio'" disabled>
            <el-radio
              v-for="opt in (field.options || '').split(',')"
              :key="opt"
              :label="opt.trim()"
            />
          </el-radio-group>
          <el-checkbox-group v-else-if="field.type === 'checkbox'" disabled>
            <el-checkbox
              v-for="opt in (field.options || '').split(',')"
              :key="opt"
              :label="opt.trim()"
            />
          </el-checkbox-group>
          <el-date-picker
            v-else-if="field.type === 'date'"
            type="date"
            placeholder="选择日期"
            disabled
            style="width: 100%"
          />
          <el-switch v-else-if="field.type === 'switch'" disabled />
          <el-input v-else :placeholder="field.placeholder || '请输入'" disabled />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, Edit, Delete, List, Rank, View, Promotion } from '@element-plus/icons-vue'
import { templateAPI } from '../../common/api'

const route = useRoute()
const router = useRouter()

const templateId = computed(() => route.params.id ? Number(route.params.id) : null)
const templateName = ref('')
const templateCategory = ref('office')
const templateData = ref<any>(null)
const fields = ref<any[]>([])
const saving = ref(false)
const publishing = ref(false)
const showFieldDialog = ref(false)
const showPreview = ref(false)
const editingFieldIndex = ref(-1)

const fieldForm = ref({
  name: '',
  type: 'text',
  placeholder: '',
  required: false,
  options: ''
})

const fieldTypeLabels: Record<string, string> = {
  text: '单行文本',
  textarea: '多行文本',
  number: '数字',
  select: '下拉选择',
  radio: '单选',
  checkbox: '多选',
  date: '日期',
  datetime: '日期时间',
  switch: '开关',
  image: '图片上传',
  file: '文件上传',
  money: '金额',
  phone: '手机号',
  email: '邮箱'
}

function goBack() {
  router.back()
}

async function loadTemplate() {
  if (!templateId.value) return

  try {
    const res = await templateAPI.get(templateId.value)
    templateData.value = res
    templateName.value = res.name || ''
    templateCategory.value = res.category || 'office'

    // 解析 modules 获取字段
    if (res.modules && res.modules.length > 0 && res.modules[0].fields) {
      fields.value = res.modules[0].fields
    }
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

async function saveTemplate() {
  if (!templateName.value.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }

  saving.value = true
  try {
    const data = {
      name: templateName.value,
      category: templateCategory.value,
      modules: [{
        name: '主表单',
        fields: fields.value
      }]
    }

    if (templateId.value) {
      await templateAPI.update(templateId.value, data)
      ElMessage.success('保存成功')
    } else {
      const res = await templateAPI.create(data)
      ElMessage.success('创建成功')
      // 跳转到新创建的模板
      router.replace(`/app/template-designer/${res.id}`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function publishTemplate() {
  if (!templateId.value) {
    ElMessage.warning('请先保存模板')
    return
  }

  publishing.value = true
  try {
    await templateAPI.publish(templateId.value)
    templateData.value.is_published = true
    ElMessage.success('发布成功')
  } catch (error: any) {
    ElMessage.error(error.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

function previewTemplate() {
  if (fields.value.length === 0) {
    ElMessage.warning('请先添加字段')
    return
  }
  showPreview.value = true
}

function showAddFieldDialog() {
  editingFieldIndex.value = -1
  fieldForm.value = {
    name: '',
    type: 'text',
    placeholder: '',
    required: false,
    options: ''
  }
  showFieldDialog.value = true
}

function editField(index: number) {
  editingFieldIndex.value = index
  const field = fields.value[index]
  fieldForm.value = {
    name: field.name || '',
    type: field.type || 'text',
    placeholder: field.placeholder || '',
    required: field.required || false,
    options: field.options || ''
  }
  showFieldDialog.value = true
}

function deleteField(index: number) {
  fields.value.splice(index, 1)
  ElMessage.success('已删除字段')
}

function saveField() {
  if (!fieldForm.value.name.trim()) {
    ElMessage.warning('请输入字段名称')
    return
  }

  const fieldData = {
    name: fieldForm.value.name.trim(),
    type: fieldForm.value.type,
    placeholder: fieldForm.value.placeholder,
    required: fieldForm.value.required,
    options: fieldForm.value.options,
    // 生成字段编码
    code: fieldForm.value.name.trim().replace(/\s+/g, '_').toLowerCase()
  }

  if (editingFieldIndex.value >= 0) {
    fields.value[editingFieldIndex.value] = fieldData
    ElMessage.success('字段已更新')
  } else {
    fields.value.push(fieldData)
    ElMessage.success('字段已添加')
  }

  showFieldDialog.value = false
}

onMounted(() => {
  loadTemplate()
})
</script>

<style scoped>
.mobile-template-designer {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 120px;
}

.designer-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409EFF;
  cursor: pointer;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right {
  display: flex;
  gap: 8px;
}

.template-info-section {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
}

.category-select {
  margin-top: 12px;
}

.fields-section {
  background: white;
  padding: 16px;
  min-height: 300px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
}

.field-count {
  font-size: 12px;
  color: #909399;
}

.empty-fields {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-fields p {
  margin: 12px 0 0;
}

.empty-fields .tip {
  font-size: 12px;
  color: #c0c4cc;
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #eee;
}

.field-drag {
  color: #c0c4cc;
  cursor: grab;
}

.field-info {
  flex: 1;
}

.field-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.field-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.required-tag {
  font-size: 11px;
  color: #F56C6C;
}

.field-actions {
  display: flex;
  gap: 12px;
  color: #909399;
}

.field-actions .el-icon {
  cursor: pointer;
  font-size: 18px;
}

.field-actions .el-icon:hover {
  color: #409EFF;
}

.add-field-section {
  padding: 16px;
  background: white;
  margin-top: 12px;
}

.bottom-actions {
  position: fixed;
  bottom: 60px;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 99;
}

.bottom-actions .el-button {
  flex: 1;
}

.preview-form {
  padding: 12px;
}

.preview-field {
  margin-bottom: 20px;
}

.preview-field label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.required-star {
  color: #F56C6C;
}

.preview-field :deep(.el-input),
.preview-field :deep(.el-select),
.preview-field :deep(.el-textarea) {
  width: 100%;
}
</style>
