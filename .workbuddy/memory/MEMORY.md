# MEMORY.md - Kflower 项目长期记忆

## 项目背景
- 用户开发基于 FastAPI 的办公自动化系统 Kflower
- 前端：Vue 3 + Element Plus，后端：FastAPI + SQLAlchemy + SQLite
- 核心功能：动态表单系统（模板设计 → 发布 → 动态建表 → 表单填写）
- 扩展功能：AI 模块、工作流引擎、插件系统、智能体编排器

## 项目目录结构（重要）
```
D:\kkflower\
├── kflower-backend/       ← 后端项目根（main.py 启动入口）
│   └── app/              ← 后端 Python 包（api/core/schemas/services/models）
│       └── migrations/   ← 数据库迁移脚本（重要！）
├── kflower-frontend/
│   └── src/
│       ├── app/           ← 前端移动端视图（手机版）
│       ├── common/        ← 公共组件和 API
│       └── pc/           ← 前端 PC 端视图
└── .workbuddy/           ← WorkBuddy 工作区（勿删）
```
**注意**：
- `kflower-backend/app/` = 后端 Python 包
- `kflower-frontend/src/app/` = 前端移动端视图（手机版入口）

## 技术细节
- **模板编码**：自动生成 `form_{id}` 格式，后端 `create_template` 创建后更新
- **动态建表**：发布时根据 `modules[].fields[]` 定义，通过 `CREATE TABLE form_data_{template_id}` 创建
- **字段类型映射**：
  - `number/money/percent` → REAL
  - `date/datetime` → TEXT
  - `switch/checkbox` → INTEGER DEFAULT 0
  - 其他 → TEXT
- **JSON 字段处理**：`modules` 和 `config` 在数据库中可能是字符串，读取后需 `json.loads()`
- **列表页和设计器发布**：共用 `confirmPublishFromPreview`，调用 `templateAPI.update` + `templateAPI.publish`

## 开发规范（重要！）

### ⚠️ 数据库变更原则（必须遵守）
**如果修改了数据库表和字段，必须加入到系统初始化的数据库初始化中！**

具体要求：
1. **创建迁移脚本**：所有数据库结构变更必须创建迁移脚本，放在 `kflower-backend/app/migrations/` 目录
2. **更新初始化**：如果有数据库初始化脚本（如 `init_db.sql` 或 `init_db.py`），必须同步更新
3. **测试迁移**：在提交前测试迁移脚本是否能在新环境正常运行
4. **记录变更**：在迁移脚本头部注明用途、日期和影响范围

### ⚠️ 依赖管理原则（必须遵守）
**如果修改部分导入了新的依赖库或者项目，必须修改 requirements.txt 文件！**

具体要求：
1. **Python 依赖**：所有新增的 Python 包必须添加到 `kflower-backend/requirements.txt`
2. **前端依赖**：所有新增的 npm 包必须添加到 `kflower-frontend/package.json`
3. **系统依赖**：如果使用了系统级工具（如 Tesseract-OCR），需要记录安装说明
4. **同步更新**：修改了代码逻辑后，同步检查并更新依赖文件

### 前端开发规范
- 页面组件放在 `kflower-frontend/src/pc/views/`
- 公共组件放在 `kflower-frontend/src/common/components/`
- API 接口统一在 `kflower-frontend/src/common/api/index.ts` 中定义
- 使用 Element Plus 作为 UI 组件库

### ⚠️ Vue 3 组件初始化避坑指南（必读！）

**错误类型**：`Cannot read properties of undefined (reading 'xxx')`

**典型场景**：组件有 `ref([])` 或 `ref({})` 初始化的响应式数据，在模板中直接访问 `.property`

**根本原因**：
1. 模板在组件挂载时**同步渲染**
2. `watch` 回调是**异步执行**
3. 初始化逻辑放在 `watch` 中 → 模板渲染时数据还没准备好

**错误示例**：
```javascript
const cellData = ref([])  // 空数组

watch(() => props.options, () => {
  initData()  // ❌ watch 是异步的，模板已经渲染了
})

// 模板中：<div>{{ cellData[0].name }}</div>  // ❌ cellData[0] 是 undefined
```

**正确做法**（三选一）：
```javascript
// 方案1：watch 添加 immediate: true
watch(() => props.options, () => { initData() }, { immediate: true })

// 方案2：使用 onMounted + nextTick
onMounted(() => { nextTick(() => initData()) })

// 方案3：使用 v-if 控制渲染时机
// <MatrixInput v-if="props.options.length > 0" ... />
```

**防御性编程原则**：
1. 模板中访问数组元素前，检查长度
2. 访问对象属性前，检查对象是否存在
3. 使用可选链 `?.` 和空值合并 `??`

**检查清单**（每次创建新组件时）：
- [ ] 响应式数据有合理的初始值
- [ ] 初始化函数在 `onMounted` 或 `immediate: true` 的 watch 中调用
- [ ] 模板中没有直接访问可能为空的数组索引或对象属性

### 后端开发规范
- API 端点放在 `kflower-backend/app/api/v1/endpoints/`
- 数据模型放在 `kflower-backend/app/models/`
- Schema 定义放在 `kflower-backend/app/schemas/`
- 业务逻辑放在 `kflower-backend/app/services/`

## 近期重要修改

### 2026-07-22 - 全阶段优化（Phase 1-4 全部执行完成）
- **Phase 1 清理**：删除 9 后端 mock 端点 + 15 前端死代码 + Provider 配置统一
- **Phase 2 Agent 重构**：删除 4 伪 Agent → 统一 UnifiedReactAgent（agent_service ReAct）；AgentType 精简；chat 首次加载缓存
- **Phase 3 前端重整**：菜单 20+→10+2 子菜单；AI 6 入口→1「AI 能力中心」；创建 AICenter.vue
- **Phase 4 安全加固**：路径穿越防护（_resolve_safe_path）、bash 白名单、SQL 列名验证
- **未涉及数据库变更**
- **后端路由总数**：288 → 279

### 2026-05-04 - 矩阵模板操作流程优化
- **问题**：矩阵模板数据列表的操作按钮和普通模板混淆，"填表"按钮没有反应
- **修改**：
  - `FormListPage.vue`：重构矩阵模板的操作流程
    - 矩阵模板显示独立的矩阵数据列表（包含查看、编辑、删除按钮）
    - 添加"新增矩阵数据"按钮，打开类似 Excel 的 MatrixInput 编辑界面
    - 添加"查看矩阵数据"弹窗，使用 MatrixView 组件展示
    - 添加"编辑矩阵数据"弹窗，使用 MatrixInput 组件编辑
  - `Templates.vue`：`openFormSubmit` 函数添加矩阵模板检测
    - 矩阵模板点击"填表"跳转到数据列表页
    - 普通模板点击"填表"打开填表弹窗
- **核心逻辑**：
  - 矩阵数据存储在 `__matrix_data` 字段中（一维数组格式）
  - `getMatrixInfo()` 函数解析并显示矩阵数据概要（行×列、数据点数量）
  - MatrixView 用于查看，MatrixInput 用于编辑

### 2026-06-23 - 工作流与智能体全面升级
- **扫描**：发现 18 个问题（2 致命 + 4 高危 + 8 中等 + 4 低危）
- **后端修复 13 项**：
  - engine.py：添加 SLAManager 导入、实现真实通知发送、并行网关 asyncio.gather 并发、TASK/CC/DATA_FILL 节点区分
  - executor.py：_execute_workflow 改用 WorkflowEngine.start_instance
  - orchestrator.py：新增 is_running()/get_task_statistics()/get_tasks() 方法
  - agent_service.py：新增 list_agents() 方法
  - ai_agent_engine.py：修复 /v1/chat/completions 拼写、移除所有模拟数据回退
  - schemas.py + agent.py：统一 ChatRequest Schema
  - sla_manager.py：实现真实催办通知 + 升级通知
  - condition_evaluator.py：LOOKUP 函数实现真实数据库查询
  - **新增** notifications 表（`app/models/notification.py` + 迁移脚本）
- **前端修复 3 项**：
  - api/index.ts：workflowAPI 新增 enable/disable/getPendingInstances/approveTask/rejectTask
  - pc/views/Workflows.vue：替换原生 fetch 为统一 API 调用
  - 删除 dead code：common/pc/views/{Workflows,WorkflowDesigner}.vue
  - 删除备份文件：engine.py.backup, WorkflowDesigner.vue.backup
- **验证**：所有模块导入通过、FastAPI 286 路由正常加载、数据库迁移成功

### 2026-05-03 - Excel 导入功能
- **前端**：`FormListPage.vue` 添加 Excel 导入对话框（3 步向导）
- **后端**：优化 `templates.py` 的 `import_template_data` 端点，支持字段名和标签两种映射方式
- **依赖**：前端使用 `xlsx` 库解析 Excel
- **注意**：本次修改未涉及数据库变更

### 2026-05-02 - 数据库类型一致性修复
- 修复 `workflow_node_mapping` 字段类型不一致问题
- 教训：修复数据库相关错误时，必须同步修复模型默认值

### 2026-05-01 - 里程碑 1.0 打包准备
- 修复应用保存 422 错误（`ApplicationUpdate` Schema 字段类型修正）
- 创建用户手册和打包部署方案
- 项目达到里程碑 1.0 状态

## 常见问题排查

### 后端启动失败
- 检查 `kflower-backend/app/api/v1/endpoints/` 下文件是否有语法错误
- 检查路由注册顺序（精确路由必须在通配路由之前）

### 前端 API 调用失败
- 检查 `kflower-frontend/src/common/api/index.ts` 中的 API 路径是否正确
- 检查后端是否返回了正确的响应格式

### 数据库迁移失败
- 检查迁移脚本中的 SQL 语法
- 检查模型定义是否与数据库一致
- 必要时手动执行 SQL 修复

---
**最后更新**：2026-07-22
**更新人**：AI Assistant
**更新原因**：全阶段优化完成（Phase 1-4）
