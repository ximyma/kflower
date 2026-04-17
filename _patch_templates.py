# -*- coding: utf-8 -*-
import re

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. Add Upload icon to imports
if 'Upload,' not in content:
    old_import = "import {\n  Plus, Edit, Delete, MagicStick, Document, Search, ArrowDown, ArrowUp,"
    new_import = "import {\n  Plus, Edit, Delete, MagicStick, Document, Search, ArrowDown, ArrowUp, Upload,"
    content = content.replace(old_import, new_import)

# 2. Add import button next to AI button
old_header_btn = '''          <el-button @click="showAIHelper = true">
            <el-icon><MagicStick /></el-icon> AI 设计
          </el-button>'''
new_header_btn = '''          <el-button @click="showImport = true">
            <el-icon><Upload /></el-icon> 导入文件
          </el-button>
          <el-button @click="showAIHelper = true">
            <el-icon><MagicStick /></el-icon> AI 设计
          </el-button>'''
content = content.replace(old_header_btn, new_header_btn)

# 3. Add import dialog before AI dialog
import_dialog = '''
    <!-- 导入Excel/图片弹窗 -->
    <el-dialog v-model="showImport" title="导入Excel或图片生成表单" width="900px" destroy-on-close>
      <div class="import-container">
        <el-steps :active="importStep" finish-status="success" style="margin-bottom:24px">
          <el-step title="上传文件" />
          <el-step title="预览数据" />
          <el-step title="调整字段" />
          <el-step title="创建模板" />
        </el-steps>

        <!-- 步骤1: 上传 -->
        <div v-if="importStep === 0">
          <el-upload
            class="import-uploader"
            drag
            :limit="1"
            accept=".xlsx,.xls,.csv,.png,.jpg,.jpeg,.bmp"
            :auto-upload="false"
            :on-change="onImportFileChange"
            ref="uploadRef"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">
              <p>拖拽文件到此处，或 <em>点击选择</em></p>
              <p class="upload-hint">支持 Excel (.xlsx/.xls/.csv) 和图片 (.png/.jpg/.jpeg)</p>
            </div>
          </el-upload>
          <div class="upload-examples">
            <span>快速示例：</span>
            <el-tag @click="loadSampleData('supplier')">供应商信息表</el-tag>
            <el-tag @click="loadSampleData('employee')">员工入职表</el-tag>
            <el-tag @click="loadSampleData('customer')">客户登记表</el-tag>
          </div>
        </div>

        <!-- 步骤2: 预览数据 -->
        <div v-if="importStep === 1">
          <el-alert :title="`已识别 ${importData.total_rows} 行 × ${importData.total_columns} 列`" type="success" show-icon />
          <div class="preview-actions">
            <el-button @click="importStep = 0">重新上传</el-button>
            <el-button type="primary" @click="importStep = 2">下一步：调整字段</el-button>
          </div>
          <el-table :data="importData.rows" border size="small" max-height="300" style="margin-top:12px">
            <el-table-column v-for="(h, idx) in importData.headers" :key="idx" :prop="String(idx)" :label="h" min-width="120" show-overflow-tooltip />
          </el-table>
        </div>

        <!-- 步骤3: 调整字段 -->
        <div v-if="importStep === 2">
          <div class="field-adjust-header">
            <span>识别到 <strong>{{ importFields.length }}</strong> 个字段，可手动调整：</span>
            <el-button size="small" @click="detectFieldTypes">重新识别类型</el-button>
          </div>
          <el-table :data="importFields" border size="small" style="margin-top:12px">
            <el-table-column label="序号" width="60" type="index" />
            <el-table-column label="原始表头" prop="label" min-width="140" />
            <el-table-column label="显示名称" min-width="140">
              <template #default="{ row }">
                <el-input v-model="row.label" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="字段标识" width="140">
              <template #default="{ row }">
                <el-input v-model="row.name" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="控件类型" width="140">
              <template #default="{ row }">
                <el-select v-model="row.type" size="small" style="width:100%">
                  <el-option v-for="ft in allFieldTypes" :key="ft.type" :label="ft.label" :value="ft.type" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="必填" width="70">
              <template #default="{ row }">
                <el-switch v-model="row.required" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="宽度" width="100">
              <template #default="{ row }">
                <el-select v-model="row.width" size="small" style="width:100%">
                  <el-option label="整行" value="100%" />
                  <el-option label="半行" value="50%" />
                </el-select>
              </template>
            </el-table-column>
          </el-table>
          <div class="step-actions">
            <el-button @click="importStep = 1">上一步</el-button>
            <el-button type="primary" @click="importStep = 3">下一步：创建模板</el-button>
          </div>
        </div>

        <!-- 步骤4: 创建模板 -->
        <div v-if="importStep === 3">
          <el-form :model="importTemplateForm" label-width="90px" style="max-width:500px">
            <el-form-item label="模板名称" required>
              <el-input v-model="importTemplateForm.name" placeholder="请输入模板名称" />
            </el-form-item>
            <el-form-item label="模板分类">
              <el-select v-model="importTemplateForm.category" style="width:100%">
                <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="模板描述">
              <el-input v-model="importTemplateForm.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
          <div class="summary-info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="字段数量">{{ importFields.length }}</el-descriptions-item>
              <el-descriptions-item label="数据行数">{{ importData.total_rows }}</el-descriptions-item>
              <el-descriptions-item label="来源文件">{{ importFileName || '示例数据' }}</el-descriptions-item>
              <el-descriptions-item label="智能识别">是</el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="step-actions">
            <el-button @click="importStep = 2">上一步</el-button>
            <el-button type="primary" :loading="importLoading" @click="confirmCreateTemplate">
              <el-icon><Select /></el-icon> 创建模板并导入数据
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
'''

content = content.replace('    <!-- AI 智能设计弹窗 -->', import_dialog + '\n    <!-- AI 智能设计弹窗 -->')

# 4. Add reactive state variables after AI-related ones
old_ai_state = '''const showAIHelper = ref(false)
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiExamples = ['供应商信息管理', '员工入职登记表', '客户投诉处理单', '采购申请流程表', '项目周报模板', '报销申请单']'''
new_ai_state = '''const showAIHelper = ref(false)
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiExamples = ['供应商信息管理', '员工入职登记表', '客户投诉处理单', '采购申请流程表', '项目周报模板', '报销申请单']

// 导入相关
const showImport = ref(false)
const importStep = ref(0)
const importLoading = ref(false)
const importFileName = ref('')
const importData = reactive({ headers: [], rows: [], total_rows: 0, total_columns: 0 })
const importFields = ref<any[]>([])
const importTemplateForm = reactive({ name: '', description: '', category: 'general' })
const uploadRef = ref()

// 全部字段类型（用于下拉选择）
const allFieldTypes = [
  { type: 'text', label: '单行文本' }, { type: 'textarea', label: '多行文本' },
  { type: 'number', label: '数字' }, { type: 'money', label: '金额' },
  { type: 'email', label: '邮箱' }, { type: 'phone', label: '电话' },
  { type: 'date', label: '日期' }, { type: 'datetime', label: '日期时间' },
  { type: 'select', label: '下拉选择' }, { type: 'radio', label: '单选' },
  { type: 'checkbox', label: '多选' }, { type: 'switch', label: '开关' },
  { type: 'slider', label: '滑块' }, { type: 'rate', label: '评分' },
  { type: 'upload', label: '文件上传' }, { type: 'image', label: '图片上传' },
  { type: 'richtext', label: '富文本' }, { type: 'divider', label: '分隔线' },
  { type: 'heading', label: '标题' }, { type: 'subform', label: '子表单' },
  { type: 'relation', label: '关联数据' }, { type: 'autonum', label: '自动编号' },
  { type: 'location', label: '地图位置' }, { type: 'color', label: '颜色选择' },
  { type: 'user', label: '人员选择' }, { type: 'org', label: '部门选择' },
]'''

content = content.replace(old_ai_state, new_ai_state)

# 5. Add import functions before generateWithAI
import_functions = '''
// ========== 导入功能 ==========
async function onImportFileChange(file: any) {
  importFileName.value = file.name || file.raw?.name || ''
  const rawFile = file.raw || file
  const formData = new FormData()
  formData.append('file', rawFile)
  try {
    const res = await (window as any).fetch('/api/v1/import/parse', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: formData
    })
    const json = await res.json()
    if (json.success) {
      importData.headers = json.data.headers
      importData.rows = json.data.rows
      importData.total_rows = json.data.total_rows
      importData.total_columns = json.data.total_columns
      importFields.value = json.data.fields.map((f: any) => ({
        ...f,
        optionsText: Array.isArray(f.options) ? f.options.join(',') : ''
      }))
      // 自动填入模板名称
      importTemplateForm.name = importFileName.value.replace(/\\.(xlsx|xls|csv|png|jpg|jpeg|bmp)$/i, '')
      importStep.value = 1
      ElMessage.success(json.message)
    } else {
      ElMessage.error(json.detail || json.message || '解析失败')
    }
  } catch (e: any) {
    ElMessage.error('解析失败: ' + (e.message || '请检查文件格式'))
  }
}

async function loadSampleData(type: string) {
  const sampleData: Record<string, any> = {
    supplier: {
      name: '供应商信息表',
      headers: ['供应商名称', '编码', '类型', '联系人', '联系电话', '电子邮箱', '地址', '营业执照号', '开户银行', '银行账号'],
      rows: [
        ['深圳市华强电子有限公司', 'SUP001', '原材料供应商', '张经理', '13812345601', 'zhang@hq.com', '深圳市南山区', '91440300MA5xxxx', '招商银行', '6225xxxx'],
        ['广州星河贸易有限公司', 'SUP002', '设备供应商', '李总', '13912345602', 'li@xh.com', '广州市天河区', '91440100MA5yyyy', '工商银行', '6222xxxx'],
      ]
    },
    employee: {
      name: '员工入职登记表',
      headers: ['姓名', '工号', '性别', '部门', '职位', '入职日期', '联系电话', '邮箱', '身份证号', '紧急联系人', '紧急联系电话'],
      rows: [
        ['王小明', 'EMP001', '男', '技术部', '高级工程师', '2024-03-01', '13612345610', 'wang@company.com', '440101199001011234', '王小红', '13812345611'],
        ['李丽华', 'EMP002', '女', '市场部', '市场专员', '2024-02-15', '13712345620', 'li@company.com', '440102199202022345', '李大明', '13912345621'],
      ]
    },
    customer: {
      name: '客户登记表',
      headers: ['客户名称', '客户编码', '客户类型', '客户等级', '联系人', '电话', '邮箱', '地址', '主要产品', '年销售额'],
      rows: [
        ['联想（北京）有限公司', 'CUS001', '企业客户', 'VIP客户', '陈总', '400-123-4567', 'chen@lenovo.com', '北京市海淀区', '电脑服务器', '50亿'],
        ['广州智造科技公司', 'CUS002', '企业客户', '重要客户', '刘经理', '020-88888888', 'liu@gzzz.com', '广州市开发区', '智能设备', '2亿'],
      ]
    }
  }
  const data = sampleData[type]
  if (!data) return
  importFileName.value = data.name + '.csv'
  importData.headers = data.headers
  importData.rows = data.rows
  importData.total_rows = data.rows.length
  importData.total_columns = data.headers.length
  importFields.value = data.headers.map((h: string, i: number) => ({
    name: h.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 20) || 'field_' + i,
    label: h, type: inferType(h), required: false, width: '100%',
    placeholder: '', options: [], optionsText: ''
  }))
  importTemplateForm.name = data.name
  importStep.value = 1
  ElMessage.success('已加载示例数据，请调整字段后继续')
}

function inferType(header: string): string {
  const h = header.toLowerCase()
  if (h.includes('金额') || h.includes('工资') || h.includes('价格') || h.includes('销售额')) return 'money'
  if (h.includes('邮箱') || h.includes('email')) return 'email'
  if (h.includes('电话') || h.includes('手机') || h.includes('固话')) return 'phone'
  if (h.includes('日期') || h.includes('时间')) return 'date'
  if (h.includes('类型') || h.includes('分类') || h.includes('等级') || h.includes('状态') || h.includes('性别')) return 'select'
  if (h.includes('网址') || h.includes('url')) return 'url'
  if (h.includes('描述') || h.includes('备注') || h.includes('地址') || h.includes('说明')) return 'textarea'
  return 'text'
}

function detectFieldTypes() {
  importFields.value.forEach(f => {
    f.type = inferType(f.label)
  })
}

async function confirmCreateTemplate() {
  if (!importTemplateForm.name.trim()) { ElMessage.warning('请输入模板名称'); return }
  importLoading.value = true
  try {
    // 构建字段数据
    const fields = importFields.value.map(({ optionsText, ...f }: any) => {
      if (['select', 'radio', 'checkbox'].includes(f.type) && optionsText) {
        f.options = optionsText.split(/[,\n]/).map((s: string) => s.trim()).filter(Boolean)
      }
      return f
    })

    const formData = new FormData()
    formData.append('name', importTemplateForm.name)
    formData.append('description', importTemplateForm.description || '')
    formData.append('category', importTemplateForm.category || 'general')
    formData.append('fields', JSON.stringify(fields))
    formData.append('filename', importFileName.value || '示例数据')

    const res = await (window as any).fetch('/api/v1/import/create-template', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: formData
    })
    const json = await res.json()
    if (json.success) {
      ElMessage.success('模板创建成功！')
      showImport.value = false
      importStep.value = 0
      importFields.value = []
      importData.headers = []
      importData.rows = []
      importFileName.value = ''
      // 刷新列表
      templates.value.unshift({
        id: json.data.id, name: json.data.name, code: json.data.code,
        category: json.data.category, fields: fields
      })
    } else {
      ElMessage.error(json.detail || '创建失败')
    }
  } catch { ElMessage.error('创建失败') }
  finally { importLoading.value = false }
}

'''

# Insert before generateWithAI function
if '// ========== 导入功能 ==========' not in content:
    # Find generateWithAI and insert before it
    idx = content.find('async function generateWithAI()')
    if idx > 0:
        content = content[:idx] + import_functions + content[idx:]

# 6. Add styles for import dialog
old_styles = '''.ai-examples'''
new_styles = '''/* 导入弹窗样式 */
.import-container { min-height: 300px; }
.import-uploader { width: 100%; margin-bottom: 16px; }
.upload-icon { font-size: 48px; color: #409eff; margin-bottom: 12px; }
.upload-text p { margin: 4px 0; }
.upload-hint { font-size: 12px; color: #999; }
.upload-examples { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }
.upload-examples .el-tag { cursor: pointer; }
.preview-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.field-adjust-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.step-actions { display: flex; justify-content: center; gap: 12px; margin-top: 20px; }
.summary-info { margin: 16px 0; }

.ai-examples'''

content = content.replace(old_styles, new_styles)

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print(f'Patched OK. Size: {len(content)} bytes')
print('Added: import button, import dialog (4 steps), import functions, import styles')
