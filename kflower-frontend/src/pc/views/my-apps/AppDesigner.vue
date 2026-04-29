<template>
  <div class="app-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h2>{{ appData.name || '未命名应用' }}</h2>
        <el-tag v-if="appData.is_published" type="success">已发布</el-tag>
        <el-tag v-else type="info">草稿</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="saveApp" :loading="saving">
          <el-icon><Check /></el-icon> 保存
        </el-button>
        <el-button type="success" @click="publishApp" v-if="!appData.is_published">
          <el-icon><Promotion /></el-icon> 发布
        </el-button>
        <el-button type="warning" @click="unpublishApp" v-if="appData.is_published">
          <el-icon><RefreshRight /></el-icon> 撤回发布
        </el-button>
      </div>
    </div>

    <!-- 标签页导航 -->
    <el-tabs v-model="activeTab" class="designer-tabs" type="border-card">
      <!-- 菜单设计 -->
      <el-tab-pane label="菜单设计" name="menus">
        <MenuDesigner 
          :app-id="appId" 
          :app-data="appData"
          @update:app-data="appData = $event"
        />
      </el-tab-pane>
      
      <!-- 表单关系 -->
      <el-tab-pane label="表单关系" name="relations">
        <RelationDesigner :app-id="appId" />
      </el-tab-pane>
      
      <!-- 业务插件 -->
      <el-tab-pane label="业务插件" name="plugins">
        <PluginEditor :app-id="appId" />
      </el-tab-pane>

      <!-- 系统插件（新版） -->
      <el-tab-pane label="系统插件" name="system-plugins">
        <AppPluginManager :app-id="appId" />
      </el-tab-pane>
      
      <!-- 仪表盘 -->
      <el-tab-pane label="仪表盘" name="dashboard">
        <DashboardDesigner :app-id="appId" />
      </el-tab-pane>
      
      <!-- 权限配置 -->
      <el-tab-pane label="权限配置" name="permissions">
        <PermissionConfig :app-id="appId" />
      </el-tab-pane>
      
      <!-- 知识库 -->
      <el-tab-pane label="知识库" name="knowledge">
        <KnowledgeBaseConfig :app-id="appId" />
      </el-tab-pane>
      
      <!-- 知识搜索 -->
      <el-tab-pane label="知识搜索" name="knowledge-search">
        <KnowledgeSearch :app-id="appId" />
      </el-tab-pane>
      
      <!-- 审计日志 -->
      <el-tab-pane label="审计日志" name="audit">
        <AuditLogViewer :app-id="appId" />
      </el-tab-pane>
      
      <!-- AI设计助手 -->
      <el-tab-pane label="AI设计助手" name="ai-design">
        <AIDesigner :app-id="appId" />
      </el-tab-pane>
      
      <!-- 版本管理 -->
      <el-tab-pane label="版本管理" name="versions">
        <VersionManager :app-id="appId" @restored="loadAppData" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Check, Promotion, RefreshRight
} from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'

// 导入子组件
import MenuDesigner from './components/MenuDesigner.vue'
import RelationDesigner from './components/RelationDesigner.vue'
import PluginEditor from './components/PluginEditor.vue'
import DashboardDesigner from './components/DashboardDesigner.vue'
import PermissionConfig from './components/PermissionConfig.vue'
import AuditLogViewer from './components/AuditLogViewer.vue'
import AIDesigner from './components/AIDesigner.vue'
import KnowledgeBaseConfig from './components/KnowledgeBaseConfig.vue'
import KnowledgeSearch from './components/KnowledgeSearch.vue'
import VersionManager from './components/VersionManager.vue'
import AppPluginManager from '../../components/AppPluginManager.vue'

const route = useRoute()
const router = useRouter()

const appId = Number(route.params.appId)
const activeTab = ref('menus')
const appData = ref<any>({
  name: '',
  description: '',
  icon: 'Document',
  theme: 'light',
  is_published: false
})
const saving = ref(false)

// 加载应用数据
async function loadAppData() {
  try {
    const res: any = await appAPI.get(appId)
    appData.value = res
  } catch (e: any) {
    // API 失败时显示错误，但不跳转，让用户可以继续编辑
    console.error('加载应用失败:', e)
    ElMessage.error('加载应用详情失败：' + (e.message || e.response?.data?.detail || '请检查网络或刷新重试'))
    // 不再跳转到 my-apps，允许用户继续在设计界面
  }
}

// 保存应用
async function saveApp() {
  if (!appData.value.name) {
    ElMessage.warning('请输入应用名称')
    return
  }

  saving.value = true
  try {
    await appAPI.update(appId, appData.value)
    ElMessage.success('保存成功')
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    saving.value = false
  }
}

// 发布应用
async function publishApp() {
  try {
    await appAPI.publish(appId)
    ElMessage.success('发布成功')
    appData.value.is_published = true
  } catch (e: any) {
    ElMessage.error('发布失败：' + (e.message || ''))
  }
}

// 撤回发布
async function unpublishApp() {
  try {
    await ElMessageBox.confirm('确定撤回发布吗？', '确认撤回', {
      type: 'warning'
    })
    await appAPI.update(appId, { is_published: false })
    ElMessage.success('已撤回发布')
    appData.value.is_published = false
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('撤回失败：' + (e.message || ''))
    }
  }
}

// 返回
function goBack() {
  router.push('/my-apps')
}

onMounted(() => {
  loadAppData()
})
</script>

<style scoped lang="scss">
.app-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.designer-header {
  height: 60px;
  padding: 0 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h2 {
      margin: 0;
      font-size: 18px;
      color: var(--el-text-color-primary);
    }
  }

  .header-right {
    display: flex;
    gap: 8px;
  }
}

.designer-tabs {
  flex: 1;
  overflow: hidden;
  
  :deep(.el-tabs__content) {
    height: calc(100% - 55px);
    overflow: auto;
  }
  
  :deep(.el-tab-pane) {
    height: 100%;
  }
}
</style>
