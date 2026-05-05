// @ts-nocheck
/**
 * AI对话状态管理 - 配置状态增强版
 * 改进错误处理、超时控制和配置状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { aiAPI, agentAPI, templateAPI, workflowAPI, systemAPI } from '../api'
import { ElMessage } from 'element-plus'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  template_data?: any
  workflow_data?: any
  suggestions?: string[]
}

interface Model {
  id: string
  provider: string
  modelId: string
  modelName: string
  apiKey: string
  baseUrl: string
  isDefault: boolean
  configured: boolean
  params?: any
}

// AI配置状态
interface AIConfigStatus {
  ready: boolean
  chat: {
    available: boolean
    models: Model[]
    current_provider: string
    default_model: Model | null
  }
  embedding: {
    available: boolean
    models: any[]
    current_model: string | null
    current_provider: string | null
    st_available: boolean
    api_key_configured: boolean
  }
  rerank: {
    available: boolean
    models: any[]
  }
  ocr: {
    available: boolean
  }
  warnings: string[]
}

export const useAIStore = defineStore('ai', () => {
  const messages = ref<Message[]>([])
  const conversationId = ref<string | null>(null)
  const loading = ref(false)
  const aiType = ref<'general' | 'template' | 'workflow' | 'analytics'>('general')
  const showChat = ref(false)

  const models = ref<Model[]>([])
  const currentModel = ref<Model | null>(null)
  const moduleAISettings = ref<Record<string, string>>({
    chatGeneral: '',
    chatTemplate: '',
    chatWorkflow: '',
    chatAnalytics: '',
    ragModel: '',
    processingModel: ''
  })

  // AI配置状态（新增）
  const configStatus = ref<AIConfigStatus | null>(null)

  // 加载模型配置
  async function loadModels() {
    try {
      const res: any = await systemAPI.getConfig()
      const config = res.data || {}

      if (config.ai_models) {
        try {
          const modelList = typeof config.ai_models === 'string' ? JSON.parse(config.ai_models) : config.ai_models
          models.value = Array.isArray(modelList) ? modelList : []
        } catch {}
      }

      if (config.module_ai_settings) {
        try {
          const settings = typeof config.module_ai_settings === 'string' ? JSON.parse(config.module_ai_settings) : config.module_ai_settings
          if (settings) {
            moduleAISettings.value = { ...moduleAISettings.value, ...settings }
          }
        } catch {}
      }

      if (models.value.length > 0) {
        currentModel.value = models.value.find(m => m.isDefault) || models.value[0]
      }
    } catch (e) {
      console.error('加载模型配置失败', e)
    }
  }

  // 加载AI配置状态（新增）
  async function loadConfigStatus() {
    try {
      const res: any = await systemAPI.getAIConfigStatus()
      if (res.data) {
        configStatus.value = res.data
      }
    } catch (e) {
      console.error('加载AI配置状态失败', e)
      configStatus.value = null
    }
  }

  // 检查AI是否已配置（新增便捷方法）
  function isAIConfigured(): boolean {
    // 如果有 configStatus，优先使用
    if (configStatus.value) {
      return configStatus.value.ready
    }
    // 没有 configStatus，尝试通过模型列表检查
    if (models.value.length > 0) {
      return models.value.some(m => m.configured)
    }
    return false
  }

  // 获取当前使用的模型描述（新增）
  function getCurrentModelDesc(): string {
    if (!configStatus.value) return '未加载'
    const chat = configStatus.value.chat
    if (!chat.available) return '未配置'
    const model = chat.default_model
    if (!model) return '未选择'
    return `${model.name || model.id} (${model.provider})`
  }

  // 获取Embedding模型描述（新增）
  function getEmbeddingDesc(): string {
    if (!configStatus.value) return '未加载'
    const embed = configStatus.value.embedding
    if (!embed.st_available && !embed.api_key_configured) {
      return 'sentence-transformers未安装，API Key未配置'
    }
    if (!embed.available) return 'Embedding未配置'
    return `${embed.current_model || '未知'} (${embed.current_provider || '未知'})`
  }

  function setModel(modelId: string) {
    const model = models.value.find(m => m.modelId === modelId)
    if (model) {
      currentModel.value = model
      ElMessage.success(`已切换到模型: ${model.modelName || model.modelId}`)
    }
  }

  function getModuleModel(module: keyof typeof moduleAISettings.value) {
    const modelId = moduleAISettings.value[module]
    if (modelId) {
      return models.value.find(m => m.modelId === modelId) || currentModel.value
    }
    return currentModel.value
  }

  // 获取用户配置的超时时间（秒），默认300秒
  function getUserTimeout(): number {
    const model = currentModel.value
    if (model?.params?.timeout && model.params.timeout > 0) {
      return model.params.timeout * 1000 // 秒 -> 毫秒
    }
    // 从第一个已配置模型获取
    const configured = models.value.find(m => m.configured && m.params?.timeout)
    if (configured?.params?.timeout && configured.params.timeout > 0) {
      return configured.params.timeout * 1000
    }
    return 300000 // 默认300秒
  }

  // 发送消息 - 使用用户配置的超时时间
  async function sendMessage(content: string, modelId?: string) {
    if (!content.trim() || loading.value) return
    
    // 确保配置状态已加载
    if (!configStatus.value) {
      try {
        await loadConfigStatus()
        await loadModels()
      } catch (e) {
        console.error('加载配置失败', e)
      }
    }
    
    // 检查AI是否已配置
    if (!isAIConfigured()) {
      messages.value.push({
        role: 'assistant',
        content: '⚠️ AI 尚未配置或配置无效，请先在「系统设置 → AI配置」中完成配置后再试。',
        timestamp: new Date().toISOString()
      })
      return
    }

    messages.value.push({
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    })

    loading.value = true
    const userTimeout = getUserTimeout()
    let errorDetail = ''
    const modelToUse = modelId || currentModel.value?.modelId

    try {
      let res: any
      let usedFallback = false

      try {
        res = await agentAPI.chat({
          message: content.trim(),
          conversation_id: conversationId.value || undefined,
          use_rag: true,
          enable_tools: true,
          model: modelToUse
        }, { timeout: userTimeout })
      } catch (agentError: any) {
        console.log('Agent API failed, falling back to AI API:', agentError)
        usedFallback = true
        errorDetail = agentError.message || ''

        try {
          res = await aiAPI.chat({
            message: content.trim(),
            conversation_id: conversationId.value || undefined,
            ai_type: aiType.value
          }, { timeout: userTimeout })
        } catch (fallbackError: any) {
          throw agentError
        }
      }

      if (!conversationId.value && res.conversation_id) {
        conversationId.value = res.conversation_id
      }

      let responseContent = res.response || res.message || res.content

      if (!responseContent || responseContent.trim() === '') {
        if (res.error) {
          responseContent = `AI 服务错误：${res.error}`
        } else if (usedFallback && errorDetail) {
          responseContent = `智能体服务暂时不可用，已切换到基础 AI 模式。${errorDetail ? '(' + errorDetail + ')' : ''}`
        } else {
          responseContent = 'AI 暂时没有回复，请稍后重试或检查 AI 配置。'
        }
      }

      const assistantMsg: Message = {
        role: 'assistant',
        content: responseContent,
        timestamp: new Date().toISOString()
      }

      if (res.template_data) {
        assistantMsg.template_data = res.template_data
      }
      if (res.workflow_data) {
        assistantMsg.workflow_data = res.workflow_data
      }
      if (res.suggestions && res.suggestions.length > 0) {
        assistantMsg.suggestions = res.suggestions
      }

      messages.value.push(assistantMsg)
    } catch (e: any) {
      console.error('AI chat error:', e)

      const timeoutSec = Math.round(userTimeout / 1000)
      let errorMsg = '抱歉，AI 服务暂时不可用'

      if (e.code === 'ECONNABORTED' || e.name === 'AbortError' || e.message?.includes('timeout')) {
        errorMsg = `AI 响应超时（${timeoutSec}秒），请尝试简化问题或增加超时时间`
      } else if (e.response?.status === 504) {
        errorMsg = `后端网关超时（${timeoutSec}秒），请增加超时时间或检查后端配置`
      } else if (e.response?.data?.detail) {
        errorMsg = `服务错误：${e.response.data.detail}`
      } else if (e.response?.data?.error) {
        errorMsg = `AI 错误：${e.response.data.error}`
      } else if (e.message) {
        if (e.message.includes('401') || e.message.includes('Invalid') || e.message.includes('unauthorized')) {
          errorMsg = 'AI 未配置或 API Key 无效，请点击右上角 ⚙ 设置 AI 模型'
        } else if (e.message.includes('Network') || e.message.includes('network')) {
          errorMsg = '网络连接失败，请检查网络或后端服务是否运行'
        } else if (e.message.includes('rate') || e.message.includes('limit')) {
          errorMsg = 'AI 调用频率超限，请稍后重试'
        } else {
          errorMsg = `服务错误：${e.message}`
        }
      }

      messages.value.push({
        role: 'assistant',
        content: errorMsg,
        timestamp: new Date().toISOString()
      })
    } finally {
      loading.value = false
    }
  }

  async function createTemplateFromChat(templateData: any): Promise<boolean> {
    try {
      const res: any = await templateAPI.create(templateData)
      ElMessage.success(`模板「${templateData.name}」创建成功！`)
      return true
    } catch (e: any) {
      const detail = e.response?.data?.detail || e.message || '未知错误'
      ElMessage.error(`创建模板失败：${detail}`)
      return false
    }
  }

  async function createWorkflowFromChat(workflowData: any): Promise<boolean> {
    try {
      const res: any = await workflowAPI.create(workflowData)
      ElMessage.success(`工作流「${workflowData.name}」创建成功！`)
      return true
    } catch (e: any) {
      const detail = e.response?.data?.detail || e.message || '未知错误'
      ElMessage.error(`创建工作流失败：${detail}`)
      return false
    }
  }

  function clearMessages() {
    messages.value = []
    conversationId.value = null
  }

  function toggleChat() {
    showChat.value = !showChat.value
  }

  function setAIType(type: 'general' | 'template' | 'workflow' | 'analytics') {
    aiType.value = type
  }

  return {
    messages,
    conversationId,
    loading,
    aiType,
    showChat,
    models,
    currentModel,
    moduleAISettings,
    configStatus,
    loadModels,
    loadConfigStatus,
    isAIConfigured,
    getCurrentModelDesc,
    getEmbeddingDesc,
    setModel,
    getModuleModel,
    getUserTimeout,
    sendMessage,
    createTemplateFromChat,
    createWorkflowFromChat,
    clearMessages,
    toggleChat,
    setAIType
  }
})
