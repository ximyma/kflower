# -*- coding: utf-8 -*-
"""
Complete WorkFine-style Template Designer
"""
import os

path = r'D:\kflower\kflower-frontend\src\common\pc\views\Templates.vue'

# Field types definition - 30+ types matching WorkFine
FIELD_TYPES = '''
// ===== 基础控件 =====
{ type: 'text',      label: '单行文本',    icon: 'Edit',           category: 'basic' },
{ type: 'textarea',  label: '多行文本',    icon: 'Document',       category: 'basic' },
{ type: 'number',    label: '数字',        icon: 'Minus',          category: 'basic' },
{ type: 'password',  label: '密码',       icon: 'Lock',           category: 'basic' },
{ type: 'email',     label: '邮箱',        icon: 'Message',        category: 'basic' },
{ type: 'phone',     label: '电话',        icon: 'Phone',          category: 'basic' },
{ type: 'url',       label: '网址',        icon: 'Link',           category: 'basic' },

// ===== 日期时间 =====
{ type: 'date',      label: '日期',        icon: 'Calendar',       category: 'datetime' },
{ type: 'datetime',  label: '日期时间',    icon: 'Timer',          category: 'datetime' },
{ type: 'time',      label: '时间',        icon: 'Alarm',          category: 'datetime' },
{ type: 'daterange', label: '日期范围',    icon: 'DateRange',      category: 'datetime' },

// ===== 选择控件 =====
{ type: 'select',    label: '下拉选择',    icon: 'ArrowDown',      category: 'select' },
{ type: 'cascader',  label: '级联选择',    icon: 'Share',          category: 'select' },
{ type: 'radio',     label: '单选',        icon: 'Pointer',        category: 'select' },
{ type: 'checkbox',  label: '多选',        icon: 'Finished',        category: 'select' },
{ type: 'switch',    label: '开关',        icon: 'Open',           category: 'select' },
{ type: 'slider',    label: '滑块',        icon: 'Operation',      category: 'select' },
{ type: 'rate',      label: '评分',        icon: 'Star',           category: 'select' },

// ===== 高级控件 =====
{ type: 'richtext',  label: '富文本',      icon: 'Notebook',       category: 'advanced' },
{ type: 'upload',    label: '文件上传',    icon: 'Upload',         category: 'advanced' },
{ type: 'image',     label: '图片上传',    icon: 'Picture',        category: 'advanced' },
{ type: 'signature', label: '签名',        icon: 'EditPen',        category: 'advanced' },
{ type: 'barcode',   label: '条码',        icon: 'Grid',           category: 'advanced' },
{ type: 'qrcode',    label: '二维码',      icon: 'Grid',           category: 'advanced' },

// ===== 布局控件 =====
{ type: 'divider',   label: '分隔线',      icon: 'Minus',          category: 'layout' },
{ type: 'heading',   label: '标题',        icon: 'Title',          category: 'layout' },
{ type: 'group',     label: '分组',        icon: 'Folder',         category: 'layout' },
{ type: 'grid',      label: '栅格布局',    icon: 'Grid',           category: 'layout' },
{ type: 'tabs',      label: '标签页',      icon: 'FolderOpened',   category: 'layout' },

// ===== 数据控件 =====
{ type: 'subform',   label: '子表单',      icon: 'List',           category: 'data' },
{ type: 'relation',  label: '关联数据',    icon: 'Connection',     category: 'data' },
{ type: 'refdata',   label: '数据引用',    icon: 'DataLine',        category: 'data' },
{ type: 'autonum',   label: '自动编号',    icon: 'Ticket',         category: 'data' },

// ===== 特殊控件 =====
{ type: 'location',  label: '地图位置',    icon: 'Location',       category: 'special' },
{ type: 'color',     label: '颜色选择',    icon: 'Brush',          category: 'special' },
{ type: 'icon',      label: '图标选择',    icon: 'PictureFilled',  category: 'special' },
{ type: 'user',      label: '人员选择',    icon: 'User',           category: 'special' },
{ type: 'org',       label: '部门选择',    icon: 'OfficeBuilding',  category: 'special' },
'''

content = '''<template>
  <div class="template-page">

    <!-- ========== 列表视图 ========== -->
    <div v-if="viewMode === 'list'" class="list-view">

      <!-- 顶部操作栏 -->
      <div class="page-header">
        <div class="header-left">
          <h2>模板设计</h2>
          <el-tag type="info">{{ templates.length }} 个模板</el-tag>
        </div>
        <div class="header-right">
          <el-input v-model="searchText" placeholder="搜索模板..." clearable style="width:260px" @input="debounceSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button @click="showAIHelper = true">
            <el-icon><MagicStick /></el-icon> AI 智能设计
          </el-button>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 新建模板
          </el-button>
        </div>
      </div>

      <!-- 分类筛选 -->
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

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-grid">
        <el-card v-for="i in 6" :key="i" shadow="hover" class="template-card-skeleton">
          <el-skeleton :rows="4" animated />
        </el-card>
      </div>

      <!-- 空状态 -->
      <el-empty v-else-if="filteredTemplates.length === 0" description="暂无模板，点击新建开始设计">
        <el-button type="primary" @click="openCreateDialog">新建模板</el-button>
      </el-empty>

      <!-- 模板卡片网格 -->
      <div v-else class="template-grid">
        <el-card v-for="t in filteredTemplates" :key="t.id" shadow="hover" class="template-card" @click="openDesigner(t)">
          <div class="card-header">
            <div class="card-icon" :style="{background: getCategoryColor(t.category)}">
              <el-icon :size="24"><component :is="getCategoryIcon(t.category)" /></el-icon>
            </div>
            <div class="card-title">
              <h4>{{ t.name }}</h4>
              <span class="card-code">{{ t.code || '无编码' }}</span>
            </div>
            <el-dropdown trigger="click" @click.stop>
              <el-button text><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click.stop="openDesigner(t)"><el-icon><SetUp /></el-icon> 设计</el-dropdown-item>
                  <el-dropdown-item @click.stop="openEditDialog(t)"><el-icon><Edit /></el-icon> 编辑</el-dropdown-item>
                  <el-dropdown-item @click.stop="duplicateTemplate(t)"><el-icon><CopyDocument /></el-icon> 复制</el-dropdown-item>
                  <el-dropdown-item @click.stop="exportTemplate(t)"><el-icon><Download /></el-icon> 导出</el-dropdown-item>
                  <el-dropdown-item divided @click.stop="deleteTemplate(t)"><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <p class="card-desc">{{ t.description || '暂无描述' }}</p>
          <div class="card-meta">
            <el-tag size="small" :type="getCategoryTagType(t.category)">{{ getCategoryLabel(t.category) }}</el-tag>
            <span class="field-count"><el-icon><List /></el-icon> {{ countFields(t.fields) }} 字段</span>
            <span class="create-time">{{ formatDateShort(t.created_at) }}</span>
          </div>
          <div class="card-stats">
            <span><el-icon><Document /></el-icon> {{ t.instance_count || 0 }} 条数据</span>
          </div>
        </el-card>
      </div>
    </div>

    <!-- ========== 设计器视图 ========== -->
    <div v-else class="designer-view">

      <!-- 设计器工具栏 -->
      <div class="designer-toolbar">
        <div class="toolbar-left">
          <el-button text @click="viewMode = 'list'"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
          <el-divider direction="vertical" />
          <el-input v-model="currentTemplate.name" placeholder="模板名称" style="width:200px">
            <template #prefix><el-icon><Document /></el-icon></template>
          </el-input>
          <el-input v-model="currentTemplate.code" placeholder="模板编码" style="width:150px" />
        </div>
        <div class="toolbar-center">
          <el-select v-model="currentTemplate.category" placeholder="选择分类" style="width:130px">
            <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
          <el-input v-model="currentTemplate.description" placeholder="模板描述" style="width:250px" />
        </div>
        <div class="toolbar-right">
          <el-button @click="previewTemplate"><el-icon><View /></el-icon> 预览</el-button>
          <el-button @click="saveTemplate" type="primary"><el-icon><Select /></el-icon> 保存</el-button>
        </div>
      </div>

      <!-- 设计器主体 -->
      <div class="designer-body">

        <!-- 左侧：字段工具箱 -->
        <div class="field-toolbox">
          <el-collapse v-model="toolboxExpanded">
            <el-collapse-item title="基础控件" name="basic">
              <div class="toolbox-grid">
                <div v-for="ft in basicFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="日期时间" name="datetime">
              <div class="toolbox-grid">
                <div v-for="ft in datetimeFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="选择控件" name="select">
              <div class="toolbox-grid">
                <div v-for="ft in selectFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="高级控件" name="advanced">
              <div class="toolbox-grid">
                <div v-for="ft in advancedFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="布局控件" name="layout">
              <div class="toolbox-grid">
                <div v-for="ft in layoutFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="数据控件" name="data">
              <div class="toolbox-grid">
                <div v-for="ft in dataFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item title="特殊控件" name="special">
              <div class="toolbox-grid">
                <div v-for="ft in specialFields" :key="ft.type"
                  class="toolbox-item"
                  draggable="true"
                  @dragstart="onDragStart($event, ft)">
                  <el-icon :size="18"><component :is="ft.icon" /></el-icon>
                  <span>{{ ft.label }}</span>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 中间：表单画布 -->
        <div class="form-canvas" ref="canvasRef"
          @dragover.prevent
          @drop="onDrop"
          @click.self="selectedField = null">

          <!-- 空状态提示 -->
          <div v-if="currentTemplate.fields.length === 0" class="canvas-empty">
            <el-icon :size="64" class="empty-icon"><SetUp /></el-icon>
            <h4>开始设计您的表单</h4>
            <p>从左侧拖拽字段到这里，或点击「AI 智能设计」自动生成</p>
            <div class="empty-actions">
              <el-button type="primary" @click="showAIHelper = true">
                <el-icon><MagicStick /></el-icon> AI 智能设计
              </el-button>
            </div>
          </div>

          <!-- 字段列表 -->
          <div v-else class="canvas-fields">
            <div v-for="(field, idx) in currentTemplate.fields" :key="field._key"
              class="canvas-field"
              :class="{selected: selectedField === idx, dragging: dragIdx === idx}"
              draggable="true"
              @click.stop="selectedField = idx"
              @dragstart="onFieldDragStart($event, idx)"
              @dragover.prevent
              @drop="onFieldDrop($event, idx)">

              <!-- 拖拽手柄 -->
              <div class="field-handle">
                <el-icon><Rank /></el-icon>
              </div>

              <!-- 字段内容 -->
              <div class="field-body">
                <div class="field-header">
                  <el-tag size="small" :type="getFieldTypeStyle(field.type)">
                    {{ getFieldTypeLabel(field.type) }}
                  </el-tag>
                  <span class="field-label">{{ field.label || '未命名' }}</span>
                  <span v-if="field.required" class="required-mark">*</span>
                </div>
                <div class="field-preview">
                  <component :is="getFieldPreview(field)" :field="field" disabled />
                </div>
                <div class="field-meta">
                  字段名: <code>{{ field.name }}</code>
                  <span v-if="field.placeholder"> | 占位: {{ field.placeholder }}</span>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="field-actions">
                <el-button size="small" text @click.stop="copyField(idx)" title="复制">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
                <el-button size="small" text @click.stop="moveField(idx, -1)" :disabled="idx === 0" title="上移">
                  <el-icon><ArrowUp /></el-icon>
                </el-button>
                <el-button size="small" text @click.stop="moveField(idx, 1)" :disabled="idx === currentTemplate.fields.length - 1" title="下移">
                  <el-icon><ArrowDown /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="removeField(idx)" title="删除">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：属性配置面板 -->
        <div class="property-panel">
          <template v-if="selectedField !== null && currentTemplate.fields[selectedField]">
            <div class="panel-header">
              <h4>字段属性</h4>
              <el-button text size="small" @click="selectedField = null">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-scrollbar class="panel-body">
              <el-form label-position="top" size="small">
                <el-form-item label="显示名称">
                  <el-input v-model="currentTemplate.fields[selectedField].label" placeholder="字段显示名称" />
                </el-form-item>
                <el-form-item label="字段标识（英文）">
                  <el-input v-model="currentTemplate.fields[selectedField].name" placeholder="如: user_name">
                    <template #append>
                      <el-button @click="autoFieldName">自动</el-button>
                    </template>
                  </el-input>
                </el-form-item>
                <el-form-item label="占位提示">
                  <el-input v-model="currentTemplate.fields[selectedField].placeholder" placeholder="输入框提示文字" />
                </el-form-item>
                <el-form-item label="帮助说明">
                  <el-input v-model="currentTemplate.fields[selectedField].help" placeholder="字段说明文字" />
                </el-form-item>
                <el-form-item label="默认值">
                  <el-input v-model="currentTemplate.fields[selectedField].defaultValue" placeholder="默认填充值" />
                </el-form-item>
                <el-form-item label="字段宽度">
                  <el-radio-group v-model="currentTemplate.fields[selectedField].width">
                    <el-radio label="100%">整行</el-radio>
                    <el-radio label="50%">半行</el-radio>
                    <el-radio label="33%">三分之一</el-radio>
                    <el-radio label="25%">四分之一</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="必填">
                  <el-switch v-model="currentTemplate.fields[selectedField].required" />
                </el-form-item>
                <el-form-item label="只读">
                  <el-switch v-model="currentTemplate.fields[selectedField].readonly" />
                </el-form-item>
                <el-form-item label="隐藏">
                  <el-switch v-model="currentTemplate.fields[selectedField].hidden" />
                </el-form-item>

                <!-- 数字类型特有属性 -->
                <template v-if="['number','rate','slider'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>数值设置</el-divider>
                  <el-form-item label="最小值">
                    <el-input-number v-model="currentTemplate.fields[selectedField].min" :step="1" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="最大值">
                    <el-input-number v-model="currentTemplate.fields[selectedField].max" :step="1" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="步长">
                    <el-input-number v-model="currentTemplate.fields[selectedField].step" :min="0.1" :step="0.1" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="精度（小数位）">
                    <el-input-number v-model="currentTemplate.fields[selectedField].precision" :min="0" :max="6" style="width:100%" />
                  </el-form-item>
                </template>

                <!-- 文本类型特有属性 -->
                <template v-if="['text','textarea','password','email','phone','url'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>文本设置</el-divider>
                  <el-form-item label="最大长度">
                    <el-input-number v-model="currentTemplate.fields[selectedField].maxLength" :min="1" :max="1000" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="正则验证">
                    <el-input v-model="currentTemplate.fields[selectedField].pattern" placeholder="如: ^[A-Za-z]+$" />
                  </el-form-item>
                  <el-form-item label="验证提示">
                    <el-input v-model="currentTemplate.fields[selectedField].patternMsg" placeholder="验证失败时的提示" />
                  </el-form-item>
                </template>

                <!-- 选项类型特有属性 -->
                <template v-if="['select','radio','checkbox','cascader'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>选项设置</el-divider>
                  <el-form-item label="选项列表">
                    <el-input v-model="currentTemplate.fields[selectedField].optionsText"
                      type="textarea" :rows="4"
                      placeholder="每行一个选项，或用逗号分隔"
                      @blur="applyOptions" />
                  </el-form-item>
                  <el-form-item label="数据源">
                    <el-select v-model="currentTemplate.fields[selectedField].dataSource" placeholder="选择数据源" clearable style="width:100%">
                      <el-option label="静态选项" value="static" />
                      <el-option label="API接口" value="api" />
                      <el-option label="数据表" value="table" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="API地址" v-if="currentTemplate.fields[selectedField].dataSource === 'api'">
                    <el-input v-model="currentTemplate.fields[selectedField].apiUrl" placeholder="选项数据API" />
                  </el-form-item>
                </template>

                <!-- 日期类型特有属性 -->
                <template v-if="['date','datetime','time','daterange'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>日期设置</el-divider>
                  <el-form-item label="日期格式">
                    <el-select v-model="currentTemplate.fields[selectedField].format" style="width:100%">
                      <el-option label="YYYY-MM-DD" value="YYYY-MM-DD" />
                      <el-option label="YYYY/MM/DD" value="YYYY/MM/DD" />
                      <el-option label="YYYY年MM月DD日" value="YYYY年MM月DD日" />
                      <el-option label="MM-DD-YYYY" value="MM-DD-YYYY" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="禁用未来日期">
                    <el-switch v-model="currentTemplate.fields[selectedField].disableFuture" />
                  </el-form-item>
                  <el-form-item label="禁用历史日期">
                    <el-switch v-model="currentTemplate.fields[selectedField].disablePast" />
                  </el-form-item>
                </template>

                <!-- 文件上传特有属性 -->
                <template v-if="['upload','image'].includes(currentTemplate.fields[selectedField].type)">
                  <el-divider>上传设置</el-divider>
                  <el-form-item label="最大文件数">
                    <el-input-number v-model="currentTemplate.fields[selectedField].limit" :min="1" :max="10" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="文件大小限制(MB)">
                    <el-input-number v-model="currentTemplate.fields[selectedField].maxSize" :min="1" :max="100" style="width:100%" />
                  </el-form-item>
                  <el-form-item label="允许类型">
                    <el-input v-model="currentTemplate.fields[selectedField].accept" placeholder="如: .jpg,.png,.pdf" />
                  </el-form-item>
                </template>

                <!-- 子表单特有属性 -->
                <template v-if="currentTemplate.fields[selectedField].type === 'subform'">
                  <el-divider>子表单设置</el-divider>
                  <el-form-item label="子表单模板">
                    <el-select v-model="currentTemplate.fields[selectedField].subformId" placeholder="选择子表单" style="width:100%">
                      <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
                    </el-select>
                  </el-form-item>
                  <el-button size="small" @click="editSubformFields">编辑子表单字段</el-button>
                </template>

                <!-- 关联数据特有属性 -->
                <template v-if="currentTemplate.fields[selectedField].type === 'relation'">
                  <el-divider>关联设置</el-divider>
                  <el-form-item label="关联模板">
                    <el-select v-model="currentTemplate.fields[selectedField].relationId" placeholder="选择关联模板" style="width:100%">
                      <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="显示字段">
                    <el-input v-model="currentTemplate.fields[selectedField].displayField" placeholder="显示哪个字段" />
                  </el-form-item>
                </template>

                <!-- 校验规则 -->
                <el-divider>校验规则</el-divider>
                <el-form-item label="自定义校验">
                  <el-input v-model="currentTemplate.fields[selectedField].validator"
                    type="textarea" :rows="3"
                    placeholder="JavaScript校验函数，返回true/false或错误消息" />
                </el-form-item>

              </el-form>
            </el-scrollbar>
          </template>
          <el-empty v-else description="点击字段进行配置" :image-size="80" />
        </div>
      </div>
    </div>

    <!-- ========== 新建/编辑弹窗 ========== -->
    <el-dialog v-model="showEditDialog" :title="editingTemplate ? '编辑模板' : '新建模板'" width="550px">
      <el-form :model="editForm" :rules="editRules" label-width="90px" ref="editFormRef">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板编码" prop="code">
          <el-input v-model="editForm.code" placeholder="唯一标识，如: supplier_info" />
        </el-form-item>
        <el-form-item label="模板分类">
          <el-select v-model="editForm.category" style="width:100%">
            <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="模板功能说明" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="editForm.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCreateOrUpdate">
          {{ editingTemplate ? '保存修改' : '创建并设计' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ========== AI 智能设计弹窗 ========== -->
    <el-dialog v-model="showAIHelper" title="AI 智能设计" width="700px">
      <div class="ai-helper-content">
        <p class="ai-hint">描述您需要的表单功能，AI 将自动生成完整的表单模板：</p>
        <el-input v-model="aiPrompt" type="textarea" :rows="5"
          placeholder="例如：设计一个供应商信息登记表，包含供应商基本信息（名称、编码、类型）、联系方式（联系人、电话、邮箱、地址）、资质证书（营业执照号、有效期、附件）、银行账户（开户行、账号）、备注说明等字段。" />
        <div class="ai-examples">
          <span class="examples-label">快速模板：</span>
          <el-tag v-for="ex in aiExamples" :key="ex" class="example-tag" @click="aiPrompt = ex">{{ ex }}</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAIHelper = false">取消</el-button>
        <el-button type="primary" :loading="aiLoading" @click="generateWithAI">
          <el-icon><MagicStick /></el-icon> 生成表单
        </el-button>
      </template>
    </el-dialog>

    <!-- ========== 预览弹窗 ========== -->
    <el-dialog v-model="showPreview" title="表单预览" width="800px" destroy-on-close>
      <div class="preview-form">
        <el-form :model="previewData" label-width="120px">
          <template v-for="f in previewFields" :key="f._key">
            <el-form-item :label="f.label + (f.required ? ' *' : '')" :required="f.required">
              <FieldPreview :field="f" v-model="previewData[f.name]" />
            </el-form-item>
          </template>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showPreview = false">关闭</el-button>
        <el-button type="primary" @click="submitPreviewData">提交测试</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, defineComponent, h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Edit, Delete, MagicStick, Document, Search, ArrowDown, ArrowUp,
  CopyDocument, Close, SetUp, Operation, View, Select, Minus, Calendar,
  Pointer, Finished, Open, Upload, Picture, EditPen, Grid, Title,
  Folder, FolderOpened, List, Connection, DataLine, Ticket, Location,
  Brush, PictureFilled, User, OfficeBuilding, Link, Message, Phone,
  Lock, Timer, Alarm, DateRange, Share, Star, Notebook, Download,
  ArrowLeft, MoreFilled, Rank
} from '@element-plus/icons-vue'
import { templateAPI } from '../../api'

// ========== 视图状态 ==========
const viewMode = ref('list')
const searchText = ref('')
const categoryFilter = ref('')
const loading = ref(false)
const toolboxExpanded = ref(['basic', 'datetime', 'select'])

// ========== 数据 ==========
const templates = ref<any[]>([])
let searchTimer: any = null

const filteredTemplates = computed(() => {
  let list = templates.value
  if (categoryFilter.value) {
    list = list.filter(t => t.category === categoryFilter.value)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(t =>
      (t.name || '').toLowerCase().includes(q) ||
      (t.description || '').toLowerCase().includes(q) ||
      (t.code || '').toLowerCase().includes(q)
    )
  }
  return list
})

function debounceSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadTemplates, 400)
}

function filterByCategory() {
  // 筛选已通过 computed 处理
}

async function loadTemplates() {
  loading.value = true
  try {
    const res: any = await templateAPI.list({ limit: 100 })
    templates.value = Array.isArray(res) ? res : (res.items || [])
  } catch {
    templates.value = []
  } finally {
    loading.value = false
  }
}

// ========== 当前编辑模板 ==========
const currentTemplate = reactive({
  id: null as number | null,
  name: '',
  code: '',
  description: '',
  category: '',
  fields: [] as any[]
})
const selectedField = ref<number | null>(null)
const dragIdx = ref<number | null>(null)

// ========== 字段类型定义 ==========
const fieldTypes = [
  // 基础控件
  { type: 'text',      label: '单行文本',    icon: 'Edit',           category: 'basic' },
  { type: 'textarea',  label: '多行文本',    icon: 'Document',       category: 'basic' },
  { type: 'number',    label: '数字',        icon: 'Minus',          category: 'basic' },
  { type: 'password',  label: '密码',       icon: 'Lock',           category: 'basic' },
  { type: 'email',     label: '邮箱',        icon: 'Message',        category: 'basic' },
  { type: 'phone',     label: '电话',        icon: 'Phone',          category: 'basic' },
  { type: 'url',       label: '网址',        icon: 'Link',           category: 'basic' },
  // 日期时间
  { type: 'date',      label: '日期',        icon: 'Calendar',       category: 'datetime' },
  { type: 'datetime',  label: '日期时间',     icon: 'Timer',          category: 'datetime' },
  { type: 'time',      label: '时间',        icon: 'Alarm',           category: 'datetime' },
  { type: 'daterange', label: '日期范围',     icon: 'DateRange',       category: 'datetime' },
  // 选择控件
  { type: 'select',    label: '下拉选择',     icon: 'ArrowDown',      category: 'select' },
  { type: 'cascader',  label: '级联选择',     icon: 'Share',          category: 'select' },
  { type: 'radio',     label: '单选',        icon: 'Pointer',        category: 'select' },
  { type: 'checkbox',  label: '多选',        icon: 'Finished',        category: 'select' },
  { type: 'switch',    label: '开关',        icon: 'Open',           category: 'select' },
  { type: 'slider',    label: '滑块',        icon: 'Operation',      category: 'select' },
  { type: 'rate',      label: '评分',        icon: 'Star',           category: 'select' },
  // 高级控件
  { type: 'richtext',  label: '富文本',      icon: 'Notebook',       category: 'advanced' },
  { type: 'upload',    label: '文件上传',     icon: 'Upload',         category: 'advanced' },
  { type: 'image',     label: '图片上传',     icon: 'Picture',        category: 'advanced' },
  { type: 'signature', label: '签名',        icon: 'EditPen',        category: 'advanced' },
  { type: 'barcode',   label: '条码',        icon: 'Grid',           category: 'advanced' },
  { type: 'qrcode',    label: '二维码',      icon: 'Grid',           category: 'advanced' },
  // 布局控件
  { type: 'divider',   label: '分隔线',      icon: 'Minus',          category: 'layout' },
  { type: 'heading',   label: '标题',        icon: 'Title',          category: 'layout' },
  { type: 'group',     label: '分组',        icon: 'Folder',         category: 'layout' },
  { type: 'grid',      label: '栅格布局',     icon: 'Grid',           category: 'layout' },
  { type: 'tabs',      label: '标签页',      icon: 'FolderOpened',   category: 'layout' },
  // 数据控件
  { type: 'subform',   label: '子表单',      icon: 'List',           category: 'data' },
  { type: 'relation',  label: '关联数据',     icon: 'Connection',      category: 'data' },
  { type: 'refdata',   label: '数据引用',     icon: 'DataLine',        category: 'data' },
  { type: 'autonum',   label: '自动编号',     icon: 'Ticket',         category: 'data' },
  // 特殊控件
  { type: 'location',  label: '地图位置',     icon: 'Location',       category: 'special' },
  { type: 'color',     label: '颜色选择',     icon: 'Brush',          category: 'special' },
  { type: 'icon',      label: '图标选择',     icon: 'PictureFilled',  category: 'special' },
  { type: 'user',      label: '人员选择',     icon: 'User',           category: 'special' },
  { type: 'org',       label: '部门选择',     icon: 'OfficeBuilding',  category: 'special' },
]

const basicFields = computed(() => fieldTypes.filter(f => f.category === 'basic'))
const datetimeFields = computed(() => fieldTypes.filter(f => f.category === 'datetime'))
const selectFields = computed(() => fieldTypes.filter(f => f.category === 'select'))
const advancedFields = computed(() => fieldTypes.filter(f => f.category === 'advanced'))
const layoutFields = computed(() => fieldTypes.filter(f => f.category === 'layout'))
const dataFields = computed(() => fieldTypes.filter(f => f.category === 'data'))
const specialFields = computed(() => fieldTypes.filter(f => f.category === 'special'))

// ========== 分类配置 ==========
const categories = [
  { value: 'crm', label: '客户管理', color: '#409EFF' },
  { value: 'order', label: '订单管理', color: '#67C23A' },
  { value: 'hr', label: '人力资源', color: '#E6A23C' },
  { value: 'inventory', label: '仓储物流', color: '#F56C6C' },
  { value: 'project', label: '项目管理', color: '#909399' },
  { value: 'finance', label: '财务报销', color: '#9B59B6' },
  { value: 'general', label: '通用表单', color: '#34495E' },
]

function getCategoryColor(cat?: string) {
  return categories.find(c => c.value === cat)?.color || '#409EFF'
}
function getCategoryLabel(cat?: string) {
  return categories.find(c => c.value === cat)?.label || '未分类'
}
function getCategoryIcon(cat?: string) {
  const map: Record<string, string> = {
    crm: 'User', order: 'ShoppingCart', hr: 'Document',
    inventory: 'Folder', project: 'Folder', finance: 'Ticket', general: 'Document'
  }
  return map[cat || 'general'] || 'Document'
}
function getCategoryTagType(cat?: string) {
  const map: Record<string, string> = {
    crm: 'primary', order: 'success', hr: 'warning',
    inventory: 'danger', project: 'info', finance: 'warning', general: 'info'
  }
  return (map[cat || 'general'] || 'info') as any
}

// ========== 拖拽逻辑 ==========
let dragFieldType: any = null
function onDragStart(e: DragEvent, ft: any) {
  dragFieldType = ft
  e.dataTransfer?.setData('text/plain', ft.type)
}
function onDrop(e: DragEvent) {
  if (!dragFieldType) return
  const key = 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6)
  const baseName = dragFieldType.type + '_field'
  let nameIdx = 1
  let fieldName = baseName
  while (currentTemplate.fields.some((f: any) => f.name === fieldName)) {
    fieldName = baseName + '_' + nameIdx++
  }
  currentTemplate.fields.push({
    _key: key,
    type: dragFieldType.type,
    label: dragFieldType.label,
    name: fieldName,
    placeholder: '',
    required: false,
    readonly: false,
    hidden: false,
    width: '100%',
    defaultValue: '',
    options: dragFieldType.type === 'select' || dragFieldType.type === 'radio' || dragFieldType.type === 'checkbox'
      ? ['选项1', '选项2', '选项3'] : [],
    optionsText: '',
    min: 0,
    max: 100,
    step: 1,
    precision: 0,
    maxLength: 255,
    limit: 1,
    maxSize: 10,
    accept: '',
    format: 'YYYY-MM-DD',
    dataSource: 'static',
  })
  selectedField.value = currentTemplate.fields.length - 1
  dragFieldType = null
}

function onFieldDragStart(e: DragEvent, idx: number) {
  dragIdx.value = idx
}
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

// ========== 字段操作 ==========
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
function autoFieldName() {
  if (selectedField.value === null) return
  const f = currentTemplate.fields[selectedField.value]
  const label = f.label || 'field'
  const pinyin: Record<string, string> = {
    '姓名': 'name', '名称': 'name', '标题': 'title', '编码': 'code', '编号': 'code',
    '电话': 'phone', '手机': 'phone', '邮箱': 'email', '地址': 'address',
    '日期': 'date', '时间': 'time', '备注': 'remark', '说明': 'desc',
    '金额': 'amount', '数量': 'quantity', '价格': 'price', '状态': 'status',
    '类型': 'type', '分类': 'category', '部门': 'dept', '人员': 'user',
  }
  f.name = pinyin[label] || label.toLowerCase().replace(/[^a-z0-9_]/g, '_').slice(0, 20)
}
function applyOptions() {
  if (selectedField.value === null) return
  const f = currentTemplate.fields[selectedField.value]
  f.options = (f.optionsText || '').split(/[,\n]/).map((s: string) => s.trim()).filter(Boolean)
}

// ========== 模板操作 ==========
const showEditDialog = ref(false)
const editingTemplate = ref<any>(null)
const editFormRef = ref()
const editForm = reactive({
  name: '',
  code: '',
  description: '',
  category: 'general',
  is_active: true
})
const editRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入模板编码', trigger: 'blur' }]
}

function openCreateDialog() {
  editingTemplate.value = null
  editForm.name = ''
  editForm.code = ''
  editForm.description = ''
  editForm.category = 'general'
  editForm.is_active = true
  showEditDialog.value = true
}
function openEditDialog(t: any) {
  editingTemplate.value = t
  editForm.name = t.name
  editForm.code = t.code || ''
  editForm.description = t.description || ''
  editForm.category = t.category || 'general'
  editForm.is_active = t.is_active !== false
  showEditDialog.value = true
}
async function confirmCreateOrUpdate() {
  if (!editForm.name.trim()) { ElMessage.warning('请输入模板名称'); return }
  if (!editForm.code.trim()) { ElMessage.warning('请输入模板编码'); return }
  try {
    if (editingTemplate.value) {
      await templateAPI.update(editingTemplate.value.id, {
        name: editForm.name,
        code: editForm.code,
        description: editForm.description,
        category: editForm.category,
        is_active: editForm.is_active
      })
      Object.assign(editingTemplate.value, editForm)
      ElMessage.success('保存成功')
    } else {
      const res: any = await templateAPI.create({
        name: editForm.name,
        code: editForm.code,
        description: editForm.description,
        category: editForm.category,
        is_active: editForm.is_active,
        fields: []
      })
      templates.value.unshift(res)
      showEditDialog.value = false
      openDesigner(res)
      ElMessage.success('模板已创建，开始设计')
      return
    }
    showEditDialog.value = false
  } catch { ElMessage.error('保存失败') }
}
function openDesigner(t: any) {
  currentTemplate.id = t.id
  currentTemplate.name = t.name
  currentTemplate.code = t.code || ''
  currentTemplate.description = t.description || ''
  currentTemplate.category = t.category || ''
  let fields = []
  if (t.fields) {
    try { fields = typeof t.fields === 'string' ? JSON.parse(t.fields) : t.fields } catch {}
  }
  currentTemplate.fields = fields.map((f: any) => ({
    ...f,
    _key: 'field_' + Math.random().toString(36).slice(2),
    optionsText: Array.isArray(f.options) ? f.options.join(',') : ''
  }))
  selectedField.value = null
  viewMode.value = 'design'
}
async function saveTemplate() {
  if (!currentTemplate.name.trim()) { ElMessage.warning('请输入模板名称'); return }
  const fieldsToSave = currentTemplate.fields.map(({ _key, _value, optionsText, ...rest }: any) => rest)
  const payload = {
    name: currentTemplate.name,
    code: currentTemplate.code,
    description: currentTemplate.description,
    category: currentTemplate.category,
    fields: fieldsToSave
  }
  try {
    if (currentTemplate.id) {
      await templateAPI.update(currentTemplate.id, payload)
      ElMessage.success('模板已更新')
    } else {
      const res: any = await templateAPI.create(payload)
      currentTemplate.id = res.id
      templates.value.unshift(res)
      ElMessage.success('模板已保存')
    }
  } catch { ElMessage.error('保存失败') }
}
async function deleteTemplate(t: any) {
  try {
    await ElMessageBox.confirm(`确定删除模板「${t.name}」？此操作不可恢复！`, '危险操作', { type: 'error' })
    await templateAPI.delete(t.id)
    templates.value = templates.value.filter(x => x.id !== t.id)
    ElMessage.success('已删除')
  } catch {}
}
async function duplicateTemplate(t: any) {
  try {
    const res: any = await templateAPI.create({
      name: t.name + ' (副本)',
      code: t.code + '_copy',
      description: t.description,
      category: t.category,
      fields: t.fields
    })
    templates.value.unshift(res)
    ElMessage.success('复制成功')
  } catch { ElMessage.error('复制失败') }
}
function exportTemplate(t: any) {
  const data = JSON.stringify(t, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${t.code || 'template'}_${t.id}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// ========== 工具函数 ==========
function countFields(fields: any) {
  if (!fields) return 0
  if (Array.isArray(fields)) return fields.length
  try { return JSON.parse(fields).length } catch { return 0 }
}
function formatDateShort(s: string | null) {
  if (!s) return '-'
  return new Date(s).toLocaleDateString('zh-CN')
}
function getFieldTypeLabel(type: string) {
  return fieldTypes.find(f => f.type === type)?.label || type
}
function getFieldTypeStyle(type: string) {
  const styles: Record<string, string> = {
    text: '', textarea: 'info', number: 'warning', password: 'danger', email: 'success',
    phone: 'success', url: 'info', date: 'primary', datetime: 'primary', time: 'primary',
    select: 'success', cascader: 'success', radio: 'info', checkbox: 'warning',
    switch: 'danger', slider: 'info', rate: 'warning', upload: 'info', image: 'success',
  }
  return (styles[type] || 'info') as any
}

// ========== 字段预览组件 ==========
const FieldPreview = defineComponent({
  props: { field: { type: Object, required: true }, modelValue: { type: [String, Number, Boolean, Array, Object] } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const val = computed({
      get: () => props.modelValue,
      set: (v) => emit('update:modelValue', v)
    })
    const f: any = computed(() => props.field)
    return () => {
      switch (f.value.type) {
        case 'text': case 'password': case 'email': case 'phone': case 'url':
          return h('input', { class: 'preview-input', placeholder: f.value.placeholder, disabled: true })
        case 'textarea':
          return h('textarea', { class: 'preview-textarea', placeholder: f.value.placeholder, disabled: true, rows: 2 })
        case 'number':
          return h('input', { class: 'preview-input', type: 'number', disabled: true, placeholder: f.value.placeholder })
        case 'date':
          return h('input', { class: 'preview-input', type: 'date', disabled: true })
        case 'select':
          return h('select', { class: 'preview-select', disabled: true },
            (f.value.options || []).map((o: string) => h('option', { key: o }, o))
          )
        case 'radio':
          return h('div', { class: 'preview-radio-group' },
            (f.value.options || []).map((o: string) => h('label', { key: o }, [
              h('input', { type: 'radio', name: f.value.name, disabled: true }),
              h('span', o)
            ]))
          )
        case 'checkbox':
          return h('div', { class: 'preview-checkbox-group' },
            (f.value.options || []).map((o: string) => h('label', { key: o }, [
              h('input', { type: 'checkbox', disabled: true }),
              h('span', o)
            ]))
          )
        case 'switch':
          return h('input', { type: 'checkbox', disabled: true })
        case 'rate':
          return h('div', { class: 'preview-rate' }, '★★★★★')
        case 'upload': case 'image':
          return h('div', { class: 'preview-upload' }, '+ 上传')
        case 'divider':
          return h('div', { class: 'preview-divider' })
        case 'heading':
          return h('h4', { class: 'preview-heading' }, f.value.label)
        default:
          return h('input', { class: 'preview-input', disabled: true })
      }
    }
  }
})

function getFieldPreview(field: any) {
  return FieldPreview
}

// ========== 预览 ==========
const showPreview = ref(false)
const previewFields = ref<any[]>([])
const previewData = reactive({} as Record<string, any>)

function previewTemplate() {
  previewFields.value = currentTemplate.fields.map(f => ({ ...f, _value: '' }))
  previewFields.value.forEach(f => { previewData[f.name] = f.defaultValue || '' })
  showPreview.value = true
}

async function submitPreviewData() {
  ElMessage.success('表单提交成功（测试模式）')
  showPreview.value = false
}

// ========== AI 设计 ==========
const showAIHelper = ref(false)
const aiPrompt = ref('')
const aiLoading = ref(false)
const aiExamples = [
  '员工入职登记表',
  '供应商信息管理',
  '客户投诉处理单',
  '采购申请流程表',
  '项目周报模板',
  '报销申请单',
]

async function generateWithAI() {
  if (!aiPrompt.value.trim()) { ElMessage.warning('请描述您的需求'); return }
  aiLoading.value = true
  try {
    // 使用预设模板匹配（后端AI接口未接入时）
    const templates: Record<string, any[]> = {
      '供应商': [
        { type: 'text', label: '供应商名称', name: 'supplier_name', required: true, width: '100%' },
        { type: 'text', label: '供应商编码', name: 'supplier_code', required: true, width: '50%' },
        { type: 'select', label: '供应商类型', name: 'supplier_type', required: true, width: '50%', options: ['原材料供应商', '设备供应商', '服务供应商', '其他'] },
        { type: 'divider', label: '联系方式', name: 'divider1', width: '100%' },
        { type: 'text', label: '联系人', name: 'contact_person', required: true, width: '50%' },
        { type: 'phone', label: '联系电话', name: 'contact_phone', required: true, width: '50%' },
        { type: 'email', label: '电子邮箱', name: 'contact_email', width: '50%' },
        { type: 'textarea', label: '详细地址', name: 'address', width: '100%' },
        { type: 'divider', label: '资质信息', name: 'divider2', width: '100%' },
        { type: 'text', label: '营业执照号', name: 'license_no', width: '50%' },
        { type: 'date', label: '有效期至', name: 'license_expiry', width: '50%' },
        { type: 'upload', label: '营业执照', name: 'license_file', width: '100%' },
        { type: 'divider', label: '银行账户', name: 'divider3', width: '100%' },
        { type: 'text', label: '开户银行', name: 'bank_name', width: '50%' },
        { type: 'text', label: '银行账号', name: 'bank_account', width: '50%' },
        { type: 'divider', label: '其他信息', name: 'divider4', width: '100%' },
        { type: 'textarea', label: '备注说明', name: 'remark', width: '100%' },
      ],
      '员工入职': [
        { type: 'heading', label: '基本信息', name: 'heading1', width: '100%' },
        { type: 'text', label: '姓名', name: 'name', required: true, width: '50%' },
        { type: 'text', label: '工号', name: 'employee_id', required: true, width: '50%' },
        { type: 'select', label: '性别', name: 'gender', required: true, width: '50%', options: ['男', '女'] },
        { type: 'date', label: '出生日期', name: 'birthday', width: '50%' },
        { type: 'select', label: '部门', name: 'department', required: true, width: '50%', options: ['技术部', '市场部', '财务部', '行政部'] },
        { type: 'text', label: '职位', name: 'position', required: true, width: '50%' },
        { type: 'date', label: '入职日期', name: 'join_date', required: true, width: '50%' },
        { type: 'heading', label: '联系方式', name: 'heading2', width: '100%' },
        { type: 'phone', label: '手机号码', name: 'mobile', required: true, width: '50%' },
        { type: 'email', label: '电子邮箱', name: 'email', width: '50%' },
        { type: 'textarea', label: '家庭住址', name: 'home_address', width: '100%' },
        { type: 'heading', label: '紧急联系人', name: 'heading3', width: '100%' },
        { type: 'text', label: '紧急联系人', name: 'emergency_contact', width: '50%' },
        { type: 'phone', label: '紧急联系电话', name: 'emergency_phone', width: '50%' },
        { type: 'heading', label: '银行账户', name: 'heading4', width: '100%' },
        { type: 'text', label: '开户银行', name: 'bank_name', width: '50%' },
        { type: 'text', label: '银行账号', name: 'bank_account', width: '50%' },
        { type: 'heading', label: '附件上传', name: 'heading5', width: '100%' },
        { type: 'image', label: '身份证正面', name: 'id_card_front', width: '50%' },
        { type: 'image', label: '身份证反面', name: 'id_card_back', width: '50%' },
        { type: 'upload', label: '学历证书', name: 'diploma', width: '100%' },
      ],
      '客户': [
        { type: 'text', label: '客户名称', name: 'customer_name', required: true, width: '100%' },
        { type: 'text', label: '客户编码', name: 'customer_code', required: true, width: '50%' },
        { type: 'select', label: '客户类型', name: 'customer_type', required: true, width: '50%', options: ['企业客户', '个人客户', '政府机构'] },
        { type: 'select', label: '客户等级', name: 'customer_level', width: '50%', options: ['VIP客户', '重要客户', '普通客户', '潜在客户'] },
        { type: 'select', label: '客户状态', name: 'status', width: '50%', options: ['活跃', '沉默', '流失'] },
        { type: 'divider', label: '联系信息', name: 'divider1', width: '100%' },
        { type: 'text', label: '联系人', name: 'contact_person', required: true, width: '50%' },
        { type: 'phone', label: '联系电话', name: 'contact_phone', required: true, width: '50%' },
        { type: 'email', label: '电子邮箱', name: 'email', width: '50%' },
        { type: 'textarea', label: '详细地址', name: 'address', width: '100%' },
        { type: 'divider', label: '其他信息', name: 'divider2', width: '100%' },
        { type: 'date', label: '建立关系日期', name: 'create_date', width: '50%' },
        { type: 'relation', label: '负责销售', name: 'sales_person', width: '50%' },
        { type: 'textarea', label: '备注', name: 'remark', width: '100%' },
      ],
    }
    // 匹配模板
    let matchedFields: any[] = []
    for (const [key, fields] of Object.entries(templates)) {
      if (aiPrompt.value.includes(key)) {
        matchedFields = fields
        break
      }
    }
    if (!matchedFields.length) {
      // 默认通用模板
      matchedFields = [
        { type: 'text', label: '名称', name: 'name', required: true, width: '50%' },
        { type: 'text', label: '编码', name: 'code', required: true, width: '50%' },
        { type: 'select', label: '类型', name: 'type', width: '50%', options: ['类型A', '类型B', '类型C'] },
        { type: 'date', label: '日期', name: 'date', width: '50%' },
        { type: 'textarea', label: '备注说明', name: 'remark', width: '100%' },
      ]
    }
    // 追加或替换字段
    const newFields = matchedFields.map(f => ({
      ...f,
      _key: 'field_' + Date.now() + '_' + Math.random().toString(36).slice(2),
      optionsText: Array.isArray(f.options) ? f.options.join(',') : ''
    }))
    if (currentTemplate.fields.length > 0) {
      newFields.forEach(f => currentTemplate.fields.push(f))
      ElMessage.success(`已追加 ${newFields.length} 个字段`)
    } else {
      currentTemplate.name = 'AI设计 - ' + aiPrompt.value.slice(0, 20)
      currentTemplate.fields = newFields
      ElMessage.success('已生成表单，请调整后保存')
    }
    showAIHelper.value = false
    aiPrompt.value = ''
  } catch {
    ElMessage.error('AI生成失败，请稍后重试')
  } finally {
    aiLoading.value = false
  }
}

onMounted(loadTemplates)
</script>

<style scoped lang="scss">
.template-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* ========== 列表视图 ========== */
.list-view {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    h2 { margin: 0; }
  }
  .header-right {
    display: flex;
    gap: 10px;
  }
}

.category-filter {
  margin-bottom: 16px;
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.template-card {
  cursor: pointer;
  transition: all 0.2s;
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  .card-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 8px;
  }
  .card-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }
  .card-title {
    flex: 1;
    min-width: 0;
    h4 {
      margin: 0 0 4px;
      font-size: 15px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .card-code {
      font-size: 11px;
      color: #aaa;
      font-family: monospace;
    }
  }
  .card-desc {
    margin: 0 0 10px;
    font-size: 13px;
    color: #666;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .card-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #999;
    margin-bottom: 8px;
    .field-count {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-left: auto;
    }
    .create-time {
      color: #bbb;
    }
  }
  .card-stats {
    font-size: 12px;
    color: #999;
    border-top: 1px solid #eee;
    padding-top: 8px;
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
    span {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }
}

/* ========== 设计器视图 ========== */
.designer-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
}

.designer-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  flex-shrink: 0;
  .toolbar-left, .toolbar-center, .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .toolbar-center {
    flex: 1;
    justify-content: center;
  }
  .toolbar-right {
    margin-left: auto;
  }
}

.designer-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧工具箱 */
.field-toolbox {
  width: 200px;
  background: white;
  border-right: 1px solid #e6e6e6;
  overflow-y: auto;
  flex-shrink: 0;
  :deep(.el-collapse-item__header) {
    padding: 0 12px;
    font-size: 13px;
    font-weight: 600;
  }
  :deep(.el-collapse-item__content) {
    padding: 0 8px 8px;
  }
}

.toolbox-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.toolbox-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: move;
  font-size: 12px;
  transition: all 0.2s;
  &:hover {
    border-color: #409eff;
    background: #ecf5ff;
    color: #409eff;
  }
}

/* 中间画布 */
.form-canvas {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #fafafa;
  background-image: 
    linear-gradient(#eee 1px, transparent 1px),
    linear-gradient