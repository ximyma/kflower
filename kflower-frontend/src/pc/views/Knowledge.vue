<template>
  <div class="knowledge-page">
    <div class="page-header">
      <div class="header-left">
        <h2>知识库管理</h2>
        <el-tag type="info">{{ knowledgeBases.length }} 个知识库</el-tag>
      </div>
      <div class="header-right">
        <el-input v-model="searchText" placeholder="搜索知识库..." clearable style="width:200px" @input="handleSearch">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新建知识库
        </el-button>
      </div>
    </div>

    <!-- 知识库列表 -->
    <div class="kb-grid" v-if="filteredBases.length > 0">
      <el-card v-for="kb in filteredBases" :key="kb.id" class="kb-card" shadow="hover">
        <template #header>
          <div class="kb-card-header">
            <div class="kb-info">
              <el-icon :size="28" color="#409EFF"><FolderOpened /></el-icon>
              <div class="kb-title">
                <h3>{{ kb.name }}</h3>
                <span class="kb-code">{{ kb.code }}</span>
              </div>
            </div>
            <el-dropdown trigger="click">
              <el-button link><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openDetailDialog(kb)">详情设置</el-dropdown-item>
                  <el-dropdown-item @click="handleDeleteKB(kb)">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        
        <div class="kb-stats">
          <div class="stat-item">
            <span class="stat-label">文档数</span>
            <span class="stat-value">{{ kb.doc_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">向量数</span>
            <span class="stat-value">{{ kb.vector_count || 0 }}</span>
          </div>
        </div>
        
        <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
        
        <div class="kb-footer">
          <span class="kb-date">{{ formatDate(kb.created_at) }}</span>
          <el-button type="primary" size="small" link @click="openDocDialog(kb)">
            <el-icon><Document /></el-icon> 文档管理
          </el-button>
        </div>
      </el-card>
    </div>

    <el-empty v-else description="暂无知识库，点击上方按钮创建">
      <el-button type="primary" @click="openCreateDialog">新建知识库</el-button>
    </el-empty>

    <!-- 新建知识库对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建知识库" width="600px">
      <el-form :model="newKBForm" label-width="100px" :rules="kbRules" ref="kbFormRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="newKBForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="newKBForm.code" placeholder="请输入知识库编码（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newKBForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        
        <el-divider content-position="left">AI 模型配置</el-divider>
        
        <el-form-item label="Embedding">
          <el-select v-model="newKBForm.embedding_model" placeholder="选择模型" style="width:100%">
            <el-option v-for="m in embeddingModels" :key="m.name" :label="m.name" :value="m.name" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Rerank">
          <el-switch v-model="newKBForm.rerank_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        
        <el-form-item label="Rerank模型" v-if="newKBForm.rerank_enabled">
          <el-select v-model="newKBForm.rerank_model" placeholder="选择模型" style="width:100%">
            <el-option label="BAAI/bge-reranker-v2-m3" value="BAAI/bge-reranker-v2-m3" />
            <el-option label="BAAI/bge-reranker-base" value="BAAI/bge-reranker-base" />
            <el-option label="cohere/rerank-multilingual-v2.0" value="cohere/rerank-multilingual-v2.0" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="OCR识别">
          <el-switch v-model="newKBForm.ocr_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        
        <el-form-item label="文本解析">
          <el-switch v-model="newKBForm.text_parse_enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSubmit" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 详情设置对话框 -->
    <el-dialog v-model="detailDialogVisible" title="知识库详情" width="650px">
      <el-form :model="currentKB" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="currentKB.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="currentKB.code" disabled />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="currentKB.description" type="textarea" :rows="3" />
        </el-form-item>
        
        <el-divider content-position="left">AI 模型配置</el-divider>
        
        <el-form-item label="Embedding">
          <el-select v-model="currentKB.embedding_model" style="width:100%">
            <el-option v-for="m in embeddingModels" :key="m.name" :label="m.name" :value="m.name" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="Rerank">
          <el-switch v-model="currentKB.rerank_enabled" />
        </el-form-item>
        
        <el-form-item label="Rerank模型" v-if="currentKB.rerank_enabled">
          <el-select v-model="currentKB.rerank_model" style="width:100%">
            <el-option label="BAAI/bge-reranker-v2-m3" value="BAAI/bge-reranker-v2-m3" />
            <el-option label="BAAI/bge-reranker-base" value="BAAI/bge-reranker-base" />
            <el-option label="cohere/rerank-multilingual-v2.0" value="cohere/rerank-multilingual-v2.0" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="OCR识别">
          <el-switch v-model="currentKB.ocr_enabled" />
        </el-form-item>
        
        <el-form-item label="文本解析">
          <el-switch v-model="currentKB.text_parse_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="detailDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateKB">保存</el-button>
      </template>
    </el-dialog>

    <!-- 文档管理对话框 -->
    <el-dialog v-model="docDialogVisible" title="文档管理" width="900px" :before-close="closeDocDialog">
      <div class="doc-header">
        <el-upload
          :action="`/api/v1/knowledge/upload/${currentKB?.id}`"
          :headers="{ Authorization: `Bearer ${token}` }"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          multiple
          accept=".txt,.md,.pdf,.docx,.xlsx,.csv"
        >
          <el-button type="primary"><el-icon><Upload /></el-icon> 上传文档</el-button>
        </el-upload>
        <el-button @click="refreshDocs" :loading="loadingDocs">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table :data="documents" v-loading="loadingDocs" style="width:100%;margin-top:16px" max-height="400">
        <el-table-column prop="title" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="parsing_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.parsing_status)" size="small">
              {{ getStatusText(row.parsing_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块" width="80" align="center" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.parsing_status === 'pending' || row.parsing_status === 'failed'"
              type="primary" 
              size="small" 
              link 
              @click="handleParseDoc(row)"
            >解析</el-button>
            <el-button type="danger" size="small" link @click="handleDeleteDoc(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Search, FolderOpened, MoreFilled, Document, Upload, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { knowledgeAPI } from '../../common/api'

const token = localStorage.getItem('kflower_token') || ''

// 数据
const knowledgeBases = ref<any[]>([])
const documents = ref<any[]>([])
const searchText = ref('')
const loading = ref(false)
const loadingDocs = ref(false)
const creating = ref(false)

// 对话框
const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const docDialogVisible = ref(false)

// 表单
const kbFormRef = ref<FormInstance>()
const currentKB = ref<any>({})
const newKBForm = ref({
  name: '',
  code: '',
  description: '',
  embedding_model: 'BAAI/bge-m3',
  rerank_enabled: false,
  rerank_model: 'BAAI/bge-reranker-v2-m3',
  ocr_enabled: true,
  text_parse_enabled: true
})

// AI模型选项
const embeddingModels = ref<any[]>([
  { name: 'BAAI/bge-m3', dimension: 1024, available: true },
  { name: 'BAAI/bge-large-zh-v1.5', dimension: 1024, available: true },
  { name: 'shibing624/text2vec-base-chinese', dimension: 768, available: true }
])

const rerankModels = ref<any[]>([
  { name: 'BAAI/bge-reranker-v2-m3', provider: '本地/云端' },
  { name: 'BAAI/bge-reranker-base', provider: '本地/云端' },
  { name: 'cohere/rerank-multilingual-v2.0', provider: 'Cohere' }
])

const kbRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

// 计算属性
const filteredBases = computed(() => {
  if (!searchText.value) return knowledgeBases.value
  const keyword = searchText.value.toLowerCase()
  return knowledgeBases.value.filter(kb => 
    kb.name?.toLowerCase().includes(keyword) || 
    kb.code?.toLowerCase().includes(keyword)
  )
})

// 方法
function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatFileSize(size: number) {
  if (!size) return '-'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / 1024 / 1024).toFixed(1) + ' MB'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    completed: 'success',
    processing: 'warning',
    pending: 'info',
    failed: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    completed: '已完成',
    processing: '处理中',
    pending: '等待中',
    failed: '失败'
  }
  return map[status] || status
}

function handleSearch() {
  // 搜索通过计算属性实现
}

async function loadKnowledgeBases() {
  loading.value = true
  try {
    const res: any = await knowledgeAPI.listBases()
    knowledgeBases.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    ElMessage.error('加载知识库失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  newKBForm.value = {
    name: '',
    code: '',
    description: '',
    embedding_model: 'BAAI/bge-m3',
    rerank_enabled: false,
    rerank_model: 'BAAI/bge-reranker-v2-m3',
    ocr_enabled: true,
    text_parse_enabled: true
  }
  createDialogVisible.value = true
}

async function handleCreateSubmit() {
  if (!kbFormRef.value) return
  await kbFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    creating.value = true
    try {
      const res: any = await knowledgeAPI.createBase(newKBForm.value)
      if (res && res.success !== false) {
        ElMessage.success('知识库创建成功')
        createDialogVisible.value = false
        loadKnowledgeBases()
      } else {
        ElMessage.error(res?.message || '创建失败')
      }
    } catch (e: any) {
      ElMessage.error(e.message || '创建失败')
    } finally {
      creating.value = false
    }
  })
}

function openDetailDialog(kb: any) {
  currentKB.value = { ...kb }
  detailDialogVisible.value = true
}

async function handleUpdateKB() {
  try {
    const res: any = await knowledgeAPI.updateBase(currentKB.value.id, {
      name: currentKB.value.name,
      description: currentKB.value.description,
      embedding_model: currentKB.value.embedding_model,
      rerank_enabled: currentKB.value.rerank_enabled,
      rerank_model: currentKB.value.rerank_model || 'BAAI/bge-reranker-v2-m3',
      ocr_enabled: currentKB.value.ocr_enabled,
      text_parse_enabled: currentKB.value.text_parse_enabled
    })
    if (res && res.success !== false) {
      ElMessage.success('更新成功')
      detailDialogVisible.value = false
      loadKnowledgeBases()
    } else {
      ElMessage.error(res?.message || '更新失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '更新失败')
  }
}

async function handleDeleteKB(kb: any) {
  try {
    await ElMessageBox.confirm(`确定要删除知识库 "${kb.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    const res: any = await knowledgeAPI.deleteBase(kb.id)
    if (res && res.success !== false) {
      ElMessage.success('删除成功')
      loadKnowledgeBases()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

async function openDocDialog(kb: any) {
  currentKB.value = { ...kb }
  docDialogVisible.value = true
  await loadDocuments()
}

async function loadDocuments() {
  if (!currentKB.value?.id) return
  loadingDocs.value = true
  try {
    const res: any = await knowledgeAPI.listDocuments(currentKB.value.id)
    documents.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    ElMessage.error('加载文档失败')
  } finally {
    loadingDocs.value = false
  }
}

function refreshDocs() {
  loadDocuments()
}

function closeDocDialog() {
  docDialogVisible.value = false
  currentKB.value = {}
  documents.value = []
}

function beforeUpload(file: File) {
  const isValidType = ['.txt', '.md', '.pdf', '.docx', '.xlsx', '.csv'].some(ext => 
    file.name.toLowerCase().endsWith(ext)
  )
  if (!isValidType) {
    ElMessage.error('只支持上传 txt, md, pdf, docx, xlsx, csv 格式文件')
    return false
  }
  return true
}

function handleUploadSuccess() {
  ElMessage.success('上传成功')
  loadDocuments()
}

function handleUploadError() {
  ElMessage.error('上传失败')
}

async function handleParseDoc(doc: any) {
  try {
    const res: any = await knowledgeAPI.parseDocument(doc.id)
    if (res && res.success !== false) {
      ElMessage.success('解析任务已提交')
      setTimeout(() => loadDocuments(), 2000)
    } else {
      ElMessage.error(res?.message || '解析失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '解析失败')
  }
}

async function handleDeleteDoc(doc: any) {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${doc.title}" 吗？`, '确认删除', {
      type: 'warning'
    })
    const res: any = await knowledgeAPI.deleteDocument(doc.id)
    if (res && res.success !== false) {
      ElMessage.success('删除成功')
      loadDocuments()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.kb-card {
  margin-bottom: 0;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.kb-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.kb-title h3 {
  margin: 0 0 4px;
  font-size: 16px;
}

.kb-code {
  font-size: 12px;
  color: #909399;
}

.kb-stats {
  display: flex;
  gap: 24px;
  margin: 12px 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #409EFF;
}

.kb-desc {
  color: #606266;
  font-size: 13px;
  margin: 12px 0;
  min-height: 40px;
}

.kb-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.kb-date {
  font-size: 12px;
  color: #c0c4cc;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
