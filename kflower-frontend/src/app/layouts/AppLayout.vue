<template>
  <div class="app-layout" :class="{ 'hide-tabbar': isFullscreenPage }">
    <!-- 顶部导航 -->
    <div class="app-header" v-if="!isFullscreenPage">
      <div class="header-left" @click="$router.push('/app/home')">
        <el-icon :size="22"><MagicStick /></el-icon>
        <span>Kflower</span>
      </div>
      <div class="header-right">
        <!-- 全屏按钮（设计页面显示） -->
        <el-button
          v-if="isDesignerPage"
          text
          style="color: white"
          @click="toggleFullscreen"
        >
          <el-icon :size="20"><FullScreen /></el-icon>
        </el-button>
        <el-badge :value="12" :max="99">
          <el-icon :size="22"><Bell /></el-icon>
        </el-badge>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="app-content" :class="{ 'fullscreen-content': isFullscreenPage }">
      <router-view />
    </div>

    <!-- 横屏提示（仅在设计页面且非全屏时显示） -->
    <div v-if="isDesignerPage && !isFullscreen && showLandscapeHint" class="landscape-hint">
      <div class="landscape-hint-content">
        <el-icon :size="40"><RefreshRight /></el-icon>
        <p>建议横屏使用以获得更好的体验</p>
        <el-button size="small" @click="showLandscapeHint = false">知道了</el-button>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="app-tabbar" v-if="!isFullscreenPage">
      <div
        v-for="tab in tabs"
        :key="tab.path"
        class="tab-item"
        :class="{ active: isActiveTab(tab.path) }"
        @click="$router.push(tab.path)"
      >
        <el-icon :size="22"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.name }}</span>
      </div>
    </div>

    <!-- AI助手悬浮按钮（仅在非设计页面显示） -->
    <div v-if="!isDesignerPage" class="ai-fab" @click="$router.push('/app/chat')">
      <el-icon :size="24"><ChatDotRound /></el-icon>
    </div>

    <!-- 退出全屏按钮 -->
    <div v-if="isFullscreenPage" class="exit-fullscreen" @click="toggleFullscreen">
      <el-icon :size="20"><Close /></el-icon>
      <span>退出全屏</span>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  MagicStick, HomeFilled, Document, Connection, Files, User, Bell,
  ChatDotRound, FullScreen, Close, RefreshRight, Grid
} from '@element-plus/icons-vue'

const route = useRoute()

// 全屏状态
const isFullscreen = ref(false)
const showLandscapeHint = ref(true)

// 判断是否为设计页面
const isDesignerPage = computed(() => {
  const path = route.path
  return path.includes('designer') || path.includes('template-designer') || path.includes('workflow-designer')
})

// 是否应该隐藏tabbar
const isFullscreenPage = computed(() => isFullscreen.value && isDesignerPage.value)

// 底部导航配置 - 5个核心模块
const tabs = [
  { name: '首页', path: '/app/home', icon: 'HomeFilled' },
  { name: '应用', path: '/app/my-apps', icon: 'Grid' },
  { name: '模板', path: '/app/templates', icon: 'Document' },
  { name: 'AI', path: '/app/chat', icon: 'MagicStick' },
  { name: '我的', path: '/app/profile', icon: 'User' }
]

// 切换全屏
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  showLandscapeHint.value = false

  if (isFullscreen.value) {
    // 进入全屏时尝试切换横屏
    if (screen.orientation && screen.orientation.lock) {
      screen.orientation.lock('landscape').catch(() => {
        // 如果不支持锁定，提示用户手动旋转
      })
    }
  } else {
    // 退出全屏时恢复竖屏
    if (screen.orientation && screen.orientation.unlock) {
      screen.orientation.unlock()
    }
  }
}

// 判断当前路由是否激活
const isActiveTab = (path: string) => {
  const currentPath = route.path
  // 精确匹配
  if (currentPath === path) return true
  // 如果是首页，其他路径不激活
  if (path === '/app/home') return currentPath === '/app/home'
  // 其他Tab：检查是否以该路径开头
  return currentPath.startsWith(path)
}

// 监听屏幕方向变化
function handleOrientationChange() {
  // 横屏时隐藏提示
  if (window.innerWidth > window.innerHeight) {
    showLandscapeHint.value = false
  }
}

onMounted(() => {
  window.addEventListener('orientationchange', handleOrientationChange)
  window.addEventListener('resize', handleOrientationChange)
})

onUnmounted(() => {
  window.removeEventListener('orientationchange', handleOrientationChange)
  window.removeEventListener('resize', handleOrientationChange)
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  max-width: 100%;
  margin: 0 auto;
  transition: all 0.3s;
}

.app-layout.hide-tabbar {
  padding-bottom: 0;
}

.app-header {
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px;
  -webkit-overflow-scrolling: touch;
}

.app-content.fullscreen-content {
  padding: 0;
  background: white;
}

.app-tabbar {
  height: 60px;
  background: white;
  display: flex;
  border-top: 1px solid #e6e6e6;
  flex-shrink: 0;
  padding-bottom: env(safe-area-inset-bottom);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 11px;
  gap: 3px;
  transition: color 0.2s;
  cursor: pointer;
}

.tab-item.active {
  color: #667eea;
}

.tab-item:active {
  opacity: 0.7;
}

.ai-fab {
  position: fixed;
  bottom: 76px;
  right: 16px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  z-index: 100;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.ai-fab:active {
  transform: scale(0.95);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 横屏提示 */
.landscape-hint {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.landscape-hint-content {
  background: white;
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  max-width: 280px;
}

.landscape-hint-content p {
  margin: 16px 0;
  color: #606266;
}

.landscape-hint-content .el-icon {
  color: #E6A23C;
}

/* 退出全屏按钮 */
.exit-fullscreen {
  position: fixed;
  top: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 8px 12px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  z-index: 1000;
  cursor: pointer;
}

.exit-fullscreen:active {
  background: rgba(0, 0, 0, 0.8);
}
</style>
