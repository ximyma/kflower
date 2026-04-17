<template>
  <div class="app-home">
    <!-- 欢迎卡片 -->
    <div class="welcome-card">
      <h2>你好，{{ userStore.userInfo?.full_name || '用户' }}</h2>
      <p>今天有什么可以帮您的？</p>
    </div>
    
    <!-- 快捷操作 -->
    <div class="quick-actions">
      <div
        v-for="action in quickActions"
        :key="action.title"
        class="action-item"
        @click="handleAction(action)"
      >
        <div class="action-icon" :style="{ background: action.color }">
          <el-icon :size="24"><component :is="action.icon" /></el-icon>
        </div>
        <span>{{ action.title }}</span>
      </div>
    </div>
    
    <!-- 待办事项 -->
    <el-card class="todo-card">
      <template #header>
        <span>📋 待办事项</span>
        <el-badge :value="todos.length" type="primary" />
      </template>
      
      <div v-if="todos.length === 0" class="empty-state">
        <el-icon :size="48" color="#c0c4cc"><SuccessFilled /></el-icon>
        <p>暂无待办事项</p>
      </div>
      
      <el-timeline v-else>
        <el-timeline-item
          v-for="todo in todos"
          :key="todo.id"
          :timestamp="todo.time"
          :type="todo.type"
        >
          {{ todo.title }}
        </el-timeline-item>
      </el-timeline>
    </el-card>
    
    <!-- AI助手入口 -->
    <el-card class="ai-card" @click="aiStore.toggleChat">
      <div class="ai-content">
        <div class="ai-icon">
          <el-icon :size="32"><MagicStick /></el-icon>
        </div>
        <div class="ai-info">
          <h3>AI 智能助手</h3>
          <p>随时为您服务</p>
        </div>
        <el-icon :size="24" color="#c0c4cc"><ArrowRight /></el-icon>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  Document, Connection, DataAnalysis, Files,
  SuccessFilled, MagicStick, ArrowRight 
} from '@element-plus/icons-vue'
import { useUserStore } from '../../common/store/user'
import { useAIStore } from '../../common/store/ai'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const aiStore = useAIStore()

const quickActions = [
  { title: '模板设计', icon: 'Document', color: '#409EFF' },
  { title: '流程审批', icon: 'Connection', color: '#67C23A' },
  { title: '数据分析', icon: 'DataAnalysis', color: '#E6A23C' },
  { title: '知识库', icon: 'Files', color: '#F56C6C' }
]

const todos = ref([
  { id: 1, time: '今天', title: '审批采购申请 #1001', type: 'warning' },
  { id: 2, time: '今天', title: '更新客户信息', type: 'primary' }
])

function handleAction(action: any) {
  aiStore.setAIType('general')
  aiStore.showChat = true
  aiStore.sendMessage(`帮我${action.title}`)
}
</script>

<style scoped>
.app-home {
  padding-bottom: 20px;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.welcome-card h2 {
  margin-bottom: 4px;
}

.welcome-card p {
  opacity: 0.9;
  font-size: 13px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: white;
  border-radius: 12px;
  cursor: pointer;
}

.action-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.action-item span {
  font-size: 12px;
  color: #606266;
}

.todo-card {
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #c0c4cc;
}

.empty-state p {
  margin-top: 8px;
}

.ai-card {
  cursor: pointer;
}

.ai-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-info {
  flex: 1;
}

.ai-info h3 {
  margin-bottom: 4px;
}

.ai-info p {
  color: #909399;
  font-size: 12px;
}
</style>
