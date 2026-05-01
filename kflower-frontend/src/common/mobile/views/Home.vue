<template>
  <div class="mobile-home">
    <!-- 顶部导航 -->
    <van-nav-bar title="Kflower" fixed placeholder>
      <template #right>
        <van-icon name="scan" size="20" @click="showScan = true" />
      </template>
    </van-nav-bar>
    
    <!-- 用户信息卡片 -->
    <div class="user-card">
      <div class="user-avatar">
        <van-image round width="50" height="50" :src="userInfo.avatar || defaultAvatar" />
      </div>
      <div class="user-info">
        <div class="user-name">{{ userInfo.full_name || userInfo.username }}</div>
        <div class="user-dept">{{ userInfo.organization_name || '未分配部门' }}</div>
      </div>
      <van-icon name="arrow" @click="goToProfile" />
    </div>
    
    <!-- 待办统计 -->
    <van-grid :column-num="4" class="stat-grid">
      <van-grid-item icon="todo-list-o" :text="String(stats.pending_tasks)" @click="goToTodo" />
      <van-grid-item icon="clock-o" :text="String(stats.today_tasks)" />
      <van-grid-item icon="passed" :text="String(stats.completed_tasks)" />
      <van-grid-item icon="warning-o" :text="String(stats.overdue_tasks)" />
    </van-grid>
    
    <!-- 快捷入口 -->
    <van-cell-group inset title="快捷入口" class="quick-entry">
      <van-grid :column-num="4">
        <van-grid-item icon="plus" text="新建" @click="showCreateSheet = true" />
        <van-grid-item icon="search" text="搜索" @click="showSearch = true" />
        <van-grid-item icon="chart-trending-o" text="报表" @click="goTo('/analytics')" />
        <van-grid-item icon="chat-o" text="AI助手" @click="showAIChat = true" />
      </van-grid>
    </van-cell-group>
    
    <!-- 我的待办 -->
    <van-cell-group inset title="我的待办" class="todo-list">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <van-swipe-cell v-for="item in todoList" :key="item.id">
            <van-cell :title="item.title" :label="item.created_at" is-link @click="handleTodo(item)">
              <template #icon>
                <van-tag :type="getStatusType(item.status)" size="medium">{{ item.status }}</van-tag>
              </template>
            </van-cell>
            <template #right>
              <van-button square type="primary" text="通过" class="swipe-btn" @click="approveTodo(item)" />
              <van-button square type="danger" text="拒绝" class="swipe-btn" @click="rejectTodo(item)" />
            </template>
          </van-swipe-cell>
        </van-list>
      </van-pull-refresh>
    </van-cell-group>
    
    <!-- AI 对话弹窗 -->
    <van-popup v-model:show="showAIChat" position="bottom" :style="{ height: '70%' }" round>
      <div class="ai-chat-popup">
        <van-nav-bar title="AI 智能助手" left-text="关闭" @click-left="showAIChat = false" />
        <div class="chat-messages" ref="chatContainer">
          <div v-for="msg in chatMessages" :key="msg.id" :class="['message', msg.role]">
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>
        <van-cell-group inset class="chat-input">
          <van-field v-model="chatInput" placeholder="输入消息..." @keyup.enter="sendChat">
            <template #button>
              <van-button size="small" type="primary" @click="sendChat">发送</van-button>
            </template>
          </van-field>
        </van-cell-group>
      </div>
    </van-popup>
    
    <!-- 搜索弹窗 -->
    <van-popup v-model:show="showSearch" position="top" :style="{ height: '100%' }">
      <van-search v-model="searchKeyword" placeholder="搜索模板、流程、数据..." show-action @cancel="showSearch = false" @search="doSearch" />
      <div class="search-results" v-if="searchResults.length">
        <van-cell-group inset title="搜索结果">
          <van-cell v-for="r in searchResults" :key="r.id" :title="r.title" :label="r.type" is-link @click="openSearchResult(r)" />
        </van-cell-group>
      </div>
      <van-empty v-else description="输入关键词搜索" />
    </van-popup>
    
    <!-- 创建选择 -->
    <van-action-sheet v-model:show="showCreateSheet" :actions="createActions" @select="onCreateSelect" />
    
    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" fixed>
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="apps-o" to="/apps">应用</van-tabbar-item>
      <van-tabbar-item icon="todo-list-o" to="/todo" :badge="stats.pending_tasks">待办</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'

const router = useRouter()
const activeTab = ref(0)
const showAIChat = ref(false)
const showSearch = ref(false)
const showCreateSheet = ref(false)
const showScan = ref(false)
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const chatInput = ref('')
const searchKeyword = ref('')
const searchResults = ref<any[]>([])
const chatContainer = ref<HTMLElement>()

const defaultAvatar = 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'

const userInfo = reactive({
  username: '',
  full_name: '',
  avatar: '',
  organization_name: ''
})

const stats = reactive({
  pending_tasks: 0,
  today_tasks: 0,
  completed_tasks: 0,
  overdue_tasks: 0
})

const todoList = ref<any[]>([])
const chatMessages = ref<any[]>([])

const createActions = [
  { name: '新建流程', value: 'workflow' },
  { name: '新建数据', value: 'data' },
  { name: '发起审批', value: 'approval' }
]

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'warning',
    running: 'primary',
    approved: 'success',
    rejected: 'danger'
  }
  return types[status] || 'default'
}

const loadUserInfo = async () => {
  try {
    const res = await fetch('/api/v1/users/me', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      Object.assign(userInfo, data)
    }
  } catch (e) {
    console.error(e)
  }
}

const loadStats = async () => {
  try {
    const res = await fetch('/api/v1/dashboard/stats', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      Object.assign(stats, data)
    }
  } catch (e) {
    console.error(e)
  }
}

const loadTodos = async () => {
  try {
    const res = await fetch('/api/v1/dashboard/pending-tasks', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      todoList.value = data.items || []
    }
  } catch (e) {
    console.error(e)
  }
  loading.value = false
  refreshing.value = false
}

const onRefresh = () => {
  finished.value = false
  loadTodos()
}

const onLoad = () => {
  if (todoList.value.length >= 20) {
    finished.value = true
  } else {
    loadTodos()
  }
}

const goTo = (path: string) => router.push(path)
const goToProfile = () => router.push('/profile')
const goToTodo = () => { activeTab.value = 2; router.push('/todo') }

const handleTodo = (item: any) => {
  router.push(`/workflow/instance/${item.id}`)
}

const approveTodo = async (item: any) => {
  showToast('已通过')
  await loadTodos()
}

const rejectTodo = async (item: any) => {
  showToast('已拒绝')
  await loadTodos()
}

const sendChat = async () => {
  if (!chatInput.value.trim()) return
  
  chatMessages.value.push({ id: Date.now(), role: 'user', content: chatInput.value })
  const userMsg = chatInput.value
  chatInput.value = ''
  
  try {
    const res = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + localStorage.getItem('access_token')
      },
      body: JSON.stringify({ message: userMsg })
    })
    if (res.ok) {
      const data = await res.json()
      chatMessages.value.push({ id: Date.now(), role: 'assistant', content: data.response || data.content })
    }
  } catch (e) {
    chatMessages.value.push({ id: Date.now(), role: 'assistant', content: '抱歉，AI 服务暂时不可用' })
  }
}

const doSearch = async () => {
  if (!searchKeyword.value.trim()) return
  showLoadingToast({ message: '搜索中...', forbidClick: true })
  
  try {
    const res = await fetch(`/api/v1/search?q=${encodeURIComponent(searchKeyword.value)}`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      searchResults.value = data.items || []
    }
  } catch (e) {
    searchResults.value = []
  }
  closeToast()
}

const openSearchResult = (r: any) => {
  showSearch.value = false
  if (r.type === 'template') router.push(`/template/${r.id}`)
  else if (r.type === 'workflow') router.push(`/workflow/${r.id}`)
}

const onCreateSelect = (action: any) => {
  if (action.value === 'workflow') router.push('/workflow/new')
  else if (action.value === 'data') router.push('/data/new')
  else if (action.value === 'approval') router.push('/approval/new')
}

onMounted(() => {
  loadUserInfo()
  loadStats()
  loadTodos()
})
</script>

<style scoped>
.mobile-home {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 60px;
}

.user-card {
  display: flex;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin: 10px;
  border-radius: 12px;
}

.user-info {
  flex: 1;
  margin-left: 12px;
}

.user-name {
  font-size: 18px;
  font-weight: bold;
}

.user-dept {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 4px;
}

.stat-grid {
  margin: 10px;
  border-radius: 12px;
  overflow: hidden;
}

.quick-entry, .todo-list {
  margin: 10px;
}

.ai-chat-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.message {
  margin-bottom: 10px;
}

.message.user .message-content {
  background: #1989fa;
  color: white;
  margin-left: auto;
}

.message.assistant .message-content {
  background: #f0f0f0;
  color: #333;
}

.message-content {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.chat-input {
  position: sticky;
  bottom: 0;
}

.swipe-btn {
  height: 100%;
}
</style>