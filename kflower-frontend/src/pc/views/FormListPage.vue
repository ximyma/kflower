<template>
  <div class="form-list-page">
    <div class="page-header">
      <h2>{{ templateData?.name || '数据列表' }}</h2>
      <div class="header-buttons">
        <el-button type="success" @click="openImportDialog">
          <el-icon><Upload /></el-icon> 导入Excel
        </el-button>
        <el-button v-if="isMatrixTemplate" type="primary" @click="createNewMatrix">
          <el-icon><Plus /></el-icon> 新增矩阵数据
        </el-button>
        <el-button v-else type="primary" @click="createNew">
          <el-icon><Plus /></el-icon> 新增
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索..."
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <!-- 普通模板数据表格 -->
      <el-table v-if="!isMatrixTemplate" :data="tableData" border stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column
          v-for="field in displayFields"
          :key="field.name"
          :prop="field.name"
          :label="field.label"
        />
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="viewDataDetail(row)" title="查看">
              <el-icon><View /></el-icon>查看
            </el-button>
            <el-button size="small" type="warning" text @click="editDataItem(row)" title="编辑">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button size="small" type="success" text @click="openFormSubmit(row)" title="填写表单">
              <el-icon><EditPen /></el-icon>填表
            </el-button>
            <el-button size="small" type="info" text @click="openFormList(row)" title="数据列表">
              <el-icon><List /></el-icon>列表
            </el-button>
            <el-button size="small" text @click="openPermissionDialog(row)" title="权限设置">
              <el-icon><Key /></el-icon>权限
            </el-button>
            <el-button size="small" type="danger" text @click="deleteDataItem(row)" title="删除">
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 矩阵模板数据列表 - 每行是一个完整的矩阵数据实例 -->
      <div v-if="isMatrixTemplate" class="matrix-list-container">
        <el-table :data="matrixTableData" border stripe>
          <el-table-column type="index" label="序号" width="60" align="center" />
          <el-table-column label="矩阵数据" min-width="200" align="center">
            <template #default="{ row }">
              <span class="matrix-info">{{ getMatrixInfo(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="提交时间" width="160" align="center">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="viewMatrixData(row)" title="查看">
                <el-icon><View /></el-icon>查看
              </el-button>
              <el-button size="small" type="warning" text @click="editMatrixData(row)" title="编辑">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button size="small" type="danger" text @click="deleteDataItem(row)" title="删除">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 矩阵视图预览（可选显示） -->
        <div v-if="selectedMatrixData && showMatrixPreview" class="matrix-preview">
          <h4>数据预览</h4>
          <MatrixView
            :data="selectedMatrixData.__matrix_data || []"
            :row-dimension-field="'row_dimension'"
            :col-dimension-field="'col_dimension'"
            :value-field="'value'"
            :title="'矩阵数据预览'"
            :row-dimension-label="getFieldByName('row_dimension')?.label || '行维度'"
            :col-dimension-label="getFieldByName('col_dimension')?.label || '列维度'"
            :show-actions="false"
            :show-totals="true"
          />
        </div>
      </div>
  
  <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="showFormDialog" :title="isEditMode ? '编辑数据' : '新增数据'" width="1200px" destroy-on-close>
      <!-- 矩阵模板：根据是否有普通字段，显示不同布局 -->
      <div v-if="isMatrixTemplate">
        <!-- 有普通字段：左侧表单 + 右侧矩阵输入 -->
        <div v-if="hasRegularFields" style="display: flex; gap: 20px;">
          <!-- 左侧：普通字段表单 -->
          <div style="flex: 1; min-width: 300px;">
            <h4 style="margin: 0 0 16px 0;">基本信息</h4>
            <el-form :model="formData" label-width="100px">
              <el-form-item
                v-for="field in regularFields"
                :key="field.name"
                :label="field.label"
                :required="field.required"
              >
                <el-input
                  v-if="field.type === 'text' || field.type === 'phone' || field.type === 'email'"
                  v-model="formData[field.name]"
                  :placeholder="field.placeholder || `请输入${field.label}`"
                />
                <el-input-number
                  v-else-if="field.type === 'number' || field.type === 'money' || field.type === 'percent'"
                  v-model="formData[field.name]"
                  :placeholder="field.placeholder || `请输入${field.label}`"
                  :precision="field.type === 'percent' ? 2 : 0"
                  style="width: 100%;"
                />
                <el-date-picker
                  v-else-if="field.type === 'date'"
                  v-model="formData[field.name]"
                  type="date"
                  :placeholder="field.placeholder || `请选择${field.label}`"
                  value-format="YYYY-MM-DD"
                  style="width: 100%;"
                />
                <el-select
                  v-else-if="field.type === 'select'"
                  v-model="formData[field.name]"
                  :placeholder="field.placeholder || `请选择${field.label}`"
                  style="width: 100%;"
                  clearable
                >
                  <el-option
                    v-for="opt in (field.options || [])"
                    :key="opt.value || opt"
                    :label="opt.label || opt"
                    :value="opt.value || opt"
                  />
                </el-select>
                <el-input
                  v-else-if="field.type === 'textarea'"
                  v-model="formData[field.name]"
                  type="textarea"
                  :rows="3"
                  :placeholder="field.placeholder || `请输入${field.label}`"
                />
                <el-input
                  v-else
                  v-model="formData[field.name]"
                  :placeholder="field.placeholder || `请输入${field.label}`"
                />
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 右侧：矩阵输入组件 -->
          <div style="flex: 2;">
            <MatrixInput
              ref="matrixInputRef"
              :row-options="getFieldByName('row_dimension')?.options || []"
              :col-options="getFieldByName('col_dimension')?.options || []"
              :title="isEditMode ? '编辑矩阵数据' : '录入矩阵数据'"
              :value-field-type="getFieldByName('value')?.type || 'number'"
              :value-options="getFieldByName('value')?.options || []"
              :show-add-row="true"
              :show-add-col="true"
              :show-edit-row="true"
              :show-edit-col="true"
              :show-totals="true"
              :show-row-totals="true"
              @add-row="addMatrixRow"
              @add-column="addMatrixColumn"
              @remove-row="removeMatrixRow"
              @remove-column="removeMatrixColumn"
            />
          </div>
        </div>
        
        <!-- 无普通字段：只显示矩阵输入 -->
        <MatrixInput
          v-else
          ref="matrixInputRef"
          :row-options="getFieldByName('row_dimension')?.options || []"
          :col-options="getFieldByName('col_dimension')?.options || []"
          :title="isEditMode ? '编辑矩阵数据' : '录入矩阵数据'"
          :value-field-type="getFieldByName('value')?.type || 'number'"
          :value-options="getFieldByName('value')?.options || []"
          :show-add-row="true"
          :show-add-col="true"
          :show-edit-row="true"
          :show-edit-col="true"
          :show-totals="true"
          :show-row-totals="true"
          @add-row="addMatrixRow"
          @add-column="addMatrixColumn"
          @remove-row="removeMatrixRow"
          @remove-column="removeMatrixColumn"
          style="margin: 16px 0;"
        />
      </div>
      
      <!-- 普通表单录入（非矩阵模板） -->
      <el-form v-else :model="formData" label-width="120px">
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
          
          <!-- 其他字段类型... -->
          <el-input-number
            v-else-if="field.type === 'number' || field.type === 'money' || field.type === 'percent'"
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
            :precision="field.type === 'percent' ? 2 : 0"
            style="width: 100%;"
          />
          
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="formData[field.name]"
            type="date"
            :placeholder="field.placeholder || `请选择${field.label}`"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
          
          <el-select
            v-else-if="field.type === 'select'"
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请选择${field.label}`"
            style="width: 100%;"
            clearable
          >
            <el-option
              v-for="opt in (field.options || [])"
              :key="opt.value || opt"
              :label="opt.label || opt"
              :value="opt.value || opt"
            />
          </el-select>
          
          <el-radio-group v-else-if="field.type === 'radio'" v-model="formData[field.name]">
            <el-radio v-for="opt in (field.options || [])" :key="opt.value || opt" :label="opt.value || opt">
              {{ opt.label || opt }}
            </el-radio>
          </el-radio-group>
          
          <el-checkbox-group v-else-if="field.type === 'checkbox'" v-model="formData[field.name]">
            <el-checkbox v-for="opt in (field.options || [])" :key="opt.value || opt" :label="opt.value || opt">
              {{ opt.label || opt }}
            </el-checkbox>
          </el-checkbox-group>
          
          <el-switch v-else-if="field.type === 'switch'" v-model="formData[field.name]" />
          
          <el-input
            v-else-if="field.type === 'textarea'"
            v-model="formData[field.name]"
            type="textarea"
            :rows="4"
            :placeholder="field.placeholder || `请输入${field.label}`"
          />
          
          <el-input
            v-else
            v-model="formData[field.name]"
            :placeholder="field.placeholder || `请输入${field.label}`"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveFormData">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="数据详情" width="600px" destroy-on-close>
      <el-form :model="detailData" label-width="120px">
        <el-form-item
          v-for="field in formFields"
          :key="field.name"
          :label="field.label"
        >
          <span>{{ detailData[field.name] ?? '-' }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 填写数据弹窗（矩阵模板使用矩阵录入，普通模板使用普通表单） -->
    <el-dialog v-model="showDataForm" :title="'填写数据 - ' + (templateData?.name || '')" width="900px" destroy-on-close>
      <!-- 矩阵表格录入（矩阵模板） -->
      <MatrixInput
        v-if="isMatrixTemplate"
        ref="matrixInputRef2"
        :row-options="getFieldByName('row_dimension')?.options || []"
        :col-options="getFieldByName('col_dimension')?.options || []"
        :title="'填写矩阵数据'"
        :value-field-type="getFieldByName('value')?.type || 'number'"
        :value-options="getFieldByName('value')?.options || []"
        :show-add-row="true"
        :show-add-col="true"
        :show-edit-row="true"
        :show-edit-col="true"
        :show-totals="true"
        :show-row-totals="true"
        style="margin: 16px 0;"
      />
      
      <!-- 普通表单录入（非矩阵模板） -->
      <el-form v-else :model="dataFormData" label-width="120px">
        <template v-for="f in formFields" :key="f.name">
          <el-form-item :label="f.label + (f.required ? ' *' : '')" :required="f.required">
            <el-input v-if="['text','email','phone','url','password'].includes(f.type)" v-model="dataFormData[f.name]" :placeholder="f.placeholder || ('请输入' + f.label)" />
            <el-input v-else-if="f.type === 'textarea'" type="textarea" v-model="dataFormData[f.name]" :placeholder="f.placeholder || ('请输入' + f.label)" :rows="3" />
            <el-input-number v-else-if="['number','money','percent'].includes(f.type)" v-model="dataFormData[f.name]" :min="f.min || 0" :max="f.max || 999999999" style="width:100%" />
            <el-select v-else-if="['select','radio'].includes(f.type)" v-model="dataFormData[f.name]" placeholder="请选择" style="width:100%">
              <el-option v-for="opt in (f.options || [])" :key="opt" :label="opt" :value="opt" />
            </el-select>
            <el-date-picker v-else-if="f.type === 'date'" v-model="dataFormData[f.name]" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" />
            <el-date-picker v-else-if="f.type === 'datetime'" v-model="dataFormData[f.name]" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" placeholder="选择日期时间" style="width:100%" />
            <el-switch v-else-if="f.type === 'switch'" v-model="dataFormData[f.name]" />
            <el-checkbox-group v-else-if="f.type === 'checkbox'" v-model="dataFormData[f.name]">
              <el-checkbox v-for="opt in (f.options || [])" :key="opt" :label="opt">{{ opt }}</el-checkbox>
            </el-checkbox-group>
            <el-rate v-else-if="f.type === 'rate'" v-model="dataFormData[f.name]" />
            <span v-else>{{ dataFormData[f.name] || '-' }}</span>
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="showDataForm = false">取消</el-button>
        <el-button type="primary" :loading="dataFormLoading" @click="submitDataForm">提交数据</el-button>
      </template>
    </el-dialog>

    <!-- 矩阵查看弹窗 -->
    <el-dialog v-model="showMatrixViewDialog" :title="'查看矩阵数据 - ' + (templateData?.name || '')" width="90%" destroy-on-close>
      <MatrixView
        v-if="selectedMatrixData"
        :data="selectedMatrixData.__matrix_data || []"
        :row-dimension-field="'row_dimension'"
        :col-dimension-field="'col_dimension'"
        :value-field="'value'"
        :title="templateData?.name || '矩阵数据'"
        :row-dimension-label="getFieldByName('row_dimension')?.label || '行维度'"
        :col-dimension-label="getFieldByName('col_dimension')?.label || '列维度'"
        :show-actions="false"
        :show-totals="true"
      />
      <div v-else class="empty-matrix">
        <el-empty description="暂无数据" />
      </div>
      <template #footer>
        <el-button @click="showMatrixViewDialog = false">关闭</el-button>
        <el-button type="primary" @click="() => { showMatrixViewDialog = false; editMatrixData(selectedMatrixData) }">
          编辑
        </el-button>
      </template>
    </el-dialog>

    <!-- 权限设置弹窗 -->
    <el-dialog v-model="showPermissionDialog" :title="'权限设置 - ' + (templateData?.name || '')" width="550px">
      <el-form label-width="90px">
        <el-form-item label="模板名称">
          <span style="font-weight:500">{{ templateData?.name }}</span>
        </el-form-item>
        <el-form-item label="访问权限">
          <el-radio-group v-model="permForm.is_public">
            <el-radio :label="false">私有（仅自己可见）</el-radio>
            <el-radio :label="true">公开（所有用户可见）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="说明">
          <div style="color: var(--el-text-color-secondary);font-size:12px;line-height:1.6">
            <p>• <strong>私有</strong>：只有创建者可以看到和使用</p>
            <p>• <strong>公开</strong>：组织内所有用户都可以看到和使用</p>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPermissionDialog = false">取消</el-button>
        <el-button type="primary" :loading="permLoading" @click="savePermission">保存</el-button>
      </template>
    </el-dialog>

    <!-- Excel导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="导入Excel数据" width="900px" destroy-on-close>
      <div class="import-steps">
        <el-steps :active="importStep" finish-status="success" style="margin-bottom:24px">
          <el-step title="上传文件" />
          <el-step title="映射字段" />
          <el-step title="导入数据" />
        </el-steps>

        <!-- 步骤1: 上传文件 -->
        <div v-if="importStep === 0">
          <el-upload
            ref="importUploadRef"
            class="import-uploader"
            drag
            accept=".xlsx,.xls,.csv"
            :auto-upload="false"
            :limit="1"
            :on-change="handleImportFileChange"
            :on-exceed="handleImportExceed"
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">将Excel文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .xlsx, .xls, .csv 格式</div>
            </template>
          </el-upload>

          <div v-if="importPreviewData.length > 0" style="margin-top:20px">
            <h4>文件预览（前5行）：</h4>
            <el-table :data="importPreviewData" border size="small" max-height="300">
              <el-table-column
                v-for="(col, idx) in importColumns"
                :key="idx"
                :prop="col"
                :label="'列' + (idx + 1) + ': ' + col"
                show-overflow-tooltip
              />
            </el-table>
            <el-button type="primary" style="margin-top:16px" @click="startFieldMapping">下一步：映射字段</el-button>
          </div>
        </div>

        <!-- 步骤2: 映射字段 -->
        <div v-else-if="importStep === 1">
          <el-alert type="info" :closable="false" style="margin-bottom:20px">
            请将Excel列映射到表单字段。不映射的列将被忽略。
          </el-alert>
          
          <div class="field-mapping-container">
            <div class="mapping-header">
              <span class="mapping-col">Excel列</span>
              <span class="mapping-arrow">→</span>
              <span class="mapping-col">表单字段</span>
            </div>
            <div v-for="(col, idx) in importColumns" :key="idx" class="mapping-row">
              <span class="mapping-col">{{ col }}</span>
              <span class="mapping-arrow">→</span>
              <el-select v-model="fieldMapping[idx]" placeholder="请选择字段" clearable style="flex:1">
                <el-option
                  v-for="field in formFields"
                  :key="field.name"
                  :label="field.label"
                  :value="field.name"
                />
              </el-select>
            </div>
          </div>

          <div style="margin-top:20px;text-align:right">
            <el-button @click="importStep = 0">上一步</el-button>
            <el-button type="primary" :disabled="!hasMapping" @click="confirmImport">确认导入</el-button>
          </div>
        </div>

        <!-- 步骤3: 导入进度 -->
        <div v-else-if="importStep === 2">
          <el-result
            :icon="importResult.success ? 'success' : 'error'"
            :title="importResult.success ? '导入成功' : '导入失败'"
            :sub-title="importResult.message"
          >
            <template #extra>
              <p v-if="importResult.errors && importResult.errors.length > 0">
                <el-alert type="warning" :closable="false">
                  <template #default>
                    <div>部分数据导入失败：</div>
                    <ul style="margin:8px 0 0 0;padding-left:20px">
                      <li v-for="(err, idx) in importResult.errors.slice(0, 5)" :key="idx">{{ err }}</li>
                    </ul>
                  </template>
                </el-alert>
              </p>
              <el-button type="primary" @click="closeImportDialog">完成</el-button>
            </template>
          </el-result>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, reactive, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, View, Edit, EditPen, List, Key, Delete, Upload, InfoFilled
} from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { templateAPI } from '@/common/api/index'

// 导入矩阵组件
import MatrixView from '@/pc/components/MatrixView.vue'
import MatrixInput from '@/pc/components/MatrixInput.vue'

const route = useRoute()
const router = useRouter()

// 兼容两种路由格式：
// 1. /form/:id （独立路由 FormList）
// 2. /app/:appId/form/:templateId （应用内路由 AppFormList）
const appId = ref<number | null>(route.params.appId ? Number(route.params.appId) : null)
const templateId = ref(Number(route.params.templateId || route.params.id))


const templateData = ref<any>(null)
const tableData = ref<any[]>([])
const displayFields = ref<any[]>([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 矩阵输入组件引用
const matrixInputRef = ref<any>(null)  // 用于 showFormDialog 弹窗
const matrixInputRef2 = ref<any>(null)  // 用于 showDataForm 弹窗

// 表单弹窗
const showFormDialog = ref(false)
const isEditMode = ref(false)
const editDataId = ref<number | null>(null)
const formFields = ref<any[]>([])
const formData = ref<Record<string, any>>({})
const saving = ref(false)

// 查看详情弹窗
const showDetailDialog = ref(false)
const detailData = ref<Record<string, any>>({})

// 填写数据弹窗
const showDataForm = ref(false)
const dataFormData = reactive<Record<string, any>>({})
const dataFormLoading = ref(false)

// 矩阵表格相关
// 判断是否为矩阵模板：优先检查 config.matrix_template 标记，其次检查字段名
const isMatrixTemplate = computed(() => {
  // 1. 优先使用 config 标记判断（创建矩阵模板时设置的标记）
  if (templateData.value?.config?.matrix_template === true) {
    return true
  }
  // 2. 兼容旧逻辑：检查是否包含矩阵特征字段
  if (!formFields.value || formFields.value.length === 0) return false
  const fieldNames = formFields.value.map(f => f.name)
  return fieldNames.includes('row_dimension') &&
         fieldNames.includes('col_dimension') &&
         fieldNames.includes('value')
})

// 判断是否有普通字段（非矩阵字段）
const hasRegularFields = computed(() => {
  if (!isMatrixTemplate.value) return true
  const matrixFieldNames = ['row_dimension', 'col_dimension', 'value']
  return formFields.value.some(f => !matrixFieldNames.includes(f.name))
})

// 获取普通字段（非矩阵字段）
const regularFields = computed(() => {
  if (!isMatrixTemplate.value) return formFields.value
  const matrixFieldNames = ['row_dimension', 'col_dimension', 'value']
  return formFields.value.filter(f => !matrixFieldNames.includes(f.name))
})

// 矩阵表格相关属性
const showMatrixView = ref(true)  // 控制矩阵视图显示
const showMatrixInput = ref(false)  // 控制矩阵录入显示
const showMatrixViewDialog = ref(false)  // 查看矩阵数据弹窗
const selectedMatrixData = ref<any>(null)  // 选中的矩阵数据
const showMatrixPreview = ref(false)  // 显示矩阵预览

// 矩阵数据列表 - 解析每行数据中的矩阵信息
const matrixTableData = computed(() => {
  if (!isMatrixTemplate.value) return []
  
  return tableData.value.map(row => {
    // 解析 __matrix_data 字段（可能存储为 JSON 字符串或数组）
    let matrixData = []
    if (row.__matrix_data) {
      if (typeof row.__matrix_data === 'string') {
        try {
          matrixData = JSON.parse(row.__matrix_data)
        } catch {
          matrixData = []
        }
      } else {
        matrixData = row.__matrix_data
      }
    }
    
    return {
      ...row,
      __matrix_data: matrixData
    }
  })
})

// 获取矩阵数据的简要信息
function getMatrixInfo(row: any) {
  const data = row.__matrix_data || []
  if (data.length === 0) return '（空数据）'
  
  const rowField = getFieldByName('row_dimension')
  const colField = getFieldByName('col_dimension')
  
  const rowCount = new Set(data.map((d: any) => d.row_dimension)).size
  const colCount = new Set(data.map((d: any) => d.col_dimension)).size
  
  return `${rowCount}行 × ${colCount}列，共 ${data.length} 个数据点`
}

// ========== 矩阵模板操作函数 ==========

// 查看矩阵数据
function viewMatrixData(row: any) {
  selectedMatrixData.value = row
  showMatrixViewDialog.value = true
}

// 编辑矩阵数据
function editMatrixData(row: any) {
  isEditMode.value = true
  editDataId.value = row.id
  selectedMatrixData.value = row
  
  // 初始化表单数据
  initFormData()
  
  // 填充普通字段数据（排除矩阵字段）
  const matrixFieldNames = ['row_dimension', 'col_dimension', 'value', '__matrix_data']
  formFields.value.forEach((field: any) => {
    if (!matrixFieldNames.includes(field.name) && row[field.name] !== undefined) {
      formData.value[field.name] = row[field.name]
    }
  })
  
  // 显示弹窗
  showFormDialog.value = true
  
  // 在下一个 tick 设置矩阵数据
  nextTick(() => {
    matrixInputRef.value?.setData(row.__matrix_data || [])
  })
}

// 新增矩阵数据
function createNewMatrix() {
  console.log('createNewMatrix called')
  try {
    isEditMode.value = false
    editDataId.value = null
    selectedMatrixData.value = null
    
    // 初始化表单数据
    initFormData()
    
    // 显示弹窗
    showFormDialog.value = true
    
    // 在下一个 tick 初始化空矩阵
    nextTick(() => {
      matrixInputRef.value?.setData([])
    })
    
    console.log('showFormDialog set to true')
  } catch (e) {
    console.error('Error in createNewMatrix:', e)
    ElMessage.error('打开矩阵编辑失败：' + (e.message || e))
  }
}

// 权限设置弹窗
const showPermissionDialog = ref(false)
const permForm = reactive({ is_public: false })
const permLoading = ref(false)

// Excel导入相关
const showImportDialog = ref(false)
const importStep = ref(0)
const importFile = ref<File | null>(null)
const importColumns = ref<string[]>([])
const importPreviewData = ref<any[]>([])
const importAllData = ref<any[]>([])
const fieldMapping = reactive<Record<number, string>>({})
const importResult = reactive({ success: false, message: '', errors: [] as string[] })
const importUploadRef = ref()

// 计算属性：是否有字段映射
const hasMapping = computed(() => {
  return Object.values(fieldMapping).some(v => v)
})

// 加载模板数据
async function loadTemplate() {
  try {
    const res: any = await templateAPI.get(templateId.value)
    // 解析 config（可能是 JSON 字符串）
    if (typeof res.config === 'string') {
      try { res.config = JSON.parse(res.config) } catch {}
    }
    templateData.value = res
    
    // 提取字段（从 modules 中）
    const modules = res.modules || []
    displayFields.value = []
    formFields.value = []
    for (const mod of modules) {
      if (mod.fields) {
        displayFields.value.push(...mod.fields.map((f: any) => ({
          name: f.name,
          label: f.label,
          type: f.type
        })))
        formFields.value.push(...mod.fields)
      }
    }
  } catch (e: any) {
    ElMessage.error('加载模板失败：' + (e.message || ''))
  }
}

// 根据字段名获取字段
function getFieldByName(name: string) {
  return formFields.value.find(f => f.name === name)
}

// 加载数据
async function loadData() {
  try {
    const res: any = await templateAPI.getData(templateId.value, {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchKeyword.value
    })
    tableData.value = res.items || res
    total.value = res.total || tableData.value.length
  } catch (e: any) {
    ElMessage.error('加载数据失败：' + (e.message || ''))
  }
}

// 监听路由变化，重新加载数据
watch(() => route.params.templateId, (newId) => {
  if (newId) {
    templateId.value = Number(newId)
    loadTemplate()
    loadData()
  }
})

// 搜索
function handleSearch() {
  currentPage.value = 1
  loadData()
}

// 初始化表单数据
function initFormData() {
  Object.keys(formData.value).forEach(k => delete formData.value[k])
  formFields.value.forEach((field: any) => {
    if (field.type === 'checkbox') {
      formData.value[field.name] = []
    } else if (field.type === 'switch') {
      formData.value[field.name] = false
    } else if (field.type === 'number' || field.type === 'money' || field.type === 'percent') {
      formData.value[field.name] = field.defaultValue !== undefined ? Number(field.defaultValue) : null
    } else {
      formData.value[field.name] = field.defaultValue || ''
    }
  })
}

// 新增
function createNew() {
  isEditMode.value = false
  editDataId.value = null
  initFormData()
  showFormDialog.value = true
}

// 查看详情
function viewDataDetail(row: any) {
  Object.keys(detailData.value).forEach(k => delete detailData.value[k])
  formFields.value.forEach((field: any) => {
    detailData.value[field.name] = row[field.name] ?? (field.type === 'checkbox' ? [] : '')
  })
  showDetailDialog.value = true
}

// 编辑
function editDataItem(row: any) {
  isEditMode.value = true
  editDataId.value = row.id
  initFormData()
  // 填充已有数据
  formFields.value.forEach((field: any) => {
    if (row[field.name] !== undefined) {
      formData.value[field.name] = row[field.name]
    }
  })
  showFormDialog.value = true
}

// 保存表单数据
async function saveFormData() {
  saving.value = true
  try {
    let submitData = { ...formData.value }
    
    // 如果是矩阵表格，从 MatrixInput 组件获取数据
    if (isMatrixTemplate.value) {
      const matrixData = matrixInputRef.value?.getData() || []
      if (matrixData.length === 0) {
        ElMessage.warning('没有矩阵数据')
        saving.value = false
        return
      }
      // 合并普通字段数据和矩阵数据
      submitData = { 
        ...formData.value,
        __matrix_data: matrixData 
      }
    }
    
    if (isEditMode.value && editDataId.value) {
      await templateAPI.updateData(templateId.value, editDataId.value, submitData)
      ElMessage.success('更新成功')
    } else {
      await templateAPI.submitData(templateId.value, submitData)
      ElMessage.success('创建成功')
    }
    showFormDialog.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    saving.value = false
  }
}

// 矩阵表格：添加行
async function addMatrixRow() {
  try {
    const rowField = formFields.value.find(f => f.name === 'row_dimension')
    if (rowField) {
      const newLabel = `新行${(rowField.options?.length || 0) + 1}`
      if (!rowField.options) rowField.options = []
      rowField.options.push({ label: newLabel, value: newLabel })
      ElMessage.success(`已添加行：${newLabel}`)
    }
  } catch (e: any) {
    ElMessage.error('添加行失败：' + e.message)
  }
}

// 矩阵表格：添加列
async function addMatrixColumn() {
  try {
    const colField = formFields.value.find(f => f.name === 'col_dimension')
    if (colField) {
      const newLabel = `新列${(colField.options?.length || 0) + 1}`
      if (!colField.options) colField.options = []
      colField.options.push({ label: newLabel, value: newLabel })
      ElMessage.success(`已添加列：${newLabel}`)
    }
  } catch (e: any) {
    ElMessage.error('添加列失败：' + e.message)
  }
}

// 矩阵表格：删除行
async function removeMatrixRow(rowIdx: number) {
  try {
    const rowField = formFields.value.find(f => f.name === 'row_dimension')
    if (rowField && rowField.options && rowField.options.length > 1) {
      const removed = rowField.options.splice(rowIdx, 1)
      ElMessage.success(`已删除行：${removed[0]?.label || ''}`)
    }
  } catch (e: any) {
    ElMessage.error('删除行失败：' + e.message)
  }
}

// 矩阵表格：删除列
async function removeMatrixColumn(colIdx: number) {
  try {
    const colField = formFields.value.find(f => f.name === 'col_dimension')
    if (colField && colField.options && colField.options.length > 1) {
      const removed = colField.options.splice(colIdx, 1)
      ElMessage.success(`已删除列：${removed[0]?.label || ''}`)
    }
  } catch (e: any) {
    ElMessage.error('删除列失败：' + e.message)
  }
}

// 删除
async function deleteDataItem(row: any) {
  try {
    await ElMessageBox.confirm('确定删除该条数据？', '删除确认', { type: 'warning' })
    await templateAPI.deleteData(templateId.value, row.id)
    ElMessage.success('数据已删除')
    loadData()
  } catch {}
}

// 填写表单
function openFormSubmit(row: any) {
  Object.keys(dataFormData).forEach(k => delete dataFormData[k])
  formFields.value.forEach((f: any) => {
    if (f.type === 'checkbox') {
      dataFormData[f.name] = []
    } else if (f.type === 'switch') {
      dataFormData[f.name] = false
    } else if (f.type === 'rate') {
      dataFormData[f.name] = 0
    } else {
      dataFormData[f.name] = f.defaultValue || ''
    }
  })
  
  // 如果是矩阵模板，初始化矩阵录入数据
  if (isMatrixTemplate.value) {
    nextTick(() => {
      matrixInputRef2.value?.setData([])
    })
  }
  
  showDataForm.value = true
}

// 提交表单数据
async function submitDataForm() {
  dataFormLoading.value = true
  try {
    let submitData = { ...dataFormData }
    
    // 如果是矩阵模板，从 MatrixInput 组件获取数据
    if (isMatrixTemplate.value) {
      const matrixData = matrixInputRef2.value?.getData() || []
      if (matrixData.length === 0) {
        ElMessage.warning('没有矩阵数据')
        dataFormLoading.value = false
        return
      }
      submitData = { __matrix_data: matrixData }
    }
    
    await templateAPI.submitData(templateId.value, submitData)
    ElMessage.success('数据提交成功！')
    showDataForm.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    dataFormLoading.value = false
  }
}

// ========== Excel导入相关方法 ==========

// 打开导入对话框
function openImportDialog() {
  showImportDialog.value = true
  importStep.value = 0
  importFile.value = null
  importColumns.value = []
  importPreviewData.value = []
  importAllData.value = []
  Object.keys(fieldMapping).forEach(k => delete fieldMapping[k])
  importResult.success = false
  importResult.message = ''
  importResult.errors = []
}

// 处理文件上传
function handleImportFileChange(uploadFile: any) {
  const file = uploadFile.raw
  if (!file) return

  importFile.value = file

  // 使用XLSX解析Excel文件
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = e.target?.result
      const workbook = XLSX.read(data, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]
      
      // 转换为JSON数据
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      if (jsonData.length < 2) {
        ElMessage.warning('Excel文件至少需要有标题行和一行数据')
        return
      }
      
      // 第一行为列名
      const columns = jsonData[0] as string[]
      importColumns.value = columns.map((col, idx) => col || `列${idx + 1}`)
      
      // 解析所有数据（跳过标题行）
      const allRows = jsonData.slice(1).map((row: any) => {
        const obj: Record<string, any> = {}
        importColumns.value.forEach((col, idx) => {
          obj[col] = row[idx]
        })
        return obj
      })
      
      importAllData.value = allRows
      importPreviewData.value = allRows.slice(0, 5)
      
      ElMessage.success(`成功解析 ${allRows.length} 行数据`)
    } catch (err: any) {
      ElMessage.error('解析Excel文件失败：' + (err.message || '未知错误'))
    }
  }
  
  reader.readAsArrayBuffer(file)
}

// 文件超出限制
function handleImportExceed() {
  ElMessage.warning('一次只能上传一个文件')
}

// 开始字段映射
function startFieldMapping() {
  if (importAllData.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }
  
  // 尝试自动映射（根据列名和字段标签匹配）
  importColumns.value.forEach((col, idx) => {
    const matchedField = formFields.value.find(f => 
      f.label === col || f.name === col
    )
    if (matchedField) {
      fieldMapping[idx] = matchedField.name
    }
  })
  
  importStep.value = 1
}

// 确认导入
async function confirmImport() {
  if (!hasMapping.value) {
    ElMessage.warning('请至少映射一个字段')
    return
  }
  
  try {
    // 构建导入数据（将Excel列映射到表单字段）
    const dataToImport = importAllData.value.map(row => {
      const mapped: Record<string, any> = {}
      Object.entries(fieldMapping).forEach(([colIdx, fieldName]) => {
        if (fieldName) {
          let value = row[importColumns.value[Number(colIdx)]]
          
          // 根据字段类型进行类型转换
          const field = formFields.value.find(f => f.name === fieldName)
          if (field) {
            if (['number', 'money', 'percent'].includes(field.type)) {
              // 数字类型：转换为数字
              value = value ? Number(value) : null
            } else if (field.type === 'switch') {
              // 开关类型：转换为布尔值
              value = value ? true : false
            } else if (field.type === 'date' || field.type === 'datetime') {
              // 日期类型：转换为字符串
              if (value instanceof Date) {
                value = value.toISOString().split('T')[0]
              } else if (typeof value === 'string') {
                value = value.trim()
              }
            } else if (field.type === 'checkbox') {
              // 多选类型：转换为数组
              if (typeof value === 'string') {
                value = value.split(',').map(s => s.trim()).filter(Boolean)
              } else if (!Array.isArray(value)) {
                value = value ? [value] : []
              }
            }
          }
          
          mapped[fieldName] = value
        }
      })
      return mapped
    })
    
    // 调用导入API
    const res = await templateAPI.importData(templateId.value, dataToImport)
    
    importResult.success = res.success || true
    importResult.message = res.message || `成功导入 ${res.imported || 0} 条数据`
    importResult.errors = res.errors || []
    importStep.value = 2
    
    // 刷新列表
    if (importResult.success) {
      loadData()
    }
  } catch (e: any) {
    importResult.success = false
    importResult.message = '导入失败：' + (e.message || '未知错误')
    importResult.errors = []
    importStep.value = 2
  }
}

// 关闭导入对话框
function closeImportDialog() {
  showImportDialog.value = false
  if (importResult.success) {
    loadData()
  }
}

// 打开数据列表
function openFormList(row: any) {
  router.push(`/form/${templateId.value}/data`)
}

// 打开权限设置弹窗
function openPermissionDialog(row: any) {
  permForm.is_public = row.is_public ?? false
  showPermissionDialog.value = true
}

// 保存权限设置
async function savePermission() {
  permLoading.value = true
  try {
    await templateAPI.update(templateId.value, { is_public: permForm.is_public })
    ElMessage.success('权限保存成功')
    showPermissionDialog.value = false
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    permLoading.value = false
  }
}

// 格式化时间
function formatDateTime(s: string | null): string {
  if (!s) return '-'
  const d = new Date(s)
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

onMounted(() => {
  loadTemplate()
  loadData()
})
</script>

<style scoped lang="scss">
.form-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.search-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.import-uploader {
  .el-upload__tip {
    text-align: center;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}

.import-steps {
  margin-bottom: 24px;
}

.field-mapping-container {
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

.mapping-header, .mapping-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
  
  &:not(:last-child) {
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
}

.mapping-header {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.mapping-col {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mapping-arrow {
  width: 40px;
  text-align: center;
  color: var(--el-color-primary);
  font-weight: bold;
}

// 矩阵相关样式
.matrix-container {
  width: 100%;
}

.matrix-list-container {
  width: 100%;
  
  .matrix-info {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
}

.matrix-preview {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  
  h4 {
    margin: 0 0 12px 0;
    color: var(--el-text-color-primary);
  }
}

.matrix-edit-container {
  .matrix-tip {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: var(--el-color-primary-light-9);
    border-radius: 4px;
    color: var(--el-color-primary);
    font-size: 14px;
  }
}

.empty-matrix {
  padding: 40px 0;
}
</style>
