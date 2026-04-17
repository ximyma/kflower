# -*- coding: utf-8 -*-
"""
Rewrite AI configuration section in Settings.vue
Support dynamic model list, multiple models, custom base URL
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 找到 AI 配置 tab 的内容
start_marker = '<el-tab-pane label="AI 配置" name="ai">'
end_marker = '</el-tab-pane>'

start_idx = content.find(start_marker)
if start_idx < 0:
    print("AI config tab not found!")
else:
    # 找到结束标签（需要找到匹配的）
    # 从 start_idx 开始数 el-tab-pane 标签
    search_start = start_idx + len(start_marker)
    depth = 1
    end_idx = search_start
    while depth > 0 and end_idx < len(content):
        next_open = content.find('<el-tab-pane', end_idx)
        next_close = content.find('</el-tab-pane>', end_idx)
        if next_close < 0:
            break
        if next_open >= 0 and next_open < next_close:
            depth += 1
            end_idx = next_open + 1
        else:
            depth -= 1
            if depth == 0:
                end_idx = next_close
            else:
                end_idx = next_close + 1
    
    print(f"AI config tab: {start_idx} to {end_idx}")
    # 提取旧内容
    old_ai_tab = content[start_idx:end_idx + len(end_marker)]

# 新的 AI 配置内容
new_ai_tab = '''      <el-tab-pane label="AI 配置" name="ai">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>AI 大模型配置</span>
              <el-button type="primary" size="small" @click="showAddModelDialog = true">
                <el-icon><Plus /></el-icon> 添加模型
              </el-button>
            </div>
          </template>
          <el-alert
            title="配置说明"
            description="配置您的 AI 模型 API Key，支持同一服务商配置多个模型。系统将自动获取可用模型列表。"
            type="info"
            show-icon
            :closable="false"
            style="margin-bottom: 20px"
          />
          
          <!-- 已配置的模型列表 -->
          <div class="configured-models">
            <h4 style="margin-bottom:16px">已配置模型</h4>
            <el-table :data="configuredModels" border stripe>
              <el-table-column label="服务商" width="120">
                <template #default="{ row }">
                  <el-tag>{{ getProviderName(row.provider) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="模型" prop="modelName" min-width="200" show-overflow-tooltip />
              <el-table-column label="模型ID" prop="modelId" width="240" show-overflow-tooltip />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.configured ? 'success' : 'info'">
                    {{ row.configured ? '已配置' : '未配置' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="默认" width="80">
                <template #default="{ row }">
                  <el-switch v-model="row.isDefault" @change="setDefaultModel(row)" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button size="small" text type="primary" @click="editModelConfig(row)">编辑</el-button>
                  <el-button size="small" text type="danger" @click="deleteModelConfig(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-divider />
          
          <!-- 快速配置 -->
          <div class="quick-config">
            <h4 style="margin-bottom:16px">快速配置</h4>
            <el-form :model="quickConfig" label-width="120px" inline>
              <el-form-item label="服务商">
                <el-select v-model="quickConfig.provider" style="width:180px" @change="onProviderChange">
                  <el-option v-for="p in allProviders" :key="p.id" :label="p.name" :value="p.id">
                    <span>{{ p.name }}</span>
                    <span style="color:#999;margin-left:8px;font-size:12px">{{ p.description }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="quickConfig.apiKey" type="password" show-password style="width:280px" placeholder="请输入 API Key" />
              </el-form-item>
              <el-form-item label="Base URL">
                <el-input v-model="quickConfig.baseUrl" style="width:280px" placeholder="留空使用默认" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="fetchModels" :loading="fetchingModels">获取模型列表</el-button>
              </el-form-item>
            </el-form>
            
            <!-- 模型选择 -->
            <div v-if="availableModels.length > 0" style="margin-top:16px">
              <el-form label-width="120px">
                <el-form-item label="选择模型">
                  <el-select v-model="quickConfig.selectedModel" filterable style="width:400px" placeholder="选择或搜索模型">
                    <el-option v-for="m in availableModels" :key="m.id" :label="m.name" :value="m.id">
                      <span>{{ m.name }}</span>
                      <span style="color:#999;margin-left:8px;font-size:12px">{{ m.id }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-form-item label="模型名称">
                  <el-input v-model="quickConfig.modelName" style="width:280px" placeholder="自定义显示名称（可选）" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveModelConfig" :loading="saving">保存配置</el-button>
                  <el-button @click="testQuickConnection" :loading="testing">测试连接</el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-card>
      </el-tab-pane>'''

# 替换
content = content.replace(old_ai_tab, new_ai_tab)
print("Replaced AI config tab")

# 添加新的响应式数据和函数
# 找到 script setup 部分
script_start = content.find('<script setup lang="ts">')
if script_start > 0:
    # 找到 const saving = ref(false) 后面
    insert_point = content.find('const saving = ref(false)')
    if insert_point > 0:
        # 找到这行结束
        line_end = content.find('\n', insert_point)
        
        new_data = '''
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
    // 解析已配置的模型
    const models: any[] = []
    if (config.ai_models) {
      try {
        const savedModels = typeof config.ai_models === 'string' ? JSON.parse(config.ai_models) : config.ai_models
        models.push(...savedModels)
      } catch {}
    }
    // 兼容旧配置
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
    // 添加到配置列表
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
    
    // 保存到后端
    await systemAPI.saveConfig({
      ai_models: JSON.stringify(configuredModels.value),
      ai_provider: quickConfig.provider,
      ai_api_key: quickConfig.apiKey,
      ai_model: quickConfig.selectedModel
    })
    
    ElMessage.success('模型配置已保存')
    
    // 重置
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
  // 加载模型列表
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

// 快速测试连接
async function testQuickConnection() {
  if (!quickConfig.apiKey || !quickConfig.selectedModel) {
    ElMessage.warning('请先选择模型')
    return
  }
  testing.value = true
  try {
    // 先保存配置
    await systemAPI.saveConfig({
      ai_provider: quickConfig.provider,
      ai_api_key: quickConfig.apiKey,
      ai_model: quickConfig.selectedModel,
      ai_base_url: quickConfig.baseUrl
    })
    // 测试
    const res: any = await systemAPI.testAI()
    if (res.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(res.message || '连接失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '测试失败')
  } finally {
    testing.value = false
  }
}

// 获取提供商名称
function getProviderName(id: string) {
  const p = allProviders.value.find(p => p.id === id)
  return p?.name || id
}

'''
        content = content[:line_end] + new_data + content[line_end:]
        print("Added new data and functions")

# 更新 onMounted
old_mounted = '''onMounted(async () => {
    // 加载系统配置
    const res: any = await systemAPI.getConfig()'''

new_mounted = '''onMounted(async () => {
    // 加载提供商列表
    await loadProviders()
    // 加载已配置模型
    await loadConfiguredModels()
    // 加载系统配置
    const res: any = await systemAPI.getConfig()'''

if old_mounted in content:
    content = content.replace(old_mounted, new_mounted)
    print("Updated onMounted")

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("Done: Settings.vue updated with dynamic AI model configuration")
