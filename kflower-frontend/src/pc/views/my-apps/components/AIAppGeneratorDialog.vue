<template>
  <el-dialog
    v-model="visible"
    title="AI 应用生成"
    width="600px"
    :close-on-click-modal="false"
  >
    <div class="ai-generator">
      <!-- 输入区域 -->
      <el-form label-position="top">
        <el-form-item label="应用名称（可选）">
          <el-input
            v-model="appName"
            placeholder="AI 会从描述中自动推断"
          />
        </el-form-item>

        <el-form-item label="需求描述">
          <el-input
            v-model="description"
            type="textarea"
            :rows="4"
            placeholder="描述您需要的业务系统，例如：创建一个采购管理系统，包括采购申请、审批流程、供应商管理、订单跟踪"
          />
          <div class="hint" style="margin-top:8px;font-size:12px;color:var(--el-text-color-secondary)">
            描述越详细，生成的应用越准确。建议包含：业务场景、需要的表单、审批流程、数据关联关系。
          </div>
        </el-form-item>

        <el-form-item label="生成选项">
          <el-checkbox-group v-model="options">
            <el-checkbox label="skipWorkflow">跳过工作流生成</el-checkbox>
            <el-checkbox label="skipDashboard">跳过仪表盘生成</el-checkbox>
            <el-checkbox label="skipAgent">跳过智能体创建</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <!-- 生成进度 -->
      <div v-if="generating" class="progress-section">
        <el-progress :percentage="progressPercent" :stroke-width="8" />
        <div class="progress-text">{{ progressText }}</div>
      </div>

      <!-- 生成结果预览 -->
      <div v-if="result && !generating" class="result-preview">
        <el-alert
          :title="`生成成功！应用: ${result.app?.name || '未命名'}`"
          type="success"
          :closable="false"
          show-icon
          style="margin-bottom:16px"
        />

        <div class="result-summary">
          <div class="summary-item">
            <el-icon><Document /></el-icon>
            <span>模板: {{ result.templates?.length || 0 }} 个</span>
          </div>
          <div class="summary-item">
            <el-icon><Share /></el-icon>
            <span>工作流: {{ result.workflows?.length || 0 }} 个</span>
          </div>
          <div class="summary-item">
            <el-icon><Connection /></el-icon>
            <span>关系: {{ result.relations?.length || 0 }} 个</span>
          </div>
          <div class="summary-item">
            <el-icon><Grid /></el-icon>
            <span>仪表盘: {{ result.dashboard ? '已配置' : '无' }}</span>
          </div>
          <div class="summary-item">
            <el-icon><User /></el-icon>
            <span>智能体: {{ result.agents?.length || 0 }} 个</span>
          </div>
        </div>

        <!-- 模板列表 -->
        <div v-if="result.templates?.length" class="templates-list">
          <div class="section-title">生成的模板</div>
          <el-tag v-for="tpl in result.templates" :key="tpl.id" style="margin-right:8px">
            {{ tpl.name }}
          </el-tag>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        @click="doGenerate"
        :loading="generating"
        :disabled="!description.trim()"
      >
        开始生成
      </el-button>
      <el-button
        v-if="result && !generating"
        type="success"
        @click="openApp"
      >
        打开应用
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Share, Connection, Grid, User } from '@element-plus/icons-vue'
import appAPI from '../../common/api/myApps'

const visible = defineModel<boolean>('visible', { default: false })

const router = useRouter()

const appName = ref('')
const description = ref('')
const options = ref<string[]>([])
const generating = ref(false)
const result = ref<any>(null)
const currentStep = ref(0)

const progressPercent = computed(() => {
  if (!generating.value) return 100
  const steps = [
    '分析需求',
    '生成模板',
    '生成工作流',
    '建立关系',
    '生成仪表盘',
    '创建智能体',
    '组装应用'
  ]
  return Math.round((currentStep.value / steps.length) * 100)
})

const progressText = computed(() => {
  const steps = [
    '正在分析需求...',
    '正在生成表单模板...',
    '正在创建工作流...',
    '正在建立表单关系...',
    '正在配置仪表盘...',
    '正在创建智能体...',
    '正在组装应用...'
  ]
  return steps[currentStep.value] || '准备开始...'
})

// 模拟进度更新（后端未返回实时进度）
watch(generating, (val) => {
  if (val) {
    currentStep.value = 0
    const timer = setInterval(() => {
      if (currentStep.value < 6 && generating.value) {
        currentStep.value++
      } else {
        clearInterval(timer)
      }
    }, 1500)
  }
})

const doGenerate = async () => {
  if (!description.value.trim()) {
    ElMessage.warning('请输入需求描述')
    return
  }

  generating.value = true
  result.value = null

  try {
    const res = await appAPI.aiGenerate(
      description.value.trim(),
      appName.value || undefined,
      {
        skipWorkflow: options.value.includes('skipWorkflow'),
        skipDashboard: options.value.includes('skipDashboard'),
        skipAgent: options.value.includes('skipAgent'),
      }
    )

    result.value = res.data
    currentStep.value = 7 // 完成
    ElMessage.success('应用生成成功！')
  } catch (e: any) {
    console.error('AI 生成失败:', e)
    ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

const openApp = () => {
  if (result.value?.app?.id) {
    router.push(`/my-apps/${result.value.app.id}/design`)
    visible.value = false
  }
}
</script>

<style scoped>
.ai-generator {
  min-height: 200px;
}
.progress-section {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}
.progress-text {
  margin-top: 12px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  text-align: center;
}
.result-preview {
  margin-top: 16px;
}
.result-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}
.summary-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.templates-list {
  margin-top: 12px;
}
.section-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
</style>