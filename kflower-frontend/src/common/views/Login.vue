<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">Kflower</h1>
      <p class="subtitle">企业智能管理低代码平台</p>

      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-link">
        没有账户？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessage } from 'element-plus'
import { checkDevice } from '../utils/device'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const form = ref({ username: 'admin', password: '123456' })

onMounted(() => {
  // 如果是移动设备，自动跳转到移动端登录页
  if (checkDevice()) {
    router.replace('/app/login')
  }
})

const handleLogin = async () => {
  loading.value = true
  try {
    await userStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    // 检查redirect参数或跳转到首页
    const redirect = route.query.redirect as string
    if (redirect) {
      router.push(redirect)
    } else {
      router.push('/home')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  width: 360px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
.title {
  text-align: center;
  color: #667eea;
  margin: 0 0 8px;
}
.subtitle {
  text-align: center;
  color: #666;
  margin: 0 0 32px;
}
.tips {
  text-align: center;
  color: #999;
  font-size: 12px;
  margin-top: 16px;
}
.register-link {
  text-align: center;
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}
.register-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}
.register-link a:hover {
  text-decoration: underline;
}
</style>
