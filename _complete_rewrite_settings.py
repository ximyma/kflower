# -*- coding: utf-8 -*-
"""
Completely fix Settings.vue - rebuild script section
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到 template 部分的结束（</template>）
template_end = content.find('</template>')
script_start = content.find('<script setup')

if template_end < 0 or script_start < 0:
    print("Cannot find template or script markers")
else:
    template_part = content[:template_end + len('</template>')]
    
    # 新的 script 部分
    new_script = '''
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Download, Upload, Delete, Refresh } from '@element-plus/icons-vue'
import { systemAPI, aiAPI } from '../../api'

const activeTab = ref('basic')

// AI 配置
const aiSettings = reactive({
  provider: 'siliconflow',
  apiKey: '',
  model: 'Qwen/Qwen2.5-7B-Instruct',
  temperature: 0.7,
  maxTokens: 2048,
  ragEnabled: true,
  embeddingModel: 'text-embedding-v2'
})

const aiStatus = reactive({
  provider: 'SiliconFlow',
  connected: false,
  model: '-',
  balance: '-'
})

const saving = ref(false)
const testing = ref(false)
const fetchingModels = ref(false)
const showAddModelDialog = ref(false)

// AI 配置数据
const allProviders = ref<any[]>([])
const availableModels = ref<any[]>([])
const configuredModels = ref<any[]>([])

const quickConfig = reactive({
  provider: 'siliconflow',
  apiKey: '',
  baseUrl: '',
  selectedModel: '',
  modelName: ''
})

// 加载提供商列表
async function loadProviders() {
  try {
    const res: any = await systemAPI.listAIProviders()
    allProviders.value = res.data?.providers || []
  } catch (e) {
    console.error('加载提供商失败', e)
  }
}

// 加载已配置的模型
async function loadConfiguredModels() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    const models: any[] = []
    if (config.ai_models) {
      try {
        const savedModels = typeof config.ai_models === 'string' ? JSON.parse(config.ai_models) : config.ai_models
        models.push(...savedModels)
      } catch {}
    }
    if (config.ai_provider && config.ai_api_key && models.length === 0) {
      models.push({
        id: 'default',
        provider: config.ai_provider,
        modelId: config.ai_model,
        modelName: config.ai_model,
        apiKey: config.ai_api_key,
        baseUrl: '',
        isDefault: true,
        configured: true
      })
    }
    configuredModels.value = models
  } catch (e) {
    console.error('加载配置模型失败', e)
  }
}

// 服务商变更
async function onProviderChange() {
  const provider = allProviders.value.find(p => p.id === quickConfig.provider)
  if (provider) {
    quickConfig.baseUrl = provider.default_base_url || ''
  }
  availableModels.value = []
  quickConfig.selectedModel = ''
}

// 获取模型列表
async function fetchModels() {
  if (!quickConfig.apiKey) {
    ElMessage.warning('请先输入 API Key')
    return
  }
  fetchingModels.value = true
  try {
    const res: any = await systemAPI.fetchAIModels(quickConfig.provider, quickConfig.apiKey, quickConfig.baseUrl)
    if (res.data?.models) {
      availableModels.value = res.data.models
      if (res.data.from_api) {
        ElMessage.success(`获取到 ${res.data.count} 个模型`)
      } else {
        ElMessage.info('使用预设模型列表')
      }
    } else {
      ElMessage.error(res.message || '获取模型列表失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '获取模型列表失败')
  } finally {
    fetchingModels.value = false
  }
}

// 保存模型配置
async function saveModelConfig() {
  if (!quickConfig.apiKey || !quickConfig.selectedModel) {
    ElMessage.warning('请填写完整配置')
    return
  }
  saving.value = true
  try {
    const newModel = {
      id: 'model_' + Date.now(),
      provider: quickConfig.provider,
      modelId: quickConfig.selectedModel,
      modelName: quickConfig.modelName || quickConfig.selectedModel,
      apiKey: quickConfig.apiKey,
      baseUrl: quickConfig.baseUrl,
      isDefault: configuredModels.value.length === 0,
      configured: true
    }
    configuredModels.value.push(newModel)
    await systemAPI.saveConfig({
      ai_models: JSON.stringify(configuredModels.value),
      ai_provider: quickConfig.provider,
      ai_api_key: quickConfig.apiKey,
      ai_model: quickConfig.selectedModel
    })
    ElMessage.success('模型配置已保存')
    quickConfig.selectedModel = ''
    quickConfig.modelName = ''
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 设置默认模型
async function setDefaultModel(row: any) {
  configuredModels.value.forEach(m => m.isDefault = false)
  row.isDefault = true
  try {
    await systemAPI.saveConfig({
      ai_models: JSON.stringify(configuredModels.value),
      ai_provider: row.provider,
      ai_api_key: row.apiKey,
      ai_model: row.modelId
    })
    ElMessage.success('默认模型已更新')
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

// 编辑模型配置
function editModelConfig(row: any) {
  quickConfig.provider = row.provider
  quickConfig.apiKey = row.apiKey
  quickConfig.baseUrl = row.baseUrl || ''
  quickConfig.selectedModel = row.modelId
  quickConfig.modelName = row.modelName
  fetchModels()
}

// 删除模型配置
async function deleteModelConfig(row: any) {
  try {
    configuredModels.value = configuredModels.value.filter(m => m.id !== row.id)
    await systemAPI.saveConfig({
      ai_models: JSON.stringify(configuredModels.value)
    })
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// 获取提供商名称
function getProviderName(id: string) {
  const p = allProviders.value.find(p => p.id === id)
  return p?.name || id
}

// 基本设置
const basicSettings = reactive({
  platformName: 'Kflower 企业智能管理平台',
  logo: '',
  description: '面向政府和企事业单位的 AI 智能体平台',
  copyright: '© 2024 Kflower. All Rights Reserved.',
  icp: ''
})

// 安全设置
const securitySettings = reactive({
  passwordStrength: 'high',
  passwordExpireDays: 90,
  maxLoginAttempts: 5,
  sessionTimeout: 30,
  twoFactorEnabled: false,
  ipWhitelist: ''
})

// 通知设置
const notificationSettings = reactive({
  emailEnabled: true,
  smtpHost: 'smtp.example.com',
  smtpPort: 587,
  smtpFrom: 'noreply@example.com',
  smsEnabled: false,
  wecomEnabled: false
})

// 数据统计
const dataStats = reactive({
  users: 156,
  templates: 28,
  workflows: 45,
  documents: 1234,
  dbSize: '256 MB'
})

// 备份设置
const backupSettings = reactive({
  autoBackup: true,
  backupFrequency: 'daily',
  keepBackups: 7
})

// 日志
const logs = ref([
  { id: 1, username: 'admin', action: '登录', module: '认证', ip: '192.168.1.100', detail: '用户登录系统', createdAt: '2024-01-15 10:30:00' },
])
const currentPage = ref(1)
const pageSize = ref(20)
const totalLogs = ref(100)

// 技术栈
const techStack = ['Vue 3', 'FastAPI', 'SQLAlchemy', 'TypeScript', 'Element Plus', 'ECharts']

// Logo 上传
const handleLogoChange = (file: any) => {
  basicSettings.logo = URL.createObjectURL(file.raw)
}

// 保存设置
const saveBasicSettings = () => ElMessage.success('基本设置已保存')
const saveSecuritySettings = () => ElMessage.success('安全设置已保存')
const saveNotificationSettings = () => ElMessage.success('通知设置已保存')
const saveBackupSettings = () => ElMessage.success('备份设置已保存')

// 测试通知
const testNotification = () => ElMessage.info('测试通知已发送')

// 数据操作
const exportData = () => ElMessage.info('数据导出功能开发中')
const importData = () => ElMessage.info('数据导入功能开发中')
const showClearDataDialog = () => ElMessage.warning('危险操作，请谨慎！')
const createBackup = () => ElMessage.success('备份创建成功')

// 日志
const refreshLogs = () => ElMessage.success('日志已刷新')
const loadLogs = () => {}

// 加载配置
onMounted(async () => {
  await loadProviders()
  await loadConfiguredModels()
  try {
    const res: any = await systemAPI.getConfig()
    if (res.data) {
      const config = res.data
      aiSettings.provider = config.ai_provider || 'siliconflow'
      aiSettings.apiKey = config.ai_api_key || ''
      aiSettings.model = config.ai_model || 'Qwen/Qwen2.5-7B-Instruct'
      aiStatus.provider = aiSettings.provider
      aiStatus.connected = !!aiSettings.apiKey
    }
  } catch (e) {
    console.error('加载配置失败', e)
  }
})
</script>

<style scoped lang="scss">
.system-settings {
  padding: 20px;
}
.settings-tabs {
  background: white;
  padding: 20px;
  border-radius: 8px;
}
.form-tip {
  margin-left: 8px;
  color: #909399;
}
.data-stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  .stat-item {
    background: #f5f7fa;
    padding: 16px 24px;
    border-radius: 8px;
    text-align: center;
    .label { display: block; color: #909399; font-size: 14px; }
    .value { display: block; font-size: 24px; font-weight: bold; color: #303133; margin-top: 4px; }
  }
}
.data-actions { display: flex; gap: 12px; }
.backup-section h4 { margin-bottom: 16px; color: #303133; }
.logs-header { display: flex; justify-content: space-between; align-items: center; }
.about-info {
  display: flex;
  gap: 40px;
  padding: 20px;
  .about-logo {
    .logo-placeholder {
      width: 120px; height: 120px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      font-size: 60px;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 24px;
    }
  }
  .about-text {
    h2 { margin: 0 0 8px; }
    .version { color: #409eff; font-size: 16px; margin: 0 0 16px; }
    .description { color: #606266; line-height: 1.8; margin-bottom: 16px; }
    .tech-stack { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
    .about-links { display: flex; gap: 12px; }
  }
}
.configured-models { margin-bottom: 20px; }
.quick-config { background: #f9fafb; padding: 20px; border-radius: 8px; }
</style>
'''

    # 组合新内容
    new_content = template_part + '\n' + new_script
    
    with open(path, 'w', encoding='utf-8-sig') as f:
        f.write(new_content)
    
    print("Done: Completely rewrote Settings.vue")
