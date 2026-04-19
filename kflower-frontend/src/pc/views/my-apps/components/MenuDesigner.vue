<template>
  <div class="menu-designer">
    <div class="designer-body">
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
          draggable
          @node-drop="handleDrop"
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

      <!-- 右侧：属性面板 -->
      <div class="sidebar-right">
        <h3>属性配置</h3>
        
        <el-form :model="appData" label-width="80px" v-if="selectedMenu === null">
          <h4>应用属性</h4>
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

        <el-form :model="menuForm" label-width="80px" v-if="selectedMenu !== null">
          <h4>菜单属性</h4>
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
        </el-form>
      </div>
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
          <el-select v-model="menuForm.parent_id" placeholder="根菜单" clearable style="width: 100%">
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import appAPI from '@/common/api/myApps'
import { templateAPI } from '@/common/api/index'

const props = defineProps<{
  appId: number
  appData: any
}>()

const emit = defineEmits(['update:app-data'])

const router = useRouter()

const menuTree = ref<any[]>([])
const allMenus = ref<any[]>([])
const templates = ref<any[]>([])
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
  is_visible: true
})
const showMenuDialog = ref(false)
const isEditMenu = ref(false)
const saving = ref(false)

// 加载菜单树
async function loadMenuTree() {
  try {
    const res: any = await appAPI.getMenuTree(props.appId)
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
    is_visible: true
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
    is_visible: true
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
    parent_id: menu.parent_id,
    menu_icon: menu.icon || 'Document',
    menu_order: menu.order || 0,
    is_visible: menu.is_visible !== false
  }
  isEditMenu.value = true
  showMenuDialog.value = true
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
      await appAPI.updateMenu(selectedMenu.value.id, menuForm.value)
      ElMessage.success('更新成功')
    } else {
      await appAPI.addMenu(props.appId, menuForm.value)
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

// 拖拽排序
async function handleDrop() {
  // TODO: 实现拖拽后的排序保存
  ElMessage.success('菜单顺序已更新')
}

// 前往新建模板
function goCreateTemplate() {
  const routeData = router.resolve({ name: 'Templates', query: { mode: 'ai' } })
  window.open(routeData.href, '_blank')
}

onMounted(() => {
  loadMenuTree()
  loadTemplates()
})
</script>

<style scoped lang="scss">
.menu-designer {
  height: 100%;
}

.designer-body {
  display: flex;
  height: 100%;
  overflow: hidden;
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

    h3 {
      margin: 0;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
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
    color: var(--el-text-color-secondary);
  }

  .tree-node {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.sidebar-right {
  width: 300px;
  background: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-light);
  padding: 16px;
  overflow-y: auto;

  h3 {
    margin: 0 0 16px;
    font-size: 14px;
    color: var(--el-text-color-secondary);
    border-bottom: 1px solid var(--el-border-color-light);
    padding-bottom: 12px;
  }

  h4 {
    margin: 0 0 16px;
    font-size: 13px;
    color: var(--el-text-color-placeholder);
  }
}
</style>
