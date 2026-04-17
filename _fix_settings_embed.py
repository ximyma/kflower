# -*- coding: utf-8 -*-
"""
修复 Settings.vue 添加嵌入模型和重排模型的增删改查功能
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 读取当前 Settings.vue
settings_path = r'D:\kflower\kflower-frontend\src\common\pc\views\Settings.vue'
with open(settings_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 替换嵌入向量配置部分，改为完整的管理界面
old_embed_section = '''          <!-- 嵌入向量配置 -->
          <div class="config-section">
            <div class="section-title">嵌入向量服务</div>
            <el-form :model="embedConfig" label-width="130px" style="max-width:600px;margin-top:12px">
              <el-form-item label="API Key">
                <el-input v-model="embedConfig.apiKey" type="password" show-password placeholder="DashScope / OpenAI API Key" />
              </el-form-item>
              <el-form-item label="Base URL">
                <el-input v-model="embedConfig.apiBase" placeholder="留空使用默认" />
              </el-form-item>
              <el-form-item label="模型">
                <el-select v-model="embedConfig.model" style="width:100%" filterable>
                  <el-option-group label="API 模型">
                    <el-option v-for="m in embedApiModels" :key="m.value" :label="m.label" :value="m.value">
                      <span>{{ m.label }}</span>
                      <span style="color:#999;font-size:12px;margin-left:8px">{{ m.desc }}</span>
                    </el-option>
                  </el-option-group>
                  <el-option-group label="本地模型" v-if="embedLocalModels.length > 0">
                    <el-option v-for="m in embedLocalModels" :key="m.value" :label="m.label" :value="m.value" :disabled="!embedSTAvailable">
                      <span>{{ m.label }}</span>
                      <span style="color:#67c23a;font-size:12px;margin-left:8px">本地</span>
                      <span style="color:#999;font-size:12px;margin-left:4px">{{ m.desc }}</span>
                    </el-option>
                  </el-option-group>
                </el-select>
                <div style="font-size:12px;color:#999;margin-top:4px" v-if="!embedSTAvailable">
                  本地模型需要安装 sentence-transformers：pip install sentence-transformers
                </div>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveEmbedConfig" :loading="savingEmbed">保存</el-button>
                <el-button @click="testEmbed" :loading="testingEmbed">测试嵌入</el-button>
              </el-form-item>
            </el-form>
          </div>'''

new_embed_section = '''          <!-- 嵌入向量模型管理 -->
          <div class="config-section">
            <div class="section-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
              <span class="section-title">嵌入向量模型</span>
              <el-button type="primary" size="small" @click="showAddEmbedModel = true; resetEmbedForm()">
                <el-icon><Plus /></el-icon> 添加嵌入模型
              </el-button>
            </div>
            
            <!-- 已配置嵌入模型列表 -->
            <el-table :data="configuredEmbedModels" border stripe style="margin-top:12px" v-if="configuredEmbedModels.length > 0">
              <el-table-column label="名称" prop="name" min-width="150" show-overflow-tooltip />
              <el-table-column label="类型" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.provider === 'local' ? 'success' : 'primary'" size="small">
                    {{ row.provider === 'local' ? '本地' : 'API' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="维度" prop="dimension" width="80" />
              <el-table-column label="默认" width="70">
                <template #default="{ row }">
                  <el-tag :type="row.isDefault ? 'success' : 'info'" size="small">{{ row.isDefault ? '是' : '否' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="160">
                <template #default="{ row }">
                  <el-button size="small" text type="primary" @click="setDefaultEmbedModel(row)">设为默认</el-button>
                  <el-button size="small" text type="danger" @click="deleteEmbedModel(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无配置，点击上方按钮添加" :image-size="60" />
            
            <!-- 添加嵌入模型对话框 -->
            <el-dialog v-model="showAddEmbedModel" title="添加嵌入模型" width="500px">
              <el-form :model="embedModelForm" label-width="100px">
                <el-form-item label="模型名称" required>
                  <el-input v-model="embedModelForm.name" placeholder="如：DashScope Embedding" />
                </el-form-item>
                <el-form-item label="类型" required>
                  <el-radio-group v-model="embedModelForm.provider">
                    <el-radio value="api">API 模型</el-radio>
                    <el-radio value="local">本地模型</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="模型ID" required>
                  <el-select v-model="embedModelForm.modelId" filterable allow-create placeholder="选择或输入模型ID" style="width:100%">
                    <el-option-group label="API 模型" v-if="embedModelForm.provider === 'api'">
                      <el-option v-for="m in embedApiModels" :key="m.value" :label="m.label" :value="m.value">
                        <span>{{ m.label }}</span>
                        <span style="color:#999;font-size:12px;margin-left:8px">{{ m.desc }}</span>
                      </el-option>
                    </el-option-group>
                    <el-option-group label="本地模型" v-if="embedModelForm.provider === 'local'">
                      <el-option v-for="m in embedLocalModels" :key="m.value" :label="m.label" :value="m.value" :disabled="!embedSTAvailable">
                        <span>{{ m.label }}</span>
                        <span style="color:#67c23a;font-size:12px;margin-left:8px">本地</span>
                      </el-option>
                    </el-option-group>
                  </el-select>
                </el-form-item>
                <el-form-item label="维度">
                  <el-input-number v-model="embedModelForm.dimension" :min="128" :max="4096" :step="64" />
                </el-form-item>
                <el-form-item label="API Key" v-if="embedModelForm.provider === 'api'">
                  <el-input v-model="embedModelForm.apiKey" type="password" show-password placeholder="API Key" />
                </el-form-item>
                <el-form-item label="Base URL" v-if="embedModelForm.provider === 'api'">
                  <el-input v-model="embedModelForm.baseUrl" placeholder="留空使用默认" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showAddEmbedModel = false">取消</el-button>
                <el-button type="primary" @click="addEmbedModel" :loading="savingEmbed">保存</el-button>
              </template>
            </el-dialog>
          </div>

          <el-divider />

          <!-- 重排模型管理 -->
          <div class="config-section">
            <div class="section-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
              <span class="section-title">重排模型 (Rerank)</span>
              <el-button type="primary" size="small" @click="showAddRerankModel = true; resetRerankForm()">
                <el-icon><Plus /></el-icon> 添加重排模型
              </el-button>
            </div>
            
            <!-- 已配置重排模型列表 -->
            <el-table :data="configuredRerankModels" border stripe style="margin-top:12px" v-if="configuredRerankModels.length > 0">
              <el-table-column label="名称" prop="name" min-width="150" show-overflow-tooltip />
              <el-table-column label="模型ID" prop="modelId" min-width="200" show-overflow-tooltip />
              <el-table-column label="默认" width="70">
                <template #default="{ row }">
                  <el-tag :type="row.isDefault ? 'success' : 'info'" size="small">{{ row.isDefault ? '是' : '否' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="160">
                <template #default="{ row }">
                  <el-button size="small" text type="primary" @click="setDefaultRerankModel(row)">设为默认</el-button>
                  <el-button size="small" text type="danger" @click="deleteRerankModel(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无配置，点击上方按钮添加" :image-size="60" />
            
            <!-- 添加重排模型对话框 -->
            <el-dialog v-model="showAddRerankModel" title="添加重排模型" width="500px">
              <el-form :model="rerankModelForm" label-width="100px">
                <el-form-item label="模型名称" required>
                  <el-input v-model="rerankModelForm.name" placeholder="如：BGE Reranker" />
                </el-form-item>
                <el-form-item label="模型ID" required>
                  <el-select v-model="rerankModelForm.modelId" filterable allow-create placeholder="选择或输入模型ID" style="width:100%">
                    <el-option v-for="m in rerankModelOptions" :key="m.value" :label="m.label" :value="m.value">
                      <span>{{ m.label }}</span>
                      <span style="color:#e6a23c;font-size:12px;margin-left:8px">{{ m.desc }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-form-item label="API Key">
                  <el-input v-model="rerankModelForm.apiKey" type="password" show-password placeholder="API Key（如需要）" />
                </el-form-item>
                <el-form-item label="Base URL">
                  <el-input v-model="rerankModelForm.baseUrl" placeholder="API 地址（如需要）" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showAddRerankModel = false">取消</el-button>
                <el-button type="primary" @click="addRerankModel" :loading="savingRerank">保存</el-button>
              </template>
            </el-dialog>
          </div>'''

if old_embed_section in content:
    content = content.replace(old_embed_section, new_embed_section)
    print("[OK] 嵌入模型管理部分已更新")
else:
    print("[WARN] 未找到嵌入配置部分，尝试其他模式")

# 2. 添加新的响应式变量和方法
old_script_vars = '''const embedConfig = reactive({ apiKey: '', apiBase: '', model: 'text-embedding-v2' })'''

new_script_vars = '''// 嵌入模型配置
const embedConfig = reactive({ apiKey: '', apiBase: '', model: 'text-embedding-v2' })
const showAddEmbedModel = ref(false)
const configuredEmbedModels = ref<any[]>([])
const embedModelForm = reactive({
  name: '', provider: 'api', modelId: '', dimension: 768, apiKey: '', baseUrl: ''
})

// 重排模型配置
const showAddRerankModel = ref(false)
const configuredRerankModels = ref<any[]>([])
const rerankModelForm = reactive({
  name: '', modelId: '', apiKey: '', baseUrl: ''
})
const rerankModelOptions = ref([
  { value: 'BAAI/bge-reranker-v2-m3', label: 'BGE-reranker-v2-m3', desc: '多语言重排' },
  { value: 'BAAI/bge-reranker-large', label: 'BGE-reranker-large', desc: '大型重排' },
  { value: 'BAAI/bge-reranker-base', label: 'BGE-reranker-base', desc: '基础重排' },
  { value: 'cohere/rerank-english-v3.0', label: 'Cohere Rerank English', desc: '英文重排' },
  { value: 'cohere/rerank-multilingual-v3.0', label: 'Cohere Rerank Multi', desc: '多语言重排' },
])
const savingRerank = ref(false)'''

if old_script_vars in content:
    content = content.replace(old_script_vars, new_script_vars)
    print("[OK] 变量已添加")

# 3. 添加方法
# 找到合适的位置添加方法（在 saveEmbedConfig 之后）
old_save_embed = '''async function saveEmbedConfig() {
  savingEmbed.value = true
  try {
    await localAIAPI.saveEmbeddingConfig(embedConfig)
    ElMessage.success('嵌入配置已保存')
    await loadServicesStatus()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingEmbed.value = false
  }
}'''

new_methods = '''async function saveEmbedConfig() {
  savingEmbed.value = true
  try {
    await localAIAPI.saveEmbeddingConfig(embedConfig)
    ElMessage.success('嵌入配置已保存')
    await loadServicesStatus()
    await loadConfiguredEmbedModels()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingEmbed.value = false
  }
}

// 加载已配置的嵌入模型
async function loadConfiguredEmbedModels() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.embed_models) {
      try {
        const models = typeof config.embed_models === 'string' ? JSON.parse(config.embed_models) : config.embed_models
        configuredEmbedModels.value = Array.isArray(models) ? models : []
      } catch { configuredEmbedModels.value = [] }
    }
    // 如果没有配置，使用默认
    if (configuredEmbedModels.value.length === 0 && embedConfig.model) {
      configuredEmbedModels.value = [{
        id: 'default',
        name: embedConfig.model,
        modelId: embedConfig.model,
        provider: embedConfig.apiKey ? 'api' : 'local',
        dimension: 768,
        isDefault: true
      }]
    }
  } catch { /* ignore */ }
}

// 重置嵌入模型表单
function resetEmbedForm() {
  embedModelForm.name = ''
  embedModelForm.provider = 'api'
  embedModelForm.modelId = ''
  embedModelForm.dimension = 768
  embedModelForm.apiKey = ''
  embedModelForm.baseUrl = ''
}

// 添加嵌入模型
async function addEmbedModel() {
  if (!embedModelForm.name || !embedModelForm.modelId) {
    ElMessage.warning('请填写必要信息')
    return
  }
  savingEmbed.value = true
  try {
    const newModel = {
      id: Date.now().toString(),
      name: embedModelForm.name,
      modelId: embedModelForm.modelId,
      provider: embedModelForm.provider,
      dimension: embedModelForm.dimension,
      apiKey: embedModelForm.apiKey,
      baseUrl: embedModelForm.baseUrl,
      isDefault: configuredEmbedModels.value.length === 0
    }
    configuredEmbedModels.value.push(newModel)
    // 保存到后端
    await systemAPI.updateConfig({ embed_models: JSON.stringify(configuredEmbedModels.value) })
    ElMessage.success('嵌入模型已添加')
    showAddEmbedModel.value = false
    resetEmbedForm()
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    savingEmbed.value = false
  }
}

// 设置默认嵌入模型
async function setDefaultEmbedModel(row: any) {
  configuredEmbedModels.value.forEach(m => m.isDefault = false)
  row.isDefault = true
  try {
    await systemAPI.updateConfig({ embed_models: JSON.stringify(configuredEmbedModels.value) })
    ElMessage.success('已设为默认')
  } catch (e: any) {
    ElMessage.error(e.message || '设置失败')
  }
}

// 删除嵌入模型
async function deleteEmbedModel(row: any) {
  try {
    configuredEmbedModels.value = configuredEmbedModels.value.filter(m => m.id !== row.id)
    await systemAPI.updateConfig({ embed_models: JSON.stringify(configuredEmbedModels.value) })
    ElMessage.success('已删除')
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}

// 加载已配置的重排模型
async function loadConfiguredRerankModels() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.rerank_models) {
      try {
        const models = typeof config.rerank_models === 'string' ? JSON.parse(config.rerank_models) : config.rerank_models
        configuredRerankModels.value = Array.isArray(models) ? models : []
      } catch { configuredRerankModels.value = [] }
    }
  } catch { /* ignore */ }
}

// 重置重排模型表单
function resetRerankForm() {
  rerankModelForm.name = ''
  rerankModelForm.modelId = ''
  rerankModelForm.apiKey = ''
  rerankModelForm.baseUrl = ''
}

// 添加重排模型
async function addRerankModel() {
  if (!rerankModelForm.name || !rerankModelForm.modelId) {
    ElMessage.warning('请填写必要信息')
    return
  }
  savingRerank.value = true
  try {
    const newModel = {
      id: Date.now().toString(),
      name: rerankModelForm.name,
      modelId: rerankModelForm.modelId,
      apiKey: rerankModelForm.apiKey,
      baseUrl: rerankModelForm.baseUrl,
      isDefault: configuredRerankModels.value.length === 0
    }
    configuredRerankModels.value.push(newModel)
    await systemAPI.updateConfig({ rerank_models: JSON.stringify(configuredRerankModels.value) })
    ElMessage.success('重排模型已添加')
    showAddRerankModel.value = false
    resetRerankForm()
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    savingRerank.value = false
  }
}

// 设置默认重排模型
async function setDefaultRerankModel(row: any) {
  configuredRerankModels.value.forEach(m => m.isDefault = false)
  row.isDefault = true
  try {
    await systemAPI.updateConfig({ rerank_models: JSON.stringify(configuredRerankModels.value) })
    ElMessage.success('已设为默认')
  } catch (e: any) {
    ElMessage.error(e.message || '设置失败')
  }
}

// 删除重排模型
async function deleteRerankModel(row: any) {
  try {
    configuredRerankModels.value = configuredRerankModels.value.filter(m => m.id !== row.id)
    await systemAPI.updateConfig({ rerank_models: JSON.stringify(configuredRerankModels.value) })
    ElMessage.success('已删除')
  } catch (e: any) {
    ElMessage.error(e.message || '删除失败')
  }
}'''

if old_save_embed in content:
    content = content.replace(old_save_embed, new_methods)
    print("[OK] 嵌入/重排模型方法已添加")

# 4. 在 onMounted 中加载配置
old_mount = '''onMounted(async () => {
  await Promise.all([
    loadProviders(),
    loadConfiguredModels(),
    loadServicesStatus(),
    loadEmbedModels(),
    loadBasicSettings(),
    loadModuleAISettings(),
    loadOCRConfig(),
    loadEmbedConfig(),
  ])
})'''

new_mount = '''onMounted(async () => {
  await Promise.all([
    loadProviders(),
    loadConfiguredModels(),
    loadServicesStatus(),
    loadEmbedModels(),
    loadBasicSettings(),
    loadModuleAISettings(),
    loadOCRConfig(),
    loadEmbedConfig(),
    loadConfiguredEmbedModels(),
    loadConfiguredRerankModels(),
  ])
})'''

if old_mount in content:
    content = content.replace(old_mount, new_mount)
    print("[OK] onMounted 已更新")

# 保存文件
with open(settings_path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print("\nSettings.vue 修复完成！")