<template>
  <div class="step1-requirement">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>📝 描述您的应用需求</span>
          <el-button text size="small" @click="$emit('load-example')">
            加载示例
          </el-button>
        </div>
      </template>

      <div class="requirement-section">
        <el-input
          v-model="localRequirement"
          type="textarea"
          :rows="12"
          placeholder="请详细描述您需要的业务应用，包括：

1. 应用名称和用途
2. 需要管理的数据类型（如：客户、订单、产品等）
3. 每个数据类型的字段（如：客户名称、电话、地址等）
4. 数据之间的关系（如：一个客户有多个订单）
5. 需要的业务规则或自动化功能

示例：
我需要一个客户关系管理系统，用于管理客户信息和销售跟进。系统需要包含客户信息表（公司名称、联系人、电话、邮箱）、跟进记录表（沟通内容、沟通时间、下次提醒）、合同管理表（合同金额、签约日期、付款状态）。客户和跟进记录是一对多关系..."
        />

        <div class="tips-section">
          <h4>💡 提示</h4>
          <ul>
            <li>描述越详细，AI 生成的方案越准确</li>
            <li>可以指定字段类型（文本、数字、日期、下拉选择等）</li>
            <li>可以说明数据之间的关系</li>
            <li>可以要求特定的业务规则或自动化功能</li>
          </ul>
        </div>
      </div>

      <!-- 跳过选项（仅在 AI 生成模式下显示） -->
      <div v-if="isGenerationMode" class="skip-options">
        <el-divider />
        <h4>⚙️ 生成选项</h4>
        <div class="skip-checkboxes">
          <el-checkbox v-model="localSkipWorkflow" label="skipWorkflow" size="large">
            跳过工作流生成
            <el-tooltip content="不生成审批流程和工作流，仅创建业务表单" placement="top">
              <el-icon style="margin-left:4px;cursor:help;color:var(--el-text-color-secondary)"><WarningFilled /></el-icon>
            </el-tooltip>
          </el-checkbox>
          <el-checkbox v-model="localSkipAgent" label="skipAgent" size="large">
            跳过智能体创建
            <el-tooltip content="不创建 AI 智能体，仅创建业务表单" placement="top">
              <el-icon style="margin-left:4px;cursor:help;color:var(--el-text-color-secondary)"><WarningFilled /></el-icon>
            </el-tooltip>
          </el-checkbox>
          <el-checkbox v-model="localSkipDashboard" label="skipDashboard" size="large">
            跳过仪表盘生成
            <el-tooltip content="不生成主页仪表盘，仅创建业务表单和菜单" placement="top">
              <el-icon style="margin-left:4px;cursor:help;color:var(--el-text-color-secondary)"><WarningFilled /></el-icon>
            </el-tooltip>
          </el-checkbox>
        </div>
        <div class="skip-hint">
          <el-tag type="warning" size="small">注意</el-tag>
          跳过工作流和智能体可避免因相关模块不完善导致的生成失败，建议首次使用AI生成时勾选。
        </div>
      </div>

      <div class="actions">
        <el-button type="primary" size="large" @click="$emit('generate')" :loading="loading" :disabled="!localRequirement.trim()">
          <el-icon><MagicStick /></el-icon>
          {{ isGenerationMode ? '开始生成应用' : '生成设计方案' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MagicStick, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  requirement: string
  loading: boolean
  isGenerationMode?: boolean
  skipWorkflow?: boolean
  skipAgent?: boolean
  skipDashboard?: boolean
}>()

const emit = defineEmits([
  'update:requirement',
  'update:skipWorkflow',
  'update:skipAgent',
  'update:skipDashboard',
  'generate',
  'load-example'
])

const localRequirement = computed({
  get: () => props.requirement,
  set: (val) => emit('update:requirement', val)
})

const localSkipWorkflow = computed({
  get: () => props.skipWorkflow ?? false,
  set: (val) => emit('update:skipWorkflow', val)
})

const localSkipAgent = computed({
  get: () => props.skipAgent ?? false,
  set: (val) => emit('update:skipAgent', val)
})

const localSkipDashboard = computed({
  get: () => props.skipDashboard ?? false,
  set: (val) => emit('update:skipDashboard', val)
})
</script>

<style scoped lang="scss">
.step1-requirement {
  max-width: 900px;
  margin: 0 auto;
}

.main-card {
  :deep(.el-card__header) {
    font-size: 16px;
    font-weight: 500;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.requirement-section {
  margin-bottom: 20px;
}

.tips-section {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;

  h4 {
    margin: 0 0 12px;
    color: var(--el-text-color-primary);
  }

  ul {
    margin: 0;
    padding-left: 20px;
    color: var(--el-text-color-secondary);

    li {
      margin-bottom: 8px;
    }
  }
}

.skip-options {
  margin-bottom: 20px;

  h4 {
    margin: 0 0 12px;
    color: var(--el-text-color-primary);
    font-size: 15px;
  }

  .skip-checkboxes {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 12px;
  }

  .skip-hint {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--el-color-warning-light-9);
    border-radius: 6px;
  }
}

.actions {
  display: flex;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);

  .el-button {
    min-width: 200px;
  }
}
</style>
