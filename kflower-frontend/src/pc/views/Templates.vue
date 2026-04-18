<template>
  <div class="template-page">

    <!-- 列表视图 -->
    <div v-if="viewMode === 'list'" class="list-view">
      <div class="page-header">
        <div class="header-left">
          <h2>模板设计</h2>
          <el-tag type="info">{{ templates.length }} 个模板</el-tag>
        </div>
        <div class="header-right">
          <el-input v-model="searchText" placeholder="搜索模板..." clearable style="width:240px" @input="debounceSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <!-- 视图切换按钮 -->
          <el-button-group>
            <el-button :type="listStyle === 'table' ? 'primary' : ''" @click="listStyle = 'table'" title="列表视图">
              <el-icon><List /></el-icon> 列表
            </el-button>
            <el-button :type="listStyle === 'card' ? 'primary' : ''" @click="listStyle = 'card'" title="卡片视图">
              <el-icon><Grid /></el-icon> 卡片
            </el-button>
          </el-button-group>
          <el-button @click="openJsonImport">
            <el-icon><Document /></el-icon> JSON导入
          </el-button>
          <el-button @click="showImport = true">
            <el-icon><Upload /></el-icon> 导入文件
          </el-button>
          <el-button @click="showAIHelper = true">
            <el-icon><MagicStick /></el-icon> AI 设计
          </el-button>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建模板
          </el-button>
        </div>
      </div>

      <div class="category-filter">
        <el-radio-group v-model="categoryFilter" @change="filterByCategory">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="crm">客户管理</el-radio-button>
          <el-radio-button label="order">订单管理</el-radio-button>
          <el-radio-button label="hr">人力资源</el-radio-button>
          <el-radio-button label="inventory">仓储物流</el-radio-button>
          <el-radio-button label="project">项目管理</el-radio-button>
          <el-radio-button label="finance">财务报销</el-radio-button>
          <el-radio-button label="general">通用表单</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="loading" class="loading-grid">
        <el-card v-for="i in 6" :key="i" shadow="hover"><el-skeleton :rows="3" animated /></el-card>
      </div>

      <el-empty v-else-if="filteredTemplates.length === 0" description="暂无模板">
        <el-button type="primary" @click="openCreateDialog">新建模板</el-button>
      </el-empty>

      <!-- ===== 列表（表格）视图 ===== -->
      <div v-else-if="listStyle === 'table'" class="template-table-wrapper">
        <el-table :data="filteredTemplates" stripe style="width:100%" v-loading="loading">
          <el-table-column label="模板名称" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="table-name-cell">
                <div class="table-icon" :style="{background: getCategoryColor(row.category)}">
                  <el-icon :size="16"><component :is="getCategoryIcon(row.category)" /></el-icon>
                </div>
                <div>
                  <div class="table-name-text">{{ row.name }}</div>
                  <div class="table-code-text">{{ row.code || '—' }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="发布状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
                {{ row.is_published ? '已发布' : '草稿' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建人" width="100" align="center">
            <template #default="{ row }">
              <span>{{ getCreatorName(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="共享状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.created_by === currentUserId" type="primary" size="small">私有</el-tag>
              <el-tag v-else type="warning" size="small">共享</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分类" width="120" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="getCategoryTagType(row.category)">
                {{ getCategoryLabel(row.category) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="字段数" width="80" align="center" sortable sort-by="fieldCount">
            <template #default="{ row }">
              <span class="field-count-num">{{ countFields(row) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="模板ID" width="90" align="center">
            <template #default="{ row }">
              <span class="template-id-text">#{{ row.id }}</span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="160" align="center" sortable sort-by="created_at">
            <template #default="{ row }">
              <span>{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" text @click="openDesigner(row)" title="查看/设计">
                <el-icon><SetUp /></el-icon>查看
              </el-button>
              <el-button size="small" type="warning" text @click="openEditDialog(row)" title="编辑">
                <el-icon><Edit /></el-icon>编辑
              </el-button>
              <el-button v-if="row.is_published" size="small" type="success" text @click="openFormSubmit(row)" title="填写表单">
                <el-icon><EditPen /></el-icon>填表
              </el-button>
              <el-button v-else size="small" type="success" text @click="publishTemplate(row)" title="发布">
                <el-icon><Promotion /></el-icon>发布
              </el-button>
              <el-button size="small" type="danger" text @click="deleteTemplate(row)" title="删除">
                <el-icon><Delete /></el-icon>删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- ===== 卡片视图 ===== -->
      <div v-else class="template-grid">
        <el-card v-for="t in filteredTemplates" :key="t.id" shadow="hover" class="template-card" @click="openDesigner(t)">
          <div class="card-header">
            <div class="card-icon" :style="{background: getCategoryColor(t.category)}">
              <el-icon :size="22"><component :is="getCategoryIcon(t.category)" /></el-icon>
            </div>
            <div class="card-title">
              <h4>{{ t.name }}</h4>
              <span class="card-code">{{ t.code || '无编码' }}</span>
            </div>
            <el-tag v-if="t.is_published" type="success" size="small">已发布</el-tag>
            <el-tag v-else type="info" size="small">草稿</el-tag>
            <el-dropdown trigger="click" @click.stop>
              <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu style="min-width:150px">
                  <el-dropdown-item @click.stop="openDesigner(t)"><el-icon><SetUp /></el-icon> 设计</el-dropdown-item>
                  <el-dropdown-item @click.stop="openEditDialog(t)"><el-icon><Edit /></el-icon> 编辑</el-dropdown-item>
                  <el-dropdown-item @click.stop="openDataForm(t)"><el-icon><EditPen /></el-icon> 填写数据</el-dropdown-item>
                  <el-dropdown-item @click.stop="openDataManager(t)"><el-icon><DataLine /></el-icon> 数据管理</el-dropdown-item>
                  <el-dropdown-item @click.stop="duplicateTemplate(t)"><el-icon><CopyDocument /></el-icon> 复制</el-dropdown-item>
                  <el-dropdown-item @click.stop="exportTemplate(t)"><el-icon><Download /></el-icon> 导出</el-dropdown-item>
                  <el-dropdown-item v-if="t.is_published" @click.stop="unpublishTemplate(t)"><el-icon><RefreshRight /></el-icon> 撤回发布</el-dropdown-item>
                  <el-dropdown-item v-else @click.stop="publishTemplate(t)"><el-icon><Promotion /></el-icon> 发布</el-dropdown-item>
                  <el-dropdown-item divided @click.stop="deleteTemplate(t)"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <p class="card-desc">{{ t.description || '暂无描述' }}</p>
          <div class="card-meta">
            <el-tag size="small" :type="getCategoryTagType(t.category)">{{ getCategoryLabel(t.category) }}</el-tag>
            <span class="field-count"><el-icon><List /></el-icon> {{ countFields(t) }} 字段</span>
            <span class="create-time">{{ formatDateShort(t.created_at) }}</span>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 设计器视图 -->
    <div v-else class="designer-view">
      <div class="designer-toolbar">
        <div class="toolbar-left">
          <el-button text @click="viewMode = 'list'"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
          <el-divider direction="vertical" />
          <el-input v-model="currentTemplate.name" placeholder="模板名称" style="width:200px" />
        </div>
        <div class="toolbar-center">
          <el-select v-model="currentTemplate.category" placeholder="分类" style="width:140px">
            <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-divider direction="vertical" />
          <el-switch v-model="currentTemplate.is_public" active-text="共享" inactive-text="私有" />
        </div>
        <div class="toolbar-right">
          <el-button @click="previewTemplate"><el-icon><View /></el-icon> 预览</el-button>
          <el-button @click="saveTemplate"><el-icon><Select /></el-icon> 保存</el-button>
          <el-button type="success" @click="publishTemplate" :loading="publishing"><el-icon><Promotion /></el-icon> 发布</el-button>
        </div>
      </div>

      <div class="designer-body">
        <!-- 左侧工具箱 -->
        <div class="field-toolbox">
          <el-collapse v-model="toolboxExpanded">
            <el-collapse-item title="基础控件" name="basic">
              <div class="toolbox-grid">
                <div v-for="ft in basicFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="日期时间" name="datetime">
              <div class="toolbox-grid">
                <div v-for="ft in datetimeFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="选择控件" name="select">
              <div class="toolbox-grid">
                <div v-for="ft in selectFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="高级控件" name="advanced">
              <div class="toolbox-grid">
                <div v-for="ft in advancedFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="布局控件" name="layout">
              <div class="toolbox-grid">
                <div v-for="ft in layoutFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="数据控件" name="data">
              <div class="toolbox-grid">
                <div v-for="ft in dataFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="特殊控件" name="special">
              <div class="toolbox-grid">
                <div v-for="ft in specialFields" :key="ft.type" class="toolbox-item" draggable="true" @dragstart="onDragStart($event, ft)">
                  <el-icon :size="16"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 中间画布 -->
        <div class="form-canvas" ref="canvasRef" @dragover.prevent @drop="onDrop" @click.self="selectedField = null">
          <div v-if="currentTemplate.fields.length === 0" class="canvas-empty">
            <el-icon :size="56" class="empty-icon"><SetUp /></el-icon>
            <h4>开始设计您的表单</h4>
            <p>从左侧拖拽字段到这里，或点击 AI 智能设计</p>
            <el-button type="primary" @click="showAIHelper = true">
              <el-icon><MagicStick /></el-icon> AI 智能设计
            </el-button>
          </div>
          <div v-else class="canvas-fields">
            <div v-for="(field, idx) in currentTemplate.fields" :key="field._key"
              class="canvas-field" :class="{selected: selectedField === idx}"
              draggable="true" @click.stop="selectedField = idx"
              @dragstart="onFieldDragStart($event, idx)" @dragover.prevent @drop="onFieldDrop($event, idx)">
              <div class="field-handle"><el-icon><Rank /></el-icon></div>
              <div class="field-body">
                <div class="field-header">
                  <el-tag size="small" :type="getFieldTypeStyle(field.type)">{{ getFieldTypeLabel(field.type) }}</el-tag>
                  <span class="field-label">{{ field.label || '未命名' }}</span>
                  <span v-if="field.required" class="required-mark">*</span>
                </div>
                <div class="field-preview"><input class="preview-input" :placeholder="field.placeholder" disabled /></div>
                <div class="field-meta">字段名: <code>{{ field.name }}</code></div>
              </div>
              <div class="field-actions">
                <el-button size="small" text @click.stop="copyField(idx)" title="复制"><el-icon><CopyDocument /></el-icon></el-button>
                <el-button size="small" text @click.stop="moveField(idx, -1)" :disabled="idx === 0" title="上移"><el-icon><ArrowUp /></el-icon></el-button>
                <el-button size="small" text @click.stop="moveField(idx, 1)" :disabled="idx === currentTemplate.fields.length - 1" title="下移"><el-icon><ArrowDown /></el-icon></el-button>
                <el-button size="small" text type="danger" @click.stop="removeField(idx)" title="删除"><el-icon><Close /></el-icon></el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧属性面板 -->
        <div class="property-panel">
          <template v-if="selectedField !== null && currentTemplate.fields[selectedField]">
            <div class="panel-header">
              <h4>字段属性</h4>
              <el-button text size="small" @click="selectedField = null"><el-icon><Close /></el-icon></el-button>
            </div>
            <el-scrollbar class="panel-body">
              <el-form label-position="top" size="small">

                <!-- 字段类型（可修改） -->
                <el-form-item label="字段类型">
                  <el-select
                    v-model="currentTemplate.fields[selectedField].type"
                    style="width:100%"
                    @change="onFieldTypeChange"
                  >
                    <el-option-group label="文本输入">
                      <el-option value="text" label="单行文本" />
                      <el-option value="textarea" label="多行文本" />
                      <el-option value="number" label="数字" />
                      <el-option value="password" label="密码" />
                      <el-option value="email" label="邮箱" />
                      <el-option value="phone" label="手机号" />
                      <el-option value="url" label="网址链接" />
                    </el-option-group>
                    <el-option-group label="日期时间">
                      <el-option value="date" label="日期" />
                      <el-option value="datetime" label="日期时间" />
                      <el-option value="time" label="时间" />
                      <el-option value="daterange" label="日期范围" />
                    </el-option-group>
                    <el-option-group label="选择控件">
                      <el-option value="select" label="下拉单选" />
                      <el-option value="radio" label="单选按钮" />
                      <el-option value="checkbox" label="多选框" />
                      <el-option value="switch" label="开关" />
                    </el-option-group>
                    <el-option-group label="高级控件">
                      <el-option value="rate" label="评分" />
                      <el-option value="slider" label="滑块" />
                      <el-option value="color" label="颜色" />
                      <el-option value="tags" label="标签" />
                      <el-option value="signature" label="签名" />
                      <el-option value="location" label="地理位置" />
                    </el-option-group>
                    <el-option-group label="文件上传">
                      <el-option value="file" label="文件上传" />
                      <el-option value="image" label="图片上传" />
                    </el-option-group>
                    <el-option-group label="布局元素">
                      <el-option value="divider" label="分割线" />
                      <el-option value="title" label="标题" />
                      <el-option value="description" label="说明文字" />
                    </el-option-group>
                  </el-select>
                </el-form-item>

                <el-form-item label="显示名称">
                  <el-input v-model="currentTemplate.fields[selectedField].label" />
                </el-form-item>
                <el-form-item label="字段标识">
                  <el-input v-model="currentTemplate.fields[selectedField].name">
                    <template #append><el-button @click="autoFieldName">自动</el-button></template>
                  </el-input>
                </el-form-item>
                <el-form-item
                  v-if="!['divider','title','description','switch','rate','color','signature','location'].includes(currentTemplate.fields[selectedField].type)"
                  label="占位提示"
                >
                  <el-input v-model="currentTemplate.fields[selectedField].placeholder" />
                </el-form-item>
                <el-form-item label="字段宽度">
                  <el-radio-group v-model="currentTemplate.fields[selectedField].width">
                    <el-radio label="100%">整行</el-radio>
                    <el-radio label="50%">半行</el-radio>
                    <el-radio label="33%">三分之一</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item
                  v-if="!['divider','title','description'].includes(currentTemplate.fields[selectedField].type)"
                  label="必填"
                >
                  <el-switch v-model="currentTemplate.fields[selectedField].required" />
                </el-form-item>
                <el-form-item
                  v-if="!['divider','title','description','switch'].includes(currentTemplate.fields[selectedField].type)"
                  label="只读"
                >
                  <el-switch v-model="currentTemplate.fields[selectedField].readonly" />
                </el-form-item>

                <!-- 选项设置（select/radio/checkbox） -->
                <template v-if="['select','radio','checkbox'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>选项设置</el-divider>
                  <el-form-item label="选项列表（每行一个）">
                    <el-input
                      v-model="currentTemplate.fields[selectedField].optionsText"
                      type="textarea" :rows="4"
                      placeholder="每行输入一个选项&#10;例如：&#10;选项一&#10;选项二"
                      @blur="applyOptions"
                    />
                  </el-form-item>
                  <el-form-item label="多选（select有效）" v-if="currentTemplate.fields[selectedField].type === 'select'">
                    <el-switch v-model="currentTemplate.fields[selectedField].multiple" />
                  </el-form-item>
                </template>

                <!-- 数值设置（number/slider） -->
                <template v-if="['number','slider'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>数值设置</el-divider>
                  <el-form-item label="最小值">
                    <el-input-number v-model="currentTemplate.fields[selectedField].min" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="最大值">
                    <el-input-number v-model="currentTemplate.fields[selectedField].max" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="步长" v-if="currentTemplate.fields[selectedField].type === 'number'">
                    <el-input-number v-model="currentTemplate.fields[selectedField].step" :min="0" style="width:100%" />
                  </el-form-item>
                </template>

                <!-- 文本长度限制 -->
                <template v-if="['text','textarea','password'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>长度限制</el-divider>
                  <el-form-item label="最大字符数">
                    <el-input-number v-model="currentTemplate.fields[selectedField].maxLength" :min="1" style="width:100%" placeholder="不限" />
                  </el-form-item>
                </template>

                <!-- 文件上传设置 -->
                <template v-if="['file','image'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>上传设置</el-divider>
                  <el-form-item label="最多文件数">
                    <el-input-number v-model="currentTemplate.fields[selectedField].limit" :min="1" :max="20" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="单文件大小限制(MB)">
                    <el-input-number v-model="currentTemplate.fields[selectedField].maxSize" :min="1" :max="200" style="width:100%" />
                  </el-form-item>
                </template>

              </el-form>
            </el-scrollbar>
          </template>
          <el-empty v-else description="点击字段进行配置" :image-size="80" />
        </div>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showEditDialog" :title="editingTemplate ? '编辑模板' : '新建模板'" width="500px">
      <el-form :model="editForm" :rules="editRules" label-width="90px" ref="editFormRef">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item v-if="editingTemplate" label="模板ID">
          <el-input :model-value="editingTemplate.id" disabled />
        </el-form-item>
        <el-form-item label="模板分类">
          <el-select v-model="editForm.category" style="width:100%">
            <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="editForm.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCreateOrUpdate">{{ editingTemplate ? '保存修改' : '创建并设计' }}</el-button>
      </template>
    </el-dialog>


    <!-- 导入Excel/图片弹窗 -->
    <el-dialog v-model="showImport" title="导入Excel或图片生成表单" width="900px" destroy-on-close @open="onImportDialogOpen">
      <div class="import-container">
        <el-steps :active="importStep" finish-status="success" style="margin-bottom:24px">
          <el-step title="上传文件" />
          <el-step title="预览数据" />
          <el-step title="调整字段" />
          <el-step title="创建模板" />
        </el-steps>

        <!-- 步骤1: 上传 -->
        <div v-if="importStep === 0">
          <!-- 依赖状态提示 -->
          <div v-if="importDependenciesStatus" class="import-deps-status">
            <div class="deps-title"><el-icon><InfoFilled /></el-icon> 组件状态</div>
            <div class="deps-list">
              <span class="dep-item" :class="importDependenciesStatus.excel?.available ? 'ok' : 'warn'">
                <el-icon><Document /></el-icon> Excel {{ importDependenciesStatus.excel?.available ? '✓' : '✗' }}
              </span>
              <span class="dep-item" :class="importDependenciesStatus.jieba?.available ? 'ok' : 'warn'">
                <el-icon><Connection /></el-icon> jieba {{ importDependenciesStatus.jieba?.available ? '✓' : '△' }}
              </span>
              <span class="dep-item" :class="importDependenciesStatus.ocr?.chi_sim_installed ? 'ok' : 'warn'">
                <el-icon><Picture /></el-icon> OCR {{ importDependenciesStatus.ocr?.chi_sim_installed ? '✓' : '✗' }}
                <el-tooltip v-if="!importDependenciesStatus.ocr?.chi_sim_installed" :content="importDependenciesStatus.ocr?.message || '请配置 Tesseract 和中文语言包'">
                  <el-icon><Warning /></el-icon>
                </el-tooltip>
              </span>
              <span class="dep-item" :class="importDependenciesStatus.cv2?.available ? 'ok' : 'warn'">
                <el-icon><Crop /></el-icon> cv2 {{ importDependenciesStatus.cv2?.available ? '✓' : '△' }}
              </span>
            </div>
            <div class="deps-tip">
              <template v-if="importDependenciesStatus.ocr && !importDependenciesStatus.ocr.chi_sim_installed">
                <el-tag type="warning" size="small">
                  OCR{{ importDependenciesStatus.ocr.engine_configured ? '缺少中文语言包' : '未就绪' }}：{{ importDependenciesStatus.ocr.message || '请在系统配置中设置 Tesseract 路径' }}
                </el-tag>
              </template>
              <template v-if="!importDependenciesStatus.excel?.xlrd">
                <el-tag type="info" size="small">提示：.xls 文件建议另存为 .xlsx 格式</el-tag>
              </template>
            </div>
          </div>
          <el-upload
            class="import-uploader"
            drag
            :limit="1"
            accept=".xlsx,.xls,.csv,.json,.png,.jpg,.jpeg,.bmp"
            :auto-upload="false"
            :on-change="onImportFileChange"
            ref="uploadRef"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">
              <p>拖拽文件到此处，或 <em>点击选择</em></p>
              <p class="upload-hint">支持 Excel (.xlsx/.xls/.csv) 和图片 (.png/.jpg/.jpeg)</p>
            </div>
          </el-upload>
          <div class="upload-examples">
            <span>快速示例：</span>
            <el-tag @click="loadSampleData('supplier')">供应商信息表</el-tag>
            <el-tag @click="loadSampleData('employee')">员工入职表</el-tag>
            <el-tag @click="loadSampleData('customer')">客户登记表</el-tag>
          </div>
        </div>

        <!-- 步骤2: 预览数据 -->
        <div v-if="importStep === 1">
          <el-alert :title="`已识别 ${importData.total_rows} 行 × ${importData.total_columns} 列`" type="success" show-icon />
          <div class="preview-controls">
            <div class="control-row">
              <span>表头行：</span>
              <el-select v-model="importHeaderRow" placeholder="选择表头行" style="width:200px" @change="reparseWithHeaderRow">
                <el-option v-for="(_, idx) in (importData.all_rows || importData.rows)" :key="idx" :label="`第 ${idx + 1} 行` + (idx === 0 ? '（默认）' : '')" :value="idx" />
              </el-select>
              <span v-if="importData.sheet_names && importData.sheet_names.length > 1" style="margin-left:16px">工作表：</span>
              <el-select v-if="importData.sheet_names && importData.sheet_names.length > 1" v-model="importSheetName" placeholder="选择工作表" style="width:160px" @change="reparseWithSheet">
                <el-option v-for="sn in importData.sheet_names" :key="sn" :label="sn" :value="sn" />
              </el-select>
            </div>
            <div class="control-row" style="margin-top:8px">
              <span>选择导入字段：</span>
              <el-checkbox v-model="importSelectAll" :indeterminate="importSelectIndeterminate" @change="onImportSelectAllChange">全选</el-checkbox>
            </div>
            <div class="field-checkboxes">
              <el-checkbox v-for="(h, idx) in importData.headers" :key="idx" v-model="importSelectedFields[idx]" @change="onImportFieldSelectChange">{{ h }}</el-checkbox>
            </div>
          </div>
          <div class="preview-actions">
            <el-button @click="importStep = 0">重新上传</el-button>
            <el-button type="primary" @click="goToFieldAdjust">下一步：调整字段</el-button>
          </div>
          <el-table :data="importData.rows" border size="small" max-height="300" style="margin-top:12px">
            <el-table-column v-for="(h, idx) in importData.headers" :key="idx" :prop="String(idx)" :label="h" min-width="120" show-overflow-tooltip />
          </el-table>
        </div>

        <!-- 步骤3: 调整字段 -->
        <div v-if="importStep === 2">
          <div class="field-adjust-header">
            <span>识别到 <strong>{{ importFields.length }}</strong> 个字段，可手动调整：</span>
            <el-button size="small" @click="detectFieldTypes">重新识别类型</el-button>
          </div>
          <el-table :data="importFields" border size="small" style="margin-top:12px">
            <el-table-column label="序号" width="60" type="index" />
            <el-table-column label="原始表头" prop="label" min-width="140" />
            <el-table-column label="显示名称" min-width="140">
              <template #default="{ row }">
                <el-input v-model="row.label" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="字段标识" width="140">
              <template #default="{ row }">
                <el-input v-model="row.name" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="控件类型" width="140">
              <template #default="{ row }">
                <el-select v-model="row.type" size="small" style="width:100%">
                  <el-option v-for="ft in allFieldTypes" :key="ft.type" :label="ft.label" :value="ft.type" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="必填" width="70">
              <template #default="{ row }">
                <el-switch v-model="row.required" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="宽度" width="100">
              <template #default="{ row }">
                <el-select v-model="row.width" size="small" style="width:100%">
                  <el-option label="整行" value="100%" />
                  <el-option label="半行" value="50%" />
                </el-select>
              </template>
            </el-table-column>
          </el-table>
          <div class="step-actions">
            <el-button @click="importStep = 1">上一步</el-button>
            <el-button type="primary" @click="importStep = 3">下一步：创建模板</el-button>
          </div>
        </div>

        <!-- 步骤4: 创建模板 -->
        <div v-if="importStep === 3">
          <el-form :model="importTemplateForm" label-width="90px" style="max-width:500px">
            <el-form-item label="模板名称" required>
              <el-input v-model="importTemplateForm.name" placeholder="请输入模板名称" />
            </el-form-item>
            <el-form-item label="模板分类">
              <el-select v-model="importTemplateForm.category" style="width:100%">
                <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="模板描述">
              <el-input v-model="importTemplateForm.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
          <div class="summary-info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="字段数量">{{ importFields.length }}</el-descriptions-item>
              <el-descriptions-item label="数据行数">{{ importData.total_rows }}</el-descriptions-item>
              <el-descriptions-item label="来源文件">{{ importFileName || '示例数据' }}</el-descriptions-item>
              <el-descriptions-item label="智能识别">是</el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="step-actions">
            <el-button @click="importStep = 2">上一步</el-button>
            <el-button type="primary" :loading="importLoading" @click="confirmCreateTemplate">
              <el-icon><Select /></el-icon> 创建模板并导入数据
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- AI 智能设计弹窗 -->
    <el-dialog v-model="showAIHelper" title="AI 智能设计" width="680px">
      <el-form label-width="80px" style="margin-bottom:12px">
        <el-form-item label="选择模型">
          <el-select v-model="selectedModelId" placeholder="选择AI模型" style="width:100%">
            <el-option v-for="model in aiStore.models" :key="model.modelId" :label="model.modelName || model.modelId" :value="model.modelId">
              <span>{{ model.modelName || model.modelId }}</span>
              <el-tag size="small" type="info" style="margin-left:8px">{{ model.provider }}</el-tag>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 预置提示词（只读展示，用户了解 AI 的行为约定） -->
      <el-form label-width="80px">
        <el-form-item label="系统提示">
          <el-input
            :model-value="AI_SYSTEM_PROMPT_HINT"
            type="textarea" :rows="3" readonly
            style="font-size:12px;color:#888;background:#f8f9fa;font-family:monospace"
          />
        </el-form-item>
        <el-form-item label="需求描述">
          <el-input
            v-model="aiPrompt" type="textarea" :rows="4"
            placeholder="例如：设计一个供应商信息登记表，包含供应商基本信息、联系方式、资质证书、银行账户等字段"
          />
        </el-form-item>
      </el-form>

      <div class="ai-examples">
        <span>快速示例：</span>
        <el-tag v-for="ex in aiExamples" :key="ex" class="example-tag" @click="aiPrompt = ex">{{ ex }}</el-tag>
      </div>
      <template #footer>
        <el-button @click="showAIHelper = false">取消</el-button>
        <el-button type="primary" :loading="aiLoading" @click="generateWithAI">
          <el-icon><MagicStick /></el-icon> 生成表单
        </el-button>
      </template>
    </el-dialog>

    <!-- JSON 导入对话框 -->
    <el-dialog v-model="showJsonImport" title="JSON 导入表单" width="680px">
      <el-alert type="info" :closable="false" style="margin-bottom:12px">
        <div style="font-size:13px;color:#666">
          <b>支持的JSON格式：</b>直接粘贴 JSON 数组，每个对象为一个字段定义。
          <br/>字段类型：<code>text</code>/<code>select</code>/<code>date</code>/<code>number</code>/<code>phone</code>/<code>email</code>/<code>radio</code>/<code>checkbox</code>/<code>upload</code>等
        </div>
      </el-alert>
      <el-input
        v-model="jsonInputText"
        type="textarea"
        :rows="12"
        placeholder='粘贴 JSON 数组，例如：[{"type":"text","label":"名称","name":"name"}]'
        style="font-family:monospace;font-size:13px"
      />
      <template #footer>
        <el-button @click="showJsonImport = false">取消</el-button>
        <el-button type="primary" @click="importFromJson">导入并生成表单</el-button>
      </template>
    </el-dialog>


    <!-- 填写数据弹窗 -->
    <el-dialog v-model="showDataForm" :title="'填写数据 - ' + (dataFormTemplate?.name || '')" width="700px" destroy-on-close>
      <el-form :model="dataFormData" label-width="120px" ref="dataFormRef">
        <template v-for="f in dataFormFields" :key="f.name">
          <el-form-item :label="f.label + (f.required ? ' *' : '')" :required="f.required">
            <el-input v-if="['text','email','phone','url','password'].includes(f.type)" v-model="dataFormData[f.name]" :placeholder="f.placeholder || ('请输入' + f.label)" />
            <el-input v-else-if="f.type === 'textarea'" type="textarea" v-model="dataFormData[f.name]" :placeholder="f.placeholder || ('请输入' + f.label)" :rows="3" />
            <el-input-number v-else-if="f.type === 'number'" v-model="dataFormData[f.name]" style="width:100%" :min="f.min" :max="f.max" />
            <el-input v-else-if="f.type === 'money'" v-model="dataFormData[f.name]" :placeholder="'请输入' + f.label">
              <template #prepend>¥</template>
            </el-input>
            <el-date-picker v-else-if="f.type === 'date'" v-model="dataFormData[f.name]" type="date" style="width:100%" value-format="YYYY-MM-DD" />
            <el-date-picker v-else-if="f.type === 'datetime'" v-model="dataFormData[f.name]" type="datetime" style="width:100%" value-format="YYYY-MM-DD HH:mm:ss" />
            <el-time-picker v-else-if="f.type === 'time'" v-model="dataFormData[f.name]" style="width:100%" />
            <el-select v-else-if="f.type === 'select'" v-model="dataFormData[f.name]" style="width:100%" :placeholder="'请选择' + f.label" clearable>
              <el-option v-for="o in (f.options || [])" :key="o" :label="o" :value="o" />
            </el-select>
            <el-radio-group v-else-if="f.type === 'radio'" v-model="dataFormData[f.name]">
              <el-radio v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-radio>
            </el-radio-group>
            <el-checkbox-group v-else-if="f.type === 'checkbox'" v-model="dataFormData[f.name]">
              <el-checkbox v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-checkbox>
            </el-checkbox-group>
            <el-switch v-else-if="f.type === 'switch'" v-model="dataFormData[f.name]" />
            <el-rate v-else-if="f.type === 'rate'" v-model="dataFormData[f.name]" />
            <el-slider v-else-if="f.type === 'slider'" v-model="dataFormData[f.name]" :min="f.min||0" :max="f.max||100" />
            <el-input v-else v-model="dataFormData[f.name]" :placeholder="'请输入' + f.label" />
          </el-form-item>
        </template>
        <el-empty v-if="dataFormFields.length === 0" description="该模板暂无字段，请先设计模板" />
      </el-form>
      <template #footer>
        <el-button @click="showDataForm = false">取消</el-button>
        <el-button type="primary" :loading="dataFormLoading" @click="submitDataForm">提交数据</el-button>
      </template>
    </el-dialog>

    <!-- 数据管理弹窗 -->
    <el-dialog v-model="showDataManager" :title="'数据管理 - ' + (dataManagerTemplate?.name || '')" width="95%" top="5vh" destroy-on-close>
      <div class="data-manager">
        <div class="data-manager-toolbar">
          <div class="toolbar-left">
            <el-input v-model="dataSearchText" placeholder="搜索数据..." clearable style="width:240px" @input="debounceDataSearch">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-tag type="info">共 {{ dataTotal }} 条数据</el-tag>
          </div>
          <div class="toolbar-right">
            <el-button @click="openDataForm(dataManagerTemplate)">
              <el-icon><Plus /></el-icon> 填写数据
            </el-button>
            <el-button @click="exportDataCSV">
              <el-icon><Download /></el-icon> 导出CSV
            </el-button>
          </div>
        </div>

        <el-table :data="dataList" border size="small" max-height="500" v-loading="dataListLoading" @selection-change="onDataSelectionChange">
          <el-table-column type="selection" width="40" />
          <el-table-column label="#" type="index" width="50" />
          <template v-for="f in dataManagerFields" :key="f.name">
            <el-table-column :label="f.label" :prop="f.name" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ getDisplayValue(row, f) }}</span>
              </template>
            </el-table-column>
          </template>
          <el-table-column label="提交时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="viewDataDetail(row)">查看</el-button>
              <el-button size="small" text type="warning" @click="editDataItem(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click="deleteDataItem(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="data-pagination">
          <el-pagination
            v-model:current-page="dataPage"
            v-model:page-size="dataPageSize"
            :total="dataTotal"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @size-change="loadDataList"
            @current-change="loadDataList"
          />
        </div>

        <!-- 汇总统计 -->
        <div v-if="dataStats && dataTotal > 0" class="data-stats">
          <h4>数据汇总</h4>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="总提交数">{{ dataStats.total_count }}</el-descriptions-item>
            <el-descriptions-item label="今日提交">{{ dataStats.today_count }}</el-descriptions-item>
          </el-descriptions>
          <div v-for="(stat, fieldName) in (dataStats.field_stats || {})" :key="fieldName" class="field-stat">
            <template v-if="stat.distribution">
              <strong>{{ getFieldLabel(fieldName) }}</strong>:
              <el-tag v-for="(count, val) in stat.distribution" :key="val" size="small" style="margin:2px">{{ val }}: {{ count }}</el-tag>
            </template>
            <template v-else-if="stat.sum !== undefined">
              <strong>{{ getFieldLabel(fieldName) }}</strong>:
              合计 {{ stat.sum?.toFixed(2) }} / 平均 {{ stat.avg }} / 最小 {{ stat.min }} / 最大 {{ stat.max }}
            </template>
            <template v-else>
              <strong>{{ getFieldLabel(fieldName) }}</strong>:
              已填 {{ stat.filled }}/{{ stat.total }}
            </template>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 数据详情/编辑弹窗 -->
    <el-dialog v-model="showDataDetail" :title="dataDetailIsEdit ? '编辑数据' : '数据详情'" width="600px" destroy-on-close>
      <el-form :model="dataDetailData" label-width="120px">
        <template v-for="f in dataManagerFields" :key="f.name">
          <el-form-item :label="f.label">
            <template v-if="dataDetailIsEdit">
              <el-input v-if="['text','email','phone','url','password'].includes(f.type)" v-model="dataDetailData[f.name]" />
              <el-input v-else-if="f.type === 'textarea'" type="textarea" v-model="dataDetailData[f.name]" :rows="3" />
              <el-input-number v-else-if="f.type === 'number'" v-model="dataDetailData[f.name]" style="width:100%" />
              <el-input v-else-if="f.type === 'money'" v-model="dataDetailData[f.name]">
                <template #prepend>¥</template>
              </el-input>
              <el-date-picker v-else-if="f.type === 'date'" v-model="dataDetailData[f.name]" type="date" style="width:100%" value-format="YYYY-MM-DD" />
              <el-select v-else-if="f.type === 'select'" v-model="dataDetailData[f.name]" style="width:100%" clearable>
                <el-option v-for="o in (f.options || [])" :key="o" :label="o" :value="o" />
              </el-select>
              <el-radio-group v-else-if="f.type === 'radio'" v-model="dataDetailData[f.name]">
                <el-radio v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-radio>
              </el-radio-group>
              <el-checkbox-group v-else-if="f.type === 'checkbox'" v-model="dataDetailData[f.name]">
                <el-checkbox v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-checkbox>
              </el-checkbox-group>
              <el-switch v-else-if="f.type === 'switch'" v-model="dataDetailData[f.name]" />
              <el-input v-else v-model="dataDetailData[f.name]" />
            </template>
            <template v-else>
              <span>{{ dataDetailData[f.name] ?? '-' }}</span>
            </template>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showDataDetail = false">关闭</el-button>
        <el-button v-if="dataDetailIsEdit" type="primary" :loading="dataDetailSaving" @click="saveDataDetail">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog v-model="showPreview" :title="isPublishPreview ? '发布预览 - 确认表单效果' : '表单预览'" width="700px" destroy-on-close @close="closePreview">
      <!-- 发布预览模式提示 -->
      <el-alert v-if="isPublishPreview" title="请确认表单效果，确认无误后点击「立即发布」" type="info" show-icon :closable="false" style="margin-bottom:16px" />
      
      <el-form :model="previewData" label-width="120px">
        <el-form-item v-for="f in previewFields" :key="f._key" :label="f.label + (f.required ? ' *' : '')" :required="f.required">
          <el-input v-if="['text','email','phone','url'].includes(f.type)" v-model="previewData[f.name]" :placeholder="f.placeholder" />
          <el-input v-else-if="f.type === 'textarea'" type="textarea" v-model="previewData[f.name]" :placeholder="f.placeholder" />
          <el-input-number v-else-if="f.type === 'number'" v-model="previewData[f.name]" style="width:100%" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="previewData[f.name]" type="date" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="previewData[f.name]" style="width:100%">
            <el-option v-for="o in (f.options || [])" :key="o" :label="o" :value="o" />
          </el-select>
          <el-radio-group v-else-if="f.type === 'radio'" v-model="previewData[f.name]">
            <el-radio v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-radio>
          </el-radio-group>
          <el-checkbox-group v-else-if="f.type === 'checkbox'" v-model="previewData[f.name]">
            <el-checkbox v-for="o in (f.options || [])" :key="o" :label="o">{{ o }}</el-checkbox>
          </el-checkbox-group>
          <el-switch v-else-if="f.type === 'switch'" v-model="previewData[f.name]" />
          <el-rate v-else-if="f.type === 'rate'" v-model="previewData[f.name]" />
          <el-slider v-else-if="f.type === 'slider'" v-model="previewData[f.name]" style="width:100%" />
          <el-input v-else-if="f.type === 'money'" v-model="previewData[f.name]" placeholder="0.00">
            <template #prepend>¥</template>
          </el-input>
          <el-input v-else-if="f.type === 'password'" type="password" v-model="previewData[f.name]" show-password placeholder="请输入密码" />
          <el-date-picker v-else-if="f.type === 'datetime'" v-model="previewData[f.name]" type="datetime" style="width:100%" />
          <el-time-picker v-else-if="f.type === 'time'" v-model="previewData[f.name]" style="width:100%" />
          <el-date-picker v-else-if="f.type === 'daterange'" v-model="previewData[f.name]" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" style="width:100%" />
          <el-upload v-else-if="f.type === 'upload'" :auto-upload="false" action="#" :limit="5">
            <el-button size="small" type="primary"><el-icon><Upload /></el-icon> 点击上传</el-button>
            <template #tip><div class="el-upload__tip">支持常见文件格式</div></template>
          </el-upload>
          <el-upload v-else-if="f.type === 'image'" :auto-upload="false" action="#" accept="image/*" list-type="picture-card" :limit="3">
            <el-icon><Plus /></el-icon>
          </el-upload>
          <el-input v-else-if="f.type === 'richtext'" type="textarea" :rows="4" v-model="previewData[f.name]" placeholder="富文本内容（预览模式）" />
          <el-input v-else-if="f.type === 'autonum'" disabled :placeholder="'自动生成编号'" />
          <el-input v-else-if="f.type === 'location'" v-model="previewData[f.name]" placeholder="请输入地址" />
          <el-color-picker v-else-if="f.type === 'color'" v-model="previewData[f.name]" />
          <el-input v-else-if="['signature','barcode','qrcode','subform','relation','refdata','user','org','icon','group','grid','tabs','cascader'].includes(f.type)" disabled :placeholder="'[' + f.type + '] ' + f.label" />
          <div v-else-if="f.type === 'divider'" style="border-top:1px solid #eee;margin:8px 0"></div>
          <h4 v-else-if="f.type === 'heading'" style="margin:8px 0">{{ f.label }}</h4>
          <el-input v-else v-model="previewData[f.name]" :placeholder="'[' + f.type + ']'" />
        </el-form-item>
      </el-form>

      <!-- 权限设置 -->
      <div v-if="isPublishPreview" class="permission-section">
        <h4>访问权限设置</h4>
        <el-radio-group v-model="accessType">
          <el-radio label="private">私有（仅自己可见）</el-radio>
          <el-radio label="public">公开（任何人可访问）</el-radio>
          <el-radio label="specified">指定用户</el-radio>
        </el-radio-group>
        <div v-if="accessType === 'specified'" class="user-selector" style="margin-top:12px">
          <div class="selected-users">
            <el-tag v-for="user in allowedUsers" :key="user.id" closable @close="removeUser(user)">
              {{ user.username }} ({{ user.full_name || '未设置姓名' }})
            </el-tag>
          </div>
          
          <div class="user-search" style="margin-top:8px">
            <el-select
              v-model="userSearchQuery"
              filterable
              remote
              reserve-keyword
              placeholder="搜索用户ID或用户名"
              :remote-method="searchUsers"
              :loading="userSearchLoading"
              @change="onUserSelected"
              style="width:100%;max-width:400px"
            >
              <el-option
                v-for="user in userSearchResults"
                :key="user.id"
                :label="`${user.username} (${user.full_name || '未设置姓名'})`"
                :value="user.username"
              />
            </el-select>
            <div class="search-hint" style="font-size:12px;color:#909399;margin-top:4px">
              输入用户ID或用户名搜索，从下拉列表中选择
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <template v-if="isPublishPreview">
          <el-button @click="closePreview">返回修改</el-button>
          <el-button type="success" :loading="publishing" @click="confirmPublishFromPreview">
            <el-icon><Promotion /></el-icon> 立即发布
          </el-button>
        </template>
        <template v-else>
          <el-button @click="showPreview = false">关闭</el-button>
          <el-button type="primary" @click="showPreview = false">提交测试</el-button>
        </template>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import {
  Plus, Edit, Delete, MagicStick, Document, Search, ArrowDown, ArrowUp,
  CopyDocument, Close, SetUp, Operation, View, Select, Minus, Calendar,
  Pointer, Finished, Open, Upload, Picture, EditPen, Grid, Title,
  Folder, FolderOpened, List, Connection, DataLine, Ticket, Location,
  Brush, PictureFilled, User, OfficeBuilding, Link, Message, Phone,
  Lock, Timer, Alarm, DateRange, Share, Star, Notebook, Download,
  ArrowLeft, MoreFilled, Rank, RefreshRight
} from '@element-plus/icons-vue'
import { templateAPI, userAPI } from '../../common/api'
import { useAIStore } from '../../common/store/ai'
import { useUserStore } from '../../common/store/user'

// 路由
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 视图状态
const viewMode = ref('list')
const listStyle = ref('table')  // 'table' | 'card'，默认表格视图
const searchText = ref('')
const categoryFilter = ref('')
const loading = ref(false)
const toolboxExpanded = ref(['basic', 'datetime', 'select'])

// 数据
const templates = ref<any[]>([])
let searchTimer: any = null

const filteredTemplates = computed(() => {
  let list = templates.value
  if (categoryFilter.value) list = list.filter(t => t.category === categoryFilter.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(t => (t.name||'').toLowerCase().includes(q) || (t.description||'').toLowerCase().includes(q) || (t.code||'').toLowerCase().includes(q))
  }
  return list
})

function debounceSearch() { clearTimeout(searchTimer); searchTimer = setTimeout(loadTemplates, 400) }
function filterByCategory() {}

async function loadTemplates() {
  loading.value = true
  try {
    const res: any = await templateAPI.list({ limit: 100 })
    console.log('[loadTemplates] API 返回原始数据:', JSON.stringify(res)?.slice(0, 200))
    if (Array.isArray(res)) {
      templates.value = res
    } else if (res && typeof res === 'object') {
      // 支持 {items: []} 或 {data: []} 或 {templates: []} 格式
      templates.value = res.items || res.data || res.templates || []
    } else {
      templates.value = []
    }
    console.log('[loadTemplates] 最终 templates.value 长度:', templates.value.length)
  } catch (e: any) {
    console.error('[loadTemplates] 加载失败:', e)
    templates.value = []
    ElMessage.error('加载模板列表失败: ' + (e?.message || e?.response?.data?.detail || '未知错误'))
  }
  finally { loading.value = false }
}

// 当前编辑模板
const currentTemplate = reactive({ id: null as number|null, name: '', code: '', description: '', category: '', is_public: false, fields: [] as any[] })
const selectedField = ref<number|null>(null)
const dragIdx = ref<number|null>(null)

// 字段类型定义 - 40种控件
const fieldTypes = [
  // 基础控件
  { type: 'text', label: '单行文本', icon: 'Edit', category: 'basic' },
  { type: 'textarea', label: '多行文本', icon: 'Document', category: 'basic' },
  { type: 'number', label: '数字', icon: 'Minus', category: 'basic' },
  { type: 'password', label: '密码', icon: 'Lock', category: 'basic' },
  { type: 'email', label: '邮箱', icon: 'Message', category: 'basic' },
  { type: 'phone', label: '电话', icon: 'Phone', category: 'basic' },
  { type: 'url', label: '网址', icon: 'Link', category: 'basic' },
  { type: 'money', label: '金额', icon: 'Ticket', category: 'basic' },
  // 日期时间
  { type: 'date', label: '日期', icon: 'Calendar', category: 'datetime' },
  { type: 'datetime', label: '日期时间', icon: 'Timer', category: 'datetime' },
  { type: 'time', label: '时间', icon: 'Alarm', category: 'datetime' },
  { type: 'daterange', label: '日期范围', icon: 'DateRange', category: 'datetime' },
  // 选择控件
  { type: 'select', label: '下拉选择', icon: 'ArrowDown', category: 'select' },
  { type: 'cascader', label: '级联选择', icon: 'Share', category: 'select' },
  { type: 'radio', label: '单选', icon: 'Pointer', category: 'select' },
  { type: 'checkbox', label: '多选', icon: 'Finished', category: 'select' },
  { type: 'switch', label: '开关', icon: 'Open', category: 'select' },
  { type: 'slider', label: '滑块', icon: 'Operation', category: 'select' },
  { type: 'rate', label: '评分', icon: 'Star', category: 'select' },
  // 高级控件
  { type: 'richtext', label: '富文本', icon: 'Notebook', category: 'advanced' },
  { type: 'upload', label: '文件上传', icon: 'Upload', category: 'advanced' },
  { type: 'image', label: '图片上传', icon: 'Picture', category: 'advanced' },
  { type: 'signature', label: '签名', icon: 'EditPen', category: 'advanced' },
  // 布局控件
  { type: 'divider', label: '分隔线', icon: 'Minus', category: 'layout' },
  { type: 'heading', label: '标题', icon: 'Title', category: 'layout' },
  { type: 'grid', label: '栅格布局', icon: 'Grid', category: 'layout' },
  { type: 'tabs', label: '标签页', icon: 'FolderOpened', category: 'layout' },
  // 数据控件
  { type: 'subform', label: '子表单', icon: 'List', category: 'data' },
  { type: 'relation', label: '关联数据', icon: 'Connection', category: 'data' },
  { type: 'autonum', label: '自动编号', icon: 'Ticket', category: 'data' },
  // 特殊控件
  { type: 'location', label: '地图位置', icon: 'Location', category: 'special' },
  { type: 'color', label: '颜色选择', icon: 'Brush', category: 'special' },
  { type: 'icon', label: '图标选择', icon: 'PictureFilled', category: 'special' },
  { type: 'user', label: '人员选择', icon: 'User', category: 'special' },
  { type: 'org', label: '部门选择', icon: 'OfficeBuilding', category: 'special' },
]

const basicFields = computed(() => fieldTypes.filter(f => f.category === 'basic'))
const datetimeFields = computed(() => fieldTypes.filter(f => f.category === 'datetime'))
const selectFields = computed(() => fieldTypes.filter(f => f.category === 'select'))
const advancedFields = computed(() => fieldTypes.filter(f => f.category === 'advanced'))
const layoutFields = computed(() => fieldTypes.filter(f => f.category === 'layout'))
const dataFields = computed(() => fieldTypes.filter(f => f.category === 'data'))
const specialFields = computed(() => fieldTypes.filter(f => f.category === 'special'))

// 分类配置
const categories = [
  { value: 'crm', label: '客户管理', color: '#409EFF' },
  { value: 'order', label: '订单管理', color: '#67C23A' },
  { value: 'hr', label: '人力资源', color: '#E6A23C' },
  { value: 'inventory', label: '仓储物流', color: '#F56C6C' },
  { value: 'project', label: '项目管理', color: '#909399' },
  { value: 'finance', label: '财务报销', color: '#9B59B6' },
  { value: 'general', label: '通用表单', color: '#34495E' },
]

function getCategoryColor(cat?: string) { return categories.find(c => c.value === cat)?.color || '#409EFF' }
function getCategoryLabel(cat?: string) { return categories.find(c => c.value === cat)?.label || '未分类' }
function getCategoryIcon(cat?: string) {
  const map: Record<string,string> = { crm:'User', order:'ShoppingCart', hr:'Document', inventory:'Folder', project:'Folder', finance:'Ticket', general:'Document' }
  return map[cat||'general'] || 'Document'
}
function getCategoryTagType(cat?: string) {
  const map: Record<string,string> = { crm:'primary', order:'success', hr:'warning', inventory:'danger', project:'info', finance:'warning', general:'info' }
  return (map[cat||'general'] || 'info') as any
}

// 拖拽逻辑
let dragFieldType: any = null
function onDragStart(e: DragEvent, ft: any) { dragFieldType = ft; e.dataTransfer?.setData('text/plain', ft.type) }
function onDrop(e: DragEvent) {
  if (!dragFieldType) return
  const key = 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2,6)
  let fieldName = dragFieldType.type + '_field'
  let idx = 1
  while (currentTemplate.fields.some((f:any) => f.name === fieldName)) { fieldName = dragFieldType.type + '_field_' + idx++ }
  currentTemplate.fields.push({
    _key: key, type: dragFieldType.type, label: dragFieldType.label, name: fieldName,
    placeholder: '', required: false, readonly: false, hidden: false, width: '100%',
    defaultValue: '', options: ['select','radio','checkbox'].includes(dragFieldType.type) ? ['选项1','选项2','选项3'] : [],
    optionsText: '', min: 0, max: 100, step: 1, precision: 0, maxLength: 255, limit: 1, maxSize: 10, accept: '', format: 'YYYY-MM-DD'
  })
  selectedField.value = currentTemplate.fields.length - 1
  dragFieldType = null
}

function onFieldDragStart(e: DragEvent, idx: number) { dragIdx.value = idx }
function onFieldDrop(e: DragEvent, targetIdx: number) {
  if (dragIdx.value === null || dragIdx.value === targetIdx) return
  const arr = currentTemplate.fields
  const item = arr.splice(dragIdx.value, 1)[0]
  arr.splice(targetIdx, 0, item)
  if (selectedField.value === dragIdx.value) selectedField.value = targetIdx
  else if (selectedField.value !== null && selectedField.value > dragIdx.value && selectedField.value <= targetIdx) selectedField.value--
  else if (selectedField.value !== null && selectedField.value < dragIdx.value && selectedField.value >= targetIdx) selectedField.value++
  dragIdx.value = null
}

// 字段操作
function removeField(idx: number) {
  currentTemplate.fields.splice(idx, 1)
  if (selectedField.value === idx) selectedField.value = null
  else if (selectedField.value !== null && selectedField.value > idx) selectedField.value--
}
function moveField(idx: number, dir: number) {
  const arr = currentTemplate.fields
  const newIdx = idx + dir
  if (newIdx < 0 || newIdx >= arr.length) return
  ;[arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]]
  if (selectedField.value === idx) selectedField.value = newIdx
  else if (selectedField.value === newIdx) selectedField.value = idx
}
function copyField(idx: number) {
  const clone = JSON.parse(JSON.stringify(currentTemplate.fields[idx]))
  clone._key = 'field_' + Date.now()
  clone.name = clone.name + '_copy'
  currentTemplate.fields.splice(idx + 1, 0, clone)
}
// 切换字段类型时的处理：初始化或清理相关属性
function onFieldTypeChange(newType: string) {
  if (selectedField.value === null) return
  const f = currentTemplate.fields[selectedField.value]
  // 切换到选择类型：若没有选项则给默认示例
  if (['select', 'radio', 'checkbox'].includes(newType)) {
    if (!f.options || f.options.length === 0) {
      f.options = ['选项一', '选项二', '选项三']
      f.optionsText = '选项一\n选项二\n选项三'
    }
  }
  // 切换到非选择类型：清空 options（但不强制，保留以备再切回）
  // 切换到数值类型：初始化 min/max
  if (newType === 'number' || newType === 'slider') {
    if (f.min === undefined || f.min === null) f.min = 0
    if (f.max === undefined || f.max === null) f.max = 100
  }
  // 切换到开关类型：清空 placeholder（无意义）
  if (newType === 'switch') { f.placeholder = '' }
}

function autoFieldName() {
  if (selectedField.value === null) return
  const f = currentTemplate.fields[selectedField.value]
  const pinyin: Record<string,string> = {'姓名':'name','名称':'name','标题':'title','编码':'code','编号':'code','电话':'phone','手机':'phone','邮箱':'email','地址':'address','日期':'date','时间':'time','备注':'remark','说明':'desc','金额':'amount','数量':'quantity','价格':'price','状态':'status','类型':'type','分类':'category','部门':'dept','人员':'user'}
  f.name = pinyin[f.label] || f.label.toLowerCase().replace(/[^a-z0-9_]/g,'_').slice(0,20)
}
function applyOptions() {
  if (selectedField.value === null) return
  const f = currentTemplate.fields[selectedField.value]
  f.options = (f.optionsText||'').split(/[,\n]/).map((s:string)=>s.trim()).filter(Boolean)
}

// 模板操作
const showEditDialog = ref(false)
const editingTemplate = ref<any>(null)
const editFormRef = ref()
const editForm = reactive({ name:'', code:'', description:'', category:'general', is_active:true })
const editRules = { name: [{ required:true, message:'请输入模板名称', trigger:'blur' }], code: [{ required:true, message:'请输入模板编码', trigger:'blur' }] }

function openCreateDialog() {
  editingTemplate.value = null
  editForm.name = ''; editForm.code = ''; editForm.description = ''; editForm.category = 'general'; editForm.is_active = true
  showEditDialog.value = true
}
function openEditDialog(t: any) {
  editingTemplate.value = t
  editForm.name = t.name; editForm.code = t.code||''; editForm.description = t.description||''; editForm.category = t.category||'general'; editForm.is_active = t.is_active!==false
  showEditDialog.value = true
}
// 从编辑框进入发布预览的入口（保存后继续发布）
function continuePublishPreview() {
  // 从 editingTemplate（原始数据）或 currentTemplate 读取 ID
  const src = editingTemplate.value || currentTemplate
  ;(currentTemplate as any).id = src.id ?? null
  currentTemplate.name = editForm.name
  currentTemplate.code = editForm.code
  currentTemplate.description = editForm.description
  currentTemplate.category = editForm.category

  if (!currentTemplate.fields || currentTemplate.fields.length === 0) {
    ElMessage.warning('请先进入设计器添加表单字段后再发布')
    showEditDialog.value = false
    return
  }

  isPublishPreview.value = true
  previewFields.value = currentTemplate.fields.map(f => ({...f, _value: ''}))
  previewFields.value.forEach(f => { previewData[f.name] = f.defaultValue || '' })
  showPreview.value = true
  editingTemplate.value = null
}

async function confirmCreateOrUpdate() {
  if (!editForm.name.trim()) { ElMessage.warning('请输入模板名称'); return }
  if (!editForm.code.trim()) { ElMessage.warning('请输入模板编码'); return }

  // 【关键】在 API 调用之前保存所有状态，不会被 API 响应覆盖
  const fromPublish = !!(editingTemplate.value && (editingTemplate.value as any)._fromPublish)
  const editingId = editingTemplate.value ? (editingTemplate.value as any).id : null
  const templateId = editingId ?? (currentTemplate as any).id ?? null

  try {
    if (editingTemplate.value) {
      // 【编辑已有模板】
      if (!templateId) {
        // ID 缺失时给出具体信息便于排查
        ElMessage.error(`模板ID缺失（editingId=${editingId}, currentId=${(currentTemplate as any).id}），请刷新页面后重试`)
        return
      }
      await templateAPI.update(templateId, {
        name: editForm.name, code: editForm.code,
        description: editForm.description, category: editForm.category,
        is_active: editForm.is_active
      })
      // 同步更新列表
      const listItem = templates.value.find(t => t.id === templateId)
      if (listItem) Object.assign(listItem, {
        name: editForm.name, code: editForm.code,
        description: editForm.description, category: editForm.category,
        is_active: editForm.is_active
      })
      if ((currentTemplate as any).id === templateId) {
        currentTemplate.name = editForm.name
        currentTemplate.code = editForm.code
        currentTemplate.description = editForm.description
        currentTemplate.category = editForm.category
      }
      ElMessage.success('保存成功')
      showEditDialog.value = false
      // 【核心】使用调用前保存的 fromPublish，不再依赖 editingTemplate.value 上的标记
      if (fromPublish) {
        continuePublishPreview()
      }
    } else {
      // 【新建模板】
      const res: any = await templateAPI.create({
        name: editForm.name, code: editForm.code,
        description: editForm.description, category: editForm.category,
        is_active: editForm.is_active, modules: []
      })
      console.log('[confirmCreateOrUpdate] 创建返回:', res)
      templates.value.unshift(res)  // 新模板加入工作区列表
      showEditDialog.value = false
      openDesigner(res)
      return
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    console.error('[confirmCreateOrUpdate] 保存失败:', msg, e)
    ElMessage.error('保存失败: ' + msg)
  }
}
// 从模板对象（含 modules/fields）提取并标准化字段数组，写入 currentTemplate
function applyTemplateFields(t: any) {
  let fields: any[] = []
  if (t.modules && Array.isArray(t.modules)) {
    for (const mod of t.modules) {
      if (mod.fields && Array.isArray(mod.fields)) {
        fields = fields.concat(mod.fields)
      }
    }
  }
  if (fields.length === 0 && t.fields) {
    try { fields = typeof t.fields === 'string' ? JSON.parse(t.fields) : t.fields } catch {}
  }
  currentTemplate.fields = fields.map(f => ({...f, _key: 'field_'+Math.random().toString(36).slice(2), optionsText: Array.isArray(f.options) ? f.options.join(',') : '' }))
}

function openDesigner(t: any) {
  currentTemplate.id = t.id; currentTemplate.name = t.name; currentTemplate.code = t.code||''
  currentTemplate.description = t.description||''; currentTemplate.category = t.category||''
  currentTemplate.is_public = t.is_public || false
  applyTemplateFields(t)
  selectedField.value = null; viewMode.value = 'design'
}
// 发布模板到数据库
const publishing = ref(false)
const isPublishPreview = ref(false)  // 标记是否为发布预览模式

// 权限设置
const accessType = ref<'private' | 'public' | 'specified'>('private')
const allowedUsers = ref<Array<{id: number, username: string, full_name?: string}>>([])
const userSearchQuery = ref('')
const userSearchResults = ref<any[]>([])
const userSearchLoading = ref(false)

// 设计界面点击发布 → 进入预览界面
async function publishTemplate(template?: any) {
  const fromList = !!template
  // 列表页发布：先把模板数据同步到 currentTemplate（提取 fields）
  if (fromList) {
    currentTemplate.id = template.id
    currentTemplate.name = template.name
    currentTemplate.code = template.code || ''
    currentTemplate.description = template.description || ''
    currentTemplate.category = template.category || ''
    currentTemplate.is_public = template.is_public || false
    applyTemplateFields(template)
  }

  const tpl = fromList ? currentTemplate : currentTemplate
  const nameVal = (currentTemplate.name || '').trim()

  if (!nameVal) {
    // 名称为空，引导填写
    if (fromList) {
      editingTemplate.value = { ...template, _fromPublish: true }
      editForm.name = template.name || ''
      editForm.code = template.code || ''
      editForm.description = template.description || ''
      editForm.category = template.category || 'general'
      editForm.is_active = true
    } else {
      editingTemplate.value = null
      editForm.name = ''
      editForm.code = ''
      editForm.description = ''
      editForm.category = 'general'
      editForm.is_active = true
    }
    showEditDialog.value = true
    ElMessage.info('请先填写模板名称后再发布')
    return
  }

  if (!currentTemplate.fields || currentTemplate.fields.length === 0) {
    ElMessage.warning('请先进入设计器添加表单字段后再发布')
    return
  }

  // 进入发布预览模式
  isPublishPreview.value = true
  previewFields.value = currentTemplate.fields.map(f => ({...f, _value:''}))
  previewFields.value.forEach(f => { previewData[f.name] = f.defaultValue || '' })
  showPreview.value = true
}

// 撤回发布：将 is_published 设为 false
async function unpublishTemplate(t: any) {
  try {
    await templateAPI.update(t.id, { is_published: false })
    // 同步列表
    const listItem = templates.value.find(x => x.id === t.id)
    if (listItem) listItem.is_published = false
    // 同步 currentTemplate
    if ((currentTemplate as any).id === t.id) {
      ;(currentTemplate as any).is_published = false
    }
    ElMessage.success('已撤回发布，模板恢复为草稿状态')
  } catch (e: any) {
    ElMessage.error('撤回失败: ' + (e?.message || ''))
  }
}

// 预览界面点击立即发布
async function confirmPublishFromPreview() {
  const tpl = currentTemplate
  publishing.value = true
  try {
    // 构建发布数据
    const publishData = {
      name: tpl.name,
      code: tpl.code || tpl.name.toLowerCase().replace(/\s+/g, '_'),
      description: tpl.description || '',
      category: tpl.category || 'general',
      is_published: true,
      config: {
        access_type: accessType.value,
        allowed_users: accessType.value === 'specified' ? allowedUsers.value.map(u => u.id) : [],
        share_link: accessType.value === 'public' ? `${window.location.origin}/form/${tpl.id || 'new'}` : null
      },
      modules: [{
        name: 'main',
        fields: tpl.fields.map((f: any) => ({
          type: f.type,
          label: f.label,
          name: f.name,
          required: f.required,
          width: f.width,
          options: f.options || [],
          placeholder: f.placeholder || ''
        }))
      }]
    }
    
    // 调用后端发布 API（创建或更新）
    let res: any
    if (tpl.id) {
      res = await templateAPI.update(tpl.id, publishData)
    } else {
      res = await templateAPI.create(publishData)
    }
    // 后端返回的直接是数据对象，不是 {success: ..., data: ...} 格式
    // res 就是 TemplateResponse: {id, name, code, ...}
    
    // 调用发布接口
    if (res.id) {
      await templateAPI.publish(res.id)
      tpl.id = res.id  // 保存ID供后续使用
      ElMessage.success('模板已发布成功！')
      showPreview.value = false
      isPublishPreview.value = false
      await loadTemplates()
      // 发布成功后跳转到表单填写页
      router.push(`/form/${res.id}`)
    } else {
      ElMessage.error('发布失败：服务器未返回模板ID')
    }
  } catch (e: any) {
    console.error('发布失败:', e)
    ElMessage.error(e.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

// 权限相关函数
function removeUser(user: {id: number}) {
  const index = allowedUsers.value.findIndex(u => u.id === user.id)
  if (index > -1) {
    allowedUsers.value.splice(index, 1)
  }
}

// 搜索用户
async function searchUsers(query: string) {
  if (!query || query.trim().length < 2) {
    userSearchResults.value = []
    return
  }
  
  userSearchLoading.value = true
  try {
    const res: any = await userAPI.list({ search: query, limit: 10 })
    userSearchResults.value = Array.isArray(res) ? res : (res.items || [])
  } catch (e) {
    console.error('搜索用户失败:', e)
    userSearchResults.value = []
  } finally {
    userSearchLoading.value = false
  }
}

// 用户选择回调
function onUserSelected(username: string) {
  if (!username) return
  
  // 在搜索结果中找到对应的用户对象
  const selectedUser = userSearchResults.value.find(u => u.username === username)
  if (!selectedUser) return
  
  // 检查是否已添加
  const alreadyAdded = allowedUsers.value.some(u => u.id === selectedUser.id)
  if (!alreadyAdded) {
    allowedUsers.value.push({
      id: selectedUser.id,
      username: selectedUser.username,
      full_name: selectedUser.full_name
    })
    userSearchQuery.value = '' // 清空搜索框
    userSearchResults.value = [] // 清空搜索结果
  }
}

// 关闭预览时重置状态
function closePreview() {
  showPreview.value = false
  isPublishPreview.value = false
  // 重置权限设置
  accessType.value = 'private'
  allowedUsers.value = []
}

async function saveTemplate() {
  if (!currentTemplate.name.trim()) { ElMessage.warning('请输入模板名称'); return }
  const fieldsToSave = currentTemplate.fields.map(({_key, _value, optionsText, ...rest}: any) => rest)
  try {
    if (currentTemplate.id) {
      await templateAPI.update(currentTemplate.id, { name:currentTemplate.name, code:currentTemplate.code, description:currentTemplate.description, category:currentTemplate.category, is_public:currentTemplate.is_public, modules:[{name:'main', label:'主表单', fields:fieldsToSave}] })
      ElMessage.success('模板已更新')
    } else {
      const res: any = await templateAPI.create({ name:currentTemplate.name, code:currentTemplate.code, description:currentTemplate.description, category:currentTemplate.category, modules:[{name:'main', label:'主表单', fields:fieldsToSave}] })
      console.log('[saveTemplate] 创建返回:', res)
      currentTemplate.id = res.id; templates.value.unshift(res)
      ElMessage.success('模板已保存')
    }
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '未知错误'
    console.error('[saveTemplate] 保存失败:', msg, e)
    ElMessage.error('保存失败: ' + msg)
  }
}
async function deleteTemplate(t: any) {
  try {
    await ElMessageBox.confirm(`确定删除模板「${t.name}」？`, '危险操作', { type: 'error' })
    await templateAPI.delete(t.id)
    templates.value = templates.value.filter(x => x.id !== t.id)
    ElMessage.success('已删除')
  } catch {}
}
async function duplicateTemplate(t: any) {
  try {
    const res: any = await templateAPI.create({ name:t.name+' (副本)', code:t.code+'_copy', description:t.description, category:t.category, fields:t.fields })
    templates.value.unshift(res); ElMessage.success('复制成功')
  } catch { ElMessage.error('复制失败') }
}
function exportTemplate(t: any) {
  const data = JSON.stringify(t, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `${t.code||'template'}_${t.id}.json`; a.click()
  URL.revokeObjectURL(url); ElMessage.success('导出成功')
}

// 工具函数
// 修复：countFields 需要处理 modules 格式
function countFields(t: any) {
  if (!t) return 0
  // 从 modules 中提取
  if (t.modules && Array.isArray(t.modules)) {
    let count = 0
    for (const mod of t.modules) {
      if (mod.fields && Array.isArray(mod.fields)) count += mod.fields.length
    }
    return count
  }
  // 兼容直接 fields
  if (t.fields) {
    if (Array.isArray(t.fields)) return t.fields.length
    try { return JSON.parse(t.fields).length } catch { return 0 }
  }
  return 0
}
function formatDateShort(s: string|null) { return s ? new Date(s).toLocaleDateString('zh-CN') : '-' }
function formatDate(s: string|null) {
  if (!s) return '-'
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}
// 获取当前用户ID
const currentUserId = computed(() => userStore.userInfo?.id ?? null)
// 获取创建人显示名
function getCreatorName(t: any) {
  if (!t.created_by) return '—'
  if (t.created_by === currentUserId.value) return '我'
  return `用户${t.created_by}`
}
function getFieldTypeLabel(type: string) { return fieldTypes.find(f => f.type === type)?.label || type }
function getFieldTypeStyle(type: string) {
  const styles: Record<string,string> = { text:'', textarea:'info', number:'warning', password:'danger', email:'success', phone:'success', url:'info', date:'primary', datetime:'primary', select:'success', radio:'info', checkbox:'warning', switch:'danger', upload:'info', image:'success' }
  return (styles[type] || 'info') as any
}

// 预览
const showPreview = ref(false)
const previewFields = ref<any[]>([])
const previewData = reactive({} as Record<string,any>)

function previewTemplate() {
  previewFields.value = currentTemplate.fields.map(f => ({...f, _value:''}))
  previewFields.value.forEach(f => { previewData[f.name] = f.defaultValue || '' })
  showPreview.value = true
}

// AI 设计
const showAIHelper = ref(false)
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiExamples = ['供应商信息管理', '员工入职登记表', '客户投诉处理单', '采购申请流程表', '项目周报模板', '报销申请单']

// 对话框中展示给用户看的系统提示词摘要（只读）
const AI_SYSTEM_PROMPT_HINT = `请输出字段定义格式（type/label/name）的JSON数组，不要输出任何其他文字。\n可用类型：text/textarea/number/date/datetime/select/radio/checkbox/switch/email/phone/file/image/divider`

// AI store
const aiStore = useAIStore()
const selectedModelId = ref('')

// 加载模型列表
onMounted(async () => {
  await loadTemplates()
  await aiStore.loadModels()
  // 设置默认模型
  if (aiStore.models.length > 0) {
    selectedModelId.value = aiStore.currentModel?.modelId || aiStore.models[0].modelId
  }
})

// 导入相关
const showImport = ref(false)
const importStep = ref(0)
const importLoading = ref(false)
const importFileName = ref('')
const importData = reactive({
  headers: [] as string[],
  rows: [] as any[],
  all_rows: [] as any[],
  total_rows: 0,
  total_columns: 0,
  sheet_names: [] as string[],
  current_sheet: 'Sheet1',
  header_row: 0,
  potential_headers: [] as any[],
  detected_header_row: 0,
  filename: ''
})
const importFields = ref<any[]>([])
const importTemplateForm = reactive({ name: '', description: '', category: 'general' })
const uploadRef = ref()
const importHeaderRow = ref(0)
const importSheetName = ref('')
const importDependenciesStatus = ref<any>(null)  // 依赖状态

// 获取导入依赖状态
async function fetchImportDependenciesStatus() {
  try {
    const res = await (window as any).fetch('/api/v1/import/status', {
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') }
    })
    const json = await res.json()
    if (json.success) {
      importDependenciesStatus.value = json.data
    }
  } catch (e) {
    console.warn('获取导入依赖状态失败', e)
  }
}
const importSelectedFields = ref<Record<number, boolean>>({})
const importSelectAll = ref(true)
const importSelectIndeterminate = ref(false)
const importFileRaw = ref<File|null>(null)  // 保存原始文件用于重新解析

// 数据提交相关
const showDataForm = ref(false)
const dataFormTemplate = ref<any>(null)
const dataFormFields = ref<any[]>([])
const dataFormData = reactive({} as Record<string, any>)
const dataFormLoading = ref(false)
const dataFormRef = ref()

// 数据管理相关
const showDataManager = ref(false)
const dataManagerTemplate = ref<any>(null)
const dataManagerFields = ref<any[]>([])
const dataList = ref<any[]>([])
const dataListLoading = ref(false)
const dataSearchText = ref('')
const dataTotal = ref(0)
const dataPage = ref(1)
const dataPageSize = ref(20)
const dataSelectedRows = ref<any[]>([])
const dataStats = ref<any>(null)
let dataSearchTimer: any = null

// 数据详情/编辑
const showDataDetail = ref(false)
const dataDetailData = reactive({} as Record<string, any>)
const dataDetailIsEdit = ref(false)
const dataDetailId = ref<number|null>(null)
const dataDetailSaving = ref(false)

// 全部字段类型（用于下拉选择）
const allFieldTypes = [
  { type: 'text', label: '单行文本' }, { type: 'textarea', label: '多行文本' },
  { type: 'number', label: '数字' }, { type: 'money', label: '金额' },
  { type: 'email', label: '邮箱' }, { type: 'phone', label: '电话' },
  { type: 'date', label: '日期' }, { type: 'datetime', label: '日期时间' },
  { type: 'select', label: '下拉选择' }, { type: 'radio', label: '单选' },
  { type: 'checkbox', label: '多选' }, { type: 'switch', label: '开关' },
  { type: 'slider', label: '滑块' }, { type: 'rate', label: '评分' },
  { type: 'upload', label: '文件上传' }, { type: 'image', label: '图片上传' },
  { type: 'richtext', label: '富文本' }, { type: 'divider', label: '分隔线' },
  { type: 'heading', label: '标题' }, { type: 'subform', label: '子表单' },
  { type: 'relation', label: '关联数据' }, { type: 'autonum', label: '自动编号' },
  { type: 'location', label: '地图位置' }, { type: 'color', label: '颜色选择' },
  { type: 'user', label: '人员选择' }, { type: 'org', label: '部门选择' },
]


// ========== 导入功能 ==========
async function onImportFileChange(file: any) {
  importFileName.value = file.name || file.raw?.name || ''
  const rawFile = file.raw || file
  importFileRaw.value = rawFile  // 保存原始文件
  importHeaderRow.value = 0
  importSheetName.value = ''
  await doParseFile(rawFile, 0, '')
}

async function doParseFile(rawFile: File, headerRow: number, sheetName: string) {
  const formData = new FormData()
  formData.append('file', rawFile)
  formData.append('header_row', String(headerRow))
  if (sheetName) formData.append('sheet_name', sheetName)
  try {
    const res = await (window as any).fetch('/api/v1/import/parse', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: formData
    })
    const json = await res.json()
    if (json.success) {
      const data = json.data || {}

      // 保存原始数据和候选表头
      importData.all_rows = data.all_rows || []
      importData.potential_headers = data.potential_headers || []
      importData.detected_header_row = data.detected_header_row ?? 0
      importData.sheet_names = data.sheet_names || []
      importData.current_sheet = data.current_sheet || 'Sheet1'
      importData.filename = data.filename || importFileName.value

      // 自动选择智能检测的最佳表头行
      importHeaderRow.value = data.detected_header_row ?? 0

      // 调用 apply-header 获取表头和字段
      await applyHeaderRow(importHeaderRow.value)

      // 自动填入模板名称
      if (data.template_name) {
        importTemplateForm.name = data.template_name
      } else {
        importTemplateForm.name = importFileName.value.replace(/\.(xlsx|xls|csv|png|jpg|jpeg|bmp|docx|json)$/i, '')
      }

      importStep.value = 1
      ElMessage.success(json.message)
    } else {
      ElMessage.error(json.detail || json.message || '解析失败')
    }
  } catch (e: any) {
    ElMessage.error('解析失败: ' + (e.message || '请检查文件格式'))
  }
}

// 应用选定的表头行
async function applyHeaderRow(headerRow: number) {
  if (!importData.all_rows || importData.all_rows.length === 0) return

  try {
    const res = await (window as any).fetch('/api/v1/import/apply-header', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + (localStorage.getItem('kflower_token') || ''),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        all_rows: importData.all_rows,
        header_row: headerRow
      })
    })
    const json = await res.json()
    if (json.success) {
      const data = json.data || {}
      importData.headers = data.headers || []
      importData.rows = data.rows || []
      importData.total_rows = data.total_rows ?? 0
      importData.total_columns = data.total_columns ?? 0
      importData.header_row = data.header_row ?? 0

      const fields: any[] = Array.isArray(data.fields) ? data.fields : []
      importFields.value = fields.map((f: any) => ({
        ...f,
        optionsText: Array.isArray(f.options) ? f.options.join(',') : ''
      }))

      // 初始化字段全选
      importSelectedFields.value = {}
      importData.headers.forEach((_: any, idx: number) => { importSelectedFields.value[idx] = true })
      importSelectAll.value = true
      importSelectIndeterminate.value = false

      if (fields.length === 0) {
        ElMessage.warning('未能识别到有效字段，请检查表头行是否正确')
      }
    } else {
      ElMessage.warning('应用表头失败: ' + (json.message || '未知错误'))
    }
  } catch (e: any) {
    ElMessage.error('应用表头失败: ' + (e.message || '网络错误'))
  }
}

// 选择表头行
async function selectHeaderRow(rowIndex: number) {
  importHeaderRow.value = rowIndex
  await applyHeaderRow(rowIndex)
}

async function reparseWithHeaderRow() {
  // 切换表头行只需重新应用，不需要重新上传文件
  await applyHeaderRow(importHeaderRow.value)
}

async function reparseWithSheet() {
  if (!importFileRaw.value) return
  await doParseFile(importFileRaw.value, importHeaderRow.value, importSheetName.value)
}

function onImportSelectAllChange(val: boolean) {
  Object.keys(importSelectedFields.value).forEach(k => { importSelectedFields.value[Number(k)] = val })
  importSelectIndeterminate.value = false
}

function onImportFieldSelectChange() {
  const total = Object.keys(importSelectedFields.value).length
  const checked = Object.values(importSelectedFields.value).filter(Boolean).length
  importSelectAll.value = checked === total
  importSelectIndeterminate.value = checked > 0 && checked < total
}

function goToFieldAdjust() {
  // 只保留选中的字段
  const selectedIndices = Object.entries(importSelectedFields.value)
    .filter(([_, v]) => v)
    .map(([k]) => Number(k))
    .sort((a, b) => a - b)
  if (selectedIndices.length === 0) {
    ElMessage.warning('请至少选择一个字段')
    return
  }
  // 过滤 importFields 只保留选中的
  importFields.value = selectedIndices.map(idx => importFields.value[idx]).filter(Boolean)
  importStep.value = 2
}

// 导入对话框打开时获取依赖状态
function onImportDialogOpen() {
  fetchImportDependenciesStatus()
}

async function loadSampleData(type: string) {
  const sampleData: Record<string, any> = {
    supplier: {
      name: '供应商信息表',
      headers: ['供应商名称', '编码', '类型', '联系人', '联系电话', '电子邮箱', '地址', '营业执照号', '开户银行', '银行账号'],
      rows: [
        ['深圳市华强电子有限公司', 'SUP001', '原材料供应商', '张经理', '13812345601', 'zhang@hq.com', '深圳市南山区', '91440300MA5xxxx', '招商银行', '6225xxxx'],
        ['广州星河贸易有限公司', 'SUP002', '设备供应商', '李总', '13912345602', 'li@xh.com', '广州市天河区', '91440100MA5yyyy', '工商银行', '6222xxxx'],
      ]
    },
    employee: {
      name: '员工入职登记表',
      headers: ['姓名', '工号', '性别', '部门', '职位', '入职日期', '联系电话', '邮箱', '身份证号', '紧急联系人', '紧急联系电话'],
      rows: [
        ['王小明', 'EMP001', '男', '技术部', '高级工程师', '2024-03-01', '13612345610', 'wang@company.com', '440101199001011234', '王小红', '13812345611'],
        ['李丽华', 'EMP002', '女', '市场部', '市场专员', '2024-02-15', '13712345620', 'li@company.com', '440102199202022345', '李大明', '13912345621'],
      ]
    },
    customer: {
      name: '客户登记表',
      headers: ['客户名称', '客户编码', '客户类型', '客户等级', '联系人', '电话', '邮箱', '地址', '主要产品', '年销售额'],
      rows: [
        ['联想（北京）有限公司', 'CUS001', '企业客户', 'VIP客户', '陈总', '400-123-4567', 'chen@lenovo.com', '北京市海淀区', '电脑服务器', '50亿'],
        ['广州智造科技公司', 'CUS002', '企业客户', '重要客户', '刘经理', '020-88888888', 'liu@gzzz.com', '广州市开发区', '智能设备', '2亿'],
      ]
    }
  }
  const data = sampleData[type]
  if (!data) return
  importFileName.value = data.name + '.csv'
  importData.headers = data.headers
  importData.rows = data.rows
  importData.all_rows = [data.headers, ...data.rows]
  importData.total_rows = data.rows.length
  importData.total_columns = data.headers.length
  importData.sheet_names = []
  importData.current_sheet = 'Sheet1'
  importData.header_row = 0
  importHeaderRow.value = 0
  importFileRaw.value = null
  importFields.value = data.headers.map((h: string, i: number) => ({
    name: h.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 20) || 'field_' + i,
    label: h, type: inferType(h), required: false, width: '100%',
    placeholder: '', options: [], optionsText: ''
  }))
  // 初始化字段全选
  importSelectedFields.value = {}
  data.headers.forEach((_: string, idx: number) => { importSelectedFields.value[idx] = true })
  importSelectAll.value = true
  importSelectIndeterminate.value = false
  importTemplateForm.name = data.name
  importStep.value = 1
  ElMessage.success('已加载示例数据，请调整字段后继续')
}

function inferType(header: string): string {
  const h = header.toLowerCase()
  if (h.includes('金额') || h.includes('工资') || h.includes('价格') || h.includes('销售额')) return 'money'
  if (h.includes('邮箱') || h.includes('email')) return 'email'
  if (h.includes('电话') || h.includes('手机') || h.includes('固话')) return 'phone'
  if (h.includes('日期') || h.includes('时间')) return 'date'
  if (h.includes('类型') || h.includes('分类') || h.includes('等级') || h.includes('状态') || h.includes('性别')) return 'select'
  if (h.includes('网址') || h.includes('url')) return 'url'
  if (h.includes('描述') || h.includes('备注') || h.includes('地址') || h.includes('说明')) return 'textarea'
  return 'text'
}

function detectFieldTypes() {
  importFields.value.forEach(f => {
    f.type = inferType(f.label)
  })
}

async function confirmCreateTemplate() {
  if (!importTemplateForm.name.trim()) { ElMessage.warning('请输入模板名称'); return }
  importLoading.value = true
  try {
    // 构建字段数据
    const fields = importFields.value.map(({ optionsText, ...f }: any) => {
      if (['select', 'radio', 'checkbox'].includes(f.type) && optionsText) {
        f.options = optionsText.split(/[，,\n]/).map((s: string) => s.trim()).filter(Boolean)
      }
      return f
    })

    const formData = new FormData()
    formData.append('name', importTemplateForm.name)
    formData.append('description', importTemplateForm.description || '')
    formData.append('category', importTemplateForm.category || 'general')
    formData.append('fields', JSON.stringify(fields))
    formData.append('filename', importFileName.value || '示例数据')

    const res = await (window as any).fetch('/api/v1/import/create-template', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + (localStorage.getItem('kflower_token') || '') },
      body: formData
    })
    const json = await res.json()
    if (json.success) {
      ElMessage.success('模板创建成功！')
      showImport.value = false
      importStep.value = 0
      importFields.value = []
      importData.headers = []
      importData.rows = []
      importFileName.value = ''
      // 刷新列表
      templates.value.unshift({
        id: json.data.id, name: json.data.name, code: json.data.code,
        category: json.data.category, fields: fields
      })
    } else {
      ElMessage.error(json.detail || '创建失败')
    }
  } catch { ElMessage.error('创建失败') }
  finally { importLoading.value = false }
}

async function generateWithAI() {
  if (!aiPrompt.value.trim()) { ElMessage.warning('请描述您的需求'); return }
  aiLoading.value = true
  
  // 预设模板（作为后备方案）
  const presetTemplates: Record<string, any[]> = {
    '供应商': [
      { type:'text', label:'供应商名称', name:'supplier_name', required:true, width:'100%', placeholder:'请输入供应商名称' },
      { type:'text', label:'供应商编码', name:'supplier_code', required:true, width:'50%', placeholder:'请输入编码' },
      { type:'select', label:'供应商类型', name:'supplier_type', required:true, width:'50%', options:['原材料供应商','设备供应商','服务供应商','其他'] },
      { type:'divider', label:'联系方式', name:'div1', width:'100%' },
      { type:'text', label:'联系人', name:'contact_person', required:true, width:'50%', placeholder:'请输入联系人' },
      { type:'phone', label:'联系电话', name:'contact_phone', required:true, width:'50%', placeholder:'请输入手机号' },
      { type:'email', label:'电子邮箱', name:'contact_email', width:'50%', placeholder:'请输入邮箱' },
      { type:'textarea', label:'详细地址', name:'address', width:'100%', placeholder:'请输入地址' },
    ],
    '员工入职': [
      { type:'heading', label:'基本信息', name:'h1', width:'100%' },
      { type:'text', label:'姓名', name:'name', required:true, width:'50%', placeholder:'请输入姓名' },
      { type:'text', label:'工号', name:'employee_id', required:true, width:'50%', placeholder:'请输入工号' },
      { type:'select', label:'性别', name:'gender', required:true, width:'50%', options:['男','女'] },
      { type:'date', label:'入职日期', name:'join_date', required:true, width:'50%' },
      { type:'select', label:'部门', name:'department', required:true, width:'50%', options:['技术部','市场部','财务部','行政部'] },
      { type:'text', label:'职位', name:'position', required:true, width:'50%', placeholder:'请输入职位' },
      { type:'phone', label:'手机号码', name:'mobile', required:true, width:'50%', placeholder:'请输入手机号' },
      { type:'email', label:'电子邮箱', name:'email', width:'50%', placeholder:'请输入邮箱' },
    ],
    '客户': [
      { type:'text', label:'客户名称', name:'customer_name', required:true, width:'100%', placeholder:'请输入客户名称' },
      { type:'text', label:'客户编码', name:'customer_code', required:true, width:'50%', placeholder:'请输入编码' },
      { type:'select', label:'客户类型', name:'customer_type', required:true, width:'50%', options:['企业客户','个人客户','政府机构'] },
      { type:'text', label:'联系人', name:'contact_person', required:true, width:'50%', placeholder:'请输入联系人' },
      { type:'phone', label:'联系电话', name:'contact_phone', required:true, width:'50%', placeholder:'请输入手机号' },
    ],
  }
  
  try {
    // ─── 规范化系统提示词：强制 AI 只输出字段定义 JSON ───
    const systemPrompt = `你是一个专业的表单设计助手。
用户会描述他们需要的表单，你需要生成对应的表单字段定义。

【重要规则】
- 只输出 JSON 数组，绝对不要输出任何其他文字、说明、Markdown 代码块标记
- 直接以 [ 开头，以 ] 结尾

【每个字段的属性】
- type: 字段类型，只能用以下值之一：
  text textarea number date datetime time daterange
  select radio checkbox switch
  email phone url
  file image
  divider title description
- label: 字段标签（中文）
- name: 字段名称（英文小写，用下划线连接，如 student_name）
- required: 是否必填（true 或 false）
- width: 宽度（"100%" 整行 或 "50%" 半行，默认 "100%"）
- options: 当 type 为 select/radio/checkbox 时必须提供，格式为字符串数组，如 ["选项A","选项B"]
- placeholder: 占位提示文字（可选）

【输出示例】
[
  {"type":"text","label":"客户名称","name":"customer_name","required":true,"width":"100%","placeholder":"请输入客户名称"},
  {"type":"select","label":"客户类型","name":"customer_type","required":true,"width":"50%","options":["企业","个人","政府"]},
  {"type":"phone","label":"联系电话","name":"phone","required":true,"width":"50%","placeholder":"请输入手机号"},
  {"type":"date","label":"合同日期","name":"contract_date","required":false,"width":"50%"},
  {"type":"switch","label":"是否启用","name":"enabled","required":false,"width":"50%"},
  {"type":"textarea","label":"备注","name":"remark","required":false,"width":"100%","placeholder":"请输入备注"}
]`

    // 获取选中的模型信息
    const selectedModel = aiStore.models.find(m => m.modelId === selectedModelId.value)
    
    // 调用 AI API - 使用 agent/chat 接口，传入系统提示词 + 用户消息
    const response = await fetch('/api/v1/agent/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('kflower_token')
      },
      body: JSON.stringify({
        message: systemPrompt + '\n\n用户需求：' + aiPrompt.value,
        enable_tools: false,
        model: selectedModelId.value || undefined,
        provider: selectedModel?.provider || undefined
      })
    })
    
    // 处理非 JSON 响应（如错误页面）
    let result: any
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      result = await response.json()
    } else {
      const text = await response.text()
      throw new Error('服务器返回了非 JSON 响应，请检查后端日志。响应内容：' + text.slice(0, 200))
    }

    // ─── 从 AI 响应中提取 JSON ───
    if (!result.response && !result.data && !result.content) {
      throw new Error('AI 服务返回错误：' + (result.message || result.error || JSON.stringify(result)))
    }
    const aiContent: string = result.response || result.data?.content || result.content || ''
    console.log('AI 原始响应:', aiContent)

    // 去除 Markdown 代码块标记，提取 JSON 数组
    let jsonStr = aiContent.replace(/```json\s*/gi, '').replace(/```\s*/g, '').trim()
    const jsonMatch = jsonStr.match(/\[[\s\S]*\]/)
    if (!jsonMatch) {
      throw new Error('AI 未返回有效的 JSON 数组，请重试或换个描述。\n\nAI 原始回复：\n' + aiContent.slice(0, 300))
    }
    jsonStr = jsonMatch[0]

    let rawFields: any[]
    try {
      rawFields = JSON.parse(jsonStr)
    } catch (e) {
      throw new Error('JSON 解析失败，AI 输出格式有误，请重试。\n\n原始内容：\n' + jsonStr.slice(0, 300))
    }

    if (!Array.isArray(rawFields) || rawFields.length === 0) {
      throw new Error('AI 返回了空的字段数组，请重新描述需求')
    }

    // ─── 复用 normalizeFieldDef 规范化每个字段 ───
    const VALID_TYPES_AI = new Set([
      'text','textarea','number','email','phone','url','password',
      'date','datetime','time','daterange',
      'select','radio','checkbox','switch',
      'rate','slider','color','file','image',
      'divider','title','description','table','relation','formula','qrcode','signature','location','tags'
    ])
    const TYPE_MAP_AI: Record<string, string> = {
      'string':'text','input':'text','textfield':'text','varchar':'text',
      'int':'number','integer':'number','float':'number','decimal':'number',
      'bool':'switch','boolean':'switch','toggle':'switch',
      'dropdown':'select','combobox':'select',
      'upload':'file','attachment':'file','img':'image','picture':'image','photo':'image',
      'tel':'phone','mobile':'phone','memo':'textarea','remark':'textarea'
    }

    const newFields = rawFields.map((f: any, idx: number) => {
      const rawType = String(f.type || 'text').toLowerCase().trim()
      const mappedType = TYPE_MAP_AI[rawType] || rawType
      const type = VALID_TYPES_AI.has(mappedType) ? mappedType : 'text'
      const rawOpts = f.options ?? f.choices ?? null
      const options: string[] = Array.isArray(rawOpts)
        ? rawOpts.map((o: any) => typeof o === 'string' ? o : String(o.label ?? o.value ?? o))
        : typeof rawOpts === 'string' ? rawOpts.split(',').map((s: string) => s.trim()).filter(Boolean)
        : []
      return {
        type,
        label: f.label ?? f.title ?? ('字段' + (idx + 1)),
        name: f.name ?? f.key ?? ('field_' + (idx + 1)),
        required: !!(f.required ?? false),
        width: f.width || '100%',
        placeholder: f.placeholder ?? '',
        defaultValue: f.defaultValue ?? f.default ?? '',
        options,
        optionsText: options.join(','),
        min: f.min ?? undefined,
        max: f.max ?? undefined,
        _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
      }
    })

    if (currentTemplate.fields.length > 0) {
      newFields.forEach((f: any) => currentTemplate.fields.push(f))
      ElMessage.success(`AI 已追加 ${newFields.length} 个字段`)
    } else {
      currentTemplate.name = 'AI设计 - ' + aiPrompt.value.slice(0, 20)
      currentTemplate.fields = newFields
      ElMessage.success(`AI 已生成 ${newFields.length} 个字段`)
    }

    showAIHelper.value = false
    aiPrompt.value = ''
    viewMode.value = 'design'
    
  } catch (e: any) {
    console.error('AI生成失败:', e)
    ElMessage.error(e.message || 'AI生成失败')
  } finally {
    aiLoading.value = false
  }
}

// JSON 导入功能
const showJsonImport = ref(false)
const jsonInputText = ref('')

function openJsonImport() {
  jsonInputText.value = ''
  showJsonImport.value = true
}

function importFromJson() {
  if (!jsonInputText.value.trim()) {
    ElMessage.warning('请输入 JSON 内容')
    return
  }

  // ─── 系统支持的合法字段类型集合 ───
  const VALID_TYPES = new Set([
    'text', 'textarea', 'number', 'email', 'phone', 'url', 'password',
    'date', 'datetime', 'time', 'daterange',
    'select', 'radio', 'checkbox', 'switch',
    'rate', 'slider', 'color',
    'file', 'image',
    'divider', 'title', 'description',
    'table', 'relation', 'formula', 'qrcode', 'signature', 'location', 'tags'
  ])

  // ─── 外部常见类型 → 系统类型 映射 ───
  const TYPE_MAP: Record<string, string> = {
    // 文本类
    'string': 'text', 'input': 'text', 'textfield': 'text', 'varchar': 'text', 'char': 'text',
    // 多行文本
    'multiline': 'textarea', 'longtext': 'textarea', 'text_area': 'textarea',
    // 数字
    'int': 'number', 'integer': 'number', 'float': 'number', 'decimal': 'number', 'numeric': 'number',
    // 日期时间
    'datetime-local': 'datetime', 'timestamp': 'datetime',
    // 选择类
    'dropdown': 'select', 'combobox': 'select', 'multiselect': 'checkbox',
    'radiogroup': 'radio', 'radio_group': 'radio',
    'toggle': 'switch', 'bool': 'switch', 'boolean': 'switch',
    // 文件
    'upload': 'file', 'attachment': 'file', 'img': 'image', 'picture': 'image', 'photo': 'image',
    // 其他
    'tel': 'phone', 'mobile': 'phone', 'link': 'url', 'href': 'url',
    'memo': 'textarea', 'remark': 'textarea', 'note': 'textarea', 'description': 'textarea',
  }

  // ─── options 统一处理：支持字符串数组、对象数组、逗号字符串 ───
  function normalizeOptions(raw: any): string[] {
    if (!raw) return []
    if (typeof raw === 'string') {
      return raw.split(',').map((s: string) => s.trim()).filter(Boolean)
    }
    if (Array.isArray(raw)) {
      return raw.map((item: any) => {
        if (typeof item === 'string') return item
        if (typeof item === 'object' && item !== null) {
          return String(item.label ?? item.text ?? item.name ?? item.value ?? item)
        }
        return String(item)
      }).filter(Boolean)
    }
    return []
  }

  // ─── 将一个字段定义对象规范化为系统字段对象 ───
  function normalizeFieldDef(f: any, idx: number): any {
    const rawType = String(f.type || 'text').toLowerCase().trim()
    const mappedType = TYPE_MAP[rawType] || rawType
    const type = VALID_TYPES.has(mappedType) ? mappedType : 'text'

    const options = normalizeOptions(f.options ?? f.choices ?? f.items ?? f.enum ?? null)
    const optionsText = options.join(',')

    // 宽度：优先取原始值，否则默认 100%
    const width = f.width || f.col || '100%'

    return {
      type,
      label: f.label ?? f.title ?? f.display ?? f.text ?? ('字段' + (idx + 1)),
      name: f.name ?? f.key ?? f.field ?? f.id ?? ('field_' + (idx + 1)),
      required: !!(f.required ?? f.mandatory ?? false),
      width,
      placeholder: f.placeholder ?? f.hint ?? f.tip ?? '',
      defaultValue: f.defaultValue ?? f.default ?? f.value ?? '',
      options,
      optionsText,
      min: f.min ?? f.minValue ?? undefined,
      max: f.max ?? f.maxValue ?? undefined,
      _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
    }
  }

  try {
    let jsonStr = jsonInputText.value.trim()

    // 去除 markdown 代码块包裹
    const codeBlockMatch = jsonStr.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (codeBlockMatch) { jsonStr = codeBlockMatch[1].trim() }

    // 尝试提取最外层数组或对象
    const arrayMatch = jsonStr.match(/(\[[\s\S]*\]|\{[\s\S]*\})/)
    if (arrayMatch) { jsonStr = arrayMatch[0] }

    const parsed = JSON.parse(jsonStr)

    let newFields: any[] = []
    let formatHint = ''

    // ─────────────────────────────────────────────────
    // 格式一：直接数组
    // ─────────────────────────────────────────────────
    if (Array.isArray(parsed) && parsed.length > 0) {
      const first = parsed[0]

      // 判断是否是字段定义格式：元素有 type 或 label 或 name 任意一个
      const isFieldDef = first && typeof first === 'object' &&
        ('type' in first || 'label' in first || 'name' in first ||
         'title' in first || 'key' in first || 'field' in first)

      if (isFieldDef) {
        // ── 字段定义格式 ──
        newFields = parsed.map((f: any, idx: number) => normalizeFieldDef(f, idx))
        formatHint = '字段定义格式'
      } else {
        // ── 数据记录格式：从样本中推断字段类型 ──
        const allKeys = new Set<string>()
        parsed.forEach((record: any) => {
          if (record && typeof record === 'object' && !Array.isArray(record)) {
            Object.keys(record).forEach(key => allKeys.add(key))
          }
        })

        if (allKeys.size === 0) {
          ElMessage.error('无法从数组元素中识别出字段')
          return
        }

        const keyList = Array.from(allKeys)
        const samples = parsed.slice(0, 10)

        const cnNameMap: Record<string, string> = {
          '会议主题': 'meeting_topic', '会议时间': 'meeting_time', '会议地点': 'meeting_location',
          '参与人员': 'participants', '主持人': 'host', '记录人': 'recorder',
          '议程': 'agenda', '讨论内容': 'discussion', '决议事项': 'resolutions',
          '后续行动': 'follow_up', '负责人': 'responsible', '截止日期': 'deadline',
          '备注': 'remark', '客户名称': 'customer_name', '联系人': 'contact_person',
          '联系电话': 'contact_phone', '供应商名称': 'supplier_name',
          '员工姓名': 'employee_name', '部门': 'department', '职位': 'position',
          '入职日期': 'join_date', '请假类型': 'leave_type', '开始日期': 'start_date',
          '结束日期': 'end_date', '请假原因': 'reason', '申请人': 'applicant',
          '申请日期': 'apply_date', '审批人': 'approver', '审批状态': 'status',
          '审批意见': 'comment', '费用类型': 'expense_type', '金额': 'amount',
          '事由': 'description', '出差地点': 'destination', '交通工具': 'transportation',
          '出差任务': 'mission',
        }

        newFields = keyList.map((key: string) => {
          const sampleValues = samples
            .map((r: any) => r[key])
            .filter((v: any) => v !== undefined && v !== null && v !== '')

          let type = 'text'
          if (sampleValues.length > 0) {
            const s = String(sampleValues[0]).trim()
            if (typeof sampleValues[0] === 'boolean') type = 'switch'
            else if (typeof sampleValues[0] === 'number') type = 'number'
            else if (/^\d{4}-\d{2}-\d{2}$/.test(s)) type = 'date'
            else if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/.test(s)) type = 'datetime'
            else if (/^\d{2}:\d{2}$/.test(s)) type = 'time'
            else if (/^1[3-9]\d{9}$/.test(s)) type = 'phone'
            else if (/^[\w.-]+@[\w.-]+\.\w+$/.test(s)) type = 'email'
            else if (s.includes('\n') || s.length > 80) type = 'textarea'
            else if (s.length <= 20) {
              const uniq = [...new Set(sampleValues.map((v: any) => String(v)))]
              if (uniq.length >= 2 && uniq.length <= 6) type = 'radio'
            }
          }

          const rawName = cnNameMap[key] ||
            key.replace(/[^\w]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '').toLowerCase()
          const name = rawName || 'field_' + Math.random().toString(36).slice(2, 6)

          const isEnum = type === 'radio' || type === 'select'
          const uniqueVals = [...new Set(sampleValues.map((v: any) => String(v)))]

          return {
            type, label: key, name,
            required: false, width: '100%',
            placeholder: '',
            options: isEnum ? uniqueVals : [],
            optionsText: isEnum ? uniqueVals.join(',') : '',
            _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
          }
        })
        formatHint = '数据记录格式（' + parsed.length + ' 条）'
      }

    // ─────────────────────────────────────────────────
    // 格式二：对象包裹，如 { fields: [...] } / { columns: [...] } / { schema: [...] }
    // ─────────────────────────────────────────────────
    } else if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      const wrapKey = ['fields', 'columns', 'schema', 'items', 'properties', 'list', 'data']
        .find(k => Array.isArray(parsed[k]))

      if (wrapKey) {
        const arr = parsed[wrapKey]
        // 检查 properties 是对象格式（JSON Schema 风格）
        if (wrapKey === 'properties') {
          newFields = Object.entries(arr).map(([key, val]: [string, any], idx) => {
            const f = { type: val.type, label: val.title || key, name: key, ...val }
            return normalizeFieldDef(f, idx)
          })
        } else {
          newFields = arr.map((f: any, idx: number) => normalizeFieldDef(f, idx))
        }
        formatHint = `对象包裹格式（${wrapKey}）`
      } else if (parsed.properties && typeof parsed.properties === 'object') {
        // JSON Schema 风格
        newFields = Object.entries(parsed.properties).map(([key, val]: [string, any], idx) => {
          const f = { type: val.type, label: val.title || key, name: key, ...val }
          return normalizeFieldDef(f, idx)
        })
        formatHint = 'JSON Schema 格式'
      } else {
        // 把单个对象的 key 视为字段
        newFields = Object.entries(parsed).map(([key, val]: [string, any], idx) => ({
          type: 'text', label: key,
          name: key.replace(/[^\w]/g, '_').toLowerCase() || ('field_' + idx),
          required: false, width: '100%',
          placeholder: '', options: [], optionsText: '',
          defaultValue: typeof val === 'string' || typeof val === 'number' ? String(val) : '',
          _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2)
        }))
        formatHint = '单条记录对象格式'
      }
    } else {
      ElMessage.error('JSON 格式无法识别，请检查输入内容')
      return
    }

    if (newFields.length === 0) {
      ElMessage.error('未能识别出任何字段，请检查 JSON 内容')
      return
    }

    // ─── 合并或替换 ───
    if (currentTemplate.fields.length > 0) {
      newFields.forEach((f: any) => currentTemplate.fields.push(f))
      ElMessage.success(`已追加 ${newFields.length} 个字段（${formatHint}）`)
    } else {
      currentTemplate.name = 'JSON导入模板'
      currentTemplate.fields = newFields
      ElMessage.success(`已导入 ${newFields.length} 个字段（${formatHint}）`)
    }

    showJsonImport.value = false
    jsonInputText.value = ''
    if (viewMode.value === 'list') { viewMode.value = 'design' }

  } catch (e: any) {
    ElMessage.error('JSON 解析失败：' + (e.message || String(e)))
  }
}


// ========== 数据提交和管理功能 ==========

function getTemplateFields(t: any): any[] {
  let fields: any[] = []
  if (t.modules && Array.isArray(t.modules)) {
    for (const mod of t.modules) {
      if (mod.fields && Array.isArray(mod.fields)) {
        fields = fields.concat(mod.fields)
      }
    }
  }
  return fields
}

// 打开表单填写页（从列表操作列点击"填表"）
function openFormSubmit(t: any) {
  openDataForm(t)
}

function openDataForm(t: any) {
  dataFormTemplate.value = t
  dataFormFields.value = getTemplateFields(t)
  // 初始化表单数据
  Object.keys(dataFormData).forEach(k => delete dataFormData[k])
  dataFormFields.value.forEach(f => {
    if (f.type === 'checkbox') {
      dataFormData[f.name] = []
    } else if (f.type === 'switch') {
      dataFormData[f.name] = false
    } else if (f.type === 'rate') {
      dataFormData[f.name] = 0
    } else if (f.type === 'slider') {
      dataFormData[f.name] = f.min || 0
    } else {
      dataFormData[f.name] = f.defaultValue || ''
    }
  })
  showDataForm.value = true
}

async function submitDataForm() {
  if (!dataFormTemplate.value) return
  // 验证必填字段
  for (const f of dataFormFields.value) {
    if (f.required) {
      const val = dataFormData[f.name]
      if (!val || (Array.isArray(val) && val.length === 0)) {
        ElMessage.warning(`请填写必填字段「${f.label}」`)
        return
      }
    }
  }
  dataFormLoading.value = true
  try {
    await templateAPI.submitData(dataFormTemplate.value.id, { ...dataFormData })
    ElMessage.success('数据提交成功！')
    showDataForm.value = false
    // 如果数据管理窗口打开，刷新列表
    if (showDataManager.value) loadDataList()
  } catch (e: any) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally { dataFormLoading.value = false }
}

function openDataManager(t: any) {
  dataManagerTemplate.value = t
  dataManagerFields.value = getTemplateFields(t)
  dataSearchText.value = ''
  dataPage.value = 1
  dataPageSize.value = 20
  dataList.value = []
  dataStats.value = null
  showDataManager.value = true
  loadDataList()
  loadStats()
}

function debounceDataSearch() {
  clearTimeout(dataSearchTimer)
  dataSearchTimer = setTimeout(() => { dataPage.value = 1; loadDataList() }, 400)
}

async function loadDataList() {
  if (!dataManagerTemplate.value) return
  dataListLoading.value = true
  try {
    const skip = (dataPage.value - 1) * dataPageSize.value
    const res: any = await templateAPI.getData(dataManagerTemplate.value.id, {
      skip, limit: dataPageSize.value, search: dataSearchText.value || undefined
    })
    const items = Array.isArray(res) ? res : (res.items || [])
    // 展开config.data到顶层
    dataList.value = items.map((item: any) => ({
      id: item.id,
      template_id: item.template_id,
      name: item.name,
      created_by: item.created_by,
      created_at: item.created_at,
      updated_at: item.updated_at,
      ...(item.config?.data || {})
    }))
    // 获取总数
    const countRes: any = await templateAPI.getDataCount(dataManagerTemplate.value.id)
    dataTotal.value = countRes?.total || items.length
  } catch { dataList.value = [] }
  finally { dataListLoading.value = false }
}

async function loadStats() {
  if (!dataManagerTemplate.value) return
  try {
    const res: any = await templateAPI.getStats(dataManagerTemplate.value.id)
    dataStats.value = res
  } catch { dataStats.value = null }
}

function getDisplayValue(row: any, f: any): string {
  const val = row[f.name]
  if (val === null || val === undefined) return '-'
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}

function getFieldLabel(fieldName: string): string {
  const f = dataManagerFields.value.find(f => f.name === fieldName)
  return f?.label || fieldName
}

function formatDateTime(s: string|null): string {
  if (!s) return '-'
  const d = new Date(s)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function onDataSelectionChange(rows: any[]) {
  dataSelectedRows.value = rows
}

function viewDataDetail(row: any) {
  dataDetailIsEdit.value = false
  dataDetailId.value = row.id
  Object.keys(dataDetailData).forEach(k => delete dataDetailData[k])
  dataManagerFields.value.forEach(f => {
    dataDetailData[f.name] = row[f.name] ?? (f.type === 'checkbox' ? [] : '')
  })
  showDataDetail.value = true
}

function editDataItem(row: any) {
  dataDetailIsEdit.value = true
  dataDetailId.value = row.id
  Object.keys(dataDetailData).forEach(k => delete dataDetailData[k])
  dataManagerFields.value.forEach(f => {
    dataDetailData[f.name] = row[f.name] ?? (f.type === 'checkbox' ? [] : f.type === 'switch' ? false : '')
  })
  showDataDetail.value = true
}

async function saveDataDetail() {
  if (!dataManagerTemplate.value || !dataDetailId.value) return
  dataDetailSaving.value = true
  try {
    await templateAPI.updateData(dataManagerTemplate.value.id, dataDetailId.value, { ...dataDetailData })
    ElMessage.success('数据已更新')
    showDataDetail.value = false
    loadDataList()
    loadStats()
  } catch (e: any) {
    ElMessage.error('更新失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
  } finally { dataDetailSaving.value = false }
}

async function deleteDataItem(row: any) {
  if (!dataManagerTemplate.value) return
  try {
    await ElMessageBox.confirm('确定删除该条数据？', '删除确认', { type: 'warning' })
    await templateAPI.deleteData(dataManagerTemplate.value.id, row.id)
    ElMessage.success('数据已删除')
    loadDataList()
    loadStats()
  } catch {}
}

function exportDataCSV() {
  if (dataList.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const fields = dataManagerFields.value
  const headers = fields.map(f => f.label).join(',')
  const rows = dataList.value.map(row => fields.map(f => {
    let val = row[f.name] ?? ''
    if (Array.isArray(val)) val = val.join(';')
    // 处理CSV中的逗号和换行
    val = String(val).replace(/"/g, '""')
    if (String(val).includes(',') || String(val).includes('\n') || String(val).includes('"')) {
      val = `"${val}"`
    }
    return val
  }).join(','))
  const csv = '\uFEFF' + headers + '\n' + rows.join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${dataManagerTemplate.value?.name || 'data'}_export.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 处理路由参数，加载模板进入设计器
async function handleRouteParams() {
  const { view, edit, create } = route.query
  
  if (view || edit) {
    // 从工作区或其他页面跳转来编辑/查看模板
    const templateId = Number(view || edit)
    if (templateId) {
      try {
        const res: any = await templateAPI.get(templateId)
        if (res && res.id) {
          openDesigner(res)
          // 清除 URL 参数
          router.replace('/templates')
        }
      } catch (e) {
        ElMessage.error('加载模板失败')
      }
    }
  } else if (create === 'new') {
    // 新建模板
    openCreateDialog()
    router.replace('/templates')
  }
}

onMounted(async () => {
  await loadTemplates()
  await handleRouteParams()
})


</script>

<style scoped lang="scss">
.template-page { height: 100%; display: flex; flex-direction: column; background: #f5f7fa; }
.list-view { padding: 20px; flex: 1; overflow-y: auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
  .header-left { display: flex; align-items: center; gap: 12px; h2 { margin: 0; } }
  .header-right { display: flex; gap: 10px; }
}
.category-filter { margin-bottom: 16px; }
.loading-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.template-table-wrapper { background: white; border-radius: 8px; padding: 16px;
  .table-name-cell { display: flex; align-items: center; gap: 10px; }
  .table-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
  .table-name-text { font-weight: 500; color: #303133; }
  .table-code-text { font-size: 12px; color: #909399; }
  .field-count-num { font-weight: 600; color: #409EFF; }
  .template-id-text { font-family: monospace; color: #909399; font-size: 12px; }
  .el-table__row { cursor: pointer; &:hover > td { background-color: #f5f7fa !important; } }
}
.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.template-card { cursor: pointer; transition: all 0.2s;
  &:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  .card-header { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
  .card-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
  .card-title { flex: 1; min-width: 0;
    h4 { margin: 0 0 4px; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .card-code { font-size: 11px; color: #aaa; font-family: monospace; }
  }
  .card-desc { margin: 0 0 10px; font-size: 13px; color: #666; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .card-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #999;
    .field-count { display: flex; align-items: center; gap: 4px; margin-left: auto; }
    .create-time { color: #bbb; }
  }
}
.designer-view { display: flex; flex-direction: column; height: calc(100vh - 60px); }
.designer-toolbar { display: flex; align-items: center; gap: 10px; padding: 10px 16px; background: white; border-bottom: 1px solid #e6e6e6; flex-shrink: 0;
  .toolbar-left, .toolbar-center, .toolbar-right { display: flex; align-items: center; gap: 8px; }
  .toolbar-center { flex: 1; justify-content: center; }
  .toolbar-right { margin-left: auto; }
}
.designer-body { display: flex; flex: 1; overflow: hidden; }
.field-toolbox { width: 200px; background: white; border-right: 1px solid #e6e6e6; overflow-y: auto; flex-shrink: 0;
  :deep(.el-collapse-item__header) { padding: 0 12px; font-size: 13px; font-weight: 600; }
  :deep(.el-collapse-item__content) { padding: 0 8px 8px; }
}
.toolbox-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.toolbox-item { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 4px; background: #f5f7fa; border: 1px solid #e4e7ed; border-radius: 6px; cursor: move; font-size: 12px; transition: all 0.2s;
  &:hover { border-color: #409eff; background: #ecf5ff; color: #409eff; }
}
.form-canvas { flex: 1; padding: 20px; overflow-y: auto; background: #fafafa;
  background-image: linear-gradient(#eee 1px, transparent 1px), linear-gradient(90deg, #eee 1px, transparent 1px);
  background-size: 20px 20px;
}
.canvas-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #aaa; text-align: center;
  .empty-icon { margin-bottom: 12px; color: #d0d0d0; }
  h4 { margin: 0 0 8px; }
}
.canvas-fields { max-width: 800px; margin: 0 auto; }
.canvas-field { display: flex; align-items: center; gap: 8px; background: white; border: 2px solid #e6e6e6; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; cursor: pointer; transition: all 0.15s;
  &:hover { border-color: #b0d4f1; }
  &.selected { border-color: #409EFF; background: #f0f7ff; box-shadow: 0 0 0 2px rgba(64,158,255,0.15); }
  .field-handle { color: #ccc; cursor: grab; flex-shrink: 0; }
  .field-body { flex: 1; min-width: 0; }
  .field-header { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 4px; }
  .required-mark { color: #f56c6c; font-size: 16px; }
  .field-preview { .preview-input { width: 100%; padding: 6px 10px; border: 1px solid #dcdfe6; border-radius: 4px; background: #f5f5f5; color: #999; font-size: 13px; } }
  .field-meta { font-size: 11px; color: #aaa; margin-top: 4px; code { background: #f5f5f5; padding: 1px 4px; border-radius: 2px; font-family: monospace; } }
  .field-actions { display: flex; gap: 2px; flex-shrink: 0; }
}
.property-panel { width: 280px; background: white; border-left: 1px solid #e6e6e6; display: flex; flex-direction: column; flex-shrink: 0;
  .panel-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #e6e6e6;
    h4 { margin: 0; font-size: 14px; }
  }
  .panel-body { flex: 1; overflow-y: auto; padding: 12px; }
}
/* 导入弹窗样式 */
.import-container { min-height: 300px; }
.import-uploader { width: 100%; margin-bottom: 16px; }
.upload-icon { font-size: 48px; color: #409eff; margin-bottom: 12px; }
.upload-text p { margin: 4px 0; }
.upload-hint { font-size: 12px; color: #999; }
.upload-examples { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }
.upload-examples .el-tag { cursor: pointer; }
/* 导入依赖状态提示 */
.import-deps-status {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
}
.import-deps-status .deps-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.import-deps-status .deps-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}
.import-deps-status .dep-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}
.import-deps-status .dep-item.ok {
  color: #67c23a;
  background: #f0f9eb;
}
.import-deps-status .dep-item.warn {
  color: #e6a23c;
  background: #fdf6ec;
}
.import-deps-status .dep-item.error {
  color: #f56c6c;
  background: #fef0f0;
}
.import-deps-status .deps-tip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.preview-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.field-adjust-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.step-actions { display: flex; justify-content: center; gap: 12px; margin-top: 20px; }
.summary-info { margin: 16px 0; }

.ai-examples { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  .example-tag { cursor: pointer; &:hover { opacity: 0.8; } }
}

/* 数据管理样式 */
.data-manager { }
.data-manager-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
  .toolbar-left { display: flex; align-items: center; gap: 10px; }
  .toolbar-right { display: flex; gap: 8px; }
}
.data-pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
.data-stats { margin-top: 20px; padding-top: 16px; border-top: 1px solid #eee;
  h4 { margin: 0 0 12px; font-size: 14px; }
  .field-stat { margin: 6px 0; font-size: 13px; color: #555; }
}

/* 导入预览控制 */
.preview-controls { margin-top: 12px; padding: 12px; background: #f5f7fa; border-radius: 6px; }
.control-row { display: flex; align-items: center; gap: 8px; }
.field-checkboxes { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; max-height: 120px; overflow-y: auto; }

/* 数据管理样式 */
.data-mgr-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; }
.data-stats-bar { display: flex; gap: 10px; margin-bottom: 12px; }
.data-pagination { display: flex; justify-content: flex-end; margin-top: 12px; }
.data-summary { font-size: 12px; color: #666; }
.stats-content h4 { color: #303133; }

/* 权限设置样式 */
.permission-section {
  margin: 20px 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    color: #303133;
  }
  .el-radio-group {
    display: flex;
    gap: 16px;
  }
  .user-selector {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .selected-users {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      .el-tag {
        margin: 2px;
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
    
    .user-search {
      .search-hint {
        font-size: 12px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }
}
</style>
