<template>
  <div class="step2-design-confirm">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📋 确认设计方案</span>
          <div class="header-actions">
            <el-button text size="small" @click="$emit('regenerate')">
              <el-icon><RefreshLeft /></el-icon> 重新生成
            </el-button>
          </div>
        </div>
      </template>

      <!-- 应用基本信息 -->
      <div class="section">
        <h3>应用信息</h3>
        <el-form :model="localDesign" label-width="100px">
          <el-form-item label="应用名称">
            <el-input v-model="localDesign.app_name" />
          </el-form-item>
          <el-form-item label="应用描述">
            <el-input v-model="localDesign.description" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 表单模板列表 -->
      <div class="section">
        <h3>表单模板 ({{ localDesign.templates?.length || 0 }}个)</h3>
        <el-collapse v-model="activeTemplates">
          <el-collapse-item 
            v-for="(tpl, idx) in localDesign.templates" 
            :key="idx"
            :title="tpl.name"
            :name="idx"
          >
            <div class="template-edit">
              <el-form :model="tpl" label-width="80px" size="small">
                <el-form-item label="表单名称">
                  <el-input v-model="tpl.name" />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input v-model="tpl.description" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="分类">
                  <el-input v-model="tpl.category" />
                </el-form-item>
              </el-form>

              <h4>字段列表</h4>
              <el-table :data="tpl.fields" size="small" border>
                <el-table-column prop="name" label="字段名" width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.name" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="label" label="显示名称" width="150">
                  <template #default="{ row }">
                    <el-input v-model="row.label" size="small" />
                  </template>
                </el-table-column>
                <el-table-column prop="type" label="类型" width="120">
                  <template #default="{ row }">
                    <el-select v-model="row.type" size="small">
                      <el-option label="文本" value="text" />
                      <el-option label="多行文本" value="textarea" />
                      <el-option label="数字" value="number" />
                      <el-option label="日期" value="date" />
                      <el-option label="日期时间" value="datetime" />
                      <el-option label="下拉选择" value="select" />
                      <el-option label="复选框" value="checkbox" />
                      <el-option label="关联" value="relation" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column prop="required" label="必填" width="80">
                  <template #default="{ row }">
                    <el-checkbox v-model="row.required" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80">
                  <template #default="{ $index }">
                    <el-button type="danger" size="small" text @click="removeField(tpl, $index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <div class="field-actions">
                <el-button size="small" @click="addField(tpl)">
                  <el-icon><Plus /></el-icon> 添加字段
                </el-button>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>

        <div class="template-actions">
          <el-button @click="addTemplate">
            <el-icon><Plus /></el-icon> 添加表单
          </el-button>
        </div>
      </div>

      <!-- 关系配置 -->
      <div class="section" v-if="localDesign.relations?.length">
        <h3>表单关系</h3>
        <el-table :data="localDesign.relations" size="small" border>
          <el-table-column prop="from_template" label="源表单" />
          <el-table-column prop="to_template" label="目标表单" />
          <el-table-column prop="relation_type" label="关系类型">
            <template #default="{ row }">
              <el-tag size="small">{{ row.relation_type === 'belongs_to' ? '属于' : '拥有' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="field" label="关联字段" />
        </el-table>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="$emit('prev')">上一步</el-button>
        <el-button type="primary" @click="$emit('next')">
          确认方案，下一步 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus, Delete, ArrowRight, RefreshLeft } from '@element-plus/icons-vue'

const props = defineProps<{
  design: any
}>()

const emit = defineEmits(['update:design', 'prev', 'next', 'regenerate'])

const localDesign = computed({
  get: () => props.design,
  set: (val) => emit('update:design', val)
})

const activeTemplates = ref([0])

function addField(tpl: any) {
  if (!tpl.fields) tpl.fields = []
  tpl.fields.push({
    name: `field_${tpl.fields.length + 1}`,
    label: `字段${tpl.fields.length + 1}`,
    type: 'text',
    required: false
  })
}

function removeField(tpl: any, idx: number) {
  tpl.fields.splice(idx, 1)
}

function addTemplate() {
  if (!localDesign.value.templates) localDesign.value.templates = []
  localDesign.value.templates.push({
    name: `新表单${localDesign.value.templates.length + 1}`,
    description: '',
    category: '业务表单',
    fields: []
  })
  activeTemplates.value = [localDesign.value.templates.length - 1]
}
</script>

<style scoped lang="scss">
.step2-design-confirm {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.section {
  margin-bottom: 30px;

  h3 {
    margin: 0 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-light);
    color: var(--el-text-color-primary);
    font-size: 16px;
  }
}

.template-edit {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;

  h4 {
    margin: 16px 0 8px;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.field-actions {
  margin-top: 12px;
}

.template-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>
