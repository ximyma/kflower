<template>
  <div class="step6-final-confirm">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>✅ 确认并创建应用</span>
        </div>
      </template>

      <!-- 应用信息编辑 -->
      <div class="section">
        <h3>应用信息</h3>
        <el-form :model="localAppInfo" label-width="100px">
          <el-form-item label="应用名称" required>
            <el-input v-model="localAppInfo.name" placeholder="请输入应用名称" />
          </el-form-item>
          <el-form-item label="应用描述">
            <el-input v-model="localAppInfo.description" type="textarea" :rows="2" placeholder="应用描述" />
          </el-form-item>
          <el-form-item label="图标">
            <el-select v-model="localAppInfo.icon" placeholder="选择图标">
              <el-option label="文档" value="Document" />
              <el-option label="文件夹" value="Folder" />
              <el-option label="购物车" value="ShoppingCart" />
              <el-option label="客户" value="User" />
              <el-option label="商品" value="Goods" />
              <el-option label="数据" value="DataLine" />
              <el-option label="设置" value="Setting" />
            </el-select>
          </el-form-item>
          <el-form-item label="主题">
            <el-radio-group v-model="localAppInfo.theme">
              <el-radio-button label="light">浅色</el-radio-button>
              <el-radio-button label="dark">深色</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <!-- 跳过选项提示 -->
      <div v-if="hasSkipOptions" class="skip-summary">
        <el-alert title="生成选项" type="warning" :closable="false" show-icon>
          <template #default>
            <div class="skip-items">
              <span v-if="skipWorkflow">✅ 跳过工作流</span>
              <span v-if="skipAgent">✅ 跳过智能体</span>
              <span v-if="skipDashboard">✅ 跳过仪表盘</span>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 创建内容预览 -->
      <div class="section">
        <h3>即将创建的内容</h3>
        <div class="preview-stats">
          <el-statistic title="业务表单" :value="successTemplates.length">
            <template #suffix>个</template>
          </el-statistic>
          <el-statistic title="应用菜单" :value="menus.length">
            <template #suffix>个</template>
          </el-statistic>
          <el-statistic title="表单关系" :value="design.relations?.length || 0">
            <template #suffix>个</template>
          </el-statistic>
          <el-statistic title="主页组件" :value="skipDashboard ? 0 : (homepage.widgets?.length || 0)">
            <template #suffix>个</template>
          </el-statistic>
        </div>
      </div>

      <!-- 详细内容 -->
      <div class="section">
        <h3>详细内容</h3>
        
        <el-collapse v-model="activeCollapse">
          <!-- 表单列表 -->
          <el-collapse-item title="业务表单" name="templates">
            <el-table :data="successTemplates" size="small">
              <el-table-column prop="name" label="表单名称" />
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
              <el-table-column prop="fields?.length" label="字段数" width="80">
                <template #default="{ row }">
                  {{ row.fields?.length || 0 }}
                </template>
              </el-table-column>
              <el-table-column prop="_id" label="模板ID" width="80">
                <template #default="{ row }">
                  <el-tag size="small" type="success">已创建</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>

          <!-- 菜单列表 -->
          <el-collapse-item title="应用菜单" name="menus">
            <el-table :data="menus" size="small">
              <el-table-column prop="label" label="菜单名称" />
              <el-table-column prop="template_name" label="关联表单" />
              <el-table-column prop="icon" label="图标" width="80" />
            </el-table>
          </el-collapse-item>

          <!-- 关系列表 -->
          <el-collapse-item title="表单关系" name="relations" v-if="design.relations?.length">
            <el-table :data="design.relations" size="small">
              <el-table-column prop="from_template" label="源表单" />
              <el-table-column prop="relation_type" label="关系">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.relation_type === 'belongs_to' ? '属于' : '拥有' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="to_template" label="目标表单" />
            </el-table>
          </el-collapse-item>

          <!-- 主页配置 -->
          <el-collapse-item v-if="!skipDashboard" title="主页配置" name="homepage">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="主页类型">
                {{ homepage.type === 'dashboard' ? '仪表盘' : homepage.type === 'list' ? '列表' : '自定义' }}
              </el-descriptions-item>
              <el-descriptions-item label="主页标题">{{ homepage.title }}</el-descriptions-item>
              <el-descriptions-item label="组件数量" :span="2">
                {{ homepage.widgets?.length || 0 }} 个
              </el-descriptions-item>
            </el-descriptions>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 确认提示 -->
      <el-alert
        title="确认创建"
        :description="confirmDescription"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="$emit('prev')">上一步</el-button>
        <el-button type="primary" size="large" @click="$emit('create')" :loading="creating">
          <el-icon><Check /></el-icon>
          {{ creating ? '创建中...' : '确认创建应用' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Check } from '@element-plus/icons-vue'

const props = defineProps<{
  design: any
  templates: any[]
  menus: any[]
  homepage: any
  appInfo: any
  creating: boolean
  skipWorkflow?: boolean
  skipAgent?: boolean
  skipDashboard?: boolean
}>()

const emit = defineEmits(['update:appInfo', 'prev', 'create'])

const localAppInfo = computed({
  get: () => props.appInfo,
  set: (val) => emit('update:appInfo', val)
})

const successTemplates = computed(() => 
  props.templates.filter(t => t._status === 'success')
)

const hasSkipOptions = computed(() =>
  props.skipWorkflow || props.skipAgent || props.skipDashboard
)

const confirmDescription = computed(() => {
  const parts = ['点击创建按钮后，系统将创建应用、发布所有表单、配置菜单']
  if (!props.skipDashboard) {
    parts.push('和主页')
  }
  parts.push('。创建完成后即可使用应用。')
  return parts.join('')
})

const activeCollapse = ref(['templates', 'menus'])
</script>

<style scoped lang="scss">
.step6-final-confirm {
  max-width: 1000px;
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

.section {
  margin-bottom: 30px;

  h3 {
    margin: 0 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--el-border-color-light);
    color: var(--el-text-color-primary);
    font-size: 16px;
  }
}

.skip-summary {
  margin-bottom: 20px;

  .skip-items {
    display: flex;
    gap: 16px;
    margin-top: 4px;
    font-size: 13px;
  }
}

.preview-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);

  .el-button--large {
    min-width: 200px;
  }
}
</style>
