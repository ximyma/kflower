<template>
  <div class="step3-form-generation">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📝 生成业务表单</span>
          <el-tag v-if="allSuccess" type="success">全部完成</el-tag>
          <el-tag v-else-if="hasError" type="danger">有失败项</el-tag>
          <el-tag v-else-if="generating" type="warning">生成中...</el-tag>
          <el-tag v-else type="info">待生成</el-tag>
        </div>
      </template>

      <!-- 生成进度 -->
      <div class="progress-section" v-if="generating || templates.length > 0">
        <div class="progress-stats">
          <el-statistic title="总表单数" :value="templates.length" />
          <el-statistic title="成功" :value="successCount">
            <template #suffix>
              <el-icon color="#67c23a"><CircleCheck /></el-icon>
            </template>
          </el-statistic>
          <el-statistic title="失败" :value="errorCount">
            <template #suffix>
              <el-icon v-if="errorCount > 0" color="#f56c6c"><CircleClose /></el-icon>
            </template>
          </el-statistic>
        </div>

        <el-progress 
          :percentage="progressPercent" 
          :status="progressStatus"
          :stroke-width="20"
          striped
          striped-flow
        />
      </div>

      <!-- 表单列表 -->
      <div class="templates-list" v-if="templates.length > 0">
        <h3>表单生成状态</h3>
        <el-table :data="templates" size="small" border>
          <el-table-column type="index" width="50" />
          <el-table-column prop="name" label="表单名称" width="200" />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column prop="fields?.length" label="字段数" width="80">
            <template #default="{ row }">
              {{ row.fields?.length || 0 }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row._status === 'pending'" type="info">待生成</el-tag>
              <el-tag v-else-if="row._status === 'generating'" type="warning">
                <el-icon class="is-loading"><Loading /></el-icon> 生成中
              </el-tag>
              <el-tag v-else-if="row._status === 'success'" type="success">成功</el-tag>
              <el-tag v-else-if="row._status === 'error'" type="danger">失败</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row, $index }">
              <el-button 
                v-if="row._status === 'error'" 
                size="small" 
                type="primary"
                @click="retryTemplate(row, $index)"
                :disabled="generating"
              >
                重试
              </el-button>
              <el-button 
                v-if="row._status === 'success'" 
                size="small"
                @click="previewTemplate(row)"
              >
                预览
              </el-button>
              <el-button 
                size="small" 
                text 
                type="danger"
                @click="removeTemplate($index)"
                :disabled="generating"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 错误详情 -->
        <div class="error-details" v-if="hasError">
          <el-alert 
            v-for="(tpl, idx) in errorTemplates" 
            :key="idx"
            :title="`${tpl.name}: ${tpl._error}`"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty v-else description="暂无表单，请返回上一步确认方案" />

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="$emit('prev')">上一步</el-button>
        <el-button 
          type="primary" 
          @click="$emit('generate-forms')"
          :loading="generating"
          :disabled="templates.length === 0 || allSuccess"
        >
          {{ allSuccess ? '已全部生成' : '开始生成表单' }}
        </el-button>
        <el-button 
          type="success" 
          @click="$emit('next')"
          :disabled="!hasSuccess"
        >
          下一步：配置菜单 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </el-card>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewVisible" title="表单预览" width="700px">
      <div v-if="previewTemplateData" class="preview-content">
        <h3>{{ previewTemplateData.name }}</h3>
        <p class="desc">{{ previewTemplateData.description }}</p>
        
        <el-divider />
        
        <div class="fields-preview">
          <div v-for="field in previewTemplateData.fields" :key="field.name" class="field-item">
            <label>{{ field.label }} ({{ field.name }})</label>
            <div class="field-component">
              <el-input v-if="field.type === 'text'" disabled placeholder="文本输入" />
              <el-input v-else-if="field.type === 'textarea'" type="textarea" disabled placeholder="多行文本" />
              <el-input-number v-else-if="field.type === 'number'" disabled />
              <el-date-picker v-else-if="field.type === 'date'" disabled style="width: 100%" />
              <el-select v-else-if="field.type === 'select'" disabled style="width: 100%">
                <el-option label="选项1" value="1" />
                <el-option label="选项2" value="2" />
              </el-select>
              <el-checkbox v-else-if="field.type === 'checkbox'" disabled>复选框</el-checkbox>
              <el-input v-else disabled placeholder="输入框" />
            </div>
            <el-tag v-if="field.required" size="small" type="danger">必填</el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Delete, ArrowRight, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const props = defineProps<{
  design: any
  templates: any[]
  generating: boolean
}>()

const emit = defineEmits(['prev', 'next', 'generate-forms', 'update-template'])

// 计算属性
const successCount = computed(() => props.templates.filter(t => t._status === 'success').length)
const errorCount = computed(() => props.templates.filter(t => t._status === 'error').length)
const allSuccess = computed(() => props.templates.length > 0 && props.templates.every(t => t._status === 'success'))
const hasSuccess = computed(() => props.templates.some(t => t._status === 'success'))
const hasError = computed(() => props.templates.some(t => t._status === 'error'))
const errorTemplates = computed(() => props.templates.filter(t => t._status === 'error'))

const progressPercent = computed(() => {
  if (props.templates.length === 0) return 0
  const completed = props.templates.filter(t => t._status === 'success' || t._status === 'error').length
  return Math.round((completed / props.templates.length) * 100)
})

const progressStatus = computed(() => {
  if (allSuccess.value) return 'success'
  if (hasError.value) return 'exception'
  return ''
})

// 预览
const previewVisible = ref(false)
const previewTemplateData = ref<any>(null)

function previewTemplate(row: any) {
  previewTemplateData.value = row
  previewVisible.value = true
}

function retryTemplate(row: any, index: number) {
  emit('update-template', index, { ...row, _status: 'pending', _error: null })
}

function removeTemplate(index: number) {
  const newTemplates = [...props.templates]
  newTemplates.splice(index, 1)
  // 通知父组件更新
  emit('update-template', -1, newTemplates)
}
</script>

<style scoped lang="scss">
.step3-form-generation {
  max-width: 1000px;
  margin: 0 auto;
}

.main-card {
  :deep(.el-card__header) {
    font-size: 16px;
    font-weight: 500;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-section {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
}

.templates-list {
  margin-bottom: 20px;

  h3 {
    margin: 0 0 16px;
    font-size: 16px;
  }
}

.error-details {
  margin-top: 16px;

  .el-alert {
    margin-bottom: 8px;
  }
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}

// 预览样式
.preview-content {
  h3 {
    margin: 0 0 8px;
  }

  .desc {
    color: var(--el-text-color-secondary);
    margin: 0 0 16px;
  }
}

.fields-preview {
  .field-item {
    margin-bottom: 16px;

    label {
      display: block;
      margin-bottom: 4px;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }

    .field-component {
      margin-bottom: 4px;
    }
  }
}
</style>
