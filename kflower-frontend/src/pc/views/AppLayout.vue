<template>
  <div class="app-layout">
    <!-- 左侧菜单 -->
    <el-aside width="200px" class="app-aside">
      <div class="app-logo">
        <el-icon :size="24"><component :is="appData.icon || 'Document'" /></el-icon>
        <span>{{ appData.name }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <!-- 首页入口 -->
        <el-menu-item :index="`/app/${appId}`">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <!-- 表单菜单项 -->
        <el-menu-item
          v-for="menu in menuTree"
          :key="menu.id"
          :index="`/app/${appId}/form/${menu.template_id}`"
        >
          <el-icon><component :is="menu.icon || 'Document'" /></el-icon>
          <template #title>{{ menu.label }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-main class="app-main">
      <router-view :key="$route.fullPath" :app-id="appId" />
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { HomeFilled } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'

const route = useRoute()
const router = useRouter()

const appId = ref(Number(route.params.appId))
const appData = ref<any>({ name: '应用', icon: 'Document' })
const menuTree = ref<any[]>([])
const activeMenu = computed(() => route.path)

// 加载应用数据
async function loadAppData() {
  try {
    const res: any = await appAPI.get(appId.value)
    appData.value = res
  } catch (e: any) {
    ElMessage.error('加载应用失败：' + (e.message || ''))
    router.push('/my-apps')
  }
}

// 加载菜单树
async function loadMenuTree() {
  try {
    const res: any = await appAPI.getMenuTree(appId.value)
    menuTree.value = res
  } catch (e: any) {
    ElMessage.error('加载菜单失败：' + (e.message || ''))
  }
}

// 监听路由变化，切换应用时重新加载
watch(() => route.params.appId, (newAppId) => {
  if (newAppId) {
    appId.value = Number(newAppId)
    loadAppData()
    loadMenuTree()
  }
})

onMounted(() => {
  loadAppData()
  loadMenuTree()
})
</script>

<style scoped lang="scss">
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.app-aside {
  background-color: #304156;
  color: white;
  overflow-y: auto;

  .app-logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 16px;
    font-weight: bold;
    background-color: #263445;
    padding: 0 20px;
  }
}

.app-main {
  flex: 1;
  background-color: #f0f2f5;
  overflow-y: auto;
}
</style>
