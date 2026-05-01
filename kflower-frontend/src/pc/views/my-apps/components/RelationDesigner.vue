<template>
  <div class="relation-designer">
    <div class="toolbar">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建关系
      </el-button>
      <el-alert
        title="表单关系用于建立表单之间的关联，如：客户-订单、订单-明细等"
        type="info"
        :closable="false"
        style="flex: 1; margin-left: 16px;"
      />
    </div>

    <!-- 关系列表 -->
    <el-table :data="relations" v-loading="loading" border stripe>
      <el-table-column prop="from_template_name" label="源表单" width="180" />
      <el-table-column prop="from_field_name" label="关联字段" width="150" />
      <el-table-column label="关系类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getRelationTypeTag(row.relation_type)">
            {{ getRelationTypeLabel(row.relation_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="to_template_name" label="目标表单" width="180" />
      <el-table-column prop="display_field" label="显示字段" width="150" />
      <el-table-column label="自动填充" width="150">
        <template #default="{ row }">
          <template v-if="row.auto_fill_fields && row.auto_fill_fields.length > 0">
            <el-tag v-for="(mapping, idx) in row.auto_fill_fields" :key="idx" size="small" style="margin: 2px;">
              {{ mapping.from }} -> {{ mapping.to }}
            </el-tag>
          </template>
          <span v-else style="color: var(--el-text-color-secondary);">无</span>
        </template>
      </el-table-column>
      <el-table-column label="删除策略" width="120">
        <template #default="{ row }">
          {{ row.on_delete === 'cascade' ? '级联删除' : '置空' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" link @click="deleteRelation(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建关系对话框 -->
    <el-dialog v-model="dialogVisible" title="新建表单关系" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="源表单" required>
          <el-select v-model="form.from_template_id" placeholder="选择源表单" style="width: 100%">
            <el-option
              v-for="tpl in templates"
              :key="tpl.id"
              :label="tpl.name"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联字段" required>
          <el-input v-model="form.from_field_name" placeholder="如：customer_id" />
          <span class="form-tip">存储目标表单ID的字段名称</span>
        </el-form-item>
        
        <el-form-item label="关系类型" required>
          <el-select v-model="form.relation_type" placeholder="选择关系类型" style="width: 100%">
            <el-option label="属于 (belongs_to)" value="belongs_to">
              <span>属于</span>
              <span class="option-desc"> - 多对一，如：订单属于客户</span>
            </el-option>
            <el-option label="拥有 (has_many)" value="has_many">
              <span>拥有</span>
              <span class="option-desc"> - 一对多，如：客户拥有多个订单</span>
            </el-option>
            <el-option label="多对多 (many_to_many)" value="many_to_many">
              <span>多对多</span>
              <span class="option-desc"> - 如：产品属于多个分类</span>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标表单" required>
          <el-select v-model="form.to_template_id" placeholder="选择目标表单" style="width: 100%">
            <el-option
              v-for="tpl in templates"
              :key="tpl.id"
              :label="tpl.name"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="显示字段">
          <el-input v-model="form.display_field" placeholder="如：name" />
          <span class="form-tip">关联后在列表中显示的字段</span>
        </el-form-item>
        
        <el-form-item label="删除策略">
          <el-radio-group v-model="form.on_delete">
            <el-radio label="set_null">置空</el-radio>
            <el-radio label="cascade">级联删除</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="反向名称">
          <el-input v-model="form.reverse_name" placeholder="如：orders" />
          <span class="form-tip">从目标表单查看时的字段名</span>
        </el-form-item>

        <!-- 自动填充字段映射 -->
        <el-divider content-position="left">自动填充配置</el-divider>
        <el-alert
          title="选择关联记录时，自动将目标表单的字段值填充到源表单的指定字段"
          type="info"
          :closable="false"
          style="margin-bottom: 12px;"
        />
        <div v-for="(mapping, idx) in form.auto_fill_fields" :key="idx" class="mapping-row">
          <el-select v-model="mapping.from" placeholder="目标字段" style="width: 40%;" :disabled="!form.to_template_id">
            <el-option v-for="f in toTemplateFields" :key="f" :label="f" :value="f" />
          </el-select>
          <span class="mapping-arrow">-></span>
          <el-select v-model="mapping.to" placeholder="源表单字段" style="width: 40%;" :disabled="!form.from_template_id">
            <el-option v-for="f in fromTemplateFields" :key="f" :label="f" :value="f" />
          </el-select>
          <el-button type="danger" link @click="form.auto_fill_fields.splice(idx, 1)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <el-button type="primary" link @click="addAutoFillMapping" :disabled="!form.from_template_id || !form.to_template_id">
          <el-icon><Plus /></el-icon> 添加字段映射
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRelation" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'
import { templateAPI } from '@/common/api/index'

const props = defineProps<{
  appId: number
}>()

const relations = ref<any[]>([])
const templates = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)

const form = ref({
  from_template_id: null as number | null,
  from_field_name: '',
  to_template_id: null as number | null,
  relation_type: 'belongs_to',
  display_field: 'name',
  on_delete: 'set_null',
  reverse_name: '',
  auto_fill_fields: [] as Array<{from: string, to: string}>
})

function getRelationTypeLabel(type: string) {
  const labels: Record<string, string> = {
    belongs_to: '属于',
    has_many: '拥有',
    many_to_many: '多对多'
  }
  return labels[type] || type
}

function getRelationTypeTag(type: string) {
  const tags: Record<string, string> = {
    belongs_to: 'primary',
    has_many: 'success',
    many_to_many: 'warning'
  }
  return tags[type] || 'info'
}

async function loadRelations() {
  loading.value = true
  try {
    const res = await appAPI.listRelations(props.appId)
    relations.value = res.data || res
    
    // 补充模板名称
    for (const rel of relations.value) {
      const fromTpl = templates.value.find(t => t.id === rel.from_template_id)
      const toTpl = templates.value.find(t => t.id === rel.to_template_id)
      rel.from_template_name = fromTpl?.name || '未知'
      rel.to_template_name = toTpl?.name || '未知'
    }
  } finally {
    loading.value = false
  }
}

async function loadTemplates() {
  const res = await templateAPI.list({ limit: 100 })
  templates.value = res.data || res
}

function openCreateDialog() {
  form.value = {
    from_template_id: null,
    from_field_name: '',
    to_template_id: null,
    relation_type: 'belongs_to',
    display_field: 'name',
    on_delete: 'set_null',
    reverse_name: ''
  }
  dialogVisible.value = true
}

async function saveRelation() {
  if (!form.value.from_template_id || !form.value.to_template_id) {
    ElMessage.warning('请选择源表单和目标表单')
    return
  }
  if (!form.value.from_field_name) {
    ElMessage.warning('请输入关联字段名称')
    return
  }

  saving.value = true
  try {
    await appAPI.addRelation(props.appId, form.value)
    ElMessage.success('关系创建成功')
    dialogVisible.value = false
    await loadRelations()
  } catch (e: any) {
    ElMessage.error('创建失败：' + (e.message || ''))
  } finally {
    saving.value = false
  }
}

async function deleteRelation(row: any) {
  try {
    await ElMessageBox.confirm('确定删除此关系吗？', '确认删除', { type: 'warning' })
    await appAPI.deleteRelation(row.id)
    ElMessage.success('删除成功')
    await loadRelations()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.message || ''))
    }
  }
}

// 获取目标模板字段列表
const toTemplateFields = ref<string[]>([])
const fromTemplateFields = ref<string[]>([])

// 当选择模板后，加载字段列表
async function loadTemplateFields(templateId: number | null, target: 'from' | 'to') {
  if (!templateId) {
    if (target === 'from') fromTemplateFields.value = []
    else toTemplateFields.value = []
    return
  }
  try {
    const res: any = await templateAPI.get(templateId)
    const fields = (res.fields || res.data?.fields || []).map((f: any) => f.name || f.field_name || f.label).filter(Boolean)
    if (target === 'from') fromTemplateFields.value = fields
    else toTemplateFields.value = fields
  } catch {
    // ignore
  }
}

// 添加字段映射
function addAutoFillMapping() {
  form.value.auto_fill_fields.push({ from: '', to: '' })
}

// 监听模板选择变化，加载字段
import { watch } from 'vue'
watch(() => form.value.to_template_id, (val) => loadTemplateFields(val, 'to'))
watch(() => form.value.from_template_id, (val) => loadTemplateFields(val, 'from'))

onMounted(async () => {
  await loadTemplates()
  await loadRelations()
})
</script>

<style scoped>
.relation-designer {
  padding: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.option-desc {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.mapping-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.mapping-arrow {
  color: var(--el-text-color-secondary);
  font-weight: bold;
}
</style>
