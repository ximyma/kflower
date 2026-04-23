<template>
  <div class="migration-page">
    <el-page-header title="数据迁移" content="支持 SQLite、MySQL、PostgreSQL 数据库互迁" />
    
    <el-row :gutter="20" class="migration-content">
      <!-- 源数据库配置 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Download /></el-icon>
              <span>源数据库</span>
              <el-tag v-if="sourceConnected" type="success">已连接</el-tag>
            </div>
          </template>
          
          <el-form :model="sourceConfig" label-width="100px">
            <el-form-item label="数据库类型">
              <el-select v-model="sourceConfig.db_type" placeholder="选择数据库类型">
                <el-option label="SQLite" value="sqlite" />
                <el-option label="MySQL" value="mysql" />
                <el-option label="PostgreSQL" value="postgresql" />
              </el-select>
            </el-form-item>
            
            <template v-if="sourceConfig.db_type === 'sqlite'">
              <el-form-item label="数据库文件">
                <el-input v-model="sourceConfig.database" placeholder="如: D:/data/source.db" />
              </el-form-item>
            </template>
            
            <template v-else>
              <el-form-item label="主机地址">
                <el-input v-model="sourceConfig.host" placeholder="localhost" />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number v-model="sourceConfig.port" :min="1" :max="65535" />
              </el-form-item>
              <el-form-item label="数据库名">
                <el-input v-model="sourceConfig.database" />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="sourceConfig.username" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="sourceConfig.password" type="password" />
              </el-form-item>
            </template>
            
            <el-form-item>
              <el-button type="primary" @click="testSourceConnection" :loading="testingSource">
                测试连接
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <!-- 目标数据库配置 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><Upload /></el-icon>
              <span>目标数据库</span>
              <el-tag v-if="targetConnected" type="success">已连接</el-tag>
            </div>
          </template>
          
          <el-form :model="targetConfig" label-width="100px">
            <el-form-item label="数据库类型">
              <el-select v-model="targetConfig.db_type" placeholder="选择数据库类型">
                <el-option label="SQLite" value="sqlite" />
                <el-option label="MySQL" value="mysql" />
                <el-option label="PostgreSQL" value="postgresql" />
              </el-select>
            </el-form-item>
            
            <template v-if="targetConfig.db_type === 'sqlite'">
              <el-form-item label="数据库文件">
                <el-input v-model="targetConfig.database" placeholder="如: D:/data/target.db" />
              </el-form-item>
            </template>
            
            <template v-else>
              <el-form-item label="主机地址">
                <el-input v-model="targetConfig.host" placeholder="localhost" />
              </el-form-item>
              <el-form-item label="端口">
                <el-input-number v-model="targetConfig.port" :min="1" :max="65535" />
              </el-form-item>
              <el-form-item label="数据库名">
                <el-input v-model="targetConfig.database" />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input v-model="targetConfig.username" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="targetConfig.password" type="password" />
              </el-form-item>
            </template>
            
            <el-form-item>
              <el-button type="primary" @click="testTargetConnection" :loading="testingTarget">
                测试连接
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 表选择 -->
    <el-card v-if="sourceTables.length > 0" class="table-selection">
      <template #header>
        <div class="card-header">
          <span>选择要迁移的表</span>
          <el-button type="primary" link @click="selectAllTables">
            {{ allSelected ? '取消全选' : '全选' }}
          </el-button>
        </div>
      </template>
      
      <el-checkbox-group v-model="selectedTables">
        <el-checkbox 
          v-for="table in sourceTables" 
          :key="table" 
          :label="table"
          border
        >
          {{ table }}
        </el-checkbox>
      </el-checkbox-group>
    </el-card>
    
    <!-- 迁移选项 -->
    <el-card class="migration-options">
      <template #header>
        <span>迁移选项</span>
      </template>
      
      <el-form :inline="true">
        <el-form-item label="每批处理">
          <el-input-number v-model="batchSize" :min="100" :max="10000" :step="100" />
          <span class="unit">条</span>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="skipExisting">跳过已存在的表</el-checkbox>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 执行按钮 -->
    <div class="action-buttons">
      <el-button 
        type="primary" 
        size="large" 
        @click="startMigration"
        :loading="migrating"
        :disabled="selectedTables.length === 0"
      >
        <el-icon><Switch /></el-icon>
        开始迁移
      </el-button>
      
      <el-button size="large" @click="generateScript">
        <el-icon><Document /></el-icon>
        生成脚本
      </el-button>
    </div>
    
    <!-- 进度显示 -->
    <el-card v-if="migrationStatus" class="migration-progress">
      <template #header>
        <span>迁移进度</span>
      </template>
      
      <el-progress 
        :percentage="progressPercent" 
        :status="progressStatus"
        :stroke-width="20"
      />
      <p class="progress-message">{{ progressMessage }}</p>
      
      <div v-if="migrationResults" class="migration-results">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="开始时间">{{ migrationResults.start_time }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ migrationResults.end_time }}</el-descriptions-item>
          <el-descriptions-item label="总迁移行数">{{ migrationResults.total_rows }}</el-descriptions-item>
          <el-descriptions-item label="错误数">{{ migrationResults.errors?.length || 0 }}</el-descriptions-item>
        </el-descriptions>
        
        <div v-if="migrationResults.errors?.length > 0" class="error-list">
          <h4>错误信息</h4>
          <el-alert 
            v-for="(error, idx) in migrationResults.errors" 
            :key="idx"
            :title="error"
            type="error"
            :closable="false"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Upload, Switch, Document } from '@element-plus/icons-vue'
import { testConnection, executeMigration, generateScript } from '../../common/api/migration'

interface DBConfig {
  db_type: string
  host?: string
  port?: number
  database: string
  username?: string
  password?: string
}

const sourceConfig = ref<DBConfig>({
  db_type: 'sqlite',
  database: 'D:/kflower/kflower-data/kflower.db'
})

const targetConfig = ref<DBConfig>({
  db_type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: 'kflower_prod'
})

const sourceConnected = ref(false)
const targetConnected = ref(false)
const testingSource = ref(false)
const testingTarget = ref(false)
const sourceTables = ref<string[]>([])
const selectedTables = ref<string[]>([])
const batchSize = ref(1000)
const skipExisting = ref(false)
const migrating = ref(false)
const migrationStatus = ref(false)
const progressPercent = ref(0)
const progressMessage = ref('')
const progressStatus = ref('')
const migrationResults = ref<any>(null)

const allSelected = computed(() => {
  return selectedTables.value.length === sourceTables.value.length && sourceTables.value.length > 0
})

const testSourceConnection = async () => {
  testingSource.value = true
  try {
    const res = await testConnection(sourceConfig.value)
    sourceTables.value = res.tables
    sourceConnected.value = true
    ElMessage.success(`连接成功，发现 ${res.tables.length} 个表`)
  } catch (error: any) {
    ElMessage.error(error.message || '连接失败')
    sourceConnected.value = false
  } finally {
    testingSource.value = false
  }
}

const testTargetConnection = async () => {
  testingTarget.value = true
  try {
    await testConnection(targetConfig.value)
    targetConnected.value = true
    ElMessage.success('目标数据库连接成功')
  } catch (error: any) {
    ElMessage.error(error.message || '连接失败')
    targetConnected.value = false
  } finally {
    testingTarget.value = false
  }
}

const selectAllTables = () => {
  if (allSelected.value) {
    selectedTables.value = []
  } else {
    selectedTables.value = [...sourceTables.value]
  }
}

const startMigration = async () => {
  if (selectedTables.value.length === 0) {
    ElMessage.warning('请选择要迁移的表')
    return
  }
  
  migrating.value = true
  migrationStatus.value = true
  progressPercent.value = 0
  progressMessage.value = '准备迁移...'
  progressStatus.value = ''
  migrationResults.value = null
  
  try {
    const res = await executeMigration({
      source: sourceConfig.value,
      target: targetConfig.value,
      tables: selectedTables.value,
      batch_size: batchSize.value,
      skip_existing: skipExisting.value
    })
    
    migrationResults.value = res.results
    progressPercent.value = 100
    progressStatus.value = 'success'
    progressMessage.value = `迁移完成！共迁移 ${res.results.total_rows} 行数据`
    ElMessage.success('数据迁移完成')
  } catch (error: any) {
    progressStatus.value = 'exception'
    progressMessage.value = '迁移失败: ' + (error.message || '未知错误')
    ElMessage.error(error.message || '迁移失败')
  } finally {
    migrating.value = false
  }
}

const generateMigrationScript = async () => {
  try {
    const res = await generateScript({
      source: sourceConfig.value,
      target: targetConfig.value,
      tables: selectedTables.value,
      batch_size: batchSize.value,
      skip_existing: skipExisting.value
    })
    
    // 下载脚本
    const blob = new Blob([res.script], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `migration_${Date.now()}.py`
    link.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('脚本已生成')
  } catch (error: any) {
    ElMessage.error(error.message || '生成失败')
  }
}
</script>

<style scoped lang="scss">
.migration-page {
  padding: 20px;
}

.migration-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-selection {
  margin-top: 20px;
  
  .el-checkbox {
    margin: 8px;
  }
}

.migration-options {
  margin-top: 20px;
  
  .unit {
    margin-left: 8px;
    color: var(--el-text-color-secondary);
  }
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.migration-progress {
  margin-top: 20px;
  
  .progress-message {
    margin-top: 16px;
    text-align: center;
    color: var(--el-text-color-regular);
  }
}

.migration-results {
  margin-top: 20px;
}

.error-list {
  margin-top: 16px;
  
  h4 {
    margin-bottom: 12px;
  }
  
  .el-alert {
    margin-bottom: 8px;
  }
}
</style>
