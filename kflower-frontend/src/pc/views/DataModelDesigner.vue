<template>
  <div class="model-designer-page" v-loading="loading">
    <!-- 顶部操作栏 -->
    <div class="designer-header">
      <div class="header-left">
        <el-button text @click="$router.push('/data-modeling')">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <el-divider direction="vertical" />
        <h3 v-if="model">{{ model.title }}</h3>
        <el-tag v-if="model" size="small" type="info" style="font-family:monospace">{{ model.name }}</el-tag>
        <el-tag v-if="model?.is_created" type="success" size="small">已建表</el-tag>
        <el-tag v-if="model?.template_id" type="warning" size="small">已生成模板</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="doCreateTable" :disabled="!model || model.is_created" type="success">
          <el-icon><Grid /></el-icon> 建表
        </el-button>
        <el-button @click="doSyncTable" :disabled="!model || !model.is_created" type="info">
          <el-icon><Refresh /></el-icon> 同步表
        </el-button>
        <el-button @click="doGenerateTemplate" :disabled="!model || !model.is_created" type="warning">
          <el-icon><Document /></el-icon> 生成模板
        </el-button>
      </div>
    </div>

    <!-- 模型基本信息编辑 -->
    <div class="model-info-section" v-if="model">
      <el-form inline size="small">
        <el-form-item label="显示名">
          <el-input v-model="model.title" style="width:160px" @change="updateModelInfo" />
        </el-form-item>
        <el-form-item label="表名">
          <el-input :model-value="model.name" disabled style="width:160px" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="model.description" style="width:280px" placeholder="可选" @change="updateModelInfo" />
        </el-form-item>
        <el-form-item>
          <el-tag :type="getSourceTagType(model.source_type)">{{ getSourceLabel(model.source_type) }}</el-tag>
        </el-form-item>
      </el-form>
    </div>

    <!-- 主内容区 -->
    <div class="designer-body" v-if="model">
      <!-- 左侧：字段列表 -->
      <div class="fields-panel">
        <div class="panel-header">
          <h4>字段列表 ({{ fields.length }})</h4>
          <el-button type="primary" size="small" @click="openAddFieldDialog">
            <el-icon><Plus /></el-icon> 添加字段
          </el-button>
        </div>

        <div class="fields-list">
          <div
            v-for="(f, idx) in fields"
            :key="f.id"
            class="field-item"
            :class="{ active: selectedFieldId === f.id }"
            @click="selectField(f)"
          >
            <div class="field-drag">
              <el-icon><Rank /></el-icon>
            </div>
            <div class="field-info">
              <div class="field-title-row">
                <span class="field-title">{{ f.title }}</span>
                <el-tag v-if="f.is_primary_key" size="small" type="danger">PK</el-tag>
                <el-tag v-if="f.is_required" size="small" type="warning">必填</el-tag>
                <el-tag v-if="f.ai_suggested" size="small" type="danger">AI</el-tag>
              </div>
              <div class="field-meta">
                <span class="field-name">{{ f.name }}</span>
                <span class="field-type">{{ f.db_type }}</span>
                <span class="field-ui">{{ getUILabel(f.ui_type) }}</span>
              </div>
            </div>
            <div class="field-actions">
              <el-button size="small" text @click.stop="openEditFieldDialog(f)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button v-if="!f.is_system" size="small" text type="danger" @click.stop="deleteField(f)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：字段详情/预览 -->
      <div class="detail-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="字段属性" name="props">
            <div v-if="selectedField" class="field-props">
              <el-form :model="selectedField" label-width="90px" size="small">
                <el-form-item label="字段名">
                  <el-input :model-value="selectedField.name" disabled />
                </el-form-item>
                <el-form-item label="显示名">
                  <el-input v-model="selectedField.title" @change="updateField" />
                </el-form-item>
                <el-form-item label="数据库类型">
                  <el-select v-model="selectedField.db_type" disabled style="width:100%">
                    <el-option v-for="t in dbTypes" :key="t.value" :label="t.label" :value="t.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="UI控件">
                  <el-select v-model="selectedField.ui_type" style="width:100%" @change="updateField">
                    <el-option v-for="t in uiTypes" :key="t.value" :label="t.label" :value="t.value" />
                  </el-select>
                </el-form-item>
                <el-divider content-position="left">约束</el-divider>
                <el-form-item label="必填">
                  <el-switch v-model="selectedField.is_required" @change="updateField" />
                </el-form-item>
                <el-form-item label="唯一">
                  <el-switch v-model="selectedField.is_unique" @change="updateField" />
                </el-form-item>
                <el-form-item label="索引">
                  <el-switch v-model="selectedField.is_indexed" @change="updateField" />
                </el-form-item>
                <el-form-item label="默认值">
                  <el-input v-model="selectedField.default_value" placeholder="无" @change="updateField" />
                </el-form-item>
                <template v-if="selectedField.db_type === 'TEXT'">
                  <el-form-item label="最大长度">
                    <el-input-number v-model="selectedField.max_length" :min="1" :max="65535" @change="updateField" />
                  </el-form-item>
                </template>
                <template v-if="['select','radio','checkbox'].includes(selectedField.ui_type)">
                  <el-divider content-position="left">选项列表</el-divider>
                  <div class="options-editor">
                    <div v-for="(opt, oi) in (selectedField.options || [])" :key="oi" class="option-row">
                      <el-input v-model="opt.label" size="small" placeholder="显示名" style="width:120px" @change="updateField" />
                      <el-input v-model="opt.value" size="small" placeholder="值" style="width:100px" @change="updateField" />
                      <el-button size="small" text type="danger" @click="removeOption(oi as number)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-button size="small" @click="addOption">+ 添加选项</el-button>
                  </div>
                </template>
                <el-divider content-position="left">显示</el-divider>
                <el-form-item label="占位提示">
                  <el-input v-model="selectedField.placeholder" placeholder="请输入..." @change="updateField" />
                </el-form-item>
                <el-form-item label="宽度">
                  <el-input v-model="selectedField.width" @change="updateField" />
                </el-form-item>
              </el-form>
            </div>
            <el-empty v-else description="选择左侧字段查看属性" />
          </el-tab-pane>

          <el-tab-pane label="关联关系" name="relations">
            <div class="relations-section">
              <el-button type="primary" size="small" @click="openAddRelationDialog" style="margin-bottom:12px">
                <el-icon><Plus /></el-icon> 添加关联
              </el-button>
              <div v-if="relations.length === 0" style="color:var(--el-text-color-secondary);font-size:13px">
                暂无关联关系
              </div>
              <div v-for="r in relations" :key="r.id" class="relation-item">
                <div class="rel-info">
                  <el-tag size="small">{{ r.from_field }}</el-tag>
                  <span class="rel-arrow">→</span>
                  <el-tag size="small" type="success">模型#{{ r.to_model_id }}.{{ r.to_field }}</el-tag>
                  <el-tag size="small" :type="getRelTagType(r.relation_type)">{{ getRelLabel(r.relation_type) }}</el-tag>
                  <span v-if="r.display_field" class="rel-display">显示: {{ r.display_field }}</span>
                </div>
                <el-button size="small" text type="danger" @click="deleteRelation(r)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="SQL预览" name="sql">
            <div class="sql-preview">
              <div class="sql-toolbar">
                <el-button size="small" @click="copySQL"><el-icon><CopyDocument /></el-icon> 复制</el-button>
              </div>
              <pre class="sql-code">{{ generatedSQL }}</pre>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 添加字段对话框 -->
    <el-dialog v-model="showFieldDialog" :title="editingField ? '编辑字段' : '添加字段'" width="520px" :close-on-click-modal="false">
      <el-form :model="fieldForm" label-width="90px" size="small">
        <el-form-item label="字段名" required>
          <el-input v-model="fieldForm.name" placeholder="英文小写下划线" :disabled="!!editingField" />
        </el-form-item>
        <el-form-item label="显示名" required>
          <el-input v-model="fieldForm.title" placeholder="中文名称" />
        </el-form-item>
        <el-form-item label="数据库类型" required>
          <el-select v-model="fieldForm.db_type" style="width:100%" :disabled="!!editingField">
            <el-option v-for="t in dbTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="UI控件">
          <el-select v-model="fieldForm.ui_type" style="width:100%">
            <el-option v-for="t in uiTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="必填">
          <el-switch v-model="fieldForm.is_required" />
        </el-form-item>
        <el-form-item label="唯一">
          <el-switch v-model="fieldForm.is_unique" />
        </el-form-item>
        <el-form-item label="索引">
          <el-switch v-model="fieldForm.is_indexed" />
        </el-form-item>
        <el-form-item label="默认值">
          <el-input v-model="fieldForm.default_value" placeholder="可选" />
        </el-form-item>
        <template v-if="fieldForm.db_type === 'TEXT'">
          <el-form-item label="最大长度">
            <el-input-number v-model="fieldForm.max_length" :min="1" :max="65535" />
          </el-form-item>
        </template>
        <template v-if="['select','radio','checkbox'].includes(fieldForm.ui_type)">
          <el-form-item label="选项列表">
            <div class="options-editor">
              <div v-for="(opt, oi) in fieldForm.options" :key="oi" class="option-row">
                <el-input v-model="opt.label" placeholder="显示名" style="width:120px" />
                <el-input v-model="opt.value" placeholder="值" style="width:100px" />
                <el-button text type="danger" @click="fieldForm.options.splice(oi, 1)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-button size="small" @click="fieldForm.options.push({ label: '', value: '' })">+ 添加选项</el-button>
            </div>
          </el-form-item>
        </template>
        <el-form-item label="占位提示">
          <el-input v-model="fieldForm.placeholder" placeholder="请输入..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFieldDialog = false">取消</el-button>
        <el-button type="primary" @click="saveField" :loading="savingField">
          {{ editingField ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加关联对话框 -->
    <el-dialog v-model="showRelationDialog" title="添加关联关系" width="500px">
      <el-form :model="relationForm" label-width="100px" size="small">
        <el-form-item label="目标模型" required>
          <el-select v-model="relationForm.to_model_id" style="width:100%" placeholder="选择目标模型">
            <el-option v-for="m in allModels" :key="m.id" :label="m.title + ' (' + m.name + ')'" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联类型" required>
          <el-select v-model="relationForm.relation_type" style="width:100%">
            <el-option label="一对一" value="one_to_one" />
            <el-option label="一对多" value="one_to_many" />
            <el-option label="多对多" value="many_to_many" />
          </el-select>
        </el-form-item>
        <el-form-item label="本表字段" required>
          <el-select v-model="relationForm.from_field" style="width:100%">
            <el-option v-for="f in fields" :key="f.id" :label="f.title + ' (' + f.name + ')'" :value="f.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标字段">
          <el-input v-model="relationForm.to_field" placeholder="默认 id" />
        </el-form-item>
        <el-form-item label="显示字段">
          <el-input v-model="relationForm.display_field" placeholder="关联时显示哪个字段" />
        </el-form-item>
        <el-form-item label="反向名称">
          <el-input v-model="relationForm.reverse_name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="删除策略">
          <el-select v-model="relationForm.on_delete" style="width:100%">
            <el-option label="设为空 (SET NULL)" value="set_null" />
            <el-option label="级联删除 (CASCADE)" value="cascade" />
            <el-option label="限制 (RESTRICT)" value="restrict" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRelationDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRelation" :loading="savingRelation">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Plus, Edit, Delete, Grid, Document, Rank,
  CopyDocument, Check, Refresh
} from '@element-plus/icons-vue'
import { dataModelAPI } from '../../common/api'

const route = useRoute()
const router = useRouter()
const modelId = computed(() => Number(route.params.id))

// 数据
const loading = ref(false)
const model = ref<any>(null)
const fields = ref<any[]>([])
const relations = ref<any[]>([])
const allModels = ref<any[]>([])
const selectedFieldId = ref<number | null>(null)
const activeTab = ref('props')

const selectedField = computed(() => fields.value.find(f => f.id === selectedFieldId.value) || null)

// 字段类型
const dbTypes = [
  { label: 'INTEGER (整数)', value: 'INTEGER' },
  { label: 'REAL (小数)', value: 'REAL' },
  { label: 'TEXT (文本)', value: 'TEXT' },
  { label: 'BOOLEAN (布尔)', value: 'BOOLEAN' },
  { label: 'DATE (日期)', value: 'DATE' },
  { label: 'DATETIME (日期时间)', value: 'DATETIME' },
  { label: 'JSON (JSON)', value: 'JSON' },
  { label: 'BLOB (二进制)', value: 'BLOB' },
]

const uiTypes = [
  { label: '文本框', value: 'text' },
  { label: '数字框', value: 'number' },
  { label: '日期选择', value: 'date' },
  { label: '日期时间', value: 'datetime' },
  { label: '下拉选择', value: 'select' },
  { label: '单选框', value: 'radio' },
  { label: '多选框', value: 'checkbox' },
  { label: '开关', value: 'switch' },
  { label: '文件上传', value: 'upload' },
  { label: '图片上传', value: 'image' },
  { label: '关联选择', value: 'relation' },
  { label: '子表单', value: 'subform' },
]

// 字段对话框
const showFieldDialog = ref(false)
const editingField = ref<any>(null)
const savingField = ref(false)
const fieldForm = ref<any>({
  name: '', title: '', db_type: 'TEXT', ui_type: 'text',
  is_required: false, is_unique: false, is_indexed: false,
  default_value: null, max_length: null, options: [], placeholder: '', width: '100%',
})

// 关联对话框
const showRelationDialog = ref(false)
const savingRelation = ref(false)
const relationForm = ref<any>({
  to_model_id: null, relation_type: 'one_to_many',
  from_field: '', to_field: 'id', display_field: '', reverse_name: '', on_delete: 'set_null',
})

// 加载数据
async function loadModel() {
  loading.value = true
  try {
    const res = await dataModelAPI.getModel(modelId.value)
    if (res?.success) {
      const d = res?.data
      model.value = d
      fields.value = d.fields || []
      relations.value = d.relations || []
    }
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function loadAllModels() {
  try {
    const res = await dataModelAPI.listModels({ limit: 200 })
    if (res?.success) {
      allModels.value = (res?.data || []).filter((m: any) => m.id !== modelId.value)
    }
  } catch { /* ignore */ }
}

// 更新模型信息
async function updateModelInfo() {
  if (!model.value) return
  try {
    await dataModelAPI.updateModel(modelId.value, {
      title: model.value.title,
      description: model.value.description,
    })
  } catch (e: any) {
    ElMessage.error('更新失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 字段操作
function selectField(f: any) {
  selectedFieldId.value = f.id
  activeTab.value = 'props'
}

async function openAddFieldDialog() {
  // 已建表模型添加字段时给出提示
  if (model.value?.is_created) {
    try {
      await ElMessageBox.confirm(
        '该模型已建表，添加字段将自动同步修改物理数据表结构。是否继续？',
        '添加字段',
        { type: 'info', confirmButtonText: '继续', cancelButtonText: '取消' }
      )
    } catch { return }
  }
  editingField.value = null
  fieldForm.value = {
    name: '', title: '', db_type: 'TEXT', ui_type: 'text',
    is_required: false, is_unique: false, is_indexed: false,
    default_value: null, max_length: null, options: [], placeholder: '', width: '100%',
  }
  showFieldDialog.value = true
}

function openEditFieldDialog(f: any) {
  editingField.value = f
  fieldForm.value = {
    name: f.name, title: f.title, db_type: f.db_type, ui_type: f.ui_type || 'text',
    is_required: f.is_required, is_unique: f.is_unique, is_indexed: f.is_indexed,
    default_value: f.default_value, max_length: f.max_length,
    options: JSON.parse(JSON.stringify(f.options || [])),
    placeholder: f.placeholder || '', width: f.width || '100%',
  }
  showFieldDialog.value = true
}

async function saveField() {
  if (!fieldForm.value.name || !fieldForm.value.title) {
    ElMessage.warning('请填写字段名和显示名')
    return
  }
  savingField.value = true
  try {
    if (editingField.value) {
      // 更新
      await dataModelAPI.updateField(modelId.value, editingField.value.id, fieldForm.value)
      ElMessage.success('字段更新成功')
    } else {
      // 添加
      await dataModelAPI.addField(modelId.value, fieldForm.value)
      ElMessage.success('字段添加成功')
    }
    showFieldDialog.value = false
    await loadModel()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    savingField.value = false
  }
}

async function updateField() {
  if (!selectedField.value) return
  try {
    await dataModelAPI.updateField(modelId.value, selectedField.value.id, {
      title: selectedField.value.title,
      ui_type: selectedField.value.ui_type,
      is_required: selectedField.value.is_required,
      is_unique: selectedField.value.is_unique,
      is_indexed: selectedField.value.is_indexed,
      default_value: selectedField.value.default_value,
      max_length: selectedField.value.max_length,
      options: selectedField.value.options,
      placeholder: selectedField.value.placeholder,
      width: selectedField.value.width,
    })
  } catch (e: any) {
    ElMessage.error('更新失败')
  }
}

async function deleteField(f: any) {
  const extraMsg = model.value?.is_created ? '\n\n⚠ 该模型已建表，删除字段将从物理表中移除对应列。' : ''
  try {
    await ElMessageBox.confirm(`确定删除字段「${f.title}」吗？${extraMsg}`, '删除确认', { type: 'warning' })
    await dataModelAPI.deleteField(modelId.value, f.id)
    if (selectedFieldId.value === f.id) selectedFieldId.value = null
    ElMessage.success('删除成功')
    await loadModel()
  } catch { /* cancel */ }
}

function addOption() {
  if (!selectedField.value) return
  if (!selectedField.value.options) selectedField.value.options = []
  selectedField.value.options.push({ label: '', value: '' })
}

function removeOption(idx: number) {
  selectedField.value.options.splice(idx, 1)
  updateField()
}

// 关联操作
function openAddRelationDialog() {
  relationForm.value = {
    to_model_id: null, relation_type: 'one_to_many',
    from_field: '', to_field: 'id', display_field: '', reverse_name: '', on_delete: 'set_null',
  }
  loadAllModels()
  showRelationDialog.value = true
}

async function saveRelation() {
  if (!relationForm.value.to_model_id || !relationForm.value.from_field) {
    ElMessage.warning('请选择目标模型和字段')
    return
  }
  savingRelation.value = true
  try {
    await dataModelAPI.addRelation(modelId.value, relationForm.value)
    ElMessage.success('关联添加成功')
    showRelationDialog.value = false
    await loadModel()
  } catch (e: any) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    savingRelation.value = false
  }
}

async function deleteRelation(r: any) {
  try {
    await ElMessageBox.confirm('确定删除此关联关系？', '删除确认', { type: 'warning' })
    await dataModelAPI.deleteRelation(modelId.value, r.id)
    ElMessage.success('删除成功')
    await loadModel()
  } catch { /* cancel */ }
}

// 生成操作
async function doCreateTable() {
  if (!model.value || model.value.is_created) return
  try {
    await ElMessageBox.confirm(`确定为「${model.value.title}」创建物理数据表吗？`, '创建数据表', { type: 'info' })
    const res = await dataModelAPI.createTable(modelId.value)
    if (res?.success) {
      ElMessage.success('数据表创建成功')
      await loadModel()
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('建表失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

async function doSyncTable() {
  if (!model.value || !model.value.is_created) return
  try {
    await ElMessageBox.confirm('将物理表与模型字段对齐，添加缺失列。是否继续？', '同步数据表', { type: 'info' })
    const res = await dataModelAPI.syncTable(modelId.value)
    if (res?.success) {
      ElMessage.success(res?.message || '同步完成')
      await loadModel()
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('同步失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

async function doGenerateTemplate() {
  if (!model.value || !model.value.is_created) return
  try {
    await ElMessageBox.confirm('确定从该模型生成 Kflower 模板吗？', '生成模板', { type: 'info' })
    const res = await dataModelAPI.generateTemplate(modelId.value)
    if (res?.success) {
      ElMessage.success('模板生成成功')
      await loadModel()
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

// SQL预览
const generatedSQL = computed(() => {
  if (!model.value || fields.value.length === 0) return '-- 请先添加字段'
  const tableName = `form_data_dm_${modelId.value}`
  const lines: string[] = []
  lines.push(`CREATE TABLE IF NOT EXISTS ${tableName} (`)
  lines.push('  id INTEGER PRIMARY KEY AUTOINCREMENT,')
  lines.push('  template_id INTEGER,')
  lines.push('  created_by INTEGER,')
  lines.push('  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,')
  lines.push('  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,')

  const fieldLines: string[] = []
  for (const f of fields.value) {
    if (f.is_primary_key && f.is_auto_increment) continue
    if (f.db_type === 'JSON') continue
    const typeMap: Record<string, string> = {
      'INTEGER': 'INTEGER', 'REAL': 'REAL', 'TEXT': f.max_length ? `VARCHAR(${f.max_length})` : 'TEXT',
      'BOOLEAN': 'BOOLEAN', 'DATE': 'DATE', 'DATETIME': 'DATETIME', 'BLOB': 'BLOB',
    }
    let col = `  "${f.name}" ${typeMap[f.db_type] || 'TEXT'}`
    if (f.is_required && !f.is_primary_key) col += ' NOT NULL'
    if (f.is_unique) col += ' UNIQUE'
    if (f.default_value) col += ` DEFAULT '${f.default_value}'`
    fieldLines.push(col)
  }
  lines.push(fieldLines.join(',\n'))
  lines.push(');')

  // 索引
  for (const f of fields.value) {
    if (f.is_indexed && !f.is_primary_key) {
      lines.push(`CREATE INDEX IF NOT EXISTS idx_${tableName}_${f.name} ON ${tableName}("${f.name}");`)
    }
  }

  return lines.join('\n')
})

function copySQL() {
  navigator.clipboard.writeText(generatedSQL.value).then(() => {
    ElMessage.success('SQL已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 辅助
function getUILabel(type: string) {
  const map: Record<string, string> = {
    text: '文本框', number: '数字框', date: '日期', datetime: '日期时间',
    select: '下拉', radio: '单选', checkbox: '多选', switch: '开关',
    upload: '上传', image: '图片', relation: '关联', subform: '子表单',
  }
  return map[type] || type
}

function getSourceTagType(t: string) {
  const map: Record<string, string> = { manual: '', import_db: 'success', copy_kflower: 'warning', ai: 'danger' }
  return map[t] || 'info'
}

function getSourceLabel(t: string) {
  const map: Record<string, string> = { manual: '手动创建', import_db: '数据库导入', copy_kflower: '复制内部表', ai: 'AI生成' }
  return map[t] || t
}

function getRelTagType(t: string) {
  const map: Record<string, string> = { one_to_one: '', one_to_many: 'success', many_to_many: 'warning' }
  return map[t] || 'info'
}

function getRelLabel(t: string) {
  const map: Record<string, string> = { one_to_one: '1:1', one_to_many: '1:N', many_to_many: 'N:N' }
  return map[t] || t
}

onMounted(() => {
  loadModel()
})
</script>

<style scoped>
.model-designer-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--el-bg-color-page);
}

.designer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left h3 {
  margin: 0;
  font-size: 17px;
  color: var(--el-text-color-primary);
}

.header-right {
  display: flex;
  gap: 8px;
}

.model-info-section {
  padding: 12px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.designer-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧字段列表 */
.fields-panel {
  width: 360px;
  border-right: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.panel-header h4 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.fields-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 4px;
}

.field-item:hover {
  background: var(--el-fill-color-light);
}

.field-item.active {
  background: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
}

.field-drag {
  color: var(--el-text-color-placeholder);
  cursor: grab;
}

.field-info {
  flex: 1;
  min-width: 0;
}

.field-title-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.field-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}

.field-name {
  font-family: monospace;
}

.field-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

/* 右侧详情 */
.detail-panel {
  flex: 1;
  padding: 16px 24px;
  overflow-y: auto;
  background: var(--el-bg-color-page);
}

.field-props {
  max-width: 600px;
}

.relations-section {
  max-width: 600px;
}

.relation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--el-bg-color);
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.rel-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.rel-arrow {
  font-size: 16px;
  color: var(--el-color-primary);
}

.rel-display {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

/* SQL预览 */
.sql-preview {
  position: relative;
}

.sql-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.sql-code {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  padding: 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--el-text-color-primary);
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

/* 选项编辑器 */
.options-editor {
  width: 100%;
}

.option-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
</style>
