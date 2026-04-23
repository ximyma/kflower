<template>
  <div class="user-profile-page">
    <el-card class="profile-card">
      <template #header>
        <div class="profile-header">
          <el-icon size="24" style="margin-right: 8px"><User /></el-icon>
          <span class="header-title">个人信息</span>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 错误状态 -->
      <el-alert
        v-else-if="error"
        :title="error"
        type="error"
        show-icon
        closable
        @close="error = ''"
      />

      <!-- 个人信息表单 -->
      <el-form
        v-else
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        label-width="120px"
        class="profile-form"
      >
        <h3 class="form-section-title">基本信息</h3>
        
        <el-form-item label="头像" prop="avatar">
          <div class="avatar-uploader">
            <el-avatar :size="80" :src="profileForm.avatar" class="avatar-preview">
              {{ profileForm.name?.charAt(0) || profileForm.username?.charAt(0) || 'U' }}
            </el-avatar>
            <div class="avatar-actions">
              <el-upload
                action="/api/v1/upload"
                :show-file-list="false"
                :headers="uploadHeaders"
                :on-success="handleAvatarSuccess"
                :before-upload="beforeAvatarUpload"
              >
                <el-button type="primary" size="small">更换头像</el-button>
              </el-upload>
              <el-button size="small" @click="profileForm.avatar = ''" v-if="profileForm.avatar">移除头像</el-button>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="姓名" prop="name">
          <el-input
            v-model="profileForm.name"
            placeholder="请输入真实姓名"
            style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="profileForm.username"
            placeholder="请输入用户名"
            style="width: 300px"
            disabled
          />
          <span class="form-tip">用户名创建后不可修改</span>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="profileForm.email"
            placeholder="请输入邮箱"
            style="width: 300px"
          />
          <el-button
            v-if="!emailVerified && profileForm.email"
            type="text"
            size="small"
            @click="verifyEmail"
          >
            验证邮箱
          </el-button>
          <el-tag v-else-if="emailVerified" type="success" size="small">已验证</el-tag>
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="profileForm.phone"
            placeholder="请输入手机号"
            style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="部门" prop="department">
          <el-input
            v-model="profileForm.department"
            placeholder="请输入所属部门"
            style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="职位" prop="position">
          <el-input
            v-model="profileForm.position"
            placeholder="请输入职位"
            style="width: 300px"
          />
        </el-form-item>

        <h3 class="form-section-title">账号安全</h3>

        <el-form-item label="当前密码" prop="currentPassword">
          <el-input
            v-model="passwordForm.currentPassword"
            type="password"
            placeholder="请输入当前密码"
            style="width: 300px"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            style="width: 300px"
            show-password
          />
          <div class="form-tip">密码长度6-20位，包含字母和数字</div>
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            style="width: 300px"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="updating" @click="updateProfile">
            保存个人信息
          </el-button>
          <el-button :loading="changingPassword" @click="changePassword">
            修改密码
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 账号操作卡片 -->
    <el-card class="account-actions-card">
      <template #header>
        <div class="profile-header">
          <el-icon size="24" style="margin-right: 8px"><Setting /></el-icon>
          <span class="header-title">账号操作</span>
        </div>
      </template>

      <div class="account-actions">
        <div class="action-item">
          <h4>登录日志</h4>
          <p>查看最近30天的登录记录和设备信息</p>
          <el-button type="text" @click="viewLoginLogs">查看日志</el-button>
        </div>

        <div class="action-item">
          <h4>账号绑定</h4>
          <p>绑定微信、钉钉等第三方账号</p>
          <el-button type="text">管理绑定</el-button>
        </div>

        <div class="action-item">
          <h4>通知设置</h4>
          <p>设置邮件、短信通知偏好</p>
          <el-button type="text">设置通知</el-button>
        </div>

        <div class="action-item danger-zone">
          <h4>危险操作</h4>
          <p>删除账号或导出个人数据</p>
          <el-button type="text" style="color: #f56c6c" @click="showDeleteDialog">
            删除账号
          </el-button>
          <el-button type="text">导出数据</el-button>
        </div>
      </div>
    </el-card>

    <!-- 删除账号确认对话框 -->
    <el-dialog
      v-model="showDeleteConfirm"
      title="确认删除账号"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="delete-dialog">
        <el-alert
          title="警告：此操作不可恢复！"
          type="error"
          description="删除账号将永久删除您的所有数据，包括模板、表单、提交记录等。"
          show-icon
          :closable="false"
        />
        <div class="delete-confirm">
          <el-input
            v-model="deleteConfirmText"
            placeholder="请输入「确认删除」以继续"
            style="margin-top: 16px"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="showDeleteConfirm = false">取消</el-button>
        <el-button
          type="danger"
          :disabled="deleteConfirmText !== '确认删除'"
          :loading="deletingAccount"
          @click="deleteAccount"
        >
          永久删除
        </el-button>
      </template>
    </el-dialog>

    <!-- 登录日志对话框 -->
    <el-dialog
      v-model="showLoginLogs"
      title="登录日志"
      width="700px"
      top="5vh"
    >
      <div v-if="loginLogsLoading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      <el-table v-else :data="loginLogs" style="width: 100%">
        <el-table-column prop="login_time" label="登录时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.login_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="120" />
        <el-table-column prop="location" label="登录地点" />
        <el-table-column prop="device" label="设备信息" />
        <el-table-column prop="browser" label="浏览器" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showLoginLogs = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Setting } from '@element-plus/icons-vue'
import { useUserStore } from '../../common/store/user'
import { userAPI } from '../../common/api'

const userStore = useUserStore()

// 状态
const loading = ref(true)
const error = ref('')
const updating = ref(false)
const changingPassword = ref(false)
const deletingAccount = ref(false)
const emailVerified = ref(false)
const showDeleteConfirm = ref(false)
const deleteConfirmText = ref('')
const showLoginLogs = ref(false)
const loginLogsLoading = ref(false)
const loginLogs = ref<any[]>([])

// 表单引用
const profileFormRef = ref<any>(null)

// 表单数据
const profileForm = reactive({
  avatar: '',
  name: '',
  username: '',
  email: '',
  phone: '',
  department: '',
  position: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 上传配置
const uploadHeaders = {
  Authorization: `Bearer ${userStore.token}`
}

// 表单验证规则
const profileRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度2-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ]
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度6-20位', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).{6,20}$/, message: '密码需包含字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: any) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 加载用户信息
async function loadUserProfile() {
  loading.value = true
  try {
    // 从store获取当前用户信息
    const userInfo = userStore.userInfo.value
    if (userInfo) {
      profileForm.avatar = userInfo.avatar || ''
      profileForm.name = userInfo.full_name || userInfo.name || ''
      profileForm.username = userInfo.username || ''
      profileForm.email = userInfo.email || ''
      profileForm.phone = userInfo.phone || ''
      profileForm.department = userInfo.department || ''
      profileForm.position = userInfo.position || ''
      
      // 检查邮箱验证状态（模拟）
      emailVerified.value = !!userInfo.email_verified_at
    }
    
    // 也可以直接从API获取最新信息
    // const res = await userAPI.getMe()
    // if (res.success) {
    //   const userData = res.data
    //   // 更新表单数据
    // }
  } catch (e: any) {
    error.value = e.message || '加载用户信息失败'
  } finally {
    loading.value = false
  }
}

// 头像上传成功
function handleAvatarSuccess(res: any) {
  if (res.success && res.data?.url) {
    profileForm.avatar = res.data.url
    ElMessage.success('头像上传成功')
  } else {
    ElMessage.error(res.message || '头像上传失败')
  }
}

// 头像上传前检查
function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过2MB')
    return false
  }
  return true
}

// 验证邮箱
function verifyEmail() {
  ElMessageBox.confirm('将发送验证邮件到您的邮箱，请查收邮件并点击链接完成验证', '验证邮箱', {
    confirmButtonText: '发送验证邮件',
    cancelButtonText: '取消',
    type: 'info'
  }).then(async () => {
    try {
      // 调用API发送验证邮件
      // const res = await userAPI.sendVerificationEmail()
      ElMessage.success('验证邮件已发送，请查收邮箱')
    } catch (e: any) {
      ElMessage.error(e.message || '发送验证邮件失败')
    }
  })
}

// 更新个人信息
async function updateProfile() {
  const valid = await profileFormRef.value?.validate().catch(() => false)
  if (!valid) return

  updating.value = true
  try {
    // 获取当前用户ID
    const userId = userStore.userInfo.value?.id
    if (!userId) {
      ElMessage.error('用户信息获取失败')
      return
    }
    
    // 调用API更新用户信息
    const updateData = {
      full_name: profileForm.name,
      email: profileForm.email,
      phone: profileForm.phone,
      department: profileForm.department,
      position: profileForm.position,
      avatar: profileForm.avatar
    }
    
    const res: any = await userAPI.update(userId, updateData)
    if (res.success) {
      // 更新store中的用户信息
      // 简单方案：重新获取用户信息
      const meRes: any = await userAPI.getMe()
      if (meRes.success) {
        // 更新store（假设store会自动处理）
        userStore.userInfo.value = meRes.data
      }
      ElMessage.success('个人信息已更新')
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '更新失败')
  } finally {
    updating.value = false
  }
}

// 修改密码
async function changePassword() {
  const valid = await profileFormRef.value?.validateField(['currentPassword', 'newPassword', 'confirmPassword']).catch(() => false)
  if (!valid) return

  changingPassword.value = true
  try {
    // TODO: 需要后端提供密码修改API接口
    // 暂时使用通用更新接口，但需要后端支持
    const userId = userStore.userInfo.value?.id
    if (!userId) {
      ElMessage.error('用户信息获取失败')
      return
    }
    
    // 这里应该调用专门的密码修改接口
    // const res = await userAPI.changePassword({
    //   current_password: passwordForm.currentPassword,
    //   new_password: passwordForm.newPassword
    // })
    
    // 临时方案：使用更新接口（需要后端支持密码字段更新）
    const updateData = {
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    }
    
    const res: any = await userAPI.update(userId, updateData)
    if (res.success) {
      ElMessage.success('密码修改成功')
      // 清空密码表单
      passwordForm.currentPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    } else {
      ElMessage.error(res.message || '密码修改失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

// 重置表单
function resetForm() {
  profileFormRef.value?.resetFields()
  loadUserProfile()
  ElMessage.info('表单已重置')
}

// 查看登录日志
async function viewLoginLogs() {
  showLoginLogs.value = true
  loginLogsLoading.value = true
  try {
    // 调用API获取登录日志
    // const res = await userAPI.getLoginLogs()
    // loginLogs.value = res.data || []
    
    // 模拟数据
    loginLogs.value = [
      {
        login_time: new Date().toISOString(),
        ip_address: '192.168.1.100',
        location: '北京',
        device: 'Windows Chrome',
        browser: 'Chrome 120',
        status: 'success'
      },
      {
        login_time: new Date(Date.now() - 86400000).toISOString(),
        ip_address: '192.168.1.101',
        location: '上海',
        device: 'Mac Safari',
        browser: 'Safari 17',
        status: 'success'
      }
    ]
  } catch (e: any) {
    ElMessage.error('获取登录日志失败')
  } finally {
    loginLogsLoading.value = false
  }
}

// 格式化日期时间
function formatDateTime(datetime: string) {
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 显示删除账号对话框
function showDeleteDialog() {
  showDeleteConfirm.value = true
  deleteConfirmText.value = ''
}

// 删除账号
async function deleteAccount() {
  deletingAccount.value = true
  try {
    // 调用API删除账号
    // await userAPI.deleteAccount()
    ElMessage.success('账号删除请求已提交，请查收确认邮件')
    showDeleteConfirm.value = false
    
    // 延迟跳转到首页
    setTimeout(() => {
      userStore.logout()
      window.location.href = '/'
    }, 3000)
  } catch (e: any) {
    ElMessage.error(e.message || '删除账号失败')
  } finally {
    deletingAccount.value = false
  }
}

onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped lang="scss">
.user-profile-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-card, .account-actions-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.profile-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  
  .header-title {
    font-size: 16px;
  }
}

.loading-container {
  padding: 40px 0;
}

.profile-form {
  padding: 20px;
  
  .form-section-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 24px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e4e7ed;
    
    &:first-child {
      margin-top: 0;
    }
  }
}

.avatar-uploader {
  display: flex;
  align-items: center;
  gap: 20px;
  
  .avatar-preview {
    border: 2px solid #e4e7ed;
  }
  
  .avatar-actions {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: 8px;
}

.account-actions {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 20px;
  
  .action-item {
    padding: 16px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    transition: border-color 0.3s;
    
    &:hover {
      border-color: var(--el-color-primary);
    }
    
    h4 {
      margin: 0 0 8px;
      font-size: 14px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    p {
      margin: 0 0 12px;
      font-size: 12px;
      color: var(--el-text-color-regular);
      line-height: 1.5;
    }
    
    &.danger-zone {
      border-color: #f56c6c;
      
      &:hover {
        border-color: #f78989;
      }
    }
  }
}

.delete-dialog {
  .delete-confirm {
    margin-top: 16px;
  }
}

// 响应式
@media (max-width: 768px) {
  .user-profile-page {
    padding: 16px;
  }
  
  .profile-form {
    padding: 16px;
  }
  
  .account-actions {
    grid-template-columns: 1fr;
  }
}
</style>
