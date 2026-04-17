<template>
  <div class="app-profile">
    <!-- 用户信息卡片 -->
    <div class="profile-header">
      <el-avatar :size="64" :icon="UserFilled" />
      <h3>{{ userStore.userInfo?.full_name || '用户' }}</h3>
      <p>{{ userStore.userInfo?.email }}</p>
    </div>
    
    <!-- 菜单列表 -->
    <el-card class="menu-card">
      <el-cell-group>
        <el-cell title="个人设置" is-link>
          <template #icon><el-icon><Setting /></el-icon></template>
        </el-cell>
        <el-cell title="AI设置" is-link>
          <template #icon><el-icon><MagicStick /></el-icon></template>
        </el-cell>
        <el-cell title="帮助与反馈" is-link>
          <template #icon><el-icon><QuestionFilled /></el-icon></template>
        </el-cell>
        <el-cell title="关于我们" is-link>
          <template #icon><el-icon><InfoFilled /></el-icon></template>
        </el-cell>
      </el-cell-group>
    </el-card>
    
    <!-- 退出登录 -->
    <el-button type="danger" plain class="logout-btn" @click="handleLogout">
      退出登录
    </el-button>
    
    <div class="version-info">
      Kflower v1.0.0
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { UserFilled, Setting, MagicStick, QuestionFilled, InfoFilled } from '@element-plus/icons-vue'
import { useUserStore } from '../../common/store/user'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    type: 'warning'
  }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}
</script>

<style scoped>
.app-profile {
  padding-bottom: 20px;
}

.profile-header {
  text-align: center;
  padding: 24px;
  background: white;
  border-radius: 12px;
  margin-bottom: 16px;
}

.profile-header h3 {
  margin-top: 12px;
  margin-bottom: 4px;
}

.profile-header p {
  color: #909399;
  font-size: 13px;
}

.menu-card {
  margin-bottom: 16px;
}

.logout-btn {
  width: 100%;
}

.version-info {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 16px;
}
</style>
