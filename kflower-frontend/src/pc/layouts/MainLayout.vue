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
          <template #title>首页</template>
        </el-menu-item>
        
        <el-menu-item index="/templates">
          <el-icon><Document /></el-icon>
          <template #title>模板设计</template>
        </el-menu-item>
        
        <el-menu-item index="/workflows">
          <el-icon><Connection /></el-icon>
          <template #title>流程审批</template>
        </el-menu-item>
        
        <el-menu-item index="/analytics">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>决策分析</template>
        </el-menu-item>
        
        <el-menu-item index="/knowledge">
          <el-icon><Files /></el-icon>
          <template #title>知识库</template>
        </el-menu-item>
        
        <el-menu-item index="/ai-digital-base">
          <el-icon><Cpu /></el-icon>
          <template #title>AI数字底座</template>
        </el-menu-item>
        
        <el-menu-item index="/ai-agent-engine">
          <el-icon><User /></el-icon>
          <template #title>AI智能体引擎</template>
        </el-menu-item>
        
        <el-menu-item index="/ai-gateway">
          <el-icon><Connection /></el-icon>
          <template #title>AI网关</template>
        </el-menu-item>
        
        <el-menu-item index="/ai-tools">
          <el-icon><Tools /></el-icon>
          <template #title>工具集</template>
        </el-menu-item>
        
        <el-menu-item index="/agent-orchestrator">
          <el-icon><SetUp /></el-icon>
          <template #title>智能体编排器</template>
        </el-menu-item>
        
        <el-menu-item index="/memory-management">
          <el-icon><Collection /></el-icon>
          <template #title>记忆管理</template>
        </el-menu-item>
        
        <el-menu-item index="/data-integration">
          <el-icon><DataBoard /></el-icon>
          <template #title>数据集成</template>
        </el-menu-item>
        
        <el-menu-item index="/migration">
          <el-icon><Upload /></el-icon>
          <template #title>数据库迁移</template>
        </el-menu-item>
        
        <el-menu-item index="/my-workspace">
          <el-icon><Folder /></el-icon>
          <template #title>我的工作区</template>
        </el-menu-item>
        
        <el-menu-item index="/my-apps">
          <el-icon><FolderOpened /></el-icon>
          <template #title>我的应用</template>
        </el-menu-item>
        
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>个人信息</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/users">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>

        <el-menu-item v-if="userStore.isAdmin" index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
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
  Cpu, Tools, SetUp, Collection, DataBoard, Upload
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

.el-aside {
  background: #304156;
  transition: width 0.3s;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #3d4a5c;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
}

.sidebar-menu .el-menu-item:hover {
  color: #ffffff;
  background-color: #263445;
}

.sidebar-menu .el-menu-item.is-active {
  color: #409eff;
  background-color: #263445;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.el-header {
  background: white;
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
  color: #333;
}

.el-main {
  background: #f5f7fa;
  padding: 16px;
}
</style>
