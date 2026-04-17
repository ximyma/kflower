<template>
  <div class="form-data-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/templates' }">模板设计</el-breadcrumb-item>
        <el-breadcrumb-item>数据管理</el-breadcrumb-item>
      </el-breadcrumb>
      <div class="header-actions">
        <el-button type="primary" @click="goToFormFill">
          <el-icon><Plus /></el-icon> 新增数据
        </el-button>
        <el-button @click="exportExcel">
          <el-icon><Download /></el-icon> 导出Excel
        </el-button>
        <el-button @click="importExcel">
          <el-icon><Upload /></el-icon> 导入Excel
        </el-button>
      </div>
    </div>

    <el-card class="main-card">
      <div class="card-header">
        <h2>{{ template.name }} - 数据列表</h2>
        <div class="card-actions">
          <el-button text @click="refreshData">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
          <el-dropdown @command="handleBatchAction">
            <el-button>
              批量操作<el-icon><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="delete">批量删除</el-dropdown-item>
                <el-dropdown-item command="exportSelected">导出选中</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 搜索和筛选 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索数据..."
          clearable
          style="width:300px"
          @keyup.enter="doSearch"
          @clear="doSearch"
        >
          <template #append>
            <el-button @click="doSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>

        <div class="filter-controls">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width:240px"
            @change="doSearch"
          />
        </div>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width:100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column type="index" label="序号" width="60" />
        
        <!-- 动态列 - 根据模板字段生成 -->
        <template v-for="(field, idx) in displayFields" :key="field.name">
          <el-table-column
            v-if="!field.hidden"
            :prop="field.name"
            :label="field.label"
            :min-width="getColumnWidth(field.type)"
          >
            <template #default="{ row }">
              <template v-if="field.type === 'switch'">
                <el-tag :type="row[field.name] ? 'success' : 'info'">
                  {{ row[field.name] ? (field.activeText || '是') : (field.inactiveText || '否') }}
                </el-tag>
              </template>
              <template v-else-if="field.type === 'date' || field.type === 'datetime'">
                {{ formatDate(row[field.name]) }}
              </template>
              <template v-else-if="field.type === 'daterange'">
                {{ row[field.name]?.join(' 至 ') }}
              </template>
              <template v-else-if="field.type === 'select' || field.type === 'radio'">
                <el-tag>{{ row[field.name] }}</el-tag>
              </template>
              <template v-else-if="field.type === 'checkbox' || field.type === 'tags'">
                <div v-if="Array.isArray(row[field.name])">
                  <el-tag v-for="(item, i) in row[field.name].slice(0, 3)" :key="i" size="small">
                    {{ item }}
                  </el-tag>
                  <span v-if="row[field.name].length > 3" class="more-tag">+{{ row[field.name].length - 3 }}</span>
                </div>
                <span v-else>{{ row[field.name] }}</span>
              </template>
              <template v-else-if="field.type === 'image' || field.type === 'file'">
                <div v-if="row[field.name]">
                  <el-button
                    v-for="(url, i) in (Array.isArray(row[field.name]) ? row[field.name] : [row[field.name]])"
                    :key="i"
                    link
                    @click="previewFile(url)"
                  >
                    文件{{ i + 1 }}
                  </el-button>
                </div>
              </template>
              <template v-else>
                {{ row[field.name] }}
              </template>
            </template>
          </el-table-column>
        </template>

        <el-table-column prop="created_at" label="提交时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="editData(row)">编辑</el-button>
            <el-button type="info" link @click="viewDetail(row)">详情</el-button>
            <el-button type="danger" link @click="deleteData(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" :title="`数据详情 - ${selectedData?.id || ''}`" width="70%">
      <el-descriptions v-if="selectedData" :column="2" border>
        <template v-for="field in displayFields" :key="field.name">
          <el-descriptions-item v-if="selectedData[field.name] !== undefined" :label="field.label">
            <template v-if="field.type === 'switch'">
              <el-tag :type="selectedData[field.name] ? 'success' : 'info'">
                {{ selectedData[field.name] ? (field.activeText || '是') : (field.inactiveText || '否') }}
              </el-tag>
            </template>
            <template v-else-if="field.type === 'image'">
              <div v-if="Array.isArray(selectedData[field.name])">
                <el-image
                  v-for="(url, i) in selectedData[field.name]"
                  :key="i"
                  :src="url"
                  style="width:100px;height:100px;margin-right:10px"
                  :preview-src-list="selectedData[field.name]"
                />
              </div>
              <el-image v-else :src="selectedData[field.name]" style="width:100px;height:100px" />
            </template>
            <template v-else-if="field.type === 'file'">
              <div v-if="Array.isArray(selectedData[field.name])">
                <div v-for="(url, i) in selectedData[field.name]" :key="i">
                  <el-button link @click="downloadFile(url)">文件{{ i + 1 }}</el-button>
                </div>
              </div>
              <el-button v-else link @click="downloadFile(selectedData[field.name])">下载文件</el-button>
            </template>
            <template v-else-if="field.type === 'daterange'">
              {{ selectedData[field.name]?.join(' 至 ') }}
            </template>
            <template v-else-if="Array.isArray(selectedData[field.name])">
              {{ selectedData[field.name].join(', ') }}
            </template>
            <template v-else>
              {{ selectedData[field.name] }}
            </template>
          </el-descriptions-item>
        </template>
        <el-descriptions-item label="提交时间">
          {{ formatDateTime(selectedData.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="最后更新">
          {{ formatDateTime(selectedData.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" :title="editMode === 'add' ? '新增数据' : '编辑数据'" width="50%">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <template v-for="field in displayFields" :key="field.name">
          <el-form-item
            v-if="!field.hidden && field.type !== 'divider' && field.type !== 'title' && field.type !== 'description'"
            :label="field.label + (field.required ? ' *' : '')"
            :prop="field.name"
          >
            <!-- 根据字段类型渲染对应控件 -->
            <template v-if="field.type === 'text' || field.type === 'email' || field.type === 'phone' || field.type === 'url'">
              <el-input v-model="editForm[field.name]" :placeholder="field.placeholder" :maxlength="field.maxLength" />
            </template>
            <template v-else-if="field.type === 'textarea'">
              <el-input v-model="editForm[field.name]" type="textarea" :rows="3" :placeholder="field.placeholder" />
            </template>
            <template v-else-if="field.type === 'number'">
              <el-input-number v-model="editForm[field.name]" :min="field.min" :max="field.max" style="width:100%" />
            </template>
            <template v-else-if="field.type === 'date'">
              <el-date-picker
                v-model="editForm[field.name]"
                type="date"
                style="width:100%"
                value-format="YYYY-MM-DD"
                :placeholder="field.placeholder"
              />
            </template>
            <template v-else-if="field.type === 'datetime'">
              <el-date-picker
                v-model="editForm[field.name]"
                type="datetime"
                style="width:100%"
                value-format="YYYY-MM-DD HH:mm:ss"
                :placeholder="field.placeholder"
              />
            </template>
            <template v-else-if="field.type === 'select'">
              <el-select v-model="editForm[field.name]" style="width:100%" :multiple="field.multiple">
                <el-option v-for="opt in field.options" :key="opt" :label="opt" :value="opt" />
              </el-select>
            </template>
            <template v-else-if="field.type === 'radio'">
              <el-radio-group v-model="editForm[field.name]">
                <el-radio v-for="opt in field.options" :key="opt" :label="opt">{{ opt }}</el-radio>
              </el-radio-group>
            </template>
            <template v-else-if="field.type === 'checkbox'">
              <el-checkbox-group v-model="editForm[field.name]">
                <el-checkbox v-for="opt in field.options" :key="opt" :label="opt">{{ opt }}</el-checkbox>
              </el-checkbox-group>
            </template>
            <template v-else-if="field.type === 'switch'">
              <el-switch v-model="editForm[field.name]" :active-text="field.activeText || '是'" :inactive-text="field.inactiveText || '否'" />
            </template>
            <template v-else>
              <el-input v-model="editForm[field.name]" :placeholder="field.placeholder" />
            </template>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveData" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 导入Excel对话框 -->
    <el-dialog v-model="showImportDialog" title="导入Excel" width="500px">
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleImportSuccess"
        :before-upload="beforeImportUpload"
        accept=".xlsx,.xls,.csv"
        :show-file-list="false"
        drag
      >
        <el-icon><Upload /></el-icon>
        <div class="el-upload__text">将Excel文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx, .xls, .csv 格式，文件大小不超过10MB<br>
            请确保Excel表头与字段名一致
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>

    <!-- 字段映射对话框 -->
    <el-dialog v-model="showMappingDialog" title="字段映射" width="700px" :close-on-click-modal="false">
      <div v-if="mappingLoading" class="mapping-loading">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else>
        <div class="mapping-info">
          <p>已解析到 {{ excelHeaders.length }} 个Excel列，{{ excelRows.length }} 行数据</p>
          <p>请将Excel列映射到对应的表单字段：</p>
        </div>
        
        <el-table :data="excelHeaders.map((header, index) => ({ header, index }))" border stripe>
          <el-table-column prop="header" label="Excel列名" width="200">
            <template #default="{ row }">
              <strong>{{ row.header || `(第${row.index + 1}列)` }}</strong>
            </template>
          </el-table-column>
          
          <el-table-column label="映射到字段" width="300">
            <template #default="{ row }">
              <el-select 
                v-model="fieldMappings[row.header]" 
                placeholder="选择映射字段"
                clearable
                style="width:100%"
                @change="updateMapping(row.header, $event)"
              >
                <el-option label="(忽略此列)" value="" />
                <el-option-group label="表单字段">
                  <el-option 
                    v-for="field in displayFields" 
                    :key="field.name"
                    :label="`${field.label} (${field.name})`"
                    :value="field.name"
                  />
                </el-option-group>
              </el-select>
            </template>
          </el-table-column>
          
          <el-table-column label="数据类型" width="150">
            <template #default="{ row }">
              <el-tag type="info" size="small">
                {{ getExcelColumnType(row.index) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="数据预览" min-width="200">
            <template #default="{ row }">
              <div class="preview-cell" :title="getPreviewText(row.index)">
                {{ getPreviewText(row.index) }}
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="mapping-actions">
          <el-button @click="autoMatchAll">自动匹配全部</el-button>
          <el-button @click="clearAllMappings">清空全部映射</el-button>
          <el-button type="primary" @click="applyMappingAndImport">确认导入</el-button>
        </div>
        
        <div class="mapping-stats">
          <p>已映射: {{ Object.values(fieldMappings).filter(v => v).length }} / {{ excelHeaders.length }} 列</p>
          <p v-if="missingRequiredFields.length > 0" class="warning-text">
            ⚠️ 缺少必填字段: {{ missingRequiredFields.map(f => f.label).join(', ') }}
          </p>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showMappingDialog = false">取消</el-button>
        <el-button type="primary" @click="applyMappingAndImport" :loading="mappingLoading">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElTable } from 'element-plus'
import { Plus, Download, Upload, Refresh, ArrowDown, Search } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { templateAPI } from '../../common/api'
import { useUserStore } from '../../common/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 模板和数据
const template = ref<any>({})
const modules = ref<any[]>([])
const displayFields = ref<any[]>([])
const loading = ref(false)
const tableData = ref<any[]>([])

// 分页和搜索
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const dateRange = ref<[string, string]>(['', ''])

// 表格选择
const multipleSelection = ref<any[]>([])
const tableRef = ref<InstanceType<typeof ElTable>>()

// 对话框
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const showImportDialog = ref(false)
const showMappingDialog = ref(false)
const selectedData = ref<any>(null)
const editForm = reactive<Record<string, any>>({})
const editMode = ref<'add' | 'edit'>('add')
const saving = ref(false)
const uploadRef = ref<any>(null)
const editFormRef = ref<any>(null)

// Excel导入相关
const excelHeaders = ref<string[]>([])
const excelRows = ref<any[][]>([])
const fieldMappings = ref<Record<string, string>>({}) // Excel列名 -> 字段名
const excelFile = ref<File | null>(null)
const mappingLoading = ref(false)

// 上传配置
const uploadUrl = computed(() => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  return `${baseURL}/upload`
})
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

// 验证规则
const editRules = computed(() => {
  const rules: Record<string, any[]> = {}
  displayFields.value.forEach((field: any) => {
    if (field.required) {
      rules[field.name] = [
        { required: true, message: `请填写${field.label}`, trigger: 'change' }
      ]
    }
  })
  return rules
})

// 计算缺少的必填字段映射
const missingRequiredFields = computed(() => {
  const requiredFields = displayFields.value.filter(f => f.required)
  return requiredFields.filter(field => {
    // 检查是否有Excel列映射到这个必填字段
    const mapped = Object.values(fieldMappings.value).includes(field.name)
    return !mapped
  })
})

// 获取列宽
function getColumnWidth(type: string): string {
  const widthMap: Record<string, string> = {
    text: '120px',
    textarea: '200px',
    number: '100px',
    date: '120px',
    datetime: '150px',
    daterange: '180px',
    select: '120px',
    radio: '100px',
    checkbox: '150px',
    switch: '100px',
    email: '150px',
    phone: '120px',
    url: '150px',
    file: '120px',
    image: '120px'
  }
  return widthMap[type] || '120px'
}

// 格式化日期
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatDateTime(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

// ============ Excel导入辅助函数 ============

// 获取Excel列的数据类型
function getExcelColumnType(colIndex: number): string {
  if (!excelRows.value || excelRows.value.length === 0) return '未知'
  
  const sampleValues = excelRows.value.slice(0, 5).map(row => row[colIndex])
  const nonEmpty = sampleValues.filter(v => v !== undefined && v !== null && v !== '')
  
  if (nonEmpty.length === 0) return '空'
  
  const firstVal = nonEmpty[0]
  if (typeof firstVal === 'number') return '数字'
  if (typeof firstVal === 'boolean') return '布尔'
  if (firstVal instanceof Date) return '日期'
  
  const strVal = String(firstVal)
  if (/^\d{4}-\d{2}-\d{2}$/.test(strVal)) return '日期'
  if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(strVal)) return '日期时间'
  if (/^1[3-9]\d{9}$/.test(strVal)) return '手机号'
  if (/^[\w.-]+@[\w.-]+\.\w+$/.test(strVal)) return '邮箱'
  if (strVal.includes('\n') || strVal.length > 50) return '长文本'
  
  return '文本'
}

// 获取预览文本
function getPreviewText(colIndex: number): string {
  if (!excelRows.value || excelRows.value.length === 0) return '无数据'
  
  const sampleValues = excelRows.value.slice(0, 3).map(row => row[colIndex])
  const nonEmpty = sampleValues.filter(v => v !== undefined && v !== null && v !== '')
  
  if (nonEmpty.length === 0) return '空'
  
  return nonEmpty.map(v => {
    if (v === null || v === undefined) return ''
    if (typeof v === 'object') return JSON.stringify(v).slice(0, 30) + '...'
    return String(v).slice(0, 30) + (String(v).length > 30 ? '...' : '')
  }).join(' | ')
}

// 更新映射关系
function updateMapping(header: string, fieldName: string) {
  if (fieldName) {
    fieldMappings.value[header] = fieldName
  } else {
    delete fieldMappings.value[header]
  }
}

// 自动匹配全部字段
function autoMatchAll() {
  const newMappings: Record<string, string> = {}
  
  excelHeaders.value.forEach((header, index) => {
    if (header && typeof header === 'string') {
      // 尝试多种匹配策略
      const matchedField = displayFields.value.find(field => {
        // 1. 完全匹配标签
        if (field.label === header.trim()) return true
        // 2. 忽略大小写和空格匹配标签
        if (field.label.toLowerCase().replace(/\s+/g, '') === header.toLowerCase().replace(/\s+/g, '')) return true
        // 3. 匹配字段名
        if (field.name === header.trim().toLowerCase().replace(/\s+/g, '_')) return true
        // 4. 匹配字段名（忽略下划线）
        if (field.name.replace(/_/g, '') === header.toLowerCase().replace(/\s+/g, '').replace(/_/g, '')) return true
        return false
      })
      
      if (matchedField) {
        newMappings[header] = matchedField.name
      }
    }
  })
  
  fieldMappings.value = newMappings
}

// 清空全部映射
function clearAllMappings() {
  fieldMappings.value = {}
}

// 应用映射并导入数据
async function applyMappingAndImport() {
  if (Object.values(fieldMappings.value).filter(v => v).length === 0) {
    ElMessage.warning('请至少映射一个字段')
    return
  }
  
  if (!excelFile.value) {
    ElMessage.error('文件不存在，请重新上传')
    return
  }
  
  mappingLoading.value = true
  try {
    const templateId = route.params.id as string
    let successCount = 0
    let errorCount = 0
    
    // 创建反向映射：字段名 -> Excel列索引
    const fieldToColIndex = new Map<string, number>()
    excelHeaders.value.forEach((header, index) => {
      const fieldName = fieldMappings.value[header]
      if (fieldName) {
        fieldToColIndex.set(fieldName, index)
      }
    })
    
    // 处理每一行数据
    for (const row of excelRows.value) {
      if (row.length === 0) continue
      
      const data: Record<string, any> = {}
      
      // 根据映射填充数据
      fieldToColIndex.forEach((colIndex, fieldName) => {
        if (colIndex < row.length) {
          data[fieldName] = row[colIndex]
        }
      })
      
      // 提交数据
      try {
        const res: any = await templateAPI.submitData(parseInt(templateId), { data })
        // 后端返回的是 TemplateDataResponse，包含 id 字段
        if (res.id) {
          successCount++
        } else {
          errorCount++
        }
      } catch (e) {
        errorCount++
        console.error('提交失败:', e)
      }
    }
    
    ElMessage.success(`导入完成：成功 ${successCount} 条，失败 ${errorCount} 条`)
    showMappingDialog.value = false
    loadData() // 刷新数据
    
  } catch (e) {
    console.error('导入失败:', e)
    ElMessage.error('导入失败：' + (e as Error).message)
  } finally {
    mappingLoading.value = false
  }
}

// 加载模板和数据
async function loadTemplate() {
  const templateId = route.params.id as string
  if (!templateId) return

  try {
    const res: any = await templateAPI.get(parseInt(templateId))
    // 后端返回的直接是数据对象
    if (res.id) {
      template.value = res
      modules.value = res.modules || []

      // 提取显示字段（排除布局元素）
      const fields: any[] = []
      modules.value.forEach(mod => {
        mod.fields.forEach((field: any) => {
          if (!['divider', 'title', 'description'].includes(field.type)) {
            fields.push({
              ...field,
              hidden: field.type === 'password' || field.type === 'signature' // 隐藏敏感字段
            })
          }
        })
      })
      displayFields.value = fields
    }
  } catch (e) {
    ElMessage.error('加载模板失败')
  }
}

async function loadData() {
  const templateId = route.params.id as string
  if (!templateId) return

  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const res: any = await templateAPI.getData(parseInt(templateId), {
      skip,
      limit: pageSize.value,
      search: searchKeyword.value || undefined
    })

    // 后端返回的是数组
    if (Array.isArray(res)) {
      tableData.value = res.map((item: any) => ({
        id: item.id,
        created_at: item.created_at,
        updated_at: item.updated_at,
        ...(item.config?.data || {})
      }))
      total.value = res.length || 0
    }
  } catch (e) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 事件处理
function handleSelectionChange(val: any[]) {
  multipleSelection.value = val
}

function handleSizeChange(val: number) {
  pageSize.value = val
  loadData()
}

function handleCurrentChange(val: number) {
  currentPage.value = val
  loadData()
}

function doSearch() {
  currentPage.value = 1
  loadData()
}

function goToFormFill() {
  router.push(`/form/${route.params.id}`)
}

function viewDetail(row: any) {
  selectedData.value = row
  showDetailDialog.value = true
}

function editData(row?: any) {
  editMode.value = row ? 'edit' : 'add'
  Object.keys(editForm).forEach(key => delete editForm[key])
  
  if (row) {
    // 编辑模式
    selectedData.value = row
    Object.assign(editForm, row)
  } else {
    // 新增模式
    selectedData.value = null
    // 设置默认值
    displayFields.value.forEach(field => {
      if (field.type === 'checkbox' || field.type === 'tags' || (field.type === 'select' && field.multiple)) {
        editForm[field.name] = field.defaultValue || []
      } else if (field.type === 'switch') {
        editForm[field.name] = field.defaultValue !== undefined ? field.defaultValue : false
      } else if (field.type === 'number') {
        editForm[field.name] = field.defaultValue !== undefined ? Number(field.defaultValue) : undefined
      } else {
        editForm[field.name] = field.defaultValue || ''
      }
    })
  }
  showEditDialog.value = true
}

async function saveData() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const templateId = parseInt(route.params.id as string)
    const dataToSave = { ...editForm }
    
    if (editMode.value === 'edit' && selectedData.value?.id) {
      // 更新
      await templateAPI.updateData(templateId, selectedData.value.id, { data: dataToSave })
      ElMessage.success('更新成功')
    } else {
      // 新增
      await templateAPI.submitData(templateId, { data: dataToSave })
      ElMessage.success('添加成功')
    }
    
    showEditDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteData(row: any) {
  try {
    await ElMessageBox.confirm('确定删除这条数据吗？删除后无法恢复', '确认删除', {
      type: 'warning'
    })
    
    const templateId = parseInt(route.params.id as string)
    await templateAPI.deleteData(templateId, row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    // 用户取消
  }
}

function handleBatchAction(command: string) {
  if (command === 'delete') {
    batchDelete()
  } else if (command === 'exportSelected') {
    exportSelected()
  }
}

async function batchDelete() {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请先选择数据')
    return
  }

  try {
    await ElMessageBox.confirm(`确定删除选中的${multipleSelection.value.length}条数据吗？`, '批量删除', {
      type: 'warning'
    })
    
    const templateId = parseInt(route.params.id as string)
    // 这里需要批量删除API，暂时逐个删除
    for (const row of multipleSelection.value) {
      await templateAPI.deleteData(templateId, row.id)
    }
    
    ElMessage.success(`已删除${multipleSelection.value.length}条数据`)
    loadData()
    multipleSelection.value = []
  } catch (e) {
    // 用户取消
  }
}

// 导出Excel
async function exportExcel() {
  const templateId = route.params.id as string
  
  // 显示加载状态
  ElMessage.info('正在获取导出数据...')
  
  try {
    // 调用后端API获取全部数据
    const res: any = await templateAPI.exportData(parseInt(templateId))
    
    if (!res.data || !Array.isArray(res.data)) {
      ElMessage.error('导出数据获取失败')
      return
    }
    
    const wsData = []

    // 表头
    const headers = ['序号']
    displayFields.value.forEach(field => {
      if (!field.hidden) {
        headers.push(field.label)
      }
    })
    headers.push('提交时间', '最后更新')
    wsData.push(headers)

    // 数据行（使用后端返回的完整数据）
    res.data.forEach((row: any, index: number) => {
      const rowData = [index + 1]
      displayFields.value.forEach(field => {
        if (!field.hidden) {
          const value = row[field.get('label')] || row[field.name]
          if (Array.isArray(value)) {
            rowData.push(value.join(', '))
          } else {
            rowData.push(value || '')
          }
        }
      })
      rowData.push(row._created_at ? formatDateTime(row._created_at) : '', 
                   row._updated_at ? formatDateTime(row._updated_at) : '')
      wsData.push(rowData)
    })

    // 创建 workbook 和 worksheet
    const wb = XLSX.utils.book_new()
    const ws = XLSX.utils.aoa_to_sheet(wsData)

    // 设置列宽
    const colWidths = headers.map((_, idx) => ({ wch: idx === 0 ? 10 : 20 }))
    ws['!cols'] = colWidths

    XLSX.utils.book_append_sheet(wb, ws, '数据')
    const fileName = res.template_name || template.value?.name || '模板数据'
    XLSX.writeFile(wb, `${fileName}_导出数据_${new Date().toISOString().slice(0,10)}.xlsx`)
    ElMessage.success(`成功导出 ${res.data.length} 条数据`)
  } catch (e: any) {
    console.error('导出失败:', e)
    ElMessage.error('导出失败：' + (e.message || '未知错误'))
  }
}

function exportSelected() {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请先选择数据')
    return
  }

  // 导出选中数据，逻辑类似 exportExcel
  const wsData = []
  const headers = ['序号']
  displayFields.value.forEach(field => {
    if (!field.hidden) {
      headers.push(field.label)
    }
  })
  headers.push('提交时间', '最后更新')
  wsData.push(headers)

  multipleSelection.value.forEach((row, index) => {
    const rowData = [index + 1]
    displayFields.value.forEach(field => {
      if (!field.hidden) {
        const value = row[field.name]
        if (Array.isArray(value)) {
          rowData.push(value.join(', '))
        } else {
          rowData.push(value || '')
        }
      }
    })
    rowData.push(formatDateTime(row.created_at), formatDateTime(row.updated_at))
    wsData.push(rowData)
  })

  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet(wsData)
  const colWidths = headers.map((_, idx) => ({ wch: idx === 0 ? 10 : 20 }))
  ws['!cols'] = colWidths

  XLSX.utils.book_append_sheet(wb, ws, '数据')
  XLSX.writeFile(wb, `${template.value.name}_选中数据_${new Date().toISOString().slice(0,10)}.xlsx`)
}

// 导入Excel
function importExcel() {
  // 重置状态
  excelHeaders.value = []
  excelRows.value = []
  fieldMappings.value = {}
  excelFile.value = null
  showImportDialog.value = true
}

function beforeImportUpload(file: File) {
  const isExcel = file.type.includes('excel') || file.type.includes('spreadsheet') ||
    ['.xlsx', '.xls', '.csv'].some(ext => file.name.toLowerCase().endsWith(ext))
  
  if (!isExcel) {
    ElMessage.error('请上传Excel文件（.xlsx, .xls, .csv）')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  
  return true
}

async function handleImportSuccess(response: any, file: File) {
  try {
    if (response.url) {
      // 如果有服务器返回的URL，可以下载解析
      // 目前我们直接在前端解析上传的文件
      ElMessage.success('文件上传成功，正在解析...')
    }
    
    // 保存文件引用
    excelFile.value = file
    
    // 解析Excel文件
    const data = await parseExcelFile(file)
    if (!data) {
      ElMessage.error('Excel文件解析失败')
      return
    }
    
    // 提取表头和数据
    const { headers, rows } = data
    if (headers.length === 0 || rows.length === 0) {
      ElMessage.error('Excel文件数据为空')
      return
    }
    
    // 保存数据
    excelHeaders.value = headers
    excelRows.value = rows
    
    // 自动匹配字段（基于标签）
    const autoMappings: Record<string, string> = {}
    headers.forEach((header, index) => {
      if (header && typeof header === 'string') {
        // 尝试匹配字段标签
        const field = displayFields.value.find(f => 
          f.label === header.trim() || 
          f.name === header.trim().toLowerCase().replace(/\s+/g, '_')
        )
        if (field) {
          autoMappings[header] = field.name
        }
      }
    })
    
    fieldMappings.value = autoMappings
    
    // 关闭上传对话框，打开映射对话框
    showImportDialog.value = false
    showMappingDialog.value = true
    
  } catch (e) {
    console.error('Excel处理错误:', e)
    ElMessage.error('Excel文件处理失败：' + (e as Error).message)
  }
}

// 解析Excel文件
function parseExcelFile(file: File): Promise<{ headers: string[], rows: any[][] }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = e.target?.result
        if (!data) {
          reject(new Error('文件读取失败'))
          return
        }
        
        const workbook = XLSX.read(data, { type: 'binary' })
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
        
        if (jsonData.length < 2) {
          reject(new Error('Excel文件数据为空或格式不正确'))
          return
        }
        
        const headers = jsonData[0] as string[]
        const rows = jsonData.slice(1) as any[][]
        
        resolve({ headers, rows })
      } catch (e) {
        reject(e)
      }
    }
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'))
    }
    
    reader.readAsBinaryString(file)
  })
}

async function confirmImport() {
  // 新流程：如果有上传的文件，解析并显示映射对话框
  if (!uploadRef.value || !uploadRef.value.uploadFiles || uploadRef.value.uploadFiles.length === 0) {
    ElMessage.warning('请先上传Excel文件')
    return
  }

  const file = uploadRef.value.uploadFiles[0].raw
  if (!file) {
    ElMessage.warning('文件不存在')
    return
  }

  try {
    // 解析Excel文件
    const data = await parseExcelFile(file)
    if (!data) {
      ElMessage.error('Excel文件解析失败')
      return
    }
    
    const { headers, rows } = data
    if (headers.length === 0 || rows.length === 0) {
      ElMessage.error('Excel文件数据为空')
      return
    }
    
    // 保存数据
    excelHeaders.value = headers
    excelRows.value = rows
    excelFile.value = file
    
    // 自动匹配字段
    const autoMappings: Record<string, string> = {}
    headers.forEach((header, index) => {
      if (header && typeof header === 'string') {
        const field = displayFields.value.find(f => 
          f.label === header.trim() || 
          f.name === header.trim().toLowerCase().replace(/\s+/g, '_')
        )
        if (field) {
          autoMappings[header] = field.name
        }
      }
    })
    
    fieldMappings.value = autoMappings
    
    // 关闭上传对话框，打开映射对话框
    showImportDialog.value = false
    showMappingDialog.value = true
    
  } catch (e) {
    console.error('Excel处理错误:', e)
    ElMessage.error('Excel文件处理失败：' + (e as Error).message)
  }
}

function refreshData() {
  loadData()
}

function previewFile(url: string) {
  window.open(url, '_blank')
}

function downloadFile(url: string) {
  window.open(url, '_blank')
}

// 监听路由变化
watch(() => route.params.id, () => {
  loadTemplate()
  loadData()
})

onMounted(() => {
  loadTemplate()
  loadData()
})
</script>

<style scoped lang="scss">
.form-data-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.main-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 18px;
      color: #303133;
    }

    .card-actions {
      display: flex;
      gap: 10px;
    }
  }

  .search-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .filter-controls {
      display: flex;
      gap: 10px;
    }
  }

  .pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e4e7ed;
  }
}

.more-tag {
  margin-left: 5px;
  color: #909399;
  font-size: 12px;
}

// 字段映射对话框样式
.mapping-loading {
  padding: 40px;
  text-align: center;
}

.mapping-info {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 4px solid #409eff;
  
  p {
    margin: 8px 0;
    color: #303133;
    font-size: 14px;
    
    &:first-child {
      margin-top: 0;
    }
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.mapping-actions {
  display: flex;
  justify-content: flex-start;
  gap: 12px;
  margin: 20px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}

.mapping-stats {
  margin-top: 16px;
  padding: 12px 16px;
  background: #fff8e6;
  border-radius: 4px;
  border-left: 4px solid #e6a23c;
  
  p {
    margin: 4px 0;
    color: #303133;
    font-size: 14px;
    
    &.warning-text {
      color: #e6a23c;
      font-weight: 500;
    }
  }
}

.preview-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: #606266;
  cursor: help;
}

// 响应式
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;

    .header-actions {
      justify-content: flex-start;
      flex-wrap: wrap;
    }
  }

  .main-card {
    .card-header {
      flex-direction: column;
      align-items: stretch;
      gap: 10px;
    }

    .search-bar {
      flex-direction: column;
      align-items: stretch;
      gap: 10px;

      .el-input {
        width: 100%;
      }

      .filter-controls {
        width: 100%;
        .el-date-editor {
          width: 100%;
        }
      }
    }
  }
}
</style>
