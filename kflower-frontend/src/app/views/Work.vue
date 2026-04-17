<template>
  <div class="app-work">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="我发起的" name="my">
        <el-card
          v-for="item in myItems"
          :key="item.id"
          class="work-item"
          @click="handleClick(item)"
        >
          <div class="work-content">
            <div class="work-info">
              <h4>{{ item.title }}</h4>
              <p>{{ item.workflow }} · {{ item.time }}</p>
            </div>
            <el-tag :type="getStatusType(item.status)" size="small">
              {{ item.status }}
            </el-tag>
          </div>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="待我审批" name="pending">
        <el-card
          v-for="item in pendingItems"
          :key="item.id"
          class="work-item pending"
          @click="handleClick(item)"
        >
          <div class="work-content">
            <div class="work-info">
              <h4>{{ item.title }}</h4>
              <p>{{ item.applicant }} · {{ item.time }}</p>
            </div>
            <div class="work-actions">
              <el-button type="success" size="small" circle>
                <el-icon><Check /></el-icon>
              </el-button>
              <el-button type="danger" size="small" circle>
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Check, Close } from '@element-plus/icons-vue'

const activeTab = ref('my')

const myItems = ref([
  { id: 1, title: '采购申请 #1001', workflow: '采购审批', status: '审批中', time: '10:00' },
  { id: 2, title: '请假申请', workflow: '请假审批', status: '已通过', time: '昨天' }
])

const pendingItems = ref([
  { id: 1, title: '采购申请 #1002', applicant: '张三', time: '09:00' },
  { id: 2, title: '费用报销 #500', applicant: '李四', time: '08:30' }
])

function getStatusType(status: string) {
  const types: Record<string, string> = {
    '审批中': 'warning',
    '已通过': 'success',
    '已拒绝': 'danger'
  }
  return types[status] || 'info'
}

function handleClick(item: any) {
  console.log('点击了:', item)
}
</script>

<style scoped>
.app-work {
  padding-bottom: 20px;
}

.work-item {
  margin-bottom: 12px;
}

.work-item.pending {
  border-left: 3px solid #67C23A;
}

.work-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.work-info h4 {
  margin-bottom: 4px;
}

.work-info p {
  color: #909399;
  font-size: 12px;
}

.work-actions {
  display: flex;
  gap: 8px;
}
</style>
