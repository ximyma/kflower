<template>
  <div class="app-home">
    <!-- 欢迎卡片 -->
    <div class="welcome-card">
      <div class="welcome-content">
        <h2>你好，{{ userStore.userInfo?.full_name || '用户' }}</h2>
        <p>今天有什么可以帮您的？</p>
      </div>
      <div class="ai-avatar" @click="$router.push('/app/chat')">
        <el-icon :size="28"><MagicStick /></el-icon>
      </div>
    </div>
    
    <!-- 快捷入口 -->
    <div class="quick-grid">
      <div
        v-for="item in quickActions"
        :key="item.path"
        class="quick-item"
        @click="$router.push(item.path)"
      >
        <div class="quick-icon" :style="{ background: item.color }">
          <el-icon :size="24"><component :is="item.icon" /></el-icon>
        </div>
        <span class="quick-title">{{ item.title }}</span>
      </div>
    </div>
    
    <!-- AI智能助手卡片 -->
    <div class="section-card ai-section" @click="$router.push('/app/chat')">
      <div class="section-left">
        <div class="section-icon ai-icon-bg">
          <el-icon :size="28"><ChatDotRound /></el-icon>
        </div>
        <div class="section-info">
          <h3>AI 智能助手</h3>
          <p>随时为您服务</p>
        </div>
      </div>
      <el-icon :size="20" color="#c0c4cc"><ArrowRight /></el-icon>
    </div>
    
    <!-- 我的应用入口 -->
    <div class="section-card" @click="$router.push('/app/my-apps')">
      <div class="section-left">
        <div class="section-icon" style="background: #67C23A;">
          <el-icon :size="24"><Grid /></el-icon>
        </div>
        <div class="section-info">
          <h3>我的应用</h3>
          <p>查看和管理我的应用</p>
        </div>
      </div>
      <el-icon :size="20" color="#c0c4cc"><ArrowRight /></el-icon>
    </div>
    
    <!-- 我的智能体入口 -->
    <div class="section-card" @click="$router.push('/app/agents')">
      <div class="section-left">
        <div class="section-icon" style="background: #E6A23C;">
          <el-icon :size="24"><Cpu /></el-icon>
        </div>
        <div class="section-info">
          <h3>我的智能体</h3>
          <p>智能体编排和管理</p>
        </div>
      </div>
      <el-icon :size="20" color="#c0c4cc"><ArrowRight /></el-icon>
    </div>
    
    <!-- AI能力卡片 -->
    <div class="section-title">AI 能力</div>
    <div class="ai-cards">
      <div class="ai-card-item" @click="$router.push('/app/ai-base')">
        <div class="ai-card-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <el-icon :size="22"><DataAnalysis /></el-icon>
        </div>
        <span>AI数字底座</span>
      </div>
      <div class="ai-card-item" @click="$router.push('/app/ai-tools')">
        <div class="ai-card-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
          <el-icon :size="22"><Tools /></el-icon>
        </div>
        <span>AI工具集</span>
      </div>
    </div>
    
    <!-- 工作区入口 -->
    <div class="section-card" @click="$router.push('/app/workspace')">
      <div class="section-left">
        <div class="section-icon" style="background: #909399;">
          <el-icon :size="24"><Monitor /></el-icon>
        </div>
        <div class="section-info">
          <h3>我的工作区</h3>
          <p>工作统计和最近活动</p>
        </div>
      </div>
      <el-icon :size="20" color="#c0c4cc"><ArrowRight /></el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  Document, Connection, Files, User,
  MagicStick, ArrowRight, ChatDotRound, Grid, Cpu,
  DataAnalysis, Tools, Monitor
} from '@element-plus/icons-vue'
import { useUserStore } from '../../common/store/user'

const userStore = useUserStore()

const quickActions = [
  { title: '模板设计', icon: 'Document', color: '#409EFF', path: '/app/templates' },
  { title: '流程审批', icon: 'Connection', color: '#67C23A', path: '/app/workflows' },
  { title: '知识库', icon: 'Files', color: '#F56C6C', path: '/app/knowledge' },
  { title: '个人中心', icon: 'User', color: '#909399', path: '/app/profile' }
]
</script>

<style scoped>
.app-home {
  padding-bottom: 30px;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-content h2 {
  margin-bottom: 4px;
  font-size: 18px;
}

.welcome-content p {
  opacity: 0.9;
  font-size: 13px;
}

.ai-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.ai-avatar:active {
  transform: scale(0.95);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  background: white;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.quick-item:active {
  transform: scale(0.97);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.quick-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.quick-title {
  font-size: 12px;
  color: #303133;
  text-align: center;
}

.section-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: transform 0.2s;
}

.section-card:active {
  transform: scale(0.98);
}

.section-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.ai-icon-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.section-info h3 {
  margin-bottom: 4px;
  font-size: 15px;
  color: #303133;
}

.section-info p {
  color: #909399;
  font-size: 12px;
}

.section-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
  margin-top: 8px;
  padding-left: 4px;
}

.ai-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.ai-card-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s;
}

.ai-card-item:active {
  transform: scale(0.97);
}

.ai-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.ai-card-item span {
  font-size: 13px;
  color: #303133;
}
</style>
