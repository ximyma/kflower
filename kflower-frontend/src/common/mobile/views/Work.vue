<template>
  <div class="mobile-work">
    <van-nav-bar title="工作台" fixed placeholder>
      <template #right>
        <van-icon name="plus" size="20" @click="showCreate = true" />
      </template>
    </van-nav-bar>
    
    <!-- 搜索 -->
    <van-search v-model="searchKeyword" placeholder="搜索工作流" shape="round" @search="doSearch" />
    
    <!-- 分类标签 -->
    <van-tabs v-model:active="activeCategory" sticky>
      <van-tab title="全部" name="all" />
      <van-tab title="进行中" name="running" />
      <van-tab title="已完成" name="completed" />
      <van-tab title="已拒绝" name="rejected" />
    </van-tabs>
    
    <!-- 工作流列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list v-model:loading="loading" :finished="finished" finished-text="没有更多了" @load="onLoad">
        <van-card v-for="item in workflowList" :key="item.id" :title="item.title" :thumb="item.icon || defaultIcon" @click="openWorkflow(item)">
          <template #desc>
            <div class="workflow-desc">{{ item.description || '暂无描述' }}</div>
          </template>
          <template #tags>
            <van-tag :type="getStatusType(item.status)" size="medium">{{ getStatusText(item.status) }}</van-tag>
            <van-tag plain size="medium">{{ item.category || '通用' }}</van-tag>
          </template>
          <template #footer>
            <span class="workflow-time">{{ item.created_at }}</span>
          </template>
        </van-card>
      </van-list>
    </van-pull-refresh>
    
    <!-- 创建选择 -->
    <van-action-sheet v-model:show="showCreate" :actions="createActions" @select="onCreateSelect" />
    
    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" fixed route>
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="apps-o" to="/apps">应用</van-tabbar-item>
      <van-tabbar-item icon="todo-list-o" to="/todo">待办</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref(1)
const activeCategory = ref('all')
const showCreate = ref(false)
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const searchKeyword = ref('')

const defaultIcon = 'https://fastly.jsdelivr.net/npm/@vant/assets/ipad.jpeg'

const workflowList = ref<any[]>([])

const createActions = [
  { name: '发起新流程', value: 'new' },
  { name: '从模板创建', value: 'template' }
]

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    running: 'primary',
    approved: 'success',
    completed: 'success',
    rejected: 'danger',
    draft: 'default'
  }
  return types[status] || 'default'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    running: '进行中',
    approved: '已批准',
    completed: '已完成',
    rejected: '已拒绝',
    draft: '草稿'
  }
  return texts[status] || status
}

const loadWorkflows = async () => {
  try {
    const params = new URLSearchParams()
    if (activeCategory.value !== 'all') {
      params.append('status', activeCategory.value)
    }
    if (searchKeyword.value) {
      params.append('search', searchKeyword.value)
    }
    
    const res = await fetch(`/api/v1/workflows/?${params}`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      workflowList.value = data.items || []
    }
  } catch (e) {
    console.error(e)
  }
  loading.value = false
  refreshing.value = false
}

const onRefresh = () => {
  finished.value = false
  loadWorkflows()
}

const onLoad = () => {
  if (workflowList.value.length >= 50) {
    finished.value = true
  } else {
    loadWorkflows()
  }
}

const doSearch = () => {
  loadWorkflows()
}

const openWorkflow = (item: any) => {
  router.push(`/workflow/${item.id}`)
}

const onCreateSelect = (action: any) => {
  if (action.value === 'new') {
    router.push('/workflow/new')
  } else if (action.value === 'template') {
    router.push('/templates')
  }
}

watch(activeCategory, () => {
  loadWorkflows()
})

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.mobile-work {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 60px;
}

.workflow-desc {
  color: #969799;
  font-size: 12px;
  margin-top: 4px;
}

.workflow-time {
  color: #969799;
  font-size: 12px;
}
</style>