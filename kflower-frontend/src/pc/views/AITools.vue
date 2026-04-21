<template>
  <div class="ai-tools-page">
    <div class="page-header">
      <h2>🛠️ AI工具集</h2>
      <p class="subtitle">为智能体提供丰富的能力扩展，包括数据查询、API调用、文件处理、代码执行等</p>
    </div>

    <div class="tools-filter">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索工具..."
        prefix-icon="Search"
        style="width:300px"
        clearable
      />
      <div class="filter-actions">
        <el-button-group>
          <el-button :type="activeCategory === 'all' ? 'primary' : ''" @click="setCategory('all')">全部</el-button>
          <el-button :type="activeCategory === 'data' ? 'primary' : ''" @click="setCategory('data')">数据操作</el-button>
          <el-button :type="activeCategory === 'api' ? 'primary' : ''" @click="setCategory('api')">API调用</el-button>
          <el-button :type="activeCategory === 'file' ? 'primary' : ''" @click="setCategory('file')">文件处理</el-button>
          <el-button :type="activeCategory === 'code' ? 'primary' : ''" @click="setCategory('code')">代码执行</el-button>
          <el-button :type="activeCategory === 'other' ? 'primary' : ''" @click="setCategory('other')">其他</el-button>
        </el-button-group>
      </div>
    </div>

    <el-row :gutter="20" class="tools-grid">
      <el-col
        v-for="tool in filteredTools"
        :key="tool.id"
        :span="6"
        style="margin-bottom:20px"
      >
        <el-card class="tool-card" :class="{ disabled: !tool.enabled }">
          <template #header>
            <div class="tool-header">
              <div class="tool-icon">
                <el-icon :size="24" :color="tool.enabled ? tool.color : '#909399'">
                  <component :is="tool.icon" />
                </el-icon>
              </div>
              <div class="tool-title">
                <h4>{{ tool.name }}</h4>
                <el-tag size="small" :type="tool.categoryTag">{{ tool.category }}</el-tag>
              </div>
              <div class="tool-actions">
                <el-switch v-model="tool.enabled" size="small" @change="toggleTool(tool)" />
              </div>
            </div>
          </template>
          
          <div class="tool-description">
            {{ tool.description }}
          </div>
          
          <div class="tool-meta">
            <div class="meta-item">
              <el-icon><Clock /></el-icon>
              <span>版本 {{ tool.version }}</span>
            </div>
            <div class="meta-item">
              <el-icon><User /></el-icon>
              <span>{{ tool.usageCount }} 次使用</span>
            </div>
          </div>
          
          <div class="tool-footer">
            <el-button type="primary" size="small" @click="testTool(tool)" :disabled="!tool.enabled">测试</el-button>
            <el-button type="info" size="small" @click="editTool(tool)">配置</el-button>
            <el-button type="text" size="small" @click="viewDocs(tool)">文档</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="tool-registration" style="margin-top:24px">
      <template #header>
        <div class="card-header">
          <span>➕ 工具注册</span>
        </div>
      </template>
      
      <el-form :model="newTool" label-width="100px" :inline="true">
        <el-form-item label="工具名称" required>
          <el-input v-model="newTool.name" placeholder="输入工具名称" style="width:200px" />
        </el-form-item>
        <el-form-item label="工具类型" required>
          <el-select v-model="newTool.category" placeholder="选择类型" style="width:150px">
            <el-option label="数据操作" value="data" />
            <el-option label="文件处理" value="file" />
            <el-option label="API调用" value="api" />
            <el-option label="代码执行" value="code" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具描述" required>
          <el-input v-model="newTool.description" placeholder="工具功能描述" style="width:300px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="registerTool">注册新工具</el-button>
        </el-form-item>
      </el-form>
      
      <div class="registration-hint">
        <el-alert title="工具注册说明" type="info" :closable="false" show-icon>
          <p>1. 工具需要实现标准的接口规范</p>
          <p>2. 支持Python函数、HTTP API、命令行等多种形式</p>
          <p>3. 注册后需编写工具描述文档和参数说明</p>
        </el-alert>
      </div>
    </el-card>

    <!-- 工具测试对话框 -->
    <el-dialog
      v-model="toolDialogVisible"
      :title="`🛠️ ${currentTool?.name || '工具测试'}`"
      width="680px"
      :close-on-click-modal="false"
    >
      <!-- 工具基本信息 -->
      <div v-if="currentTool" class="tool-info-bar">
        <el-tag :type="getCategoryTag(currentTool.category)">{{ currentTool.categoryLabel }}</el-tag>
        <span class="tool-desc-text">{{ currentTool.description }}</span>
      </div>

      <!-- 文档转换工具 -->
      <div v-if="currentTool?.name === 'convert_document'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="上传文件" required>
            <el-upload
              ref="convertUploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".doc,.docx,.xls,.xlsx,.ppt,.pptx,.pdf,.odt,.ods,.odp"
              :on-change="handleConvertFileChange"
              :file-list="convertFileList"
              style="width:100%"
            >
              <template #trigger>
                <el-button type="primary">选择文件</el-button>
              </template>
              <template #tip>
                <div class="el-upload__tip">支持 doc/docx/xls/xlsx/ppt/pptx/pdf/odt/ods/odp</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="目标格式" required>
            <el-select v-model="convertForm.targetFormat" placeholder="选择目标格式" style="width:200px">
              <el-option label="docx" value="docx" />
              <el-option label="xlsx" value="xlsx" />
              <el-option label="pptx" value="pptx" />
              <el-option label="pdf" value="pdf" />
              <el-option label="json" value="json" />
            </el-select>
            <span class="format-hint">doc→docx、xls→xlsx、ppt→pptx、任意→pdf</span>
          </el-form-item>
        </el-form>

        <!-- 转换结果预览 -->
        <div v-if="convertResult" class="result-box">
          <el-alert
            :title="convertResult.success ? '✅ 转换成功' : '❌ 转换失败'"
            :type="convertResult.success ? 'success' : 'error'"
            :description="convertResult.message || convertResult.error"
            show-icon
            :closable="false"
          />
          <div v-if="convertResult.success && convertResult.data" class="json-preview">
            <div class="preview-label">转换信息：</div>
            <pre>{{ JSON.stringify(convertResult.data, null, 2) }}</pre>
          </div>
          <el-button v-if="convertResult.success" type="primary" plain size="small" @click="downloadResult">
            📥 下载转换结果
          </el-button>
        </div>
      </div>

      <!-- Excel/CSV 提取 JSON 工具 -->
      <div v-else-if="currentTool?.name === 'extract_excel_json'" class="tool-panel">
        <el-form label-width="130px">
          <el-form-item label="上传 Excel/CSV" required>
            <el-upload
              ref="extractUploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls,.csv,.ods"
              :on-change="handleExtractFileChange"
              :file-list="extractFileList"
              style="width:100%"
            >
              <template #trigger>
                <el-button type="primary">选择文件</el-button>
              </template>
              <template #tip>
                <div class="el-upload__tip">支持 xlsx / xls / csv / ods 格式</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="工作表名称">
            <el-input v-model="extractForm.sheetName" placeholder="留空默认取第一个工作表" style="width:200px" clearable />
          </el-form-item>
          <el-form-item label="表头所在行">
            <el-input-number v-model="extractForm.headerRow" :min="0" :max="50" style="width:120px" />
            <span class="format-hint">0 表示无表头，按列名 A/B/C…</span>
          </el-form-item>
          <el-form-item label="最大行数">
            <el-input-number v-model="extractForm.maxRows" :min="1" :max="10000" :step="100" style="width:120px" />
          </el-form-item>
        </el-form>

        <!-- JSON 预览 -->
        <div v-if="extractResult" class="result-box">
          <el-alert
            v-if="extractResult.success !== false"
            title="✅ 提取成功"
            type="success"
            :description="`共 ${extractResult.data?.row_count || 0} 行，` +
              `${(extractResult.data?.fields || []).length} 个字段`"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 提取失败"
            :type="extractResult.success === false ? 'error' : 'info'"
            :description="extractResult.message || extractResult.error"
            show-icon
            :closable="false"
          />
          <div v-if="extractResult.data?.sample_rows?.length" class="json-preview">
            <div class="preview-label">字段列表：{{ (extractResult.data.fields || []).join(', ') }}</div>
            <pre>{{ JSON.stringify(extractResult.data.sample_rows.slice(0, 5), null, 2) }}</pre>
          </div>
          <div class="result-actions">
            <el-button type="primary" plain size="small" @click="copyJson">
              📋 复制 JSON
            </el-button>
            <el-button type="info" plain size="small" @click="downloadJson">
              📥 导出 JSON
            </el-button>
          </div>
        </div>
      </div>

      <!-- 自动转换工具 -->
      <div v-else-if="currentTool?.name === 'auto_convert_upload'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="上传旧格式文档" required>
            <el-upload
              ref="autoConvertUploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".doc,.xls,.ppt,.odt,.ods,.odp"
              :on-change="handleAutoConvertFileChange"
              :file-list="autoConvertFileList"
              style="width:100%"
            >
              <template #trigger>
                <el-button type="primary">选择文件</el-button>
              </template>
              <template #tip>
                <div class="el-upload__tip">自动将旧格式 doc/xls/ppt 转为 docx/xlsx/pptx</div>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>

        <div v-if="autoConvertResult" class="result-box">
          <el-alert
            v-if="autoConvertResult.converted !== false"
            :title="autoConvertResult.converted ? '✅ 转换成功' : 'ℹ️ 无需转换'"
            :type="autoConvertResult.converted ? 'success' : 'info'"
            :description="autoConvertResult.message || (autoConvertResult.converted ? '已自动转换为新格式' : '文件已是新格式，无需转换')"
            show-icon
            :closable="false"
          />
          <el-button v-if="autoConvertResult.converted || autoConvertResult.downloadUrl" type="primary" plain size="small" @click="downloadAutoConvertResult">
            📥 下载结果
          </el-button>
        </div>
      </div>

      <!-- 执行工作流工具 -->
      <div v-else-if="currentTool?.name === 'execute_workflow'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="选择工作流" required>
            <el-select
              v-model="executeWorkflowForm.workflowId"
              placeholder="请选择工作流"
              filterable
              style="width:100%"
              @change="onWorkflowSelected"
            >
              <el-option
                v-for="wf in workflowList"
                :key="wf.id"
                :label="wf.name"
                :value="wf.id"
              >
                <span>{{ wf.name }}</span>
                <span class="wf-desc">{{ wf.description }}</span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="实例标题" required>
            <el-input v-model="executeWorkflowForm.title" placeholder="输入此次执行的标题" clearable />
          </el-form-item>
          <el-form-item label="表单数据">
            <el-input
              v-model="executeWorkflowForm.dataJson"
              type="textarea"
              :rows="4"
              placeholder='JSON 格式，如 {"字段名": "值"}'
              style="font-family:monospace"
            />
          </el-form-item>
        </el-form>

        <div v-if="workflowExecuteResult" class="result-box">
          <el-alert
            :title="workflowExecuteResult.success !== false ? '✅ 工作流已启动' : '❌ 启动失败'"
            :type="workflowExecuteResult.success !== false ? 'success' : 'error'"
            :description="workflowExecuteResult.message || workflowExecuteResult.error"
            show-icon
            :closable="false"
          />
          <div v-if="workflowExecuteResult.data" class="result-detail">
            <el-tag size="small">实例ID: {{ workflowExecuteResult.data.instance_id }}</el-tag>
            <el-tag size="small" type="info">状态: {{ workflowExecuteResult.data.status || 'running' }}</el-tag>
          </div>
        </div>
      </div>

      <!-- 创建工作流工具 -->
      <div v-else-if="currentTool?.name === 'create_workflow'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="工作流名称" required>
            <el-input v-model="createWorkflowForm.name" placeholder="输入工作流名称" clearable />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="createWorkflowForm.description" placeholder="简要描述工作流功能" clearable />
          </el-form-item>
          <el-form-item label="流程类型">
            <el-select v-model="createWorkflowForm.flowType" style="width:200px">
              <el-option label="审批流程" value="approval" />
              <el-option label="数据收集" value="data_collection" />
              <el-option label="通知流程" value="notification" />
              <el-option label="自定义" value="custom" />
            </el-select>
          </el-form-item>
        </el-form>

        <div v-if="workflowCreateResult" class="result-box">
          <el-alert
            v-if="workflowCreateResult.id"
            title="✅ 工作流创建成功"
            type="success"
            :description="`工作流「${workflowCreateResult.name}」已创建，ID: ${workflowCreateResult.id}`"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 创建失败"
            :description="workflowCreateResult.message || workflowCreateResult.error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <!-- 模板列表面板 -->
      <div v-else-if="currentTool?.name === 'list_templates'" class="tool-panel">
        <div class="tool-panel-toolbar">
          <el-button size="small" @click="loadTemplateList" :loading="templateListLoading">
            🔄 刷新列表
          </el-button>
          <span class="tool-panel-hint">已注册到系统的业务模板</span>
        </div>

        <el-table
          v-if="templateList.length"
          :data="templateList"
          size="small"
          max-height="320"
          style="margin-top:12px"
        >
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="模板名称" min-width="140" />
          <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="is_published" label="状态" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_published ? 'success' : 'info'">
                {{ row.is_published ? '已发布' : '草稿' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else-if="!templateListLoading" description="暂无模板" />
        <div v-if="templateListLoading" class="loading-mask">
          <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        </div>
      </div>

      <!-- 创建模板工具 -->
      <div v-else-if="currentTool?.name === 'create_template'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="模板名称" required>
            <el-input v-model="createTemplateForm.name" placeholder="输入模板名称" clearable />
          </el-form-item>
          <el-form-item label="模板描述">
            <el-input v-model="createTemplateForm.description" placeholder="简要描述模板用途" clearable />
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="createTemplateForm.category" style="width:200px">
              <el-option label="通用" value="general" />
              <el-option label="人事" value="hr" />
              <el-option label="财务" value="finance" />
              <el-option label="行政" value="admin" />
              <el-option label="业务" value="business" />
            </el-select>
          </el-form-item>
        </el-form>

        <div v-if="templateCreateResult" class="result-box">
          <el-alert
            v-if="templateCreateResult.id"
            title="✅ 模板创建成功"
            type="success"
            :description="`模板「${templateCreateResult.name}」已创建`"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 创建失败"
            :description="templateCreateResult.message || templateCreateResult.error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <!-- 数据查询工具 -->
      <div v-else-if="currentTool?.name === 'query_data'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="自然语言查询" required>
            <el-input
              v-model="queryDataForm.query"
              type="textarea"
              :rows="3"
              placeholder="用自然语言描述你想查询的数据，如：查询所有北京部门的客户"
              clearable
            />
          </el-form-item>
        </el-form>

        <div v-if="queryDataResult" class="result-box">
          <el-alert
            v-if="queryDataResult.success !== false"
            :title="`✅ 查询成功，返回 ${queryDataResult.data?.length || 0} 条记录`"
            type="success"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 查询失败"
            :description="queryDataResult.message || queryDataResult.error"
            type="error"
            show-icon
            :closable="false"
          />
          <div v-if="queryDataResult.data?.length" class="json-preview">
            <pre>{{ JSON.stringify(queryDataResult.data.slice(0, 10), null, 2) }}</pre>
          </div>
        </div>
      </div>

      <!-- 发送通知工具 -->
      <div v-else-if="currentTool?.name === 'send_notification'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="通知渠道">
            <el-radio-group v-model="notifyForm.channel">
              <el-radio label="system">📢 系统通知</el-radio>
              <el-radio label="email">📧 邮件</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="接收人">
            <el-select
              v-model="notifyForm.userId"
              placeholder="选择用户（留空发给所有人）"
              clearable
              filterable
              style="width:100%"
            >
              <el-option
                v-for="u in userList"
                :key="u.id"
                :label="u.full_name || u.username"
                :value="u.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="通知内容" required>
            <el-input
              v-model="notifyForm.message"
              type="textarea"
              :rows="4"
              placeholder="输入要发送的通知内容..."
            />
          </el-form-item>
        </el-form>

        <div v-if="notifyResult" class="result-box">
          <el-alert
            v-if="notifyResult.success !== false"
            title="✅ 通知已发送"
            type="success"
            :description="notifyResult.message || '通知发送成功'"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 发送失败"
            :description="notifyResult.message || notifyResult.error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <!-- 文件上传工具 -->
      <div v-else-if="currentTool?.name === 'upload_file'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="目标知识库" required>
            <el-select
              v-model="uploadForm.kbId"
              placeholder="选择要上传到的知识库"
              filterable
              style="width:100%"
            >
              <el-option
                v-for="kb in knowledgeBaseList"
                :key="kb.id"
                :label="kb.name"
                :value="kb.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="上传文件" required>
            <el-upload
              ref="uploadFileRef"
              :auto-upload="false"
              :limit="5"
              :on-change="handleUploadFileChange"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.md"
              style="width:100%"
            >
              <template #trigger>
                <el-button type="primary">选择文件（最多5个）</el-button>
              </template>
              <template #tip>
                <div class="el-upload__tip">支持 PDF/Word/Excel/TXT/CSV/MD，单个不超过 50MB</div>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>

        <div v-if="uploadResult" class="result-box">
          <el-alert
            v-if="uploadResult.success !== false"
            :title="`✅ 上传成功 (${uploadResult.data?.length || 0} 个文件)`"
            type="success"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 上传失败"
            :description="uploadResult.message || uploadResult.error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <!-- 统计面板 -->
      <div v-else-if="currentTool?.name === 'get_statistics'" class="tool-panel">
        <el-form label-width="120px">
          <el-form-item label="统计指标" required>
            <el-select v-model="statsForm.metric" style="width:100%">
              <el-option label="近7天工作流实例数" value="workflow_count" />
              <el-option label="近7天活跃用户数" value="user_activity" />
              <el-option label="当前待处理任务数" value="pending_tasks" />
              <el-option label="知识库文档总数" value="doc_count" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-select v-model="statsForm.timeRange" style="width:160px">
              <el-option label="今天" value="today" />
              <el-option label="近7天" value="7days" />
              <el-option label="近30天" value="30days" />
            </el-select>
          </el-form-item>
        </el-form>

        <div v-if="statsResult" class="result-box">
          <el-alert
            v-if="statsResult.value !== undefined"
            :title="`📊 ${currentTool?.description} = ${statsResult.value}`"
            type="success"
            show-icon
            :closable="false"
          />
          <el-alert
            v-else
            title="❌ 获取失败"
            :description="statsResult.message || statsResult.error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <!-- 文件下载工具（引导说明） -->
      <div v-else-if="currentTool?.name === 'download_file'" class="tool-panel">
        <el-alert
          title="📥 文件下载工具"
          description="该工具用于下载系统中的文件资源。请在知识库或模板页面中右键点击文件进行下载，或联系管理员获取文件链接。"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="tool-guide">
          <p class="guide-title">使用方法：</p>
          <ul class="guide-list">
            <li>在「知识库」页面，找到文档后点击下载按钮</li>
            <li>在「模板管理」页面，导出模板数据</li>
            <li>在「文档转换」工具中，转换完成后直接下载</li>
          </ul>
        </div>
      </div>

      <!-- 通用工具参数面板（其他工具） -->
      <div v-else-if="currentTool" class="tool-panel">
        <el-alert
          title="工具参数配置"
          type="info"
          :description="`该工具需要配置参数后执行。${currentTool.description}`"
          :closable="false"
          show-icon
          style="margin-bottom:16px"
        />
        <div v-if="currentTool.parameters?.length" class="params-form">
          <el-form label-width="130px">
            <el-form-item
              v-for="param in currentTool.parameters"
              :key="param.name"
              :label="param.name"
              :required="param.required"
            >
              <el-input
                v-if="param.type === 'string'"
                v-model="genericParams[param.name]"
                :placeholder="`输入 ${param.name}`"
                style="width:300px"
              />
              <el-input-number
                v-else-if="param.type === 'integer'"
                v-model="genericParams[param.name]"
                style="width:200px"
              />
              <el-switch
                v-else-if="param.type === 'boolean'"
                v-model="genericParams[param.name]"
              />
              <span v-else class="param-hint">类型: {{ param.type }}</span>
            </el-form-item>
          </el-form>
        </div>
        <div v-else class="no-params-hint">该工具无需额外参数</div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="toolDialogVisible = false">关闭</el-button>
          <!-- 文档转换类 -->
          <el-button
            v-if="currentTool?.name === 'convert_document'"
            type="primary"
            :loading="toolRunning"
            :disabled="!convertFile"
            @click="executeConvert"
          >{{ toolRunning ? '转换中…' : '执行转换' }}</el-button>
          <el-button
            v-else-if="currentTool?.name === 'extract_excel_json'"
            type="primary"
            :loading="toolRunning"
            :disabled="!extractFile"
            @click="executeExtractJson"
          >{{ toolRunning ? '提取中…' : '提取 JSON' }}</el-button>
          <el-button
            v-else-if="currentTool?.name === 'auto_convert_upload'"
            type="primary"
            :loading="toolRunning"
            :disabled="!autoConvertFile"
            @click="executeAutoConvert"
          >{{ toolRunning ? '处理中…' : '自动转换' }}</el-button>
          <!-- 执行工作流 -->
          <el-button
            v-else-if="currentTool?.name === 'execute_workflow'"
            type="primary"
            :loading="toolRunning"
            :disabled="!executeWorkflowForm.workflowId || !executeWorkflowForm.title"
            @click="executeWorkflowTool"
          >{{ toolRunning ? '启动中…' : '🚀 启动工作流' }}</el-button>
          <!-- 创建工作流 -->
          <el-button
            v-else-if="currentTool?.name === 'create_workflow'"
            type="primary"
            :loading="toolRunning"
            :disabled="!createWorkflowForm.name"
            @click="executeCreateWorkflow"
          >{{ toolRunning ? '创建中…' : '✅ 创建工作流' }}</el-button>
          <!-- 列表/创建模板 -->
          <el-button
            v-else-if="currentTool?.name === 'create_template'"
            type="primary"
            :loading="toolRunning"
            :disabled="!createTemplateForm.name"
            @click="executeCreateTemplate"
          >{{ toolRunning ? '创建中…' : '✅ 创建模板' }}</el-button>
          <!-- 数据查询 -->
          <el-button
            v-else-if="currentTool?.name === 'query_data'"
            type="primary"
            :loading="toolRunning"
            :disabled="!queryDataForm.query"
            @click="executeQueryData"
          >{{ toolRunning ? '查询中…' : '🔍 执行查询' }}</el-button>
          <!-- 发送通知 -->
          <el-button
            v-else-if="currentTool?.name === 'send_notification'"
            type="primary"
            :loading="toolRunning"
            :disabled="!notifyForm.message"
            @click="executeSendNotification"
          >{{ toolRunning ? '发送中…' : '📤 发送通知' }}</el-button>
          <!-- 文件上传 -->
          <el-button
            v-else-if="currentTool?.name === 'upload_file'"
            type="primary"
            :loading="toolRunning"
            :disabled="!uploadForm.kbId || !uploadFile"
            @click="executeUploadFile"
          >{{ toolRunning ? '上传中…' : '⬆️ 上传文件' }}</el-button>
          <!-- 统计 -->
          <el-button
            v-else-if="currentTool?.name === 'get_statistics'"
            type="primary"
            :loading="toolRunning"
            :disabled="!statsForm.metric"
            @click="executeGetStats"
          >{{ toolRunning ? '获取中…' : '📊 获取统计' }}</el-button>
          <!-- 通用 -->
          <el-button
            v-else
            type="primary"
            :loading="toolRunning"
            @click="executeGenericTool"
          >{{ toolRunning ? '执行中…' : '执行' }}</el-button>
        </div>
      </template>
    </el-dialog>

    <el-card class="development-info" style="margin-top:24px">
      <template #header>
        <div class="card-header">
          <span>🚀 开发进展</span>
        </div>
      </template>
      <div class="progress-section">
        <div class="progress-item">
          <div class="progress-label">工具框架基础</div>
          <el-progress :percentage="100" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具注册与管理</div>
          <el-progress :percentage="85" status="success" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具描述语言</div>
          <el-progress :percentage="70" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具自动发现</div>
          <el-progress :percentage="50" status="warning" :stroke-width="12" />
        </div>
        <div class="progress-item">
          <div class="progress-label">工具市场</div>
          <el-progress :percentage="30" status="warning" :stroke-width="12" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Clock, User, DataBoard, Connection, Document, VideoPlay, Tools, Setting, ChatDotRound, Collection, Upload, Download, Edit, Delete, Loading } from '@element-plus/icons-vue'
import { aiAPI, docConverterAPI, workflowAPI, templateAPI, analyticsAPI, knowledgeAPI, notificationAPI } from '@/common/api/index'

const searchKeyword = ref('')
const activeCategory = ref('all')

const tools = ref<any[]>([])
const newTool = ref({
  name: '',
  category: 'data',
  description: ''
})

// ─── 工具对话框状态 ───────────────────────────────
const toolDialogVisible = ref(false)
const currentTool = ref<any>(null)
const toolRunning = ref(false)

// 文档转换
const convertUploadRef = ref()
const convertFile = ref<File | null>(null)
const convertFileList = ref<any[]>([])
const convertForm = ref({ targetFormat: 'docx' })
const convertResult = ref<any>(null)
let convertDownloadBlob: Blob | null = null

// Excel 提取 JSON
const extractUploadRef = ref()
const extractFile = ref<File | null>(null)
const extractFileList = ref<any[]>([])
const extractForm = ref({ sheetName: '', headerRow: 0, maxRows: 2000 })
const extractResult = ref<any>(null)

// 自动转换
const autoConvertUploadRef = ref()
const autoConvertFile = ref<File | null>(null)
const autoConvertFileList = ref<any[]>([])
const autoConvertResult = ref<any>(null)
let autoConvertBlob: Blob | null = null

// 通用参数
const genericParams = ref<Record<string, any>>({})

// ─── 执行工作流 ────────────────────────────────
const workflowList = ref<any[]>([])
const executeWorkflowForm = ref({ workflowId: null as number|null, title: '', dataJson: '{}' })
const workflowExecuteResult = ref<any>(null)

// ─── 创建工作流 ────────────────────────────────
const createWorkflowForm = ref({ name: '', description: '', flowType: 'approval' })
const workflowCreateResult = ref<any>(null)

// ─── 模板列表 ────────────────────────────────
const templateList = ref<any[]>([])
const templateListLoading = ref(false)

// ─── 创建模板 ────────────────────────────────
const createTemplateForm = ref({ name: '', description: '', category: 'general' })
const templateCreateResult = ref<any>(null)

// ─── 数据查询 ────────────────────────────────
const queryDataForm = ref({ query: '' })
const queryDataResult = ref<any>(null)

// ─── 发送通知 ────────────────────────────────
const userList = ref<any[]>([])
const notifyForm = ref({ userId: null as number|null, message: '', channel: 'system' })
const notifyResult = ref<any>(null)

// ─── 文件上传 ────────────────────────────────
const knowledgeBaseList = ref<any[]>([])
const uploadFileRef = ref()
const uploadFile = ref<File[]>([])
const uploadForm = ref({ kbId: null as number|null })
const uploadResult = ref<any>(null)

// ─── 统计 ────────────────────────────────
const statsForm = ref({ metric: 'workflow_count', timeRange: '7days' })
const statsResult = ref<any>(null)

// ─── 工具执行函数 ────────────────────────────────
function testTool(tool: any) {
  currentTool.value = tool
  toolRunning.value = false

  // 重置所有工具状态
  convertResult.value = null; convertFile.value = null; convertFileList.value = []
  extractResult.value = null; extractFile.value = null; extractFileList.value = []
  autoConvertResult.value = null; autoConvertFile.value = null; autoConvertFileList.value = []
  workflowExecuteResult.value = null; workflowCreateResult.value = null
  templateList.value = []; templateCreateResult.value = null
  queryDataResult.value = null; notifyResult.value = null
  uploadResult.value = null; uploadFile.value = []
  statsResult.value = null
  genericParams.value = {}

  // 根据工具类型预加载数据
  if (tool.name === 'execute_workflow' || tool.name === 'create_workflow') {
    loadWorkflowList()
  }
  if (tool.name === 'list_templates') {
    loadTemplateList()
  }
  if (tool.name === 'send_notification') {
    loadUserList()
  }
  if (tool.name === 'upload_file') {
    loadKnowledgeBases()
  }

  // 预填通用参数默认值
  if (tool.parameters?.length) {
    tool.parameters.forEach((p: any) => {
      if (p.type === 'boolean') genericParams.value[p.name] = false
      else if (p.type === 'integer') genericParams.value[p.name] = 0
      else genericParams.value[p.name] = ''
    })
  }

  toolDialogVisible.value = true
}

async function executeConvert() {
  if (!convertFile.value) {
    ElMessage.warning('请先选择要转换的文件')
    return
  }
  toolRunning.value = true
  convertResult.value = null
  convertDownloadBlob = null
  try {
    const res = await docConverterAPI.convert(convertFile.value, convertForm.value.targetFormat)
    // 如果返回的是 blob（文件下载），需要特殊处理
    if (res instanceof Blob) {
      convertDownloadBlob = res
      const ext = convertForm.value.targetFormat
      const origName = convertFile.value.name.replace(/\.[^.]+$/, '')
      convertResult.value = {
        success: true,
        message: `文件已转换完成，请点击「下载转换结果」保存 ${origName}.${ext}`,
        data: { filename: `${origName}.${ext}`, format: ext }
      }
    } else if (res.success !== false) {
      convertResult.value = res
    } else {
      convertResult.value = res
      ElMessage.error(res.message || res.error || '转换失败')
    }
  } catch (err: any) {
    convertResult.value = { success: false, error: err?.message || '网络错误' }
    ElMessage.error('转换请求失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

function downloadResult() {
  if (!convertDownloadBlob || !convertFile.value) return
  const ext = convertForm.value.targetFormat
  const origName = convertFile.value.name.replace(/\.[^.]+$/, '')
  const url = URL.createObjectURL(convertDownloadBlob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${origName}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}

function handleConvertFileChange(file: any) {
  convertFile.value = file.raw as File
}

async function executeExtractJson() {
  if (!extractFile.value) {
    ElMessage.warning('请先选择要提取的 Excel/CSV 文件')
    return
  }
  toolRunning.value = true
  extractResult.value = null
  try {
    const res = await docConverterAPI.extractJson(
      extractFile.value,
      extractForm.value.headerRow,
      extractForm.value.maxRows
    )
    extractResult.value = res
    if (res.success !== false) {
      ElMessage.success(`成功提取 ${res.data?.row_count || 0} 行数据`)
    } else {
      ElMessage.error(res.message || res.error || '提取失败')
    }
  } catch (err: any) {
    extractResult.value = { success: false, error: err?.message || '网络错误' }
    ElMessage.error('提取请求失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

function handleExtractFileChange(file: any) {
  extractFile.value = file.raw as File
}

function copyJson() {
  if (!extractResult.value?.data) return
  const text = JSON.stringify(extractResult.value.data.sample_rows || extractResult.value.data, null, 2)
  navigator.clipboard.writeText(text).then(() => ElMessage.success('JSON 已复制到剪贴板'))
}

function downloadJson() {
  if (!extractResult.value?.data) return
  const text = JSON.stringify(extractResult.value.data.sample_rows || extractResult.value.data, null, 2)
  const blob = new Blob([text], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = (extractFile.value?.name || 'data') + '.json'
  a.click()
  URL.revokeObjectURL(url)
}

async function executeAutoConvert() {
  if (!autoConvertFile.value) {
    ElMessage.warning('请先选择要转换的文件')
    return
  }
  toolRunning.value = true
  autoConvertResult.value = null
  autoConvertBlob = null
  try {
    const res = await docConverterAPI.autoConvert(autoConvertFile.value)
    if (res instanceof Blob) {
      autoConvertBlob = res
      autoConvertResult.value = {
        converted: true,
        downloadUrl: URL.createObjectURL(res),
        message: '文件已处理完成，点击「下载结果」保存'
      }
    } else {
      autoConvertResult.value = res
    }
  } catch (err: any) {
    autoConvertResult.value = { converted: false, message: err?.message || '处理失败' }
    ElMessage.error('处理请求失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

function downloadAutoConvertResult() {
  if (!autoConvertBlob || !autoConvertFile.value) return
  const origName = autoConvertFile.value.name.replace(/\.[^.]+$/, '')
  // 尝试从 header 推断扩展名
  const ext = origName.split('.').pop() === 'doc' ? 'docx'
    : origName.split('.').pop() === 'xls' ? 'xlsx'
    : origName.split('.').pop() === 'ppt' ? 'pptx'
    : origName.split('.').pop()
  const url = URL.createObjectURL(autoConvertBlob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${origName}_converted.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}

function handleAutoConvertFileChange(file: any) {
  autoConvertFile.value = file.raw as File
}

function executeGenericTool() {
  ElMessage.info('该工具正在开发中，请使用已实现的功能')
}

// ─── 执行工作流 ────────────────────────────────
async function loadWorkflowList() {
  try {
    const res = await workflowAPI.list({ limit: 50 })
    workflowList.value = res?.data || res || []
  } catch {
    workflowList.value = []
  }
}

function onWorkflowSelected(id: number) {
  const wf = workflowList.value.find(w => w.id === id)
  if (wf && !executeWorkflowForm.value.title) {
    executeWorkflowForm.value.title = `执行: ${wf.name}`
  }
}

async function executeWorkflowTool() {
  if (!executeWorkflowForm.value.workflowId) { ElMessage.warning('请选择工作流'); return }
  if (!executeWorkflowForm.value.title) { ElMessage.warning('请填写实例标题'); return }
  toolRunning.value = true
  workflowExecuteResult.value = null
  let data = {}
  try {
    data = JSON.parse(executeWorkflowForm.value.dataJson || '{}')
  } catch {
    ElMessage.warning('表单数据必须是合法 JSON'); toolRunning.value = false; return
  }
  try {
    const res = await workflowAPI.execute(
      executeWorkflowForm.value.workflowId,
      executeWorkflowForm.value.title,
      data
    )
    workflowExecuteResult.value = res
    if (res.success !== false) ElMessage.success('工作流已启动')
    else ElMessage.error(res.message || '启动失败')
  } catch (err: any) {
    workflowExecuteResult.value = { success: false, error: err?.message }
    ElMessage.error('启动失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 创建工作流 ────────────────────────────────
async function executeCreateWorkflow() {
  if (!createWorkflowForm.value.name) { ElMessage.warning('请填写工作流名称'); return }
  toolRunning.value = true
  workflowCreateResult.value = null
  try {
    const res = await workflowAPI.create({
      name: createWorkflowForm.value.name,
      description: createWorkflowForm.value.description,
      flow_type: createWorkflowForm.value.flowType,
      nodes: [],
      edges: [],
    })
    workflowCreateResult.value = res?.data || res
    if (res?.id || res?.data?.id) {
      ElMessage.success('工作流创建成功')
    } else {
      ElMessage.error(res?.message || '创建失败')
    }
  } catch (err: any) {
    workflowCreateResult.value = { error: err?.message }
    ElMessage.error('创建失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 模板列表 ────────────────────────────────
async function loadTemplateList() {
  templateListLoading.value = true
  try {
    const res = await templateAPI.list({ limit: 50 })
    templateList.value = res?.data || res || []
  } catch { templateList.value = [] }
  finally { templateListLoading.value = false }
}

// ─── 创建模板 ────────────────────────────────
async function executeCreateTemplate() {
  if (!createTemplateForm.value.name) { ElMessage.warning('请填写模板名称'); return }
  toolRunning.value = true
  templateCreateResult.value = null
  try {
    const res = await templateAPI.create({
      name: createTemplateForm.value.name,
      description: createTemplateForm.value.description,
      category: createTemplateForm.value.category,
      modules: [],
    })
    templateCreateResult.value = res?.data || res
    if (res?.id || res?.data?.id) ElMessage.success('模板创建成功')
    else ElMessage.error(res?.message || '创建失败')
  } catch (err: any) {
    templateCreateResult.value = { error: err?.message }
    ElMessage.error('创建失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 数据查询 ────────────────────────────────
async function executeQueryData() {
  if (!queryDataForm.value.query) { ElMessage.warning('请输入查询语句'); return }
  toolRunning.value = true
  queryDataResult.value = null
  try {
    const res = await agentAPI.query({ query: queryDataForm.value.query })
    queryDataResult.value = res
    if (res.data?.length) ElMessage.success(`查询返回 ${res.data.length} 条结果`)
    else ElMessage.warning('查询未返回任何数据')
  } catch (err: any) {
    queryDataResult.value = { success: false, error: err?.message }
    ElMessage.error('查询失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 发送通知 ────────────────────────────────
async function loadUserList() {
  try {
    const res = await notificationAPI.listUsers({ limit: 100 })
    userList.value = res?.data || res || []
  } catch { userList.value = [] }
}

async function executeSendNotification() {
  if (!notifyForm.value.message) { ElMessage.warning('请填写通知内容'); return }
  toolRunning.value = true
  notifyResult.value = null
  try {
    const res = await notificationAPI.send({
      user_id: notifyForm.value.userId || undefined,
      message: notifyForm.value.message,
      channel: notifyForm.value.channel,
    })
    notifyResult.value = res
    if (res.success !== false) ElMessage.success('通知发送成功')
    else ElMessage.error(res.message || '发送失败')
  } catch (err: any) {
    notifyResult.value = { success: false, error: err?.message }
    ElMessage.error('发送失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 文件上传 ────────────────────────────────
async function loadKnowledgeBases() {
  try {
    const res = await knowledgeAPI.listBases()
    knowledgeBaseList.value = res?.data || res || []
  } catch { knowledgeBaseList.value = [] }
}

function handleUploadFileChange(file: any, fileList: any[]) {
  uploadFile.value = fileList.map((f: any) => f.raw as File)
}

async function executeUploadFile() {
  if (!uploadForm.value.kbId) { ElMessage.warning('请选择目标知识库'); return }
  if (!uploadFile.value.length) { ElMessage.warning('请选择要上传的文件'); return }
  toolRunning.value = true
  uploadResult.value = null
  const results: any[] = []
  try {
    for (const file of uploadFile.value) {
      const res = await knowledgeAPI.upload(uploadForm.value.kbId, file)
      results.push(res?.data || res)
    }
    uploadResult.value = { success: true, data: results }
    ElMessage.success(`${results.length} 个文件上传成功`)
  } catch (err: any) {
    uploadResult.value = { success: false, error: err?.message }
    ElMessage.error('上传失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 统计 ────────────────────────────────
async function executeGetStats() {
  if (!statsForm.value.metric) { ElMessage.warning('请选择统计指标'); return }
  toolRunning.value = true
  statsResult.value = null
  try {
    // 从 analytics API 获取概览统计
    const res = await analyticsAPI.getOverview()
    const overview = res?.data || res || {}
    const metric = statsForm.value.metric
    let value = 0
    if (metric === 'workflow_count') value = overview.workflow_count || overview.workflows_total || 0
    else if (metric === 'user_activity') value = overview.user_count || overview.users_active || 0
    else if (metric === 'pending_tasks') value = overview.pending_tasks || 0
    else if (metric === 'doc_count') value = overview.document_count || overview.docs_total || 0
    statsResult.value = { value }
  } catch (err: any) {
    statsResult.value = { error: err?.message }
    ElMessage.error('获取统计失败: ' + (err?.message || ''))
  } finally {
    toolRunning.value = false
  }
}

// ─── 加载工具列表 ───────────────────────────────
async function loadTools() {
  try {
    const response = await aiAPI.getAgentEngineTools()
    if (response.success && response.data?.length) {
      tools.value = response.data.map((tool: any, index: number) => {
        const cat = mapCategory(tool.category)
        return {
          id: index + 1,
          name: tool.name,
          description: tool.description || '',
          category: cat,
          categoryLabel: getCategoryLabel(tool.category),
          categoryTag: getCategoryTag(cat),
          icon: getIconForCategory(cat),
          color: getColorForCategory(cat),
          version: 'v1.0',
          usageCount: tool.call_count || 0,
          enabled: tool.enabled !== false,
          parameters: tool.parameters || [],
        }
      })
    } else {
      loadMockTools()
    }
  } catch (error) {
    console.error('加载工具列表失败:', error)
    ElMessage.error('加载工具列表失败，使用默认工具集')
    loadMockTools()
  }
}

function loadMockTools() {
  const mock = [
    { name: 'convert_document', description: '文档格式转换：doc→docx、xls→xlsx、ppt→pptx、任意→pdf', category: '文件处理', parameters: [] },
    { name: 'extract_excel_json', description: '将 Excel/CSV 文件提取为 JSON 数据，用于模板导入和数据分析', category: '数据操作', parameters: [] },
    { name: 'auto_convert_upload', description: '自动将旧格式文档（doc/xls/ppt）转换为新格式（docx/xlsx/pptx），供上传使用', category: '文件处理', parameters: [] },
    { name: 'create_template', description: '创建新的业务模板', category: '数据操作', parameters: [
      { name: 'name', type: 'string', required: true },
      { name: 'description', type: 'string', required: true },
    ]},
    { name: 'list_templates', description: '列出所有模板', category: '数据操作', parameters: [] },
    { name: 'query_data', description: '查询业务数据', category: '数据操作', parameters: [
      { name: 'table', type: 'string', required: true },
    ]},
    { name: 'upload_file', description: '上传文件到服务器', category: '文件处理', parameters: [
      { name: 'folder', type: 'string', required: false },
    ]},
  ]
  tools.value = mock.map((tool: any, i: number) => {
    const cat = mapCategory(tool.category)
    return {
      id: i + 1, name: tool.name, description: tool.description,
      category: cat, categoryLabel: tool.category,
      categoryTag: getCategoryTag(cat), icon: getIconForCategory(cat),
      color: getColorForCategory(cat), version: 'v1.0', usageCount: Math.floor(Math.random() * 200),
      enabled: true, parameters: tool.parameters || [],
    }
  })
}

function mapCategory(backendCategory: string): string {
  const mapping: Record<string, string> = {
    '网络': 'api', '工具': 'other', '生活': 'api', '语言': 'other',
    '数据操作': 'data', '文件处理': 'file', '可视化': 'data',
    'api': 'api', 'data': 'data', 'file': 'file', 'code': 'code',
  }
  return mapping[backendCategory] || 'other'
}

function getCategoryLabel(backendCategory: string): string {
  const map: Record<string, string> = {
    'api': 'API调用', 'data': '数据操作', 'file': '文件处理',
    'code': '代码执行', 'other': '其他',
    '网络': 'API调用', '工具': '其他', '生活': 'API调用', '语言': '其他',
    '数据操作': '数据操作', '文件处理': '文件处理', '可视化': '数据操作',
  }
  return map[backendCategory] || backendCategory || '其他'
}

function getIconForCategory(category: string) {
  const iconMap: Record<string, any> = {
    'data': DataBoard, 'api': Connection, 'file': Document,
    'code': VideoPlay, 'other': Tools,
  }
  return iconMap[category] || Tools
}

function getColorForCategory(category: string) {
  const colorMap: Record<string, string> = {
    'data': '#409EFF', 'api': '#67C23A', 'file': '#E6A23C',
    'code': '#F56C6C', 'other': '#909399',
  }
  return colorMap[category] || '#909399'
}

const filteredTools = computed(() => {
  let result = tools.value
  if (activeCategory.value !== 'all') {
    result = result.filter(tool => tool.category === activeCategory.value)
  }
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(tool =>
      tool.name.toLowerCase().includes(keyword) ||
      tool.description.toLowerCase().includes(keyword)
    )
  }
  return result
})

onMounted(() => { loadTools() })

function setCategory(category: string) { activeCategory.value = category }

function toggleTool(tool: any) {
  ElMessage.success(`${tool.name} ${tool.enabled ? '已启用' : '已禁用'}`)
}

function editTool(tool: any) {
  ElMessage.info(`配置工具: ${tool.name}`)
}

function viewDocs(tool: any) {
  ElMessage.info(`查看 ${tool.name} 的文档`)
}

function registerTool() {
  if (!newTool.value.name.trim() || !newTool.value.description.trim()) {
    ElMessage.warning('请填写工具名称和描述')
    return
  }
  const cat = mapCategory('其他')
  tools.value.push({
    id: tools.value.length + 1,
    name: newTool.value.name,
    category: cat,
    categoryLabel: '其他',
    categoryTag: getCategoryTag(cat),
    icon: Tools,
    color: '#909399',
    description: newTool.value.description,
    version: 'v1.0',
    usageCount: 0,
    enabled: true,
    parameters: [],
  })
  ElMessage.success(`工具 "${newTool.value.name}" 已注册`)
  newTool.value = { name: '', category: 'data', description: '' }
}

function getCategoryTag(category: string) {
  const map: any = {
    data: 'primary', api: 'success', file: 'warning', code: 'danger', other: 'info',
  }
  return map[category] || 'info'
}
</script>

<style scoped>
.ai-tools-page {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 8px 0 0;
  color: #606266;
  font-size: 14px;
}

.tools-filter {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.tools-grid {
  margin-bottom: 20px;
}

.tool-card {
  height: 100%;
  transition: all 0.3s;
}

.tool-card.disabled {
  opacity: 0.7;
  background: #fafafa;
}

.tool-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tool-icon {
  flex-shrink: 0;
}

.tool-title {
  flex: 1;
}

.tool-title h4 {
  margin: 0 0 4px;
  font-size: 16px;
}

.tool-actions {
  flex-shrink: 0;
}

.tool-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 16px;
  line-height: 1.5;
}

.tool-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 12px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tool-footer {
  display: flex;
  justify-content: space-between;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.registration-hint {
  margin-top: 16px;
}

.development-info {
  border-radius: 8px;
}

.progress-section {
  padding: 8px 0;
}

.progress-item {
  margin-bottom: 20px;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-label {
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

/* ─── 工具对话框样式 ─── */
.tool-info-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.tool-desc-text {
  font-size: 14px;
  color: #606266;
}

.tool-panel {
  min-height: 200px;
}

.format-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.param-hint {
  font-size: 12px;
  color: #909399;
}

.result-box {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.json-preview {
  background: #1e1e1e;
  border-radius: 6px;
  padding: 12px;
  max-height: 260px;
  overflow: auto;
}

.preview-label {
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
}

.json-preview pre {
  margin: 0;
  font-size: 12px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.no-params-hint {
  color: #909399;
  font-size: 14px;
  text-align: center;
  padding: 32px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.params-form {
  padding: 8px 0;
}

.tool-panel-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.tool-panel-hint {
  font-size: 12px;
  color: #909399;
}

.wf-desc {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.loading-mask {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  color: #409EFF;
}

.tool-guide {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.guide-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
}

.guide-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.result-detail {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}
</style>