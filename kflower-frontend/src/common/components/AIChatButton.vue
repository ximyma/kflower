<script setup lang="ts">
/**
 * AI对话悬浮按钮组件
 */
import { useAIStore } from '../store/ai'
import AIChatDialog from './AIChatDialog.vue'

const aiStore = useAIStore()

// 关闭对话框（直接设置为 false，而不是切换）
function closeChat() {
  aiStore.showChat = false
}
</script>

<template>
  <div class="ai-chat-wrapper">
    <!-- AI对话框 -->
    <AIChatDialog 
      v-if="aiStore.showChat"
      @close="closeChat"
    />
    
    <!-- 悬浮按钮 -->
    <div 
      class="ai-float-btn"
      @click="aiStore.toggleChat"
      v-if="!aiStore.showChat"
    >
      <el-icon :size="28"><MagicStick /></el-icon>
      <span class="ai-label">AI助手</span>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-wrapper {
  position: fixed;
  bottom: 100px;
  right: 30px;
  z-index: 9999;
}

.ai-float-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: white;
}

.ai-float-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.ai-label {
  font-size: 10px;
  margin-top: 2px;
}
</style>
