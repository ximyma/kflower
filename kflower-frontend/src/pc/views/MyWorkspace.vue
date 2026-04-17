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
              <el-button type="primary" @click="createTemplate">
                <el-icon><Plus /></el-icon> 新建模板
              </el-button>
              <el-button @click="refreshTemplates">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </div>

          <!-- 模板列表 -->
          <el-table
            v-loading="loadingTemplates"
            :data="myTemplates"
            style="width: 100%"
            row-key="id"
          >
            <el-table-column prop="name" label="模板名称" min-width="200">
              <template #default="{ row }">
                <div class="template-name-cell">
                  <div class="template-name">{{ row.name }}</div>
                  <div class="template-code">编码: {{ row.code }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="fieldsCount" label="字段数" width="80" align="center">
              <template #default="{ row }">
                {{ getFieldsCount(row) }}
              </template>
            </el-table-column>
            <el-table-column prop="ai_generated" label="AI生成" width="80" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.ai_generated" type="success" size="small">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="is_published" label="发布状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_published" type="primary" size="small">已发布</el-tag>
                <el-tag v-else type="info" size="small">未发布</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" @click="viewTemplate(row)">
                    <el-icon><View /></el-icon>
                  </el-button>
                  <el-button size="small" @click="editTemplate(row)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button size="small" @click="publishTemplate(row)" v-if="!row.is_published">
                    <el-icon><Promotion /></el-icon>
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteTemplate(row)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 空状态 -->
          <el-empty v-if="!loadingTemplates && myTemplates.length === 0" description="暂无模板">
            <el-button type="primary" @click="createTemplate">创建第一个模板</el-button>
          </el-empty>
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

          <!-- 表单列表 -->
          <el-table
            v-loading="loadingForms"
            :data="publishedForms"
            style="width: 100%"
            row-key="id"
          >
            <el-table-column prop="name" label="表单名称" min-width="200">
              <template #default="{ row }">
                <div class="form-name-cell">
                  <div class="form-name">{{ row.name }}</div>
                  <div class="form-code">编码: {{ row.code }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="fieldsCount" label="字段数" width="80" align="center">
              <template #default="{ row }">
                {{ getFieldsCount(row) }}
              </template>
            </el-table-column>
            <el-table-column label="访问权限" width="120">
              <template #default="{ row }">
                <el-tag v-if="getAccessType(row) === 'public'" type="success" size="small">公开</el-tag>
                <el-tag v-else-if="getAccessType(row) === 'specified'" type="warning" size="small">指定用户</el-tag>
                <el-tag v-else type="info" size="small">私有</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数据统计" width="180">
              <template #default="{ row }">
                <div class="form-stats">
                  <span>提交: {{ row.submissionCount || 0 }}</span>
                  <el-divider direction="vertical" />
                  <span>今日: {{ row.todaySubmissions || 0 }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="分享链接" min-width="250">
              <template #default="{ row }">
                <div v-if="getAccessType(row) === 'public' && getShareLink(row)" class="share-link">
                  <el-input :value="getShareLink(row)" readonly size="small">
                    <template #append>
                      <el-button @click="copyShareLink(getShareLink(row))">
                        <el-icon><CopyDocument /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </div>
                <span v-else class="no-link">无公开链接</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" type="primary" @click="openFormPage(row)">
                    <el-icon><Link /></el-icon> 访问表单
                  </el-button>
                  <el-button size="small" @click="manageFormData(row)">
                    <el-icon><DataAnalysis /></el-icon> 数据管理
                  </el-button>
                  <el-button size="small" @click="editFormSettings(row)">
                    <el-icon><Setting /></el-icon>
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <!-- 空状态 -->
          <el-empty v-if="!loadingForms && publishedForms.length === 0" description="暂无发布的表单">
            <p>请先创建并发布一个模板</p>
          </el-empty>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, Share, DataLine, Calendar,
  Plus, Refresh, View, Edit, Promotion, Delete,
  CopyDocument, Link, DataAnalysis, Setting 
} from '@element-plus/icons-vue'
import { templateAPI } from '../../common/api'
import { useUserStore } from '../../common/store/user'
import type { Template } from '../../common/types/template'

const router = useRouter()
const userStore = useUserStore()

// 状态
const activeTab = ref('templates')
const loadingTemplates = ref(false)
const loadingForms = ref(false)
const myTemplates = ref<Template[]>([])
const publishedForms = ref<Template[]>([])
const userInfo = reactive({
  avatar: '',
  name: '',
  username: '',
  email: ''
})

// 统计数据
const myTemplatesCount = computed(() => myTemplates.value.length)
const publishedFormsCount = computed(() => publishedForms.value.length)
const totalSubmissions = ref(0)
const todaySubmissions = ref(0)

// 加载用户信息
function loadUserInfo() {
  const user = userStore.userInfo
  if (user) {
    userInfo.avatar = user.avatar || ''
    userInfo.name = user.name || ''
    userInfo.username = user.username || ''
    userInfo.email = user.email || ''
  }
}

// 加载我的模板
async function loadMyTemplates() {
  loadingTemplates.value = true
  try {
    // 获取所有模板，然后过滤出自己创建的
    const res: any = await templateAPI.list()
    // 后端返回的直接是数组 TemplateResponse[]
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
    // 获取所有模板，然后过滤出自己创建且已发布的
    const res: any = await templateAPI.list()
    // 后端返回的直接是数组 TemplateResponse[]
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
function getFieldsCount(template: Template): number {
  if (!template.modules) return 0
  let count = 0
  template.modules.forEach((mod: any) => {
    if (mod.fields && Array.isArray(mod.fields)) {
      count += mod.fields.length
    }
  })
  return count
}

// 获取访问权限类型
function getAccessType(template: Template): string {
  if (!template.config || typeof template.config !== 'object') return 'private'
  return (template.config as any).access_type || 'private'
}

// 获取分享链接
function getShareLink(template: Template): string {
  if (!template.config || typeof template.config !== 'object') return ''
  const config = template.config as any
  if (config.access_type === 'public' && config.share_link) {
    return config.share_link
  }
  // 如果没有配置分享链接，生成一个默认的
  const baseUrl = window.location.origin
  return `${baseUrl}/form/${template.id}`
}

// 格式化日期
function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 查看模板
function viewTemplate(template: Template) {
  router.push(`/templates?view=${template.id}`)
}

// 编辑模板
function editTemplate(template: Template) {
  router.push(`/templates?edit=${template.id}`)
}

// 发布模板
async function publishTemplate(template: Template) {
  try {
    const res: any = await templateAPI.publish(template.id)
    // 后端返回 BaseResponse，success 字段
    if (res && res.success !== false) {
      ElMessage.success('模板发布成功')
      loadMyTemplates()
      loadPublishedForms()
    } else {
      ElMessage.error(res?.message || '发布失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '发布失败')
  }
}

// 删除模板
async function deleteTemplate(template: Template) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？此操作将删除模板及所有相关数据`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res: any = await templateAPI.delete(template.id)
    // 后端返回 BaseResponse，success 字段
    if (res && res.success !== false) {
      ElMessage.success('模板删除成功')
      loadMyTemplates()
      loadPublishedForms()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch {
    // 用户取消
  }
}

// 打开表单页面
function openFormPage(template: Template) {
  const link = getShareLink(template)
  window.open(link, '_blank')
}

// 管理表单数据
function manageFormData(template: Template) {
  router.push(`/form/${template.id}/data`)
}

// 编辑表单设置
function editFormSettings(template: Template) {
  router.push(`/templates?edit=${template.id}&tab=settings`)
}

// 创建新模板
function createTemplate() {
  router.push('/templates?create=new')
}

// 复制分享链接
function copyShareLink(link: string) {
  navigator.clipboard.writeText(link).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 刷新
function refreshTemplates() {
  loadMyTemplates()
}

function refreshForms() {
  loadPublishedForms()
}

// 初始化加载
onMounted(() => {
  loadUserInfo()
  loadMyTemplates()
  loadPublishedForms()
  
  // 加载总提交统计（简化版）
  // 这里可以调用专门的统计API，暂时用已发布表单的统计累加
  publishedForms.value.forEach(form => {
    totalSubmissions.value += form.submissionCount || 0
    todaySubmissions.value += form.todaySubmissions || 0
  })
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
    color: #303133;
    margin: 0 0 8px;
  }
  
  .page-subtitle {
    font-size: 14px;
    color: #606266;
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
          color: #303133;
          margin-bottom: 4px;
          line-height: 1;
        }
        
        .stat-label {
          font-size: 13px;
          color: #606266;
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
    background: #fff;
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
    margin-bottom: 20px;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
}

.template-name-cell, .form-name-cell {
  .template-name, .form-name {
    font-weight: 500;
    margin-bottom: 4px;
  }
  
  .template-code, .form-code {
    font-size: 12px;
    color: #909399;
  }
}

.form-stats {
  display: flex;
  align-items: center;
  
  span {
    font-size: 12px;
    color: #606266;
  }
}

.share-link {
  .el-input {
    :deep(.el-input-group__append) {
      padding: 0;
    }
  }
}

.no-link {
  color: #c0c4cc;
  font-size: 12px;
}

// 响应式
@media (max-width: 768px) {
  .user-info-card {
    .user-header {
      flex-direction: column;
      text-align: center;
      gap: 12px;
    }
    
    .user-stats {
      .stat-item {
        .stat-number {
          font-size: 20px;
        }
      }
    }
  }
  
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