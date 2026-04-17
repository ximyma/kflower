<template>
  <div class="mobile-login">
    <div class="login-header">
      <div class="logo">K</div>
      <h1>Kflower</h1>
      <p>企业智能管理低代码平台</p>
    </div>
    
    <van-form @submit="handleLogin" class="login-form">
      <van-cell-group inset>
        <van-field
          v-model="form.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        />
        <van-field
          v-model="form.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        />
      </van-cell-group>
      
      <div class="login-btn">
        <van-button type="primary" block round native-type="submit" :loading="loading">
          登录
        </van-button>
      </div>
    </van-form>
    
    <div class="login-footer">
      <p>© 2024 Kflower. All Rights Reserved.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  loading.value = true
  showLoadingToast({ message: '登录中...', forbidClick: true })
  
  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    
    if (res.ok) {
      const data = await res.json()
      localStorage.setItem('kflower_token', data.access_token)
      showToast('登录成功')
      router.push('/')
    } else {
      const err = await res.json()
      showToast(err.detail || '登录失败')
    }
  } catch (e) {
    showToast('网络错误，请重试')
  } finally {
    loading.value = false
    closeToast()
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
  padding: 20px;
}

.login-btn {
  margin-top: 20px;
}

.login-footer {
  text-align: center;
  color: white;
  opacity: 0.7;
  font-size: 12px;
  margin-top: 40px;
}
</style>