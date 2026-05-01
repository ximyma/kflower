<template>
  <div class="doc-converter-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>📄 文档转换工具</h2>
      <p class="subtitle">支持 doc/xls/ppt 等旧格式转换为 docx/xlsx/pptx/pdf，以及 Excel→JSON 数据提取</p>
    </div>

    <!-- 服务状态 -->
    <el-card class="status-card" style="margin-bottom:20px">
      <template #header>
        <div class="card-header">
          <span>🔧 服务状态</span>
          <el-button size="small" @click="loadStatus" :loading="loadingStatus">刷新</el-button>
        </div>
      </template>
      <div v-if="converterStatus" class="status-grid">
        <div class="status-item">
          <el-tag :type="converterStatus.libreoffice_available ? 'success' : 'warning'" size="large">
            <el-icon><component :is="converterStatus.libreoffice_available ? 'CircleCheck' : 'Warning'" /></el-icon>
            LibreOffice {{ converterStatus.libreoffice_available ? '已安装' : '未安装' }}
          </el-tag>
          <p v-if="converterStatus.libreoffice_path" class="status-path">{{ converterStatus.libreoffice_path }}</p>
          <p v-else class="status-hint">安装 LibreOffice 可支持全部格式转换</p>
        </div>
        <div class="status-item">
          <p class="dep-title">Python 依赖</p>
          <el-space wrap>
            <el-tag
              v-for="(ok, lib) in converterStatus.python_dependencies"
              :key="lib"
              :type="ok ? 'success' : 'info'"
              size="small"
            >{{ lib }}</el-tag>
          </el-space>
        </div>
        <div class="status-item">
          <el-tag :type="converterStatus.ready ? 'success' : 'danger'" size="large">
            {{ converterStatus.ready ? '✅ 服务就绪' : '❌ 服务不可用' }}
          </el-tag>
        </div>
      </div>
      <el-skeleton v-else :rows="2" animated />
    </el-card>

    <el-row :gutter="20">
      <!-- 左：单文件转换 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <span>🔄 格式转换</span>
          </template>

          <!-- 拖拽上传区 -->
          <el-upload
            ref="uploadRef"
            class="conv-uploader"
            drag
            :auto-upload="false"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
            :limit="1"
            :accept="acceptExts"
          >
            <el-icon :size="48" color="#c0c4cc"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或 <em>点击选择</em>
            </div>
            <template #tip>
              <div class="upload-tip">
                支持：{{ supportedInputList }}
              </div>
            </template>
          </el-upload>

          <!-- 目标格式 -->
          <div class="format-selector">
            <el-form :model="convForm" label-width="90px" style="margin-top:16px">
              <el-form-item label="目标格式">
                <el-radio-group v-model="convForm.targetFormat">
                  <el-radio-button v-for="fmt in availableTargets" :key="fmt" :label="fmt">
                    .{{ fmt }}
                  </el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="converting"
                  :disabled="!selectedFile || !convForm.targetFormat"
                  @click="doConvert"
                >
                  <el-icon><Download /></el-icon>
                  转换并下载
                </el-button>
                <el-button @click="resetConv">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 结果 -->
          <el-alert
            v-if="convResult"
            :title="convResult.message"
            :type="convResult.success ? 'success' : 'error'"
            show-icon
            :closable="false"
            style="margin-top:12px"
          />
        </el-card>
      </el-col>

      <!-- 右：Excel→JSON -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>📊 Excel → JSON 提取</span>
          </template>

          <el-upload
            ref="jsonUploadRef"
            class="json-uploader"
            drag
            :auto-upload="false"
            :on-change="onJsonFileChange"
            :on-remove="() => { jsonFile = null; jsonResult = null }"
            :limit="1"
            accept=".xlsx,.xls,.ods,.csv"
          >
            <el-icon :size="36" color="#c0c4cc"><Document /></el-icon>
            <div class="el-upload__text" style="font-size:13px">
              拖拽 Excel/CSV 文件，或 <em>点击选择</em>
            </div>
          </el-upload>

          <el-form :model="jsonForm" label-width="80px" style="margin-top:12px">
            <el-form-item label="表头行">
              <el-input-number v-model="jsonForm.headerRow" :min="0" :max="10" size="small" />
              <span style="font-size:12px;color: var(--el-text-color-secondary);margin-left:8px">（0=第1行为表头）</span>
            </el-form-item>
            <el-form-item label="最大行数">
              <el-input-number v-model="jsonForm.maxRows" :min="10" :max="10000" :step="100" size="small" />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="small"
                :loading="extracting"
                :disabled="!jsonFile"
                @click="doExtractJson"
              >提取 JSON</el-button>
              <el-button
                v-if="jsonResult?.success"
                size="small"
                @click="downloadJson"
              >下载 JSON</el-button>
            </el-form-item>
          </el-form>

          <!-- JSON 预览 -->
          <div v-if="jsonResult?.success" class="json-preview">
            <el-divider>预览（前5行，共 {{ jsonResult.row_count }} 行）</el-divider>
            <el-table
              :data="jsonResult.data?.slice(0, 5)"
              size="small"
              border
              style="width:100%;overflow-x:auto"
              :max-height="220"
            >
              <el-table-column
                v-for="col in jsonResult.columns?.slice(0, 6)"
                :key="col"
                :prop="col"
                :label="col"
                :min-width="80"
                show-overflow-tooltip
              />
            </el-table>
            <p v-if="(jsonResult.columns?.length || 0) > 6" class="hint-text">
              仅显示前6列，共 {{ jsonResult.columns?.length }} 列
            </p>
          </div>
          <el-alert
            v-else-if="jsonResult && !jsonResult.success"
            :title="jsonResult.error"
            type="error"
            show-icon
            :closable="false"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 批量转换 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span>📦 批量转换（最多20个文件）</span>
      </template>

      <el-upload
        ref="batchUploadRef"
        :auto-upload="false"
        :on-change="onBatchFileChange"
        :on-remove="onBatchFileRemove"
        multiple
        :limit="20"
        :accept="acceptExts"
      >
        <el-button type="default">
          <el-icon><Plus /></el-icon> 添加文件
        </el-button>
        <template #tip>
          <span style="font-size:12px;color:#909399">最多20个文件，转换完成后打包为 zip 下载</span>
        </template>
      </el-upload>

      <div v-if="batchFiles.length" style="margin-top:12px">
        <el-form :inline="true">
          <el-form-item label="目标格式">
            <el-select v-model="batchTargetFormat" style="width:100px">
              <el-option v-for="fmt in allTargetFormats" :key="fmt" :label="'.' + fmt" :value="fmt" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="batchConverting"
              @click="doBatchConvert"
            >
              批量转换并打包下载
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 格式支持说明 -->
    <el-card style="margin-top:20px">
      <template #header><span>📋 支持的转换格式</span></template>
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="Word">
          doc → docx, pdf ｜ docx → doc, pdf ｜ odt → docx, pdf
        </el-descriptions-item>
        <el-descriptions-item label="Excel">
          xls → xlsx, pdf ｜ xlsx → xls, pdf ｜ ods → xlsx, pdf
        </el-descriptions-item>
        <el-descriptions-item label="PowerPoint">
          ppt → pptx, pdf ｜ pptx → ppt, pdf ｜ odp → pptx, pdf
        </el-descriptions-item>
        <el-descriptions-item label="数据提取">
          xlsx / xls / ods / csv → JSON
        </el-descriptions-item>
        <el-descriptions-item label="引擎">
          LibreOffice headless（全功能）或 openpyxl（xls→xlsx 轻量）
        </el-descriptions-item>
        <el-descriptions-item label="批量">
          支持最多20个文件同时转换，结果打包 zip
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled, Document, Download, Plus, CircleCheck, Warning
} from '@element-plus/icons-vue'
import { docConverterAPI } from '@/common/api/index'

// ─── 状态 ───────────────────────────────────
const loadingStatus = ref(false)
const converterStatus = ref<any>(null)

const uploadRef = ref()
const jsonUploadRef = ref()
const batchUploadRef = ref()

const selectedFile = ref<File | null>(null)
const convForm = ref({ targetFormat: 'pdf' })
const converting = ref(false)
const convResult = ref<any>(null)

const jsonFile = ref<File | null>(null)
const jsonForm = ref({ headerRow: 0, maxRows: 2000 })
const extracting = ref(false)
const jsonResult = ref<any>(null)

const batchFiles = ref<File[]>([])
const batchTargetFormat = ref('pdf')
const batchConverting = ref(false)

// ─── 格式映射 ─────────────────────────────
const CONV_MAP: Record<string, string[]> = {
  doc:  ['docx', 'pdf'],
  docx: ['doc', 'pdf'],
  odt:  ['docx', 'pdf'],
  xls:  ['xlsx', 'pdf'],
  xlsx: ['xls', 'pdf'],
  ods:  ['xlsx', 'pdf'],
  csv:  ['json'],
  ppt:  ['pptx', 'pdf'],
  pptx: ['ppt', 'pdf'],
  odp:  ['pptx', 'pdf'],
  txt:  ['pdf'],
  md:   ['pdf'],
}

const acceptExts = '.doc,.docx,.odt,.xls,.xlsx,.ods,.csv,.ppt,.pptx,.odp,.txt,.md'
const supportedInputList = 'doc, docx, xls, xlsx, ppt, pptx, odt, ods, odp, csv, txt, md'
const allTargetFormats = ['pdf', 'docx', 'xlsx', 'pptx', 'doc', 'xls', 'ppt', 'json']

const availableTargets = computed(() => {
  if (!selectedFile.value) return ['pdf', 'docx', 'xlsx', 'pptx']
  const ext = selectedFile.value.name.split('.').pop()?.toLowerCase() || ''
  return CONV_MAP[ext] || ['pdf']
})

// ─── 生命周期 ─────────────────────────────
onMounted(() => {
  loadStatus()
})

async function loadStatus() {
  loadingStatus.value = true
  try {
    const res: any = await docConverterAPI.getStatus()
    converterStatus.value = res.data || res
  } catch {
    converterStatus.value = null
  } finally {
    loadingStatus.value = false
  }
}

// ─── 单文件转换 ───────────────────────────
function onFileChange(file: any) {
  selectedFile.value = file.raw as File
  convResult.value = null
  // 自动选第一个可用目标格式
  const targets = availableTargets.value
  if (targets.length && !targets.includes(convForm.value.targetFormat)) {
    convForm.value.targetFormat = targets[0]
  }
}

function onFileRemove() {
  selectedFile.value = null
  convResult.value = null
}

async function doConvert() {
  if (!selectedFile.value) return
  converting.value = true
  convResult.value = null
  try {
    const blob = await docConverterAPI.convert(selectedFile.value, convForm.value.targetFormat)
    // 触发下载
    const url = URL.createObjectURL(blob as Blob)
    const a = document.createElement('a')
    const stem = selectedFile.value.name.replace(/\.[^.]+$/, '')
    a.href = url
    a.download = `${stem}.${convForm.value.targetFormat}`
    a.click()
    URL.revokeObjectURL(url)
    convResult.value = { success: true, message: `转换成功，文件已下载：${stem}.${convForm.value.targetFormat}` }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '转换失败'
    convResult.value = { success: false, message: msg }
    ElMessage.error(msg)
  } finally {
    converting.value = false
  }
}

function resetConv() {
  uploadRef.value?.clearFiles()
  selectedFile.value = null
  convForm.value.targetFormat = 'pdf'
  convResult.value = null
}

// ─── JSON 提取 ────────────────────────────
function onJsonFileChange(file: any) {
  jsonFile.value = file.raw as File
  jsonResult.value = null
}

async function doExtractJson() {
  if (!jsonFile.value) return
  extracting.value = true
  jsonResult.value = null
  try {
    const res: any = await docConverterAPI.extractJson(
      jsonFile.value,
      jsonForm.value.headerRow,
      jsonForm.value.maxRows,
    )
    jsonResult.value = res.data || res
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '提取失败'
    jsonResult.value = { success: false, error: msg }
    ElMessage.error(msg)
  } finally {
    extracting.value = false
  }
}

function downloadJson() {
  if (!jsonResult.value?.data) return
  const blob = new Blob([JSON.stringify(jsonResult.value.data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const stem = jsonFile.value?.name.replace(/\.[^.]+$/, '') || 'data'
  a.href = url
  a.download = `${stem}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// ─── 批量转换 ─────────────────────────────
function onBatchFileChange(file: any) {
  batchFiles.value.push(file.raw as File)
}

function onBatchFileRemove(file: any) {
  batchFiles.value = batchFiles.value.filter(f => f.name !== file.name)
}

async function doBatchConvert() {
  if (!batchFiles.value.length) return
  batchConverting.value = true
  try {
    const blob = await docConverterAPI.batchConvert(batchFiles.value, batchTargetFormat.value)
    const url = URL.createObjectURL(blob as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'converted.zip'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(`批量转换完成，共 ${batchFiles.value.length} 个文件已打包下载`)
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '批量转换失败'
    ElMessage.error(msg)
  } finally {
    batchConverting.value = false
  }
}
</script>

<style scoped>
.doc-converter-page {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-grid {
  display: flex;
  gap: 32px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 0;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-hint {
  font-size: 12px;
  color: #e6a23c;
  margin: 0;
}

.dep-title {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin: 0 0 4px;
}

.conv-uploader {
  width: 100%;
}

.json-uploader {
  width: 100%;
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.format-selector {
  margin-top: 8px;
}

.json-preview {
  margin-top: 8px;
}

.hint-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin: 4px 0 0;
}
</style>
