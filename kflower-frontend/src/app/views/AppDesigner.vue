<template>
  <div class="mobile-app-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </div>
      <div class="header-title">{{ appName || '新建应用' }}</div>
      <div class="header-right">
        <el-button type="primary" size="small" @click="saveApp" :loading="saving">
          保存
        </el-button>
      </div>
    </div>

    <!-- 应用信息 -->
    <div class="app-info-section">
      <el-input v-model="appName" placeholder="应用名称" size="large" />
      <el-input
        v-model="appDescription"
        type="textarea"
        :rows="2"
        placeholder="应用描述（可选）"
        style="margin-top: 12px"
      />
    </div>

    <!-- 菜单设计 -->
    <div class="menus-section">
      <div class="section-header">
        <span class="section-title">应用菜单</span>
        <el-button size="small" @click="showAddMenuDialog">
          <el-icon><Plus /></el-icon> 添加菜单
        </el-button>
      </div>

      <div v-if="menus.length === 0" class="empty-menus">
        <el-icon :size="48" color="#c0c4cc"><Menu /></el-icon>
        <p>暂无菜单</p>
        <p class="tip">添加菜单让用户可以访问应用功能</p>
      </div>

      <div v-else class="menu-list">
        <div v-for="(menu, index) in menus" :key="index" class="menu-item">
          <div class="menu-icon">
            <el-icon><component :is="menu.icon || 'Document'" /></el-icon>
          </div>
          <div class="menu-info">
            <div class="menu-name">{{ menu.name || '未命名菜单' }}</div>
            <div class="menu-type">
              <el-tag size="small">{{ menu.type === 'page' ? '页面' : '功能' }}</el-tag>
            </div>
          </div>
          <div class="menu-actions">
            <el-icon @click="editMenu(index)"><Edit /></el-icon>
            <el-icon @click="deleteMenu(index)"><Delete /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 关联模板 -->
    <div class="templates-section">
      <div class="section-header">
        <span class="section-title">关联模板</span>
        <el-button size="small" @click="showTemplateSelector">
          <el-icon><Plus /></el-icon> 添加模板
        </el-button>
      </div>

      <div v-if="linkedTemplates.length === 0" class="empty-templates">
        <p class="tip">添加关联模板到应用菜单</p>
      </div>

      <div v-else class="template-tags">
        <el-tag
          v-for="(template, index) in linkedTemplates"
          :key="index"
          closable
          @close="removeTemplate(index)"
          style="margin-right: 8px; margin-bottom: 8px"
        >
          {{ template.name }}
        </el-tag>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="bottom-actions">
      <el-button @click="previewApp">
        <el-icon><View /></el-icon> 预览
      </el-button>
      <el-button type="success" @click="publishApp" :loading="publishing">
        <el-icon><Promotion /></el-icon> {{ appData?.is_published ? '已发布' : '发布' }}
      </el-button>
    </div>

    <!-- 添加/编辑菜单对话框 -->
    <el-dialog
      v-model="showMenuDialog"
      :title="editingMenuIndex >= 0 ? '编辑菜单' : '添加菜单'"
      width="90%"
      :close-on-click-modal="false"
    >
      <el-form :model="menuForm" label-position="top">
        <el-form-item label="菜单名称" required>
          <el-input v-model="menuForm.name" placeholder="请输入菜单名称" />
        </el-form-item>
        <el-form-item label="菜单类型">
          <el-radio-group v-model="menuForm.type">
            <el-radio label="page">页面</el-radio>
            <el-radio label="action">功能</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="关联模板" v-if="menuForm.type === 'page'">
          <el-select v-model="menuForm.templateId" placeholder="选择模板" style="width: 100%">
            <el-option
              v-for="t in availableTemplates"
              :key="t.id"
              :label="t.name"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="菜单图标">
          <el-select v-model="menuForm.icon" placeholder="选择图标" style="width: 100%">
            <el-option label="📄 文档" value="Document" />
            <el-option label="📊 图表" value="DataLine" />
            <el-option label="📁 文件夹" value="Folder" />
            <el-option label="👤 用户" value="User" />
            <el-option label="⚙️ 设置" value="Setting" />
            <el-option label="📝 列表" value="List" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMenuDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMenu">确定</el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <el-dialog v-model="showTemplateDialog" title="选择模板" width="90%">
      <div class="template-selector">
        <div
          v-for="template in availableTemplates"
          :key="template.id"
          class="template-option"
          :class="{ selected: selectedTemplateIds.includes(template.id) }"
          @click="toggleTemplate(template)"
        >
          <el-checkbox :model-value="selectedTemplateIds.includes(template.id)" />
          <div class="template-option-info">
            <div class="template-option-name">{{ template.name }}</div>
            <div class="template-option-desc">{{ template.description || '暂无描述' }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmTemplates">确定</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreview" title="应用预览" width="95%" fullscreen>
      <div class="app-preview">
        <div class="preview-header">
          <h3>{{ appName || '未命名应用' }}</h3>
          <p>{{ appDescription || '暂无描述' }}</p>
        </div>
        <div class="preview-menus">
          <div v-for="(menu, index) in menus" :key="index" class="preview-menu-item">
            <el-icon><component :is="menu.icon || 'Document'" /></el-icon>
            <span>{{ menu.name }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, Edit, Delete, Menu, View, Promotion, Document, DataLine, Folder, User, Setting, List } from '@element-plus/icons-vue'
import appAPI from '../../common/api/myApps'
import { templateAPI } from '../../common/api'

const route = useRoute()
const router = useRouter()

const appId = computed(() => route.params.appId ? Number(route.params.appId) : null)
const appName = ref('')
const appDescription = ref('')
const appData = ref<any>(null)
const menus = ref<any[]>([])
const linkedTemplates = ref<any[]>([])
const availableTemplates = ref<any[]>([])
const saving = ref(false)
const publishing = ref(false)
const showMenuDialog = ref(false)
const showTemplateDialog = ref(false)
const showPreview = ref(false)
const editingMenuIndex = ref(-1)
const selectedTemplateIds = ref<number[]>([])

const menuForm = ref({
  name: '',
  type: 'page',
  templateId: null as number | null,
  icon: 'Document'
})

function goBack() {
  router.back()
}

async function loadApp() {
  if (!appId.value) {
    // 新建应用
    return
  }

  try {
    const res = await appAPI.get(appId.value)
    appData.value = res
    appName.value = res.name || ''
    appDescription.value = res.description || ''

    // 解析菜单
    if (res.menus) {
      menus.value = typeof res.menus === 'string' ? JSON.parse(res.menus) : res.menus
    }

    // 解析关联模板
    if (res.templates) {
      linkedTemplates.value = typeof res.templates === 'string'
        ? JSON.parse(res.templates)
        : res.templates
    }
  } catch (error) {
    console.error('加载应用失败:', error)
  }
}

async function loadTemplates() {
  try {
    const res = await templateAPI.list({ limit: 100 })
    availableTemplates.value = res.items || res || []
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

async function saveApp() {
  if (!appName.value.trim()) {
    ElMessage.warning('请输入应用名称')
    return
  }

  saving.value = true
  try {
    const data = {
      name: appName.value,
      description: appDescription.value,
      menus: menus.value,
      templates: linkedTemplates.value
    }

    if (appId.value) {
      await appAPI.update(appId.value, data)
      ElMessage.success('保存成功')
    } else {
      const res = await appAPI.create(data)
      ElMessage.success('创建成功')
      router.replace(`/app/app-designer/${res.id}`)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function publishApp() {
  if (!appId.value) {
    ElMessage.warning('请先保存应用')
    return
  }

  publishing.value = true
  try {
    await appAPI.publish(appId.value)
    appData.value.is_published = true
    ElMessage.success('发布成功')
  } catch (error: any) {
    ElMessage.error(error.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

function previewApp() {
  showPreview.value = true
}

function showAddMenuDialog() {
  editingMenuIndex.value = -1
  menuForm.value = {
    name: '',
    type: 'page',
    templateId: null,
    icon: 'Document'
  }
  showMenuDialog.value = true
}

function editMenu(index: number) {
  editingMenuIndex.value = index
  const menu = menus.value[index]
  menuForm.value = {
    name: menu.name || '',
    type: menu.type || 'page',
    templateId: menu.templateId || null,
    icon: menu.icon || 'Document'
  }
  showMenuDialog.value = true
}

function deleteMenu(index: number) {
  menus.value.splice(index, 1)
  ElMessage.success('已删除菜单')
}

function saveMenu() {
  if (!menuForm.value.name.trim()) {
    ElMessage.warning('请输入菜单名称')
    return
  }

  if (editingMenuIndex.value >= 0) {
    menus.value[editingMenuIndex.value] = {
      ...menuForm.value,
      id: menus.value[editingMenuIndex.value].id || Date.now()
    }
    ElMessage.success('菜单已更新')
  } else {
    menus.value.push({
      ...menuForm.value,
      id: Date.now()
    })
    ElMessage.success('菜单已添加')
  }

  showMenuDialog.value = false
}

function showTemplateSelector() {
  selectedTemplateIds.value = linkedTemplates.value.map(t => t.id)
  showTemplateDialog.value = true
}

function toggleTemplate(template: any) {
  const index = selectedTemplateIds.value.indexOf(template.id)
  if (index >= 0) {
    selectedTemplateIds.value.splice(index, 1)
  } else {
    selectedTemplateIds.value.push(template.id)
  }
}

function confirmTemplates() {
  linkedTemplates.value = availableTemplates.value.filter(t =>
    selectedTemplateIds.value.includes(t.id)
  )
  showTemplateDialog.value = false
  ElMessage.success('已更新关联模板')
}

function removeTemplate(index: number) {
  linkedTemplates.value.splice(index, 1)
}

onMounted(() => {
  loadApp()
  loadTemplates()
})
</script>

<style scoped>
.mobile-app-designer {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 120px;
}

.designer-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409EFF;
  cursor: pointer;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right {
  display: flex;
  gap: 8px;
}

.app-info-section {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
}

.menus-section,
.templates-section {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
}

.empty-menus,
.empty-templates {
  text-align: center;
  padding: 30px 20px;
  color: #909399;
}

.empty-menus p,
.empty-templates p {
  margin: 12px 0 0;
}

.tip {
  font-size: 12px;
  color: #c0c4cc;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #eee;
}

.menu-icon {
  width: 36px;
  height: 36px;
  background: #667eea;
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-info {
  flex: 1;
}

.menu-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.menu-actions {
  display: flex;
  gap: 12px;
  color: #909399;
}

.menu-actions .el-icon {
  cursor: pointer;
  font-size: 18px;
}

.menu-actions .el-icon:hover {
  color: #409EFF;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
}

.bottom-actions {
  position: fixed;
  bottom: 60px;
  left: 0;
  right: 0;
  background: white;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 99;
}

.bottom-actions .el-button {
  flex: 1;
}

.template-selector {
  max-height: 400px;
  overflow-y: auto;
}

.template-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-option.selected {
  border-color: #667eea;
  background: #f0f5ff;
}

.template-option-info {
  flex: 1;
}

.template-option-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.template-option-desc {
  font-size: 12px;
  color: #909399;
}

.app-preview {
  padding: 16px;
}

.preview-header {
  text-align: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.preview-header h3 {
  margin-bottom: 8px;
}

.preview-header p {
  color: #909399;
  font-size: 13px;
}

.preview-menus {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.preview-menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  color: #606266;
}

.preview-menu-item span {
  font-size: 12px;
}
</style>
