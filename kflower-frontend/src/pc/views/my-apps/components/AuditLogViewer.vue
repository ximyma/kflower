<template>
  <div class="audit-log-viewer">
    <div class="toolbar">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="资源类型">
          <el-select v-model="searchForm.resource_type" clearable placeholder="全部" style="width: 150px">
            <el-option label="模板数据" value="template_data" />
            <el-option label="应用" value="application" />
            <el-option label="插件" value="plugin" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">查询</el-button>
          <el-button @click="exportLogs">导出</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table :data="logs" v-loading="loading" border stripe>
      <el-table-column prop="created_at" label="时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="user_name" label="操作用户" width="120" />
      <el-table-column prop="action" label="操作" width="100">
        <template #default="{ row }">
          <el-tag :type="getActionType(row.action)">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resource_type" label="资源类型" width="120" />
      <el-table-column prop="resource_id" label="资源ID" width="100" />
      <el-table-column prop="detail" label="详情" min-width="200">
        <template #default="{ row }">
          {{ row.detail || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP地址" width="130" />
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadLogs"
        @current-change="loadLogs"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { appAPI } from '@/common/api/myApps'

const loading = ref(false)
const logs = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const dateRange = ref<[string, string] | null>(null)

const searchForm = reactive({
  resource_type: ''
})

function formatTime(time: string) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function getActionType(action: string) {
  const types: Record<string, string> = {
    create: 'success',
    update: 'warning',
    delete: 'danger',
    login: 'info',
  }
  return types[action] || ''
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (searchForm.resource_type) {
      params.resource_type = searchForm.resource_type
    }
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res: any = await appAPI.getAuditLogs(params)
    const data = res.data || res
    logs.value = data.logs || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

async function exportLogs() {
  try {
    const params: any = {}
    if (searchForm.resource_type) {
      params.resource_type = searchForm.resource_type
    }
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    ElMessage.info('正在导出，请稍候...')
    await appAPI.exportAuditLogs(params)
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.audit-log-viewer {
  padding: 16px;
}
.toolbar {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
