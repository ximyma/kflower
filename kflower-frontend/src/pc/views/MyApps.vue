<template>
  <div class="apps-container">
    <div class="page-header">
      <h2>我的应用</h2>
      <div class="header-actions">
        <el-button @click="goToAIDesigner">
          <el-icon><MagicStick /></el-icon> AI设计助手
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon> 新建应用
        </el-button>
      </div>
    </div>

    <!-- 应用列表 -->
    <div class="apps-grid">
      <el-card v-for="app in apps" :key="app.id" class="app-card" shadow="hover">
        <div class="app-icon" :style="{ background: getAppColor(app.theme) }">
          <el-icon :size="32"><component :is="app.icon || 'Document'" /></el-icon>
        </div>
        <h3>{{ app.name }}</h3>
        <p class="app-desc">{{ app.description || '暂无描述' }}</p>
        <div class="app-meta">
          <el-tag v-if="app.is_published" type="success" size="small">已发布</el-tag>
          <el-tag v-else type="info" size="small">草稿</el-tag>
          <span class="create-time">{{ formatDate(app.created_at) }}</span>
        </div>
        <div class="app-actions">
          <div class="action-row">
            <el-button size="small" type="primary" @click="openApp(app)">
              <el-icon><View /></el-icon> 进入
            </el-button>
            <el-button size="small" @click="designApp(app)">
              <el-icon><SetUp /></el-icon> 设计
            </el-button>
            <el-button size="small" @click="editAppInfo(app)">
              <el-icon><Edit /></el-icon> 信息
            </el-button>
          </div>
          <div class="action-row">
            <el-button v-if="!app.is_published" size="small" type="success" @click="publishApp(app)">
              <el-icon><Promotion /></el-icon> 发布
            </el-button>
            <el-button v-if="app.is_published" size="small" type="warning" @click="unpublishApp(app)">
              <el-icon><ArrowDown /></el-icon> 撤回
            </el-button>
            <el-button v-if="app.is_published" size="small" @click="publishApp(app)">
              <el-icon><RefreshRight /></el-icon> 重新发布
            </el-button>
            <el-button size="small" type="danger" @click="deleteApp(app)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="apps.length === 0" description="还没有创建应用，点击新建应用开始" />
    </div>

    <!-- 新建/编辑应用对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editingApp ? '编辑应用' : '新建应用'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="应用名称" required>
          <el-input v-model="form.name" placeholder="如：进销存系统" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="图标">
          <el-select v-model="form.icon" placeholder="选择图标">
            <el-option label="文档" value="Document" />
            <el-option label="文件夹" value="Folder" />
            <el-option label="购物车" value="ShoppingCart" />
            <el-option label="客户" value="User" />
            <el-option label="商品" value="Goods" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-radio-group v-model="form.theme">
            <el-radio label="light">浅色</el-radio>
            <el-radio label="dark">深色</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveApp" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Promotion, Delete, SetUp, MagicStick, ArrowDown, RefreshRight } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'

const router = useRouter()
const apps = ref<any[]>([])
const showCreateDialog = ref(false)
const editingApp = ref<any>(null)
const saving = ref(false)

const form = ref({
  name: '',
  description: '',
  icon: 'Document',
  theme: 'light'
})

// 获取应用列表
async function loadApps() {
  try {
    const res: any = await appAPI.list()
    apps.value = res
  } catch (e: any) {
    ElMessage.error('加载应用列表失败：' + (e.message || ''))
  }
}

// 打开应用
function openApp(app: any) {
  if (!app.is_published) {
    ElMessage.warning('请先发布应用')
    return
  }
  router.push(`/app/${app.id}`)
}

// 编辑应用信息
function editAppInfo(app: any) {
  editingApp.value = app
  form.value = {
    name: app.name,
    description: app.description || '',
    icon: app.icon || 'Document',
    theme: app.theme || 'light'
  }
  showCreateDialog.value = true
}

// 进入应用设计器
function designApp(app: any) {
  router.push(`/app-designer/${app.id}`)
}

// 进入AI设计助手
function goToAIDesigner() {
  router.push('/ai-app-designer?mode=designer')
}

// 保存应用
async function saveApp() {
  if (!form.value.name) {
    ElMessage.warning('请输入应用名称')
    return
  }

  saving.value = true
  try {
    if (editingApp.value) {
      await appAPI.update(editingApp.value.id, form.value)
      // 如果应用已发布，自动重新发布
      if (editingApp.value.is_published) {
        await appAPI.publish(editingApp.value.id)
        ElMessage.success('更新并重新发布成功')
      } else {
        ElMessage.success('更新成功（草稿状态）')
      }
    } else {
      const res = await appAPI.create(form.value)
      const newId = res.id || res.data?.id
      if (newId) {
        await appAPI.publish(newId)
        ElMessage.success('创建并发布成功')
      } else {
        ElMessage.success('创建成功')
      }
    }
    showCreateDialog.value = false
    editingApp.value = null
    form.value = { name: '', description: '', icon: 'Document', theme: 'light' }
    await loadApps()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    saving.value = false
  }
}

// 发布应用
async function publishApp(app: any) {
  try {
    await appAPI.publish(app.id)
    ElMessage.success('发布成功')
    await loadApps()
  } catch (e: any) {
    ElMessage.error('发布失败：' + (e.message || ''))
  }
}

// 撤回应用
async function unpublishApp(app: any) {
  try {
    await ElMessageBox.confirm(`确定撤回应用「${app.name}」吗？撤回后用户将无法访问。`, '确认撤回', {
      type: 'warning'
    })
    await appAPI.unpublish(app.id)
    ElMessage.success('已撤回')
    await loadApps()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('撤回失败：' + (e.message || ''))
    }
  }
}

// 删除应用
async function deleteApp(app: any) {
  try {
    await ElMessageBox.confirm(`确定删除应用「${app.name}」吗？`, '确认删除', {
      type: 'warning'
    })
    await appAPI.delete(app.id)
    ElMessage.success('删除成功')
    await loadApps()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.message || ''))
    }
  }
}

// 工具函数
function getAppColor(theme: string) {
  return theme === 'dark' ? '#409eff' : '#67c23a'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadApps()
})
</script>

<style scoped lang="scss">
.apps-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  h2 {
    margin: 0;
    font-size: 24px;
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.app-card {
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
  cursor: pointer;

  &:hover {
    transform: translateY(-4px);
  }

  .app-icon {
    width: 80px;
    height: 80px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    color: white;
  }

  h3 {
    margin: 0 0 8px;
    font-size: 18px;
  }

  .app-desc {
    color: var(--el-text-color-secondary);
    font-size: 14px;
    margin: 0 0 12px;
    min-height: 40px;
  }

  .app-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .create-time {
      font-size: 12px;
      color: #c0c4cc;
    }
  }

  .app-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: center;

    .action-row {
      display: flex;
      gap: 8px;
      justify-content: center;
      flex-wrap: wrap;
    }
  }
}
</style>
