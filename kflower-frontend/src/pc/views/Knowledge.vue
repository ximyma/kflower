<template>
  <div class="knowledge-page">
    <!-- 左侧知识库面板 -->
    <div class="left-panel">
      <div class="panel-header">
        <h3>知识库</h3>
        <div class="panel-actions">
          <el-button size="small" type="primary" @click="openCreateKBDlg">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button size="small" @click="loadKnowledgeBases">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="kb-list">
        <div
          v-for="kb in knowledgeBases" :key="kb.id"
          class="kb-item"
          :class="{ active: currentKB?.id === kb.id }"
          @click="selectKB(kb)"
          @contextmenu.prevent="showKBMenu($event, kb)"
        >
          <el-icon><FolderOpened /></el-icon>
          <div class="kb-item-info">
            <span class="kb-item-name">{{ kb.name }}</span>
            <span class="kb-item-count">{{ kb.doc_count || 0 }} 篇</span>
          </div>
        </div>
        <el-empty v-if="!knowledgeBases.length" description="暂无知识库" :image-size="60" />
      </div>
    </div>

    <!-- 右侧主面板 -->
    <div class="right-panel">
      <template v-if="currentKB">
        <!-- 标签页 -->
        <el-tabs v-model="activeTab" class="main-tabs">
          <!-- 文档管理 -->
          <el-tab-pane label="文档管理" name="docs">
            <div class="tab-toolbar">
              <el-upload
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
              </el-button>
              <el-button size="small" @click="parseAllDocs" :loading="parsingAll">
                <el-icon><MagicStick /></el-icon> 批量解析
              </el-button>
              <el-button size="small" @click="batchRenameDocs">
                <el-icon><Edit /></el-icon> 批量改名
              </el-button>
              <el-button size="small" @click="loadDocuments">
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
              <div style="flex:1" />
              <el-input v-model="docSearch" placeholder="搜索文档..." clearable style="width:200px" @input="filterDocs">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </div>
            <el-table :data="filteredDocs" v-loading="loadingDocs" style="width:100%" max-height="calc(100vh - 260px)"
              @row-contextmenu="showDocMenu"
            >
              <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
              <el-table-column prop="file_type" label="类型" width="70">
                <template #default="{ row }">
                  <el-tag size="small">{{ (row.file_type || '').toUpperCase() }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="file_size" label="大小" width="80">
                <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
              </el-table-column>
              <el-table-column prop="parsing_status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="statusType(row.parsing_status)" size="small">{{ statusText(row.parsing_status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="关键词" min-width="150">
                <template #default="{ row }">
                  <el-tag v-for="kw in (row.keywords || []).slice(0,3)" :key="kw" size="small" type="info" style="margin:2px">{{ kw }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="标签" min-width="120">
                <template #default="{ row }">
                  <el-tag v-for="t in (row.tags || []).slice(0,3)" :key="t" size="small" style="margin:2px">{{ t }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" link @click="viewDoc(row)">查看</el-button>
                  <el-button v-if="row.parsing_status==='pending'||row.parsing_status==='failed'" size="small" link type="primary" @click="parseDoc(row)">解析</el-button>
                  <el-button size="small" link type="danger" @click="deleteDoc(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 高级检索 -->
          <el-tab-pane label="高级检索" name="search">
            <div class="search-bar">
              <el-radio-group v-model="searchType" size="small">
                <el-radio-button value="fulltext">全文</el-radio-button>
                <el-radio-button value="keyword">关键词</el-radio-button>
                <el-radio-button value="vector">向量</el-radio-button>
                <el-radio-button value="hybrid">混合</el-radio-button>
              </el-radio-group>
              <el-input v-model="searchQuery" placeholder="输入检索内容..." clearable style="flex:1" @keyup.enter="doSearch">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
              <el-select v-model="searchTag" placeholder="标签过滤" clearable size="small" style="width:120px">
                <el-option v-for="t in allTags" :key="t.id" :label="t.name" :value="t.name" />
              </el-select>
              <el-button type="primary" @click="doSearch" :loading="searching">检索</el-button>
              <el-button size="small" @click="sendSearchToChat" :disabled="!searchResults.length">
                <el-icon><ChatLineSquare /></el-icon> 发送到AI
              </el-button>
            </div>
            <el-table :data="searchResults" style="width:100%;margin-top:16px" max-height="calc(100vh - 320px)">
              <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
              <el-table-column label="得分" width="80">
                <template #default="{ row }">{{ (row.score || 0).toFixed(3) }}</template>
              </el-table-column>
              <el-table-column prop="text" label="内容片段" min-width="300" show-overflow-tooltip />
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button size="small" link @click="viewDoc({id: row.doc_id, title: row.title})">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 标签管理 -->
          <el-tab-pane label="标签管理" name="tags">
            <div class="tab-toolbar" style="margin-bottom:12px">
              <el-button size="small" type="primary" @click="showCreateTagDlg">
                <el-icon><Plus /></el-icon> 新建标签
              </el-button>
              <el-button size="small" @click="batchAutoTag" :loading="autoTagging">
                <el-icon><MagicStick /></el-icon> 批量自动打标签
              </el-button>
            </div>
            <div class="tag-grid">
              <div v-for="tag in allTags" :key="tag.id" class="tag-card"
                :style="{ borderColor: tag.color + '40', background: tag.color + '10' }"
              >
                <span class="tag-dot" :style="{ background: tag.color }" />
                <span class="tag-name">{{ tag.name }}</span>
                <span class="tag-count">{{ tag.doc_count || 0 }} 篇</span>
                <div class="tag-actions">
                  <el-button size="small" link @click="editTag(tag)">编辑</el-button>
                  <el-button size="small" link type="danger" @click="deleteTag(tag)">删除</el-button>
                </div>
              </div>
              <el-empty v-if="!allTags.length" description="暂无标签" :image-size="60" />
            </div>
          </el-tab-pane>

          <!-- AI对话 -->
          <el-tab-pane label="AI对话" name="chat">
            <div class="chat-container">
              <div class="chat-messages" ref="chatBox">
                <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.role]">
                  <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
                  <div class="msg-content">{{ msg.content }}</div>
                </div>
                <div v-if="chatLoading" class="chat-msg assistant">
                  <div class="msg-avatar">🤖</div>
                  <div class="msg-content typing">思考中...</div>
                </div>
              </div>
              <div class="chat-input">
                <el-upload
                  :action="`/api/v1/knowledge/upload/${currentKB?.id}`"
                  :headers="uploadHeaders"
                  :on-success="onChatFileUpload"
                  :before-upload="beforeUpload"
                  :show-file-list="false"
                  accept=".txt,.md,.pdf,.docx"
                >
                  <el-button size="small" :disabled="chatLoading"><el-icon><Upload /></el-icon></el-button>
                </el-upload>
                <el-input v-model="chatInput" placeholder="基于知识库提问..." @keyup.enter="sendChat" :disabled="chatLoading" style="flex:1" />
                <el-button type="primary" @click="sendChat" :loading="chatLoading">发送</el-button>
              </div>
            </div>
          </el-tab-pane>

          <!-- 笔记 -->
          <el-tab-pane label="笔记" name="notes">
            <div class="notes-layout">
              <div class="notes-list">
                <el-button size="small" type="primary" style="width:100%;margin-bottom:8px" @click="createNote">新建笔记</el-button>
                <div
                  v-for="n in notes" :key="n.id"
                  class="note-item"
                  :class="{ active: currentNote?.id === n.id }"
                  @click="selectNote(n)"
                >
                  <div class="note-title">{{ n.title }}</div>
                  <div class="note-date">{{ formatDate(n.updated_at || n.created_at) }}</div>
                </div>
                <el-empty v-if="!notes.length" description="暂无笔记" :image-size="40" />
              </div>
              <div class="notes-editor" v-if="currentNote">
                <el-input v-model="currentNote.title" placeholder="标题" style="margin-bottom:8px" @change="saveNote" />
                <el-input type="textarea" v-model="currentNote.content" :rows="16" placeholder="内容（支持Markdown）" @change="saveNote" />
                <div style="margin-top:8px;display:flex;gap:8px">
                  <el-tag v-for="t in (currentNote.tags || [])" :key="t" closable @close="removeNoteTag(t)" size="small">{{ t }}</el-tag>
                  <el-button size="small" @click="addNoteTag">+标签</el-button>
                  <div style="flex:1" />
                  <el-button size="small" type="danger" @click="deleteNote">删除</el-button>
                </div>
              </div>
              <div v-else class="notes-placeholder">选择或新建笔记</div>
            </div>
          </el-tab-pane>

          <!-- 知识图谱 -->
          <el-tab-pane label="知识图谱" name="graph">
            <div ref="graphContainer" class="graph-container" v-loading="loadingGraph">
              <div v-if="!graphData.nodes.length" class="graph-placeholder">
                <el-empty description="暂无图谱数据" />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
      <template v-else>
        <div class="empty-state">
          <el-icon :size="64" color="#c0c4cc"><FolderOpened /></el-icon>
          <p>请从左侧选择或新建知识库</p>
        </div>
      </template>
    </div>

    <!-- 新建知识库对话框 -->
    <el-dialog v-model="createKBDlg" title="新建知识库" width="500px">
      <el-form :model="newKBForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="newKBForm.name" placeholder="知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newKBForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="Embedding">
          <el-select v-model="newKBForm.embedding_model" style="width:100%">
            <el-option label="all-mpnet-base-v2 (本地)" value="E:\models\all-mpnet-base-v2" />
            <el-option label="BAAI/bge-m3" value="BAAI/bge-m3" />
            <el-option label="text-embedding-v2" value="text-embedding-v2" />
          </el-select>
        </el-form-item>
        <el-form-item label="Rerank">
          <el-switch v-model="newKBForm.rerank_enabled" />
        </el-form-item>
        <el-form-item label="Rerank模型" v-if="newKBForm.rerank_enabled">
          <el-select v-model="newKBForm.rerank_model" style="width:100%">
            <el-option label="bge-reranker-v2-m3 (本地)" value="E:\models\bge-reranker-v2-m3" />
            <el-option label="BAAI/bge-reranker-v2-m3" value="BAAI/bge-reranker-v2-m3" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createKBDlg = false">取消</el-button>
        <el-button type="primary" @click="handleCreateKB" :loading="creatingKB">创建</el-button>
      </template>
    </el-dialog>

    <!-- 批量上传对话框 -->
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

    <!-- 新建/编辑标签对话框 -->
    <el-dialog v-model="tagDialogVisible" :title="editingTag ? '编辑标签' : '新建标签'" width="400px">
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="tagForm.name" placeholder="标签名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="tagForm.color" />
          <span style="margin-left:8px">{{ tagForm.color }}</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="tagForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tagDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveTag" :loading="savingTag">保存</el-button>
      </template>
    </el-dialog>

    <!-- 文档右键菜单 -->
    <el-dialog v-model="docMenuVisible" title="文档操作" width="400px" :modal="false">
      <div style="display:flex;flex-direction:column;gap:4px">
        <el-button text @click="viewDoc(selectedDoc!)"><el-icon><View /></el-icon> 查看文档</el-button>
        <el-button text @click="sendDocToChat(selectedDoc!)"><el-icon><ChatLineSquare /></el-icon> 发送到AI聊天</el-button>
        <el-button text @click="analyzeDoc(selectedDoc!)"><el-icon><DataAnalysis /></el-icon> 分析文档</el-button>
        <el-button text @click="manageDocTags(selectedDoc!)"><el-icon><Collection /></el-icon> 管理标签</el-button>
        <el-button v-if="selectedDoc?.parsing_status==='pending'||selectedDoc?.parsing_status==='failed'" text @click="parseDoc(selectedDoc!)"><el-icon><MagicStick /></el-icon> 解析文档</el-button>
        <el-button text @click="renameDoc(selectedDoc!)"><el-icon><Edit /></el-icon> 重命名</el-button>
        <el-button text type="danger" @click="deleteDoc(selectedDoc!)"><el-icon><Delete /></el-icon> 删除文档</el-button>
      </div>
    </el-dialog>

    <!-- 批量改名对话框 -->
    <el-dialog v-model="batchRenameDlg" title="批量修改文档名" width="600px">
      <p style="color:var(--el-text-color-secondary);margin-bottom:12px">
        共 {{ selectedDocsForRename.length }} 个文档，将按规则批量重命名
      </p>
      <el-form label-width="120px">
        <el-form-item label="命名规则">
          <el-input v-model="renameRule" placeholder="如: {title}_{date}" style="width:300px" />
        </el-form-item>
        <el-form-item label="预览">
          <div style="max-height:200px;overflow-y:auto">
            <div v-for="doc in selectedDocsForRename.slice(0,10)" :key="doc.id" style="font-size:12px;margin:4px 0">
              {{ doc.title }} → <span style="color:var(--el-color-success)">{{ applyRenameRule(doc) }}</span>
            </div>
            <div v-if="selectedDocsForRename.length > 10" style="color:var(--el-text-color-secondary)">
              ...还有 {{ selectedDocsForRename.length - 10 }} 个
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchRenameDlg = false">取消</el-button>
        <el-button type="primary" @click="applyBatchRename">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 文档标签管理对话框 -->
    <el-dialog v-model="docTagsDlgVisible" :title="`管理标签 - ${tagDoc?.title}`" width="500px">
      <div class="doc-tags-editor">
        <p style="margin-bottom:12px">当前标签：</p>
        <div style="margin-bottom:12px;display:flex;flex-wrap:wrap;gap:6px">
          <el-tag
            v-for="t in docCurrentTags" :key="t.id"
            closable @close="removeDocTag(t)"
            :style="{ borderColor: t.color + '60' }"
          >{{ t.name }}</el-tag>
        </div>
        <el-divider />
        <p style="margin-bottom:8px">添加标签：</p>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          <el-tag
            v-for="t in allTags.filter(tag => !docCurrentTags.find(t2 => t2.id === tag.id))"
            :key="tag.id"
            style="cursor:pointer"
            @click="addDocTag(tag)"
            :style="{ borderColor: tag.color + '40', background: tag.color + '10' }"
          >+ {{ tag.name }}</el-tag>
        </div>
        <el-empty v-if="allTags.length === 0" description="暂无标签，请先创建" />
      </div>
    </el-dialog>

    <!-- 文档详情对话框 -->
    <el-dialog v-model="docDetailDlg" :title="docDetail?.title" width="700px">
      <div v-if="docDetail">
        <div style="margin-bottom:12px">
          <el-tag size="small">{{ docDetail.file_type?.toUpperCase() }}</el-tag>
          <span style="margin-left:8px;color:var(--el-text-color-secondary)">{{ formatSize(docDetail.file_size) }}</span>
          <span style="margin-left:8px;color:var(--el-text-color-secondary)">{{ formatDate(docDetail.created_at) }}</span>
        </div>
        <div v-if="docDetail.keywords?.length" style="margin-bottom:12px">
          <strong>关键词：</strong>
          <el-tag v-for="kw in docDetail.keywords" :key="kw" size="small" type="info" style="margin:2px">{{ kw }}</el-tag>
        </div>
        <div v-if="docDetail.summary" style="margin-bottom:12px;padding:8px 12px;background:var(--el-fill-color-light);border-radius:4px">
          <strong>摘要：</strong>{{ docDetail.summary }}
        </div>
        <el-input type="textarea" :model-value="docDetail.content?.substring(0, 3000)" :rows="12" readonly />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import {
  Plus, Refresh, FolderOpened, Upload, Search, MagicStick, Document, MoreFilled,
  ChatLineSquare, DataAnalysis, Collection, Edit, View, Folder, CircleCheck, CircleClose
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeAPI } from '../../common/api'

const token = localStorage.getItem('kflower_token') || ''
const uploadHeaders = { Authorization: `Bearer ${token}` }

// ===== 知识库 =====
const knowledgeBases = ref<any[]>([])
const currentKB = ref<any>(null)
const createKBDlg = ref(false)
const creatingKB = ref(false)
const newKBForm = ref({ name: '', description: '', embedding_model: 'E:\\models\\all-mpnet-base-v2', rerank_enabled: false, rerank_model: 'E:\\models\\bge-reranker-v2-m3' })

async function loadKnowledgeBases() {
  try {
    const res: any = await knowledgeAPI.listBases()
    knowledgeBases.value = Array.isArray(res) ? res : (res.data || [])
  } catch { ElMessage.error('加载知识库失败') }
}

function selectKB(kb: any) {
  currentKB.value = kb
  activeTab.value = 'docs'
  loadDocuments()
  loadTags()
  loadNotes()
}

function openCreateKBDlg() {
  newKBForm.value = { name: '', description: '', embedding_model: 'E:\\models\\all-mpnet-base-v2', rerank_enabled: false, rerank_model: 'E:\\models\\bge-reranker-v2-m3' }
  createKBDlg.value = true
}

async function handleCreateKB() {
  if (!newKBForm.value.name) return ElMessage.warning('请输入名称')
  creatingKB.value = true
  try {
    await knowledgeAPI.createBase(newKBForm.value)
    ElMessage.success('创建成功')
    createKBDlg.value = false
    loadKnowledgeBases()
  } catch (e: any) { ElMessage.error(e.message || '创建失败') }
  finally { creatingKB.value = false }
}

function showKBMenu(e: MouseEvent, kb: any) {
  // 右键菜单可后续用el-dropdown实现
}

// ===== 文档 =====
const documents = ref<any[]>([])
const loadingDocs = ref(false)
const docSearch = ref('')
const parsingAll = ref(false)
const docDetailDlg = ref(false)
const docDetail = ref<any>(null)

const filteredDocs = computed(() => {
  if (!docSearch.value) return documents.value
  const kw = docSearch.value.toLowerCase()
  return documents.value.filter(d => d.title?.toLowerCase().includes(kw) || (d.keywords || []).some((k: string) => k.toLowerCase().includes(kw)))
})

async function loadDocuments() {
  if (!currentKB.value) return
  loadingDocs.value = true
  try {
    const res: any = await knowledgeAPI.listDocuments(currentKB.value.id)
    documents.value = Array.isArray(res) ? res : (res.data || [])
  } catch { ElMessage.error('加载文档失败') }
  finally { loadingDocs.value = false }
}

function filterDocs() {}

function beforeUpload(file: File) {
  const ok = ['.txt', '.md', '.pdf', '.docx', '.xlsx', '.csv', '.jpg', '.png'].some(ext => file.name.toLowerCase().endsWith(ext))
  if (!ok) { ElMessage.error('不支持的格式'); return false }
  return true
}

function onUploadSuccess() { ElMessage.success('上传成功'); loadDocuments() }
function onUploadError() { ElMessage.error('上传失败') }

async function parseDoc(doc: any) {
  try {
    await knowledgeAPI.parseDocument(doc.id)
    ElMessage.success('解析已提交')
    setTimeout(() => loadDocuments(), 2000)
  } catch (e: any) { ElMessage.error(e.message || '解析失败') }
}

async function parseAllDocs() {
  if (!currentKB.value) return
  parsingAll.value = true
  try {
    await knowledgeAPI.parseAll(currentKB.value.id)
    ElMessage.success('批量解析完成')
    loadDocuments()
  } catch (e: any) { ElMessage.error(e.message || '批量解析失败') }
  finally { parsingAll.value = false }
}

async function deleteDoc(doc: any) {
  try {
    await ElMessageBox.confirm(`删除文档 "${doc.title}"？`, '确认', { type: 'warning' })
    await knowledgeAPI.deleteDocument(doc.id)
    ElMessage.success('已删除')
    loadDocuments()
  } catch {}
}

async function viewDoc(doc: any) {
  try {
    const res: any = await knowledgeAPI.getDocument(doc.id)
    docDetail.value = res.data || res
    docDetailDlg.value = true
  } catch { ElMessage.error('加载失败') }
}

// ===== 检索 =====
const activeTab = ref('docs')
const searchType = ref('hybrid')
const searchQuery = ref('')
const searchTag = ref('')
const searching = ref(false)
const searchResults = ref<any[]>([])

async function doSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const res: any = await knowledgeAPI.search({
      q: searchQuery.value,
      type: searchType.value,
      kb_id: currentKB.value?.id,
      tag: searchTag.value || undefined,
      top_k: 10
    })
    searchResults.value = res.results || res.data || []
  } catch (e: any) { ElMessage.error(e.message || '检索失败') }
  finally { searching.value = false }
}

// ===== 标签 =====
const allTags = ref<any[]>([])

async function loadTags() {
  try {
    const res: any = await knowledgeAPI.listTags(currentKB.value?.id)
    allTags.value = Array.isArray(res) ? res : (res.data || [])
  } catch {}
}

// ===== AI对话 =====
const chatMessages = ref<{ role: string; content: string }[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatBox = ref<HTMLElement>()

async function sendChat() {
  const q = chatInput.value.trim()
  if (!q) return
  chatMessages.value.push({ role: 'user', content: q })
  chatInput.value = ''
  chatLoading.value = true
  try {
    const res: any = await knowledgeAPI.query({ query: q, kb_id: currentKB.value?.id, top_k: 5 })
    const results = res.results || []
    let answer = '未找到相关内容。'
    if (results.length > 0) {
      answer = results.map((r: any, i: number) => `【${i + 1}】${r.text || r.content || ''}`).join('\n\n')
    }
    chatMessages.value.push({ role: 'assistant', content: answer })
  } catch (e: any) {
    chatMessages.value.push({ role: 'assistant', content: '查询出错: ' + (e.message || '') })
  } finally { chatLoading.value = false }
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

// ===== 笔记 =====
const notes = ref<any[]>([])
const currentNote = ref<any>(null)

async function loadNotes() {
  try {
    const res: any = await knowledgeAPI.listNotes(currentKB.value?.id)
    notes.value = Array.isArray(res) ? res : (res.data || [])
  } catch {}
}

function createNote() {
  const n = { id: 0, title: '新笔记', content: '', tags: [], is_daily: false }
  notes.value.unshift(n)
  currentNote.value = n
}

async function selectNote(n: any) {
  if (n.id) {
    try {
      const res: any = await knowledgeAPI.getNote(n.id)
      currentNote.value = res.data || res
    } catch { currentNote.value = n }
  } else {
    currentNote.value = n
  }
}

async function saveNote() {
  if (!currentNote.value) return
  try {
    if (currentNote.value.id) {
      await knowledgeAPI.updateNote(currentNote.value.id, {
        title: currentNote.value.title,
        content: currentNote.value.content,
        tags: currentNote.value.tags
      })
    } else {
      const res: any = await knowledgeAPI.createNote({
        title: currentNote.value.title,
        content: currentNote.value.content,
        tags: currentNote.value.tags,
        knowledge_base_id: currentKB.value?.id
      })
      currentNote.value.id = res.data?.id || res.id
    }
    ElMessage.success('已保存')
    loadNotes()
  } catch (e: any) { ElMessage.error(e.message || '保存失败') }
}

async function deleteNote() {
  if (!currentNote.value?.id) return
  try {
    await ElMessageBox.confirm('删除此笔记？', '确认', { type: 'warning' })
    await knowledgeAPI.deleteNote(currentNote.value.id)
    currentNote.value = null
    loadNotes()
  } catch {}
}

function addNoteTag() {
  const tag = prompt('输入标签名')
  if (tag && currentNote.value) {
    if (!currentNote.value.tags) currentNote.value.tags = []
    currentNote.value.tags.push(tag)
    saveNote()
  }
}

function removeNoteTag(tag: string) {
  if (currentNote.value?.tags) {
    currentNote.value.tags = currentNote.value.tags.filter((t: string) => t !== tag)
    saveNote()
  }
}

// ===== 知识图谱 =====
const graphContainer = ref<HTMLElement>()
const graphData = ref<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] })
const loadingGraph = ref(false)

async function loadGraph() {
  if (!currentKB.value) return
  loadingGraph.value = true
  try {
    const res: any = await knowledgeAPI.getGraph(currentKB.value.id)
    graphData.value = res.data || res || { nodes: [], links: [] }
    if (graphData.value.nodes.length) {
      await nextTick()
      renderGraph()
    }
  } catch {}
  finally { loadingGraph.value = false }
}

function renderGraph() {
  // 简单ECharts关系图渲染
  if (!graphContainer.value || !graphData.value.nodes.length) return
  import('echarts').then(echarts => {
    const chart = echarts.init(graphContainer.value!)
    chart.setOption({
      tooltip: {},
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        label: { show: true, position: 'right' },
        force: { repulsion: 100, edgeLength: 80 },
        data: graphData.value.nodes,
        links: graphData.value.links
      }]
    })
  })
}

watch(activeTab, (v) => { if (v === 'graph') loadGraph() })

// ===== 工具函数 =====
function formatDate(d: string) { return d ? new Date(d).toLocaleDateString('zh-CN') : '-' }
function formatSize(s: number) {
  if (!s) return '-'
  if (s < 1024) return s + ' B'
  if (s < 1048576) return (s / 1024).toFixed(1) + ' KB'
  return (s / 1048576).toFixed(1) + ' MB'
}
function statusType(s: string) { return ({ completed: 'success', processing: 'warning', pending: 'info', failed: 'danger' } as any)[s] || 'info' }
function statusText(s: string) { return ({ completed: '已完成', processing: '处理中', pending: '等待中', failed: '失败' } as any)[s] || s }


// ===== 批量改名 =====
const batchRenameDlg = ref(false)
const renameRule = ref('{title}')
const selectedDocsForRename = ref<any[]>([])

function batchRenameDocs() {
  if (!filteredDocs.value.length) return ElMessage.warning('没有可改名的文档')
  selectedDocsForRename.value = [...filteredDocs.value]
  renameRule.value = '{title}'
  batchRenameDlg.value = true
}

function applyRenameRule(doc: any) {
  const d = new Date().toISOString().substring(0, 10)
  return renameRule.value
    .replace('{title}', doc.title.replace(/\.[^.]+$/, ''))
    .replace('{date}', d)
    .replace('{type}', doc.file_type || 'doc')
}

async function applyBatchRename() {
  ElMessage.info('批量改名功能已记录，暂支持手动编辑文档名称')
  batchRenameDlg.value = false
}

// ===== 文档右键菜单 =====
const docMenuVisible = ref(false)
const selectedDoc = ref<any>(null)

function showDocMenu(row: any, event: MouseEvent) {
  selectedDoc.value = row
  // 使用el-popover模拟右键菜单
  docMenuVisible.value = true
}

async function sendDocToChat(doc: any) {
  docMenuVisible.value = false
  try {
    const res: any = await knowledgeAPI.getDocument(doc.id)
    const d = res.data || res
    if (d.content) {
      activeTab.value = 'chat'
      chatMessages.value.push({
        role: 'user',
        content: `请分析以下文档内容：\n\n【${d.title}】\n${d.content.substring(0, 2000)}`
      })
      sendChat()
    } else {
      ElMessage.warning('文档内容为空，请先解析')
    }
  } catch { ElMessage.error('加载文档失败') }
}

async function analyzeDoc(doc: any) {
  docMenuVisible.value = false
  try {
    const res: any = await knowledgeAPI.getDocument(doc.id)
    const d = res.data || res
    const info = [
      `标题: ${d.title}`,
      `类型: ${d.file_type}`,
      `大小: ${formatSize(d.file_size)}`,
      `状态: ${statusText(d.parsing_status)}`,
      `关键词: ${(d.keywords || []).join(', ') || '无'}`,
      `摘要: ${d.summary || '无'}`,
      `字数: ${(d.content || '').length} 字`,
      `创建: ${formatDate(d.created_at)}`,
    ].join('\n')
    ElMessageBox.alert(info, '文档分析', { confirmButtonText: '确定' })
  } catch { ElMessage.error('分析失败') }
}

async function manageDocTags(doc: any) {
  docMenuVisible.value = false
  tagDoc.value = doc
  // 加载文档已有标签
  try {
    const allT: any[] = await knowledgeAPI.listTags(currentKB.value?.id)
    const tags = Array.isArray(allT) ? allT : (allT.data || [])
    // 文档标签从文档详情中获取
    const res: any = await knowledgeAPI.getDocument(doc.id)
    const d = res.data || res
    const docTagIds = (d.tags || []).map((t: any) => typeof t === 'object' ? t.id : t)
    docCurrentTags.value = tags.filter((t: any) => docTagIds.includes(t.id))
  } catch {}
  docTagsDlgVisible.value = true
}

function renameDoc(doc: any) {
  docMenuVisible.value = false
  ElMessageBox.prompt('输入新名称', '重命名文档', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: doc.title
  }).then(({ value }: any) => {
    ElMessage.info('重命名功能需要后端支持，目前请通过编辑知识库元数据实现')
  }).catch(() => {})
}

// ===== 标签管理 =====
const tagDialogVisible = ref(false)
const editingTag = ref<any>(null)
const tagForm = ref({ name: '', color: '#1890ff', description: '' })
const savingTag = ref(false)
const autoTagging = ref(false)

function showCreateTagDlg() {
  editingTag.value = null
  tagForm.value = { name: '', color: '#1890ff', description: '' }
  tagDialogVisible.value = true
}

function editTag(tag: any) {
  editingTag.value = tag
  tagForm.value = { name: tag.name, color: tag.color || '#1890ff', description: tag.description || '' }
  tagDialogVisible.value = true
}

async function handleSaveTag() {
  if (!tagForm.value.name) return ElMessage.warning('请输入名称')
  savingTag.value = true
  try {
    if (editingTag.value) {
      ElMessage.info('标签更新已记录')
    } else {
      await knowledgeAPI.createTag({
        name: tagForm.value.name,
        color: tagForm.value.color,
        description: tagForm.value.description
      })
      ElMessage.success('标签创建成功')
    }
    tagDialogVisible.value = false
    loadTags()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
  finally { savingTag.value = false }
}

async function deleteTag(tag: any) {
  try {
    await ElMessageBox.confirm(`删除标签"${tag.name}"？`, '确认', { type: 'warning' })
    await knowledgeAPI.deleteTag(tag.id)
    ElMessage.success('已删除')
    loadTags()
  } catch {}
}

// ===== 批量自动打标签 =====
async function batchAutoTag() {
  if (!filteredDocs.value.length) return ElMessage.warning('没有可处理的文档')
  autoTagging.value = true
  let done = 0
  for (const doc of filteredDocs.value) {
    if (doc.parsing_status !== 'completed') continue
    try {
      // 自动打标签逻辑：根据关键词自动匹配已有标签
      const kwList: string[] = doc.keywords || []
      for (const tag of allTags.value) {
        if (kwList.some(kw => tag.name.includes(kw) || kw.includes(tag.name))) {
          await knowledgeAPI.addDocTag(doc.id, tag.id)
        }
      }
      done++
    } catch {}
  }
  autoTagging.value = false
  ElMessage.success(`批量打标签完成，处理了 ${done} 个文档`)
  loadDocuments()
}

// ===== 文档标签管理对话框 =====
const docTagsDlgVisible = ref(false)
const tagDoc = ref<any>(null)
const docCurrentTags = ref<any[]>([])

async function addDocTag(tag: any) {
  if (!tagDoc.value) return
  try {
    await knowledgeAPI.addDocTag(tagDoc.value.id, tag.id)
    docCurrentTags.value.push(tag)
    ElMessage.success(`已添加标签"${tag.name}"`)
  } catch (e: any) { ElMessage.error(e.message || '添加失败') }
}

async function removeDocTag(tag: any) {
  if (!tagDoc.value) return
  try {
    await knowledgeAPI.removeDocTag(tagDoc.value.id, tag.id)
    docCurrentTags.value = docCurrentTags.value.filter(t => t.id !== tag.id)
    ElMessage.success(`已移除标签"${tag.name}"`)
  } catch (e: any) { ElMessage.error(e.message || '移除失败') }
}

// ===== 搜索结果发送到AI对话 =====
function sendSearchToChat() {
  if (!searchResults.value.length) return
  activeTab.value = 'chat'
  const summary = searchResults.value.map((r: any, i: number) =>
    `【${i + 1}】${r.title || r.text?.substring(0, 50)}\n${r.summary || r.text || ''}`
  ).join('\n\n')
  chatMessages.value.push({
    role: 'user',
    content: `基于以下检索结果回答问题：\n${summary}`
  })
  sendChat()
}

// ===== AI对话增强 =====

async function onChatFileUpload(res: any) {
  ElMessage.success('文件已上传，可结合此文档提问')
}

// ===== 批量上传 =====
const batchUploadDlgVisible = ref(false)
const batchUploadRef = ref<any>(null)
const batchUploadResults = ref<any[]>([])
const batchUploadSuccessCount = ref(0)
const batchParsing = ref(false)

function showBatchUploadDlg() {
  batchUploadResults.value = []
  batchUploadSuccessCount.value = 0
  batchUploadDlgVisible.value = true
}

function beforeBatchUpload(file: File) {
  const ok = ['.txt', '.md', '.pdf', '.docx', '.xlsx', '.csv', '.jpg', '.jpeg', '.png', '.bmp'].some(ext => file.name.toLowerCase().endsWith(ext))
  if (!ok) {
    ElMessage.warning(`不支持的格式: ${file.name}`)
    return false
  }
  return true
}

function onBatchUploadSuccess(res: any, file: File) {
  batchUploadResults.value.push({
    title: file.name,
    success: true,
    file_type: file.name.split('.').pop(),
    ocr_used: file.type?.startsWith('image/') || file.name.match(/\.(jpg|jpeg|png|bmp)$/i)
  })
  batchUploadSuccessCount.value++
  ElMessage.success(`${file.name} 上传成功`)
}

function onBatchUploadError(err: any, file: File) {
  batchUploadResults.value.push({
    title: file.name,
    success: false,
    error: err?.message || '上传失败'
  })
  ElMessage.error(`${file.name} 上传失败`)
}

async function startBatchParse() {
  if (!currentKB.value) return
  batchParsing.value = true
  try {
    await knowledgeAPI.parseAll(currentKB.value.id)
    ElMessage.success('批量解析已启动')
    batchUploadDlgVisible.value = false
    setTimeout(() => loadDocuments(), 3000)
  } catch (e: any) {
    ElMessage.error(e.message || '解析失败')
  } finally {
    batchParsing.value = false
  }
}

// ===== 文件夹上传 =====
const folderUploadDlgVisible = ref(false)
const folderInputRef = ref<HTMLInputElement>()
const folderFiles = ref<File[]>([])
const folderUploading = ref(false)

function showFolderUploadDlg() {
  folderFiles.value = []
  folderUploadDlgVisible.value = true
}

function onFolderSelected(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files) {
    const supported = ['.txt', '.md', '.pdf', '.docx', '.xlsx', '.csv', '.jpg', '.jpeg', '.png', '.bmp']
    folderFiles.value = Array.from(files).filter(f => supported.some(ext => f.name.toLowerCase().endsWith(ext)))
  }
}

async function uploadFolderFiles() {
  if (!currentKB.value || !folderFiles.value.length) return
  folderUploading.value = true
  const formData = new FormData()
  folderFiles.value.forEach(f => formData.append('files', f))
  try {
    const res: any = await fetch(`/api/v1/knowledge/upload-batch/${currentKB.value.id}`, {
      method: 'POST',
      headers: { 'Authorization': uploadHeaders.Authorization },
      body: formData
    })
    const data = await res.json()
    if (data.success !== false) {
      ElMessage.success(`成功上传 ${folderFiles.value.length} 个文件`)
      folderUploadDlgVisible.value = false
      loadDocuments()
    } else {
      ElMessage.error(data.message || '上传失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    folderUploading.value = false
  }
}

onMounted(() => { loadKnowledgeBases() })
</script>

<style scoped>
.knowledge-page {
  display: flex;
  height: calc(100vh - 100px);
  gap: 0;
}
.left-panel {
  width: 240px;
  min-width: 240px;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-light);
}
.panel-header h3 {
  margin: 0;
  font-size: 15px;
}
.panel-actions {
  display: flex;
  gap: 4px;
}
.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.kb-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.kb-item:hover {
  background: var(--el-fill-color);
}
.kb-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.kb-item-info {
  flex: 1;
  min-width: 0;
}
.kb-item-name {
  display: block;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kb-item-count {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.right-panel {
  flex: 1;
  min-width: 0;
  padding: 12px 20px;
  overflow-y: auto;
}
.main-tabs {
  height: 100%;
}
.tab-toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
}
/* 检索 */
.search-bar {
  display: flex;
  gap: 8px;
  align-items: center;
}
/* AI对话 */
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 260px);
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.chat-msg {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.chat-msg.user {
  flex-direction: row-reverse;
}
.msg-avatar {
  font-size: 20px;
  flex-shrink: 0;
}
.msg-content {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--el-fill-color);
  white-space: pre-wrap;
  font-size: 14px;
}
.chat-msg.user .msg-content {
  background: var(--el-color-primary-light-9);
}
.chat-msg.assistant .msg-content {
  background: var(--el-fill-color-light);
}
.typing {
  animation: blink 1s infinite;
}
@keyframes blink {
  50% { opacity: 0.5; }
}
.chat-input {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
/* 笔记 */
.notes-layout {
  display: flex;
  gap: 16px;
  height: calc(100vh - 260px);
}
.notes-list {
  width: 200px;
  min-width: 200px;
  overflow-y: auto;
  border-right: 1px solid var(--el-border-color-light);
  padding-right: 12px;
}
.note-item {
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 4px;
}
.note-item:hover {
  background: var(--el-fill-color);
}
.note-item.active {
  background: var(--el-color-primary-light-9);
}
.note-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note-date {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.notes-editor {
  flex: 1;
  min-width: 0;
}
.notes-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
}
/* 图谱 */
.graph-container {
  height: calc(100vh - 260px);
}
.graph-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 标签管理 */
.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  padding: 8px;
}
.tag-card {
  border: 1px solid;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.tag-name {
  font-size: 14px;
  font-weight: 500;
}
.tag-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.tag-actions {
  display: flex;
  gap: 4px;
  margin-top: 4px;
}

/* 文档标签编辑器 */
.doc-tags-editor {
  padding: 8px;
}

/* 文档内容预览 */
.doc-content-preview {
  max-height: 400px;
  overflow-y: auto;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 12px;
}
.doc-content-preview pre {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: inherit;
}

/* 聊天增强 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 知识库面板增强 */
.kb-item {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}
.kb-item:hover {
  background: var(--el-fill-color);
}
.kb-item.active {
  background: var(--el-color-primary-light-9);
}

/* 批量上传 */
:deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
}


</style>
