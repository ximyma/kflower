<template>
  <div class="workspace-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">我的工作区</h1>
      <p class="page-subtitle">管理您的模板、表单和数据统计</p>
    </div>

    <!-- 工作区统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6f7ff; color: #1890ff;">
              <el-icon size="24"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ myTemplatesCount }}</div>
              <div class="stat-label">我的模板</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f6ffed; color: #52c41a;">
              <el-icon size="24"><Share /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ publishedFormsCount }}</div>
              <div class="stat-label">发布表单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fff7e6; color: #fa8c16;">
              <el-icon size="24"><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ totalSubmissions }}</div>
              <div class="stat-label">总提交</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fff2f0; color: #ff4d4f;">
              <el-icon size="24"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ todaySubmissions }}</div>
              <div class="stat-label">今日提交</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主要内容标签页 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 我的模板 -->
      <el-tab-pane label="我的模板" name="templates">
        <div class="tab-content">
          <div class="tab-header">
            <h3>我的模板</h3>
            <div class="tab-actions">
              <el-button type="primary" @click="goToTemplateDesigner">
                <el-icon><Plus /></el-icon> 新建模板
              </el-button>
              <el-button @click="refreshTemplates">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-input v-model="templateSearch" placeholder="搜索模板名称..." clearable style="width: 300px" @input="debounceTemplateSearch">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>

          <!-- 视图切换 + 模板列表 -->
          <div class="template-list-wrapper">
            <!-- 加载状态 -->
            <div v-if="loadingTemplates" class="loading-skeleton">
              <el-skeleton :rows="5" animated />
            </div>

            <!-- 空状态 -->
            <el-empty v-else-if="filteredTemplates.length === 0" description="暂无模板">
              <el-button type="primary" @click="goToTemplateDesigner">创建第一个模板</el-button>
            </el-empty>

            <!-- 表格视图 -->
            <div v-else class="template-table-wrapper">
              <el-table :data="filteredTemplates" stripe style="width:100%" v-loading="loadingTemplates">
                <el-table-column label="模板名称" min-width="200" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div class="table-name-cell">
                      <div class="table-icon" :style="{ background: getTemplateColor(row.name) }">
                        <el-icon><Document /></el-icon>
                      </div>
                      <div>
                        <div class="table-name-text">{{ row.name }}</div>
                        <div class="table-code-text">{{ row.code || 'ID: ' + row.id }}</div>
                      </div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="发布状态" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
                      {{ row.is_published ? '已发布' : '草稿' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="创建人" width="100" align="center">
                  <template #default="{ row }">
                    <span>{{ getCreatorName(row) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="共享" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.created_by === currentUserId" type="primary" size="small">私有</el-tag>
                    <el-tag v-else type="warning" size="small">共享</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="category" label="分类" width="100" align="center" />
                <el-table-column label="字段数" width="80" align="center">
                  <template #default="{ row }">
                    <span class="field-count-num">{{ getFieldsCount(row) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="模板ID" width="100" align="center">
                  <template #default="{ row }">
                    <span class="template-id-text">{{ row.id }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160" align="center">
                  <template #default="{ row }">
                    <span>{{ formatDate(row.created_at) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="340" fixed="right" align="center">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" text @click="viewTemplate(row)" title="查看">
                      <el-icon><View /></el-icon>查看
                    </el-button>
                    <el-button size="small" type="warning" text @click="editTemplate(row)" title="编辑">
                      <el-icon><Edit /></el-icon>编辑
                    </el-button>
                    <el-button v-if="row.is_published" size="small" type="success" text @click="openFormSubmit(row)" title="填写表单">
                      <el-icon><EditPen /></el-icon>填表
                    </el-button>
                    <el-button v-else size="small" type="success" text @click="publishTemplate(row)" title="发布">
                      <el-icon><Promotion /></el-icon>发布
                    </el-button>
                    <el-button v-if="row.is_published" size="small" type="info" text @click="openFormList(row)" title="数据列表">
                      <el-icon><List /></el-icon>列表
                    </el-button>
                    <el-button size="small" text @click="openPermissionDialog(row, 'template')" title="权限设置">
                      <el-icon><Key /></el-icon>权限
                    </el-button>
                    <el-button size="small" type="danger" text @click="deleteTemplate(row)" title="删除">
                      <el-icon><Delete /></el-icon>删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 我发布的表单 -->
      <el-tab-pane label="我发布的表单" name="forms">
        <div class="tab-content">
          <div class="tab-header">
            <h3>我发布的表单</h3>
            <div class="tab-actions">
              <el-button @click="refreshForms">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-input v-model="formSearch" placeholder="搜索表单名称..." clearable style="width: 300px" @input="debounceFormSearch">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>

          <!-- 表单列表 -->
          <div class="form-list-wrapper">
            <div v-if="loadingForms" class="loading-skeleton">
              <el-skeleton :rows="5" animated />
            </div>

            <el-empty v-else-if="filteredForms.length === 0" description="暂无发布的表单">
              <p>请先创建并发布一个模板</p>
              <el-button type="primary" @click="goToTemplateDesigner">去创建模板</el-button>
            </el-empty>

            <!-- 表格视图 -->
            <div v-else class="template-table-wrapper">
              <el-table :data="filteredForms" stripe style="width:100%" v-loading="loadingForms">
                <el-table-column label="表单名称" min-width="200" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div class="table-name-cell">
                      <div class="table-icon" :style="{ background: getTemplateColor(row.name) }">
                        <el-icon><Document /></el-icon>
                      </div>
                      <div>
                        <div class="table-name-text">{{ row.name }}</div>
                        <div class="table-code-text">{{ row.code || 'ID: ' + row.id }}</div>
                      </div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="category" label="分类" width="100" align="center" />
                <el-table-column label="共享" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.created_by === currentUserId" type="primary" size="small">私有</el-tag>
                    <el-tag v-else type="warning" size="small">共享</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="数据统计" width="180" align="center">
                  <template #default="{ row }">
                    <div class="form-stats">
                      <span>提交: {{ row.submissionCount || 0 }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="模板ID" width="100" align="center">
                  <template #default="{ row }">
                    <span class="template-id-text">{{ row.id }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="160" align="center">
                  <template #default="{ row }">
                    <span>{{ formatDate(row.created_at) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="280" fixed="right" align="center">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" text @click="openFormSubmit(row)" title="填写表单">
                      <el-icon><EditPen /></el-icon>填表
                    </el-button>
                    <el-button size="small" type="success" text @click="openFormList(row)" title="数据列表">
                      <el-icon><List /></el-icon>列表
                    </el-button>
                    <el-button size="small" type="warning" text @click="editTemplate(row)" title="编辑模板">
                      <el-icon><Edit /></el-icon>编辑
                    </el-button>
                    <el-button size="small" text @click="openPermissionDialog(row, 'form')" title="权限设置">
                      <el-icon><Key /></el-icon>权限
                    </el-button>
                    <el-button size="small" type="danger" text @click="unpublishTemplate(row)" title="撤回发布">
                      <el-icon><RefreshRight /></el-icon>撤回
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 我的应用 -->
      <el-tab-pane label="我的应用" name="apps">
        <div class="tab-content">
          <div class="tab-header">
            <h3>我的应用</h3>
            <div class="tab-actions">
              <el-button type="primary" @click="goToMyAppsPage">
                <el-icon><Plus /></el-icon> 新建应用
              </el-button>
              <el-button @click="refreshApps">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>

          <!-- 应用列表 -->
          <div class="app-list-wrapper">
            <div v-if="loadingApps" class="loading-skeleton">
              <el-skeleton :rows="5" animated />
            </div>

            <el-empty v-else-if="myApps.length === 0" description="暂无应用">
              <p>创建一个应用来组织您的表单和菜单</p>
              <el-button type="primary" @click="goToMyAppsPage">去创建应用</el-button>
            </el-empty>

            <div v-else class="template-table-wrapper">
              <el-table :data="myApps" stripe style="width:100%" v-loading="loadingApps">
                <el-table-column label="应用名称" min-width="200" show-overflow-tooltip>
                  <template #default="{ row }">
                    <div class="table-name-cell">
                      <div class="table-icon" :style="{ background: getTemplateColor(row.name) }">
                        <el-icon><Document /></el-icon>
                      </div>
                      <div>
                        <div class="table-name-text">{{ row.name }}</div>
                        <div class="table-code-text">{{ row.code || 'ID: ' + row.id }}</div>
                      </div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                <el-table-column label="状态" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.is_published" type="success" size="small">已发布</el-tag>
                    <el-tag v-else type="info" size="small">草稿</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="180" align="center" />
                <el-table-column label="操作" width="340" fixed="right" align="center">
                  <template #default="{ row }">
                    <el-button size="small" type="warning" text @click="designApp(row)" title="设计">
                      <el-icon><Edit /></el-icon>设计
                    </el-button>
                    <el-button v-if="row.is_published" size="small" type="success" text @click="openApp(row)" title="打开应用">
                      <el-icon><View /></el-icon>打开
                    </el-button>
                    <el-button v-if="row.is_published" size="small" type="warning" text @click="unpublishApp(row)" title="撤回应用">
                      <el-icon><ArrowDown /></el-icon>撤回
                    </el-button>
                    <el-button size="small" type="danger" text @click="deleteApp(row)" title="删除">
                      <el-icon><Delete /></el-icon>删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 填写数据弹窗 -->
    <el-dialog v-model="showDataForm" :title="'填写数据 - ' + (dataFormTemplate?.name || '')" width="700px" destroy-on-close>
      <el-form :model="dataFormData" label-width="120px" ref="dataFormRef">
        <template v-for="f in dataFormFields" :key="f.name">
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

    <!-- 权限设置弹窗 -->
    <el-dialog v-model="showPermissionDialog" :title="'权限设置 - ' + (permTemplate?.name || '')" width="550px">
      <el-form label-width="90px">
        <el-form-item label="模板名称">
          <span style="font-weight:500">{{ permTemplate?.name }}</span>
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
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, Share, DataLine, Calendar,
  Plus, Refresh, View, Edit, Promotion, Delete, Search,
  EditPen, List, RefreshRight, Key, ArrowDown
} from '@element-plus/icons-vue'
import { templateAPI } from '../../common/api'
import { appAPI } from '../../common/api/myApps'
import { useUserStore } from '../../common/store/user'

const router = useRouter()
const userStore = useUserStore()

// 状态
const activeTab = ref('templates')
const loadingTemplates = ref(false)
const loadingForms = ref(false)
const loadingApps = ref(false)
const myTemplates = ref<any[]>([])
const publishedForms = ref<any[]>([])
const myApps = ref<any[]>([])
const templateSearch = ref('')
const formSearch = ref('')
const templateListLoading = ref(false)
const formListLoading = ref(false)

// 统计数据
const myTemplatesCount = computed(() => myTemplates.value.length)
const publishedFormsCount = computed(() => publishedForms.value.length)
const totalSubmissions = ref(0)
const todaySubmissions = ref(0)

// 当前用户ID
const currentUserId = computed(() => userStore.userInfo?.id ?? null)

// 过滤后的模板列表
const filteredTemplates = computed(() => {
  if (!templateSearch.value) return myTemplates.value
  const search = templateSearch.value.toLowerCase()
  return myTemplates.value.filter(t => 
    t.name?.toLowerCase().includes(search) || 
    t.code?.toLowerCase().includes(search) ||
    String(t.id).includes(search)
  )
})

// 过滤后的表单列表
const filteredForms = computed(() => {
  if (!formSearch.value) return publishedForms.value
  const search = formSearch.value.toLowerCase()
  return publishedForms.value.filter(f => 
    f.name?.toLowerCase().includes(search) || 
    f.code?.toLowerCase().includes(search) ||
    String(f.id).includes(search)
  )
})

// 填写表单相关
const showDataForm = ref(false)
const dataFormTemplate = ref<any>(null)
const dataFormFields = ref<any[]>([])
const dataFormData = reactive<Record<string, any>>({})
const dataFormLoading = ref(false)

// 权限设置相关
const showPermissionDialog = ref(false)
const permTemplate = ref<any>(null)
const permForm = reactive({ is_public: false })
const permLoading = ref(false)

// 去创建模板
function goToTemplateDesigner() {
  router.push('/templates?create=new')
}

// 加载我的模板
async function loadMyTemplates() {
  loadingTemplates.value = true
  try {
    const res: any = await templateAPI.list()
    if (Array.isArray(res)) {
      const userId = userStore.userInfo?.id
      if (userId) {
        myTemplates.value = res.filter((t: any) => t.created_by === userId)
      } else {
        myTemplates.value = []
      }
    } else {
      ElMessage.error('加载模板失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '加载模板失败')
  } finally {
    loadingTemplates.value = false
  }
}

// 加载我发布的表单
async function loadPublishedForms() {
  loadingForms.value = true
  try {
    const res: any = await templateAPI.list()
    if (Array.isArray(res)) {
      const userId = userStore.userInfo?.id
      if (userId) {
        publishedForms.value = res.filter((t: any) => 
          t.created_by === userId && t.is_published
        )
        
        // 加载每个表单的数据统计
        for (const form of publishedForms.value) {
          try {
            const statsRes: any = await templateAPI.getStats(form.id)
            if (statsRes && statsRes.total_count !== undefined) {
              form.submissionCount = statsRes.total_count
              form.todaySubmissions = statsRes.today_count
            }
          } catch (e) {
            console.error(`加载表单 ${form.id} 统计失败`, e)
          }
        }
      } else {
        publishedForms.value = []
      }
    } else {
      ElMessage.error('加载表单失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '加载表单失败')
  } finally {
    loadingForms.value = false
  }
}

// 获取字段数量
function getFieldsCount(template: any): number {
  if (!template.modules) return 0
  let count = 0
  template.modules.forEach((mod: any) => {
    if (mod.fields && Array.isArray(mod.fields)) {
      count += mod.fields.length
    }
  })
  return count
}

// 获取模板颜色
function getTemplateColor(name: string): string {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#C0C4CC']
  let hash = 0
  for (let i = 0; i < (name || '').length; i++) {
    hash = ((hash << 5) - hash) + name.charCodeAt(i)
    hash = hash & hash
  }
  return colors[Math.abs(hash) % colors.length]
}

// 获取创建人名称
function getCreatorName(row: any): string {
  if (!row.created_by) return '—'
  if (row.created_by === currentUserId.value) return '我'
  return `用户${row.created_by}`
}

// 格式化日期
function formatDate(dateString: string): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')} ${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}

// 搜索防抖
let templateSearchTimer: any = null
function debounceTemplateSearch() {
  clearTimeout(templateSearchTimer)
  templateSearchTimer = setTimeout(() => {
    // 搜索逻辑已通过 computed 实现
  }, 300)
}

let formSearchTimer: any = null
function debounceFormSearch() {
  clearTimeout(formSearchTimer)
  formSearchTimer = setTimeout(() => {
    // 搜索逻辑已通过 computed 实现
  }, 300)
}

// 查看模板
function viewTemplate(template: any) {
  router.push(`/templates?view=${template.id}`)
}

// 编辑模板
function editTemplate(template: any) {
  router.push(`/templates?edit=${template.id}`)
}

// 发布模板
async function publishTemplate(template: any) {
  try {
    const res: any = await templateAPI.publish(template.id)
    if (res && res.success !== false) {
      ElMessage.success('模板发布成功！数据表已创建。')
      loadMyTemplates()
      loadPublishedForms()
    } else {
      ElMessage.error(res?.message || '发布失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '发布失败')
  }
}

// 撤回发布
async function unpublishTemplate(template: any) {
  try {
    await ElMessageBox.confirm(
      `确定要撤回模板「${template.name}」的发布吗？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await templateAPI.update(template.id, { is_published: false })
    ElMessage.success('已撤回发布')
    loadMyTemplates()
    loadPublishedForms()
  } catch {
    // 用户取消
  }
}

// 删除模板
async function deleteTemplate(template: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板「${template.name}」吗？此操作将删除模板及所有相关数据`,
      '警告',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'error' }
    )
    await templateAPI.delete(template.id)
    ElMessage.success('模板删除成功')
    loadMyTemplates()
    loadPublishedForms()
  } catch {
    // 用户取消
  }
}

// 打开表单填写
function openFormSubmit(t: any) {
  dataFormTemplate.value = t
  dataFormFields.value = getTemplateFields(t)
  // 初始化表单数据
  Object.keys(dataFormData).forEach(k => delete dataFormData[k])
  dataFormFields.value.forEach(f => {
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
  showDataForm.value = true
}

// 获取模板字段
function getTemplateFields(template: any): any[] {
  const fields: any[] = []
  if (template.modules) {
    template.modules.forEach((mod: any) => {
      if (mod.fields && Array.isArray(mod.fields)) {
        fields.push(...mod.fields)
      }
    })
  }
  return fields
}

// 提交表单数据
async function submitDataForm() {
  if (!dataFormTemplate.value) return
  
  // 验证必填字段
  for (const f of dataFormFields.value) {
    if (f.required) {
      const val = dataFormData[f.name]
      if (!val || (Array.isArray(val) && val.length === 0)) {
        ElMessage.warning(`请填写必填字段「${f.label}」`)
        return
      }
    }
  }
  
  dataFormLoading.value = true
  try {
    await templateAPI.submitData(dataFormTemplate.value.id, { ...dataFormData })
    ElMessage.success('数据提交成功！')
    showDataForm.value = false
    loadPublishedForms()
  } catch (e: any) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    dataFormLoading.value = false
  }
}

// 打开权限设置弹窗
function openPermissionDialog(row: any, type: 'template' | 'form') {
  permTemplate.value = row
  permForm.is_public = row.is_public ?? false
  showPermissionDialog.value = true
}

// 保存权限设置
async function savePermission() {
  if (!permTemplate.value) return
  permLoading.value = true
  try {
    await templateAPI.update(permTemplate.value.id, { is_public: permForm.is_public })
    ElMessage.success('权限保存成功')
    showPermissionDialog.value = false
    loadMyTemplates()
    loadPublishedForms()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    permLoading.value = false
  }
}

// 打开表单数据列表
function openFormList(template: any) {
  router.push(`/form/${template.id}/data`)
}

// 刷新
function refreshTemplates() {
  loadMyTemplates()
}

function refreshForms() {
  loadPublishedForms()
}

// ========== 应用相关方法 ==========
async function loadMyApps() {
  loadingApps.value = true
  try {
    const res = await appAPI.list()
    myApps.value = res || []
  } catch (error: any) {
    ElMessage.error('加载应用列表失败：' + (error.message || '未知错误'))
  } finally {
    loadingApps.value = false
  }
}

function refreshApps() {
  loadMyApps()
}

function goToMyAppsPage() {
  router.push('/my-apps')
}

function designApp(app: any) {
  router.push(`/app-designer/${app.id}`)
}

function openApp(app: any) {
  // 打开应用（跳转到应用容器页）
  router.push(`/app/${app.id}`)
}

async function unpublishApp(app: any) {
  try {
    await ElMessageBox.confirm(`确定撤回应用「${app.name}」吗？撤回后用户将无法访问。`, '确认撤回', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await appAPI.unpublish(app.id)
    ElMessage.success('已撤回')
    loadMyApps()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('撤回失败：' + (error.message || '未知错误'))
    }
  }
}

async function deleteApp(app: any) {
  try {
    await ElMessageBox.confirm(`确定要删除应用"${app.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await appAPI.delete(app.id)
    ElMessage.success('应用已删除')
    loadMyApps()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + (error.message || '未知错误'))
    }
  }
}

// 初始化加载
onMounted(() => {
  loadMyTemplates()
  loadPublishedForms()
  loadMyApps()
})
</script>

<style scoped lang="scss">
.workspace-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
  
  .page-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px;
  }
  
  .page-subtitle {
    font-size: 14px;
    color: var(--el-text-color-regular);
    margin: 0;
  }
}

.stats-row {
  margin-bottom: 24px;
  
  .stat-card {
    height: 100%;
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      
      .stat-info {
        flex: 1;
        
        .stat-number {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
          line-height: 1;
        }
        
        .stat-label {
          font-size: 13px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
}

.main-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
  
  :deep(.el-tabs__content) {
    padding: 24px;
    background: var(--el-bg-color);
    border-radius: 0 0 8px 8px;
    border: 1px solid #e4e7ed;
    border-top: none;
  }
}

.tab-content {
  .tab-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0;
    }
  }
}

.search-bar {
  margin-bottom: 16px;
}

.template-list-wrapper,
.form-list-wrapper {
  min-height: 200px;
}

.loading-skeleton {
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
}

.template-table-wrapper {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 16px;
  
  .table-name-cell {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .table-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }
  
  .table-name-text {
    font-weight: 500;
    color: var(--el-text-color-primary);
  }
  
  .table-code-text {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  
  .field-count-num {
    font-weight: 600;
    color: #409EFF;
  }
  
  .template-id-text {
    font-family: monospace;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
  
  .form-stats {
    display: flex;
    align-items: center;
    
    span {
      font-size: 12px;
      color: var(--el-text-color-regular);
    }
  }
}

@media (max-width: 768px) {
  .tab-content {
    .tab-header {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
      
      h3 {
        text-align: center;
      }
    }
  }
}
</style>
