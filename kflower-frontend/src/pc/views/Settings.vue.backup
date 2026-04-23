<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- AI配置（统一入口） -->
      <el-tab-pane label="AI配置" name="ai-models">
        <!-- AI配置状态总览 -->
        <el-card class="status-overview-card">
          <template #header>
            <div class="card-header">
              <span>🤖 AI 配置状态</span>
              <el-button size="small" @click="refreshConfigStatus" :loading="loadingConfigStatus">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </template>

          <!-- 正在加载 -->
          <div v-if="loadingConfigStatus && !aiConfigStatus" class="loading-state">
            <el-skeleton animated />
          </div>

          <!-- 状态概览行 -->
          <div v-else-if="aiConfigStatus" class="status-overview-row">
            <!-- 对话模型 -->
            <div class="status-card" :class="{ ready: aiConfigStatus.chat?.available, warn: !aiConfigStatus.chat?.available }">
              <div class="status-icon">
                <el-icon size="32" :color="aiConfigStatus.chat?.available ? '#67c23a' : '#e6a23c'">
                  <ChatDotRound v-if="aiConfigStatus.chat?.available" />
                  <WarningFilled v-else />
                </el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">对话模型</div>
                <div class="status-desc">{{ aiConfigStatus.chat?.available ? (aiConfigStatus.chat.default_model?.name || aiConfigStatus.chat.default_model?.id || '已配置') : '未配置' }}</div>
                <div class="status-provider" v-if="aiConfigStatus.chat?.current_provider">
                  {{ aiConfigStatus.chat.current_provider }}
                </div>
              </div>
            </div>

            <!-- Embedding模型 -->
            <div class="status-card" :class="{ ready: aiConfigStatus.embedding?.available, warn: !aiConfigStatus.embedding?.available }">
              <div class="status-icon">
                <el-icon size="32" :color="aiConfigStatus.embedding?.available ? '#67c23a' : '#909399'">
                  <Connection v-if="aiConfigStatus.embedding?.available" />
                  <CircleCloseFilled v-else-if="!aiConfigStatus.embedding?.st_available" />
                  <WarningFilled v-else />
                </el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">Embedding</div>
                <div class="status-desc">
                  {{ aiConfigStatus.embedding?.available
                    ? (aiConfigStatus.embedding.current_model || '未知')
                    : aiConfigStatus.embedding?.st_available
                      ? 'API未配置'
                      : 'sentence-transformers未安装' }}
                </div>
                <div class="status-provider" v-if="aiConfigStatus.embedding?.current_provider">
                  {{ aiConfigStatus.embedding.current_provider }}
                </div>
              </div>
            </div>

            <!-- Rerank模型 -->
            <div class="status-card" :class="{ ready: aiConfigStatus.rerank?.available }">
              <div class="status-icon">
                <el-icon size="32" :color="aiConfigStatus.rerank?.available ? '#67c23a' : '#909399'">
                  <Filter v-if="aiConfigStatus.rerank?.available" />
                  <CircleCloseFilled v-else />
                </el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">Rerank</div>
                <div class="status-desc">{{ aiConfigStatus.rerank?.available ? '已配置' : '未配置' }}</div>
              </div>
            </div>

            <!-- OCR -->
            <div class="status-card" :class="{ ready: aiConfigStatus.ocr?.available }">
              <div class="status-icon">
                <el-icon size="32" :color="aiConfigStatus.ocr?.available ? '#67c23a' : '#909399'">
                  <Picture v-if="aiConfigStatus.ocr?.available" />
                  <CircleCloseFilled v-else />
                </el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">OCR</div>
                <div class="status-desc">{{ aiConfigStatus.ocr?.available ? '已安装' : '未安装' }}</div>
              </div>
            </div>
          </div>

          <!-- 警告信息 -->
          <el-alert
            v-if="aiConfigStatus?.warnings?.length"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top:12px"
          >
            <template #title>
              <span>⚠️ 以下配置项需要完善：</span>
            </template>
            <template #default>
              <div v-for="(w, i) in aiConfigStatus.warnings" :key="i" style="margin-top:4px">{{ w }}</div>
            </template>
          </el-alert>
        </el-card>

        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI 模型配置</span>
              <el-button type="primary" size="small" @click="openAddModelDialog">
                <el-icon><Plus /></el-icon> 添加模型
              </el-button>
            </div>
          </template>
          
          <el-table :data="aiModels" style="width:100%" v-loading="loadingModels">
            <el-table-column prop="provider" label="供应商" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getProviderName(row.provider) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="modelId" label="模型ID" min-width="180">
              <template #default="{ row }">
                <span class="font-medium">{{ row.modelId }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="modelName" label="模型名称" width="150" />
            <el-table-column prop="baseUrl" label="API地址" min-width="200">
              <template #default="{ row }">
                <span class="text-mono" v-if="row.baseUrl">{{ row.baseUrl }}</span>
                <span class="text-muted" v-else>默认</span>
              </template>
            </el-table-column>
            <el-table-column prop="configured" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.configured ? 'success' : 'info'" size="small">
                  {{ row.configured ? '已配置' : '未配置' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="isDefault" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.isDefault" type="success" size="small">默认</el-tag>
                <el-tag v-else type="info" size="small">-</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="editModel(row)">编辑</el-button>
                <el-button type="danger" size="small" link @click="deleteModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 模块AI配置 -->
        <el-card style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>模块 AI 模型分配</span>
            </div>
          </template>
          <el-form label-width="140px">
            <el-form-item label="智能助手">
              <el-select v-model="moduleSettings.chatGeneral" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="模板设计">
              <el-select v-model="moduleSettings.chatTemplate" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="流程审批">
              <el-select v-model="moduleSettings.chatWorkflow" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="决策分析">
              <el-select v-model="moduleSettings.chatAnalytics" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="知识库">
              <el-select v-model="moduleSettings.ragModel" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item label="文档处理">
              <el-select v-model="moduleSettings.processingModel" style="width:300px" placeholder="选择模型">
                <el-option v-for="m in availableModelsForSelect" :key="m.modelId" :label="m.modelName || m.modelId" :value="m.modelId" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveModuleSettings">保存模块配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 本地模型配置 -->
      <el-tab-pane label="本地模型" name="local">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Ollama 本地模型配置</span>
              <el-button type="primary" size="small" @click="openAddLocalModelDialog">
                <el-icon><Plus /></el-icon> 添加连接
              </el-button>
            </div>
          </template>
          
          <el-table :data="localModels" style="width:100%" v-loading="loadingLocalModels">
            <el-table-column prop="name" label="连接名称" width="150">
              <template #default="{ row }">
                <span class="font-medium">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="url" label="API地址" min-width="220">
              <template #default="{ row }">
                <span class="text-mono">{{ row.url }}{{ row.apiPath || '/v1' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="defaultModel" label="默认模型" width="150">
              <template #default="{ row }">
                <el-tag v-if="row.defaultModel" size="small" type="success">{{ row.defaultModel }}</el-tag>
                <span v-else class="text-muted">未设置</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'connected' ? 'success' : 'info'" size="small">
                  {{ row.status === 'connected' ? '已连接' : '未连接' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="models" label="可用模型" min-width="180">
              <template #default="{ row }">
                <el-tag v-for="m in row.models?.slice(0, 2)" :key="m" size="small" style="margin-right:4px">{{ m }}</el-tag>
                <el-tag v-if="row.models?.length > 2" size="small">+{{ row.models.length - 2 }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="editLocalModel(row)">编辑</el-button>
                <el-button type="danger" size="small" link @click="deleteLocalModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        
        <el-card style="margin-top:16px">
          <template #header>
            <div class="card-header">
              <span>Rerank 模型配置</span>
              <el-button type="primary" size="small" @click="openAddRerankDialog">
                <el-icon><Plus /></el-icon> 添加 Rerank
              </el-button>
            </div>
          </template>
          
          <el-table :data="rerankModels" style="width:100%" v-loading="loadingRerank">
            <el-table-column prop="name" label="模型名称" width="200">
              <template #default="{ row }">
                <span class="font-medium">{{ row.name || row.model }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="model" label="模型ID" min-width="200">
              <template #default="{ row }">
                <span class="text-mono">{{ row.model }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="provider" label="服务商" width="150">
              <template #default="{ row }">
                <el-tag size="small">{{ row.provider || '本地' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="apiKey" label="API Key" width="200">
              <template #default="{ row }">
                <span v-if="row.apiKey">{{ row.apiKey.substring(0, 8) }}***</span>
                <span v-else class="text-muted">未配置</span>
              </template>
            </el-table-column>
            <el-table-column prop="enabled" label="启用" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.enabled" @change="toggleRerankModel(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="editRerankModel(row)">编辑</el-button>
                <el-button type="danger" size="small" link @click="deleteRerankModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <!-- Embedding配置 -->
      <el-tab-pane label="Embedding配置" name="embedding">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>向量嵌入模型配置</span>
              <el-button type="primary" size="small" @click="openAddEmbeddingDialog">
                <el-icon><Plus /></el-icon> 添加模型
              </el-button>
            </div>
          </template>
          
          <el-alert title="配置说明" description="支持添加本地模型和远程API模型。本地模型需要安装 sentence-transformers。API模型需要配置有效的API Key。" type="info" show-icon :closable="false" style="margin-bottom:16px" />
          
          <!-- 服务状态 -->
          <div class="embedding-status-row">
            <div class="status-item">
              <span class="status-label">sentence-transformers:</span>
              <el-tag :type="embeddingConfig.stAvailable ? 'success' : 'danger'" size="small">
                {{ embeddingConfig.stAvailable ? '已安装' : '未安装' }}
              </el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">当前模型:</span>
              <el-tag type="primary" size="small">{{ embeddingConfig.currentModel }}</el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">当前类型:</span>
              <el-tag :type="embeddingConfig.currentProvider === 'local' ? 'success' : 'primary'" size="small">
                {{ embeddingConfig.currentProvider === 'local' ? '本地模型' : 'API模型' }}
              </el-tag>
            </div>
          </div>
          
          <el-table :data="embeddingModels" style="width:100%;margin-top:16px" v-loading="loadingEmbedding">
            <el-table-column prop="name" label="名称" min-width="150">
              <template #default="{ row }">
                <div class="model-cell">
                  <span class="font-medium">{{ row.name || row.model }}</span>
                  <el-tag v-if="row.is_builtin" size="small" type="info" style="margin-left:4px">内置</el-tag>
                  <el-tag v-else size="small" type="warning" style="margin-left:4px">自定义</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="provider" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.provider === 'local' ? 'success' : 'primary'" size="small">
                  {{ row.provider === 'local' ? '本地' : 'API' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dimension" label="维度" width="80" />
            <el-table-column prop="api_base" label="API地址" min-width="200">
              <template #default="{ row }">
                <span class="text-mono" v-if="row.api_base">{{ row.api_base }}</span>
                <span class="text-muted" v-else-if="row.provider === 'local'">{{ row.model_path || 'HuggingFace' }}</span>
                <span class="text-muted" v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="device" label="设备" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.device || 'cpu' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default || row.isDefault" type="success" size="small">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" link @click="editEmbeddingModel(row)">编辑</el-button>
                <el-button type="success" size="small" link @click="setDefaultEmbeddingModel(row)" v-if="!row.is_default && !row.isDefault">设为默认</el-button>
                <el-button type="warning" size="small" link @click="testEmbeddingModel(row)">测试</el-button>
                <el-button type="danger" size="small" link @click="deleteEmbeddingModel(row)" v-if="!row.is_builtin">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-divider />
          
          <el-form label-width="140px">
            <el-form-item label="当前 Embedding">
              <el-select v-model="embeddingConfig.currentModel" style="width:300px" @change="onCurrentEmbeddingChange">
                <el-option
                  v-for="m in embeddingModels"
                  :key="m.model || m.name"
                  :label="`${m.name || m.model} (${m.provider === 'local' ? '本地' : 'API'})`"
                  :value="m.model || m.name"
                />
              </el-select>
            </el-form-item>

            <!-- API 模型配置区 -->
            <template v-if="currentEmbeddingDetail && currentEmbeddingDetail.provider === 'api'">
              <el-form-item label="API 地址">
                <el-input :model-value="currentEmbeddingDetail.api_base || ''" disabled style="max-width:500px" />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input :model-value="currentEmbeddingDetail.api_key ? '已配置' : '未配置'" disabled style="max-width:300px" />
              </el-form-item>
            </template>

            <!-- 本地模型配置区 -->
            <template v-if="currentEmbeddingDetail && currentEmbeddingDetail.provider === 'local'">
              <el-form-item label="模型本地路径">
                <div style="display:flex;gap:8px;width:100%;max-width:500px">
                  <el-input
                    v-model="currentEmbeddingDetail.model_path"
                    placeholder="如: E:\models\bge-m3"
                    style="flex:1"
                  />
                  <el-button type="success" @click="updateEmbeddingField('model_path', currentEmbeddingDetail.model_path)" :loading="savingEmbedding">保存</el-button>
                </div>
                <div style="font-size:12px;color:var(--el-text-color-secondary);margin-top:4px">
                  留空将从 HuggingFace 自动下载，建议提前下载到本地加速加载
                </div>
              </el-form-item>
              <el-form-item label="运行设备">
                <el-select v-model="currentEmbeddingDetail.device" style="width:300px" @change="updateEmbeddingField('device', currentEmbeddingDetail.device)">
                  <el-option label="CPU（通用）" value="cpu" />
                  <el-option label="CUDA（NVIDIA GPU）" value="cuda" />
                  <el-option label="MPS（Apple Silicon）" value="mps" />
                </el-select>
              </el-form-item>
              <el-form-item label="Batch Size">
                <el-input-number v-model="currentEmbeddingDetail.batch_size" :min="1" :max="256" style="width:200px" @change="updateEmbeddingField('batch_size', currentEmbeddingDetail.batch_size)" />
              </el-form-item>
              <el-form-item label="sentence-transformers">
                <el-tag :type="embeddingConfig.stAvailable ? 'success' : 'danger'" size="small">
                  {{ embeddingConfig.stAvailable ? '已安装' : '未安装' }}
                </el-tag>
                <span style="font-size:12px;color:var(--el-text-color-secondary);margin-left:8px">本地模型运行需要安装此库</span>
              </el-form-item>
            </template>

            <el-form-item>
              <el-button type="primary" @click="saveEmbeddingConfig" :loading="savingEmbedding">保存配置</el-button>
              <el-button type="success" @click="testCurrentEmbedding" :loading="testingEmbedding">测试当前模型</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 基本配置 -->
      <el-tab-pane label="基本配置" name="basic">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统基本信息</span>
            </div>
          </template>
          
          <el-form label-width="140px">
            <el-form-item label="系统名称">
              <el-input v-model="basicConfig.appName" style="width:300px" />
            </el-form-item>
            
            <el-form-item label="系统主题">
              <el-radio-group v-model="basicConfig.theme">
                <el-radio label="light">浅色</el-radio>
                <el-radio label="dark">深色</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBasicConfig" :loading="savingBasic">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 系统健康 -->
      <el-tab-pane label="系统健康" name="health">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统运行状态</span>
              <el-button link @click="loadHealth"><el-icon><Refresh /></el-icon> 刷新</el-button>
            </div>
          </template>
          
          <el-row :gutter="20" v-loading="loadingHealth">
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon cpu"><el-icon><Cpu /></el-icon></div>
                <div class="health-info">
                  <span class="health-label">CPU 使用</span>
                  <span class="health-value">{{ healthData.cpu_percent?.toFixed(1) }}%</span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon mem"><el-icon><Monitor /></el-icon></div>
                <div class="health-info">
                  <span class="health-label">内存使用</span>
                  <span class="health-value">{{ healthData.memory_percent?.toFixed(1) }}%</span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon disk"><el-icon><Folder /></el-icon></div>
                <div class="health-info">
                  <span class="health-label">磁盘使用</span>
                  <span class="health-value">{{ healthData.disk_percent?.toFixed(1) }}%</span>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="health-card">
                <div class="health-icon status" :class="healthData.status">
                  <el-icon><CircleCheck v-if="healthData.status === 'healthy'" /><CircleClose v-else /></el-icon>
                </div>
                <div class="health-info">
                  <span class="health-label">系统状态</span>
                  <span class="health-value">{{ healthData.status === 'healthy' ? '正常' : '异常' }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加AI模型对话框 -->
    <el-dialog v-model="showModelDialog" :title="editingModel ? '编辑AI模型' : '添加AI模型'" width="700px">
      <el-form :model="modelForm" label-width="120px">
        <el-form-item label="AI供应商" required>
          <el-select v-model="modelForm.provider" style="width:100%" @change="handleProviderChange">
            <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型ID" required>
          <el-input v-model="modelForm.modelId" placeholder="如: Qwen/Qwen2.5-7B-Instruct" />
        </el-form-item>
        
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.modelName" placeholder="如: 通义千问 7B" />
        </el-form-item>
        
        <el-form-item label="API Key" v-if="!isLocalProvider(modelForm.provider)">
          <el-input v-model="modelForm.apiKey" type="password" show-password placeholder="API Key" />
        </el-form-item>
        
        <el-form-item label="API地址" v-if="isLocalProvider(modelForm.provider)">
          <el-input v-model="modelForm.baseUrl" placeholder="Ollama 服务地址，如: http://localhost:11434/v1" />
        </el-form-item>
        <el-form-item label="API地址" v-else>
          <el-input v-model="modelForm.baseUrl" placeholder="自定义API地址（可选）" />
        </el-form-item>
        
        <el-divider content-position="left">模型参数</el-divider>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Temperature">
              <el-input-number v-model="modelForm.temperature" :min="0" :max="2" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Top P">
              <el-input-number v-model="modelForm.topP" :min="0" :max="1" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Top K">
              <el-input-number v-model="modelForm.topK" :min="1" :max="100" :step="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Max Tokens">
              <el-input-number v-model="modelForm.maxTokens" :min="1" :max="32768" :step="100" style="width:100%" placeholder="最大输出token数" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="上下文窗口">
              <el-input-number v-model="modelForm.contextWindow" :min="1024" :max="200000" :step="1024" style="width:100%" placeholder="上下文token数" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="频率惩罚">
              <el-input-number v-model="modelForm.frequencyPenalty" :min="-2" :max="2" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="存在惩罚">
              <el-input-number v-model="modelForm.presencePenalty" :min="-2" :max="2" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重复惩罚">
              <el-input-number v-model="modelForm.repeatPenalty" :min="1" :max="2" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider content-position="left">请求配置</el-divider>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="Timeout (秒)">
              <el-input-number v-model="modelForm.timeout" :min="10" :max="300" :step="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大重试">
              <el-input-number v-model="modelForm.maxRetries" :min="0" :max="5" :step="1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="流式响应">
              <el-switch v-model="modelForm.stream" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设为默认">
              <el-switch v-model="modelForm.isDefault" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="额外参数">
          <el-input v-model="modelForm.extraParams" type="textarea" :rows="2" placeholder="JSON格式，如: {response_format: 'json'}" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showModelDialog = false">取消</el-button>
        <el-button type="primary" @click="saveModel" :loading="savingModel">{{ editingModel ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑Ollama连接对话框 -->
    <el-dialog v-model="showLocalModelDialog" :title="editingLocalModel ? '编辑 Ollama 连接' : '添加 Ollama 连接'" width="700px">
      <el-form :model="localModelForm" label-width="130px">
        <el-form-item label="连接名称" required>
          <el-input v-model="localModelForm.name" placeholder="如: 本地 Ollama" />
        </el-form-item>
        <el-form-item label="Ollama 地址" required>
          <el-input v-model="localModelForm.url" placeholder="http://localhost:11434" />
        </el-form-item>
        <el-form-item label="API 路径">
          <el-input v-model="localModelForm.apiPath" placeholder="/v1 或留空" />
          <span class="form-tip">OpenAI兼容API路径，默认为 /v1</span>
        </el-form-item>
        <el-form-item label="默认模型">
          <el-select v-model="localModelForm.defaultModel" style="width:100%" allow-create filterable placeholder="选择或输入默认模型">
            <el-option v-for="m in localModelForm.availableModels" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="localModelForm.apiKey" type="password" show-password placeholder="可选，如需远程访问" />
        </el-form-item>
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="localModelForm.timeout" :min="5" :max="300" style="width:100%" />
        </el-form-item>
        <el-form-item label="自动下载模型">
          <el-switch v-model="localModelForm.autoPull" />
          <span class="form-tip">模型不存在时自动下载</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="localModelForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLocalModelDialog = false">取消</el-button>
        <el-button type="info" @click="testOllamaConnection(localModelForm)" :loading="addingLocalModel">测试连接</el-button>
        <el-button type="primary" @click="saveOllamaConnection" :loading="addingLocalModel">
          {{ editingLocalModel ? '保存' : '添加并测试' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑 Rerank 模型对话框 -->
    <el-dialog v-model="showRerankDialog" :title="editingRerank ? '编辑 Rerank 模型' : '添加 Rerank 模型'" width="600px">
      <el-form :model="rerankForm" label-width="130px">
        <el-form-item label="模型名称" required>
          <el-input v-model="rerankForm.name" placeholder="如: BGE Reranker" />
        </el-form-item>
        <el-form-item label="模型 ID" required>
          <el-select
            v-model="rerankForm.model"
            filterable
            allow-create
            placeholder="选择或输入 Rerank 模型 ID"
            style="width:100%"
            :reserve-keyword="false"
          >
            <el-option-group label="SiliconFlow (推荐)">
              <el-option value="BAAI/bge-reranker-v2-m3" label="BAAI/bge-reranker-v2-m3" description="BGE 多语言重排序模型" />
              <el-option value="BAAI/bge-reranker-base" label="BAAI/bge-reranker-base" description="BGE 基础重排序模型" />
            </el-option-group>
            <el-option-group label="Cohere">
              <el-option value="rerank-multilingual-v2.0" label="rerank-multilingual-v2.0" description="Cohere 多语言重排序" />
              <el-option value="rerank-english-v2.0" label="rerank-english-v2.0" description="Cohere 英文重排序" />
            </el-option-group>
            <el-option-group label="本地模型">
              <el-option value="Xorbits/neural-searcher" label="Xorbits/neural-searcher" description="本地神经搜索模型" />
            </el-option-group>
          </el-select>
          <div class="form-tip">可直接输入自定义模型 ID，支持 HuggingFace 模型名称</div>
        </el-form-item>
        <el-form-item label="服务商">
          <el-select v-model="rerankForm.provider" style="width:100%">
            <el-option label="本地部署" value="local" />
            <el-option label="Cohere" value="cohere" />
            <el-option label="SiliconFlow" value="siliconflow" />
            <el-option label="Jina AI" value="jina" />
          </el-select>
        </el-form-item>
        <el-form-item label="API 地址">
          <el-input v-model="rerankForm.apiUrl" placeholder="自定义 API 地址（可选）" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="rerankForm.apiKey" type="password" show-password placeholder="API Key" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="rerankForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRerankDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRerankModel" :loading="savingRerank">
          {{ editingRerank ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑 Embedding 模型对话框 -->
    <el-dialog v-model="showEmbeddingDialog" :title="editingEmbedding ? '编辑 Embedding 模型' : '添加 Embedding 模型'" width="650px">
      <el-form :model="embeddingForm" label-width="120px">
        <el-form-item label="类型" required>
          <el-radio-group v-model="embeddingForm.provider" @change="handleEmbeddingProviderChange">
            <el-radio value="api">API 模型</el-radio>
            <el-radio value="local">本地模型</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="模型名称" required>
          <el-input v-model="embeddingForm.name" placeholder="如: 阿里云 Embedding" />
        </el-form-item>
        
        <el-form-item label="模型 ID" required>
          <el-select v-model="embeddingForm.model" filterable allow-create placeholder="选择或输入模型ID" style="width:100%">
            <el-option-group v-if="embeddingForm.provider === 'api'" label="API 模型">
              <el-option value="text-embedding-v2" label="text-embedding-v2" description="DashScope 1536维" />
              <el-option value="text-embedding-v3" label="text-embedding-v3" description="DashScope 1024维" />
              <el-option value="text-embedding-3-small" label="text-embedding-3-small" description="OpenAI 1536维" />
              <el-option value="text-embedding-3-large" label="text-embedding-3-large" description="OpenAI 3072维" />
            </el-option-group>
            <el-option-group v-if="embeddingForm.provider === 'local'" label="本地模型">
              <el-option value="BAAI/bge-m3" label="BAAI/bge-m3" description="BGE多语言模型 1024维" />
              <el-option value="BAAI/bge-large-zh-v1.5" label="BAAI/bge-large-zh-v1.5" description="BGE大型中文模型 1024维" />
              <el-option value="BAAI/bge-base-zh-v1.5" label="BAAI/bge-base-zh-v1.5" description="BGE基础中文模型 768维" />
              <el-option value="sentence-transformers/all-mpnet-base-v2" label="all-mpnet-base-v2" description="MPNet高质量英文模型 768维" />
              <el-option value="all-MiniLM-L6-v2" label="all-MiniLM-L6-v2" description="轻量级英文模型 384维" />
              <el-option value="shibing624/text2vec-base-chinese" label="text2vec-base-chinese" description="中文向量化模型 768维" />
            </el-option-group>
          </el-select>
        </el-form-item>
        
        <el-form-item label="向量维度">
          <el-input-number v-model="embeddingForm.dimension" :min="128" :max="4096" style="width:100%" />
        </el-form-item>
        
        <!-- API 模型配置 -->
        <template v-if="embeddingForm.provider === 'api'">
          <el-form-item label="API 地址">
            <el-input v-model="embeddingForm.apiBase" placeholder="如: https://dashscope.aliyuncs.com/compatible-mode/v1" />
          </el-form-item>
          <el-form-item label="API Key" required>
            <el-input v-model="embeddingForm.apiKey" type="password" show-password placeholder="输入 API Key" />
          </el-form-item>
        </template>
        
        <!-- 本地模型配置 -->
        <template v-if="embeddingForm.provider === 'local'">
          <el-form-item label="模型本地路径">
            <el-input v-model="embeddingForm.modelPath" placeholder="本地模型路径（可选，留空从HuggingFace下载）" />
          </el-form-item>
          <el-form-item label="运行设备">
            <el-select v-model="embeddingForm.device" style="width:100%">
              <el-option label="CPU" value="cpu" />
              <el-option label="CUDA (GPU)" value="cuda" />
              <el-option label="MPS (Apple Silicon)" value="mps" />
            </el-select>
          </el-form-item>
        </template>
        
        <el-form-item label="Batch Size">
          <el-input-number v-model="embeddingForm.batchSize" :min="1" :max="256" style="width:100%" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="embeddingForm.description" type="textarea" :rows="2" placeholder="模型描述（可选）" />
        </el-form-item>
        
        <el-form-item label="启用">
          <el-switch v-model="embeddingForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEmbeddingDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEmbeddingModel" :loading="savingEmbedding">
          {{ editingEmbedding ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Refresh, Cpu, Monitor, Folder, CircleCheck, CircleClose, Document, Files, Setting, Plus, ChatDotRound, Connection, Filter, Picture, CircleCloseFilled, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemAPI, localAIAPI } from '../../common/api'

const activeTab = ref('ai-models')
const aiConfigStatus = ref<any>(null)
const loadingConfigStatus = ref(false)

// AI模型管理
const aiModels = ref<any[]>([])
const loadingModels = ref(false)
const showModelDialog = ref(false)
const editingModel = ref<any>(null)
const savingModel = ref(false)

const modelForm = reactive({
  provider: 'siliconflow',
  modelId: '',
  modelName: '',
  apiKey: '',
  baseUrl: '',
  // 模型参数
  temperature: 0.7,
  topP: 0.9,
  topK: 40,
  maxTokens: 8192,
  contextWindow: 32768,
  frequencyPenalty: 0,
  presencePenalty: 0,
  repeatPenalty: 1.1,
  // 请求配置
  timeout: 120,
  maxRetries: 3,
  stream: true,
  // 额外参数
  extraParams: '',
  isDefault: false
})

// 重置模型表单
function resetModelForm() {
  Object.assign(modelForm, {
    provider: 'siliconflow',
    modelId: '',
    modelName: '',
    apiKey: '',
    baseUrl: '',
    temperature: 0.7,
    topP: 0.9,
    topK: 40,
    maxTokens: 8192,
    contextWindow: 32768,
    frequencyPenalty: 0,
    presencePenalty: 0,
    repeatPenalty: 1.1,
    timeout: 120,
    maxRetries: 3,
    stream: true,
    extraParams: '',
    isDefault: false
  })
}

// 模块AI配置
const moduleSettings = reactive({
  chatGeneral: '',
  chatTemplate: '',
  chatWorkflow: '',
  chatAnalytics: '',
  ragModel: '',
  processingModel: ''
})

// 可用于选择的模型列表
const availableModelsForSelect = computed(() => aiModels.value.filter(m => m.configured))

// 本地模型配置
const localModels = ref<any[]>([])
const loadingLocalModels = ref(false)
const showLocalModelDialog = ref(false)
const editingLocalModel = ref<any>(null)
const addingLocalModel = ref(false)

const localModelForm = reactive({
  name: '',
  url: 'http://localhost:11434',
  apiPath: '/v1',
  defaultModel: '',
  apiKey: '',
  timeout: 60,
  autoPull: true,
  enabled: true,
  availableModels: [] as string[]
})

// Rerank模型配置
const rerankModels = ref<any[]>([])
const loadingRerank = ref(false)
const showRerankDialog = ref(false)
const editingRerank = ref<any>(null)
const savingRerank = ref(false)

const rerankForm = reactive({
  name: '',
  model: '',
  provider: 'local',
  apiUrl: '',
  apiKey: '',
  enabled: true
})

// Embedding配置
const embeddingConfig = reactive({
  currentModel: 'text-embedding-v2',
  currentProvider: 'api',
  stAvailable: false
})
const embeddingModels = ref<any[]>([])
const loadingEmbedding = ref(false)
const showEmbeddingDialog = ref(false)
const editingEmbedding = ref<any>(null)
const savingEmbedding = ref(false)
const testingEmbedding = ref(false)

// 当前选中的Embedding模型详情（用于标签页内的配置区）
const currentEmbeddingDetail = computed(() => {
  return embeddingModels.value.find(m => (m.model || m.name) === embeddingConfig.currentModel) || null
})

const embeddingForm = reactive({
  name: '',
  model: '',
  provider: 'api',
  dimension: 1024,
  device: 'cpu',
  apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  apiKey: '',
  modelPath: '',
  batchSize: 32,
  description: '',
  enabled: true
})

// 基本配置
const basicConfig = reactive({
  appName: 'Kflower 企业智能管理低代码平台',
  theme: 'light'
})
const savingBasic = ref(false)

// 健康检查
const healthData = ref<any>({
  cpu_percent: 0,
  memory_percent: 0,
  disk_percent: 0,
  status: 'healthy'
})
const loadingHealth = ref(false)

// AI提供商列表
const providers = ref<any[]>([
  { id: 'siliconflow', name: 'SiliconFlow' },
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'zhipuai', name: '智谱AI' },
  { id: 'dashscope', name: '阿里云百炼' },
  { id: 'openai', name: 'OpenAI' },
  { id: 'ollama', name: 'Ollama (本地)' }
])

function getProviderName(id: string) {
  return providers.value.find(p => p.id === id)?.name || id
}

// 判断是否为本地服务商（不需要API Key）
function isLocalProvider(provider: string) {
  return ['ollama', 'local'].includes(provider)
}

// 加载AI模型列表
async function loadAIConfigStatus() {
  loadingConfigStatus.value = true
  try {
    const res: any = await systemAPI.getAIConfigStatus()
    if (res?.data) {
      aiConfigStatus.value = res.data
    }
  } catch (e: any) {
    console.error('加载AI配置状态失败:', e)
  } finally {
    loadingConfigStatus.value = false
  }
}

function refreshConfigStatus() {
  loadAIConfigStatus()
}

async function loadAiModels() {
  loadingModels.value = true
  try {
    const res: any = await systemAPI.getConfig()
    if (res && res.success !== false) {
      const data = res.data || {}
      
      // 解析已保存的模型列表
      if (data.ai_models) {
        try {
          aiModels.value = typeof data.ai_models === 'string' ? JSON.parse(data.ai_models) : data.ai_models
        } catch { aiModels.value = [] }
      }
      
      // 解析模块配置
      if (data.module_ai_settings) {
        try {
          const settings = typeof data.module_ai_settings === 'string' ? JSON.parse(data.module_ai_settings) : data.module_ai_settings
          Object.assign(moduleSettings, settings)
        } catch {}
      }
    }
  } catch (e) {
    console.warn('Failed to load AI models')
  } finally {
    loadingModels.value = false
  }
}

// 添加模型对话框
function openAddModelDialog() {
  editingModel.value = null
  resetModelForm()
  showModelDialog.value = true
}

// 编辑模型
function editModel(row: any) {
  editingModel.value = row
  // 确保所有参数都有默认值
  resetModelForm()
  const params = row.params || {}
  Object.assign(modelForm, {
    provider: row.provider || 'siliconflow',
    modelId: row.modelId || '',
    modelName: row.modelName || '',
    apiKey: row.apiKey || '',
    baseUrl: row.baseUrl || '',
    // 从params中读取参数，如果没有则使用row顶层参数（兼容旧数据）
    temperature: params.temperature ?? row.temperature ?? 0.7,
    topP: params.topP ?? row.topP ?? 0.9,
    topK: params.topK ?? row.topK ?? 40,
    maxTokens: params.maxTokens ?? row.maxTokens ?? 8192,
    contextWindow: params.contextWindow ?? row.contextWindow ?? 32768,
    frequencyPenalty: params.frequencyPenalty ?? row.frequencyPenalty ?? 0,
    presencePenalty: params.presencePenalty ?? row.presencePenalty ?? 0,
    repeatPenalty: params.repeatPenalty ?? row.repeatPenalty ?? 1.1,
    timeout: params.timeout ?? row.timeout ?? 120,
    maxRetries: params.maxRetries ?? row.maxRetries ?? 3,
    stream: params.stream ?? row.stream ?? true,
    extraParams: params.extraParams || row.extraParams || '',
    isDefault: row.isDefault || false
  })
  showModelDialog.value = true
}

// 保存模型
async function saveModel() {
  if (!modelForm.modelId.trim()) {
    ElMessage.warning('请输入模型ID')
    return
  }
  
  savingModel.value = true
  try {
    let models = [...aiModels.value]
    
    // 构建模型数据，参数放在 params 对象中
    const modelData = {
      provider: modelForm.provider,
      modelId: modelForm.modelId,
      modelName: modelForm.modelName,
      apiKey: modelForm.apiKey,
      baseUrl: modelForm.baseUrl,
      isDefault: modelForm.isDefault,
      configured: true,
      params: {
        temperature: modelForm.temperature,
        topP: modelForm.topP,
        topK: modelForm.topK,
        maxTokens: modelForm.maxTokens,
        contextWindow: modelForm.contextWindow,
        frequencyPenalty: modelForm.frequencyPenalty,
        presencePenalty: modelForm.presencePenalty,
        repeatPenalty: modelForm.repeatPenalty,
        timeout: modelForm.timeout,
        maxRetries: modelForm.maxRetries,
        stream: modelForm.stream,
        extraParams: modelForm.extraParams
      }
    }
    
    if (editingModel.value) {
      // 更新现有模型
      const idx = models.findIndex(m => m.modelId === editingModel.value.modelId)
      if (idx > -1) {
        models[idx] = modelData
      }
    } else {
      // 添加新模型
      if (modelForm.isDefault) {
        // 如果设为默认，取消其他默认
        models.forEach(m => m.isDefault = false)
      }
      models.push(modelData)
    }
    
    const res: any = await systemAPI.saveConfig({ ai_models: JSON.stringify(models) })
    if (res && res.success !== false) {
      ElMessage.success(editingModel.value ? '模型已更新' : '模型已添加')
      aiModels.value = models
      showModelDialog.value = false
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    savingModel.value = false
  }
}

// 删除模型
async function deleteModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除模型 "${row.modelName || row.modelId}" 吗？`, '确认删除', { type: 'warning' })
    aiModels.value = aiModels.value.filter(m => m.modelId !== row.modelId)
    await systemAPI.saveConfig({ ai_models: JSON.stringify(aiModels.value) })
    ElMessage.success('模型已删除')
  } catch (e) {}
}

// 保存模块配置
async function saveModuleSettings() {
  try {
    const res: any = await systemAPI.saveConfig({ module_ai_settings: JSON.stringify(moduleSettings) })
    if (res && res.success !== false) {
      ElMessage.success('模块配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 加载本地模型
async function loadLocalModels() {
  loadingLocalModels.value = true
  try {
    const res: any = await systemAPI.getConfig()
    if (res && res.success !== false) {
      const data = res.data || {}
      if (data.local_ollama_connections) {
        localModels.value = typeof data.local_ollama_connections === 'string' ? JSON.parse(data.local_ollama_connections) : data.local_ollama_connections
      }
      // 加载Rerank配置
      if (data.rerank_models) {
        rerankModels.value = typeof data.rerank_models === 'string' ? JSON.parse(data.rerank_models) : data.rerank_models
      }
    }
  } catch (e) {
    console.warn('Failed to load local models')
  } finally {
    loadingLocalModels.value = false
  }
}

// 加载 Ollama 连接（从后端获取真实连接状态）
async function loadOllamaConnections() {
  try {
    const res: any = await systemAPI.listOllamaConnections()
    if (res && res.success !== false && res.data?.connections) {
      // 更新本地模型列表的连接状态
      for (const conn of res.data.connections) {
        const localConn = localModels.value.find(m => m.id === conn.id || m.name === conn.name)
        if (localConn) {
          localConn.status = conn.status || 'disconnected'
          localConn.models = conn.models || []
        }
      }
    }
  } catch (e) {
    console.warn('Failed to load Ollama connections')
  }
}

// 加载 Rerank 模型列表（从后端获取真实模型）
async function loadRerankModels() {
  try {
    const res: any = await systemAPI.listRerankModels()
    if (res && res.success !== false && res.data?.models) {
      // 合并后端模型到本地列表
      for (const m of res.data.models) {
        if (!rerankModels.value.find(r => r.model === m.id || r.name === m.id)) {
          rerankModels.value.push({
            id: m.id,
            name: m.name,
            model: m.id,
            provider: m.provider,
            description: m.description,
            is_preset: !m.is_custom,
          })
        }
      }
    }
  } catch (e) {
    console.warn('Failed to load rerank models')
  }
}

// 添加Ollama连接对话框
function openAddLocalModelDialog() {
  editingLocalModel.value = null
  Object.assign(localModelForm, {
    name: '',
    url: 'http://localhost:11434',
    apiPath: '/v1',
    defaultModel: '',
    apiKey: '',
    timeout: 60,
    autoPull: true,
    enabled: true,
    availableModels: []
  })
  showLocalModelDialog.value = true
}

// 编辑Ollama连接
function editLocalModel(row: any) {
  editingLocalModel.value = row
  Object.assign(localModelForm, {
    name: row.name || '',
    url: row.url || 'http://localhost:11434',
    apiPath: row.apiPath || '/v1',
    defaultModel: row.defaultModel || row.default_model || '',
    apiKey: row.apiKey || '',
    timeout: row.timeout || 60,
    autoPull: row.autoPull !== false,
    enabled: row.enabled !== false,
    availableModels: row.models || []
  })
  showLocalModelDialog.value = true
}

// 保存Ollama连接
async function saveOllamaConnection() {
  if (!localModelForm.name.trim() || !localModelForm.url.trim()) {
    ElMessage.warning('请填写连接名称和地址')
    return
  }
  
  addingLocalModel.value = true
  try {
    let status = 'disconnected'
    let models: string[] = []
    
    // 测试连接
    try {
      const res = await fetch(`${localModelForm.url}/api/tags`)
      if (res.ok) {
        const data = await res.json()
        models = (data.models || []).map((m: any) => m.name)
        localModelForm.availableModels = models
        status = 'connected'
        ElMessage.success('连接成功，发现 ' + models.length + ' 个模型')
      } else {
        ElMessage.warning('Ollama 连接失败，但仍保存配置')
      }
    } catch (e: any) {
      ElMessage.warning('无法连接到 Ollama: ' + e.message)
    }
    
    const connData = {
      id: editingLocalModel.value?.id || Date.now(),
      name: localModelForm.name,
      url: localModelForm.url,
      apiPath: localModelForm.apiPath,
      defaultModel: localModelForm.defaultModel,
      apiKey: localModelForm.apiKey,
      timeout: localModelForm.timeout,
      autoPull: localModelForm.autoPull,
      enabled: localModelForm.enabled,
      status,
      models: models.length ? models : localModelForm.availableModels
    }
    
    if (editingLocalModel.value) {
      const idx = localModels.value.findIndex(m => m.id === editingLocalModel.value.id)
      if (idx > -1) localModels.value[idx] = connData
      ElMessage.success('Ollama 配置已保存')
    } else {
      localModels.value.push(connData)
      if (status === 'disconnected') {
        ElMessage.warning('配置已保存，但 Ollama 连接失败')
      }
    }
    
    await systemAPI.saveConfig({ local_ollama_connections: JSON.stringify(localModels.value) })
    showLocalModelDialog.value = false
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    addingLocalModel.value = false
  }
}

// 测试Ollama连接
async function testOllamaConnection(row: any) {
  try {
    const res = await fetch(`${row.url}/api/tags`)
    if (res.ok) {
      const data = await res.json()
      row.status = 'connected'
      row.models = (data.models || []).map((m: any) => m.name)
      ElMessage.success('连接成功，可用模型: ' + row.models.length)
    } else {
      row.status = 'disconnected'
      ElMessage.error('连接失败')
    }
  } catch (e) {
    row.status = 'disconnected'
    ElMessage.error('无法连接到 Ollama')
  }
}

// 删除本地模型连接
async function deleteLocalModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除连接 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    localModels.value = localModels.value.filter(m => m.id !== row.id)
    await systemAPI.saveConfig({ local_ollama_connections: JSON.stringify(localModels.value) })
    ElMessage.success('已删除')
  } catch (e) {}
}

// ===== Rerank 模型管理 =====

function openAddRerankDialog() {
  editingRerank.value = null
  Object.assign(rerankForm, {
    name: '',
    model: '',
    provider: 'local',
    apiUrl: '',
    apiKey: '',
    enabled: true
  })
  showRerankDialog.value = true
}

function editRerankModel(row: any) {
  editingRerank.value = row
  Object.assign(rerankForm, {
    name: row.name || '',
    model: row.model || '',
    provider: row.provider || 'local',
    apiUrl: row.apiUrl || '',
    apiKey: row.apiKey || '',
    enabled: row.enabled !== false
  })
  showRerankDialog.value = true
}

async function saveRerankModel() {
  if (!rerankForm.name.trim() || !rerankForm.model.trim()) {
    ElMessage.warning('请填写模型名称和模型ID')
    return
  }
  
  savingRerank.value = true
  try {
    const modelData = {
      id: editingRerank.value?.id || Date.now(),
      ...rerankForm
    }
    
    if (editingRerank.value) {
      const idx = rerankModels.value.findIndex(m => m.id === editingRerank.value.id)
      if (idx > -1) rerankModels.value[idx] = modelData
    } else {
      rerankModels.value.push(modelData)
    }
    
    await systemAPI.saveConfig({ rerank_models: JSON.stringify(rerankModels.value) })
    ElMessage.success(editingRerank.value ? '已更新' : '已添加')
    showRerankDialog.value = false
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    savingRerank.value = false
  }
}

async function toggleRerankModel(row: any) {
  try {
    await systemAPI.saveConfig({ rerank_models: JSON.stringify(rerankModels.value) })
    ElMessage.success(row.enabled ? '已启用' : '已禁用')
  } catch (e) {}
}

async function deleteRerankModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.name || row.model}" 吗？`, '确认删除', { type: 'warning' })
    rerankModels.value = rerankModels.value.filter(m => m.id !== row.id)
    await systemAPI.saveConfig({ rerank_models: JSON.stringify(rerankModels.value) })
    ElMessage.success('已删除')
  } catch (e) {}
}

// ===== Embedding 模型管理 =====

// 当前Embedding切换时同步更新provider
function onCurrentEmbeddingChange(modelId: string) {
  const found = embeddingModels.value.find(m => (m.model || m.name) === modelId)
  if (found) {
    embeddingConfig.currentProvider = found.provider || 'api'
  }
  saveEmbeddingConfig()
}

// 直接更新当前Embedding模型的某个字段并保存
async function updateEmbeddingField(field: string, value: any) {
  if (!currentEmbeddingDetail.value) return
  const modelId = currentEmbeddingDetail.value.model || currentEmbeddingDetail.value.name
  try {
    savingEmbedding.value = true
    await localAIAPI.updateEmbedModel(modelId, { [field]: value })
    // 更新本地数据
    ;(currentEmbeddingDetail.value as any)[field] = value
    ElMessage.success('已保存')
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    savingEmbedding.value = false
  }
}

function handleEmbeddingProviderChange(provider: string) {
  // 切换类型时清空相关字段
  if (provider === 'api') {
    embeddingForm.model = 'text-embedding-v2'
    embeddingForm.dimension = 1536
    embeddingForm.apiBase = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    embeddingForm.apiKey = ''
  } else {
    embeddingForm.model = 'BAAI/bge-m3'
    embeddingForm.dimension = 1024
    embeddingForm.device = 'cpu'
    embeddingForm.modelPath = ''
  }
}

function openAddEmbeddingDialog() {
  editingEmbedding.value = null
  Object.assign(embeddingForm, {
    name: '',
    model: '',
    provider: 'api',
    dimension: 1536,
    device: 'cpu',
    apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: '',
    modelPath: '',
    batchSize: 32,
    description: '',
    enabled: true
  })
  showEmbeddingDialog.value = true
}

function editEmbeddingModel(row: any) {
  editingEmbedding.value = row
  Object.assign(embeddingForm, {
    name: row.name || row.model || '',
    model: row.model || row.name || '',
    provider: row.provider || 'api',
    dimension: row.dimension || 1024,
    device: row.device || 'cpu',
    apiBase: row.api_base || row.apiBase || 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: row.api_key || row.apiKey || '',
    modelPath: row.model_path || row.modelPath || '',
    batchSize: row.batch_size || row.batchSize || 32,
    description: row.description || '',
    enabled: row.enabled !== false
  })
  showEmbeddingDialog.value = true
}

async function saveEmbeddingModel() {
  if (!embeddingForm.name.trim()) {
    ElMessage.warning('请填写模型名称')
    return
  }
  if (!embeddingForm.model.trim()) {
    ElMessage.warning('请填写模型 ID')
    return
  }
  if (embeddingForm.provider === 'api' && !embeddingForm.apiKey.trim()) {
    ElMessage.warning('API 模型需要填写 API Key')
    return
  }

  savingEmbedding.value = true
  try {
    const modelData = {
      name: embeddingForm.name,
      model: embeddingForm.model,
      provider: embeddingForm.provider,
      dimension: embeddingForm.dimension,
      description: embeddingForm.description,
      api_key: embeddingForm.apiKey,
      api_base: embeddingForm.apiBase,
      model_path: embeddingForm.modelPath,
      device: embeddingForm.device,
      batch_size: embeddingForm.batchSize,
      enabled: embeddingForm.enabled
    }
    
    let res: any
    if (editingEmbedding.value) {
      res = await localAIAPI.updateEmbedModel(embeddingForm.model, modelData)
    } else {
      res = await localAIAPI.addEmbedModel(modelData)
    }
    
    if (res && res.success !== false) {
      ElMessage.success(editingEmbedding.value ? '已更新' : '已添加')
      showEmbeddingDialog.value = false
      await loadEmbeddingModels()
    } else {
      ElMessage.error(res?.message || '保存失败')
    }
  } catch (e: any) {
    ElMessage.error('保存失败: ' + e.message)
  } finally {
    savingEmbedding.value = false
  }
}

async function deleteEmbeddingModel(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.name || row.model}" 吗？`, '确认删除', { type: 'warning' })
    const res: any = await localAIAPI.deleteEmbedModel(row.model || row.name)
    if (res && res.success !== false) {
      ElMessage.success('已删除')
      await loadEmbeddingModels()
    } else {
      ElMessage.error(res?.message || '删除失败')
    }
  } catch (e) {}
}

async function setDefaultEmbeddingModel(row: any) {
  try {
    const modelId = row.model || row.name
    const res: any = await localAIAPI.setDefaultEmbedModel(modelId)
    if (res && res.success !== false) {
      ElMessage.success(res.message || '已设为默认')
      await loadEmbeddingModels()
    } else {
      ElMessage.error(res?.message || '设置失败')
    }
  } catch (e: any) {
    ElMessage.error('设置失败: ' + e.message)
  }
}

async function testEmbeddingModel(row: any) {
  try {
    const modelId = row.model || row.name
    ElMessage.info('正在测试模型，请稍候...')
    const res: any = await localAIAPI.testEmbedModel(modelId)
    if (res && res.success !== false) {
      ElMessage.success(`测试成功！模型: ${res.data?.model}, 维度: ${res.data?.dimension}`)
    } else {
      ElMessage.error(res?.message || '测试失败')
    }
  } catch (e: any) {
    ElMessage.error('测试失败: ' + e.message)
  }
}

async function testCurrentEmbedding() {
  testingEmbedding.value = true
  try {
    ElMessage.info('正在测试当前模型...')
    const res: any = await localAIAPI.embed('这是一条测试文本，用于验证嵌入向量服务。Hello World.')
    if (res && res.success !== false) {
      ElMessage.success(`当前模型测试成功！向量维度: ${res.data?.embedding?.length || res.embedding?.length || 0}`)
    } else {
      ElMessage.error(res?.error || '测试失败，请检查配置')
    }
  } catch (e: any) {
    ElMessage.error('测试失败: ' + e.message)
  } finally {
    testingEmbedding.value = false
  }
}

// 加载Embedding模型
async function loadEmbeddingModels() {
  loadingEmbedding.value = true
  try {
    // 使用新的 API 获取模型列表
    const res: any = await localAIAPI.listEmbedModels()
    if (res && res.success !== false) {
      embeddingModels.value = res.data?.models || []
      embeddingConfig.currentModel = res.data?.current_model || 'text-embedding-v2'
      embeddingConfig.currentProvider = res.data?.current_provider || 'api'
      embeddingConfig.stAvailable = res.data?.st_available || false
    } else {
      // 回退到旧的加载方式
      const configRes: any = await systemAPI.getConfig()
      if (configRes && configRes.success !== false) {
        const data = configRes.data || {}
        if (data.embedding_models) {
          embeddingModels.value = typeof data.embedding_models === 'string' ? JSON.parse(data.embedding_models) : data.embedding_models
        }
        if (data.embedding_model) {
          embeddingConfig.currentModel = data.embedding_model
        }
      }
      // 获取系统Embedding状态
      try {
        const embedRes: any = await systemAPI.getEmbeddingModels()
        if (embedRes && embedRes.success !== false) {
          embeddingConfig.stAvailable = embedRes.data?.st_available || false
        }
      } catch {}
    }
  } catch (e) {
    console.warn('Failed to load embedding models', e)
    // 设置默认值
    embeddingModels.value = [
      { id: 'text-embedding-v2', name: 'text-embedding-v2', model: 'text-embedding-v2', provider: 'api', dimension: 1536, is_builtin: true, is_default: true }
    ]
  } finally {
    loadingEmbedding.value = false
  }
}

// 保存Embedding默认配置
async function saveEmbeddingConfig() {
  try {
    const res: any = await systemAPI.saveConfig({ 
      embedding_model: embeddingConfig.currentModel,
      embedding_models: JSON.stringify(embeddingModels.value)
    })
    if (res && res.success !== false) {
      ElMessage.success('Embedding配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 加载系统配置
async function loadSettings() {
  try {
    const res: any = await systemAPI.getConfig()
    if (res && res.success !== false) {
      const data = res.data || {}
      if (data.app_name) basicConfig.appName = data.app_name
      if (data.theme) basicConfig.theme = data.theme
      // Rerank配置已整合到列表中
    }
  } catch (e) {
    console.warn('Failed to load settings')
  }
}

// 保存基本配置
async function saveBasicConfig() {
  try {
    const res: any = await systemAPI.saveConfig({ app_name: basicConfig.appName, theme: basicConfig.theme })
    if (res && res.success !== false) {
      ElMessage.success('基本配置已保存')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 加载健康状态
async function loadHealth() {
  loadingHealth.value = true
  try {
    const res: any = await systemAPI.healthCheck()
    if (res && res.success !== false) {
      healthData.value = res.data || {}
    }
  } catch (e) {
    console.warn('Failed to load health')
  } finally {
    loadingHealth.value = false
  }
}

function handleProviderChange() {
  modelForm.modelId = ''
}

onMounted(async () => {
  await Promise.all([
    loadAiModels(),
    loadLocalModels(),
    loadEmbeddingModels(),
    loadSettings(),
    loadHealth(),
    loadOllamaConnections(),
    loadRerankModels(),
    loadAIConfigStatus()
  ])
})
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.settings-tabs {
  background: #fff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-overview-card {
  margin-bottom: 16px;
}

.loading-state {
  padding: 20px 0;
}

.status-overview-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.status-card {
  flex: 1;
  min-width: 160px;
  max-width: 220px;
  padding: 16px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-light);
  display: flex;
  gap: 12px;
  align-items: flex-start;
  transition: all 0.3s;

  &.ready {
    background: var(--el-color-success-light-9);
    border-color: var(--el-color-success-light-5);
  }

  &.warn {
    background: var(--el-color-warning-light-9);
    border-color: var(--el-color-warning-light-5);
  }

  .status-icon {
    flex-shrink: 0;
  }

  .status-info {
    .status-title {
      font-weight: 600;
      font-size: 14px;
      color: var(--el-text-color-primary);
    }

    .status-desc {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      margin-top: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .status-provider {
      font-size: 11px;
      color: var(--el-text-color-placeholder);
      margin-top: 2px;
    }
  }
}

.ai-test-section {
  margin-top: 20px;
}

.ai-test-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #606266;
}

.test-response {
  margin-top: 16px;
}

.test-response pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-size: 13px;
  max-height: 200px;
  overflow-y: auto;
}

.health-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.health-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.health-icon.cpu { background: #ecf5ff; color: #409EFF; }
.health-icon.mem { background: #f0f9eb; color: #67C23A; }
.health-icon.disk { background: #fdf6ec; color: #E6A23C; }
.health-icon.status { background: #f0f9eb; color: #67C23A; }
.health-icon.status.healthy { background: #f0f9eb; color: #67C23A; }
.health-icon.status.unhealthy { background: #fef0f0; color: #F56C6C; }

.health-info {
  display: flex;
  flex-direction: column;
}

.health-label {
  font-size: 13px;
  color: #909399;
}

.health-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

/* 通用样式 */
.font-medium {
  font-weight: 500;
}

.text-mono {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #606266;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}

.form-tip {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 本地工具样式 */
.tool-card {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.tool-info h3 {
  margin: 0 0 4px;
  font-size: 15px;
}

.tool-desc {
  color: #909399;
  font-size: 13px;
  margin: 0 0 12px;
}

.tool-actions {
  display: flex;
  gap: 8px;
}

.tool-result {
  margin-top: 12px;
}

.tool-result pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-size: 12px;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  max-height: 100px;
  overflow-y: auto;
}

.tool-result .result-label {
  font-size: 12px;
  color: #909399;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #ebeef5;
}

.service-item:last-child {
  border-bottom: none;
}

/* Embedding 配置样式 */
.embedding-status-row {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 13px;
  color: #606266;
}

.model-cell {
  display: flex;
  align-items: center;
}
</style>
