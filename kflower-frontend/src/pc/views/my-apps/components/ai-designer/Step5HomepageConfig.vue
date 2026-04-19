<template>
  <div class="step5-homepage-config">
    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span>🏠 配置应用主页</span>
          <el-radio-group v-model="localHomepage.type" size="small">
            <el-radio-button label="dashboard">仪表盘</el-radio-button>
            <el-radio-button label="list">列表</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 主页基本信息 -->
      <div class="homepage-info">
        <el-form :model="localHomepage" label-width="100px">
          <el-form-item label="主页标题">
            <el-input v-model="localHomepage.title" placeholder="如：工作台、概览" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="localHomepage.description" type="textarea" :rows="2" placeholder="主页描述" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 仪表盘类型 -->
      <div v-if="localHomepage.type === 'dashboard'" class="dashboard-config">
        <div class="section-header">
          <h4>组件配置</h4>
          <el-button size="small" @click="addWidget">
            <el-icon><Plus /></el-icon> 添加组件
          </el-button>
        </div>

        <div class="widgets-grid">
          <el-card 
            v-for="(widget, idx) in localHomepage.widgets" 
            :key="String(widget.id || idx)"
            class="widget-card"
            shadow="hover"
          >
            <template #header>
              <div class="widget-header">
                <span>{{ widget.title || '未命名组件' }}</span>
                <el-button type="danger" size="small" text @click="removeWidget(idx as number)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>

            <el-form :model="widget" label-width="80px" size="small">
              <el-form-item label="组件标题">
                <el-input v-model="widget.title" />
              </el-form-item>
              <el-form-item label="组件类型">
                <el-select v-model="widget.type" style="width: 100%">
                  <el-option label="统计卡片" value="stat" />
                  <el-option label="数据列表" value="list" />
                  <el-option label="图表" value="chart" />
                  <el-option label="快捷入口" value="quick" />
                </el-select>
              </el-form-item>
              <el-form-item label="数据源">
                <el-select v-model="widget.template_id" style="width: 100%" clearable>
                  <el-option 
                    v-for="tpl in availableTemplates" 
                    :key="tpl._id" 
                    :label="tpl.name" 
                    :value="tpl._id"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="尺寸">
                <div class="size-inputs">
                  <el-input-number v-model="widget.w" :min="4" :max="24" :step="4" size="small" />
                  <span>x</span>
                  <el-input-number v-model="widget.h" :min="2" :max="12" size="small" />
                </div>
              </el-form-item>
            </el-form>
          </el-card>
        </div>

        <!-- 预览 -->
        <div class="preview-section">
          <h4>布局预览</h4>
          <div class="preview-grid">
            <div 
              v-for="(widget, idx) in localHomepage.widgets" 
              :key="idx"
              class="preview-item"
              :style="{ 
                gridColumn: `span ${widget.w || 8}`,
                gridRow: `span ${widget.h || 4}`
              }"
            >
              <div class="preview-card">
                <span>{{ widget.title }}</span>
                <el-tag size="small">{{ widget.type }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 列表类型 -->
      <div v-else-if="localHomepage.type === 'list'" class="list-config">
        <el-form :model="localHomepage.listConfig" label-width="100px">
          <el-form-item label="默认列表">
            <el-select v-model="localHomepage.defaultTemplateId" style="width: 100%">
              <el-option 
                v-for="tpl in availableTemplates" 
                :key="tpl._id" 
                :label="tpl.name" 
                :value="tpl._id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="显示字段">
            <el-select 
              v-model="localHomepage.displayFields" 
              multiple 
              style="width: 100%"
              placeholder="选择要显示的字段"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 自定义类型 -->
      <div v-else class="custom-config">
        <el-alert 
          title="自定义主页" 
          description="将在后续版本中支持自定义HTML和组件编排"
          type="info"
          show-icon
        />
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button @click="$emit('prev')">上一步</el-button>
        <el-button type="primary" @click="$emit('next')">
          下一步：确认创建 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Delete, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  design: any
  templates: any[]
  homepage: any
}>()

const emit = defineEmits(['update:homepage', 'prev', 'next'])

const localHomepage = computed({
  get: () => props.homepage,
  set: (val) => emit('update:homepage', val)
})

const availableTemplates = computed(() => 
  props.templates.filter(t => t._status === 'success' && t._id)
)

function addWidget() {
  if (!localHomepage.value.widgets) {
    localHomepage.value.widgets = []
  }
  
  const idx = localHomepage.value.widgets.length
  localHomepage.value.widgets.push({
    id: `widget_${Date.now()}`,
    type: 'stat',
    title: `组件${idx + 1}`,
    template_id: availableTemplates.value[0]?._id || null,
    x: (idx % 3) * 8,
    y: Math.floor(idx / 3) * 4,
    w: 8,
    h: 4
  })
}

function removeWidget(idx: number) {
  if (!localHomepage.value.widgets) return
  localHomepage.value.widgets.splice(idx, 1)
}
</script>

<style scoped lang="scss">
.step5-homepage-config {
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

.homepage-info {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h4 {
    margin: 0;
  }
}

.widgets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 30px;
}

.widget-card {
  :deep(.el-card__header) {
    padding: 12px 16px;
  }
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
}

.size-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);

  h4 {
    margin: 0 0 16px;
  }
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
  gap: 8px;
  min-height: 200px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.preview-item {
  min-height: 80px;
}

.preview-card {
  height: 100%;
  padding: 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;

  span {
    font-size: 14px;
    font-weight: 500;
  }
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color-light);
}
</style>
