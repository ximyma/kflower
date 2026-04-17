<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- AI模型管理 -->
      <el-tab-pane label="AI模型管理" name="ai-models">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI 模型配置</span>
              <el-button type="primary" size="small" @click="openAddModelDialog">
                <el-icon><Plus /></el-icon> 添加模型
              </el-button>
            </div>
          </template>
          
          <el-table :data="aiModels" style="width:100%" v-loading="loadingModels">
            <el-table-column prop="provider" label="供应商" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getProviderName(row.provider) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="modelId" label="模型ID" min-width="180" />
            <el-table-column prop="modelName" label="模型名称" width="150" />
            <el-table-column prop="isDefault" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.isDefault" type="success" size="small">默认</el-tag>
                <el-tag v-else type="info" size="small">-</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="configured" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.configured ? 'success' : 'info'" size="small">
                  {{ row.configured ? '已配置' : '未配置' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="editModel(row)">编辑</el-button>
                <el-button type="danger" size="small" link @click="deleteModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 模块AI配置 -->
        <el-card style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>模块 AI 模型分配</span>
            </div>
          </template>
          <el-form label-width="140px">
            <el-form-item label="智能助手">
              <el-select v-model="moduleSettings.chatGeneral" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="模板设计">
              <el-select v-model="moduleSettings.chatTemplate" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="流程审批">
              <el-select v-model="moduleSettings.chatWorkflow" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="决策分析">
              <el-select v-model="moduleSettings.chatAnalytics" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveModuleSettings">保存模块配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 本地模型配置 -->
      <el-tab-pane label="本地模型" name="local">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Ollama 本地模型配置</span>
              <el-button type="primary" size="small" @click="openAddLocalModelDialog">
                <el-icon><Plus /></el-icon> 添加 Ollama 连接
              </el-button>
            </div>
          </template>
          
          <el-table :data="localModels" style="width:100%" v-loading="loadingLocalModels">
            <el-table-column prop="name" label="连接名称" width="150" />
            <el-table-column prop="url" label="Ollama 地址" min-width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'connected' ? 'success' : 'info'" size="small">
                  {{ row.status === 'connected' ? '已连接' : '未连接' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="models" label="可用模型" min-width="200">
              <template #default="{ row }">
                <el-tag v-for="m in row.models?.slice(0, 3)" :key="m" size="small" style="margin-right:4px">{{ m }}</el-tag>
                <el-tag v-if="row.models?.length > 3" size="small">+{{ row.models.length - 3 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="testOllamaConnection(row)">测试</el-button>
                <el-button type="danger" size="small" link @click="deleteLocalModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        
        <el-card style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>Rerank 模型配置</span>
            </div>
          </template>
          
          <el-form label-width="140px">
            <el-form-item label="启用 Rerank">
              <el-switch v-model="rerankConfig.enabled" />
            </el-form-item>
            
            <el-form-item label="Rerank 模型">
              <el-select v-model="rerankConfig.model" style="width:300px" :disabled="!rerankConfig.enabled">
                <el-option label="BAAI/bge-reranker-v2-m3" value="BAAI/bge-reranker-v2-m3" />
                <el-option label="BAAI/bge-reranker-base" value="BAAI/bge-reranker-base" />
                <el-option label="cohere/rerank-multilingual-v2.0" value="cohere/rerank-multilingual-v2.0" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="API Key" v-if="rerankConfig.enabled">
              <el-input v-model="rerankConfig.apiKey" type="password" show-password style="width:300px" placeholder="Rerank API Key" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveRerankConfig" :loading="savingRerank">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- Embedding配置 -->
      <el-tab-pane label="Embedding配置" name="embedding">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>向量嵌入模型配置</span>
            </div>
          </template>
          
          <el-form label-width="140px">
            <el-form-item label="当前Embedding">
              <el-select v-model="embeddingConfig.model" style="width:300px">
                <el-option
                  v-for="m in embeddingModels"
                  :key="m.name"
                  :label="`${m.name} (${m.dimension}维)`"
                  :value="m.name"
                  :disabled="!m.available"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="sentence-transformers">
              <el-tag :type="embeddingConfig.stAvailable ? 'success' : 'danger'">
                {{ embeddingConfig.stAvailable ? '已安装' : '未安装' }}
              </el-tag>
              <span v-if="!embeddingConfig.stAvailable" style="margin-left:12px;color:#909399;font-size:12px">
                请运行: pip install sentence-transformers
              </span>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveEmbeddingConfig" :loading="savingEmbedding">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 本地工具 -->
      <el-tab-pane label="本地工具" name="tools">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>本地 AI 工具配置</span>
            </div>
          </template>
          
          <el-table :data="localTools" style="width:100%">
            <el-table-column prop="name" label="工具名称" width="150" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="enabled" label="启用" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" @change="toggleTool(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="testTool(row)">测试</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        
        <el-card style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>添加本地工具</span>
            </div>
          </template>
          
          <el-form label-width="140px">
            <el-form-item label="工具类型">
              <el-select v-model="newTool.type" style="width:200px">
                <el-option label="OCR 文字识别" value="ocr" />
                <el-option label="文本解析" value="text_parser" />
                <el-option label="Embedding 向量" value="embedding" />
                <el-option label="自定义 API" value="custom_api" />
              </el-select>
            </el-form-item>
            <el-form-item label="工具名称">
              <el-input v-model="newTool.name" style="width:300px" placeholder="工具名称" />
            </el-form-item>
            <el-form-item label="API 地址" v-if="newTool.type === 'custom_api'">
              <el-input v-model="newTool.apiUrl" style="width:400px" placeholder="http://localhost:xxxx/api" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="addLocalTool">添加工具</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 基本配置 -->
      <el-tab-pane label="基本配置" name="basic">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统基本信息</span>
            </div>
          </template>
          
          <el-form label-width="140px">
            <el-form-item label="系统名称">
              <el-input v-model="basicConfig.appName" style="width:300px" />
            </el-form-item>
            
            <el-form-item label="系统主题">
              <el-radio-group v-model="basicConfig.theme">
                <el-radio label="light">浅色</el-radio>
                <el-radio label="dark">深色</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBasicConfig" :loading="savingBasic">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 系统健康 -->
      <el-tab-pane label="系统健康" name="health">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统运行状态</span>
              <el-button link @click="loadHealth"><el-icon><Refresh /></el-icon> 刷新</el-button>
            </div>
          </template>
          
          <el-row :gutter="20" v-loading="loadingHealth">
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon cpu"><el-icon><Cpu /></el-icon></div>
                <div class="health-info">
                  <span class="health-label">CPU 使用</span>
                  <span class="health-value">{{ healthData.cpu_percent?.toFixed(1) }}%</span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon mem"><el-icon><Monitor /></el-icon></div>
                <div class="health-info">
                  <span class="health-label">内存使用</span>
                  <span class="health-value">{{ healthData.memory_percent?.toFixed(1) }}%</span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon disk"><el-icon><Folder /></el-icon></div>
                <div class="health-info">
                  <span class="health-label">磁盘使用</span>
                  <span class="health-value">{{ healthData.disk_percent?.toFixed(1) }}%</span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon status" :class="healthData.status">
                  <el-icon><CircleCheck v-if="healthData.status === 'healthy'" /><CircleClose v-else /></el-icon>
                </div>
                <div class="health-info">
                  <span class="health-label">系统状态</span>
                  <span class="health-value">{{ healthData.status === 'healthy' ? '正常' : '异常' }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加AI模型对话框 -->
    <el-dialog v-model="showModelDialog" :title="editingModel ? '编辑AI模型' : '添加AI模型'" width="700px">
      <el-form :model="modelForm" label-width="120px">
        <el-form-item label="AI供应商" required>
          <el-select v-model="modelForm.provider" style="width:100%" @change="handleProviderChange">
            <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型ID" required>
          <el-input v-model="modelForm.modelId" placeholder="如: Qwen/Qwen2.5-7B-Instruct" />
        </el-form-item>
        
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.modelName" placeholder="如: 通义千问 7B" />
        </el-form-item>
        
        <el-form-item label="API Key" v-if="modelForm.provider !== 'ollama'">
          <el-input v-model="modelForm.apiKey" type="password" show-password placeholder="API Key" />
        </el-form-item>
        
        <el-form-item label="API地址" v-if="modelForm.provider !== 'ollama'">
          <el-input v-model="modelForm.baseUrl" placeholder="自定义API地址（可选）" />
        </el-form-item>
        
        <el-divider content-position="left">模型参数</el-divider>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Temperature">
              <el-input-number v-model="modelForm.temperature" :min="0" :max="2" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Top P">
              <el-input-number v-model="modelForm.topP" :min="0" :max="1" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Top K">
              <el-input-number v-model="modelForm.topK" :min="1" :max="100" :step="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Max Tokens">
              <el-input-number v-model="modelForm.maxTokens" :min="1" :max="32768" :step="100" style="width:100%" placeholder="最大输出token数" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="上下文窗口">
              <el-input-number v-model="modelForm.contextWindow" :min="1024" :max="200000" :step="1024" style="width:100%" placeholder="上下文token数" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="频率惩罚">
              <el-input-number v-model="modelForm.frequencyPenalty" :min="-2" :max="2" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="存在惩罚">
              <el-input-number v-model="modelForm.presencePenalty" :min="-2" :max="2" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重复惩罚">
              <el-input-number v-model="modelForm.repeatPenalty" :min="1" :max="2" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">请求配置</el-divider>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Timeout (秒)">
              <el-input-number v-model="modelForm.timeout" :min="10" :max="300" :step="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大重试">
              <el-input-number v-model="modelForm.maxRetries" :min="0" :max="5" :step="1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="流式响应">
              <el-switch v-model="modelForm.stream" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设为默认">
              <el-switch v-model="modelForm.isDefault" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="额外参数">
          <el-input v-model="modelForm.extraParams" type="textarea" :rows="2" placeholder="JSON格式，如: {response_format: 'json'}" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showModelDialog = false">取消</el-button>
        <el-button type="primary" @click="saveModel" :loading="savingModel">{{ editingModel ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加Ollama连接对话框 -->
    <el-dialog v-model="showLocalModelDialog" title="添加 Ollama 连接" width="500px">
      <el-form :model="localModelForm" label-width="100px">
        <el-form-item label="连接名称">
          <el-input v-model="localModelForm.name" placeholder="如: 本地 Ollama" />
        </el-form-item>
        <el-form-item label="Ollama 地址" required>
          <el-input v-model="localModelForm.url" placeholder="http://localhost:11434" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLocalModelDialog = false">取消</el-button>
        <el-button type="primary" @click="addOllamaConnection" :loading="addingLocalModel">添加并测试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Refresh, Cpu, Monitor, Folder, CircleCheck, CircleClose, Document, Files, Setting, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemAPI, localAIAPI } from '../../common/api'

const activeTab = ref('ai-models')

// AI模型管理
const aiModels = ref<any[]>([])
const loadingModels = ref(false)
const showModelDialog = ref(false)
const editingModel = ref<any>(null)
const savingModel = ref(false)

const modelForm = reactive({
  provider: 'siliconflow',
  modelId: '',
  modelName: '',
  apiKey: '',
  baseUrl: '',
  // 模型参数
  temperature: 0.7,
  topP: 0.9,
  topK: 40,
  maxTokens: 8192,
  contextWindow: 32768,
  frequencyPenalty: 0,
  presencePenalty: 0,
  repeatPenalty: 1.1,
  // 请求配置
  timeout: 120,
  maxRetries: 3,
  stream: true,
  // 额外参数
  extraParams: '',
  isDefault: false
})

// 重置模型表单
function resetModelForm() {
  Object.assign(modelForm, {
    provider: 'siliconflow',
    modelId: '',
    modelName: '',
    apiKey: '',
    baseUrl: '',
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    maxTokens: 8192,
    contextWindow: 32768,
    frequencyPenalty: 0,
    presencePenalty: 0,
    repeatPenalty: 1.1,
    timeout: 120,
    maxRetries: 3,
    stream: true,
    extraParams: '',
    isDefault: false
  })
}

// 模块AI配置
const moduleSettings = reactive({
  chatGeneral: '',
  chatTemplate: '',
  chatWorkflow: '',
  chatAnalytics: '',
  ragModel: '',
  processingModel: ''
})

// 可用于选择的模型列表
const availableModelsForSelect = computed(() => aiModels.value.filter(m => m.configured))

// 本地模型配置
const localModels = ref<any[]>([])
const loadingLocalModels = ref(false)
const showLocalModelDialog = ref(false)
const addingLocalModel = ref(false)

const localModelForm = reactive({
  name: '',
  url: 'http://localhost:11434'
})

// Rerank配置
const rerankConfig = reactive({
  enabled: false,
  model: 'BAAI/bge-reranker-v2-m3',
  apiKey: ''
})
const savingRerank = ref(false)

// Embedding配置
const embeddingConfig = reactive({
  model: 'BAAI/bge-m3',
  stAvailable: false
})
const embeddingModels = ref<any[]>([])
const savingEmbedding = ref(false)

// 本地工具配置
const localTools = ref<any[]>([
  { name: 'OCR 文字识别', type: 'OCR', description: '从图片中提取文字，支持中文、英文、表格', enabled: true },
  { name: '文本解析', type: 'TextParser', description: '文本分词、关键词提取、摘要生成', enabled: true },
  { name: 'Embedding 向量', type: 'Embedding', description: '文本向量化处理', enabled: true }
])

const newTool = reactive({
  type: 'ocr',
  name: '',
  apiUrl: ''
})

// 基本配置
const basicConfig = reactive({
  appName: 'Kflower 企业智能管理低代码平台',
  theme: 'light'
})
const savingBasic = ref(false)

// 健康检查
const healthData = ref<any>({
  cpu_percent: 0,
  memory_percent: 0,
  disk_percent: 0,
  status: 'healthy'
})
const loadingHealth = ref(false)

// AI提供商列表
const providers = ref<any[]>([
  { id: 'siliconflow', name: 'SiliconFlow' },
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'zhipuai', name: '智谱AI' },
  { id: 'dashscope', name: '阿里云百炼' },
  { id: 'openai', name: 'OpenAI' },
  { id: 'ollama', name: 'Ollama (本地)' }
])

function getProviderName(id: string) {
  return providers.value.find(p => p.id === id)?.name || id
}

// 加载AI模型列表
async function loadAiModels() {
  loadingModels.value = true
  try {
    const res: any = await systemAPI.getConfig()
    if (res && res.success !== false) {
      const data = res.data || {}
      
      // 解析已保存的模型列表
      if (data.ai_models) {
        try {
          aiModels.value = typeof data.ai_models === 'string' ? JSON.parse(data.ai_models) : data.ai_models
        } catch { aiModels.value = [] }
      }
      
      // 解析模块配置
      if (data.module_ai_settings) {
        try {
          const settings = typeof data.module_ai_settings === 'string' ? JSON.parse(data.module_ai_settings) : data.module_ai_settings
          Object.assign(moduleSettings, settings)
        } catch {}
      }
    }
  } catch (e) {
    console.warn('Failed to load AI models')
  } finally {
    loadingModels.value = false
  }
}

// 添加模型对话框
function openAddModelDialog() {
  editingModel.value = null
  resetModelForm()
  showModelDialog.value = true
}

// 编辑模型
function editModel(row: any) {
  editingModel.value = row
  // 确保所有参数都有默认值
  resetModelForm()
  const params = row.params || {}
  Object.assign(modelForm, {
    provider: row.provider || 'siliconflow',
    modelId: row.modelId || '',
    modelName: row.modelName || '',
    apiKey: row.apiKey || '',
    baseUrl: row.baseUrl || '',
    // 从params中读取参数，如果没有则使用row顶层参数（兼容旧数据）
    temperature: params.temperature ?? row.temperature ?? 0.7,
    topP: params.topP ?? row.topP ?? 0.9,
    topK: params.topK ?? row.topK ?? 40,
    maxTokens: params.maxTokens ?? row.maxTokens ?? 8192,
    contextWindow: params.contextWindow ?? row.contextWindow ?? 32768,
    frequencyPenalty: params.frequencyPenalty ?? row.frequencyPenalty ?? 0,
    presencePenalty: params.presencePenalty ?? row.presencePenalty ?? 0,
    repeatPenalty: params.repeatPenalty ?? row.repeatPenalty ?? 1.1,
    timeout: params.timeout ?? row.timeout ?? 120,
    maxRetries: params.maxRetries ?? row.maxRetries ?? 3,
    stream: params.stream ?? row.stream ?? true,
    extraParams: params.extraParams || row.extraParams || '',
    isDefault: row.isDefault || false
  })
  showModelDialog.value = true
}

// 保存模型
async function saveModel() {
  if (!modelForm.modelId.trim()) {
    ElMessage.warning('请输入模型ID')
    return
  }
  
  savingModel.value = true
  try {
    let models = [...aiModels.value]
    
    // 构建模型数据，参数放在 params 对象中
    const modelData = {
      provider: modelForm.provider,
      modelId: modelForm.modelId,
      modelName: modelForm.modelName,
      apiKey: modelForm.apiKey,
      baseUrl: modelForm.baseUrl,
      isDefault: modelForm.isDefault,
      configured: true,
      params: {
        temperature: modelForm.temperature,
        topP: modelForm.topP,
        topK: modelForm.topK,
        maxTokens: modelForm.maxTokens,
        contextWindow: modelForm.contextWindow,
        frequencyPenalty: modelForm.frequencyPenalty,
        presencePenalty: modelForm.presencePenalty,
        repeatPenalty: modelForm.repeatPenalty,
        timeout: modelForm.timeout,
        maxRetries: modelForm.maxRetries,
        stream: modelForm.stream,
        extraParams: modelForm.extraParams
      }
    }
    
    if (editingModel.value) {
      // 更新现有模型
      const idx = models.findIndex(m => m.modelId === editingModel.value.modelId)
      if (idx > -1) {
        models[idx] = modelData
      }
    } else {
      // 添加新模型
      if (modelForm.isDefault) {
        // 如果设为默认，取消其他默认
        models.forEach(m => m.isDefault = false)
      }
      models.push(modelData)
    }
    
    const res: any = await systemAPI.saveConfig({ ai_models: JSON.stringify(models) })
    if (res && res.success !== false) {
      ElMessage.success(editingModel.value ? '模型已更新' : '模型已添加')
      aiModels.value = models
      showModelDialog.value = false
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingModel.value = false
  }
}

// 删除模型
async function deleteModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除模型 "${row.modelName || row.modelId}" 吗？`, '确认删除', { type: 'warning' })
    aiModels.value = aiModels.value.filter(m => m.modelId !== row.modelId)
    await systemAPI.saveConfig({ ai_models: JSON.stringify(aiModels.value) })
    ElMessage.success('模型已删除')
  } catch (e) {}
}

// 保存模块配置
async function saveModuleSettings() {
  try {
    const res: any = await systemAPI.saveConfig({ module_ai_settings: JSON.stringify(moduleSettings) })
    if (res && res.success !== false) {
      ElMessage.success('模块配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 加载本地模型
async function loadLocalModels() {
  loadingLocalModels.value = true
  try {
    const res: any = await systemAPI.getConfig()
    if (res && res.success !== false) {
      const data = res.data || {}
      if (data.local_ollama_connections) {
        localModels.value = typeof data.local_ollama_connections === 'string' ? JSON.parse(data.local_ollama_connections) : data.local_ollama_connections
      }
    }
  } catch (e) {
    console.warn('Failed to load local models')
  } finally {
    loadingLocalModels.value = false
  }
}

// 添加Ollama连接对话框
function openAddLocalModelDialog() {
  Object.assign(localModelForm, { name: '', url: 'http://localhost:11434' })
  showLocalModelDialog.value = true
}

// 添加Ollama连接
async function addOllamaConnection() {
  if (!localModelForm.url.trim()) {
    ElMessage.warning('请输入 Ollama 地址')
    return
  }
  
  addingLocalModel.value = true
  try {
    // 测试连接
    const res = await fetch(`${localModelForm.url}/api/tags`)
    let models: string[] = []
    let status = 'disconnected'
    
    if (res.ok) {
      const data = await res.json()
      models = (data.models || []).map((m: any) => m.name)
      status = 'connected'
      ElMessage.success('Ollama 连接成功')
    } else {
      ElMessage.warning('Ollama 连接失败，但仍保存配置')
    }
    
    const newConn = {
      id: Date.now(),
      name: localModelForm.name || 'Ollama',
      url: localModelForm.url,
      status,
      models
    }
    
    localModels.value.push(newConn)
    await systemAPI.saveConfig({ local_ollama_connections: JSON.stringify(localModels.value) })
    showLocalModelDialog.value = false
  } catch (e: any) {
    ElMessage.error('无法连接到 Ollama: ' + e.message)
  } finally {
    addingLocalModel.value = false
  }
}

// 测试Ollama连接
async function testOllamaConnection(row: any) {
  try {
    const res = await fetch(`${row.url}/api/tags`)
    if (res.ok) {
      const data = await res.json()
      row.status = 'connected'
      row.models = (data.models || []).map((m: any) => m.name)
      ElMessage.success('连接成功')
    } else {
      row.status = 'disconnected'
      ElMessage.error('连接失败')
    }
  } catch (e) {
    row.status = 'disconnected'
    ElMessage.error('无法连接到 Ollama')
  }
}

// 删除本地模型连接
async function deleteLocalModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除连接 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    localModels.value = localModels.value.filter(m => m.id !== row.id)
    await systemAPI.saveConfig({ local_ollama_connections: JSON.stringify(localModels.value) })
    ElMessage.success('已删除')
  } catch (e) {}
}

// 加载Embedding模型
async function loadEmbeddingModels() {
  try {
    const res: any = await systemAPI.getEmbeddingModels()
    if (res && res.success !== false) {
      embeddingModels.value = res.data?.models || []
      embeddingConfig.stAvailable = res.data?.st_available || false
      if (res.data?.current_model) {
        embeddingConfig.model = res.data.current_model
      }
    }
  } catch (e) {
    console.warn('Failed to load embedding models')
  }
}

// 保存Embedding配置
async function saveEmbeddingConfig() {
  try {
    const res: any = await systemAPI.saveConfig({ embedding_model: embeddingConfig.model })
    if (res && res.success !== false) {
      ElMessage.success('Embedding配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 切换工具启用状态
async function toggleTool(row: any) {
  try {
    await systemAPI.saveConfig({ [`tool_${row.type}_enabled`]: row.enabled })
    ElMessage.success(row.enabled ? '工具已启用' : '工具已禁用')
  } catch (e) {}
}

// 测试工具
async function testTool(row: any) {
  if (row.type === 'OCR') {
    ElMessage.info('请在上传组件中测试OCR功能')
  } else if (row.type === 'Embedding') {
    try {
      const res: any = await localAIAPI.embed('测试文本')
      if (res && res.success !== false) {
        ElMessage.success(`Embedding 生成成功，向量维度: ${res.data?.embedding?.length || 0}`)
      }
    } catch (e) {
      ElMessage.error('Embedding 服务不可用')
    }
  } else if (row.type === 'TextParser') {
    try {
      const res: any = await localAIAPI.textKeywords('这是一个测试文本')
      if (res && res.success !== false) {
        ElMessage.success('文本解析成功')
      }
    } catch (e) {
      ElMessage.error('文本解析服务不可用')
    }
  }
}

// 添加工具
async function addLocalTool() {
  if (!newTool.name.trim()) {
    ElMessage.warning('请输入工具名称')
    return
  }
  
  const typeNames: Record<string, string> = { ocr: 'OCR', text_parser: '文本解析', embedding: 'Embedding', custom_api: '自定义API' }
  const tool = { name: newTool.name, type: typeNames[newTool.type] || newTool.type, description: '自定义工具', enabled: true }
  localTools.value.push(tool)
  ElMessage.success('工具已添加')
  Object.assign(newTool, { type: 'ocr', name: '', apiUrl: '' })
}

// 加载系统配置
async function loadSettings() {
  try {
    const res: any = await systemAPI.getConfig()
    if (res && res.success !== false) {
      const data = res.data || {}
      if (data.app_name) basicConfig.appName = data.app_name
      if (data.theme) basicConfig.theme = data.theme
      if (data.rerank_enabled) rerankConfig.enabled = data.rerank_enabled
      if (data.rerank_model) rerankConfig.model = data.rerank_model
      if (data.rerank_api_key) rerankConfig.apiKey = data.rerank_api_key
    }
  } catch (e) {
    console.warn('Failed to load settings')
  }
}

// 保存基本配置
async function saveBasicConfig() {
  try {
    const res: any = await systemAPI.saveConfig({ app_name: basicConfig.appName, theme: basicConfig.theme })
    if (res && res.success !== false) {
      ElMessage.success('基本配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 保存Rerank配置
async function saveRerankConfig() {
  try {
    const res: any = await systemAPI.saveConfig({
      rerank_enabled: rerankConfig.enabled,
      rerank_model: rerankConfig.model,
      rerank_api_key: rerankConfig.apiKey
    })
    if (res && res.success !== false) {
      ElMessage.success('Rerank配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 加载健康状态
async function loadHealth() {
  loadingHealth.value = true
  try {
    const res: any = await systemAPI.healthCheck()
    if (res && res.success !== false) {
      healthData.value = res.data || {}
    }
  } catch (e) {
    console.warn('Failed to load health')
  } finally {
    loadingHealth.value = false
  }
}

function handleProviderChange() {
  modelForm.modelId = ''
}

onMounted(() => {
  loadAiModels()
  loadLocalModels()
  loadEmbeddingModels()
  loadSettings()
  loadHealth()
})
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.settings-tabs {
  background: #fff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-test-section {
  margin-top: 20px;
}

.ai-test-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #606266;
}

.test-response {
  margin-top: 16px;
}

.test-response pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-size: 13px;
  max-height: 200px;
  overflow-y: auto;
}

.health-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.health-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.health-icon.cpu { background: #ecf5ff; color: #409EFF; }
.health-icon.mem { background: #f0f9eb; color: #67C23A; }
.health-icon.disk { background: #fdf6ec; color: #E6A23C; }
.health-icon.status { background: #f0f9eb; color: #67C23A; }
.health-icon.status.healthy { background: #f0f9eb; color: #67C23A; }
.health-icon.status.unhealthy { background: #fef0f0; color: #F56C6C; }

.health-info {
  display: flex;
  flex-direction: column;
}

.health-label {
  font-size: 13px;
  color: #909399;
}

.health-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

/* 本地工具样式 */
.tool-card {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.tool-info h3 {
  margin: 0 0 4px;
  font-size: 15px;
}

.tool-desc {
  color: #909399;
  font-size: 13px;
  margin: 0 0 12px;
}

.tool-actions {
  display: flex;
  gap: 8px;
}

.tool-result {
  margin-top: 12px;
}

.tool-result pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-size: 12px;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  max-height: 100px;
  overflow-y: auto;
}

.tool-result .result-label {
  font-size: 12px;
  color: #909399;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #ebeef5;
}

.service-item:last-child {
  border-bottom: none;
}
</style>
