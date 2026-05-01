<template>
  <div class="app-templates">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>模板设计</h2>
      <el-button type="primary" size="small" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
    </div>
    
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索模板..."
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>
    
    <!-- 模板列表 -->
    <div class="template-list" v-loading="loading">
      <div v-if="filteredTemplates.length === 0 && !loading" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Document /></el-icon>
        <p>暂无模板</p>
        <el-button type="primary" size="small" @click="showCreateDialog = true">创建第一个模板</el-button>
      </div>
      
      <div
        v-for="template in filteredTemplates"
        :key="template.id"
        class="template-item"
        @click="viewTemplate(template)"
      >
        <div class="template-icon" :style="{ background: getCategoryColor(template.category) }">
          <el-icon :size="24"><component :is="getCategoryIcon(template.category)" /></el-icon>
        </div>
        <div class="template-info">
          <h3>{{ template.name }}</h3>
          <p class="template-desc">{{ template.description || '暂无描述' }}</p>
          <div class="template-meta">
            <el-tag size="small" :type="template.is_published ? 'success' : 'info'">
              {{ template.is_published ? '已发布' : '草稿' }}
            </el-tag>
            <span class="template-time">{{ formatTime(template.updated_at) }}</span>
          </div>
        </div>
        <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, template)">
          <el-icon :size="20" color="#909399"><MoreFilled /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="publish" v-if="!template.is_published">发布</el-dropdown-item>
              <el-dropdown-item command="data">查看数据</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 新建模板对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建模板" width="90%" :close-on-click-modal="false">
      <el-form :model="newTemplate" label-position="top">
        <el-form-item label="模板名称" required>
          <el-input v-model="newTemplate.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="newTemplate.category" placeholder="选择分类" style="width: 100%">
            <el-option label="办公表单" value="office" />
            <el-option label="业务流程" value="business" />
            <el-option label="数据采集" value="data" />
            <el-option label="调查问卷" value="survey" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newTemplate.description" type="textarea" :rows="2" placeholder="模板描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTemplate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Document, MoreFilled, Edit, Tickets, DataLine, List, User } from '@element-plus/icons-vue'
import { templateAPI } from '../../common/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const templates = ref<any[]>([])
const searchText = ref('')
const showCreateDialog = ref(false)

const newTemplate = ref({
  name: '',
  category: 'office',
  description: ''
})

const filteredTemplates = computed(() => {
  if (!searchText.value) return templates.value
  const keyword = searchText.value.toLowerCase()
  return templates.value.filter(t => 
    t.name.toLowerCase().includes(keyword) ||
    (t.description && t.description.toLowerCase().includes(keyword))
  )
})

function getCategoryColor(category: string) {
  const colors: Record<string, string> = {
    office: '#409EFF',
    business: '#67C23A',
    data: '#E6A23C',
    survey: '#F56C6C',
    other: '#909399'
  }
  return colors[category] || colors.other
}

function getCategoryIcon(category: string) {
  const icons: Record<string, string> = {
    office: 'Document',
    business: 'Tickets',
    data: 'DataLine',
    survey: 'List',
    other: 'User'
  }
  return icons[category] || icons.other
}

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString()
}

async function loadTemplates() {
  loading.value = true
  try {
    const res = await templateAPI.list({ limit: 100 })
    templates.value = res.items || res || []
  } catch (error) {
    console.error('加载模板失败:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 搜索是computed自动处理的
}

function viewTemplate(template: any) {
  // 跳转到移动端模板设计器
  router.push(`/app/template-designer/${template.id}`)
}

async function handleCommand(command: string, template: any) {
  switch (command) {
    case 'edit':
      viewTemplate(template)
      break
    case 'publish':
      await publishTemplate(template)
      break
    case 'data':
      router.push(`/app/template-data/${template.id}`)
      break
    case 'delete':
      await deleteTemplate(template)
      break
  }
}

async function publishTemplate(template: any) {
  try {
    await templateAPI.publish(template.id)
    ElMessage.success('发布成功')
    loadTemplates()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

async function deleteTemplate(template: any) {
  try {
    await ElMessageBox.confirm(`确定要删除模板"${template.name}"吗？`, '删除确认', {
      type: 'warning'
    })
    await templateAPI.delete(template.id)
    ElMessage.success('删除成功')
    loadTemplates()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function createTemplate() {
  if (!newTemplate.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  
  creating.value = true
  try {
    await templateAPI.create({
      name: newTemplate.value.name,
      category: newTemplate.value.category,
      description: newTemplate.value.description
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newTemplate.value = { name: '', category: 'office', description: '' }
    loadTemplates()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.app-templates {
  padding-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.search-bar {
  margin-bottom: 16px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 20px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state p {
  margin: 16px 0;
}

.template-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.template-item:active {
  transform: scale(0.98);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.template-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-info h3 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-time {
  font-size: 11px;
  color: #c0c4cc;
}
</style>
