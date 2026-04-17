<template>
  <div class="app-layout">
    <!-- 顶部导航 -->
    <div class="app-header">
      <div class="header-title">
        <el-icon :size="20"><MagicStick /></el-icon>
        <span>Kflower</span>
      </div>
      <el-icon :size="24"><Bell /></el-icon>
    </div>
    
    <!-- 内容区 -->
    <div class="app-content">
      <router-view />
    </div>
    
    <!-- 底部导航 -->
    <div class="app-tabbar">
      <div
        v-for="tab in tabs"
        :key="tab.path"
        class="tab-item"
        :class="{ active: $route.path === tab.path }"
        @click="$router.push(tab.path)"
      >
        <el-icon :size="24"><component :is="tab.icon" /></el-icon>
        <span>{{ tab.name }}</span>
      </div>
    </div>
    
    <!-- AI助手按钮 -->
    <div class="ai-fab" @click="aiStore.toggleChat">
      <el-icon :size="28"><MagicStick /></el-icon>
    </div>
    
    <!-- AI对话框 -->
    <AIChatDialog v-if="aiStore.showChat" @close="aiStore.toggleChat" />
  </div>
</template>

<script setup lang="ts">
import { MagicStick, HomeFilled, Briefcase, User, Bell } from '@element-plus/icons-vue'
import { useAIStore } from '../../common/store/ai'
import AIChatDialog from '../../common/components/AIChatDialog.vue'

const aiStore = useAIStore()

const tabs = [
  { name: '首页', path: '/app/home', icon: 'HomeFilled' },
  { name: '工作', path: '/app/work', icon: 'Briefcase' },
  { name: '我的', path: '/app/profile', icon: 'User' }
]
</script>

<style scoped>
.app-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.app-header {
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.app-tabbar {
  height: 56px;
  background: white;
  display: flex;
  border-top: 1px solid #e6e6e6;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 12px;
  gap: 2px;
}

.tab-item.active {
  color: #667eea;
}

.ai-fab {
  position: fixed;
  bottom: 80px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
