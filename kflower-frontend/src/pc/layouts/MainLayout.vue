<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapsed ? '64px' : '200px'">
      <div class="logo">
        <el-icon :size="24"><MagicStick /></el-icon>
        <span v-if="!isCollapsed">Kflower</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>
        
        <el-menu-item index="/templates">
          <el-icon><Document /></el-icon>
          <template #title>模板管理</template>
        </el-menu-item>
        
        <el-menu-item index="/workflows">
          <el-icon><Connection /></el-icon>
          <template #title>流程中心</template>
        </el-menu-item>
        
        <el-menu-item index="/analytics">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>
        
        <el-menu-item index="/knowledge">
          <el-icon><Files /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>

        <el-menu-item index="/my-apps">
          <el-icon><FolderOpened /></el-icon>
          <template #title>应用搭建</template>
        </el-menu-item>

        <!-- AI 能力中心 — 统一入口 -->
        <el-menu-item index="/ai-center">
          <el-icon><Cpu /></el-icon>
          <template #title>AI 能力中心</template>
        </el-menu-item>

        <!-- 插件生态 -->
        <el-sub-menu v-if="userStore.isAdmin" index="/plugins-group">
          <template #title>
            <el-icon><Box /></el-icon>
            <span>插件生态</span>
          </template>
          <el-menu-item index="/plugins">插件管理</el-menu-item>
          <el-menu-item index="/plugin-market">插件市场</el-menu-item>
        </el-sub-menu>

        <!-- 系统管理 -->
        <el-sub-menu v-if="userStore.isAdmin" index="/system-group">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/data-modeling">数据建模</el-menu-item>
          <el-menu-item index="/migration">数据迁移</el-menu-item>
          <el-menu-item index="/doc-converter">文档转换</el-menu-item>
          <el-menu-item index="/users">用户管理</el-menu-item>
          <el-menu-item index="/settings">系统设置</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>个人信息</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <!-- 顶部导航 -->
      <el-header>
        <div class="header-left">
          <el-button 
            text 
            @click="isCollapsed = !isCollapsed"
          >
            <el-icon size="20">
              <Fold v-if="!isCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
        </div>
        
        <div class="header-right">
          <el-input
            v-model="globalSearch"
            placeholder="全局搜索..."
            prefix-icon="Search"
            style="width: 200px; margin-right: 16px;"
          />
          
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ userStore.userInfo?.full_name }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="workspace">我的工作区</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../common/store/user'
import { ElMessageBox } from 'element-plus'
import {
  HomeFilled, Document, Connection, DataAnalysis,
  Files, Setting, MagicStick, Fold, Expand, UserFilled, User, Folder, FolderOpened,
  Cpu, Tools, SetUp, Collection, DataBoard, Upload, Box, ShoppingBag
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapsed = ref(false)
const globalSearch = ref('')

const activeMenu = computed(() => route.path)

function handleUserCommand(command: string) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'workspace') {
    router.push('/my-workspace')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

/* ===== 侧边栏深色主题 ===== */
.el-aside {
  background-color: #1d1e2c;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #ffffff;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #2a2b3d;
  background-color: #1d1e2c;
}

/* --- 菜单容器 --- */
.sidebar-menu {
  border-right: none !important;
  background-color: #1d1e2c !important;
}

/* --- 一级菜单项 --- */
.sidebar-menu :deep(.el-menu-item) {
  color: #b0b3c1 !important;
  background-color: #1d1e2c !important;
  border-bottom: 1px solid transparent;
}
.sidebar-menu :deep(.el-menu-item:hover) {
  color: #ffffff !important;
  background-color: #2a2b3d !important;
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #5b9cf5 !important;
  background-color: #252636 !important;
  border-left: 3px solid #5b9cf5;
}

/* --- 子菜单标题 --- */
.sidebar-menu :deep(.el-sub-menu__title) {
  color: #b0b3c1 !important;
  background-color: #1d1e2c !important;
}
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  color: #ffffff !important;
  background-color: #2a2b3d !important;
}

/* --- 子菜单展开后的子项 --- */
.sidebar-menu :deep(.el-menu--inline) {
  background-color: #151622 !important;
}
.sidebar-menu :deep(.el-menu--inline .el-menu-item) {
  background-color: #151622 !important;
  padding-left: 56px !important;
}
.sidebar-menu :deep(.el-menu--inline .el-menu-item:hover) {
  background-color: #2a2b3d !important;
}

/* --- 折叠状态 --- */
.sidebar-menu.el-menu--collapse :deep(.el-sub-menu__title) {
  text-align: center;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

/* --- 顶部栏 --- */
.el-header {
  background: var(--el-bg-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  color: var(--el-text-color-primary);
}

/* --- 主内容区 --- */
.el-main {
  background: #f5f7fa;
  padding: 16px;
}
</style>
