<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './common/store/user'
import AIChatButton from './common/components/AIChatButton.vue'
import { checkDevice } from './common/utils/device'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isMobile = checkDevice()

onMounted(async () => {
  // 仅在 token 存在但 userInfo 为空时才尝试自动登录
  // 避免刚登录成功后又重复请求 /auth/me
  if (userStore.isLoggedIn && !userStore.userInfo) {
    const ok = await userStore.autoLogin()
    if (ok) {
      router.push('/home')
    }
  } else if (userStore.isLoggedIn) {
    router.push('/home')
  }
})

// PC端才显示AI聊天按钮
const showAIButton = computed(() => userStore.isLoggedIn && !isMobile)
</script>

<template>
  <div class="app-container">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <AIChatButton v-if="showAIButton" />
  </div>
</template>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
  background: var(--bg-color);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
