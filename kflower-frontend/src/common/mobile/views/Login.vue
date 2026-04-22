<template>
  <div class="mobile-login">
    <div class="login-header">
      <div class="logo">K</div>
      <h1>Kflower</h1>
      <p>企业智能管理低代码平台</p>
    </div>

    <div class="login-form">
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-link">
        没有账户？<el-link type="primary" @click="$router.push('/app/register')">立即注册</el-link>
      </div>
    </div>

    <div class="login-footer">
      <p>© 2024 Kflower. All Rights Reserved.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true

  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })

    if (res.ok) {
      const data = await res.json()
      // 保存 token
      localStorage.setItem('access_token', data.access_token)
      // 更新 userStore 状态
      userStore.token = data.access_token
      // 获取用户信息
      try {
        await userStore.autoLogin()
      } catch (e) {
        console.warn('获取用户信息失败，将继续跳转')
      }
      ElMessage.success('登录成功')
      // 使用 replace 而不是 push，避免后退回到登录页
      // 添加延迟确保响应式数据更新
      setTimeout(() => {
        router.replace('/app/home')
      }, 100)
    } else {
      const err = await res.json()
      ElMessage.error(err.detail || '登录失败')
    }
  } catch (e) {
    ElMessage.error('网络错误，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mobile-login {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.login-header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
}

.logo {
  width: 80px;
  height: 80px;
  background: white;
  color: #667eea;
  font-size: 40px;
  font-weight: bold;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.login-header h1 {
  font-size: 28px;
  margin: 0;
}

.login-header p {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 8px;
}

.login-form {
  background: white;
  border-radius: 16px;
  padding: 24px 20px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
}

.login-form :deep(.el-button) {
  margin-top: 8px;
  height: 44px;
  font-size: 16px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
}

.login-footer {
  text-align: center;
  color: white;
  opacity: 0.7;
  font-size: 12px;
  margin-top: 40px;
}
</style>
