<template>
  <div class="mobile-register">
    <div class="register-header">
      <div class="logo">K</div>
      <h1>注册 Kflower</h1>
      <p>企业智能管理低代码平台</p>
    </div>

    <div class="register-form">
      <el-form :model="form" @submit.prevent="handleRegister">
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
            v-model="form.email"
            placeholder="邮箱"
            size="large"
            prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.full_name"
            placeholder="姓名"
            size="large"
            prefix-icon="UserFilled"
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
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-link">
        已有账户？<el-link type="primary" @click="$router.push('/app/login')">立即登录</el-link>
      </div>
    </div>

    <div class="register-footer">
      <p>© 2024 Kflower. All Rights Reserved.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = ref({
  username: '',
  email: '',
  full_name: '',
  password: ''
})

const handleRegister = async () => {
  if (!form.value.username || !form.value.email || !form.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }

  // 简单验证邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(form.value.email)) {
    ElMessage.warning('请输入正确的邮箱格式')
    return
  }

  loading.value = true

  try {
    const success = await userStore.register(form.value)
    if (success) {
      router.push('/app/login')
    }
  } catch (e) {
    ElMessage.error('网络错误，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mobile-register {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 20px;
  box-sizing: border-box;
}

.register-header {
  text-align: center;
  color: white;
  margin-bottom: 32px;
}

.logo {
  width: 70px;
  height: 70px;
  background: white;
  color: #667eea;
  font-size: 36px;
  font-weight: bold;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.register-header h1 {
  font-size: 24px;
  margin: 0;
}

.register-header p {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 6px;
}

.register-form {
  background: white;
  border-radius: 16px;
  padding: 24px 20px;
}

.register-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
}

.register-form :deep(.el-button) {
  margin-top: 8px;
  height: 44px;
  font-size: 16px;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
}

.register-footer {
  text-align: center;
  color: white;
  opacity: 0.7;
  font-size: 12px;
  margin-top: 40px;
}
</style>
