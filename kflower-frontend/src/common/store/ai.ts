/**
 * AI对话状态管理 - 修复版
 * 改进错误处理和超时控制
 */
import { defineStore } from 'pinia'
import { ref, onMounted } from 'vue'
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

    messages.value.push({
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    })

    loading.value = true
    const userTimeout = getUserTimeout()
    let errorDetail = ''
    // 使用传入的模型或当前选中的模型
    const modelToUse = modelId || currentModel.value?.modelId

    try {
      let res: any
      let usedFallback = false
      
      // 首先尝试 agent API（使用用户配置的超时）
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
        
        // 回退到基础 AI 对话
        try {
          res = await aiAPI.chat({
            message: content.trim(),
            conversation_id: conversationId.value || undefined,
            ai_type: aiType.value
          }, { timeout: userTimeout })
        } catch (fallbackError: any) {
          // 两个都失败，抛出原始错误
          throw agentError
        }
      }

      // 设置对话ID
      if (!conversationId.value && res.conversation_id) {
        conversationId.value = res.conversation_id
      }

      // 提取响应内容 - 处理多种可能的字段名
      let responseContent = res.response || res.message || res.content
      
      // 如果响应为空，显示错误信息
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

  // 从AI对话创建模板
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

  // 从AI对话创建工作流
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
    loadModels,
    setModel,
    getModuleModel,
    sendMessage,
    createTemplateFromChat,
    createWorkflowFromChat,
    clearMessages,
    toggleChat,
    setAIType
  }
})