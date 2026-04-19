<template>
  <div class="step4-menu-config">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📑 配置应用菜单</span>
          <el-button size="small" @click="autoGenerateMenus">
            <el-icon><Refresh /></el-icon> 重新生成
          </el-button>
        </div>
      </template>

      <div class="menu-layout">
        <!-- 左侧：表单列表 -->
        <div class="templates-panel">
          <h4>可用表单</h4>
          <p class="hint">拖拽表单到右侧菜单树</p>
          <div class="template-list">
            <div 
              v-for="tpl in availableTemplates" 
              :key="tpl._id"
              class="template-item"
              draggable="true"
              @dragstart="handleDragStart($event, tpl)"
            >
              <el-icon><Document /></el-icon>
              <span>{{ tpl.name }}</span>
              <el-tag v-if="tpl._status === 'success'" size="small" type="success">已生成</el-tag>
            </div>
          </div>
        </div>

        <!-- 右侧：菜单树 -->
        <div class="menu-panel">
          <h4>应用菜单</h4>
          <div class="menu-actions">
            <el-button size="small" @click="addMenuItem">
              <el-icon><Plus /></el-icon> 添加菜单
            </el-button>
            <el-button size="small" text @click="clearMenus">
              清空
            </el-button>
          </div>

          <div 
            class="menu-tree-container"
            @dragover.prevent
            @drop="handleDrop($event, null)"
          >
            <div v-if="localMenus.length === 0" class="empty-drop">
              <el-icon :size="48"><FolderOpened /></el-icon>
              <p>拖拽表单到此处添加菜单</p>
            </div>

            <div v-else class="menu-list">
              <div 
                v-for="(menu, idx) in localMenus" 
                :key="menu.id || idx"
                class="menu-item"
                :class="{ 'is-active': selectedMenu?.id === menu.id }"
                @click="selectMenu(menu)"
              >
                <div class="menu-item-content">
                  <el-icon><component :is="menu.icon || 'Document'" /></el-icon>
                  <span class="menu-label">{{ menu.label }}</span>
                  <el-tag v-if="menu.template_name" size="small" type="info">{{ menu.template_name }}</el-tag>
                </div>
                <div class="menu-item-actions">
                  <el-button size="small" text @click.stop="moveMenu(idx, -1)" :disabled="idx === 0">
                    <el-icon><ArrowUp /></el-icon>
                  </el-button>
                  <el-button size="small" text @click.stop="moveMenu(idx, 1)" :disabled="idx === localMenus.length - 1">
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <el-button size="small" text type="danger" @click.stop="removeMenu(idx)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：菜单属性 -->
        <div class="properties-panel" v-if="selectedMenu">
          <h4>菜单属性</h4>
          <el-form :model="selectedMenu" label-width="80px" size="small">
            <el-form-item label="菜单名称">
              <el-input v-model="selectedMenu.label" />
            </el-form-item>
            <el-form-item label="图标">
              <el-select v-model="selectedMenu.icon" style="width: 100%">
                <el-option label="文档" value="Document" />
                <el-option label="文件夹" value="Folder" />
                <el-option label="用户" value="User" />
                <el-option label="设置" value="Setting" />
                <el-option label="图表" value="TrendCharts" />
                <el-option label="列表" value="List" />
                <el-option label="表格" value="Grid" />
              </el-select>
            </el-form-item>
            <el-form-item label="关联表单">
              <el-select v-model="selectedMenu.template_id" style="width: 100%" clearable>
                <el-option 
                  v-for="tpl in availableTemplates" 
                  :key="tpl._id" 
                  :label="tpl.name" 
                  :value="tpl._id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="显示">
              <el-switch v-model="selectedMenu.is_visible" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="$emit('prev')">上一步</el-button>
        <el-button type="primary" @click="$emit('next')" :disabled="localMenus.length === 0">
          下一步：配置主页 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus, Delete, ArrowUp, ArrowDown, Document, FolderOpened, Refresh, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  design: any
  templates: any[]
  menus: any[]
}>()

const emit = defineEmits(['update:menus', 'prev', 'next'])

const localMenus = computed({
  get: () => props.menus,
  set: (val) => emit('update:menus', val)
})

const availableTemplates = computed(() => 
  props.templates.filter(t => t._status === 'success' && t._id)
)

const selectedMenu = ref<any>(null)

// 自动生成菜单
function autoGenerateMenus() {
  const menus = availableTemplates.value.map((tpl, idx) => ({
    id: `menu_${idx}`,
    label: tpl.name,
    icon: 'Document',
    template_id: tpl._id,
    template_name: tpl.name,
    menu_order: idx,
    is_visible: true
  }))
  localMenus.value = menus
  selectedMenu.value = null
}

// 拖拽处理
function handleDragStart(e: DragEvent, tpl: any) {
  e.dataTransfer?.setData('application/json', JSON.stringify({
    type: 'template',
    template_id: tpl._id,
    template_name: tpl.name
  }))
}

function handleDrop(e: DragEvent, parent: any) {
  e.preventDefault()
  const data = e.dataTransfer?.getData('application/json')
  if (!data) return

  try {
    const { type, template_id, template_name } = JSON.parse(data)
    if (type === 'template') {
      const newMenu = {
        id: `menu_${Date.now()}`,
        label: template_name,
        icon: 'Document',
        template_id,
        template_name,
        menu_order: localMenus.value.length,
        is_visible: true
      }
      localMenus.value = [...localMenus.value, newMenu]
    }
  } catch {}
}

// 菜单操作
function addMenuItem() {
  const newMenu = {
    id: `menu_${Date.now()}`,
    label: `新菜单${localMenus.value.length + 1}`,
    icon: 'Document',
    template_id: null,
    template_name: null,
    menu_order: localMenus.value.length,
    is_visible: true
  }
  localMenus.value = [...localMenus.value, newMenu]
  selectedMenu.value = newMenu
}

function removeMenu(idx: number) {
  const newMenus = [...localMenus.value]
  newMenus.splice(idx, 1)
  // 重新排序
  newMenus.forEach((m, i) => m.menu_order = i)
  localMenus.value = newMenus
  if (selectedMenu.value?.id === localMenus.value[idx]?.id) {
    selectedMenu.value = null
  }
}

function moveMenu(idx: number, direction: number) {
  const newIdx = idx + direction
  if (newIdx < 0 || newIdx >= localMenus.value.length) return
  
  const newMenus = [...localMenus.value]
  const temp = newMenus[idx]
  newMenus[idx] = newMenus[newIdx]
  newMenus[newIdx] = temp
  
  // 更新顺序
  newMenus.forEach((m, i) => m.menu_order = i)
  localMenus.value = newMenus
}

function selectMenu(menu: any) {
  selectedMenu.value = menu
}

function clearMenus() {
  localMenus.value = []
  selectedMenu.value = null
}
</script>

<style scoped lang="scss">
.step4-menu-config {
  max-width: 1200px;
  margin: 0 auto;
}

.main-card {
  :deep(.el-card__header) {
    font-size: 16px;
    font-weight: 500;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-layout {
  display: grid;
  grid-template-columns: 250px 1fr 280px;
  gap: 20px;
  min-height: 400px;
}

.templates-panel, .menu-panel, .properties-panel {
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    color: var(--el-text-color-primary);
  }
}

.hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 0 0 12px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;

  &:hover {
    background: var(--el-fill-color);
  }

  .el-icon {
    color: var(--el-text-color-secondary);
  }

  span {
    flex: 1;
    font-size: 13px;
  }
}

.menu-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.menu-tree-container {
  min-height: 300px;
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
}

.empty-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);

  p {
    margin-top: 12px;
  }
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover, &.is-active {
    background: var(--el-color-primary-light-9);
    border-left: 3px solid var(--el-color-primary);
  }

  .menu-item-content {
    display: flex;
    align-items: center;
    gap: 8px;

    .menu-label {
      font-weight: 500;
    }
  }

  .menu-item-actions {
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
  }

  &:hover .menu-item-actions {
    opacity: 1;
  }
}

.properties-panel {
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>
