<template>
  <div class="app-chat">
    <!-- 聊天头部 -->
    <div class="chat-header">
      <el-icon :size="22" @click="$router.back()"><ArrowLeft /></el-icon>
      <span class="header-title">AI 智能助手</span>
      <el-icon :size="22"><MoreFilled /></el-icon>
    </div>
    
    <!-- 聊天消息区 -->
    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="empty-chat">
        <div class="empty-icon">
          <el-icon :size="48"><ChatDotRound /></el-icon>
        </div>
        <p>你好！我是AI智能助手</p>
        <p class="empty-hint">有什么可以帮您的？</p>
        
        <!-- 快捷问题 -->
        <div class="quick-questions">
          <div
            v-for="q in quickQuestions"
            :key="q"
            class="quick-q"
            @click="sendQuickQuestion(q)"
          >
            {{ q }}
          </div>
        </div>
      </div>
      
      <div v-else class="message-list">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message-item"
          :class="msg.role"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" :size="20"><User /></el-icon>
            <el-icon v-else :size="20"><MagicStick /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
      </div>
      
      <!-- 加载中 -->
      <div v-if="loading" class="message-item assistant">
        <div class="message-avatar">
          <el-icon :size="20"><MagicStick /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-text loading">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 输入区域 -->
    <div class="chat-input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 3 }"
        placeholder="输入消息..."
        @keydown.enter.exact.prevent="sendMessage"
      />
      <el-button type="primary" :loading="loading" @click="sendMessage" :disabled="!inputText.trim()">
        <el-icon><Promotion /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, MoreFilled, ChatDotRound, User, MagicStick, Promotion } from '@element-plus/icons-vue'
import { useAIStore } from '../../common/store/ai'
import { aiAPI } from '../../common/api'

const router = useRouter()
const aiStore = useAIStore()

const inputText = ref('')
const loading = ref(false)
const messages = ref<Array<{ role: string; content: string; time: string }>>([])

const quickQuestions = [
  '帮我创建一个请假模板',
  '查询我的待办流程',
  '搜索知识库中关于...的内容',
  '介绍一下AI数字底座'
]

function formatMessage(content: string) {
  // 简单的Markdown格式处理
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function getCurrentTime() {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    time: getCurrentTime()
  })
  inputText.value = ''
  loading.value = true
  scrollToBottom()
  
  try {
    const response = await aiAPI.chat({
      message: text,
      conversation_id: 'mobile-' + Date.now()
    })
    
    messages.value.push({
      role: 'assistant',
      content: response.response || response.message || response.content || '抱歉，我没有收到回复。',
      time: getCurrentTime()
    })
  } catch (error: any) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，服务出了点问题，请稍后重试。',
      time: getCurrentTime()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function sendQuickQuestion(q: string) {
  inputText.value = q
  sendMessage()
}

function scrollToBottom() {
  nextTick(() => {
    const el = document.querySelector('.chat-messages')
    if (el) el.scrollTop = el.scrollHeight
  })
}
</script>

<style scoped>
.app-chat {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 122px);
  margin: -12px;
  background: #f5f7fa;
}

.chat-header {
  height: 50px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  -webkit-overflow-scrolling: touch;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #909399;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-chat p {
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 13px;
  color: #c0c4cc;
  margin-bottom: 20px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  max-width: 300px;
}

.quick-q {
  padding: 8px 14px;
  background: white;
  border-radius: 18px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  border: 1px solid #e6e6e6;
  transition: all 0.2s;
}

.quick-q:active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 10px;
  max-width: 85%;
}

.message-item.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: #409EFF;
}

.message-content {
  flex: 1;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.message-item.assistant .message-text {
  background: white;
  color: #303133;
  border-bottom-left-radius: 4px;
}

.message-item.user .message-text {
  background: #409EFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
  padding: 0 4px;
}

.message-item.user .message-time {
  text-align: right;
}

.loading {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #909399;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  background: white;
  padding: 10px 12px;
  display: flex;
  gap: 10px;
  align-items: flex-end;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 20px;
  padding: 8px 12px;
  resize: none;
}

.chat-input-area .el-button {
  border-radius: 50%;
  width: 38px;
  height: 38px;
  padding: 0;
}
</style>
