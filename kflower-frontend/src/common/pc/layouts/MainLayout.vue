<template>
  <div class="main-layout">
    <div class="sidebar">
      <div class="logo">Kflower</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/home">
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <span>模板设计</span>
        </el-menu-item>
        <el-menu-item index="/workflows">
          <span>流程审批</span>
        </el-menu-item>
        <el-menu-item index="/analytics">
          <span>决策分析</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isAdmin" index="/settings">
          <span>系统设置</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isAdmin" index="/migration">
          <span>数据迁移</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="main-content">
      <header class="topbar">
        <div class="topbar-left">
          <h2>Kflower 企业智能管理平台</h2>
        </div>
        <div class="topbar-right">
          <AIChatButton />
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              {{ userStore.userInfo?.full_name || userStore.userInfo?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      <main class="page-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { ElMessage } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import AIChatButton from '../../components/AIChatButton.vue'

const router = useRouter()
const userStore = useUserStore()

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 200px;
  background: #304156;
  flex-shrink: 0;
  overflow-y: auto;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  letter-spacing: 2px;
  border-bottom: 1px solid #263445;
}

.sidebar :deep(.el-menu) {
  border-right: none;
  background: #304156;
}

.sidebar :deep(.el-menu-item) {
  color: #bfcbd9;
  font-size: 14px;
}

.sidebar :deep(.el-menu-item:hover),
.sidebar :deep(.el-menu-item.is-active) {
  background: #263445;
  color: #409eff;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.topbar {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
}

.topbar-left h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
  font-weight: 600;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #333;
  font-size: 14px;
}

.page-content {
  flex: 1;
  overflow-y: auto;
  background: #f0f2f5;
  padding: 20px;
}
</style>
