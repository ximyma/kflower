<template>
  <div class="app-knowledge">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>知识库</h2>
      <el-button type="primary" size="small" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建知识库
      </el-button>
    </div>
    
    <!-- Tab切换 -->
    <div class="tab-bar">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        {{ tab.label }}
      </div>
    </div>
    
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索知识..."
        clearable
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button @click="handleSearch"><el-icon><Search /></el-icon></el-button>
        </template>
      </el-input>
    </div>
    
    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="section-title">搜索结果 ({{ searchResults.length }})</div>
      <div
        v-for="result in searchResults"
        :key="result.id"
        class="result-item"
        @click="viewDocument(result)"
      >
        <div class="result-icon">
          <el-icon :size="20"><Document /></el-icon>
        </div>
        <div class="result-info">
          <h4>{{ result.title || result.name }}</h4>
          <p v-if="result.content">{{ result.content.substring(0, 100) }}...</p>
        </div>
      </div>
    </div>
    
    <!-- 知识库列表 -->
    <div class="knowledge-list" v-loading="loading">
      <div v-if="knowledgeBases.length === 0 && !loading && !searchResults.length" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Files /></el-icon>
        <p>暂无知识库</p>
        <el-button type="primary" size="small" @click="showCreateDialog = true">创建知识库</el-button>
      </div>
      
      <div
        v-for="kb in knowledgeBases"
        :key="kb.id"
        class="kb-item"
        @click="viewKnowledgeBase(kb)"
      >
        <div class="kb-icon" :style="{ background: getColor(kb.id) }">
          <el-icon :size="22"><Reading /></el-icon>
        </div>
        <div class="kb-info">
          <h3>{{ kb.name }}</h3>
          <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
          <div class="kb-stats">
            <span><el-icon><Document /></el-icon> {{ kb.doc_count || 0 }} 文档</span>
            <span v-if="kb.updated_at">更新于 {{ formatTime(kb.updated_at) }}</span>
          </div>
        </div>
        <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, kb)">
          <el-icon :size="20" color="#909399"><MoreFilled /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="upload">上传文档</el-dropdown-item>
              <el-dropdown-item command="search">检索</el-dropdown-item>
              <el-dropdown-item command="settings">设置</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 新建知识库对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建知识库" width="90%" :close-on-click-modal="false">
      <el-form :model="newKB" label-position="top">
        <el-form-item label="知识库名称" required>
          <el-input v-model="newKB.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newKB.description" type="textarea" :rows="2" placeholder="知识库描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createKnowledgeBase" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
    
    <!-- 上传文档对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="90%">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="10"
        :on-change="handleFileChange"
        drag
        multiple
      >
        <el-icon :size="40" color="#c0c4cc"><Upload /></el-icon>
        <div>将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、Word、Excel、TXT 等格式</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadFiles" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { Plus, Search, Files, Document, Reading, MoreFilled, Upload, UploadFilled } from '@element-plus/icons-vue'
import { knowledgeAPI } from '../../common/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const creating = ref(false)
const uploading = ref(false)
const knowledgeBases = ref<any[]>([])
const searchText = ref('')
const searchResults = ref<any[]>([])
const currentTab = ref('bases')
const showCreateDialog = ref(false)
const showUploadDialog = ref(false)
const uploadKBId = ref<number | null>(null)
const uploadFilesList = ref<File[]>([])

const tabs = [
  { key: 'bases', label: '知识库' },
  { key: 'docs', label: '我的文档' },
  { key: 'notes', label: '我的笔记' }
]

const newKB = ref({
  name: '',
  description: ''
})

function getColor(id: number) {
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#19D9FF']
  return colors[id % colors.length]
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

async function loadKnowledgeBases() {
  loading.value = true
  try {
    const res = await knowledgeAPI.listBases()
    knowledgeBases.value = res || []
  } catch (error) {
    console.error('加载知识库失败:', error)
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  if (!searchText.value.trim()) {
    searchResults.value = []
    return
  }
  
  loading.value = true
  try {
    const res = await knowledgeAPI.search({ q: searchText.value, top_k: 20 })
    searchResults.value = res.results || res || []
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

function viewKnowledgeBase(kb: any) {
  // 跳转到PC端查看详情
  ElMessageBox.confirm('知识库详情需要在电脑端查看。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(() => {
    window.open('/', '_blank')
  }).catch(() => {})
}

function viewDocument(doc: any) {
  viewKnowledgeBase(doc)
}

async function handleCommand(command: string, kb: any) {
  switch (command) {
    case 'upload':
      uploadKBId.value = kb.id
      showUploadDialog.value = true
      break
    case 'search':
      searchText.value = ''
      searchResults.value = []
      break
    case 'settings':
      viewKnowledgeBase(kb)
      break
    case 'delete':
      await deleteKnowledgeBase(kb)
      break
  }
}

async function createKnowledgeBase() {
  if (!newKB.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  
  creating.value = true
  try {
    await knowledgeAPI.createBase({
      name: newKB.value.name,
      description: newKB.value.description
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newKB.value = { name: '', description: '' }
    loadKnowledgeBases()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

async function deleteKnowledgeBase(kb: any) {
  try {
    await ElMessageBox.confirm(`确定要删除知识库"${kb.name}"吗？`, '删除确认', {
      type: 'warning'
    })
    await knowledgeAPI.deleteBase(kb.id)
    ElMessage.success('删除成功')
    loadKnowledgeBases()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function handleFileChange(file: any, files: any[]) {
  uploadFilesList.value = files.map((f: any) => f.raw)
}

async function uploadFiles() {
  if (!uploadKBId.value || uploadFilesList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  uploading.value = true
  try {
    for (const file of uploadFilesList.value) {
      await knowledgeAPI.upload(uploadKBId.value, file)
    }
    ElMessage.success(`成功上传 ${uploadFilesList.value.length} 个文件`)
    showUploadDialog.value = false
    uploadFilesList.value = []
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.app-knowledge {
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

.tab-bar {
  display: flex;
  background: white;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 12px;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 10px;
  font-size: 13px;
  color: #606266;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item.active {
  background: #667eea;
  color: white;
}

.search-bar {
  margin-bottom: 12px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 20px;
}

.search-bar :deep(.el-input-group__append) {
  border-radius: 0 20px 20px 0;
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.search-results {
  margin-bottom: 16px;
}

.section-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  padding-left: 4px;
}

.result-item {
  background: white;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 8px;
  display: flex;
  gap: 12px;
  cursor: pointer;
}

.result-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #ecf5ff;
  color: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.result-info h4 {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.result-info p {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.knowledge-list {
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

.kb-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.kb-item:active {
  transform: scale(0.98);
}

.kb-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.kb-info {
  flex: 1;
  min-width: 0;
}

.kb-info h3 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
}

.kb-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #c0c4cc;
}

.kb-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
