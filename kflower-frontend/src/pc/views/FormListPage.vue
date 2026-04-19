<template>
  <div class="form-list-page">
    <div class="page-header">
      <h2>{{ templateData?.name || '数据列表' }}</h2>
      <el-button type="primary" @click="createNew">
        <el-icon><Plus /></el-icon> 新增
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索..."
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table :data="tableData" border stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column
          v-for="field in displayFields"
          :key="field.name"
          :prop="field.name"
          :label="field.label"
        />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewRow(row)">查看</el-button>
            <el-button size="small" type="primary" @click="editRow(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteRow(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { templateAPI } from '@/common/api/index'

const route = useRoute()
const router = useRouter()

const appId = ref(Number(route.params.appId))
const templateId = ref(Number(route.params.templateId))

const templateData = ref<any>(null)
const tableData = ref<any[]>([])
const displayFields = ref<any[]>([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 加载模板数据
async function loadTemplate() {
  try {
    const res: any = await templateAPI.get(templateId.value)
    templateData.value = res
    
    // 提取字段（从 modules 中）
    const modules = res.modules || []
    displayFields.value = []
    for (const mod of modules) {
      if (mod.fields) {
        displayFields.value.push(...mod.fields.map((f: any) => ({
          name: f.name,
          label: f.label,
          type: f.type
        })))
      }
    }
  } catch (e: any) {
    ElMessage.error('加载模板失败：' + (e.message || ''))
  }
}

// 加载数据
async function loadData() {
  try {
    const res: any = await templateAPI.getData(templateId.value, {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchKeyword.value
    })
    tableData.value = res.items || res
    total.value = res.total || tableData.value.length
  } catch (e: any) {
    ElMessage.error('加载数据失败：' + (e.message || ''))
  }
}

// 监听路由变化，重新加载数据
watch(() => route.params.templateId, (newId) => {
  if (newId) {
    templateId.value = Number(newId)
    loadTemplate()
    loadData()
  }
})

// 搜索
function handleSearch() {
  currentPage.value = 1
  loadData()
}

// 新增
function createNew() {
  router.push(`/app/${appId}/form/${templateId}/edit`)
}

// 查看
function viewRow(row: any) {
  router.push(`/app/${appId}/form/${templateId}/edit/${row.id}`)
}

// 编辑
function editRow(row: any) {
  router.push(`/app/${appId}/form/${templateId}/edit/${row.id}`)
}

// 删除
async function deleteRow(row: any) {
  try {
    await ElMessageBox.confirm('确定删除这条数据吗？', '确认删除', {
      type: 'warning'
    })
    await templateAPI.deleteData(templateId, row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败：' + (e.message || ''))
    }
  }
}

onMounted(() => {
  loadTemplate()
  loadData()
})
</script>

<style scoped lang="scss">
.form-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.search-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
