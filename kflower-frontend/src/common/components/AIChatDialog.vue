<template>
  <div class="ai-chat-dialog">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-title-row">
        <el-icon :size="20"><MagicStick /></el-icon>
        <span class="header-title-text">AI 智能助手</span>
      </div>
      <div class="header-actions">
        <el-select v-model="aiStore.aiType" size="small" class="header-select" @change="aiStore.setAIType">
          <el-option value="general" label="智能助手" />
          <el-option value="template" label="模板设计" />
          <el-option value="workflow" label="流程审批" />
          <el-option value="analytics" label="决策分析" />
        </el-select>
        <el-select 
          v-model="selectedModelId" 
          size="small" 
          class="header-select header-select-wide" 
          @change="handleModelChange" 
          placeholder="选择模型"
          teleported
          popper-class="ai-model-dropdown"
          :popper-options="{
            placement: 'bottom-start',
            modifiers: [
              { name: 'preventOverflow', options: { boundary: 'viewport' } }
            ]
          }"
        >
          <el-option v-for="model in aiStore.models" :key="model.modelId" :label="model.modelName || model.modelId" :value="model.modelId">
            <span>{{ model.modelName || model.modelId }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">{{ model.provider }}</el-tag>
          </el-option>
        </el-select>
        <button class="header-icon-btn" @click="goToSettings" title="AI配置">
          <el-icon :size="16"><Setting /></el-icon>
        </button>
        <button class="header-icon-btn" @click="aiStore.clearMessages" title="清空对话">
          <el-icon :size="16"><Delete /></el-icon>
        </button>
        <button class="header-close-btn" @click="emit('close')" title="关闭">
          <el-icon :size="18"><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div v-if="aiStore.messages.length === 0" class="welcome-message">
        <div class="welcome-icon"><el-icon :size="48"><MagicStick /></el-icon></div>
        <h3>您好，我是 Kflower AI 助手</h3>
        <p>我可以帮助您：</p>
        <ul>
          <li>📋 设计业务模板和表单</li>
          <li>🔄 规划和优化工作流程</li>
          <li>📊 分析数据并生成图表</li>
          <li>💡 提供智能决策建议</li>
          <li>✅ 每次输入对话要写：请输出字段定义格式（type/label/name）的json文件，不要输出任何其他文字：</li>
        </ul>
        <div class="quick-actions">
          <el-tag v-for="action in ['帮我设计一个请假审批流程', '推荐一些常用的业务模板', '分析本月销售数据']"
            :key="action" @click="aiStore.sendMessage(action)" class="quick-action">
            {{ action }}
          </el-tag>
        </div>
      </div>

      <!-- 消息 -->
      <div v-for="(msg, index) in aiStore.messages" :key="index" class="message-item" :class="msg.role">
        <div class="message-avatar">
          <el-icon :size="20"><User v-if="msg.role === 'user'" /><Setting v-else /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-text" v-html="msg.content.replace(/\n/g, '<br>')"></div>
          <!-- AI消息操作按钮区域 -->
          <div v-if="msg.role === 'assistant' && (msg.template_data || msg.workflow_data)" class="message-actions">
            <el-button
              v-if="msg.template_data"
              type="primary"
              size="small"
              :loading="creatingTemplate"
              @click="handleCreateTemplate(msg.template_data)"
            >
              <el-icon><Document /></el-icon> 创建为表单
            </el-button>
            <el-button
              v-if="msg.workflow_data"
              type="success"
              size="small"
              :loading="creatingWorkflow"
              @click="handleCreateWorkflow(msg.workflow_data)"
            >
              <el-icon><Connection /></el-icon> 创建为工作流
            </el-button>
          </div>
          <!-- 创建成功提示 -->
          <div v-if="msg._created_template" class="creation-notice success">
            <el-icon><CircleCheck /></el-icon> 模板已创建，<el-link type="primary" @click="goToTemplate(msg._created_template)">点击查看</el-link>
          </div>
          <div v-if="msg._created_workflow" class="creation-notice success">
            <el-icon><CircleCheck /></el-icon> 工作流已创建，<el-link type="primary" @click="goToWorkflow(msg._created_workflow)">点击查看</el-link>
          </div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="aiStore.loading" class="message-item assistant">
        <div class="message-avatar"><el-icon :size="20"><Setting /></el-icon></div>
        <div class="message-content">
          <div class="message-text loading">
            <span class="dots"><span></span><span></span><span></span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input">
      <!-- 附件列表 -->
      <div v-if="attachments.length > 0" class="attachment-list">
        <div v-for="att in attachments" :key="att.id" class="attachment-item">
          <el-icon><Document /></el-icon>
          <span class="att-name">{{ att.name }}</span>
          <el-tag v-if="att.text" size="small" type="success">已OCR</el-tag>
          <el-button size="small" text type="danger" @click="removeAttachment(att.id)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 上传 + 输入 + 发送 -->
      <div class="input-row">
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          accept=".jpg,.jpeg,.png,.gif,.bmp,.pdf,.txt,.doc,.docx"
          :on-change="handleFileChange"
        >
          <el-button :disabled="aiStore.loading || uploading"><el-icon><Upload /></el-icon></el-button>
        </el-upload>
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入您的问题... (支持上传图片/文档作为附件)"
          @keydown.enter.ctrl="handleSend"
        />
        <el-button type="primary" :disabled="(!inputMessage.trim() && attachments.length === 0) || aiStore.loading" @click="handleSend">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAIStore } from '../store/ai'
import { Document, Connection, Close, Setting, Delete, Upload, MagicStick, User } from '@element-plus/icons-vue'

const emit = defineEmits(['close'])
const aiStore = useAIStore()
const router = useRouter()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const attachments = ref<any[]>([])
const uploading = ref(false)
const creatingTemplate = ref(false)
const creatingWorkflow = ref(false)
const selectedModelId = ref('')

// 初始化模型选择
function initModelSelection() {
  if (aiStore.currentModel) {
    selectedModelId.value = aiStore.currentModel.modelId
  }
}

// 处理模型切换
function handleModelChange(modelId: string) {
  aiStore.setModel(modelId)
}

// 初始化 - 加载模型列表
initModelSelection()
aiStore.loadModels()

function goToSettings() {
  emit('close')
  router.push('/settings?tab=ai')
}

function goToTemplate(id: number) {
  emit('close')
  router.push(`/templates/${id}`)
}

function goToWorkflow(id: number) {
  emit('close')
  router.push(`/workflows/${id}`)
}

function formatTime(ts?: string) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function handleCreateTemplate(templateData: any) {
  creatingTemplate.value = true
  try {
    const success = await aiStore.createTemplateFromChat(templateData)
    if (success) {
      // 标记当前消息的模板已创建，隐藏按钮
      const msg = aiStore.messages.find(
        (m: any) => m.template_data === templateData
      )
      if (msg) {
        ;(msg as any)._created_template = true
        msg.template_data = undefined
      }
    }
  } finally {
    creatingTemplate.value = false
  }
}

async function handleCreateWorkflow(workflowData: any) {
  creatingWorkflow.value = true
  try {
    const success = await aiStore.createWorkflowFromChat(workflowData)
    if (success) {
      // 标记当前消息的工作流已创建，隐藏按钮
      const msg = aiStore.messages.find(
        (m: any) => m.workflow_data === workflowData
      )
      if (msg) {
        ;(msg as any)._created_workflow = true
        msg.workflow_data = undefined
      }
    }
  } finally {
    creatingWorkflow.value = false
  }
}

async function handleFileChange(file: any) {
  const raw = file.raw || file
  uploading.value = true
  try {
    const form = new FormData()
    form.append('file', raw)
    form.append('operations', JSON.stringify(['ocr', 'segment', 'keywords']))
    const res: any = await (window as any).fetch('/api/v1/local-ai/process-attachment', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('access_token') || '') },
      body: form
    })
    const json = await res.json()
    if (json.success) {
      attachments.value.push({
        id: Date.now(),
        name: raw.name,
        type: raw.type,
        size: raw.size,
        text: json.content_text || (json.results?.ocr?.text) || '',
        keywords: json.results?.keywords?.keywords || [],
        ready: true
      })
    } else {
      // 附件解析失败，当作普通文本附件处理
      attachments.value.push({
        id: Date.now(), name: raw.name, type: raw.type, size: raw.size,
        text: '', keywords: [], ready: true
      })
    }
  } catch {
    attachments.value.push({
      id: Date.now(), name: raw.name, type: raw.type, size: raw.size,
      text: '', keywords: [], ready: true
    })
  } finally {
    uploading.value = false
  }
}

function removeAttachment(id: number) {
  attachments.value = attachments.value.filter((a: any) => a.id !== id)
}

async function handleSend() {
  const hasContent = inputMessage.value.trim() || attachments.value.length > 0
  if (!hasContent || aiStore.loading) return

  let message = inputMessage.value.trim()

  // 附加文件内容
  if (attachments.value.length > 0) {
    const parts = attachments.value.map((a: any) => {
      let part = `[附件: ${a.name}]`
      if (a.text) {
        part += `\n内容摘要: ${a.text.substring(0, 500)}${a.text.length > 500 ? '...' : ''}`
      }
      if (a.keywords?.length) {
        const kws = a.keywords.slice(0, 10).map((k: any) => k.word || k).join(', ')
        part += `\n关键词: ${kws}`
      }
      return part
    })
    message = message ? `${message}\n\n${parts.join('\n\n')}` : parts.join('\n\n')
  }

  // 立即清空输入框和附件，不等AI回复
  inputMessage.value = ''
  attachments.value = []

  // 异步发送，不阻塞UI
  aiStore.sendMessage(message)
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}
</script>

<style scoped>
.ai-chat-dialog {
  position: fixed; bottom: 100px; right: 30px;
  width: 400px; height: 550px;
  background: white; border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  display: flex; flex-direction: column;
  /* 移除 overflow: hidden，避免下拉框被裁剪 */
  /* overflow: hidden; */
  z-index: 9999;
}
.chat-header {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white; display: flex; align-items: center; justify-content: space-between;
}
.header-title-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 600; margin-bottom: 8px;
}
.header-title-text { letter-spacing: 2px; }
.header-actions { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.header-actions { display: flex; align-items: center; gap: 4px; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px; }
.welcome-message { text-align: center; padding: 20px; }
.welcome-icon { color: #667eea; margin-bottom: 16px; }
.welcome-message h3 { margin-bottom: 12px; }
.welcome-message ul { text-align: left; list-style: none; padding: 0; margin: 16px 0; }
.welcome-message li { padding: 6px 0; }
.quick-actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.quick-action { cursor: pointer; }
.message-item { display: flex; margin-bottom: 16px; }
.message-item.user { flex-direction: row-reverse; }
.message-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.user .message-avatar { background: #409EFF; color: white; }
.assistant .message-avatar { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
.message-content { max-width: 75%; margin: 0 8px; }
.message-text { padding: 10px 14px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; }
.user .message-text { background: #409EFF; color: white; border-bottom-right-radius: 4px; }
.assistant .message-text { background: #f5f7fa; color: #333; border-bottom-left-radius: 4px; }
.message-time { font-size: 11px; color: #999; margin-top: 4px; }
.user .message-time { text-align: right; }
.message-actions { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.message-actions .el-button { border-radius: 6px; }
.creation-notice {
  margin-top: 6px; padding: 6px 10px; border-radius: 6px;
  font-size: 12px; display: flex; align-items: center; gap: 4px;
}
.creation-notice.success { background: #f0f9eb; color: #67c23a; border: 1px solid #b3e19d; }
.creation-notice .el-link { font-size: 12px; }
.chat-input { padding: 12px; border-top: 1px solid #eee; display: flex; flex-direction: column; gap: 8px; }
.attachment-list { display: flex; flex-wrap: wrap; gap: 6px; }
.attachment-item { display: flex; align-items: center; gap: 4px; padding: 3px 8px; background: #f0f9eb; border: 1px solid #b3e19d; border-radius: 4px; font-size: 12px; }
.att-name { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.input-row { display: flex; gap: 8px; align-items: flex-end; }
.input-row .el-textarea { flex: 1; }
.dots { display: flex; gap: 4px; }
.dots span { width: 6px; height: 6px; border-radius: 50%; background: #999; animation: load 1.4s infinite ease-in-out both; }
.dots span:nth-child(1) { animation-delay: -0.32s; }
.dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes load { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* Header buttons - high contrast on gradient */
.header-select { width: 100px; }
.header-select-wide { width: 140px; }
.header-select :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.15) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255,255,255,0.3) !important;
}
.header-select :deep(.el-input__inner) {
  color: #fff !important;
  font-size: 13px;
}
.header-select :deep(.el-input__inner)::placeholder {
  color: rgba(255,255,255,0.6) !important;
}
.header-select :deep(.el-select__caret) {
  color: rgba(255,255,255,0.8) !important;
}
.header-icon-btn {
  width: 32px; height: 32px; border-radius: 6px;
  border: none; cursor: pointer;
  background: rgba(255,255,255,0.15);
  color: #fff; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
}
.header-icon-btn:hover {
  background: rgba(255,255,255,0.3);
}
.header-close-btn {
  width: 32px; height: 32px; border-radius: 6px;
  border: none; cursor: pointer;
  background: rgba(255,71,87,0.8);
  color: #fff; display: flex; align-items: center; justify-content: center;
  transition: background 0.2s;
  font-size: 16px;
}
.header-close-btn:hover {
  background: #ff4757;
}
</style>

<!-- 非scoped 样式，确保下拉框正确显示 -->
<style>
.ai-model-dropdown {
  z-index: 20000 !important;
}

.ai-model-dropdown .el-select-dropdown__item {
  padding: 8px 20px !important;
  font-size: 14px;
}

.ai-model-dropdown .el-select-dropdown__item.selected {
  font-weight: 600 !important;
  color: var(--el-color-primary) !important;
  background-color: var(--el-color-primary-light-9) !important;
}
</style>
