import re

path = r'E:\kkflower\kflower-frontend\src\pc\views\Knowledge.vue'
with open(path, encoding='utf-8') as f:
    content = f.read()

# ===== 1. 添加批量上传按钮（文件夹上传）=====
old = """              <el-upload
                :action="`/api/v1/knowledge/upload/${currentKB.id}`"
                :headers="uploadHeaders"
                :on-success="onUploadSuccess"
                :on-error="onUploadError"
                :before-upload="beforeUpload"
                multiple
                :show-file-list="false"
                accept=".txt,.md,.pdf,.docx,.xlsx,.csv,.jpg,.png"
              >
                <el-button type="primary" size="small"><el-icon><Upload /></el-icon> 上传</el-button>
              </el-upload>"""
new = """              <el-upload
                :action="`/api/v1/knowledge/upload/${currentKB.id}`"
                :headers="uploadHeaders"
                :on-success="onUploadSuccess"
                :on-error="onUploadError"
                :before-upload="beforeUpload"
                multiple
                :show-file-list="false"
                accept=".txt,.md,.pdf,.docx,.xlsx,.csv,.jpg,.png"
              >
                <el-button type="primary" size="small"><el-icon><Upload /></el-icon> 上传</el-button>
              </el-upload>
              <el-button size="small" @click="showBatchUploadDlg">
                <el-icon><FolderOpened /></el-icon> 批量上传
              </el-button>
              <el-button size="small" @click="showFolderUploadDlg">
                <el-icon><Folder /></el-icon> 上传文件夹
              </el-button>"""
content = content.replace(old, new)

# ===== 2. 添加批量上传对话框 =====
old = """    <!-- 新建/编辑标签对话框 -->"""
new = """    <!-- 批量上传对话框 -->
    <el-dialog v-model="batchUploadDlgVisible" title="批量上传文档" width="600px">
      <div style="margin-bottom:12px">
        <p style="color:var(--el-text-color-secondary);margin-bottom:8px">
          支持格式：TXT, MD, PDF, DOCX, XLSX, CSV, JPG, PNG
        </p>
        <p style="color:var(--el-text-color-secondary);font-size:12px">
          自动识别：文本提取 / OCR图片识别 / jieba分词 / 嵌入向量 / reranker重排
        </p>
      </div>
      <el-upload
        ref="batchUploadRef"
        :action="`/api/v1/knowledge/upload-batch/${currentKB?.id}`"
        :headers="uploadHeaders"
        :on-success="onBatchUploadSuccess"
        :on-error="onBatchUploadError"
        :before-upload="beforeBatchUpload"
        multiple
        drag
        :show-file-list="true"
        accept=".txt,.md,.pdf,.docx,.xlsx,.csv,.jpg,.png"
        style="width:100%"
      >
        <el-icon :size="48" style="color:var(--el-text-color-secondary)"><Upload /></el-icon>
        <div style="margin-top:8px">拖拽文件到此处，或<em>点击上传</em></div>
        <template #tip>
          <div style="font-size:12px;color:var(--el-text-color-secondary)">
            可一次选择多个文件，系统将自动识别类型并处理
          </div>
        </template>
      </el-upload>
      <div v-if="batchUploadResults.length" style="margin-top:16px">
        <el-divider />
        <p style="font-weight:500;margin-bottom:8px">处理结果：</p>
        <div v-for="r in batchUploadResults" :key="r.title" style="font-size:13px;margin:4px 0;display:flex;align-items:center;gap:8px">
          <el-icon v-if="r.success" color="var(--el-color-success)"><CircleCheck /></el-icon>
          <el-icon v-else color="var(--el-color-danger)"><CircleClose /></el-icon>
          <span>{{ r.title }}</span>
          <el-tag v-if="r.file_type" size="small">{{ r.file_type.toUpperCase() }}</el-tag>
          <el-tag v-if="r.ocr_used" size="small" type="warning">OCR</el-tag>
          <span v-if="r.error" style="color:var(--el-color-danger)">{{ r.error }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="batchUploadDlgVisible = false">关闭</el-button>
        <el-button type="primary" @click="startBatchParse" :loading="batchParsing" :disabled="!batchUploadSuccessCount">
          开始批量解析
        </el-button>
      </template>
    </el-dialog>

    <!-- 文件夹上传对话框 -->
    <el-dialog v-model="folderUploadDlgVisible" title="上传文件夹" width="600px">
      <div style="margin-bottom:12px">
        <p style="color:var(--el-text-color-secondary)">选择文件夹，系统将递归上传所有支持的文件</p>
      </div>
      <input
        ref="folderInputRef"
        type="file"
        webkitdirectory
        directory
        multiple
        style="display:none"
        @change="onFolderSelected"
      />
      <el-button type="primary" @click="folderInputRef?.click()">
        <el-icon><Folder /></el-icon> 选择文件夹
      </el-button>
      <div v-if="folderFiles.length" style="margin-top:16px;max-height:300px;overflow-y:auto">
        <el-divider />
        <p style="font-weight:500;margin-bottom:8px">待上传文件 ({{ folderFiles.length }}个):</p>
        <div v-for="f in folderFiles.slice(0,20)" :key="f.name" style="font-size:13px;margin:2px 0">
          {{ f.name }} ({{ formatSize(f.size) }})
        </div>
        <div v-if="folderFiles.length > 20" style="color:var(--el-text-color-secondary);font-size:12px">
          ...还有 {{ folderFiles.length - 20 }} 个文件
        </div>
      </div>
      <template #footer>
        <el-button @click="folderUploadDlgVisible = false">取消</el-button>
        <el-button type="primary" @click="uploadFolderFiles" :loading="folderUploading" :disabled="!folderFiles.length">
          开始上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑标签对话框 -->"""
content = content.replace(old, new)

# ===== 3. 添加图标导入 =====
old = "  Plus, Refresh, FolderOpened, Upload, Search, MagicStick, Document, MoreFilled,\n  ChatLineSquare, DataAnalysis, Collection, Edit, View\n} from '@element-plus/icons-vue'"
new = "  Plus, Refresh, FolderOpened, Upload, Search, MagicStick, Document, MoreFilled,\n  ChatLineSquare, DataAnalysis, Collection, Edit, View, Folder, CircleCheck, CircleClose\n} from '@element-plus/icons-vue'"
content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Lines: {len(content.splitlines())}')
