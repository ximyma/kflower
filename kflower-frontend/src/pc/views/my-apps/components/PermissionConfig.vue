<template>
  <div class="permission-config">
    <el-tabs v-model="activeTab">
      <!-- 应用访问权限 -->
      <el-tab-pane label="访问权限" name="access">
        <el-alert title="设置哪些角色可以访问此应用" type="info" :closable="false" style="margin-bottom: 16px" />
        <el-checkbox-group v-model="allowedRoles">
          <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">
            {{ role.name }}
          </el-checkbox>
        </el-checkbox-group>
      </el-tab-pane>

      <!-- 菜单权限 -->
      <el-tab-pane label="菜单权限" name="menus">
        <el-alert title="设置每个菜单对不同角色的可见性" type="info" :closable="false" style="margin-bottom: 16px" />
        <el-table :data="menus" border>
          <el-table-column prop="label" label="菜单名称" width="180" />
          <el-table-column label="可见角色">
            <template #default="{ row }">
              <el-checkbox-group v-model="menuPermissions[row.id]">
                <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">
                  {{ role.name }}
                </el-checkbox>
              </el-checkbox-group>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 字段权限 -->
      <el-tab-pane label="字段权限" name="fields">
        <el-alert title="设置不同角色对表单字段的操作权限" type="info" :closable="false" style="margin-bottom: 16px" />
        <el-select v-model="selectedTemplate" placeholder="选择模板" style="width: 300px; margin-bottom: 16px">
          <el-option v-for="tpl in templatesList" :key="tpl.id" :label="tpl.name" :value="tpl.id" />
        </el-select>

        <el-table v-if="currentTemplateFields.length" :data="currentTemplateFields" border>
          <el-table-column prop="label" label="字段名称" width="150" />
          <el-table-column prop="name" label="字段标识" width="150" />
          <el-table-column v-for="role in roles" :key="role.id" :label="role.name" width="130">
            <template #default="{ row }">
              <el-select v-model="fieldPermissions[row.name][role.id]" size="small">
                <el-option label="可读写" value="write" />
                <el-option label="只读" value="readonly" />
                <el-option label="隐藏" value="hidden" />
              </el-select>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <div class="action-bar">
      <el-button type="primary" @click="savePermissions" :loading="saving">保存配置</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { appAPI } from '@/common/api/myApps'
import { templateAPI } from '@/common/api'

const props = defineProps<{ appId: number }>()

const activeTab = ref('access')
const roles = ref<any[]>([])
const menus = ref<any[]>([])
const templatesList = ref<any[]>([])
const selectedTemplate = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)

const allowedRoles = ref<number[]>([])
const menuPermissions = reactive<Record<number, number[]>>({})
const fieldPermissions = reactive<Record<string, Record<number, string>>>({})

const currentTemplateFields = computed(() => {
  if (!selectedTemplate.value) return []
  const tpl = templatesList.value.find(t => t.id === selectedTemplate.value)
  if (!tpl?.fields) return []
  return tpl.fields.filter((f: any) => f.type !== 'divider' && f.type !== 'title')
})

async function loadPermissions() {
  loading.value = true
  try {
    const res: any = await appAPI.getPermissions(props.appId)
    const data = res.data || res

    roles.value = data.roles || []
    menus.value = data.menus || []

    const perms = data.permissions || {}
    allowedRoles.value = perms.allowed_roles || []

    // 初始化菜单权限
    for (const menu of menus.value) {
      if (!menuPermissions[menu.id]) {
        menuPermissions[menu.id] = []
      }
    }
    const savedMenuPerms = perms.menu_permissions || {}
    for (const menuId in savedMenuPerms) {
      menuPermissions[parseInt(menuId)] = savedMenuPerms[menuId]
    }

    // 处理模板和字段权限
    const templatesData = data.templates || {}
    templatesList.value = Object.entries(templatesData).map(([id, info]: [any, any]) => ({
      id: parseInt(id),
      name: info.name,
      fields: info.fields || []
    }))

    const savedFieldPerms = perms.field_permissions || {}
    for (const tpl of templatesList.value) {
      for (const field of tpl.fields || []) {
        const key = field.name
        if (!fieldPermissions[key]) {
          fieldPermissions[key] = {}
        }
        const tplPerms = savedFieldPerms[tpl.id] || {}
        for (const role of roles.value) {
          fieldPermissions[key][role.id] = tplPerms[field.name] || 'write'
        }
      }
    }

    if (templatesList.value.length > 0) {
      selectedTemplate.value = templatesList.value[0].id
    }
  } catch (e) {
    ElMessage.error('加载权限配置失败')
  } finally {
    loading.value = false
  }
}

async function savePermissions() {
  saving.value = true
  try {
    const config: any = {
      allowed_roles: allowedRoles.value,
      menu_permissions: menuPermissions,
      field_permissions: {}
    }

    for (const tpl of templatesList.value) {
      config.field_permissions[tpl.id] = {}
      for (const field of tpl.fields || []) {
        config.field_permissions[tpl.id][field.name] = fieldPermissions[field.name] || 'write'
      }
    }

    await appAPI.savePermissions(props.appId, config)
    ElMessage.success('权限配置已保存')
  } catch (e: any) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.permission-config {
  padding: 16px;
}
.action-bar {
  margin-top: 24px;
  text-align: center;
}
</style>
