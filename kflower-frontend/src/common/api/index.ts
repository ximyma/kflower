/**
 * API 请求封装
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 添加Token
    const token = localStorage.getItem('kflower_token')
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error: AxiosError) => {
    const status = error.response?.status
    
    if (status === 401) {
      // Token过期或无效
      localStorage.removeItem('kflower_token')
      ElMessage.error('登录已过期，请重新登录')
      // 避免在登录页重复跳转
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    } else if (status === 403) {
      ElMessage.error('没有权限访问')
    } else if (status === 404) {
      ElMessage.error('请求的资源不存在')
    } else if (status === 500) {
      ElMessage.error('服务器错误，请稍后重试')
      // 500错误不清除token，不跳转登录页
    }
    
    return Promise.reject(error)
  }
)

// API方法
export const authAPI = {
  login: (data: { username: string; password: string }) => api.post('/auth/login', data),
  register: (data: { username: string; email: string; password: string; full_name: string }) => 
    api.post('/auth/register', data),
  getUserInfo: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh')
}

export const aiAPI = {
  chat: (data: { 
    message: string; 
    conversation_id?: string; 
    ai_type?: string;
    related_type?: string;
    related_id?: number;
  }, config?: AxiosRequestConfig) => api.post('/ai/chat', data, config),
  getHistory: (conversation_id: string) => api.get(`/ai/history?conversation_id=${conversation_id}`),
  deleteHistory: (conversation_id: string) => api.delete(`/ai/history/${conversation_id}`),
  listProviders: () => api.get('/ai/providers'),
  getDigitalBaseStatus: () => api.get('/ai/digital-base/status'),
  getDigitalBaseProviders: () => api.get('/ai/digital-base/providers/detailed'),
  getDigitalBaseModels: (provider?: string) => api.get('/ai/digital-base/models/available', { params: { provider } }),
  getDigitalBaseUsageStats: (days?: number) => api.get('/ai/digital-base/usage/stats', { params: { days } }),
  // AI智能体引擎API
  getAgentEngineStatus: () => api.get('/ai/agent-engine/status'),
  getAgentEngineAgents: () => api.get('/ai/agent-engine/agents'),
  createAgent: (data: any) => api.post('/ai/agent-engine/agents', data),
  updateAgent: (id: number, data: any) => api.put(`/ai/agent-engine/agents/${id}`, data),
  deleteAgent: (id: number) => api.delete(`/ai/agent-engine/agents/${id}`),
  getAgentEngineTools: () => api.get('/ai/agent-engine/tools'),
  getAgentEngineTasks: () => api.get('/ai/agent-engine/tasks'),
  // AI能力API
  executeCapability: (capability: string, input_data: any) => api.post('/ai/capability/execute', { capability, input_data }),
  listCapabilities: () => api.get('/ai/capability/list'),
  // AI网关API
  getGatewayStats: () => api.get('/ai/digital-base/gateway-stats'),
  // 记忆管理API
  getMemoryStats: () => api.get('/ai/agent-engine/memory/stats'),
  listMemories: (limit?: number) => api.get('/ai/agent-engine/memory/list', { params: { limit } }),
  // 数据集成API
  getDataIntegrationStats: () => api.get('/ai/digital-base/data-integration/stats'),
  getDataIntegrationConnections: () => api.get('/ai/digital-base/data-integration/connections'),
  getDataIntegrationSyncTasks: () => api.get('/ai/digital-base/data-integration/sync-tasks'),
  // 数据库迁移API
  getMigrationStats: () => api.get('/ai/digital-base/migration/stats')
}

export const agentAPI = {
  chat: (data: {
    message: string;
    conversation_id?: string;
    use_rag?: boolean;
    enable_tools?: boolean;
    model?: string;
    provider?: string;
  }, config?: AxiosRequestConfig) => api.post('/agent/chat', data, config),
  generateTemplate: (data: { description: string; category?: string }) =>
    api.post('/agent/generate-template', data),
  query: (data: { query: string }) =>
    api.post('/agent/query', data),
  listTools: () => api.get('/agent/tools'),
  listAgents: () => api.get('/agent/agents'),
  getHistory: (count?: number) => api.get('/agent/history', { params: { count } }),
  analyzeIntent: (message: string) =>
    api.post('/agent/analyze-intent', { query: message }),
}

export const templateAPI = {
  list: (params?: { category?: string; search?: string; skip?: number; limit?: number }) => 
    api.get('/templates/', { params }),
  get: (id: number) => api.get(`/templates/${id}`),
  create: (data: any) => api.post('/templates/', data),
  update: (id: number, data: any) => api.put(`/templates/${id}`, data),
  delete: (id: number) => api.delete(`/templates/${id}`),
  // 数据提交与管理
  submitData: (id: number, data: any) => api.post(`/templates/${id}/submit`, { data }),
  getData: (id: number, params?: any) => api.get(`/templates/${id}/data`, { params }),
  getDataCount: (id: number) => api.get(`/templates/${id}/data/count`),
  getDataDetail: (id: number, dataId: number) => api.get(`/templates/${id}/data/${dataId}`),
  deleteData: (id: number, dataId: number) => api.delete(`/templates/${id}/data/${dataId}`),
  updateData: (id: number, dataId: number, data: any) => api.put(`/templates/${id}/data/${dataId}`, { data }),
  getStats: (id: number) => api.get(`/templates/${id}/stats`),
  // 导入导出
  exportData: (id: number) => api.get(`/templates/${id}/data/export`),
  importData: (id: number, data: any[]) => api.post(`/templates/${id}/data/import`, { data }),
  // 发布模板
  publish: (id: number) => api.post(`/templates/${id}/publish`),
  // 保存模板（兼容旧调用）
  saveTemplate: (id: number | null, data: any) => {
    if (id) {
      return api.put(`/templates/${id}`, data)
    } else {
      return api.post('/templates/', data)
    }
  },
}

export const workflowAPI = {
  list: (params?: { search?: string; skip?: number; limit?: number }) =>
    api.get('/workflows/', { params }),
  get: (id: number) => api.get(`/workflows/${id}`),
  create: (data: any) => api.post('/workflows/', data),
  update: (id: number, data: any) => api.put(`/workflows/${id}`, data),
  delete: (id: number) => api.delete(`/workflows/${id}`),
  execute: (id: number, title: string, data: any) =>
    api.post(`/workflows/${id}/execute`, { title, data }),
  executeStart: (id: number, data: any) =>
    api.post(`/workflows/${id}/start`, data),
}

export const notificationAPI = {
  send: (data: { user_id: number; message: string; channel?: string }) =>
    api.post('/notifications/send', data),
  listUsers: (params?: any) => api.get('/users/', { params }),
}

export const knowledgeAPI = {
  listBases: () => api.get('/knowledge/bases'),
  getBase: (id: number) => api.get(`/knowledge/bases/${id}`),
  createBase: (data: { name: string; code?: string; description?: string; embedding_model?: string; rerank_model?: string; rerank_enabled?: boolean }) => 
    api.post('/knowledge/bases', data),
  updateBase: (id: number, data: { name?: string; description?: string; embedding_model?: string; rerank_model?: string; rerank_enabled?: boolean }) => 
    api.put(`/knowledge/bases/${id}`, data),
  deleteBase: (id: number) => api.delete(`/knowledge/bases/${id}`),
  upload: (kb_id: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/knowledge/upload/${kb_id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  uploadBatch: (kb_id: number, files: File[]) => {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    return api.post(`/knowledge/upload-batch/${kb_id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  listDocuments: (kb_id?: number) => api.get('/knowledge/documents', { params: { kb_id } }),
  getDocument: (doc_id: number) => api.get(`/knowledge/documents/${doc_id}`),
  deleteDocument: (doc_id: number) => api.delete(`/knowledge/documents/${doc_id}`),
  parseDocument: (doc_id: number) => api.post(`/knowledge/parse/${doc_id}`),
  parseAll: (kb_id: number) => api.post(`/knowledge/parse-all/${kb_id}`),
  vectorize: (doc_id: number) => api.post(`/knowledge/vectorize/${doc_id}`),
  vectorizeAll: (kb_id: number) => api.post(`/knowledge/vectorize-all/${kb_id}`),
  query: (params: { query: string; kb_id?: number; top_k?: number }) => 
    api.post('/knowledge/query', null, { params }),
  // 高级检索
  search: (params: { q: string; type?: string; kb_id?: number; tag?: string; top_k?: number }) =>
    api.get('/knowledge/search', { params }),
  // 标签管理
  listTags: (kb_id?: number) => api.get('/knowledge/tags', { params: { kb_id } }),
  createTag: (data: { name: string; color?: string; description?: string; kb_id?: number }) =>
    api.post('/knowledge/tags', data),
  deleteTag: (tag_id: number) => api.delete(`/knowledge/tags/${tag_id}`),
  addDocTag: (doc_id: number, tag_id: number) =>
    api.post(`/knowledge/documents/${doc_id}/tags`, { tag_id }),
  removeDocTag: (doc_id: number, tag_id: number) =>
    api.delete(`/knowledge/documents/${doc_id}/tags/${tag_id}`),
  // 笔记
  listNotes: (kb_id?: number) => api.get('/knowledge/notes', { params: { kb_id } }),
  getNote: (note_id: number) => api.get(`/knowledge/notes/${note_id}`),
  createNote: (data: { title: string; content?: string; tags?: string[]; is_daily?: boolean; knowledge_base_id?: number }) =>
    api.post('/knowledge/notes', data),
  updateNote: (note_id: number, data: { title?: string; content?: string; tags?: string[]; is_daily?: boolean }) =>
    api.put(`/knowledge/notes/${note_id}`, data),
  deleteNote: (note_id: number) => api.delete(`/knowledge/notes/${note_id}`),
  // 知识图谱
  getGraph: (kb_id?: number) => api.get('/knowledge/graph', { params: { kb_id } }),
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getRecentActivities: (limit?: number) => api.get('/dashboard/recent-activities', { params: { limit } }),
  getPendingTasks: () => api.get('/dashboard/pending-tasks'),
  getQuickStats: () => api.get('/dashboard/quick-stats'),
}

export const systemAPI = {
  getConfig: () => api.get('/system/config'),
  updateConfig: (key: string, value: string, description?: string) => 
    api.put(`/system/config/${key}`, { value, description }),
  saveConfig: (configs: Record<string, any>) => api.post('/system/config', configs),
  healthCheck: () => api.get('/system/health'),
  testAI: () => api.post('/system/test-ai'),
  listAIProviders: () => api.get('/system/ai-providers'),
  listAIModels: (provider: string) => api.get(`/system/ai-models/${provider}`),
  fetchAIModels: (provider: string, apiKey: string, baseUrl?: string) => 
    api.post(`/system/ai-models/${provider}`, { api_key: apiKey, base_url: baseUrl }),
  listEmbeddingModels: () => api.get('/system/embedding-models'),
  // Ollama 连接管理
  listOllamaConnections: () => api.get('/system/ollama-connections'),
  testOllamaConnection: (url: string, timeout?: number) => 
    api.post('/system/ollama-connections/test', { url, timeout: timeout || 5 }),
  // Rerank 模型管理
  listRerankModels: () => api.get('/system/rerank-models'),
  testRerankModel: (modelId: string) => api.post('/system/rerank-models/test', { model_id: modelId }),
  // 别名方法
  getAIProviders: () => api.get('/system/ai-providers'),
  getAIModels: (provider: string) => api.get(`/system/ai-models/${provider}`),
  getEmbeddingModels: () => api.get('/system/embedding-models'),
  // AI配置状态总览
  getAIConfigStatus: () => api.get('/system/ai-config-status'),
}

// 本地AI服务
export const localAIAPI = {
  ocrText: (file: File, lang?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (lang) form.append('lang', lang)
    return api.post('/local-ai/ocr/text', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  ocrTable: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/local-ai/ocr/table', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  ocrStatus: () => api.get('/local-ai/ocr/status'),
  ocrConfigure: (tesseractPath: string, lang?: string) =>
    api.put('/local-ai/ocr/config', null, { params: { tesseract_path: tesseractPath, lang: lang || 'chi_sim+eng' } }),
  textSegment: (text: string, mode?: string) =>
    api.post('/local-ai/text/segment', { text, mode: mode || 'default' }),
  textKeywords: (text: string, topK?: number) =>
    api.post('/local-ai/text/keywords', { text, top_k: topK || 10 }),
  textSummary: (text: string, maxLength?: number) =>
    api.post('/local-ai/text/summary', { text, max_length: maxLength || 200 }),
  textParse: (text: string) => api.post('/local-ai/text/parse', { text }),
  embed: (text: string) => api.post('/local-ai/embed', { text }),
  embedBatch: (texts: string[]) => api.post('/local-ai/embed/batch', { texts: JSON.stringify(texts) }),
  embedStatus: () => api.get('/local-ai/embed/status'),
  embedConfig: (params: { apiKey?: string; apiBase?: string; model?: string; provider?: string; stDevice?: string }) =>
    api.put('/local-ai/embed/config', null, { params }),
  // ============ 新增：Embedding 模型管理 API ============
  listEmbedModels: () => api.get('/local-ai/embed/models'),
  addEmbedModel: (modelConfig: {
    name?: string;
    model?: string;
    provider?: string;
    dimension?: number;
    description?: string;
    api_key?: string;
    api_base?: string;
    model_path?: string;
    device?: string;
    batch_size?: number;
    enabled?: boolean;
  }) => api.post('/local-ai/embed/models', modelConfig),
  updateEmbedModel: (modelId: string, modelConfig: {
    name?: string;
    provider?: string;
    dimension?: number;
    description?: string;
    api_key?: string;
    api_base?: string;
    model_path?: string;
    device?: string;
    batch_size?: number;
    enabled?: boolean;
  }) => api.put(`/local-ai/embed/models/${encodeURIComponent(modelId)}`, modelConfig),
  deleteEmbedModel: (modelId: string) => api.delete(`/local-ai/embed/models/${encodeURIComponent(modelId)}`),
  setDefaultEmbedModel: (modelId: string) => api.put(`/local-ai/embed/models/${encodeURIComponent(modelId)}/default`, {}),
  testEmbedModel: (modelId: string) => api.post(`/local-ai/embed/models/${encodeURIComponent(modelId)}/test`, {}),
  processAttachment: (file: File, operations?: string[]) => {
    const form = new FormData()
    form.append('file', file)
    form.append('operations', JSON.stringify(operations || ['ocr', 'segment']))
    return api.post('/local-ai/process-attachment', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  servicesStatus: () => api.get('/local-ai/services-status'),
}

export const orgAPI = {
  list: () => api.get('/organizations/'),
  create: (data: { name: string; code?: string; parent_id?: number; description?: string }) => 
    api.post('/organizations/', data),
  get: (id: number) => api.get(`/organizations/${id}`),
  delete: (id: number) => api.delete(`/organizations/${id}`),
}

export const userAPI = {
  list: (params?: { search?: string; skip?: number; limit?: number }) => 
    api.get('/users/', { params }),
  getMe: () => api.get('/users/me'),
  get: (id: number) => api.get(`/users/${id}`),
  create: (data: { username: string; email: string; password: string; full_name: string; phone?: string; organization_id?: number }) => 
    api.post('/users/', data),
  update: (id: number, data: any) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
}

export const analyticsAPI = {
  getOverview: () => api.get('/analytics/overview'),
  getWorkflowPerformance: (params?: { start_date?: string; end_date?: string }) => 
    api.get('/analytics/workflow-performance', { params }),
  getUserActivity: (days?: number) => api.get('/analytics/user-activity', { params: { days } }),
  getTemplateAnalytics: () => api.get('/analytics/template-analytics'),
  getOrgPerformance: () => api.get('/analytics/org-performance'),
  getKnowledgeAnalytics: () => api.get('/analytics/knowledge-analytics'),
  query: (question: string) => api.post('/analytics/query', { question }),
  getDashboardSummary: () => api.get('/analytics/dashboard-summary'),
}

export const docConverterAPI = {
  // 获取转换服务状态
  getStatus: () => api.get('/doc-converter/status'),
  // 获取支持的格式列表
  getSupportedFormats: () => api.get('/doc-converter/supported-formats'),
  // 单文件转换（返回 blob）
  convert: (file: File, targetFormat: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('target_format', targetFormat)
    return api.post('/doc-converter/convert', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    })
  },
  // Excel/CSV 提取为 JSON
  extractJson: (file: File, headerRow?: number, maxRows?: number) => {
    const form = new FormData()
    form.append('file', file)
    if (headerRow !== undefined) form.append('header_row', String(headerRow))
    if (maxRows !== undefined) form.append('max_rows', String(maxRows))
    return api.post('/doc-converter/extract-json', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  // 自动转换旧格式（上传前置处理）
  autoConvert: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/doc-converter/auto-convert', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    })
  },
  // 批量转换（返回 zip blob）
  batchConvert: (files: File[], targetFormat: string) => {
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    form.append('target_format', targetFormat)
    return api.post('/doc-converter/batch-convert', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    })
  },
}

export default api