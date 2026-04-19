<template>
  <div class="ai-designer">
    <div class="ai-header">
      <h3>🤖 AI 设计助手</h3>
      <p class="subtitle">用自然语言描述你的应用需求，AI 将自动生成应用结构</p>
    </div>

    <div class="ai-content">
      <!-- 输入区域 -->
      <el-card class="input-card">
        <template #header>
          <span>描述你的应用需求</span>
        </template>
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="6"
          placeholder="例如：我需要一个客户关系管理系统，包含客户信息、跟进记录、合同管理三个模块。客户信息需要记录公司名称、联系人、电话、地址等字段..."
        />
        <div class="input-actions">
          <el-button 
            type="primary" 
            @click="generateDesign" 
            :loading="generating"
            :disabled="!prompt.trim()"
          >
            <el-icon><MagicStick /></el-icon> 生成设计方案
          </el-button>
          <el-button @click="loadExample">查看示例</el-button>
        </div>
      </el-card>

      <!-- 生成结果 -->
      <el-card v-if="designResult" class="result-card">
        <template #header>
          <div class="result-header">
            <span>📋 设计方案</span>
            <el-button type="success" size="small" @click="applyDesign" :loading="applying">
              <el-icon><Check /></el-icon> 应用此方案
            </el-button>
          </div>
        </template>

        <div class="design-section">
          <h4>应用结构</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="应用名称">{{ designResult.app_name }}</el-descriptions-item>
            <el-descriptions-item label="模块数量">{{ designResult.templates?.length || 0 }} 个</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="design-section" v-if="designResult.templates?.length">
          <h4>表单模板</h4>
          <el-collapse>
            <el-collapse-item 
              v-for="(tpl, idx) in designResult.templates" 
              :key="idx"
              :title="tpl.name"
            >
              <p class="tpl-desc">{{ tpl.description }}</p>
              <el-tag v-for="field in tpl.fields" :key="field.name" size="small" class="field-tag">
                {{ field.label }} ({{ field.type }})
              </el-tag>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div class="design-section" v-if="designResult.relations?.length">
          <h4>表单关系</h4>
          <el-timeline>
            <el-timeline-item 
              v-for="(rel, idx) in designResult.relations" 
              :key="idx"
              :type="rel.relation_type === 'belongs_to' ? 'primary' : 'success'"
            >
              {{ getRelationDesc(rel) }}
            </el-timeline-item>
          </el-timeline>
        </div>

        <div class="design-section" v-if="designResult.plugins?.length">
          <h4>业务插件</h4>
          <el-table :data="designResult.plugins" size="small">
            <el-table-column prop="name" label="插件名称" />
            <el-table-column prop="trigger_event" label="触发时机">
              <template #default="{ row }">
                <el-tag size="small">{{ row.trigger_event }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- 历史记录 -->
      <el-card v-if="history.length" class="history-card">
        <template #header>
          <span>📝 历史记录</span>
        </template>
        <el-timeline>
          <el-timeline-item 
            v-for="(item, idx) in history" 
            :key="idx"
            :timestamp="item.time"
          >
            <el-link @click="loadHistory(item)">{{ item.prompt.substring(0, 50) }}...</el-link>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Check } from '@element-plus/icons-vue'
import { appAPI } from '@/common/api/myApps'

const props = defineProps<{
  appId: number
}>()

const prompt = ref('')
const generating = ref(false)
const applying = ref(false)
const designResult = ref<any>(null)
const history = ref<any[]>([])

const examplePrompt = `我需要一个客户关系管理系统，包含以下功能：

1. 客户信息管理：记录公司名称、联系人、电话、邮箱、地址、行业类型、客户等级
2. 跟进记录：记录每次与客户的沟通内容、沟通时间、跟进人、下次跟进提醒
3. 合同管理：合同编号、签约日期、合同金额、付款方式、合同状态

要求：
- 客户和跟进记录是一对多关系
- 客户和合同是一对多关系
- 合同金额变更时自动记录日志
- 跟进提醒到期时发送通知`

function loadExample() {
  prompt.value = examplePrompt
}

async function generateDesign() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入应用需求描述')
    return
  }

  generating.value = true
  try {
    // 调用后端 AI 设计接口
    const res: any = await appAPI.generateAIDesign({
      app_id: props.appId,
      prompt: prompt.value
    })
    
    designResult.value = res.data || res
    
    // 添加到历史记录
    history.value.unshift({
      prompt: prompt.value,
      result: designResult.value,
      time: new Date().toLocaleString()
    })
    
    ElMessage.success('设计方案生成成功')
  } catch (e: any) {
    ElMessage.error('生成失败：' + (e.message || 'AI服务暂不可用'))
    
    // 演示模式：生成模拟数据
    generateMockDesign()
  } finally {
    generating.value = false
  }
}

function generateMockDesign() {
  // 模拟 AI 返回的设计方案
  designResult.value = {
    app_name: '客户关系管理系统',
    templates: [
      {
        name: '客户信息',
        description: '存储客户的基本信息',
        fields: [
          { name: 'company_name', label: '公司名称', type: 'text', required: true },
          { name: 'contact_name', label: '联系人', type: 'text', required: true },
          { name: 'phone', label: '电话', type: 'text' },
          { name: 'email', label: '邮箱', type: 'text' },
          { name: 'address', label: '地址', type: 'textarea' },
          { name: 'industry', label: '行业类型', type: 'select' },
          { name: 'level', label: '客户等级', type: 'select' }
        ]
      },
      {
        name: '跟进记录',
        description: '记录客户沟通历史',
        fields: [
          { name: 'customer_id', label: '关联客户', type: 'relation' },
          { name: 'content', label: '沟通内容', type: 'textarea', required: true },
          { name: 'contact_time', label: '沟通时间', type: 'datetime' },
          { name: 'follow_up_by', label: '跟进人', type: 'text' },
          { name: 'next_reminder', label: '下次提醒', type: 'datetime' }
        ]
      },
      {
        name: '合同管理',
        description: '管理客户合同信息',
        fields: [
          { name: 'contract_no', label: '合同编号', type: 'text', required: true },
          { name: 'customer_id', label: '关联客户', type: 'relation' },
          { name: 'sign_date', label: '签约日期', type: 'date' },
          { name: 'amount', label: '合同金额', type: 'number' },
          { name: 'payment_method', label: '付款方式', type: 'select' },
          { name: 'status', label: '合同状态', type: 'select' }
        ]
      }
    ],
    relations: [
      { from_template: '跟进记录', to_template: '客户信息', relation_type: 'belongs_to', field: 'customer_id' },
      { from_template: '合同管理', to_template: '客户信息', relation_type: 'belongs_to', field: 'customer_id' }
    ],
    plugins: [
      { name: '合同金额变更日志', trigger_event: 'after_save', description: '记录合同金额变更历史' },
      { name: '跟进提醒通知', trigger_event: 'on_load', description: '检查并发送跟进提醒' }
    ]
  }
  
  history.value.unshift({
    prompt: prompt.value,
    result: designResult.value,
    time: new Date().toLocaleString() + ' (演示模式)'
  })
  
  ElMessage.info('当前为演示模式，使用模拟数据')
}

function getRelationDesc(rel: any) {
  const typeMap: Record<string, string> = {
    belongs_to: '属于',
    has_many: '拥有',
    many_to_many: '多对多'
  }
  return `${rel.from_template} ${typeMap[rel.relation_type] || rel.relation_type} ${rel.to_template} (通过 ${rel.field} 字段)`
}

async function applyDesign() {
  if (!designResult.value) return

  try {
    await ElMessageBox.confirm(
      `将创建 ${designResult.value.templates?.length || 0} 个表单模板、${designResult.value.relations?.length || 0} 个关系、${designResult.value.plugins?.length || 0} 个插件。确定应用此方案吗？`,
      '确认应用',
      { type: 'warning' }
    )
  } catch {
    return
  }

  applying.value = true
  try {
    await appAPI.applyAIDesign(props.appId, designResult.value)
    ElMessage.success('设计方案已应用')
    designResult.value = null
    prompt.value = ''
  } catch (e: any) {
    ElMessage.error('应用失败：' + (e.message || ''))
  } finally {
    applying.value = false
  }
}

function loadHistory(item: any) {
  prompt.value = item.prompt
  designResult.value = item.result
}

onMounted(() => {
  // 加载历史记录（从 localStorage）
  const saved = localStorage.getItem(`ai_design_history_${props.appId}`)
  if (saved) {
    try {
      history.value = JSON.parse(saved)
    } catch {}
  }
})
</script>

<style scoped>
.ai-designer {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.ai-header {
  text-align: center;
  margin-bottom: 24px;
}

.ai-header h3 {
  margin: 0 0 8px;
  font-size: 24px;
}

.subtitle {
  color: var(--el-text-color-secondary);
  margin: 0;
}

.ai-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-card .el-card__body {
  padding: 20px;
}

.input-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.design-section {
  margin-bottom: 20px;
}

.design-section h4 {
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.tpl-desc {
  color: var(--el-text-color-secondary);
  margin: 0 0 12px;
}

.field-tag {
  margin: 4px;
}

.history-card {
  margin-top: 20px;
}
</style>
