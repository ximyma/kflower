<template>
  <div class="system-settings">
    <!-- 隐藏的OCR测试文件输入 -->
    <input
      ref="ocrTestInput"
      type="file"
      accept="image/*"
      style="display:none"
      @change="onOCRTestFileSelected"
    />
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 基本设置 -->
      <el-tab-pane label="基本设置" name="basic">
        <el-card>
          <template #header><span>平台基本设置</span></template>
          <el-form :model="basicSettings" label-width="120px">
            <el-form-item label="平台名称">
              <el-input v-model="basicSettings.platformName" placeholder="请输入平台名称" />
            </el-form-item>
            <el-form-item label="平台描述">
              <el-input v-model="basicSettings.description" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- AI 配置 -->
      <el-tab-pane label="AI 配置" name="ai">
        <el-card>
          <template #header><span>AI 大模型配置</span></template>
          <el-alert title="配置说明" description="配置 AI 模型 API Key，支持完整参数调优和多模型管理。" type="info" show-icon :closable="false" style="margin-bottom:16px" />

          <!-- 已配置模型 -->
          <div class="model-list-section">
            <div class="section-header">
              <span class="section-title">已配置模型</span>
              <el-button type="primary" size="small" @click="showAddModel = true">
                <el-icon><Plus /></el-icon> 添加模型
              </el-button>
            </div>
            <el-empty v-if="configuredModels.length === 0" description="暂无配置，点击添加" />
            <el-table v-else :data="configuredModels" border stripe style="margin-top:12px">
              <el-table-column label="服务商" width="110">
                <template #default="{ row }"><el-tag size="small">{{ getProviderName(row.provider) }}</el-tag></template>
              </el-table-column>
              <el-table-column label="模型" prop="modelName" min-width="180" show-overflow-tooltip />
              <el-table-column label="模型ID" prop="modelId" min-width="200" show-overflow-tooltip />
              <el-table-column label="默认" width="70">
                <template #default="{ row }">
                  <el-tag :type="row.isDefault ? 'success' : 'info'" size="small">{{ row.isDefault ? '是' : '否' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button size="small" text type="primary" @click="editModel(row)">编辑</el-button>
                  <el-button size="small" text type="danger" @click="deleteModel(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <el-divider />

          <!-- 添加/编辑模型 -->
          <div class="model-form-section">
            <div class="section-title">{{ editingModel ? '编辑模型' : '添加新模型' }}</div>
            <el-form :model="modelForm" label-width="100px" style="max-width:700px;margin-top:12px">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="服务商" required>
                    <el-select v-model="modelForm.provider" style="width:100%" @change="onProviderChange">
                      <el-option v-for="p in allProviders" :key="p.id" :label="p.name" :value="p.id">
                        <span>{{ p.name }}</span>
                        <span v-if="p.no_api_key" style="color:#67c23a;margin-left:8px;font-size:12px">本地</span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="'API Key'" :required="!isLocalProvider">
                    <el-input v-model="modelForm.apiKey" type="password" show-password :placeholder="isLocalProvider ? '本地服务无需 API Key' : '输入 API Key'" :disabled="isLocalProvider" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="Base URL">
                    <el-input v-model="modelForm.baseUrl" placeholder="留空使用默认" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="显示名称">
                    <el-input v-model="modelForm.modelName" placeholder="自定义名称（可选）" />
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 模型参数 -->
              <div class="params-header" @click="showAdvanced = !showAdvanced">
                <span>模型参数</span>
                <el-icon><component :is="showAdvanced ? 'ArrowUp' : 'ArrowDown'" /></el-icon>
              </div>
              <div v-if="showAdvanced" class="params-grid">
                <el-form-item label="Temperature">
                  <el-slider v-model="modelForm.temperature" :min="0" :max="2" :step="0.1" show-input />
                  <div class="param-tip">控制随机性，越高越有创造性（0-2）</div>
                </el-form-item>
                <el-form-item label="Max Tokens">
                  <el-input-number v-model="modelForm.maxTokens" :min="256" :max="128000" :step="256" />
                  <div class="param-tip">最大输出 token 数</div>
                </el-form-item>
                <el-form-item label="Top P">
                  <el-slider v-model="modelForm.topP" :min="0" :max="1" :step="0.05" show-input />
                  <div class="param-tip">Nucleus 采样阈值（0-1）</div>
                </el-form-item>
                <el-form-item label="Top K">
                  <el-input-number v-model="modelForm.topK" :min="1" :max="100" />
                  <div class="param-tip">Top-K 采样数量</div>
                </el-form-item>
                <el-form-item label="Frequency Penalty">
                  <el-slider v-model="modelForm.frequencyPenalty" :min="-2" :max="2" :step="0.1" show-input />
                  <div class="param-tip">减少重复词（-2到2）</div>
                </el-form-item>
                <el-form-item label="Presence Penalty">
                  <el-slider v-model="modelForm.presencePenalty" :min="-2" :max="2" :step="0.1" show-input />
                  <div class="param-tip">鼓励新话题（-2到2）</div>
                </el-form-item>
                <el-form-item label="Timeout">
                  <el-input-number v-model="modelForm.timeout" :min="10" :max="600" :step="10" />
                  <div class="param-tip">请求超时（秒）</div>
                </el-form-item>
                <el-form-item label="Context Window">
                  <el-input-number v-model="modelForm.contextWindow" :min="1024" :max="1000000" :step="1024" />
                  <div class="param-tip">上下文窗口大小（token）</div>
                </el-form-item>
              </div>

              <el-form-item>
                <el-button type="primary" @click="fetchModels" :loading="fetchingModels" plain>获取模型列表</el-button>
              </el-form-item>

              <!-- 模型选择 -->
              <div class="model-select">
                <el-form-item label="选择模型" required>
                  <el-select v-model="modelForm.modelId" filterable allow-create default-first-option placeholder="选择、搜索或输入模型ID" style="width:100%">
                    <el-option v-for="m in availableModels" :key="m.id" :label="m.name || m.id" :value="m.id">
                      <span>{{ m.name || m.id }}</span>
                      <span v-if="m.local" style="color:#67c23a;margin-left:8px;font-size:12px">本地</span>
                      <span v-if="m.recommended" style="color:#409eff;margin-left:8px;font-size:12px">推荐</span>
                    </el-option>
                  </el-select>
                  <div class="param-tip" v-if="availableModels.length === 0">点击"获取模型列表"获取可用模型，或直接输入模型ID（如 qwen2.5:7b）</div>
                </el-form-item>
              </div>

              <el-form-item>
                <el-button type="primary" @click="saveModelConfig" :loading="saving">{{ editingModel ? '更新' : '添加' }}配置</el-button>
                <el-button @click="testConnection" :loading="testing">测试连接</el-button>
                <el-button @click="resetForm" plain>重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 本地服务配置 -->
      <el-tab-pane label="本地服务" name="local">
        <el-card>
          <template #header><span>本地 AI 服务配置</span></template>

          <!-- 服务状态 -->
          <div class="service-status">
            <el-row :gutter="16">
              <el-col :span="8">
                <div class="status-card" :class="servicesStatus.ocr?.available ? 'success' : 'warning'">
                  <el-icon :size="32"><Picture /></el-icon>
                  <div class="status-info">
                    <div class="status-name">Tesseract OCR</div>
                    <div class="status-desc">{{ servicesStatus.ocr?.available ? '已就绪' : '未安装' }}</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="status-card" :class="servicesStatus.jieba?.available ? 'success' : 'warning'">
                  <el-icon :size="32"><Document /></el-icon>
                  <div class="status-info">
                    <div class="status-name">Jieba 分词</div>
                    <div class="status-desc">{{ servicesStatus.jieba?.available ? '已就绪' : '未安装' }}</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="status-card" :class="servicesStatus.embedding?.configured ? 'success' : 'warning'">
                  <el-icon :size="32"><Grid /></el-icon>
                  <div class="status-info">
                    <div class="status-name">嵌入向量</div>
                    <div class="status-desc">{{ servicesStatus.embedding?.configured ? '已配置' : '未配置' }}</div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>

          <el-divider />

          <!-- OCR 配置 -->
          <div class="config-section">
            <div class="section-title">OCR 文字识别</div>
            <el-form :model="ocrConfig" label-width="130px" style="max-width:600px;margin-top:12px">
              <el-form-item label="Tesseract 路径">
                <el-input v-model="ocrConfig.tesseractPath" placeholder="D:\Tesseract-OCR\tesseract.exe" />
              </el-form-item>
              <el-form-item label="默认语言">
                <el-select v-model="ocrConfig.lang" style="width:100%">
                  <el-option label="简体中文+英文" value="chi_sim+eng" />
                  <el-option label="简体中文" value="chi_sim" />
                  <el-option label="英文" value="eng" />
                  <el-option label="繁体中文" value="chi_tra" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveOCRConfig" :loading="savingOCR">保存</el-button>
                <el-button @click="testOCR" :loading="testingOCR">测试 OCR</el-button>
              </el-form-item>
            </el-form>
          </div>

          <el-divider />

          <!-- 嵌入向量模型管理 -->
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
              <el-table-column label="操作" width="200">
                <template #default="{ row }">
                  <el-button size="small" text type="success" @click="testRerankModel(row)">测试</el-button>
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
                <el-form-item label="本地模型路径">
                  <el-input v-model="rerankModelForm.modelPath" placeholder="本地模型路径（如：E:\models\bge-reranker-v2-m3）" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showAddRerankModel = false">取消</el-button>
                <el-button type="primary" @click="addRerankModel" :loading="savingRerank">保存</el-button>
              </template>
            </el-dialog>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 模块 AI 设置 -->
      <el-tab-pane label="模块AI设置" name="module">
        <el-card>
          <template #header><span>各模块 AI 模型配置</span></template>
          <el-alert title="说明" description="为不同功能模块配置专用的 AI 模型。每个模块可使用不同的模型。" type="info" show-icon :closable="false" style="margin-bottom:16px" />

          <el-form :model="moduleAISettings" label-width="160px" style="max-width:700px">
            <el-form-item label="智能助手">
              <el-select v-model="moduleAISettings.chatGeneral" placeholder="选择模型" style="width:100%" @change="saveModuleAI">
                <el-option v-for="m in configuredModels" :key="m.id" :label="`${m.modelName || m.modelId}`" :value="m.modelId">
                  <span>{{ m.modelName || m.modelId }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="模板设计 AI">
              <el-select v-model="moduleAISettings.chatTemplate" placeholder="选择模型" style="width:100%" @change="saveModuleAI">
                <el-option v-for="m in configuredModels" :key="m.id" :label="`${m.modelName || m.modelId}`" :value="m.modelId">
                  <span>{{ m.modelName || m.modelId }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="流程设计 AI">
              <el-select v-model="moduleAISettings.chatWorkflow" placeholder="选择模型" style="width:100%" @change="saveModuleAI">
                <el-option v-for="m in configuredModels" :key="m.id" :label="`${m.modelName || m.modelId}`" :value="m.modelId">
                  <span>{{ m.modelName || m.modelId }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="数据分析 AI">
              <el-select v-model="moduleAISettings.chatAnalytics" placeholder="选择模型" style="width:100%" @change="saveModuleAI">
                <el-option v-for="m in configuredModels" :key="m.id" :label="`${m.modelName || m.modelId}`" :value="m.modelId">
                  <span>{{ m.modelName || m.modelId }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="知识库 RAG">
              <el-select v-model="moduleAISettings.ragModel" placeholder="选择模型" style="width:100%" @change="saveModuleAI">
                <el-option v-for="m in configuredModels" :key="m.id" :label="`${m.modelName || m.modelId}`" :value="m.modelId">
                  <span>{{ m.modelName || m.modelId }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="附件处理（OCR/分词）">
              <el-select v-model="moduleAISettings.processingModel" placeholder="选择模型" style="width:100%" @change="saveModuleAI">
                <el-option v-for="m in configuredModels" :key="m.id" :label="`${m.modelName || m.modelId}`" :value="m.modelId">
                  <span>{{ m.modelName || m.modelId }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveModuleAI" :loading="savingModule">保存模块设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 关于 -->
      <el-tab-pane label="关于系统" name="about">
        <el-card>
          <template #header><span>关于 Kflower</span></template>
          <div class="about-info">
            <div class="about-logo"><div class="logo-placeholder">K</div></div>
            <div class="about-text">
              <h2>Kflower 企业智能管理平台</h2>
              <p class="version">版本 v1.0.0</p>
              <p class="description">面向政府和企事业单位的 AI 智能体平台</p>
              <div class="tech-stack">
                <el-tag v-for="tech in techStack" :key="tech" type="info">{{ tech }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture, Document, Grid, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { systemAPI, localAIAPI } from '../../api'

const activeTab = ref('ai')
const showAddModel = ref(false)
const showAdvanced = ref(false)
const saving = ref(false)
const testing = ref(false)
const fetchingModels = ref(false)
const savingOCR = ref(false)
const savingEmbed = ref(false)
const savingModule = ref(false)
const testingOCR = ref(false)
const testingEmbed = ref(false)

const allProviders = ref<any[]>([])
const availableModels = ref<any[]>([])
const configuredModels = ref<any[]>([])
const editingModel = ref<string | null>(null)

const isLocalProvider = computed(() => {
  const p = allProviders.value.find(x => x.id === modelForm.provider)
  return !!p?.no_api_key
})

const modelForm = reactive({
  id: '', provider: 'siliconflow', apiKey: '', baseUrl: '', modelId: '', modelName: '',
  temperature: 0.7, maxTokens: 4096, topP: 0.95, topK: 50,
  frequencyPenalty: 0, presencePenalty: 0, timeout: 120, contextWindow: 32768
})

const servicesStatus = ref<any>({})
const ocrConfig = reactive({ tesseractPath: 'D:\\Tesseract-OCR\\tesseract.exe', lang: 'chi_sim+eng' })
// 嵌入模型配置
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
  name: '', modelId: '', apiKey: '', baseUrl: '', modelPath: ''
})
const rerankModelOptions = ref([
  { value: 'BAAI/bge-reranker-v2-m3', label: 'BGE-reranker-v2-m3', desc: '多语言重排' },
  { value: 'BAAI/bge-reranker-large', label: 'BGE-reranker-large', desc: '大型重排' },
  { value: 'BAAI/bge-reranker-base', label: 'BGE-reranker-base', desc: '基础重排' },
  { value: 'cohere/rerank-english-v3.0', label: 'Cohere Rerank English', desc: '英文重排' },
  { value: 'cohere/rerank-multilingual-v3.0', label: 'Cohere Rerank Multi', desc: '多语言重排' },
])
const savingRerank = ref(false)

// 嵌入模型列表（从后端动态加载）
const embedApiModels = ref([
  { value: 'text-embedding-v2', label: 'text-embedding-v2', desc: 'DashScope 1536维' },
  { value: 'text-embedding-v3', label: 'text-embedding-v3', desc: 'DashScope 1024维' },
  { value: 'text-embedding-3-small', label: 'text-embedding-3-small', desc: 'OpenAI 1536维' },
  { value: 'text-embedding-3-large', label: 'text-embedding-3-large', desc: 'OpenAI 3072维' },
])
const embedLocalModels = ref<any[]>([])
const embedSTAvailable = ref(false)

async function loadEmbedModels() {
  try {
    const res: any = await systemAPI.listEmbeddingModels()
    if (res.data?.models) {
      const models = res.data.models
      embedSTAvailable.value = !!res.data.st_available
      const apiModels = models.filter((m: any) => m.provider === 'api')
      const localModels = models.filter((m: any) => m.provider === 'local')
      if (apiModels.length) {
        embedApiModels.value = apiModels.map((m: any) => ({
          value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`
        }))
      }
      if (localModels.length) {
        embedLocalModels.value = localModels.map((m: any) => ({
          value: m.name, label: m.name, desc: `${m.description} ${m.dimension}维`, available: m.available
        }))
      }
    }
  } catch { /* 使用默认列表 */ }
}

const moduleAISettings = reactive({
  chatGeneral: '', chatTemplate: '', chatWorkflow: '', chatAnalytics: '',
  ragModel: '', processingModel: ''
})

const basicSettings = reactive({ platformName: 'Kflower', description: '' })
const techStack = ['Vue 3', 'FastAPI', 'TypeScript', 'Element Plus', 'OCR', 'Embedding']

async function loadProviders() {
  try {
    const res: any = await systemAPI.listAIProviders()
    allProviders.value = res.data?.providers || []
  } catch (e) { console.error('加载提供商失败', e) }
}

async function loadConfiguredModels() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    const models: any[] = []
    if (config.ai_models) {
      try { models.push(...(typeof config.ai_models === 'string' ? JSON.parse(config.ai_models) : config.ai_models)) } catch {}
    }
    
    // 加载 OCR 配置
    if (config.ocr_tesseract_path) {
      ocrConfig.tesseractPath = config.ocr_tesseract_path
    }
    if (config.ocr_lang) {
      ocrConfig.lang = config.ocr_lang
    }
    
    // 加载嵌入模型配置
    if (config.embedding_api_key) {
      embedConfig.apiKey = config.embedding_api_key
    }
    if (config.embedding_api_base) {
      embedConfig.apiBase = config.embedding_api_base
    }
    if (config.embedding_model) {
      embedConfig.model = config.embedding_model
    }
    
    if (!models.length && config.ai_api_key) {
      models.push({ id: 'default', provider: config.ai_provider || 'siliconflow', modelId: config.ai_model || '',
        modelName: config.ai_model || '', apiKey: config.ai_api_key, baseUrl: config.ai_base_url || '',
        isDefault: true, configured: true, ...(config.ai_params || {}) })
    }
    configuredModels.value = models
    // 加载模块设置
    if (config.module_ai_settings) {
      try { Object.assign(moduleAISettings, typeof config.module_ai_settings === 'string' ? JSON.parse(config.module_ai_settings) : config.module_ai_settings) } catch {}
    }
  } catch (e) { console.error('加载模型失败', e) }
}

async function loadServicesStatus() {
  try {
    const res: any = await localAIAPI.servicesStatus()
    servicesStatus.value = res.data || {}
    if (res.data?.ocr?.tesseract_path) ocrConfig.tesseractPath = res.data.ocr.tesseract_path
  } catch (e) { console.error('加载服务状态失败', e) }
}

function onProviderChange() {
  const p = allProviders.value.find(x => x.id === modelForm.provider)
  if (p) modelForm.baseUrl = p.default_base_url || ''
  // 本地服务无需 API Key，清空并自动获取模型列表
  if (p?.no_api_key) {
    modelForm.apiKey = ''
    // 自动获取模型列表
    fetchModels()
  }
  availableModels.value = []
  modelForm.modelId = ''
}

async function fetchModels() {
  // 本地服务无需 API Key，其他服务商必须
  if (!isLocalProvider.value && !modelForm.apiKey) {
    ElMessage.warning('请先输入 API Key')
    return
  }
  fetchingModels.value = true
  try {
    const res: any = await systemAPI.fetchAIModels(modelForm.provider, modelForm.apiKey || '', modelForm.baseUrl)
    availableModels.value = res.data?.models || []
    if (res.data?.from_api) {
      ElMessage.success(`获取到 ${res.data.count} 个模型`)
    } else if (res.success === false) {
      // API 失败但仍可能有 fallback 模型
      if (availableModels.value.length > 0) {
        ElMessage.warning('获取模型列表失败，使用预设模型列表')
      } else {
        ElMessage.error(res.message || '获取模型列表失败')
      }
    } else {
      ElMessage.info('使用预设模型列表')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '获取失败')
  }
  finally { fetchingModels.value = false }
}

function editModel(row: any) {
  editingModel.value = row.id
  Object.assign(modelForm, row)
  showAdvanced.value = true
  fetchModels()
}

async function saveModelConfig() {
  // 本地服务无需 API Key
  if (!isLocalProvider.value && !modelForm.apiKey) { ElMessage.warning('请填写 API Key'); return }
  if (!modelForm.modelId) { ElMessage.warning('请选择模型'); return }
  saving.value = true
  try {
    const params = {
      temperature: modelForm.temperature, max_tokens: modelForm.maxTokens,
      top_p: modelForm.topP, top_k: modelForm.topK,
      frequency_penalty: modelForm.frequencyPenalty, presence_penalty: modelForm.presencePenalty,
      timeout: modelForm.timeout, context_window: modelForm.contextWindow
    }
    const newModel = {
      id: editingModel.value || 'model_' + Date.now(),
      provider: modelForm.provider, apiKey: modelForm.apiKey, baseUrl: modelForm.baseUrl,
      modelId: modelForm.modelId, modelName: modelForm.modelName || modelForm.modelId,
      isDefault: editingModel.value ? configuredModels.value.find(m => m.id === editingModel.value)?.isDefault : configuredModels.value.length === 0,
      configured: true, params
    }
    if (editingModel.value) {
      const idx = configuredModels.value.findIndex(m => m.id === editingModel.value)
      if (idx >= 0) configuredModels.value[idx] = newModel
    } else {
      configuredModels.value.push(newModel)
    }
    await systemAPI.saveConfig({
      ai_models: configuredModels.value,
      ai_provider: modelForm.provider, ai_api_key: modelForm.apiKey,
      ai_model: modelForm.modelId, ai_base_url: modelForm.baseUrl,
      ai_params: params
    })
    ElMessage.success(editingModel.value ? '模型已更新' : '模型已添加')
    resetForm()
  } catch (e: any) { ElMessage.error(e.message || '保存失败') }
  finally { saving.value = false }
}

async function deleteModel(row: any) {
  configuredModels.value = configuredModels.value.filter(m => m.id !== row.id)
  try {
    await systemAPI.saveConfig({ ai_models: configuredModels.value })
    ElMessage.success('已删除')
  } catch { ElMessage.error('删除失败') }
}

async function testConnection() {
  if (!isLocalProvider.value && !modelForm.apiKey) { ElMessage.warning('请先填写 API Key'); return }
  if (!modelForm.modelId) { ElMessage.warning('请先选择模型'); return }
  testing.value = true
  try {
    await systemAPI.saveConfig({
      ai_provider: modelForm.provider, ai_api_key: modelForm.apiKey,
      ai_model: modelForm.modelId, ai_base_url: modelForm.baseUrl
    })
    const res: any = await systemAPI.testAI()
    ElMessage[res.success ? 'success' : 'error'](res.message || (res.success ? '连接成功' : '连接失败'))
  } catch (e: any) { ElMessage.error(e.message || '测试失败') }
  finally { testing.value = false }
}

function resetForm() {
  editingModel.value = null
  modelForm.id = ''; modelForm.apiKey = ''; modelForm.baseUrl = ''
  modelForm.modelId = ''; modelForm.modelName = ''
  modelForm.temperature = 0.7; modelForm.maxTokens = 4096
  modelForm.topP = 0.95; modelForm.topK = 50
  modelForm.frequencyPenalty = 0; modelForm.presencePenalty = 0
  modelForm.timeout = 120; modelForm.contextWindow = 32768
  availableModels.value = []
  showAdvanced.value = false
}

function getProviderName(id: string) {
  return allProviders.value.find(p => p.id === id)?.name || id
}

async function saveOCRConfig() {
  savingOCR.value = true
  try {
    // 保存到系统配置
    await systemAPI.saveConfig({ ocr_tesseract_path: ocrConfig.tesseractPath, ocr_lang: ocrConfig.lang })
    // 同时调用后端API保存并刷新配置
    await localAIAPI.ocrConfigure(ocrConfig.tesseractPath, ocrConfig.lang)
    ElMessage.success('OCR 配置已保存')
  } catch (e: any) { ElMessage.error(e.message || '保存失败') }
  finally { savingOCR.value = false }
}

// OCR测试用的隐藏文件上传
const ocrTestInput = ref<HTMLInputElement|null>(null)
function triggerOCRTest() {
  ocrTestInput.value?.click()
}
async function onOCRTestFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  
  testingOCR.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('lang', ocrConfig.lang)
    
    const res = await (window as any).fetch('/api/v1/local-ai/ocr/text', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: formData
    })
    const json = await res.json()
    
    if (json.success) {
      ElMessage.success('OCR 识别成功！')
      // 显示识别结果
      const preview = json.data.text?.substring(0, 200) + (json.data.text?.length > 200 ? '...' : '')
      ElMessageBox.alert(`识别结果：\n${preview || '(无文字)'}\n\n置信度：${(json.data.confidence * 100).toFixed(1)}%`, 'OCR 识别结果', {
        confirmButtonText: '确定',
        customClass: 'ocr-result-dialog'
      })
    } else {
      ElMessage.error('OCR 识别失败：' + (json.message || json.detail || '未知错误'))
    }
  } catch (e: any) {
    ElMessage.error('OCR 测试失败：' + (e.message || '请检查 Tesseract 路径配置是否正确'))
  } finally {
    testingOCR.value = false
    input.value = ''
  }
}

async function testOCR() {
  // 触发文件选择
  triggerOCRTest()
}

async function loadEmbedConfig() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.embedding_api_key) embedConfig.apiKey = config.embedding_api_key
    if (config.embedding_base_url) embedConfig.apiBase = config.embedding_base_url
    if (config.embedding_model) embedConfig.model = config.embedding_model
  } catch { /* ignore */ }
}

async function loadBasicSettings() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.platform_name) basicSettings.platformName = config.platform_name
    if (config.platform_description) basicSettings.description = config.platform_description
  } catch { /* ignore */ }
}

async function loadModuleAISettings() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.module_ai_settings) {
      const settings = typeof config.module_ai_settings === 'string' 
        ? JSON.parse(config.module_ai_settings) 
        : config.module_ai_settings
      Object.assign(moduleAISettings, settings)
    }
  } catch { /* ignore */ }
}

async function loadOCRConfig() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.ocr_tesseract_path) ocrConfig.tesseractPath = config.ocr_tesseract_path
    if (config.ocr_lang) ocrConfig.lang = config.ocr_lang
  } catch { /* ignore */ }
}

async function saveBasicSettings() {
  saving.value = true
  try {
    await systemAPI.saveConfig({ platform_name: basicSettings.platformName, platform_description: basicSettings.description })
    ElMessage.success('基本设置已保存')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveEmbedConfig() {
  savingEmbed.value = true
  try {
    await localAIAPI.embedConfig({ apiKey: embedConfig.apiKey, apiBase: embedConfig.apiBase, model: embedConfig.model })
    await systemAPI.saveConfig({ embedding_api_key: embedConfig.apiKey, embedding_model: embedConfig.model })
    ElMessage.success('嵌入配置已保存')
  } catch (e: any) { ElMessage.error(e.message || '保存失败') }
  finally { savingEmbed.value = false }
}

async function testEmbed() {
  testingEmbed.value = true
  try {
    const res: any = await localAIAPI.textSummary('这是一个测试文本，用于验证嵌入向量服务是否正常工作。')
    ElMessage[res.success ? 'success' : 'error'](res.success ? `嵌入服务正常：${res.summary?.substring(0, 50)}` : '嵌入服务测试失败')
  } catch (e: any) { ElMessage.error(e.message || '测试失败') }
  finally { testingEmbed.value = false }
}

async function saveModuleAI() {
  savingModule.value = true
  try {
    await systemAPI.saveConfig({ module_ai_settings: JSON.stringify(moduleAISettings) })
    ElMessage.success('模块 AI 设置已保存')
  } catch (e: any) { ElMessage.error(e.message || '保存失败') }
  finally { savingModule.value = false }
}

// 加载已配置的 Embed 模型
async function loadConfiguredEmbedModels() {
  try {
    // 使用新的 API 获取模型列表
    const res: any = await localAIAPI.listEmbedModels()
    if (res && res.success !== false && res.data?.models) {
      configuredEmbedModels.value = res.data.models.map((m: any) => ({
        ...m,
        id: m.model || m.name,
        modelId: m.model,
        isDefault: m.is_default || m.isDefault,
      }))
      embedSTAvailable.value = res.data.st_available || false
    } else {
      // 回退到旧的加载方式
      const configRes: any = await systemAPI.getConfig()
      const config = configRes.data || {}
      if (config.embedding_models) {
        configuredEmbedModels.value = typeof config.embedding_models === 'string' 
          ? JSON.parse(config.embedding_models) 
          : config.embedding_models
      }
    }
  } catch { /* ignore */ }
}

// 加载已配置的 Rerank 模型
async function loadConfiguredRerankModels() {
  try {
    const res: any = await systemAPI.getConfig()
    const config = res.data || {}
    if (config.rerank_models) {
      configuredRerankModels.value = typeof config.rerank_models === 'string' 
        ? JSON.parse(config.rerank_models) 
        : config.rerank_models
    }
    // 同时获取后端提供的预设 Rerank 模型列表
    await loadRerankModelOptions()
  } catch { /* ignore */ }
}

// 加载 Rerank 模型选项（从后端获取）
async function loadRerankModelOptions() {
  try {
    const res: any = await systemAPI.listRerankModels()
    if (res && res.success !== false && res.data?.models) {
      // 更新预设模型列表（添加到表单选项）
      const presets = res.data.models.map((m: any) => ({
        value: m.id,
        label: m.name || m.id,
        desc: m.description || `${m.provider} 模型`,
        provider: m.provider,
        is_preset: !m.is_custom,
      }))
      // 合并到现有选项（避免重复）
      for (const preset of presets) {
        if (!rerankModelOptions.value.find(o => o.value === preset.value)) {
          rerankModelOptions.value.push(preset)
        }
      }
    }
  } catch { /* ignore */ }
}

// 测试 Rerank 模型
async function testRerankModel(row?: any) {
  const modelId = row?.modelId || row?.model || configuredRerankModels.value[0]?.modelId
  if (!modelId) {
    ElMessage.warning('请先添加 Rerank 模型')
    return
  }
  
  const loading = ElMessage({ message: '正在测试 Rerank 模型...', duration: 0 })
  try {
    const res: any = await systemAPI.testRerankModel(modelId)
    loading.close()
    if (res && res.success !== false) {
      ElMessage.success(`Rerank 模型测试成功！${res.message || ''}`)
    } else {
      ElMessage.error(res?.message || '测试失败')
    }
  } catch (e: any) {
    loading.close()
    ElMessage.error('测试失败：' + (e.message || '请检查模型配置'))
  }
}

// 添加 Embed 模型
async function addEmbedModel() {
  if (!embedModelForm.modelId) {
    ElMessage.warning('请输入模型ID')
    return
  }
  if (embedModelForm.provider === 'api' && !embedModelForm.apiKey) {
    ElMessage.warning('API 模型需要填写 API Key')
    return
  }
  
  try {
    const modelConfig = {
      name: embedModelForm.name,
      model: embedModelForm.modelId,
      provider: embedModelForm.provider,
      dimension: embedModelForm.dimension,
      api_key: embedModelForm.apiKey,
      api_base: embedModelForm.baseUrl || 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      description: ''
    }
    
    const res: any = await localAIAPI.addEmbedModel(modelConfig)
    if (res && res.success !== false) {
      ElMessage.success('嵌入模型已添加')
      showAddEmbedModel.value = false
      resetEmbedForm()
      await loadConfiguredEmbedModels()
    } else {
      ElMessage.error(res?.message || '添加失败')
    }
  } catch (e: any) {
    ElMessage.error('添加失败: ' + e.message)
  }
}

// 删除 Embed 模型
async function deleteEmbedModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除模型 "${row.name || row.modelId || row.model}" 吗？`, '确认删除', { type: 'warning' })
    const modelId = row.model || row.modelId || row.name
    const res: any = await localAIAPI.deleteEmbedModel(modelId)
    if (res && res.success !== false) {
      ElMessage.success('模型已删除')
      await loadConfiguredEmbedModels()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch { /* cancel */ }
}

// 设为默认 Embed 模型
async function setDefaultEmbedModel(row: any) {
  try {
    const modelId = row.model || row.modelId || row.name
    const res: any = await localAIAPI.setDefaultEmbedModel(modelId)
    if (res && res.success !== false) {
      ElMessage.success('已设为默认模型')
      await loadConfiguredEmbedModels()
    } else {
      ElMessage.error(res?.message || '设置失败')
    }
  } catch (e: any) {
    ElMessage.error('设置失败: ' + e.message)
  }
}

// 添加 Rerank 模型
async function addRerankModel() {
  if (!rerankModelForm.modelId) {
    ElMessage.warning('请输入模型ID')
    return
  }
  const model = { ...rerankModelForm, id: Date.now() }
  configuredRerankModels.value.push(model)
  await systemAPI.saveConfig({ rerank_models: JSON.stringify(configuredRerankModels.value) })
  ElMessage.success('重排模型已添加')
  showAddRerankModel.value = false
  resetRerankForm()
}

// 删除 Rerank 模型
async function deleteRerankModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除模型 "${row.name || row.modelId}" 吗？`, '确认删除', { type: 'warning' })
    configuredRerankModels.value = configuredRerankModels.value.filter(m => m.id !== row.id)
    await systemAPI.saveConfig({ rerank_models: JSON.stringify(configuredRerankModels.value) })
    ElMessage.success('模型已删除')
  } catch { /* cancel */ }
}

// 设为默认 Rerank 模型
async function setDefaultRerankModel(row: any) {
  configuredRerankModels.value.forEach(m => m.isDefault = false)
  const idx = configuredRerankModels.value.findIndex(m => m.id === row.id)
  if (idx > -1) {
    configuredRerankModels.value[idx].isDefault = true
  }
  await systemAPI.saveConfig({ rerank_models: JSON.stringify(configuredRerankModels.value) })
  ElMessage.success('已设为默认模型')
}

function resetEmbedForm() {
  embedModelForm.name = ''
  embedModelForm.provider = 'api'
  embedModelForm.modelId = ''
  embedModelForm.dimension = 768
  embedModelForm.apiKey = ''
  embedModelForm.baseUrl = ''
}

function resetRerankForm() {
  rerankModelForm.name = ''
  rerankModelForm.modelId = ''
  rerankModelForm.apiKey = ''
  rerankModelForm.baseUrl = ''
  rerankModelForm.modelPath = ''
}

onMounted(async () => {
  await Promise.all([
    loadProviders(), 
    loadConfiguredModels(), 
    loadServicesStatus(), 
    loadEmbedModels(),
    loadEmbedConfig(),
    loadBasicSettings(),
    loadModuleAISettings(),
    loadOCRConfig(),
    loadConfiguredEmbedModels(),
    loadConfiguredRerankModels(),
  ])
})
</script>

<style scoped lang="scss">
.system-settings { padding: 20px; }
.settings-tabs { background: white; padding: 20px; border-radius: 8px; }
.model-list-section, .model-form-section { margin-bottom: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.section-title { font-size: 15px; font-weight: 600; color: #303133; }
.params-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; cursor: pointer; color: #606266; }
.params-grid { background: #f5f7fa; padding: 16px; border-radius: 8px; margin: 12px 0; }
.param-tip { font-size: 12px; color: #999; margin-top: 4px; }
.model-select { margin-top: 12px; }
.service-status { margin-bottom: 16px; }
.status-card { display: flex; align-items: center; gap: 12px; padding: 16px; border-radius: 8px; background: #f5f7fa; border: 1px solid #ebeef5;
  &.success { border-color: #67c23a; background: #f0f9eb; }
  &.warning { border-color: #e6a23c; background: #fdf6ec; }
  .status-name { font-weight: 600; font-size: 14px; }
  .status-desc { font-size: 12px; color: #909399; }
}
.config-section { margin-bottom: 16px; }
.about-info { display: flex; gap: 40px; padding: 20px;
  .logo-placeholder { width: 80px; height: 80px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 40px; font-weight: bold; display: flex; align-items: center; justify-content: center; border-radius: 16px; }
  .about-text { h2 { margin: 0 0 8px; } .version { color: #409eff; margin: 0 0 12px; } .description { color: #666; margin: 0 0 12px; } }
  .tech-stack { display: flex; gap: 8px; flex-wrap: wrap; }
}
</style>
