<template>
  <div class="ai-app-designer">
    <!-- AI未配置警告横幅 -->
    <div v-if="configWarning" class="ai-warning-banner">
      <el-alert type="warning" :closable="false" show-icon>
        <template #title>
          <span>⚠️ AI 尚未配置完整，部分功能可能不可用</span>
        </template>
        <template #default>
          <div class="warning-content">
            <span v-for="(w, i) in configWarnings" :key="i" class="warning-item">{{ w }}</span>
          </div>
          <el-button type="warning" size="small" @click="goToAIConfig" style="margin-top:8px">
            <el-icon><Setting /></el-icon> 去配置 AI
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- 顶部导航 -->
    <div class="designer-header">
      <div class="header-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h2>AI 应用设计助手</h2>
      </div>
      <div class="header-right">
        <!-- AI 模型状态指示器 -->
        <div class="model-status" :class="{ configured: isAIConfigured }">
          <el-icon :color="isAIConfigured ? '#67c23a' : '#e6a23c'">
            <component :is="isAIConfigured ? 'CircleCheckFilled' : 'WarningFilled'" />
          </el-icon>
          <span class="model-desc">{{ modelStatusDesc }}</span>
        </div>

        <!-- AI 模型选择 -->
        <el-select
          v-model="selectedModelId"
          size="small"
          class="model-select"
          placeholder="选择AI模型"
          :disabled="!isAIConfigured"
          style="width:180px"
        >
          <el-option
            v-for="model in availableModels"
            :key="model.modelId || model.id"
            :label="model.modelName || model.name || model.id || model.modelId"
            :value="model.modelId || model.id"
          >
            <span>{{ model.modelName || model.name || model.id || model.modelId }}</span>
            <el-tag size="small" type="info" style="margin-left:8px">{{ model.provider }}</el-tag>
          </el-option>
        </el-select>
        <el-button size="small" @click="goToAIConfig">
          <el-icon><Setting /></el-icon> AI配置
        </el-button>
      </div>
    </div>

    <!-- 步骤条 -->
    <div class="steps-container">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="需求描述" description="描述应用需求" />
        <el-step title="方案确认" description="确认设计方案" />
        <el-step title="表单生成" description="生成业务表单" />
        <el-step title="菜单配置" description="配置应用菜单" />
        <el-step title="主页配置" description="设计应用主页" />
        <el-step title="完成创建" description="确认并创建应用" />
      </el-steps>
    </div>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 需求描述 -->
      <Step1Requirement
        v-if="currentStep === 0"
        v-model:requirement="requirement"
        :loading="generating"
        @generate="generateDesign"
        @load-example="loadExample"
      />

      <!-- 步骤2: 方案确认 -->
      <Step2DesignConfirm
        v-if="currentStep === 1"
        v-model:design="designResult"
        @prev="currentStep--"
        @next="goToStep3"
        @regenerate="currentStep = 0"
      />

      <!-- 步骤3: 表单生成 -->
      <Step3FormGeneration
        v-if="currentStep === 2"
        :design="designResult"
        :templates="generatedTemplates"
        :generating="generatingForms"
        @prev="currentStep--"
        @next="goToStep4"
        @generate-forms="generateForms"
        @update-template="updateTemplate"
      />

      <!-- 步骤4: 菜单配置 -->
      <Step4MenuConfig
        v-if="currentStep === 3"
        :design="designResult"
        :templates="generatedTemplates"
        v-model:menus="menuConfig"
        @prev="currentStep--"
        @next="goToStep5"
      />

      <!-- 步骤5: 主页配置 -->
      <Step5HomepageConfig
        v-if="currentStep === 4"
        v-model:homepage="homepageConfig"
        :design="designResult"
        :templates="generatedTemplates"
        @prev="currentStep--"
        @next="goToStep6"
      />

      <!-- 步骤6: 完成创建 -->
      <Step6FinalConfirm
        v-if="currentStep === 5"
        :design="designResult"
        :templates="generatedTemplates"
        :menus="menuConfig"
        :homepage="homepageConfig"
        :app-info="appInfo"
        :creating="creating"
        @prev="currentStep--"
        @create="createApplication"
        @update-app-info="appInfo = $event"
      />
    </div>

    <!-- 完成对话框 -->
    <el-dialog v-model="showSuccessDialog" title="🎉 应用创建成功" width="500px" :close-on-click-modal="false">
      <div class="success-content">
        <el-result icon="success" :title="createdApp?.name" sub-title="应用已成功创建并发布">
          <template #extra>
            <el-button type="primary" @click="enterApp">进入应用</el-button>
            <el-button @click="goToApps">返回应用列表</el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Setting, CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue'
import { useAIStore } from '@/common/store/ai'
import { appAPI } from '@/common/api/myApps'
import { templateAPI } from '@/common/api'
import { agentAPI } from '@/common/api'

// 导入步骤组件
import Step1Requirement from './components/ai-designer/Step1Requirement.vue'
import Step2DesignConfirm from './components/ai-designer/Step2DesignConfirm.vue'
import Step3FormGeneration from './components/ai-designer/Step3FormGeneration.vue'
import Step4MenuConfig from './components/ai-designer/Step4MenuConfig.vue'
import Step5HomepageConfig from './components/ai-designer/Step5HomepageConfig.vue'
import Step6FinalConfirm from './components/ai-designer/Step6FinalConfirm.vue'

const router = useRouter()
const aiStore = useAIStore()

// 状态
const currentStep = ref(0)
const selectedModelId = ref('')
const requirement = ref('')
const generating = ref(false)
const generatingForms = ref(false)
const creating = ref(false)
const showSuccessDialog = ref(false)
const createdApp = ref<any>(null)

// 从配置状态获取可用的模型列表
const availableModels = computed(() => {
  const status = aiStore.configStatus
  if (status?.chat?.models?.length) {
    return status.chat.models
  }
  return aiStore.models
})

// AI是否已配置
const isAIConfigured = computed(() => aiStore.isAIConfigured())

// 配置警告信息
const configWarning = computed(() => {
  const status = aiStore.configStatus
  return status && (!status.ready || (status.warnings && status.warnings.length > 0))
})

const configWarnings = computed(() => {
  return aiStore.configStatus?.warnings || []
})

// 模型状态描述
const modelStatusDesc = computed(() => {
  const status = aiStore.configStatus
  if (!status) return '加载中...'
  if (!status.ready) return 'AI未配置'
  const model = status.chat.default_model
  if (!model) return '未选择模型'
  return `${model.name || model.id} (${model.provider})`
})

// 设计结果
const designResult = ref<any>({
  app_name: '',
  description: '',
  templates: [],
  relations: [],
  plugins: []
})

// 生成的模板
const generatedTemplates = ref<any[]>([])

// 菜单配置
const menuConfig = ref<any[]>([])

// 主页配置
const homepageConfig = ref<any>({
  type: 'dashboard',
  title: '',
  description: '',
  widgets: []
})

// 应用信息
const appInfo = ref({
  name: '',
  description: '',
  icon: 'Document',
  theme: 'light'
})

// 初始化
onMounted(async () => {
  // 并行加载模型配置和状态
  await Promise.all([
    aiStore.loadModels(),
    aiStore.loadConfigStatus()
  ])
  // 设置默认模型
  if (aiStore.currentModel) {
    selectedModelId.value = aiStore.currentModel.modelId
  } else if (aiStore.configStatus?.chat?.default_model?.modelId) {
    selectedModelId.value = aiStore.configStatus.chat.default_model.modelId
  }
})

// 加载示例
function loadExample() {
  requirement.value = `我需要一个客户关系管理系统，包含以下功能：

1. 客户信息管理：记录公司名称、联系人、电话、邮箱、地址、行业类型、客户等级
2. 跟进记录：记录每次与客户的沟通内容、沟通时间、跟进人、下次跟进提醒
3. 合同管理：合同编号、签约日期、合同金额、付款方式、合同状态

要求：
- 客户和跟进记录是一对多关系
- 客户和合同是一对多关系
- 合同金额变更时自动记录日志
- 跟进提醒到期时发送通知`
}

// 生成设计方案
async function generateDesign() {
  if (!requirement.value.trim()) {
    ElMessage.warning('请输入应用需求描述')
    return
  }
  if (!isAIConfigured.value) {
    ElMessage.warning('AI 尚未配置或配置无效，请先在「AI配置」中完成配置')
    return
  }
  if (!selectedModelId.value) {
    ElMessage.warning('请选择AI模型')
    return
  }

  generating.value = true
  try {
    const prompt = `请根据以下需求设计一个业务应用，返回标准的JSON格式设计方案：

需求描述：
${requirement.value}

请返回以下格式的JSON（不要包含任何其他文字，只返回JSON）：
{
  "app_name": "应用名称",
  "description": "应用描述",
  "templates": [
    {
      "name": "表单名称",
      "description": "表单描述",
      "category": "分类",
      "fields": [
        {
          "name": "字段名",
          "label": "显示名称",
          "type": "字段类型(text/number/select/date/textarea/relation等)",
          "required": true/false,
          "options": ["选项1", "选项2"]
        }
      ]
    }
  ],
  "relations": [
    {
      "from_template": "源表单名称",
      "to_template": "目标表单名称",
      "relation_type": "belongs_to/has_many",
      "field": "关联字段名"
    }
  ],
  "plugins": [
    {
      "name": "插件名称",
      "trigger_event": "before_save/after_save/on_load",
      "description": "插件功能描述"
    }
  ],
  "menus": [
    {
      "label": "菜单名称",
      "icon": "菜单图标",
      "template_name": "关联的表单名称"
    }
  ],
  "homepage": {
    "type": "dashboard",
    "title": "主页标题",
    "widgets": [
      {
        "type": "stat/list/chart",
        "title": "组件标题",
        "template_name": "数据源表单"
      }
    ]
  }
}`

    const res: any = await agentAPI.chat({
      message: prompt,
      model: selectedModelId.value,
      use_rag: false,
      enable_tools: false
    }, { timeout: 120000 })

    const content = res.response || res.message || res.content || ''

    let parsedDesign = null

    const codeBlockMatch = content.match(/```(?:json)?\s*\n?([\s\S]*?)\n?```/)
    if (codeBlockMatch) {
      try {
        parsedDesign = JSON.parse(codeBlockMatch[1].trim())
      } catch {}
    }

    if (!parsedDesign) {
      const firstBrace = content.indexOf('{')
      const lastBrace = content.lastIndexOf('}')
      if (firstBrace >= 0 && lastBrace > firstBrace) {
        const jsonStr = content.substring(firstBrace, lastBrace + 1)
        try {
          parsedDesign = JSON.parse(jsonStr)
        } catch (e: any) {
          console.error('JSON parse error, raw content:', content)
          throw new Error('AI返回的JSON格式有误: ' + e.message + '\n\n原始内容:\n' + content.substring(0, 500))
        }
      }
    }

    if (!parsedDesign) {
      throw new Error('无法从AI返回中解析设计方案，请检查AI模型输出是否正常')
    }

    designResult.value = parsedDesign

    appInfo.value.name = parsedDesign.app_name || ''
    appInfo.value.description = parsedDesign.description || ''

    if (parsedDesign.homepage) {
      homepageConfig.value = parsedDesign.homepage
    }

    currentStep.value = 1
    ElMessage.success('设计方案生成成功')
  } catch (e: any) {
    console.error('Generate design error:', e)
    let errMsg = e.message || '请检查AI配置'
    if (errMsg.length > 200) {
      errMsg = errMsg.substring(0, 200) + '...'
    }
    ElMessage.error('生成设计方案失败：' + errMsg)
  } finally {
    generating.value = false
  }
}

// 进入步骤3
function goToStep3() {
  generatedTemplates.value = designResult.value.templates?.map((t: any) => ({
    ...t,
    _status: 'pending',
    _id: null
  })) || []
  currentStep.value = 2
}

// 生成表单
async function generateForms() {
  generatingForms.value = true
  generatedTemplates.value = []

  for (const tpl of designResult.value.templates || []) {
    const tplWithStatus = { ...tpl, _status: 'generating', _id: null }
    generatedTemplates.value.push(tplWithStatus)

    try {
      const templateData = {
        name: tpl.name,
        description: tpl.description,
        category: tpl.category || '业务表单',
        config: {
          fields: tpl.fields?.map((f: any) => ({
            name: f.name,
            label: f.label,
            type: f.type || 'text',
            required: f.required || false,
            options: f.options || []
          })) || []
        },
        is_published: true,
        is_public: false
      }

      const res: any = await templateAPI.create(templateData)

      const idx = generatedTemplates.value.findIndex(t => t.name === tpl.name)
      if (idx >= 0) {
        generatedTemplates.value[idx]._status = 'success'
        generatedTemplates.value[idx]._id = res.id || res.data?.id
      }

      ElMessage.success(`表单「${tpl.name}」创建成功`)
    } catch (e: any) {
      console.error(`Create template ${tpl.name} error:`, e)
      const idx = generatedTemplates.value.findIndex(t => t.name === tpl.name)
      if (idx >= 0) {
        generatedTemplates.value[idx]._status = 'error'
        generatedTemplates.value[idx]._error = e.message
      }
      ElMessage.error(`表单「${tpl.name}」创建失败`)
    }
  }

  generatingForms.value = false
}

// 更新模板
function updateTemplate(index: number, data: any) {
  if (generatedTemplates.value[index]) {
    generatedTemplates.value[index] = { ...generatedTemplates.value[index], ...data }
  }
}

// 进入步骤4
function goToStep4() {
  menuConfig.value = designResult.value.menus?.map((m: any, idx: number) => {
    const template = generatedTemplates.value.find(t => t.name === m.template_name)
    return {
      id: `temp_${idx}`,
      label: m.label,
      icon: m.icon || 'Document',
      template_id: template?._id || null,
      template_name: m.template_name,
      menu_order: idx,
      is_visible: true
    }
  }) || []

  if (menuConfig.value.length === 0) {
    menuConfig.value = generatedTemplates.value.map((t, idx) => ({
      id: `temp_${idx}`,
      label: t.name,
      icon: 'Document',
      template_id: t._id,
      template_name: t.name,
      menu_order: idx,
      is_visible: true
    }))
  }

  currentStep.value = 3
}

// 进入步骤5
function goToStep5() {
  if (!homepageConfig.value.widgets?.length) {
    homepageConfig.value = {
      type: 'dashboard',
      title: `${appInfo.value.name}主页`,
      description: appInfo.value.description,
      widgets: generatedTemplates.value.map((t, idx) => ({
        id: `widget_${idx}`,
        type: 'stat',
        title: t.name,
        template_id: t._id,
        template_name: t.name,
        x: (idx % 3) * 8,
        y: Math.floor(idx / 3) * 4,
        w: 8,
        h: 4
      }))
    }
  }
  currentStep.value = 4
}

// 进入步骤6
function goToStep6() {
  currentStep.value = 5
}

// 创建应用
async function createApplication() {
  if (!appInfo.value.name) {
    ElMessage.warning('请输入应用名称')
    return
  }

  creating.value = true
  try {
    const appRes: any = await appAPI.create({
      name: appInfo.value.name,
      description: appInfo.value.description,
      icon: appInfo.value.icon,
      theme: appInfo.value.theme
    })

    const appId = appRes.id || appRes.data?.id
    createdApp.value = { ...appRes, id: appId }

    for (const menu of menuConfig.value) {
      if (menu.template_id) {
        try {
          await appAPI.addMenu(appId, {
            template_id: menu.template_id,
            menu_label: menu.label,
            menu_icon: menu.icon,
            menu_order: menu.menu_order,
            parent_id: undefined
          })
        } catch (e) {
          console.error('Add menu error:', e)
        }
      }
    }

    for (const rel of designResult.value.relations || []) {
      const fromTpl = generatedTemplates.value.find(t => t.name === rel.from_template)
      const toTpl = generatedTemplates.value.find(t => t.name === rel.to_template)
      if (fromTpl?._id && toTpl?._id) {
        try {
          await appAPI.addRelation(appId, {
            from_template_id: fromTpl._id,
            from_field_name: rel.field,
            to_template_id: toTpl._id,
            relation_type: rel.relation_type
          })
        } catch (e) {
          console.error('Add relation error:', e)
        }
      }
    }

    await appAPI.publish(appId)

    if (homepageConfig.value.widgets?.length) {
      try {
        await appAPI.saveDashboard(appId, {
          pages: [{
            title: '首页',
            widgets: homepageConfig.value.widgets
          }]
        })
      } catch (e) {
        console.error('Save dashboard error:', e)
      }
    }

    showSuccessDialog.value = true
  } catch (e: any) {
    console.error('Create application error:', e)
    ElMessage.error('创建应用失败：' + (e.message || ''))
  } finally {
    creating.value = false
  }
}

// 导航
function goBack() {
  if (currentStep.value > 0) {
    ElMessageBox.confirm('确定要退出AI设计助手吗？当前进度将丢失。', '确认退出', {
      type: 'warning'
    }).then(() => {
      router.push('/my-apps')
    }).catch(() => {})
  } else {
    router.push('/my-apps')
  }
}

function goToAIConfig() {
  router.push('/settings?tab=ai')
}

function goToApps() {
  showSuccessDialog.value = false
  router.push('/my-apps')
}

function enterApp() {
  showSuccessDialog.value = false
  if (createdApp.value?.id) {
    router.push(`/app/${createdApp.value.id}`)
  }
}
</script>

<style scoped lang="scss">
.ai-app-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.ai-warning-banner {
  padding: 8px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  flex-shrink: 0;

  .warning-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 4px;
  }

  .warning-item {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

.designer-header {
  height: 60px;
  padding: 0 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h2 {
      margin: 0;
      font-size: 18px;
      color: var(--el-text-color-primary);
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;

    .model-status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 16px;
      background: var(--el-fill-color-light);
      font-size: 13px;
      color: var(--el-text-color-secondary);
      border: 1px solid var(--el-border-color-light);

      &.configured {
        background: var(--el-color-success-light-9);
        border-color: var(--el-color-success-light-5);
        color: var(--el-color-success);
      }

      .model-desc {
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

.steps-container {
  padding: 20px 40px 0;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}

.step-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.success-content {
  padding: 20px;
}
</style>
