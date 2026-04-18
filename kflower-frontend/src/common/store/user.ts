/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { authAPI } from '../api'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_superuser: boolean
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('kflower_token'))
  const userInfo = ref<User | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.is_superuser === true)

  async function autoLogin() {
    if (!token.value) return false
    try {
      const res: any = await authAPI.getUserInfo()
      userInfo.value = res
      return true
    } catch (e: any) {
      // 只有 401 (token无效/过期) 才清除登录状态
      // 500 等服务器错误保留 token，用户仍可使用已有权限
      const status = e?.response?.status
      if (status === 401) {
        logout()
      }
      return false
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const res: any = await authAPI.login({ username, password })
      token.value = res.access_token
      userInfo.value = res.user
      localStorage.setItem('kflower_token', res.access_token)
      return true
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '登录失败')
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(data: { username: string; email: string; password: string; full_name: string }) {
    loading.value = true
    try {
      await authAPI.register(data)
      ElMessage.success('注册成功，请登录')
      return true
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '注册失败')
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    userInfo.value = null
    localStorage.removeItem('kflower_token')
  }

  return {
    token,
    userInfo,
    loading,
    isLoggedIn,
    isAdmin,
    autoLogin,
    login,
    register,
    logout
  }
})
