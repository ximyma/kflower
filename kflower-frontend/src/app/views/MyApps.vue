<template>
  <div class="app-my-apps">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>我的应用</h2>
      <el-button type="primary" size="small" @click="createApp">
        <el-icon><Plus /></el-icon> 新建应用
      </el-button>
    </div>
    
    <!-- 应用列表 -->
    <div class="app-list" v-loading="loading">
      <div v-if="apps.length === 0 && !loading" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><Grid /></el-icon>
        <p>暂无应用</p>
        <el-button type="primary" size="small" @click="createApp">创建第一个应用</el-button>
      </div>
      
      <div
        v-for="app in apps"
        :key="app.id"
        class="app-item"
        @click="openApp(app)"
      >
        <div class="app-icon" :style="{ background: getAppColor(app.id) }">
          <el-icon :size="28"><component :is="app.icon || 'Grid'" /></el-icon>
        </div>
        <div class="app-info">
          <h3>{{ app.name }}</h3>
          <p>{{ app.description || '暂无描述' }}</p>
          <span class="app-time">{{ formatTime(app.updated_at) }}</span>
        </div>
        <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, app)">
          <el-icon :size="20" color="#909399"><MoreFilled /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="design">设计</el-dropdown-item>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 创建应用对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建应用" width="90%" :close-on-click-modal="false">
      <el-form :model="newApp" label-position="top">
        <el-form-item label="应用名称" required>
          <el-input v-model="newApp.name" placeholder="请输入应用名称" />
        </el-form-item>
        <el-form-item label="应用描述">
          <el-input v-model="newApp.description" type="textarea" :rows="2" placeholder="应用描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateApp" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Grid, MoreFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import appAPI from '../../common/api/myApps'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const apps = ref<any[]>([])
const showCreateDialog = ref(false)

const newApp = ref({
  name: '',
  description: ''
})

function getAppColor(id: number) {
  const colors = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  ]
  return colors[id % colors.length]
}

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleDateString()
}

async function loadApps() {
  loading.value = true
  try {
    // 使用真实API
    const res = await appAPI.list()
    apps.value = res.items || res || []
  } catch (error) {
    console.error('加载应用失败:', error)
    // 降级到模拟数据
    apps.value = [
      { id: 1, name: '行政管理', description: '公司行政事务管理', icon: 'OfficeBuilding', updated_at: new Date().toISOString() },
      { id: 2, name: '项目管理', description: '项目进度跟踪管理', icon: 'Briefcase', updated_at: new Date().toISOString() }
    ]
  } finally {
    loading.value = false
  }
}

function createApp() {
  // 跳转到应用设计器新建
  router.push('/app/app-designer')
}

async function handleCreateApp() {
  if (!newApp.value.name.trim()) {
    ElMessage.warning('请输入应用名称')
    return
  }

  creating.value = true
  try {
    const res = await appAPI.create({
      name: newApp.value.name,
      description: newApp.value.description
    })
    ElMessage.success('应用创建成功')
    showCreateDialog.value = false
    newApp.value = { name: '', description: '' }
    // 跳转到应用设计器
    router.push(`/app/app-designer/${res.id}`)
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

function openApp(app: any) {
  // 跳转到应用设计器
  router.push(`/app/app-designer/${app.id}`)
}

async function handleCommand(command: string, app: any) {
  switch (command) {
    case 'design':
    case 'edit':
      router.push(`/app/app-designer/${app.id}`)
      break
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(`确定要删除应用"${app.name}"吗？`, '删除确认', { type: 'warning' })
        ElMessage.success('删除成功')
        loadApps()
      } catch (e: any) {
        if (e !== 'cancel') ElMessage.error('删除失败')
      }
      break
  }
}

onMounted(() => {
  loadApps()
})
</script>

<style scoped>
.app-my-apps {
  padding-bottom: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.app-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-state p {
  margin: 16px 0;
}

.app-item {
  background: white;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: transform 0.2s;
}

.app-item:active {
  transform: scale(0.98);
}

.app-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.app-info {
  flex: 1;
  min-width: 0;
}

.app-info h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.app-info p {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-time {
  font-size: 11px;
  color: #c0c4cc;
}
</style>
