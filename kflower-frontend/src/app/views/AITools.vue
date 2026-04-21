<template>
  <div class="app-ai-tools">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>AI工具集</h2>
    </div>
    
    <!-- 工具分类 -->
    <div class="tool-category" v-for="category in toolCategories" :key="category.name">
      <div class="category-title">{{ category.name }}</div>
      <div class="tool-grid">
        <div
          v-for="tool in category.tools"
          :key="tool.key"
          class="tool-item"
          @click="openTool(tool)"
        >
          <div class="tool-icon" :style="{ background: tool.color }">
            <el-icon :size="24"><component :is="tool.icon" /></el-icon>
          </div>
          <span class="tool-name">{{ tool.name }}</span>
        </div>
      </div>
    </div>
    
    <!-- 工具使用对话框 -->
    <el-dialog v-model="showToolDialog" :title="currentTool?.name" width="95%" :close-on-click-modal="true">
      <div class="tool-content" v-if="currentTool">
        <p class="tool-desc">{{ currentTool.description }}</p>
        
        <!-- 文本处理工具 -->
        <template v-if="currentTool.key === 'text_summary' || currentTool.key === 'text_keywords' || currentTool.key === 'text_parse'">
          <el-input
            v-model="toolInput"
            type="textarea"
            :rows="6"
            placeholder="请输入要处理的文本..."
          />
          <el-button type="primary" class="tool-btn" @click="processText" :loading="processing">
            开始处理
          </el-button>
        </template>
        
        <!-- OCR工具 -->
        <template v-else-if="currentTool.key === 'ocr_text' || currentTool.key === 'ocr_table'">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            drag
          >
            <el-icon :size="40" color="#c0c4cc"><Upload /></el-icon>
            <div>点击或拖拽上传图片</div>
          </el-upload>
          <el-button type="primary" class="tool-btn" @click="processImage" :loading="processing" :disabled="!selectedFile">
            开始识别
          </el-button>
        </template>
        
        <!-- 结果展示 -->
        <div v-if="toolResult" class="tool-result">
          <div class="result-header">
            <span>处理结果</span>
            <el-button size="small" text @click="copyResult">复制</el-button>
          </div>
          <el-input
            v-model="toolResult"
            type="textarea"
            :rows="8"
            readonly
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  Document, Files, Picture, DataLine, Edit,
  Upload, CopyDocument, Delete, DocumentChecked
} from '@element-plus/icons-vue'
import { localAIAPI } from '../../common/api'
import { ElMessage } from 'element-plus'

const showToolDialog = ref(false)
const currentTool = ref<any>(null)
const toolInput = ref('')
const toolResult = ref('')
const processing = ref(false)
const selectedFile = ref<File | null>(null)

const toolCategories = [
  {
    name: '文本处理',
    tools: [
      { key: 'text_summary', name: '文本摘要', icon: 'Document', color: '#409EFF', description: '将长文本压缩为简洁摘要，提取关键信息' },
      { key: 'text_keywords', name: '关键词提取', icon: 'Tickets', color: '#67C23A', description: '从文本中提取最重要的关键词' },
      { key: 'text_parse', name: '文本解析', icon: 'Edit', color: '#E6A23C', description: '结构化解析文本内容' }
    ]
  },
  {
    name: 'OCR识别',
    tools: [
      { key: 'ocr_text', name: '文字识别', icon: 'Picture', color: '#F56C6C', description: '从图片中识别提取文字' },
      { key: 'ocr_table', name: '表格识别', icon: 'DataLine', color: '#909399', description: '识别图片中的表格结构' }
    ]
  },
  {
    name: '文档处理',
    tools: [
      { key: 'doc_convert', name: '文档转换', icon: 'Files', color: '#19D9FF', description: '支持多种文档格式转换' },
      { key: 'doc_extract', name: '内容提取', icon: 'DocumentChecked', color: '#7C3AED', description: '从文档中提取关键内容' }
    ]
  }
]

function openTool(tool: any) {
  currentTool.value = tool
  toolInput.value = ''
  toolResult.value = ''
  selectedFile.value = null
  showToolDialog.value = true
}

async function processText() {
  if (!toolInput.value.trim()) {
    ElMessage.warning('请输入要处理的文本')
    return
  }
  
  processing.value = true
  try {
    let res: any
    switch (currentTool.value.key) {
      case 'text_summary':
        res = await localAIAPI.textSummary(toolInput.value)
        toolResult.value = res.summary || res.result || JSON.stringify(res)
        break
      case 'text_keywords':
        res = await localAIAPI.textKeywords(toolInput.value)
        toolResult.value = res.keywords?.join(', ') || JSON.stringify(res)
        break
      case 'text_parse':
        res = await localAIAPI.textParse(toolInput.value)
        toolResult.value = typeof res === 'string' ? res : JSON.stringify(res, null, 2)
        break
    }
    ElMessage.success('处理完成')
  } catch (error) {
    ElMessage.error('处理失败，请稍后重试')
    console.error(error)
  } finally {
    processing.value = false
  }
}

function handleFileChange(file: any) {
  selectedFile.value = file.raw
}

async function processImage() {
  if (!selectedFile.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  
  processing.value = true
  try {
    let res: any
    if (currentTool.value.key === 'ocr_text') {
      res = await localAIAPI.ocrText(selectedFile.value)
    } else {
      res = await localAIAPI.ocrTable(selectedFile.value)
    }
    toolResult.value = res.text || res.result || JSON.stringify(res)
    ElMessage.success('识别完成')
  } catch (error) {
    ElMessage.error('识别失败，请稍后重试')
    console.error(error)
  } finally {
    processing.value = false
  }
}

function copyResult() {
  if (toolResult.value) {
    navigator.clipboard.writeText(toolResult.value)
    ElMessage.success('已复制到剪贴板')
  }
}
</script>

<style scoped>
.app-ai-tools {
  padding-bottom: 20px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  font-size: 18px;
  color: #303133;
  margin: 0;
}

.tool-category {
  margin-bottom: 20px;
}

.category-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 4px;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.tool-item {
  background: white;
  border-radius: 12px;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.tool-item:active {
  transform: scale(0.95);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tool-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.tool-name {
  font-size: 12px;
  color: #303133;
  text-align: center;
}

.tool-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.tool-desc {
  color: #909399;
  font-size: 13px;
  margin: 0;
}

.tool-btn {
  width: 100%;
}

.tool-result {
  margin-top: 8px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}
</style>
