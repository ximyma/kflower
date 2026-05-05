<template>
  <div class="app-form-list">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-left" @click="goBack">
        <el-icon :size="22"><ArrowLeft /></el-icon>
      </div>
      <div class="nav-title">{{ templateData.name || '数据列表' }}</div>
      <div class="nav-right">
        <el-button type="primary" size="small" round @click="addNew">
          <el-icon><Plus /></el-icon>新增
        </el-button>
      </div>
    </div>

    <div class="page-content" v-loading="loading">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索数据..."
          clearable
          size="large"
          :prefix-icon="Search"
          @input="onSearch"
        />
      </div>

      <!-- 数据列表 -->
      <div class="data-list">
        <!-- 空状态 -->
        <div v-if="filteredData.length === 0 && !loading" class="empty-state">
          <div class="empty-icon">
            <el-icon :size="48"><Document /></el-icon>
          </div>
          <p class="empty-text">{{ searchKeyword ? '没有找到相关数据' : '还没有数据' }}</p>
          <el-button v-if="!searchKeyword" type="primary" round @click="addNew">
            添加第一条数据
          </el-button>
        </div>

        <!-- 数据卡片列表 -->
        <div
          v-for="item in filteredData"
          :key="item.id"
          class="data-card"
          @click="viewDetail(item)"
        >
          <div class="card-title">{{ getItemTitle(item) }}</div>
          <div class="card-meta">
            <span class="card-time" v-if="item.created_at">{{ formatTime(item.created_at) }}</span>
          </div>
          <div class="card-summary">{{ getItemSummary(item) }}</div>
        </div>

        <!-- 加载更多 -->
        <div v-if="hasMore && !loading" class="load-more">
          <el-button text @click="loadMore">加载更多</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, Plus, Search, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { templateAPI } from '../../common/api'

const router = useRouter()
const route = useRoute()
const appId = Number(route.params.appId)
const templateId = Number(route.params.templateId)

const loading = ref(false)
const dataList = ref<any[]>([])
const templateData = ref<any>({})
const searchKeyword = ref('')
const hasMore = ref(false)
const currentPage = ref(1)
const pageSize = 20

const filteredData = computed(() => {
  if (!searchKeyword.value.trim()) return dataList.value
  const kw = searchKeyword.value.toLowerCase()
  return dataList.value.filter(item =>
    (item.title || item.name || '').toLowerCase().includes(kw) ||
    (item.description || item.content || '').toLowerCase().includes(kw)
  )
})

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function getItemTitle(item: any) {
  // 尝试从数据中获取标题字段
  // 后端返回 name 格式为 "模板名_数据_id"，但实际数据在 item 里是展开的
  // 优先使用 name 字段，如果没有则用 id
  if (item.name && item.name !== `数据_#${item.id}`) {
    return item.name
  }
  return `数据 #${item.id}`
}

function getItemSummary(item: any) {
  // 显示创建时间
  if (item.created_at) {
    return formatTime(item.created_at)
  }
  return '点击查看详情'
}

function goBack() {
  router.push(`/app/app-home/${appId}`)
}

function addNew() {
  router.push({ name: 'AppFormNew', params: { appId, templateId: String(templateId) } })
}

function viewDetail(item: any) {
  router.push({
    name: 'AppFormEditPage',
    params: { appId, templateId: String(templateId), dataId: String(item.id) }
  })
}

let searchTimer: any = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    // 搜索时重新加载数据
    currentPage.value = 1
    loadData()
  }, 300)
}

async function loadMore() {
  currentPage.value++
  await loadData(true)
}

async function loadData(append = false) {
  loading.value = true
  try {
    // 并行加载模板信息和数据
    const [tmplRes, dataRes] = await Promise.all([
      templateAPI.get(templateId),
      templateAPI.getData(templateId, {
        skip: (currentPage.value - 1) * pageSize,
        limit: pageSize
      })
    ])

    templateData.value = tmplRes

    // 后端返回的是数组，不是 {items: [...]} 格式
    const items = Array.isArray(dataRes) ? dataRes : (dataRes.items || dataRes || [])
    if (append) {
      dataList.value = [...dataList.value, ...items]
    } else {
      dataList.value = items
    }

    // 判断是否还有更多数据
    hasMore.value = items.length >= pageSize

    console.log('[AppFormList] 加载成功:', {
      template: tmplRes.name,
      dataCount: dataList.value.length,
      hasMore: hasMore.value
    })
  } catch (error) {
    console.error('[AppFormList] 加载失败:', error)
    if (!append) {
      dataList.value = []
    }
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.app-form-list {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 20px;
}

/* 顶部导航 */
.nav-bar {
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.nav-title {
  flex: 1;
  font-size: 17px;
  font-weight: 600;
  text-align: center;
  padding-right: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-right {
  padding-right: 8px;
}

.nav-right :deep(.el-button) {
  padding: 6px 12px;
  font-size: 12px;
}

.page-content {
  padding: 16px;
}

.search-bar {
  margin-bottom: 12px;
}

.search-bar :deep(.el-input__wrapper) {
  border-radius: 22px;
  background: white;
  box-shadow: 0 0 0 1px #e8e8e8;
  padding: 6px 16px;
}

.search-bar :deep(.el-input__inner) {
  font-size: 14px;
}

.data-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 16px;
  border: 1px solid #f0f0f0;
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f0f2f5 0%, #e8e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
  color: #c0c4cc;
}

.empty-text {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 14px;
}

.data-card {
  background: white;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s;
}

.data-card:active {
  transform: scale(0.98);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.card-time {
  font-size: 11px;
  color: #c0c4cc;
}

.card-summary {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.load-more {
  text-align: center;
  padding: 16px;
}
</style>
