<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <div class="header-actions">
            <el-button @click="showCreateKB = true">
              <el-icon><Plus /></el-icon> 新建知识库
            </el-button>
            <el-button type="primary" @click="openUploadDialog">
              <el-icon><Upload /></el-icon> 上传文档
            </el-button>
          </div>
        </div>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="知识库列表" name="list">
          <el-empty v-if="kbList.length === 0" description="暂无知识库，请先创建" />
          <el-row :gutter="20" v-else>
            <el-col :span="8" v-for="kb in kbList" :key="kb.id">
              <el-card shadow="hover" class="kb-card">
                <div class="kb-header">
                  <el-icon :size="24" color="#409EFF"><Document /></el-icon>
                  <h3>{{ kb.name }}</h3>
                  <el-dropdown trigger="click" @click.stop>
                    <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="editKB(kb)"><el-icon><Edit /></el-icon> 编辑</el-dropdown-item>
                        <el-dropdown-item @click="queryKB(kb)"><el-icon><Search /></el-icon> 检索</el-dropdown-item>
                        <el-dropdown-item @click="viewDocuments(kb)"><el-icon><List /></el-icon> 查看文档</el-dropdown-item>
                        <el-dropdown-item @click="uploadToKB(kb)"><el-icon><Upload /></el-icon> 上传文档</el-dropdown-item>
                        <el-dropdown-item divided @click="deleteKB(kb)"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
                <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
                <div class="kb-meta">
                  <el-tag size="small" type="info">文档数: {{ kb.doc_count || 0 }}</el-tag>
                  <el-tag size="small" v-if="kb.embedding_model" type="warning">{{ kb.embedding_model }}</el-tag>
                  <el-tag size="small" v-if="kb.rerank_enabled" type="danger">重排</el-tag>
                  <el-tag size="small" type="success" v-if="kb.is_active">已启用</el-tag>
                </div>
                <div class="kb-actions">
                  <el-button size="small" type="primary" @click="queryKB(kb)">检索</el-button>
                  <el-button size="small" @click="viewDocuments(kb)">查看文档</el-button>
                  <el-button size="small" @click="uploadToKB(kb)">上传</el-button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        <el-tab-pane label="智能检索" name="query">
          <div class="query-section">
            <el-input 
              v-model="queryText" 
              placeholder="输入检索内容，例如：请假流程如何申请？" 
              size="large" 
              class="query-input"
              @keyup.enter="doQuery"
            >
              <template #append>
                <el-button type="primary" @click="doQuery" :loading="querying">
                  <el-icon><Search /></el-icon> 检索
                </el-button>
              </template>
            </el-input>
            <div class="query-options">
              <el-select v-model="selectedKB" placeholder="全部知识库" clearable style="width: 200px">
                <el-option 
                  v-for="kb in kbList" 
                  :key="kb.id" 
                  :label="kb.name" 
                  :value="kb.id" 
                />
              </el-select>
              <el-slider v-model="topK" :min="1" :max="10" show-stops style="width: 200px" />
              <span class="slider-label">返回 {{ topK }} 条结果</span>
            </div>
          </div>
          <div v-if="queryResults.length > 0" class="results">
            <h4>检索结果</h4>
            <el-card v-for="(r, i) in queryResults" :key="i" class="result-item" shadow="hover">
              <div class="result-header">
                <h4>{{ r.title || '文档 ' + (i+1) }}</h4>
                <el-tag size="small" type="success">相关度: {{ (r.score * 100).toFixed(1) }}%</el-tag>
              </div>
              <p class="result-content">{{ r.text || r.content }}</p>
              <div class="result-source" v-if="r.metadata?.source">
                <el-tag size="small" type="info">来源: {{ r.metadata.source }}</el-tag>
              </div>
            </el-card>
          </div>
          <el-empty v-else-if="hasQueried" description="未找到相关内容" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新建/编辑知识库对话框 -->
    <el-dialog v-model="showCreateKB" :title="editingKB ? '编辑知识库' : '新建知识库'" width="600px">
      <el-form :model="createKBForm" label-width="100px" :rules="kbRules" ref="kbFormRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createKBForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="createKBForm.code" placeholder="可选，用于API调用" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createKBForm.description" type="textarea" :rows="3" placeholder="请输入知识库描述" />
        </el-form-item>
        <el-form-item label="嵌入模型">
          <el-select v-model="createKBForm.embedding_model" placeholder="选择嵌入模型" style="width: 100%" filterable>
            <el-option-group label="API 模型">
              <el-option v-for="m in apiEmbeddingModels" :key="m.value" :label="m.label" :value="m.value">
                <span>{{ m.label }}</span>
                <span style="color:#999;font-size:12px;margin-left:8px">{{ m.desc }}</span>
              </el-option>
            </el-option-group>
            <el-option-group label="本地模型 (sentence-transformers)" v-if="localEmbeddingModels.length > 0">
              <el-option v-for="m in localEmbeddingModels" :key="m.value" :label="m.label" :value="m.value" :disabled="!m.available">
                <span>{{ m.label }}</span>
                <span style="color:#67c23a;font-size:12px;margin-left:8px">本地</span>
                <span style="color:#999;font-size:12px;margin-left:4px">{{ m.desc }}</span>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="检索重排">
          <el-switch v-model="createKBForm.rerank_enabled" active-text="启用" inactive-text="关闭" />
          <div style="font-size:12px;color:#999;margin-top:4px">启用后检索结果将通过AI模型重排序，提高相关性</div>
        </el-form-item>
        <el-form-item label="重排模型" v-if="createKBForm.rerank_enabled">
          <el-select v-model="createKBForm.rerank_model" placeholder="选择重排模型" style="width: 100%" filterable allow-create default-first-option>
            <el-option-group label="Rerank 专用模型">
              <el-option v-for="m in rerankModels" :key="m.value" :label="m.label" :value="m.value">
                <span>{{ m.label }}</span>
                <span style="color:#e6a23c;font-size:12px;margin-left:8px">Rerank</span>
              </el-option>
            </el-option-group>
            <el-option-group label="系统AI模型（LLM重排）">
              <el-option v-for="m in configuredModels" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId">
                <span>{{ m.modelName || m.modelId }}</span>
                <el-tag size="small" type="info" style="margin-left:8px">{{ getProviderName(m.provider) }}</el-tag>
              </el-option>
            </el-option-group>
          </el-select>
          <div style="font-size:12px;color:#999;margin-top:4px">
            可选Rerank专用模型（更精准）或已配置的AI模型（LLM打分排序），也可直接输入模型ID
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateKB = false">取消</el-button>
        <el-button type="primary" @click="createOrUpdateKB" :loading="creating">{{ editingKB ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>

    <!-- 上传文档对话框（支持单文件/多文件/批量上传） -->
    <el-dialog v-model="showUpload" title="上传文档" width="650px" destroy-on-close>
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="知识库" required>
          <el-select v-model="uploadForm.kb_id" placeholder="选择知识库" style="width: 100%">
            <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传文件" required>
          <el-upload
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="uploadFileList"
            :on-remove="handleFileRemove"
            multiple
            accept=".pdf,.docx,.txt,.md,.doc,.xlsx,.xls,.ppt,.pptx,.png,.jpg,.jpeg,.bmp,.gif,.tiff"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击选择</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                <p>支持格式：PDF、Word、Excel、PPT、TXT、Markdown、图片（PNG/JPG/BMP/GIF/TIFF）</p>
                <p>支持同时选择多个文件批量上传，单个文件不超过 100MB</p>
                <p>图片文件将自动OCR识别，文档将自动提取文字和关键词</p>
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="自动解析">
          <el-switch v-model="uploadForm.auto_parse" active-text="上传后自动解析" inactive-text="手动触发解析" />
          <div style="font-size:12px;color:#999;margin-top:4px">
            自动解析：上传后立即提取文字、关键词、摘要并生成向量。关闭则需要手动点击解析。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="uploadDocs" :loading="uploading" :disabled="uploadFileList.length === 0">
          上传 {{ uploadFileList.length }} 个文件
        </el-button>
      </template>
    </el-dialog>

    <!-- 文档列表对话框 -->
    <el-dialog v-model="showDocs" :title="`文档列表 - ${currentKB?.name || ''}`" width="850px">
      <div class="doc-toolbar">
        <el-button type="primary" size="small" @click="uploadToKB(currentKB)">
          <el-icon><Upload /></el-icon> 上传文档
        </el-button>
        <el-button size="small" @click="parseAllDocs" :loading="parsingAll">
          <el-icon><MagicStick /></el-icon> 解析全部
        </el-button>
        <el-button size="small" @click="loadDocuments" :loading="loadingDocs">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
      <el-table :data="documentList" v-loading="loadingDocs" border stripe>
        <el-table-column prop="title" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getFileTypeTag(row.file_type)">{{ row.file_type?.toUpperCase() || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="parsing_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.parsing_status)" size="small">{{ getStatusLabel(row.parsing_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块" width="70">
          <template #default="{ row }">
            {{ row.chunk_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="parseDocument(row)" 
              :disabled="row.parsing_status === 'processing'" :loading="row.parsing_status === 'processing'">
              {{ row.parsing_status === 'pending' ? '解析' : '重新解析' }}
            </el-button>
            <el-button size="small" text @click="viewDocContent(row)">查看内容</el-button>
            <el-button size="small" type="danger" text @click="deleteDocument(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 文档内容查看对话框 -->
    <el-dialog v-model="showDocContent" title="文档内容" width="700px">
      <div v-if="currentDoc" class="doc-content-view">
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
          <el-descriptions-item label="文件名">{{ currentDoc.title }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ currentDoc.file_type }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatFileSize(currentDoc.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ getStatusLabel(currentDoc.parsing_status) }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="currentDoc.content" class="doc-text-content">
          <h4>提取的文字内容</h4>
          <el-scrollbar max-height="300px">
            <pre class="content-text">{{ currentDoc.content }}</pre>
          </el-scrollbar>
        </div>
        <el-empty v-else description="文档尚未解析，请先点击解析" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Search, Document, UploadFilled, Edit, Delete, List, MoreFilled, MagicStick, Refresh } from '@element-plus/icons-vue'
import { knowledgeAPI, systemAPI } from '../../api'

const kbList = ref<any[]>([])
const activeTab = ref('list')
const showUpload = ref(false)
const showCreateKB = ref(false)
const showDocs = ref(false)
const showDocContent = ref(false)
const loadingDocs = ref(false)
const documentList = ref<any[]>([])
const currentKB = ref<any>(null)
const currentDoc = ref<any>(null)
const editingKB = ref<any>(null)
const parsingAll = ref(false)
const configuredModels = ref<any[]>([])

const createKBForm = reactive({
  name: '',
  code: '',
  description: '',
  embedding_model: 'text-embedding-v2',
  rerank_model: '',
  rerank_enabled: false
})

const kbRules = {
  name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }]
}

const kbFormRef = ref()
const creating = ref(false)

const uploadForm = reactive({ kb_id: null as number | null, auto_parse: true })
const uploadFileList = ref<any[]>([])
const uploading = ref(false)

const queryText = ref('')
const queryResults = ref<any[]>([])
const querying = ref(false)
const hasQueried = ref(false)
const selectedKB = ref<number | null>(null)
const topK = ref(5)

// 嵌入模型列表
const apiEmbeddingModels = ref([
  { value: 'text-embedding-v2', label: 'text-embedding-v2', desc: 'DashScope 1536维' },
  { value: 'text-embedding-v3', label: 'text-embedding-v3', desc: 'DashScope 1024维' },
  { value: 'text-embedding-3-small', label: 'text-embedding-3-small', desc: 'OpenAI 1536维' },
  { value: 'text-embedding-3-large', label: 'text-embedding-3-large', desc: 'OpenAI 3072维' },
])

const localEmbeddingModels = ref<any[]>([
  { value: 'all-MiniLM-L6-v2', label: 'all-MiniLM-L6-v2', desc: '英文轻量(80MB)', available: true },
  { value: 'paraphrase-multilingual-MiniLM-L12-v2', label: 'multilingual-MiniLM-L12', desc: '多语言(420MB)', available: true },
  { value: 'paraphrase-multilingual-mpnet-base-v2', label: 'multilingual-mpnet-base', desc: '多语言高质量(970MB)', available: true },
  { value: 'shibing624/text2vec-base-chinese', label: 'text2vec-base-chinese', desc: '中文(400MB)', available: true },
  { value: 'moka-ai/m3e-small', label: 'M3E-small', desc: '中文小型(512维)', available: true },
  { value: 'moka-ai/m3e-base', label: 'M3E-base', desc: '中文基础(768维)', available: true },
  { value: 'moka-ai/m3e-large', label: 'M3E-large', desc: '中文大型(1024维)', available: true },
  { value: 'BAAI/bge-small-zh-v1.5', label: 'BGE-small-zh', desc: '中文小型(512维)', available: true },
  { value: 'BAAI/bge-base-zh-v1.5', label: 'BGE-base-zh', desc: '中文基础(768维)', available: true },
  { value: 'BAAI/bge-large-zh-v1.5', label: 'BGE-large-zh', desc: '中文大型(1024维)', available: true },
])

// Rerank 模型列表
const rerankModels = ref([
  { value: 'BAAI/bge-reranker-v2-m3', label: 'BGE-reranker-v2-m3', desc: '多语言重排' },
  { value: 'BAAI/bge-reranker-large', label: 'BGE-reranker-large', desc: '大型重排' },
  { value: 'BAAI/bge-reranker-base', label: 'BGE-reranker-base', desc: '基础重排' },
])

// 尝试从后端加载模型列表
async function loadEmbeddingModels() {
  try {
    // 优先从系统配置加载已配置的嵌入模型
    const configRes: any = await systemAPI.getConfig()
    if (configRes.data?.embed_models) {
      const models = typeof configRes.data.embed_models === 'string' 
        ? JSON.parse(configRes.data.embed_models) 
        : configRes.data.embed_models
      if (Array.isArray(models) && models.length > 0) {
        apiEmbeddingModels.value = models.map((m: any) => ({
          value: m.modelId, 
          label: m.name || m.modelId, 
          desc: m.provider === 'local' ? '本地模型' : `${m.dimension || 768}维`,
          provider: m.provider
        }))
        console.log('从配置加载嵌入模型:', apiEmbeddingModels.value.length)
        return
      }
    }
    
    // 回退到后端模型列表
    const res: any = await systemAPI.listEmbeddingModels()
    if (res.data?.models) {
      const models = res.data.models
      if (Array.isArray(models)) {
        const stAvailable = !!res.data.st_available
        const apiModels = models.filter((m: any) => m.provider === 'api')
        const localModels = models.filter((m: any) => m.provider === 'local')
        if (apiModels.length) {
          apiEmbeddingModels.value = apiModels.map((m: any) => ({
            value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`
          }))
        }
        if (localModels.length) {
          localEmbeddingModels.value = localModels.map((m: any) => ({
            value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`, available: stAvailable && m.available
          }))
        }
      }
    }
  } catch (e) {
    console.error('加载嵌入模型列表失败:', e)
    // 使用默认列表（已在 ref 中定义）
  }
}

// 尝试从后端加载重排模型列表
async function loadRerankModels() {
  try {
    // 从系统配置加载已配置的重排模型
    const configRes: any = await systemAPI.getConfig()
    if (configRes.data?.rerank_models) {
      const models = typeof configRes.data.rerank_models === 'string' 
        ? JSON.parse(configRes.data.rerank_models) 
        : configRes.data.rerank_models
      if (Array.isArray(models) && models.length > 0) {
        rerankModels.value = models.map((m: any) => ({
          value: m.modelId, 
          label: m.name || m.modelId, 
          desc: '重排模型'
        }))
        console.log('从配置加载重排模型:', rerankModels.value.length)
        return
      }
    }
    // 使用默认列表（已在 ref 中定义）
    console.log('使用默认重排模型列表')
  } catch (e) {
    console.error('加载重排模型列表失败:', e)
    // 使用默认列表
  }
}

onMounted(async () => {
  await Promise.all([loadKBs(), loadEmbeddingModels(), loadRerankModels(), loadConfiguredModels()])
})

const loadKBs = async () => {
  try {
    const res: any = await knowledgeAPI.listBases()
    kbList.value = Array.isArray(res) ? res : (res.items || res.data || [])
  } catch (e) {
    console.error(e)
    ElMessage.error('加载知识库失败')
  }
}

const loadConfiguredModels = async () => {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.ai_models) {
      try {
        const models = typeof config.ai_models === 'string' ? JSON.parse(config.ai_models) : config.ai_models
        configuredModels.value = Array.isArray(models) ? models : []
      } catch { configuredModels.value = [] }
    }
  } catch { /* ignore */ }
}

const getProviderName = (id: string) => {
  const names: Record<string, string> = {
    siliconflow: 'SiliconFlow', deepseek: 'DeepSeek', qwen: '通义千问',
    openai: 'OpenAI', moonshot: 'Moonshot', zhipu: '智谱AI', ollama: 'Ollama',
    baidu: '百度文心', minimax: 'MiniMax', custom: '自定义'
  }
  return names[id] || id
}

const editKB = (kb: any) => {
  editingKB.value = kb
  createKBForm.name = kb.name
  createKBForm.code = kb.code || ''
  createKBForm.description = kb.description || ''
  createKBForm.embedding_model = kb.embedding_model || 'text-embedding-v2'
  createKBForm.rerank_model = kb.rerank_model || ''
  createKBForm.rerank_enabled = kb.rerank_enabled || false
  showCreateKB.value = true
}

const createOrUpdateKB = async () => {
  const valid = await kbFormRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    if (editingKB.value) {
      await knowledgeAPI.updateBase?.(editingKB.value.id, {
        name: createKBForm.name,
        description: createKBForm.description,
        embedding_model: createKBForm.embedding_model,
        rerank_model: createKBForm.rerank_model || undefined,
        rerank_enabled: createKBForm.rerank_enabled
      })
      ElMessage.success('知识库更新成功')
    } else {
      await knowledgeAPI.createBase({
        name: createKBForm.name,
        code: createKBForm.code || undefined,
        description: createKBForm.description,
        embedding_model: createKBForm.embedding_model,
        rerank_model: createKBForm.rerank_model || undefined,
        rerank_enabled: createKBForm.rerank_enabled
      })
      ElMessage.success('知识库创建成功')
    }
    showCreateKB.value = false
    editingKB.value = null
    createKBForm.name = ''
    createKBForm.code = ''
    createKBForm.description = ''
    createKBForm.embedding_model = 'text-embedding-v2'
    createKBForm.rerank_model = ''
    createKBForm.rerank_enabled = false
    await loadKBs()
  } catch (e: any) {
    ElMessage.error(e.message || (editingKB.value ? '更新失败' : '创建失败'))
  } finally {
    creating.value = false
  }
}

const deleteKB = async (kb: any) => {
  try {
    await ElMessageBox.confirm(`确定删除知识库 "${kb.name}" 吗？删除后不可恢复。`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeAPI.deleteBase?.(kb.id)
    ElMessage.success('删除成功')
    await loadKBs()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const queryKB = (kb: any) => {
  activeTab.value = 'query'
  selectedKB.value = kb.id
}

const openUploadDialog = () => {
  uploadForm.kb_id = kbList.value.length > 0 ? kbList.value[0].id : null
  uploadForm.auto_parse = true
  uploadFileList.value = []
  showUpload.value = true
}

const uploadToKB = (kb: any) => {
  uploadForm.kb_id = kb.id
  uploadForm.auto_parse = true
  uploadFileList.value = []
  showUpload.value = true
}

const viewDocuments = async (kb: any) => {
  currentKB.value = kb
  showDocs.value = true
  await loadDocuments()
}

const loadDocuments = async () => {
  if (!currentKB.value) return
  loadingDocs.value = true
  try {
    const res: any = await knowledgeAPI.listDocuments?.(currentKB.value.id)
    documentList.value = Array.isArray(res) ? res : (res.items || res.data || [])
  } catch (e) {
    documentList.value = []
  } finally {
    loadingDocs.value = false
  }
}

const parseDocument = async (doc: any) => {
  try {
    await knowledgeAPI.parseDocument?.(doc.id)
    ElMessage.success('文档解析已启动')
    await loadDocuments()
  } catch (e: any) {
    ElMessage.error(e.message || '解析失败')
  }
}

const parseAllDocs = async () => {
  if (!currentKB.value) return
  parsingAll.value = true
  try {
    await knowledgeAPI.parseAll?.(currentKB.value.id)
    ElMessage.success('批量解析已启动')
    await loadDocuments()
  } catch (e: any) {
    ElMessage.error(e.message || '批量解析失败')
  } finally {
    parsingAll.value = false
  }
}

const viewDocContent = async (doc: any) => {
  try {
    const res: any = await knowledgeAPI.getDocument(doc.id)
    currentDoc.value = res
  } catch {
    currentDoc.value = doc  // fallback 到列表数据
  }
  showDocContent.value = true
}

const deleteDocument = async (doc: any) => {
  try {
    await ElMessageBox.confirm(`确定删除文档 "${doc.title || doc.file_name}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await knowledgeAPI.deleteDocument?.(doc.id)
    ElMessage.success('删除成功')
    await loadDocuments()
    await loadKBs()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const doQuery = async () => {
  if (!queryText.value.trim()) {
    ElMessage.warning('请输入检索内容')
    return
  }
  querying.value = true
  hasQueried.value = true
  try {
    const res: any = await knowledgeAPI.query({
      query: queryText.value,
      kb_id: selectedKB.value || undefined,
      top_k: topK.value
    })
    queryResults.value = res.results || res.data || []
  } catch (e: any) {
    ElMessage.error(e.message || '检索失败')
    queryResults.value = []
  } finally {
    querying.value = false
  }
}

const handleFileChange = (file: any, fileList: any[]) => {
  uploadFileList.value = fileList
}

const handleFileRemove = (file: any, fileList: any[]) => {
  uploadFileList.value = fileList
}

const uploadDocs = async () => {
  if (!uploadForm.kb_id) {
    ElMessage.warning('请选择知识库')
    return
  }
  if (uploadFileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  let successCount = 0
  let failCount = 0

  try {
    // 逐个上传文件
    for (const file of uploadFileList.value) {
      try {
        const formData = new FormData()
        formData.append('file', file.raw)
        formData.append('auto_parse', String(uploadForm.auto_parse))
        
        // 参考模板设计的上传逻辑，使用fetch直接调用API
        const res = await (window as any).fetch(`/api/v1/knowledge/upload/${uploadForm.kb_id}`, {
          method: 'POST',
          headers: { Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '') },
          body: formData
        })
        
        const json = await res.json()
        if (json.success) {
          successCount++
        } else {
          failCount++
          console.error('上传失败:', json.message || '未知错误')
        }
      } catch (e: any) {
        failCount++
        console.error('上传失败:', e.message)
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功上传 ${successCount} 个文件${failCount > 0 ? `，${failCount} 个失败` : ''}`)
      showUpload.value = false
      uploadFileList.value = []
      await loadKBs()
      // 如果文档列表正在显示，刷新它
      if (showDocs.value && currentKB.value?.id === uploadForm.kb_id) {
        await loadDocuments()
      }
    } else {
      ElMessage.error('所有文件上传失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

const formatFileSize = (size: number) => {
  if (!size) return '0 B'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    'pending': '待解析',
    'processing': '解析中',
    'completed': '已完成',
    'failed': '失败'
  }
  return labels[status] || status || '未知'
}

const getFileTypeTag = (type: string) => {
  if (!type) return 'info'
  const docTypes = ['pdf', 'docx', 'doc', 'txt', 'md']
  const imgTypes = ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff']
  const sheetTypes = ['xlsx', 'xls', 'csv']
  if (imgTypes.includes(type?.toLowerCase())) return 'warning'
  if (sheetTypes.includes(type?.toLowerCase())) return 'success'
  if (docTypes.includes(type?.toLowerCase())) return 'primary'
  return 'info'
}
</script>

<style scoped>
.page-container { padding: 20px; }
.card-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.kb-card { 
  margin-bottom: 20px;
  transition: all 0.3s;
}
.kb-card:hover {
  transform: translateY(-2px);
}
.kb-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.kb-header h3 { 
  margin: 0;
  font-size: 16px;
  flex: 1;
}
.kb-desc { 
  color: #666; 
  margin: 0 0 10px;
  font-size: 14px;
  min-height: 40px;
}
.kb-meta { 
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.kb-actions {
  display: flex;
  gap: 8px;
}
.query-section {
  margin: 20px 0;
}
.query-input { 
  margin-bottom: 15px;
}
.query-options {
  display: flex;
  align-items: center;
  gap: 20px;
}
.slider-label {
  color: #666;
  font-size: 14px;
}
.results { 
  margin-top: 20px;
}
.results h4 {
  margin-bottom: 15px;
  color: #303133;
}
.result-item { 
  margin-bottom: 15px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.result-header h4 { 
  margin: 0;
  font-size: 15px;
}
.result-content { 
  margin: 0 0 10px; 
  color: #606266;
  line-height: 1.6;
}
.result-source {
  margin-top: 10px;
}
.doc-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.doc-content-view {
  padding: 10px 0;
}
.doc-text-content h4 {
  margin: 0 0 10px;
  color: #303133;
}
.content-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin: 0;
}
.upload-area {
  width: 100%;
}
</style>
