<template>
  <div class="app-profile">
    <!-- 用户信息卡片 -->
    <div class="profile-header">
      <div class="avatar-wrapper">
        <el-avatar :size="72" :icon="UserFilled" />
        <div class="avatar-badge" v-if="userStore.isAdmin">
          <el-icon :size="12"><Star /></el-icon>
        </div>
      </div>
      <h3>{{ userStore.userInfo?.full_name || '用户' }}</h3>
      <p>{{ userStore.userInfo?.email || userStore.userInfo?.username }}</p>
      <div class="user-tags">
        <el-tag size="small" v-if="userStore.isAdmin" type="warning">管理员</el-tag>
        <el-tag size="small" type="info">{{ userStore.userInfo?.organization || '个人用户' }}</el-tag>
      </div>
    </div>
    
    <!-- 功能入口 -->
    <div class="entry-grid">
      <div class="entry-item" @click="$router.push('/app/my-apps')">
        <div class="entry-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <el-icon :size="22"><Grid /></el-icon>
        </div>
        <span>我的应用</span>
      </div>
      <div class="entry-item" @click="$router.push('/app/agents')">
        <div class="entry-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
          <el-icon :size="22"><Cpu /></el-icon>
        </div>
        <span>我的智能体</span>
      </div>
      <div class="entry-item" @click="$router.push('/app/ai-base')">
        <div class="entry-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
          <el-icon :size="22"><DataAnalysis /></el-icon>
        </div>
        <span>AI底座</span>
      </div>
      <div class="entry-item" @click="$router.push('/app/ai-tools')">
        <div class="entry-icon" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
          <el-icon :size="22"><Tools /></el-icon>
        </div>
        <span>AI工具</span>
      </div>
    </div>
    
    <!-- 设置菜单 -->
    <div class="menu-list">
      <div class="menu-item" @click="goToSettings('profile')">
        <div class="menu-left">
          <el-icon :size="20" color="#409EFF"><User /></el-icon>
          <span>个人信息</span>
        </div>
        <el-icon :size="16" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="goToSettings('ai')">
        <div class="menu-left">
          <el-icon :size="20" color="#667eea"><MagicStick /></el-icon>
          <span>AI设置</span>
        </div>
        <el-icon :size="16" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="goToSettings('system')">
        <div class="menu-left">
          <el-icon :size="20" color="#67C23A"><Setting /></el-icon>
          <span>系统设置</span>
        </div>
        <el-icon :size="16" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="showHelp">
        <div class="menu-left">
          <el-icon :size="20" color="#E6A23C"><QuestionFilled /></el-icon>
          <span>帮助与反馈</span>
        </div>
        <el-icon :size="16" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="showAbout">
        <div class="menu-left">
          <el-icon :size="20" color="#909399"><InfoFilled /></el-icon>
          <span>关于我们</span>
        </div>
        <el-icon :size="16" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
    </div>
    
    <!-- 退出登录 -->
    <el-button type="danger" plain class="logout-btn" @click="handleLogout">
      <el-icon><SwitchButton /></el-icon>
      退出登录
    </el-button>
    
    <div class="version-info">
      Kflower v1.0.0 · 移动端
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { useRouter } from 'vue-router'
import { UserFilled, User, Setting, MagicStick, QuestionFilled, InfoFilled, ArrowRight, Grid, Cpu, DataAnalysis, Tools, Star, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '../../common/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

function goToSettings(type: string) {
  ElMessageBox.confirm('该功能需要在电脑端进行设置。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).catch(() => {})
}

function showHelp() {
  ElMessage.info('帮助文档请访问官网')
}

function showAbout() {
  ElMessageBox.alert('Kflower 智能应用设计平台<br>v1.0.0<br><br>基于 AI 的低代码应用开发平台', '关于我们', {
    confirmButtonText: '知道了'
  })
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    type: 'warning'
  }).then(() => {
    userStore.logout()
    router.push('/app/login')
  }).catch(() => {})
}
</script>

<style scoped>
.app-profile {
  padding-bottom: 30px;
}

.profile-header {
  text-align: center;
  padding: 24px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 0 0 24px 24px;
  margin: -12px -12px 16px -12px;
  color: white;
}

.avatar-wrapper {
  position: relative;
  display: inline-block;
}

.avatar-wrapper :deep(.el-avatar) {
  background: rgba(255, 255, 255, 0.2);
}

.avatar-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 22px;
  height: 22px;
  background: #E6A23C;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.profile-header h3 {
  margin-top: 12px;
  margin-bottom: 4px;
  font-size: 18px;
}

.profile-header p {
  opacity: 0.9;
  font-size: 13px;
  margin-bottom: 10px;
}

.user-tags {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.user-tags :deep(.el-tag) {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px;
  background: white;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.entry-item:active {
  transform: scale(0.95);
}

.entry-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.entry-item span {
  font-size: 11px;
  color: #606266;
}

.menu-list {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 16px;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-item:active {
  background: #f5f7fa;
}

.menu-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-left span {
  font-size: 14px;
  color: #303133;
}

.logout-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
}

.version-info {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 20px;
}
</style>
