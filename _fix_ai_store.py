# -*- coding: utf-8 -*-
"""Fix AI store: 1) use user-configured timeout, 2) clear input properly"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\store\ai.ts'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# === Fix 1: Add getUserTimeout helper and use it ===
# Replace the sendMessage function entirely

old_send = """  // 发送消息 - 改进版，更好的错误处理和超时控制
  async function sendMessage(content: string) {
    if (!content.trim() || loading.value) return

    messages.value.push({
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    })

    loading.value = true
    let errorDetail = ''

    try {
      let res: any
      let usedFallback = false
      
      // 首先尝试 agent API（带超时控制）
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 30000) // 30秒超时
        
        res = await agentAPI.chat({
          message: content.trim(),
          conversation_id: conversationId.value || undefined,
          use_rag: true,
          enable_tools: true
        })
        
        clearTimeout(timeoutId)
      } catch (agentError: any) {
        console.log('Agent API failed, falling back to AI API:', agentError)
        usedFallback = true
        errorDetail = agentError.message || ''
        
        // 回退到基础 AI 对话
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 30000)
        
        res = await aiAPI.chat({
          message: content.trim(),
          conversation_id: conversationId.value || undefined,
          ai_type: aiType.value
        })
        
        clearTimeout(timeoutId)
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
      
      let errorMsg = '抱歉，AI 服务暂时不可用'
      
      if (e.name === 'AbortError') {
        errorMsg = 'AI 响应超时（30秒），请稍后重试或简化您的问题'
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
        } else if (e.message.includes('timeout') || e.message.includes('Timeout')) {
          errorMsg = 'AI 响应超时，请稍后重试'
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
  }"""

new_send = """  // 获取用户配置的超时时间（秒），默认300秒
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
  async function sendMessage(content: string) {
    if (!content.trim() || loading.value) return

    messages.value.push({
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    })

    loading.value = true
    const userTimeout = getUserTimeout()
    let errorDetail = ''

    try {
      let res: any
      let usedFallback = false
      
      // 首先尝试 agent API（使用用户配置的超时）
      try {
        res = await agentAPI.chat({
          message: content.trim(),
          conversation_id: conversationId.value || undefined,
          use_rag: true,
          enable_tools: true
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
  }"""

if old_send in content:
    content = content.replace(old_send, new_send)
    print("[OK] Replaced sendMessage with timeout-aware version")
else:
    print("[ERROR] Could not find sendMessage function to replace")
    # Debug
    idx = content.find('async function sendMessage')
    if idx > 0:
        print(f"Found at index {idx}")
        print(content[idx:idx+100])

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("ai.ts updated!")
