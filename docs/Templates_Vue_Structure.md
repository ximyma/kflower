# Templates.vue 代码结构文档

> **文件路径**: `D:\kkflower\kflower-frontend\src\pc\views\Templates.vue`  
> **总代码行数**: 4252 行  
> **创建日期**: 2024年  
> **最后更新**: 2026-05-04  
> **用途**: 模板设计器主页面（列表视图 + 设计器视图）

---

## 📋 目录

1. [文件概述](#文件概述)
2. [Template 部分（HTML 模板）](#template-部分)
3. [Script 部分（Vue 3 Composition API）](#script-部分)
4. [Style 部分（SCSS 样式）](#style-部分)
5. [函数清单（按功能分类）](#函数清单)
6. [响应式数据清单](#响应式数据清单)
7. [Computed 属性清单](#computed-属性清单)
8. [生命周期钩子](#生命周期钩子)
9. [依赖关系](#依赖关系)
10. [使用说明](#使用说明)

---

## 文件概述

`Templates.vue` 是 Kflower 系统的**模板设计器主页面**，包含两大核心视图：

### 1. 列表视图（List View）
- 模板列表展示（表格视图 / 卡片视图）
- 模板搜索、分类过滤
- 模板操作（查看、编辑、发布、删除、复制、导出）

### 2. 设计器视图（Designer View）
- 左侧字段工具箱（拖拽字段类型）
- 中间表单画布（拖拽排序字段）
- 右侧属性面板（配置字段属性）
- 支持 40+ 种字段类型

### 3. 弹窗组件（Dialogs）
- 新建/编辑模板弹窗
- Excel/图片导入弹窗（4 步骤向导）
- AI 智能设计弹窗
- JSON 导入弹窗
- 填写数据弹窗
- 数据管理弹窗
- 数据详情/编辑弹窗
- 预览弹窗（支持发布预览）
- 权限设置弹窗
- 插件管理弹窗

---

## Template 部分

### 主要区域

| 区域 | CSS 类名 | 功能描述 |
|------|-----------|-----------|
| 列表视图 | `.list-view` | 展示模板列表，支持表格/卡片切换 |
| 页面头部 | `.page-header` | 搜索框、视图切换、操作按钮 |
| 分类过滤 | `.category-filter` | 按分类筛选模板 |
| 表格视图 | `.template-table-wrapper` | 表格形式展示模板 |
| 卡片视图 | `.template-grid` | 卡片形式展示模板 |
| 设计器视图 | `.designer-view` | 模板设计器主界面 |
| 设计器工具栏 | `.designer-toolbar` | 模板名称、分类、共享开关、操作按钮 |
| 字段工具箱 | `.field-toolbox` | 左侧字段类型列表（可拖拽） |
| 表单画布 | `.form-canvas` | 中间拖拽区域（字段排序） |
| 属性面板 | `.property-panel` | 右侧字段属性配置 |

### 弹窗列表

| 弹窗 | v-model 控制变量 | 功能描述 |
|-------|-------------------|-----------|
| 新建/编辑弹窗 | `showEditDialog` | 创建或编辑模板基本信息 |
| 导入 Excel/图片弹窗 | `showImport` | 4 步骤向导导入 Excel 或图片 |
| AI 设计弹窗 | `showAIHelper` | AI 智能生成表单字段 |
| JSON 导入弹窗 | `showJsonImport` | 粘贴 JSON 生成表单 |
| 填写数据弹窗 | `showDataForm` | 填写表单数据 |
| 数据管理弹窗 | `showDataManager` | 查看、编辑、删除表单数据 |
| 数据详情弹窗 | `showDataDetail` | 查看或编辑单条数据 |
| 预览弹窗 | `showPreview` | 预览表单效果（支持发布预览） |
| 权限设置弹窗 | `showPermissionDialog` | 设置模板访问权限 |
| 插件管理弹窗 | `showTemplatePluginDialog` | 管理模板插件 |

---

## Script 部分

### 导入语句

```typescript
// Vue 核心
import { ref, reactive, computed, onMounted } from 'vue'

// Element Plus
import { ElMessage, ElMessageBox } from 'element-plus'

// Vue Router
import { useRouter, useRoute } from 'vue-router'

// Element Plus 图标
import {
  Plus, Edit, Delete, MagicStick, Document, Search, ArrowDown, ArrowUp,
  CopyDocument, Close, SetUp, Operation, View, Select, Minus, Calendar,
  Pointer, Finished, Open, Upload, Picture, EditPen, Grid,
  Folder, FolderOpened, List, Connection, DataLine, Ticket, Location,
  Brush, PictureFilled, User, OfficeBuilding, Link, Message, Phone,
  Lock, Timer, Share, Star, Notebook, Download,
  ArrowLeft, MoreFilled, Rank, RefreshRight, QuestionFilled, Promotion,
  InfoFilled, Coin, CircleCheck, CircleClose, Key
} from '@element-plus/icons-vue'

// API
import { templateAPI, userAPI } from '../../common/api'

// Store
import { useAIStore } from '../../common/store/ai'
import { useUserStore } from '../../common/store/user'

// 组件
import TemplatePluginManager from '../components/TemplatePluginManager.vue'
```

---

## 响应式数据清单

### Ref 响应式变量

| 变量名 | 类型 | 初始值 | 用途 |
|--------|------|--------|------|
| `viewMode` | `Ref<string>` | `'list'` | 视图模式：`'list'` 或 `'design'` |
| `listStyle` | `Ref<string>` | `'table'` | 列表样式：`'table'` 或 `'card'` |
| `searchText` | `Ref<string>` | `''` | 搜索文本 |
| `categoryFilter` | `Ref<string>` | `''` | 分类过滤 |
| `loading` | `Ref<boolean>` | `false` | 加载状态 |
| `toolboxExpanded` | `Ref<string[]>` | `['basic', 'datetime', 'select']` | 工具箱展开状态 |
| `selectedField` | `Ref<number \| null>` | `null` | 选中字段索引 |
| `showEditDialog` | `Ref<boolean>` | `false` | 显示编辑弹窗 |
| `editingTemplate` | `Ref<any>` | `null` | 正在编辑的模板 |
| `editFormRef` | `Ref<any>` | `null` | 编辑表单引用 |
| `publishing` | `Ref<boolean>` | `false` | 发布中状态 |
| `isPublishPreview` | `Ref<boolean>` | `false` | 是否为发布预览模式 |
| `accessType` | `Ref<'private' \| 'public' \| 'specified'>` | `'private'` | 访问类型 |
| `allowedUsers` | `Ref<Array<...>>` | `[]` | 允许的用户列表 |
| `userSearchQuery` | `Ref<string>` | `''` | 用户搜索查询 |
| `userSearchResults` | `Ref<any[]>` | `[]` | 用户搜索结果 |
| `userSearchLoading` | `Ref<boolean>` | `false` | 用户搜索加载 |
| `showPreview` | `Ref<boolean>` | `false` | 显示预览弹窗 |
| `showAIHelper` | `Ref<boolean>` | `false` | 显示 AI 设计弹窗 |
| `aiPrompt` | `Ref<string>` | `''` | AI 提示词 |
| `aiLoading` | `Ref<boolean>` | `false` | AI 加载状态 |
| `selectedModelId` | `Ref<string>` | `''` | 选中的 AI 模型 ID |
| `showImport` | `Ref<boolean>` | `false` | 显示导入弹窗 |
| `importStep` | `Ref<number>` | `0` | 导入步骤（0-3） |
| `importLoading` | `Ref<boolean>` | `false` | 导入加载状态 |
| `importFileName` | `Ref<string>` | `''` | 导入文件名 |
| `importDialogFullscreen` | `Ref<boolean>` | `false` | 导入对话框全屏状态 |
| `importHeaderRow` | `Ref<number>` | `0` | 导入表头行 |
| `importSheetName` | `Ref<string>` | `''` | 导入工作表名 |
| `importDependenciesStatus` | `Ref<any>` | `null` | 导入依赖状态 |
| `tableType` | `Ref<string>` | `'onedim'` | 表格类型：`'onedim'` 或 `'matrix'` |
| `matrixRowHeaderRow` | `Ref<number>` | `0` | 矩阵行表头行索引 |
| `matrixColHeaderCol` | `Ref<number>` | `0` | 矩阵列表头列索引 |
| `matrixMergeType` | `Ref<string>` | `'concat'` | 矩阵字段组合方式 |
| `matrixLoading` | `Ref<boolean>` | `false` | 矩阵处理加载状态 |
| `enableMultiRowHeader` | `Ref<boolean>` | `false` | 启用多行表头 |
| `selectedHeaderRows` | `Ref<number[]>` | `[0]` | 选中的表头行 |
| `multiHeaderMergeType` | `Ref<string>` | `'vertical'` | 多行表头合并类型 |
| `mergedHeaderPreview` | `Ref<string[]>` | `[]` | 合并后的表头预览 |
| `importSelectedFields` | `Ref<Record<number, boolean>>` | `{}` | 导入选中的字段 |
| `importSelectAll` | `Ref<boolean>` | `true` | 导入全选 |
| `importSelectIndeterminate` | `Ref<boolean>` | `false` | 导入半选状态 |
| `importFileRaw` | `Ref<File \| null>` | `null` | 导入原始文件 |
| `showDataForm` | `Ref<boolean>` | `false` | 显示数据表单弹窗 |
| `dataFormTemplate` | `Ref<any>` | `null` | 数据表单模板 |
| `dataFormFields` | `Ref<any[]>` | `[]` | 数据表单字段 |
| `dataFormLoading` | `Ref<boolean>` | `false` | 数据表单加载 |
| `dataFormRef` | `Ref<any>` | `null` | 数据表单引用 |
| `showDataManager` | `Ref<boolean>` | `false` | 显示数据管理弹窗 |
| `dataManagerTemplate` | `Ref<any>` | `null` | 数据管理模板 |
| `dataManagerFields` | `Ref<any[]>` | `[]` | 数据管理字段 |
| `dataList` | `Ref<any[]>` | `[]` | 数据列表 |
| `dataListLoading` | `Ref<boolean>` | `false` | 数据列表加载 |
| `dataSearchText` | `Ref<string>` | `''` | 数据搜索文本 |
| `dataTotal` | `Ref<number>` | `0` | 数据总数 |
| `dataPage` | `Ref<number>` | `1` | 数据页码 |
| `dataPageSize` | `Ref<number>` | `20` | 数据页大小 |
| `dataSelectedRows` | `Ref<any[]>` | `[]` | 数据选中的行 |
| `dataStats` | `Ref<any>` | `null` | 数据统计 |
| `showDataDetail` | `Ref<boolean>` | `false` | 显示数据详情弹窗 |
| `dataDetailIsEdit` | `Ref<boolean>` | `false` | 数据详情是否编辑 |
| `dataDetailId` | `Ref<number \| null>` | `null` | 数据详情 ID |
| `dataDetailSaving` | `Ref<boolean>` | `false` | 数据详情保存中 |
| `showJsonImport` | `Ref<boolean>` | `false` | 显示 JSON 导入弹窗 |
| `jsonInputText` | `Ref<string>` | `''` | JSON 输入文本 |
| `showPermissionDialog` | `Ref<boolean>` | `false` | 显示权限设置弹窗 |
| `permTemplate` | `Ref<any>` | `null` | 权限模板 |
| `permLoading` | `Ref<boolean>` | `false` | 权限保存加载 |
| `showTemplatePluginDialog` | `Ref<boolean>` | `false` | 显示插件管理弹窗 |
| `pluginTemplate` | `Ref<any>` | `null` | 插件模板 |
| `formulaValidation` | `Ref<Record<number, {...}>` | `{}` | 公式验证状态 |
| `uploadRef` | `Ref<any>` | `null` | 上传组件引用 |

### Reactive 响应式对象

| 变量名 | 类型 | 用途 |
|--------|------|------|
| `currentTemplate` | `Reactive` | 当前编辑的模板对象（id, name, code, description, category, is_public, fields） |
| `editForm` | `Reactive` | 编辑表单数据（name, code, description, category, is_active） |
| `importData` | `Reactive` | 导入数据（headers, rows, all_rows, total_rows, total_columns, sheet_names...） |
| `importTemplateForm` | `Reactive` | 导入模板表单（name, description, category） |
| `previewData` | `Reactive` | 预览数据（Record<string, any>） |
| `dataFormData` | `Reactive` | 数据表单数据（Record<string, any>） |
| `dataDetailData` | `Reactive` | 数据详情数据（Record<string, any>） |
| `permForm` | `Reactive` | 权限表单数据（is_public） |
| `matrixPreview` | `Reactive` | 矩阵预览数据（headers, rows） |

---

## Computed 属性清单

| 属性名 | 依赖 | 返回值 | 用途 |
|--------|------|--------|------|
| `filteredTemplates` | `templates`, `categoryFilter`, `searchText` | `ComputedRef<any[]>` | 过滤后的模板列表（按分类和搜索文本） |
| `basicFields` | `fieldTypes` | `ComputedRef` | 基础字段类型列表 |
| `datetimeFields` | `fieldTypes` | `ComputedRef` | 日期时间字段类型列表 |
| `selectFields` | `fieldTypes` | `ComputedRef` | 选择控件字段类型列表 |
| `advancedFields` | `fieldTypes` | `ComputedRef` | 高级控件字段类型列表 |
| `layoutFields` | `fieldTypes` | `ComputedRef` | 布局控件字段类型列表 |
| `dataFields` | `fieldTypes` | `ComputedRef` | 数据控件字段类型列表 |
| `specialFields` | `fieldTypes` | `ComputedRef` | 特殊控件字段类型列表 |
| `availableFieldsForFormula` | `currentTemplate.fields`, `selectedField` | `ComputedRef<any[]>` | 可用于公式引用的字段（排除当前字段和计算字段） |
| `formulaDependencies` | `selectedField`, `currentTemplate.fields` | `ComputedRef<string[]>` | 公式依赖的字段名列表 |
| `currentUserId` | `userStore.userInfo` | `ComputedRef<number \| null>` | 当前用户 ID |

---

## 函数清单

### 1. 核心功能函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `loadTemplates` | 无 | `Promise<void>` | 加载模板列表 |
| `debounceSearch` | 无 | `void` | 防抖搜索 |
| `filterByCategory` | 无 | `void` | 按分类过滤（空函数） |
| `openCreateDialog` | 无 | `void` | 打开新建模板对话框 |
| `openEditDialog` | `t: any` | `void` | 打开编辑模板对话框 |
| `confirmCreateOrUpdate` | 无 | `Promise<void>` | 确认创建或更新模板 |
| `openDesigner` | `t: any` | `void` | 打开设计器 |
| `saveTemplate` | 无 | `Promise<void>` | 保存模板 |
| `publishTemplate` | `template?: any` | `Promise<void>` | 发布模板 |
| `unpublishTemplate` | `t: any` | `Promise<void>` | 撤回发布 |
| `confirmPublishFromPreview` | 无 | `Promise<void>` | 从预览确认发布 |
| `deleteTemplate` | `t: any` | `Promise<void>` | 删除模板 |
| `duplicateTemplate` | `t: any` | `Promise<void>` | 复制模板 |
| `exportTemplate` | `t: any` | `void` | 导出模板为 JSON |
| `previewTemplate` | 无 | `void` | 预览模板 |

### 2. 字段操作函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `onDragStart` | `e: DragEvent, ft: any` | `void` | 拖拽字段开始 |
| `onDrop` | `e: DragEvent` | `void` | 拖拽字段放下 |
| `onFieldDragStart` | `e: DragEvent, idx: number` | `void` | 字段拖拽排序开始 |
| `onFieldDrop` | `e: DragEvent, targetIdx: number` | `void` | 字段拖拽排序放下 |
| `removeField` | `idx: number` | `void` | 删除字段 |
| `moveField` | `idx: number, dir: number` | `void` | 移动字段（上/下） |
| `copyField` | `idx: number` | `void` | 复制字段 |
| `onFieldTypeChange` | `newType: string` | `void` | 字段类型变更处理 |
| `autoFieldName` | 无 | `void` | 自动生成字段名（根据 label 转拼音） |
| `applyOptions` | 无 | `void` | 应用选项（optionsText → options） |

### 3. 公式相关函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `insertFieldToFormula` | `fieldName: string` | `void` | 插入字段到公式 |
| `insertFunctionToFormula` | `template: string` | `void` | 插入函数到公式 |
| `onFormulaInput` | 无 | `void` | 公式输入时实时验证（防抖） |
| `validateFieldFormula` | 无 | `void` | 验证字段公式语法 |

### 4. 条件显示函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `onVisibilityModeChange` | 无 | `void` | 可见性模式变更处理 |
| `buildVisibilityRule` | `idx: number` | `void` | 构建可见性规则 |

### 5. 校验规则函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `addValidationRule` | `idx: number` | `void` | 添加校验规则 |
| `removeValidationRule` | `idx: number, ruleIdx: number` | `void` | 删除校验规则 |

### 6. 级联选项函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `toggleCascade` | `idx: number` | `void` | 切换级联开关 |
| `updateCascadeSource` | `idx: number` | `void` | 更新级联数据源 |

### 7. 子表字段函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `addSubFormField` | `idx: number` | `void` | 添加子表单字段 |
| `removeSubFormField` | `idx: number, sfIdx: number` | `void` | 删除子表单字段 |

### 8. 关联数据函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `updateRelationConfig` | `idx: number` | `void` | 更新关联数据配置 |

### 9. 权限管理函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `openPermissionDialog` | `row: any` | `void` | 打开权限设置弹窗 |
| `savePermission` | 无 | `Promise<void>` | 保存权限设置 |
| `removeUser` | `user: {id: number}` | `void` | 删除已选中的用户 |
| `searchUsers` | `query: string` | `Promise<void>` | 搜索用户 |
| `onUserSelected` | `username: string` | `void` | 用户选中回调 |

### 10. 导入功能函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `onImportFileChange` | `file: any` | `Promise<void>` | 导入文件变更处理 |
| `doParseFile` | `rawFile: File, headerRow: number, sheetName: string` | `Promise<void>` | 解析文件（调用后端 API） |
| `applyHeaderRow` | `headerRow: number` | `Promise<void>` | 应用选定的表头行 |
| `selectHeaderRow` | `rowIndex: number` | `Promise<void>` | 选择表头行 |
| `reparseWithHeaderRow` | 无 | `Promise<void>` | 重新解析表头行 |
| `applyMergedHeader` | 无 | `Promise<void>` | 应用合并后的多行表头 |
| `reparseWithSheet` | 无 | `Promise<void>` | 重新解析工作表 |
| `onImportSelectAllChange` | `val: boolean` | `void` | 导入字段全选变更 |
| `onImportFieldSelectChange` | 无 | `void` | 导入字段选择变更 |
| `goToFieldAdjust` | 无 | `void` | 跳转到字段调整步骤 |
| `onImportDialogOpen` | 无 | `void` | 导入对话框打开回调 |
| `fetchImportDependenciesStatus` | 无 | `Promise<void>` | 获取导入依赖状态 |
| `loadSampleData` | `type: string` | `void` | 加载示例数据 |
| `detectFieldTypes` | 无 | `void` | 自动检测字段类型 |
| `addFieldOption` | `row: any` | `void` | 添加字段选项 |
| `confirmCreateTemplate` | 无 | `Promise<void>` | 确认创建模板并导入数据 |
| `inferType` | `header: string` | `string` | 推断字段类型（根据表头关键词） |
| `getMatrixColIndices` | 无 | `number[]` | 获取矩阵列索引列表 |
| `getMatrixColPreview` | `colIdx: number` | `string` | 获取矩阵列预览 |
| `applyMatrixHeader` | 无 | `Promise<void>` | 应用矩阵表头 |
| `mergeMultiRowHeaders` | 无 | `void` | 合并多行表头 |

### 11. AI 设计函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `generateWithAI` | 无 | `Promise<void>` | 使用 AI 生成表单字段 |

### 12. JSON 导入函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `openJsonImport` | 无 | `void` | 打开 JSON 导入弹窗 |
| `importFromJson` | 无 | `void` | 从 JSON 导入表单 |

### 13. 数据提交和管理函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `getTemplateFields` | `t: any` | `any[]` | 获取模板字段（从 modules 或 fields） |
| `evaluateFormula` | `formula: string, ctx: Record<string, any>` | `any` | 计算公式（前端求值器） |
| `computeDataFormFormulas` | 无 | `void` | 计算所有公式字段 |
| `onDataFormFieldChange` | `_fieldName: string` | `void` | 字段值变化时触发公式重算 |
| `openFormSubmit` | `t: any` | `void` | 打开表单提交（从列表） |
| `openDataForm` | `t: any` | `void` | 打开数据表单弹窗 |
| `submitDataForm` | 无 | `Promise<void>` | 提交数据表单 |
| `openDataManager` | `t: any` | `void` | 打开数据管理弹窗 |
| `openDataList` | `t: any` | `void` | 打开数据列表（路由跳转） |
| `debounceDataSearch` | 无 | `void` | 防抖数据搜索 |
| `loadDataList` | 无 | `Promise<void>` | 加载数据列表 |
| `loadStats` | 无 | `Promise<void>` | 加载数据统计 |
| `getDisplayValue` | `row: any, f: any` | `string` | 获取字段显示值 |
| `getFieldLabel` | `fieldName: string` | `string` | 获取字段标签 |
| `formatDateTime` | `s: string \| null` | `string` | 格式化日期时间 |
| `onDataSelectionChange` | `rows: any[]` | `void` | 数据选择变更 |
| `viewDataDetail` | `row: any` | `void` | 查看数据详情 |
| `editDataItem` | `row: any` | `void` | 编辑数据项 |
| `saveDataDetail` | 无 | `Promise<void>` | 保存数据详情 |
| `deleteDataItem` | `row: any` | `Promise<void>` | 删除数据项 |
| `exportDataCSV` | 无 | `void` | 导出数据为 CSV |

### 14. 工具函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `countFields` | `t: any` | `number` | 计算模板字段数量 |
| `formatDateShort` | `s: string \| null` | `string` | 格式化短日期 |
| `formatDate` | `s: string \| null` | `string` | 格式化日期时间 |
| `getCreatorName` | `t: any` | `string` | 获取创建人显示名 |
| `getFieldTypeLabel` | `type: string` | `string` | 获取字段类型标签 |
| `getFieldTypeStyle` | `type: string` | `string` | 获取字段类型样式 |
| `getCategoryColor` | `cat?: string` | `string` | 获取分类颜色 |
| `getCategoryLabel` | `cat?: string` | `string` | 获取分类标签 |
| `getCategoryIcon` | `cat?: string` | `string` | 获取分类图标 |
| `getCategoryTagType` | `cat?: string` | `string` | 获取分类标签类型 |

### 15. 路由和初始化函数

| 函数名 | 参数 | 返回值 | 用途 |
|--------|------|--------|------|
| `handleRouteParams` | 无 | `Promise<void>` | 处理路由参数（从 URL 加载模板） |
| `onMounted` | 无 | `Promise<void>` | 生命周期钩子（加载模板列表、AI 模型、处理路由参数） |
| `goDataModeling` | 无 | `void` | 跳转到数据建模页面 |
| `continuePublishPreview` | 无 | `void` | 从编辑框继续发布预览 |
| `closePreview` | 无 | `void` | 关闭预览时重置状态 |
| `applyTemplateFields` | `t: any` | `void` | 从模板对象提取并标准化字段数组 |
| `openTemplatePluginDialog` | `row: any` | `void` | 打开插件管理弹窗 |

---

## 生命周期钩子

### onMounted

```typescript
onMounted(async () => {
  // 1. 加载模板列表
  await loadTemplates()
  
  // 2. 并行加载 AI 模型和处理路由参数
  await Promise.all([
    aiStore.loadModels(),
    handleRouteParams()
  ])
  
  // 3. 设置默认 AI 模型
  if (aiStore.models.length > 0) {
    selectedModelId.value = aiStore.currentModel?.modelId || aiStore.models[0].modelId
  }
  
  // 4. 处理路由参数（从应用设计器跳转）
  if (route.query.mode === 'ai') {
    showAIHelper.value = true
  }
})
```

---

## 依赖关系

### 组件依赖

| 依赖 | 用途 |
|------|------|
| `TemplatePluginManager` | 模板插件管理组件（从 `../components/TemplatePluginManager.vue` 导入） |

### Store 依赖

| Store | 用途 |
|-------|------|
| `useAIStore()` | AI 模型管理（加载模型、当前模型） |
| `useUserStore()` | 用户信息（currentUserId） |

### API 依赖

| API | 用途 |
|-----|------|
| `templateAPI` | 模板 CRUD、发布、数据提交、数据管理 |
| `userAPI` | 用户搜索 |

### 外部库依赖

| 库 | 用途 |
|-----|------|
| Vue 3 | Composition API（ref, reactive, computed, onMounted） |
| Element Plus | UI 组件库（按钮、表格、对话框、表单等） |
| Element Plus Icons | 图标库 |
| Vue Router | 路由管理 |

---

## Style 部分

### 主要样式类

| CSS 类名 | 用途 |
|----------|------|
| `.template-page` | 页面容器 |
| `.list-view` | 列表视图容器 |
| `.page-header` | 页面头部 |
| `.category-filter` | 分类过滤器 |
| `.template-table-wrapper` | 表格视图容器 |
| `.template-grid` | 卡片视图容器 |
| `.template-card` | 模板卡片 |
| `.designer-view` | 设计器视图容器 |
| `.designer-toolbar` | 设计器工具栏 |
| `.designer-body` | 设计器主体（工具箱 + 画布 + 属性面板） |
| `.field-toolbox` | 字段工具箱 |
| `.toolbox-grid` | 工具箱网格布局 |
| `.toolbox-item` | 工具箱项（可拖拽） |
| `.form-canvas` | 表单画布（带网格背景） |
| `.canvas-empty` | 画布空状态 |
| `.canvas-field` | 画布字段项（可拖拽排序） |
| `.property-panel` | 属性面板 |
| `.import-container` | 导入弹窗容器 |
| `.import-uploader` | 导入上传组件 |
| `.data-manager` | 数据管理容器 |
| `.data-pagination` | 数据分页 |
| `.permission-section` | 权限设置区域 |
| `.user-selector` | 用户选择器 |

---

## 使用说明

### 1. 在列表视图中查找函数

- **搜索模板**：`searchText` ref + `debounceSearch()` 函数
- **过滤模板**：`categoryFilter` ref + `filterByCategory()` 函数
- **新建模板**：`openCreateDialog()` → `confirmCreateOrUpdate()`
- **编辑模板**：`openEditDialog(t)` → `confirmCreateOrUpdate()`
- **发布模板**：`publishTemplate(t)` → `confirmPublishFromPreview()`
- **删除模板**：`deleteTemplate(t)`

### 2. 在设计器视图中查找函数

- **拖拽字段到画布**：`onDragStart(e, ft)` → `onDrop(e)`
- **拖拽排序字段**：`onFieldDragStart(e, idx)` → `onFieldDrop(e, targetIdx)`
- **删除字段**：`removeField(idx)`
- **移动字段**：`moveField(idx, dir)`
- **复制字段**：`copyField(idx)`
- **修改字段属性**：直接在属性面板修改（双向绑定）

### 3. 在导入功能中查找函数

- **上传文件**：`onImportFileChange(file)` → `doParseFile(rawFile, headerRow, sheetName)`
- **选择表头行**：`selectHeaderRow(rowIndex)` → `applyHeaderRow(headerRow)`
- **调整字段**：`detectFieldTypes()` → 手动修改 `importFields`
- **创建模板**：`confirmCreateTemplate()`

### 4. 在数据管理中查找函数

- **打开数据管理**：`openDataManager(t)` → `loadDataList()` + `loadStats()`
- **提交数据**：`openDataForm(t)` → `submitDataForm()`
- **编辑数据**：`editDataItem(row)` → `saveDataDetail()`
- **删除数据**：`deleteDataItem(row)`
- **导出 CSV**：`exportDataCSV()`

### 5. 常见修改场景

#### 场景 1：添加新的字段类型
1. 在 `fieldTypes` 数组中添加新类型
2. 在 `allFieldTypes` 数组中添加新类型
3. 在 Template 的属性面板中添加对应的配置项
4. 在 `FormListPage.vue` 中添加对应的输入组件

#### 场景 2：修改导入逻辑
1. 修改 `doParseFile()` 函数（前端）
2. 修改后端 `/api/v1/import/parse` 接口
3. 修改 `applyHeaderRow()` 函数（处理表头）
4. 修改 `confirmCreateTemplate()` 函数（创建模板）

#### 场景 3：修改公式功能
1. 修改 `FORMULA_FUNCTIONS` 对象（添加新函数）
2. 修改 `validateFieldFormula()` 函数（语法检查）
3. 修改 `evaluateFormula()` 函数（前端求值器）
4. 修改后端公式解析器（如果需要后端计算）

---

## 更新记录

| 日期 | 更新内容 | 更新人 |
|------|----------|--------|
| 2026-05-04 | 初始版本，完整代码结构和函数清单 | AI Assistant |
| | | |

---

## 注意事项

1. **文件非常大**（4252 行），修改时请使用 VS Code 的大文件优化功能
2. **函数数量多**（80+ 个），修改前请先查看本文档确认函数用途
3. **响应式数据多**（50+ 个 ref/reactive），注意依赖关系
4. **Template 部分复杂**（多个弹窗、多个视图），修改时请仔细测试
5. **样式使用 SCSS**，注意嵌套层级

---

## 快速查找函数技巧

### 在 VS Code 中
1. 按 `Ctrl+Shift+O`（Windows/Linux）或 `Cmd+Shift+O`（Mac）打开符号面板
2. 输入函数名关键词快速跳转

### 在本文档中
1. 使用 Ctrl+F 搜索函数名
2. 查看"函数清单"章节，按功能分类查找

---

**文档版本**: 1.0  
**最后更新**: 2026-05-04  
**作者**: AI Assistant
