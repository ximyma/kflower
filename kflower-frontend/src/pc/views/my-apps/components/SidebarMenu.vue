<template>
  <div class="sidebar-menu">
    <!-- 递归渲染菜单 -->
    <template v-for="menu in menus" :key="menu.id">
      <!-- 有子菜单：使用 el-sub-menu 渲染折叠菜单 -->
      <el-sub-menu
        v-if="menu.children && menu.children.length > 0"
        :index="String(menu.id)"
      >
        <template #title>
          <el-icon><component :is="menu.icon || 'Folder'" /></el-icon>
          <span>{{ menu.label }}</span>
        </template>
        <!-- 递归渲染子菜单 -->
        <sidebar-menu :menus="menu.children" :app-id="appId" />
      </el-sub-menu>

      <!-- 无子菜单：使用 el-menu-item 渲染普通菜单项 -->
      <el-menu-item
        v-else
        :index="getMenuIndex(menu)"
      >
        <el-icon><component :is="menu.icon || 'Document'" /></el-icon>
        <template #title>{{ menu.label }}</template>
      </el-menu-item>
    </template>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck

const props = defineProps<{
  menus: any[]
  appId: number
}>()

// 生成菜单项的索引（用于路由跳转）
function getMenuIndex(menu: any) {
  if (menu.template_id) {
    return `/app/${props.appId}/form/${menu.template_id}`
  }
  // 如果没有关联模板，使用菜单ID作为索引
  return `/app/${props.appId}/menu/${menu.id}`
}
</script>

<style scoped lang="scss">
.sidebar-menu {
  // 确保子菜单缩进正确
  :deep(.el-sub-menu .el-menu-item) {
    padding-left: 40px !important;
  }
}
</style>
