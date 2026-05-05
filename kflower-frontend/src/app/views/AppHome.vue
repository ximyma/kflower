<template>
  <div class="app-home-page">
    <!-- 顶部导航 -->
    <div class="nav-bar">
      <div class="nav-left" @click="$router.back()">
        <el-icon :size="22"><ArrowLeft /></el-icon>
      </div>
      <div class="nav-title">{{ appData.name || '加载中...' }}</div>
      <div class="nav-right">
        <el-button text size="small" @click="$router.push(`/app/app-designer/${appId}`)" style="color: white;">
          <el-icon><Edit /></el-icon> 设计
        </el-button>
      </div>
    </div>

    <div class="page-content" v-loading="loading">
      <!-- 应用介绍卡片 -->
      <div class="app-hero" v-if="appData.name">
        <div class="hero-icon" :style="{ background: getAppGradient(appData.id) }">
          <el-icon :size="32"><component :is="appData.icon || 'Grid'" /></el-icon>
        </div>
        <div class="hero-info">
          <h2 class="hero-name">{{ appData.name }}</h2>
          <p class="hero-desc" v-if="appData.description">{{ appData.description }}</p>
          <p class="hero-desc" v-else>点击下方模块开始使用</p>
        </div>
      </div>

      <!-- 菜单列表 -->
      <div class="module-section">
        <div class="section-header">
          <span class="section-title">功能模块</span>
          <span class="section-count">{{ flatMenus.length }}个</span>
        </div>

        <!-- 空白状态 -->
        <div v-if="flatMenus.length === 0 && !loading" class="empty-modules">
          <div class="empty-icon-wrap">
            <el-icon :size="44"><Document /></el-icon>
          </div>
          <p class="empty-text">还没有功能模块</p>
          <p class="empty-sub">请在应用设计器中添加菜单</p>
          <el-button type="primary" round @click="$router.push(`/app/app-designer/${appId}`)">
            去设计应用
          </el-button>
        </div>

        <!-- 菜单卡片网格 -->
        <div class="menu-grid">
          <div
            v-for="menu in flatMenus"
            :key="menu.id"
            class="menu-card"
            @click="openMenu(menu)"
          >
            <!-- 卡片顶部色条 -->
            <div class="card-top-bar" :style="{ background: getModuleColor(menu.id) }" />

            <!-- 卡片内容 -->
            <div class="card-content">
              <div class="card-icon-wrap" :style="{ background: getModuleColor(menu.id) + '22' }">
                <el-icon :size="22" :style="{ color: getModuleColor(menu.id) }">
                  <component :is="getMenuIcon(menu)" />
                </el-icon>
              </div>
              <div class="card-info">
                <div class="card-name">{{ menu.label }}</div>
                <div class="card-sub" v-if="menu.workflow_id">工作流</div>
              </div>
            </div>

            <!-- 箭头 -->
            <div class="card-arrow">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowLeft, ArrowRight, Edit, Grid, Document, List, Checked,
  Connection, Folder, Setting, ChatDotRound, DataAnalysis, Files
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import appAPI from '../../common/api/myApps'

const route = useRoute()
const router = useRouter()

const appId = Number(route.params.appId)
const loading = ref(false)
const appData = ref<any>({})
const menuTree = ref<any[]>([])

// 渐变色
const gradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
]

// 模块颜色
const moduleColors = [
  '#667eea', '#f5576c', '#00c6fb', '#38a169',
  '#ed8936', '#d53f8c', '#319795', '#805ad5',
  '#dd6b20', '#38b2ac', '#e53e3e', '#2b6cb0',
]

// 将菜单树扁平化，只显示有 template_id 的叶子节点
const flatMenus = computed(() => {
  const result: any[] = []

  function traverse(menus: any[]) {
    for (const menu of menus) {
      // 如果有 template_id，说明是一个功能菜单
      if (menu.template_id) {
        result.push(menu)
      }
      // 递归处理子菜单
      if (menu.children && menu.children.length > 0) {
        traverse(menu.children)
      }
    }
  }

  traverse(menuTree.value)
  return result
})

function getAppGradient(id: number) {
  return gradients[id % gradients.length]
}

function getModuleColor(id: number) {
  return moduleColors[id % moduleColors.length]
}

function getMenuIcon(menu: any) {
  // 根据 icon 或者菜单类型返回图标
  if (menu.icon) return menu.icon
  if (menu.workflow_id) return 'Connection'
  if (menu.template_id) return 'List'
  return 'Document'
}

async function loadApp() {
  loading.value = true
  try {
    // 并行加载应用详情和菜单树
    const [appDetail, treeData] = await Promise.all([
      appAPI.get(appId),
      appAPI.getMenuTree(appId)
    ])

    appData.value = appDetail
    menuTree.value = treeData || []

    console.log('[AppHome] 加载成功:', {
      app: appDetail.name,
      menus: menuTree.value,
      flatMenus: flatMenus.value.length
    })
  } catch (e: any) {
    console.error('[AppHome] 加载应用失败:', e)
    ElMessage.error('加载应用失败')
  } finally {
    loading.value = false
  }
}

function openMenu(menu: any) {
  console.log('[AppHome] 打开菜单:', menu)

  // 如果有工作流ID
  if (menu.workflow_id) {
    // TODO: 进入工作流
    ElMessage.info('工作流功能开发中')
    return
  }

  // 有模板ID，进入表单数据列表
  if (menu.template_id) {
    router.push({
      name: 'AppFormListPage',
      params: { appId, templateId: String(menu.template_id) }
    })
    return
  }

  // 两者都没有，提示用户
  ElMessage.warning('该菜单未配置功能')
}

onMounted(() => {
  loadApp()
})
</script>

<style scoped>
.app-home-page {
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

/* 页面内容 */
.page-content {
  padding: 16px;
}

/* 应用介绍卡片 */
.app-hero {
  background: white;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
}

.hero-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}

.hero-info {
  flex: 1;
  min-width: 0;
}

.hero-name {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.hero-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.4;
}

/* 功能模块区域 */
.module-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 0 2px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.section-count {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 空白状态 */
.empty-modules {
  text-align: center;
  padding: 48px 20px;
  background: white;
  border-radius: 16px;
  border: 1px solid #f0f0f0;
}

.empty-icon-wrap {
  width: 88px;
  height: 88px;
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
  margin-bottom: 4px;
}

.empty-sub {
  font-size: 13px;
  color: #909399;
  margin-bottom: 18px;
}

/* 菜单卡片网格 */
.menu-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-card {
  background: white;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: transform 0.18s, box-shadow 0.18s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f0f0;
}

.menu-card:active {
  transform: scale(0.98);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-top-bar {
  width: 4px;
  min-height: 70px;
  align-self: stretch;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 8px 14px 14px;
}

.card-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.card-arrow {
  padding: 0 14px;
  color: #c0c4cc;
  flex-shrink: 0;
}
</style>
