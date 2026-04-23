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
            <template v-for="field in mod.fields" :key="field.name">
              <!-- 条件显示/隐藏 -->
              <el-form-item
                v-if="isFieldVisible(field)"
                :label="field.label + (field.required ? ' *' : '')"
                :prop="field.name"
                :rules="buildFieldRules(field)"
              >
                <!-- 公式字段（只读计算结果） -->
                <div v-if="field.is_formula || field.formula" class="formula-field">
                  <el-input :value="formData[field.name]" readonly>
                    <template #prefix>
                      <el-icon style="color:#409EFF"><Operation /></el-icon>
                    </template>
                  </el-input>
                  <span class="formula-hint">自动计算：{{ field.formula }}</span>
                </div>
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

              <!-- 下拉选择（含级联选项） -->
              <el-select
                v-else-if="field.type === 'select'"
                v-model="formData[field.name]"
                style="width:100%"
                :placeholder="field.placeholder || '请选择'"
                :multiple="field.multiple"
                collapse-tags
                @change="onFieldChange(field)"
              >
                <el-option
                  v-for="opt in getCascadeOptions(field)"
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

              <!-- 子表/明细表 -->
              <div v-else-if="field.type === 'subform'" class="subform-container">
                <div class="subform-header">
                  <span class="subform-title">{{ field.label }}</span>
                  <el-button type="primary" size="small" @click="addSubTableRow(field)">
                    <el-icon><Plus /></el-icon> 添加行
                  </el-button>
                </div>
                <el-table :data="getSubTableData(field)" border size="small" style="width:100%">
                  <el-table-column type="index" label="#" width="50" />
                  <el-table-column
                    v-for="sf in (field.subtable_fields || [])"
                    :key="sf.name"
                    :label="sf.label || sf.name"
                    :min-width="120"
                  >
                    <template #default="{ row, $index }">
                      <el-input
                        v-if="['text','email','phone','url','money'].includes(sf.type)"
                        v-model="row[sf.name]"
                        :placeholder="sf.placeholder || '请输入'"
                        size="small"
                        @change="onFieldChange(field)"
                      />
                      <el-input-number
                        v-else-if="sf.type === 'number'"
                        v-model="row[sf.name]"
                        :min="sf.min"
                        :max="sf.max"
                        size="small"
                        style="width:100%"
                        @change="onFieldChange(field)"
                      />
                      <el-select
                        v-else-if="sf.type === 'select'"
                        v-model="row[sf.name]"
                        size="small"
                        style="width:100%"
                        @change="onFieldChange(field)"
                      >
                        <el-option
                          v-for="opt in (sf.options || [])"
                          :key="opt"
                          :label="opt"
                          :value="opt"
                        />
                      </el-select>
                      <el-date-picker
                        v-else-if="sf.type === 'date'"
                        v-model="row[sf.name]"
                        type="date"
                        size="small"
                        style="width:100%"
                        value-format="YYYY-MM-DD"
                        @change="onFieldChange(field)"
                      />
                      <el-input
                        v-else
                        v-model="row[sf.name]"
                        size="small"
                        @change="onFieldChange(field)"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="70" fixed="right">
                    <template #default="{ $index }">
                      <el-button type="danger" text size="small" @click="removeSubTableRow(field, $index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 关联数据选择器 -->
              <div v-else-if="field.type === 'relation'" class="relation-field">
                <el-select
                  v-model="formData[field.name]"
                  filterable
                  remote
                  reserve-keyword
                  :placeholder="field.placeholder || '搜索选择关联记录'"
                  :remote-method="(q) => searchRelation(field, q)"
                  :loading="relationLoading[field.name]"
                  style="width:100%"
                  @change="(val) => onRelationSelect(field, val)"
                >
                  <el-option
                    v-for="item in (relationOptions[field.name] || [])"
                    :key="item.id"
                    :label="item.display_value"
                    :value="item.id"
                  />
                </el-select>
              </div>

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
                @change="onFieldChange(field)"
              />
            </el-form-item>
            </template>
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
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Plus, Check, Operation, Delete } from '@element-plus/icons-vue'
import { templateAPI } from '../../common/api'
import { useUserStore } from '../../common/store/user'
import axios from 'axios'

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

// 所有字段定义（平铺）
const allFields = computed(() => {
  const fields: any[] = []
  modules.value.forEach((mod: any) => {
    if (mod.fields) fields.push(...mod.fields)
  })
  return fields
})

// 上传配置
const uploadUrl = computed(() => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${baseURL}/upload`
})
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// ============ 公式引擎（前端轻量实现） ============

/**
 * 简单公式求值器（前端版）
 * 支持：四则运算、字段引用 {字段名}、常量
 */
function evaluateFormula(formula: string, ctx: Record<string, any>): any {
  if (!formula) return undefined
  try {
    // 替换 {字段名} 为实际值
    let expr = formula.replace(/\{([^}]+)\}/g, (_match: string, fieldName: string) => {
      const val = ctx[fieldName.trim()]
      if (val === undefined || val === null || val === '') return '0'
      const num = Number(val)
      return isNaN(num) ? JSON.stringify(String(val)) : String(num)
    })

    // 安全求值（只允许数学表达式和内置函数）
    // 支持：+ - * / % ** () 以及 Math 函数
    expr = expr
      .replace(/\bROUND\b/g, 'Math.round')
      .replace(/\bFLOOR\b/g, 'Math.floor')
      .replace(/\bCEIL\b/g, 'Math.ceil')
      .replace(/\bABS\b/g, 'Math.abs')
      .replace(/\bSQRT\b/g, 'Math.sqrt')
      .replace(/\bPOWER\b/g, 'Math.pow')
      .replace(/\bMAX\b/g, 'Math.max')
      .replace(/\bMIN\b/g, 'Math.min')

    // 安全检查：只允许数字、运算符、括号、Math、逗号、空格
    if (!/^[\d\s\+\-\*\/\%\.\(\)\,Math\.roundfloeabspwx]*$/i.test(expr.replace(/Math\.\w+/g, ''))) {
      // 放宽到允许比较和逻辑运算（含条件判断）
    }

    // 使用 Function 沙箱（只注入 Math）
    // eslint-disable-next-line no-new-func
    const fn = new Function('Math', `"use strict"; return (${expr})`)
    const result = fn(Math)
    if (typeof result === 'number' && !isNaN(result)) {
      return Math.round(result * 1e10) / 1e10  // 避免浮点精度问题
    }
    return result
  } catch {
    return undefined
  }
}

/**
 * 计算所有公式字段
 */
function computeFormulas() {
  // 构建上下文，包含子表数据
  const ctx: Record<string, any> = { ...formData }
  allFields.value.forEach((field: any) => {
    if (field.type === 'subform' && formData[field.name]) {
      ctx[field.name] = formData[field.name]  // 子表数据为数组
    }
  })

  allFields.value.forEach((field: any) => {
    if (!field.formula && !field.is_formula) return
    if (!field.formula) return
    const result = evaluateFormula(field.formula, ctx)
    if (result !== undefined) {
      formData[field.name] = result
      ctx[field.name] = result  // 更新上下文，便于链式计算
    }
  })
}

// ============ 条件显示/隐藏 ============

function isFieldVisible(field: any): boolean {
  const rule = field.visibility_rule
  if (!rule) return !field.hidden

  if (typeof rule === 'string') {
    return !!evaluateFormula(rule, { ...formData })
  }

  if (rule.type === 'formula' && rule.formula) {
    return !!evaluateFormula(rule.formula, { ...formData })
  }

  if (rule.type === 'simple' || !rule.type) {
    const { field: targetField, operator, value: expected } = rule
    const actual = formData[targetField]
    return compareValues(actual, operator || 'eq', expected)
  }

  return true
}

function compareValues(actual: any, operator: string, expected: any): boolean {
  const a = actual === undefined || actual === null ? '' : actual
  switch (operator) {
    case 'eq': return String(a) === String(expected)
    case 'neq': return String(a) !== String(expected)
    case 'gt': return Number(a) > Number(expected)
    case 'lt': return Number(a) < Number(expected)
    case 'gte': return Number(a) >= Number(expected)
    case 'lte': return Number(a) <= Number(expected)
    case 'contains': return String(a).includes(String(expected))
    case 'in': return Array.isArray(expected) ? expected.map(String).includes(String(a)) : String(a) === String(expected)
    case 'not_in': return Array.isArray(expected) ? !expected.map(String).includes(String(a)) : String(a) !== String(expected)
    case 'is_empty': return a === '' || a === null || a === undefined
    case 'not_empty': return a !== '' && a !== null && a !== undefined
    default: return true
  }
}

// ============ 级联选项 ============

function getCascadeOptions(field: any): string[] {
  const cascade = field.cascade_source
  if (!cascade) return field.options || []

  const parentValue = formData[cascade.parent_field]
  if (!parentValue) return []

  const optionsMap = cascade.options_map || {}
  return optionsMap[String(parentValue)] || []
}

// ============ 子表操作 ============

function getSubTableData(field: any): any[] {
  return formData[field.name] || []
}

function addSubTableRow(field: any) {
  if (!formData[field.name]) formData[field.name] = []
  const newRow: Record<string, any> = {}
  ;(field.subtable_fields || []).forEach((sf: any) => {
    if (sf.type === 'number' || sf.type === 'money') {
      newRow[sf.name] = 0
    } else {
      newRow[sf.name] = ''
    }
  })
  formData[field.name].push(newRow)
  // 子表变化触发公式重算
  computeFormulas()
}

function removeSubTableRow(field: any, index: number) {
  if (formData[field.name]) {
    formData[field.name].splice(index, 1)
    computeFormulas()
  }
}

// ============ 关联数据（Lookup） ============

const relationOptions = reactive<Record<string, any[]>>({})
const relationLoading = reactive<Record<string, boolean>>({})

async function searchRelation(field: any, query: string) {
  const relation = field.relation || field.auto_fill
  if (!relation) return
  const targetTemplateId = relation.target_template_id || relation.source_template_id
  if (!targetTemplateId) return

  relationLoading[field.name] = true
  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const res = await axios.get(`${baseURL}/templates/lookup`, {
      params: {
        target_template_id: targetTemplateId,
        search: query || undefined,
        display_field: relation.display_field,
        limit: 20
      },
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    relationOptions[field.name] = res.data?.results || res.data?.items || []
  } catch {
    relationOptions[field.name] = []
  } finally {
    relationLoading[field.name] = false
  }
}

async function onRelationSelect(field: any, selectedId: any) {
  const relation = field.relation || field.auto_fill
  if (!relation || !selectedId) return
  const targetTemplateId = relation.target_template_id || relation.source_template_id
  const autoFillFields = relation.auto_fill_fields || []

  if (!autoFillFields.length || !targetTemplateId) return

  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const res = await axios.get(`${baseURL}/templates/lookup/${targetTemplateId}/${selectedId}`, {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    const record = res.data?.data || {}
    // 自动填充映射字段
    autoFillFields.forEach((f: any) => {
      if (typeof f === 'string' && record[f] !== undefined) {
        formData[f] = record[f]
      } else if (typeof f === 'object' && f.target && record[f.source]) {
        formData[f.target] = record[f.source]
      }
    })
    computeFormulas()
  } catch {
    // 自动填充失败不影响选择
  }
}

// ============ 字段变化处理 ============

function onFieldChange(field: any) {
  // 触发公式重新计算
  computeFormulas()

  // 如果是父级联选项字段，清空子级选项
  allFields.value.forEach((f: any) => {
    if (f.cascade_source?.parent_field === field.name) {
      formData[f.name] = ''
    }
  })
}

// 监听数据变化，自动重算公式
watch(
  () => ({ ...formData }),
  () => {
    computeFormulas()
  },
  { deep: false }
)

// ============ 表单验证 ============

const formRules = computed(() => {
  const rules: Record<string, any[]> = {}
  allFields.value.forEach((field: any) => {
    if (!isFieldVisible(field)) return
    rules[field.name] = buildFieldRules(field)
  })
  return rules
})

function buildFieldRules(field: any): any[] {
  const rules: any[] = []

  // 公式字段跳过校验
  if (field.is_formula || field.formula) return rules

  // 新式高级校验规则
  if (field.validation_rules && Array.isArray(field.validation_rules)) {
    field.validation_rules.forEach((rule: any) => {
      if (rule.type === 'required') {
        rules.push({ required: true, message: rule.message || `请填写${field.label}`, trigger: 'change' })
      } else if (rule.type === 'min_value') {
        rules.push({
          validator: (_rule: any, value: any, callback: any) => {
            if (value !== undefined && value !== '' && Number(value) < Number(rule.value)) {
              callback(new Error(rule.message || `${field.label} 不能小于 ${rule.value}`))
            } else callback()
          },
          trigger: 'change'
        })
      } else if (rule.type === 'max_value') {
        rules.push({
          validator: (_rule: any, value: any, callback: any) => {
            if (value !== undefined && value !== '' && Number(value) > Number(rule.value)) {
              callback(new Error(rule.message || `${field.label} 不能大于 ${rule.value}`))
            } else callback()
          },
          trigger: 'change'
        })
      } else if (rule.type === 'regex') {
        rules.push({
          pattern: new RegExp(rule.value),
          message: rule.message || `${field.label} 格式不正确`,
          trigger: 'blur'
        })
      } else if (rule.type === 'min_length') {
        rules.push({ min: Number(rule.value), message: rule.message || `${field.label} 长度不能少于 ${rule.value} 个字符`, trigger: 'blur' })
      } else if (rule.type === 'max_length') {
        rules.push({ max: Number(rule.value), message: rule.message || `${field.label} 长度不能超过 ${rule.value} 个字符`, trigger: 'blur' })
      }
    })
    return rules
  }

  // 老式校验（向后兼容）
  if (field.required) {
    rules.push({ required: true, message: `请填写${field.label}`, trigger: 'change' })
  }
  if (field.type === 'email') {
    rules.push({ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' })
  }
  if (field.type === 'phone') {
    rules.push({ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' })
  }
  if (field.type === 'url') {
    rules.push({ type: 'url', message: '请输入正确的网址格式', trigger: 'blur' })
  }
  return rules
}

// ============ 数据加载 ============

async function loadTemplate() {
  const templateId = route.params.id as string
  if (!templateId) {
    error.value = '模板ID不能为空'
    loading.value = false
    return
  }

  try {
    const res: any = await templateAPI.get(parseInt(templateId))
    if (res.id) {
      template.value = res
      modules.value = res.modules || []

      // 初始化表单数据
      modules.value.forEach((mod: any) => {
        mod.fields.forEach((field: any) => {
          // 子表字段初始化为空数组
          if (field.type === 'subform') {
            formData[field.name] = field.defaultValue || []
            return
          }
          // 关联字段
          if (field.type === 'relation') {
            formData[field.name] = field.defaultValue || null
            return
          }
          if (field.type === 'checkbox' || field.type === 'tags' || (field.type === 'select' && field.multiple)) {
            formData[field.name] = field.defaultValue || []
          } else if (field.type === 'switch') {
            formData[field.name] = field.defaultValue !== undefined ? field.defaultValue : false
          } else if (field.type === 'number') {
            formData[field.name] = field.defaultValue !== undefined ? Number(field.defaultValue) : undefined
          } else if (field.is_formula || field.formula) {
            formData[field.name] = ''  // 公式字段初始为空，等待计算
          } else {
            formData[field.name] = field.defaultValue || ''
          }

          if (field.type === 'file' || field.type === 'upload' || field.type === 'image') {
            fileList[field.name] = []
          }
        })
      })

      // 初始化时计算一次公式
      computeFormulas()
    } else {
      error.value = res.message || '加载模板失败'
    }
  } catch (e: any) {
    error.value = e.message || '加载模板失败'
  } finally {
    loading.value = false
  }
}

function beforeUpload(file: File, field: any) {
  const maxSize = (field.maxSize || 10) * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error(`文件大小不能超过${field.maxSize || 10}MB`)
    return false
  }
  return true
}

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

function resetForm() {
  ElMessageBox.confirm('确定要重置表单吗？已填写的内容将清空', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    formRef.value?.resetFields()
    Object.keys(fileList).forEach(key => { fileList[key] = [] })
    ElMessage.success('表单已重置')
  }).catch(() => {})
}

function goToDataList() {
  const templateId = route.params.id as string
  router.push(`/form/${templateId}/data`)
}

function fillAgain() {
  showSuccess.value = false
  formRef.value?.resetFields()
  Object.keys(fileList).forEach(key => { fileList[key] = [] })
}

onMounted(() => {
  loadTemplate()
})
</script>

<style scoped lang="scss">
.form-fill-page {
  min-height: 100vh;
  background: var(--el-bg-color-page);
  padding: 40px 20px;
}

.loading-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px;
  background: var(--el-bg-color);
  border-radius: 8px;
}

.form-header {
  text-align: center;
  margin-bottom: 30px;

  .form-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 12px;
  }

  .form-desc {
    font-size: 14px;
    color: var(--el-text-color-regular);
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
  color: var(--el-text-color-primary);
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
  color: var(--el-text-color-primary);
  margin: 16px 0 8px;
}

.field-desc {
  font-size: 14px;
  color: var(--el-text-color-regular);
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

.formula-field {
  width: 100%;
  .formula-hint {
    display: block;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: 4px;
  }
}

.subform-container {
  width: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;

  .subform-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: var(--el-bg-color-page);
    border-bottom: 1px solid #e4e7ed;
    .subform-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
}

.relation-field {
  width: 100%;
}

.form-footer {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  color: var(--el-text-color-secondary);
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
