<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon> 新增用户
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索用户名/姓名/邮箱"
            clearable
            style="width: 250px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon> 重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table
        :data="users"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" class="user-avatar">
                {{ row.full_name?.charAt(0) || row.username?.charAt(0) || 'U' }}
              </el-avatar>
              <span class="username">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="warning" size="small">管理员</el-tag>
            <el-tag v-else type="info" size="small">普通用户</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button
              v-if="row.id !== currentUserId"
              :type="row.is_active ? 'warning' : 'success'"
              size="small"
              link
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="row.id !== currentUserId"
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="部门" prop="organization_id">
          <el-select
            v-model="form.organization_id"
            placeholder="请选择部门"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="org in organizations"
              :key="org.id"
              :label="org.name"
              :value="org.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="管理员" prop="is_superuser" v-if="isEdit && isCurrentUserAdmin">
          <el-switch v-model="form.is_superuser" />
          <span class="form-tip">开启后该用户将成为系统管理员</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="400px"
    >
      <p>确定要删除用户 <strong>{{ deleteTarget?.username }}</strong> 吗？</p>
      <p style="color: #f56c6c; margin-top: 8px;">此操作不可恢复！</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="deleting" @click="confirmDelete">
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { userAPI, orgAPI } from '../../common/api'
import { useUserStore } from '../../common/store/user'

const userStore = useUserStore()

// 状态
const loading = ref(false)
const users = ref<any[]>([])
const organizations = ref<any[]>([])
const dialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const deleteTarget = ref<any>(null)

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 表单
const formRef = ref<any>(null)
const form = reactive({
  username: '',
  full_name: '',
  email: '',
  phone: '',
  password: '',
  organization_id: null as number | null,
  is_superuser: false
})

// 表单验证
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度3-50个字符', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

// 计算属性
const currentUserId = computed(() => userStore.userInfo?.id)
const isCurrentUserAdmin = computed(() => userStore.isAdmin)

// 加载用户列表
async function loadUsers() {
  loading.value = true
  try {
    const res: any = await userAPI.list({
      search: searchForm.keyword || undefined,
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    })

    if (res.success) {
      users.value = res.data.users || []
      pagination.total = res.data.total || 0
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 加载组织列表
async function loadOrganizations() {
  try {
    const res: any = await orgAPI.list()
    if (res.success) {
      organizations.value = res.data.organizations || []
    }
  } catch (e) {
    console.error('加载组织列表失败', e)
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  loadUsers()
}

// 重置
function handleReset() {
  searchForm.keyword = ''
  pagination.page = 1
  loadUsers()
}

// 打开创建对话框
function openCreateDialog() {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

// 打开编辑对话框
async function openEditDialog(row: any) {
  isEdit.value = true
  editingId.value = row.id
  form.username = row.username
  form.full_name = row.full_name || ''
  form.email = row.email || ''
  form.phone = row.phone || ''
  form.organization_id = row.organization_id
  form.is_superuser = row.is_superuser || false
  dialogVisible.value = true
}

// 重置表单
function resetForm() {
  form.username = ''
  form.full_name = ''
  form.email = ''
  form.phone = ''
  form.password = ''
  form.organization_id = null
  form.is_superuser = false
  formRef.value?.resetFields()
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    interface CreateUserData {
      username: string
      email: string
      password: string
      full_name: string
      phone?: string
      organization_id?: number
    }
    const createData: CreateUserData = {
      username: form.username,
      full_name: form.full_name,
      email: form.email,
      password: form.password,
    }
    if (form.phone) createData.phone = form.phone
    if (form.organization_id !== null) createData.organization_id = form.organization_id

    let res: any
    if (isEdit.value && editingId.value) {
      // 编辑
      const updateData = {
        username: form.username,
        full_name: form.full_name,
        email: form.email,
      }
      if (form.phone) (updateData as any).phone = form.phone
      if (form.organization_id !== null) (updateData as any).organization_id = form.organization_id
      res = await userAPI.update(editingId.value, updateData)
    } else {
      // 创建
      res = await userAPI.create(createData)
    }

    if (res.success) {
      ElMessage.success(isEdit.value ? '用户更新成功' : '用户创建成功')
      dialogVisible.value = false
      loadUsers()
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 切换用户状态
async function toggleUserStatus(row: any) {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      `确定要${action}用户 ${row.username} 吗？`,
      '提示',
      { type: 'warning' }
    )

    const res: any = await userAPI.update(row.id, { is_active: !row.is_active })
    if (res.success) {
      ElMessage.success(`${action}成功`)
      loadUsers()
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || `${action}失败`)
    }
  }
}

// 删除用户
function handleDelete(row: any) {
  deleteTarget.value = row
  deleteDialogVisible.value = true
}

// 确认删除
async function confirmDelete() {
  if (!deleteTarget.value) return

  deleting.value = true
  try {
    const res: any = await userAPI.delete(deleteTarget.value.id)
    if (res.success) {
      ElMessage.success('删除成功')
      deleteDialogVisible.value = false
      loadUsers()
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

// 格式化日期时间
function formatDateTime(datetime: string | null) {
  if (!datetime) return '-'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 页面加载
onMounted(() => {
  loadUsers()
  loadOrganizations()
})
</script>

<style scoped lang="scss">
.users-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.search-card {
  margin-bottom: 16px;
}

.table-card {
  background: var(--el-bg-color);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;

  .user-avatar {
    background: var(--el-color-primary);
    color: white;
    font-size: 14px;
  }

  .username {
    font-weight: 500;
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.el-dialog {
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>
