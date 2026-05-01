<template>
  <div class="mobile-profile">
    <van-nav-bar title="我的" fixed placeholder />
    
    <!-- 用户卡片 -->
    <div class="user-header">
      <van-image round width="80" height="80" :src="userInfo.avatar || defaultAvatar" />
      <div class="user-name">{{ userInfo.full_name || userInfo.username }}</div>
      <div class="user-dept">{{ userInfo.organization_name || '未分配部门' }}</div>
    </div>
    
    <!-- 统计 -->
    <van-grid :column-num="3" class="stat-grid">
      <van-grid-item icon="todo-list-o" text="待办" :badge="stats.pending" />
      <van-grid-item icon="passed" text="已完成" :badge="stats.completed" />
      <van-grid-item icon="clock-o" text="进行中" :badge="stats.running" />
    </van-grid>
    
    <!-- 菜单 -->
    <van-cell-group inset class="menu-group">
      <van-cell title="个人信息" icon="user-o" is-link @click="showEditProfile = true" />
      <van-cell title="我的应用" icon="apps-o" is-link to="/apps" />
      <van-cell title="我的流程" icon="logistics" is-link to="/workflows" />
      <van-cell title="消息通知" icon="bell" is-link :badge="unreadCount" />
      <van-cell title="AI 配置" icon="chat-o" is-link to="/ai-settings" />
    </van-cell-group>
    
    <van-cell-group inset class="menu-group">
      <van-cell title="账号安全" icon="shield-o" is-link />
      <van-cell title="设置" icon="setting-o" is-link to="/settings" />
      <van-cell title="帮助文档" icon="question-o" is-link />
      <van-cell title="关于" icon="info-o" is-link />
    </van-cell-group>
    
    <!-- 退出登录 -->
    <div class="logout-btn">
      <van-button type="danger" block round @click="handleLogout">退出登录</van-button>
    </div>
    
    <!-- 编辑个人信息 -->
    <van-popup v-model:show="showEditProfile" position="bottom" round :style="{ height: '60%' }">
      <van-nav-bar title="编辑个人信息" left-text="取消" @click-left="showEditProfile = false" />
      <van-form @submit="saveProfile">
        <van-cell-group inset>
          <van-field v-model="editForm.full_name" label="姓名" placeholder="请输入姓名" />
          <van-field v-model="editForm.phone" label="手机号" placeholder="请输入手机号" />
          <van-field v-model="editForm.email" label="邮箱" placeholder="请输入邮箱" />
        </van-cell-group>
        <div style="margin: 16px;">
          <van-button type="primary" block round native-type="submit">保存</van-button>
        </div>
      </van-form>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const showEditProfile = ref(false)
const unreadCount = ref('')

const defaultAvatar = 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'

const userInfo = reactive({
  username: '',
  full_name: '',
  avatar: '',
  organization_name: '',
  phone: '',
  email: ''
})

const stats = reactive({
  pending: 0,
  completed: 0,
  running: 0
})

const editForm = reactive({
  full_name: '',
  phone: '',
  email: ''
})

const loadUserInfo = async () => {
  try {
    const res = await fetch('/api/v1/users/me', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      Object.assign(userInfo, data)
      Object.assign(editForm, { full_name: data.full_name, phone: data.phone, email: data.email })
    }
  } catch (e) {
    console.error(e)
  }
}

const loadStats = async () => {
  try {
    const res = await fetch('/api/v1/dashboard/stats', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('access_token') }
    })
    if (res.ok) {
      const data = await res.json()
      Object.assign(stats, data)
    }
  } catch (e) {
    console.error(e)
  }
}

const saveProfile = async () => {
  try {
    const res = await fetch('/api/v1/users/me', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + localStorage.getItem('access_token')
      },
      body: JSON.stringify(editForm)
    })
    if (res.ok) {
      showToast('保存成功')
      Object.assign(userInfo, editForm)
      showEditProfile.value = false
    }
  } catch (e) {
    showToast('保存失败')
  }
}

const handleLogout = async () => {
  try {
    await showConfirmDialog({ title: '提示', message: '确定退出登录吗？' })
    localStorage.removeItem('access_token')
    router.push('/login')
  } catch (e) {
    // 取消
  }
}

onMounted(() => {
  loadUserInfo()
  loadStats()
})
</script>

<style scoped>
.mobile-profile {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 60px;
}

.user-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.user-name {
  font-size: 20px;
  font-weight: bold;
  margin-top: 12px;
}

.user-dept {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

.stat-grid {
  margin: -20px 10px 10px;
  border-radius: 12px;
  overflow: hidden;
}

.menu-group {
  margin: 10px;
}

.logout-btn {
  margin: 20px;
}
</style>