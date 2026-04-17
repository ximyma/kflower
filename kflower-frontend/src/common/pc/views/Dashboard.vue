<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1>欢迎使用 Kflower 企业智能管理平台</h1>
      </el-col>
    </el-row>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>模板设计</span>
              <el-icon class="icon"><document /></el-icon>
            </div>
          </template>
          <p>AI智能生成业务模板，快速构建企业应�?/p>
          <el-button type="primary" @click="$router.push('/templates')">进入</el-button>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>流程审批</span>
              <el-icon class="icon"><data-analysis /></el-icon>
            </div>
          </template>
          <p>可视化流程编排，智能审批助手</p>
          <el-button type="success" @click="$router.push('/workflows')">进入</el-button>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>决策分析</span>
              <el-icon class="icon"><pie-chart /></el-icon>
            </div>
          </template>
          <p>AI驱动的数据分析与智能预测</p>
          <el-button type="warning" @click="$router.push('/analytics')">进入</el-button>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>知识�?/span>
              <el-icon class="icon"><collection /></el-icon>
            </div>
          </template>
          <p>企业知识沉淀，智能检索问�?/p>
          <el-button type="info" @click="$router.push('/knowledge')">进入</el-button>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI 助手</span>
            </div>
          </template>
          <p>有问题？试试�?AI 助手</p>
          <el-button type="primary" @click="aiStore.toggleChat()">打开 AI 对话</el-button>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <el-space wrap>
            <el-button>新建模板</el-button>
            <el-button>创建流程</el-button>
            <el-button>上传文档</el-button>
          </el-space>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { useAIStore } from '../../store/ai'
const aiStore = useAIStore()
</script>

<style scoped>
.dashboard {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.icon {
  font-size: 24px;
}
</style>
