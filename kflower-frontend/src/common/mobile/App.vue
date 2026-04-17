<template>
  <div class="mobile-app">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  // 设置移动端视口
  document.documentElement.classList.add('mobile-mode')
  document.body.classList.add('mobile-body')
})
</script>

<style>
.mobile-mode {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
}

.mobile-body {
  margin: 0;
  padding: 0;
  background: #f7f8fa;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.mobile-app {
  min-height: 100vh;
}
</style>