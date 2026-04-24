<template>
  <div class="knowledge-search">
    <!-- 搜索输入 -->
    <el-row :gutter="12" align="middle">
      <el-col :span="18">
        <el-input
          v-model="searchQuery"
          placeholder="输入关键词搜索应用知识库..."
          :prefix-icon="Search"
          clearable
          @keyup.enter="doSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="doSearch" :loading="searching">搜索</el-button>
          </template>
        </el-input>
      </el-col>
      <el-col :span="6">
        <el-select v-model="topK" placeholder="结果数" size="default" style="width:100%">
          <el-option :value="3" label="3条" />
          <el-option :value="5" label="5条" />
          <el-option :value="10" label="10条" />
          <el-option :value="20" label="20条" />
        </el-select>
      </el-col>
    </el-row>

    <!-- 搜索结果 -->
    <div v-if="results.length > 0" class="search-results">
      <div class="results-header">
        <span style="color:var(--el-text-color-secondary);font-size:13px">
          找到 {{ results.length }} 条相关结果
        </span>
      </div>

      <div
        v-for="(item, idx) in results"
        :key="idx"
        class="result-card"
      >
        <div class="result-header">
          <el-tag size="small" :type="getScoreType(item.score)">
            {{ (item.score * 100).toFixed(1) }}%
          </el-tag>
          <span v-if="item.metadata?.template_name" class="result-source">
            {{ item.metadata.template_name }}
          </span>
          <span v-if="item.metadata?.data_id" class="result-id">
            #{{ item.metadata.data_id }}
          </span>
        </div>
        <div class="result-text">{{ item.text }}</div>
        <div v-if="item.metadata?.indexed_at" class="result-meta">
          索引时间: {{ formatTime(item.metadata.indexed_at) }}
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-else-if="searched && !searching"
      description="未找到相关内容"
      :image-size="80"
    />

    <!-- 初始状态 -->
    <div v-else-if="!searched" class="search-hint">
      <el-icon :size="32" color="var(--el-text-color-placeholder)"><Search /></el-icon>
      <p style="color:var(--el-text-color-secondary);margin-top:12px">
        在应用绑定的知识库中进行语义搜索
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/common/api'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  appId: number
}>()

const searchQuery = ref('')
const topK = ref(5)
const searching = ref(false)
const searched = ref(false)
const results = ref<any[]>([])

const doSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  searching.value = true
  searched.value = true
  
  try {
    const res = await knowledgeAPI.searchApp(props.appId, searchQuery.value.trim(), topK.value)
    results.value = res.data?.results || []
  } catch (e: any) {
    console.error('知识搜索失败:', e)
    ElMessage.error('搜索失败: ' + (e.response?.data?.detail || e.message))
    results.value = []
  } finally {
    searching.value = false
  }
}

const getScoreType = (score: number) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.5) return 'warning'
  return 'info'
}

const formatTime = (iso: string) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN')
  } catch {
    return iso
  }
}
</script>

<style scoped>
.knowledge-search {
  padding: 12px 0;
}
.search-results {
  margin-top: 16px;
}
.results-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.result-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 10px;
  transition: border-color 0.2s;
}
.result-card:hover {
  border-color: var(--el-color-primary-light-3);
}
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.result-source {
  font-size: 13px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}
.result-id {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.result-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 120px;
  overflow: hidden;
  position: relative;
}
.result-text::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 30px;
  background: linear-gradient(transparent, var(--el-bg-color));
}
.result-meta {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.search-hint {
  text-align: center;
  padding: 40px 0;
}
</style>
