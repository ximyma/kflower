<template>
  <div class="app-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h2>{{ appData.name || '未命名应用' }}</h2>
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

    <!-- 顶部 Tab 导航 -->
    <div class="designer-tabs">
      <el-tabs v-model="designerTab" class="app-designer-tabs">
        <el-tab-pane label="菜单设计" name="menu">
          <template #label>
            <span class="tab-label">
              <el-icon><Menu /></el-icon>
              菜单设计
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="表单关系" name="relation">
          <template #label>
            <span class="tab-label">
              <el-icon><Connection /></el-icon>
              表单关系
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="仪表盘" name="dashboard">
          <template #label>
            <span class="tab-label">
              <el-icon><DataBoard /></el-icon>
              仪表盘
            </span>
          </template>
        </el-tab-pane>
        <el-tab-pane label="应用属性" name="app">
          <template #label>
            <span class="tab-label">
              <el-icon><Setting /></el-icon>
              应用属性
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Tab 内容区域 -->
    <div class="designer-body">
      <!-- 菜单设计 Tab -->
      <template v-if="designerTab === 'menu'">
        <!-- 左侧：可用模板列表 -->
        <div class="sidebar-left">
          <div class="sidebar-left-header">
            <h3>可用模板</h3>
            <el-tooltip content="前往模板设计页新建模板" placement="top">
              <el-button
                size="small"
                type="primary"
                plain
                @click="goCreateTemplate"
              >
                <el-icon><Plus /></el-icon> 新建模板
              </el-button>
            </el-tooltip>
          </div>
          <el-input
            v-model="templateSearch"
            placeholder="搜索模板..."
            clearable
            style="margin-bottom: 12px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-scrollbar height="calc(100vh - 280px)">
            <el-card
              v-for="tpl in filteredTemplates"
              :key="tpl.id"
              class="template-card"
              @click="addTemplateToMenu(tpl)"
              style="cursor: pointer; margin-bottom: 12px"
            >
              <div class="template-info">
                <h4>{{ tpl.name }}</h4>
                <p>{{ tpl.description || '暂无描述' }}</p>
                <el-tag size="small" type="success" v-if="tpl.is_published">已发布</el-tag>
                <el-tag size="small" type="info" v-else>草稿</el-tag>
              </div>
            </el-card>
            <el-empty v-if="filteredTemplates.length === 0" description="没有找到模板" />
          </el-scrollbar>
        </div>

        <!-- 中间：菜单树 -->
        <div class="center-canvas">
          <h3>应用菜单</h3>
          <el-button size="small" @click="addRootMenu" style="margin-bottom: 12px">
            <el-icon><Plus /></el-icon> 添加根菜单
          </el-button>

          <el-tree
            :data="menuTree"
            :props="{ label: 'label', children: 'children' }"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="onMenuNodeClick"
            @node-contextmenu="handleNodeContextMenu"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon><component :is="data.icon || 'Document'" /></el-icon>
                <span>{{ node.label }}</span>
                <el-button
                  size="small"
                  text
                  @click.stop="editMenu(data)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button
                  size="small"
                  text
                  type="danger"
                  @click.stop="deleteMenu(data)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </span>
            </template>
          </el-tree>

          <el-empty v-if="menuTree.length === 0" description="还没有菜单，从左侧添加模板或点击添加根菜单">
            <el-button type="primary" @click="addRootMenu">添加第一个菜单</el-button>
          </el-empty>
        </div>

        <!-- 右侧：菜单属性面板 -->
        <div class="sidebar-right">
          <div class="panel-header">
            <h3>{{ selectedMenu ? '菜单属性' : '请选择菜单' }}</h3>
          </div>

          <el-form :model="menuForm" label-width="80px" v-if="selectedMenu">
            <el-form-item label="菜单名称">
              <el-input v-model="menuForm.menu_label" placeholder="菜单显示名称" />
            </el-form-item>
            <el-form-item label="关联模板">
              <el-select v-model="menuForm.template_id" placeholder="选择表单模板">
                <el-option
                  v-for="tpl in publishedTemplates"
                  :key="tpl.id"
                  :label="tpl.name"
                  :value="tpl.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="图标">
              <el-select v-model="menuForm.menu_icon" placeholder="选择图标">
                <el-option label="文档" value="Document" />
                <el-option label="文件夹" value="Folder" />
                <el-option label="客户" value="User" />
                <el-option label="商品" value="Goods" />
              </el-select>
            </el-form-item>
            <el-form-item label="排序">
              <el-input-number v-model="menuForm.menu_order" :min="0" />
            </el-form-item>
            <el-form-item label="可见">
              <el-switch v-model="menuForm.is_visible" />
            </el-form-item>

            <!-- 流程审批配置 -->
            <div class="section-divider">
              <span>流程审批</span>
            </div>
            <el-form-item label="绑定工作流">
              <el-select v-model="menuForm.workflow_id" placeholder="不绑定工作流" clearable>
                <el-option
                  v-for="wf in allWorkflows"
                  :key="wf.id"
                  :label="wf.name"
                  :value="wf.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="触发方式" v-if="menuForm.workflow_id">
              <el-select v-model="menuForm.workflow_trigger" placeholder="选择触发方式">
                <el-option label="手动发起" value="manual" />
                <el-option label="提交后自动发起" value="submit" />
                <el-option label="修改后发起" value="update" />
              </el-select>
            </el-form-item>
            <el-form-item label="自动发起" v-if="menuForm.workflow_id">
              <el-switch v-model="menuForm.workflow_auto_approve" />
              <div style="font-size:12px;color:var(--el-text-color-secondary);margin-top:4px">开启后提交表单时自动触发审批流程</div>
            </el-form-item>
            <el-form-item label="变量映射" v-if="menuForm.workflow_id">
              <div class="field-mapping-list">
                <div v-for="(map, idx) in (menuForm.workflow_node_mapping || [])" :key="idx" class="field-mapping-item">
                  <el-input v-model="map.form_field" placeholder="表单字段" style="width:120px" />
                  <span style="padding:0 8px">→</span>
                  <el-input v-model="map.workflow_var" placeholder="流程变量" style="width:120px" />
                  <el-button size="small" text type="danger" @click="removeMapping(idx)"><el-icon><Delete /></el-icon></el-button>
                </div>
                <el-button size="small" @click="addMapping" :disabled="!menuForm.workflow_id">
                  <el-icon><Plus /></el-icon> 添加映射
                </el-button>
              </div>
            </el-form-item>

            <!-- 保存菜单按钮 -->
            <el-form-item>
              <el-button type="primary" @click="saveMenu" :loading="saving" style="width: 100%">
                保存菜单
              </el-button>
            </el-form-item>
          </el-form>

          <div v-else class="no-selection-hint">
            <el-empty description="从左侧选择菜单查看属性" :image-size="60" />
          </div>
        </div>
      </template>

      <!-- 表单关系 Tab -->
      <template v-else-if="designerTab === 'relation'">
        <div class="placeholder-content">
          <el-empty description="表单关系功能开发中..." :image-size="80">
            <template #image>
              <el-icon size="80" color="#909399"><Connection /></el-icon>
            </template>
          </el-empty>
        </div>
      </template>

      <!-- 仪表盘 Tab -->
      <template v-else-if="designerTab === 'dashboard'">
        <div class="placeholder-content">
          <el-empty description="仪表盘功能开发中..." :image-size="80">
            <template #image>
              <el-icon size="80" color="#909399"><DataBoard /></el-icon>
            </template>
          </el-empty>
        </div>
      </template>

      <!-- 应用属性 Tab -->
      <template v-else-if="designerTab === 'app'">
        <div class="app-settings-container">
          <el-card class="app-settings-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><InfoFilled /></el-icon> 基本信息</span>
              </div>
            </template>
            <el-form :model="appData" label-width="100px">
              <el-form-item label="应用名称">
                <el-input v-model="appData.name" placeholder="如：客户关系管理系统" />
              </el-form-item>
              <el-form-item label="描述">
                <el-input v-model="appData.description" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item label="图标">
                <el-select v-model="appData.icon" placeholder="选择图标">
                  <el-option label="文档" value="Document" />
                  <el-option label="文件夹" value="Folder" />
                  <el-option label="购物车" value="ShoppingCart" />
                  <el-option label="客户" value="User" />
                  <el-option label="商品" value="Goods" />
                  <el-option label="设置" value="Setting" />
                </el-select>
              </el-form-item>
              <el-form-item label="主题">
                <el-radio-group v-model="appData.theme">
                  <el-radio label="light">浅色</el-radio>
                  <el-radio label="dark">深色</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card class="app-settings-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><Connection /></el-icon> 模块绑定</span>
              </div>
            </template>
            <div class="app-binding-section">
              <!-- 绑定智能体 -->
              <div class="binding-item">
                <div class="binding-header">
                  <el-icon><User /></el-icon>
                  <span>绑定智能体</span>
                </div>
                <div class="binding-desc">选择应用中可用的智能体</div>
                <el-select
                  v-model="appData.bound_agents"
                  multiple
                  placeholder="选择绑定的智能体"
                  style="width: 100%"
                  clearable
                >
                  <el-option
                    v-for="agent in availableAgents"
                    :key="agent.id"
                    :label="agent.name"
                    :value="agent.id"
                  />
                </el-select>
              </div>

              <!-- 绑定知识库 -->
              <div class="binding-item">
                <div class="binding-header">
                  <el-icon><Reading /></el-icon>
                  <span>绑定知识库</span>
                </div>
                <div class="binding-desc">选择应用专属的知识库</div>
                <el-select
                  v-model="appData.knowledge_base_ids"
                  multiple
                  placeholder="选择绑定的知识库"
                  style="width: 100%"
                  clearable
                >
                  <el-option
                    v-for="kb in availableKnowledgeBases"
                    :key="kb.id"
                    :label="kb.name"
                    :value="kb.id"
                  />
                </el-select>
              </div>

              <!-- 绑定工作流 -->
              <div class="binding-item">
                <div class="binding-header">
                  <el-icon><SetUp /></el-icon>
                  <span>绑定工作流</span>
                </div>
                <div class="binding-desc">选择应用可用的工作流</div>
                <el-select
                  v-model="appData.workflow_ids"
                  multiple
                  placeholder="选择绑定的工作流"
                  style="width: 100%"
                  clearable
                >
                  <el-option
                    v-for="wf in allWorkflows"
                    :key="wf.id"
                    :label="wf.name || wf.title"
                    :value="wf.id"
                  />
                </el-select>
              </div>
            </div>
          </el-card>

          <div class="save-section">
            <el-button type="primary" size="large" @click="saveApp" :loading="saving">
              <el-icon><Check /></el-icon> 保存应用设置
            </el-button>
          </div>
        </div>
      </template>
    </div>

    <!-- 新建/编辑菜单对话框 -->
    <el-dialog v-model="showMenuDialog" :title="isEditMenu ? '编辑菜单' : '新建菜单'" width="500px">
      <el-form :model="menuForm" label-width="100px">
        <el-form-item label="菜单名称" required>
          <el-input v-model="menuForm.menu_label" placeholder="菜单显示名称" />
        </el-form-item>
        <el-form-item label="关联模板" required>
          <el-select v-model="menuForm.template_id" placeholder="选择表单模板" style="width: 100%">
            <el-option
              v-for="tpl in publishedTemplates"
              :key="tpl.id"
              :label="tpl.name"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="父菜单">
          <el-select v-model="menuForm.parent_id" placeholder="根菜单" allow-clear style="width: 100%">
            <el-option label="根菜单" :value="null" />
            <el-option
              v-for="menu in flatMenus"
              :key="menu.id"
              :label="menu.menu_label"
              :value="menu.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="图标">
          <el-select v-model="menuForm.menu_icon" placeholder="选择图标">
            <el-option label="文档" value="Document" />
            <el-option label="文件夹" value="Folder" />
            <el-option label="客户" value="User" />
            <el-option label="商品" value="Goods" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="menuForm.menu_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMenuDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMenu" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Check, Promotion, RefreshRight, Search, Plus, Edit, Delete, User, Reading, Connection, Setting,
  Menu, DataBoard, SetUp, InfoFilled
} from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'
import { templateAPI, aiAPI } from '@/common/api/index'

const route = useRoute()
const router = useRouter()

const appId = Number(route.params.appId)
const designerTab = ref('menu')  // 顶部 Tab：menu | relation | dashboard | app
const appConfigTab = ref('basic')

const appData = ref<any>({
  name: '',
  description: '',
  icon: 'Document',
  theme: 'light',
  is_published: false,
  bound_agents: [] as number[],
  knowledge_base_ids: [] as number[],
  workflow_ids: [] as number[],
})
const menuTree = ref<any[]>([])
const allMenus = ref<any[]>([])
const templates = ref<any[]>([])
const allWorkflows = ref<any[]>([])
const availableAgents = ref<any[]>([])
const availableKnowledgeBases = ref<any[]>([])
const publishedTemplates = computed(() => templates.value.filter(t => t.is_published))
const templateSearch = ref('')
const filteredTemplates = computed(() => {
  if (!templateSearch.value) return templates.value
  return templates.value.filter(t => 
    t.name.toLowerCase().includes(templateSearch.value.toLowerCase()) ||
    (t.description && t.description.toLowerCase().includes(templateSearch.value.toLowerCase()))
  )
})
const selectedMenu = ref<any | null>(null)
const menuForm = ref({
  menu_label: '',
  template_id: null as number | null,
  parent_id: null as number | null,
  menu_icon: 'Document',
  menu_order: 0,
  is_visible: true,
  workflow_id: null as number | null,
  workflow_trigger: 'manual',
  workflow_auto_approve: false,
  workflow_node_mapping: [] as Array<{form_field: string; workflow_var: string}>
})
const showMenuDialog = ref(false)
const isEditMenu = ref(false)
const saving = ref(false)

// 加载应用数据
async function loadAppData() {
  try {
    const res: any = await appAPI.get(appId)
    appData.value = res
  } catch (e: any) {
    ElMessage.error('加载应用失败：' + (e.message || ''))
    router.push('/my-apps')
  }
}

// 加载菜单树
async function loadMenuTree() {
  try {
    const res: any = await appAPI.getMenuTree(appId)
    menuTree.value = res
    allMenus.value = flattenMenus(res)
  } catch (e: any) {
    ElMessage.error('加载菜单失败：' + (e.message || ''))
  }
}

// 加载模板列表
async function loadTemplates() {
  try {
    const res: any = await templateAPI.list()
    templates.value = res
  } catch (e: any) {
    ElMessage.error('加载模板失败：' + (e.message || ''))
  }
}

// 加载工作流列表
async function loadWorkflows() {
  try {
    const res: any = await fetch('/api/v1/workflows/', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())
    allWorkflows.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e: any) {
    console.error('加载工作流失败', e)
  }
}

// 添加/移除字段映射
function addMapping() {
  if (!menuForm.value.workflow_node_mapping) {
    menuForm.value.workflow_node_mapping = []
  }
  menuForm.value.workflow_node_mapping.push({ form_field: '', workflow_var: '' })
}

function removeMapping(idx: number) {
  if (menuForm.value.workflow_node_mapping) {
    menuForm.value.workflow_node_mapping.splice(idx, 1)
  }
}

// 扁平化菜单树
function flattenMenus(trees: any[]): any[] {
  let result: any[] = []
  trees.forEach(tree => {
    result.push({ id: tree.id, menu_label: tree.label })
    if (tree.children && tree.children.length > 0) {
      result = result.concat(flattenMenus(tree.children))
    }
  })
  return result
}

const flatMenus = computed(() => flattenMenus(menuTree.value))

// 添加模板到菜单
function addTemplateToMenu(tpl: any) {
  if (!tpl.is_published) {
    ElMessage.warning('请先发布模板')
    return
  }
  menuForm.value = {
    menu_label: tpl.name,
    template_id: tpl.id,
    parent_id: null,
    menu_icon: 'Document',
    menu_order: allMenus.value.length + 1,
    is_visible: true,
    workflow_id: null,
    workflow_trigger: 'manual',
    workflow_auto_approve: false,
    workflow_node_mapping: [],
  }
  isEditMenu.value = false
  showMenuDialog.value = true
}

// 添加根菜单
function addRootMenu() {
  menuForm.value = {
    menu_label: '',
    template_id: null,
    parent_id: null,
    menu_icon: 'Document',
    menu_order: allMenus.value.length + 1,
    is_visible: true,
    workflow_id: null,
    workflow_trigger: 'manual',
    workflow_auto_approve: false,
    workflow_node_mapping: [],
  }
  isEditMenu.value = false
  showMenuDialog.value = true
}

// 编辑菜单
function editMenu(menu: any) {
  selectedMenu.value = menu
  menuForm.value = {
    menu_label: menu.label,
    template_id: menu.template_id,
    parent_id: menu.parent_id || null,
    menu_icon: menu.icon || 'Document',
    menu_order: menu.menu_order || 0,
    is_visible: menu.is_visible !== false,
    workflow_id: menu.workflow_id || null,
    workflow_trigger: menu.workflow_trigger || 'manual',
    workflow_auto_approve: menu.workflow_auto_approve || false,
    workflow_node_mapping: menu.workflow_node_mapping || [],
  }
}

// 删除菜单
async function deleteMenu(menu: any) {
  try {
    await ElMessageBox.confirm(`确定删除菜单「${menu.label}」吗？`, '确认删除', {
      type: 'warning'
    })
    await appAPI.deleteMenu(menu.id)
    ElMessage.success('删除成功')
    await loadMenuTree()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.message || ''))
    }
  }
}

// 保存菜单
async function saveMenu() {
  if (!menuForm.value.menu_label) {
    ElMessage.warning('请输入菜单名称')
    return
  }
  if (!menuForm.value.template_id) {
    ElMessage.warning('请选择关联的模板')
    return
  }

  saving.value = true
  try {
    if (isEditMenu.value && selectedMenu.value) {
      // 更新菜单
      await appAPI.updateMenu(selectedMenu.value.id, menuForm.value)
      ElMessage.success('更新成功')
    } else {
      // 新建菜单
      await appAPI.addMenu(appId, menuForm.value)
      ElMessage.success('添加成功')
    }
    showMenuDialog.value = false
    selectedMenu.value = null
    await loadMenuTree()
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    saving.value = false
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

// 前往新建模板（在新标签页打开，不离开当前设计器）
function goCreateTemplate() {
  const routeData = router.resolve({ name: 'Templates', query: { mode: 'ai' } })
  window.open(routeData.href, '_blank')
}


// 右键菜单（预留）
function handleNodeContextMenu(event: Event, node: any, data: any) {
  event.preventDefault()
  ElMessage.info('右键菜单功能开发中...')
}

// 点击菜单节点 - 切换到菜单设计 Tab 并加载菜单属性
function onMenuNodeClick(data: any) {
  designerTab.value = 'menu'  // 确保在菜单设计 Tab
  editMenu(data)
}

onMounted(() => {
  loadAppData()
  loadMenuTree()
  loadTemplates()
  loadWorkflows()
  loadModuleOptions()
})

// 加载模块绑定选项（智能体、知识库）
async function loadModuleOptions() {
  // 加载智能体列表
  try {
    const agentRes = await aiAPI.getAgentEngineAgents()
    availableAgents.value = agentRes.data || []
  } catch (e) {
    console.error('加载智能体列表失败', e)
  }
  
  // 加载知识库列表
  try {
    const kbRes = await fetch('/api/v1/knowledge-bases/', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json())
    availableKnowledgeBases.value = Array.isArray(kbRes) ? kbRes : (kbRes.data || [])
  } catch (e) {
    console.error('加载知识库列表失败', e)
  }
}
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

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h2 {
      margin: 0;
      font-size: 18px;
    }
  }

  .header-right {
    display: flex;
    gap: 8px;
  }
}

.designer-tabs {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px;

  .app-designer-tabs {
    margin-bottom: 0;

    :deep(.el-tabs__header) {
      margin-bottom: 0;
    }

    :deep(.el-tabs__nav-wrap::after) {
      display: none;
    }
  }

  .tab-label {
    display: flex;
    align-items: center;
    gap: 6px;

    .el-icon {
      font-size: 16px;
    }
  }
}

.designer-body {
  flex: 1;
  display: flex;
  overflow: hidden;

  // 菜单设计 Tab 使用三栏布局
  > template[v-if="designerTab === 'menu'] {
    display: contents;
  }
}

.sidebar-left {
  width: 280px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  padding: 16px;
  display: flex;
  flex-direction: column;

  .sidebar-left-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  h3 {
    margin: 0;
    font-size: 14px;
    color: var(--el-text-color-regular);
  }

  .template-card {
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      transform: translateX(4px);
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    }

    .template-info {
      h4 {
        margin: 0 0 8px;
        font-size: 14px;
      }

      p {
        margin: 0;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

.center-canvas {
  flex: 1;
  background: var(--el-bg-color-page);
  padding: 16px;
  overflow-y: auto;

  h3 {
    margin: 0 0 12px;
    font-size: 14px;
    color: var(--el-text-color-regular);
  }

  .tree-node {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.sidebar-right {
  width: 320px;
  background: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-light);
  padding: 16px;
  overflow-y: auto;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-light);
    padding-bottom: 12px;

    h3 {
      margin: 0;
      font-size: 14px;
      color: var(--el-text-color-regular);
    }
  }

  .section-divider {
    margin: 20px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px dashed var(--el-border-color-lighter);

    span {
      font-size: 13px;
      font-weight: 500;
      color: var(--el-text-color-primary);
    }
  }

  .no-selection-hint {
    padding: 40px 0;
    text-align: center;
  }
}

/* 应用设置页面样式 */
.app-settings-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  max-width: 800px;
  margin: 0 auto;
}

.app-settings-card {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;

    .el-icon {
      color: var(--el-color-primary);
    }
  }
}

/* 占位内容样式 */
.placeholder-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}

/* 应用模块绑定样式 */
.app-binding-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.binding-item {
  padding: 14px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.binding-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--el-text-color-primary);

  .el-icon {
    font-size: 16px;
    color: var(--el-color-primary);
  }
}

.binding-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 10px;
}

.save-section {
  text-align: center;
  margin-top: 24px;
}
</style>
