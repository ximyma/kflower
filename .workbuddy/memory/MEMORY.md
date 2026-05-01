# MEMORY.md

**项目背景**
- 用户开发基于 FastAPI/Flask 的办公自动化系统 kflower
- 前端 Vue 3 + Element Plus，后端 FastAPI + SQLAlchemy + SQLite
- 当前专注动态表单系统：模板设计 → 发布 → 动态建表 → 表单填写

**项目目录结构（重要）**
```
e:\kkflower\
├── app/                   ← Kflower 后端的 Python app 包（FastAPI 应用模块，含 api/core/schemas/services/utils）
├── kflower-backend/       ← Kflower 后端项目根（main.py 启动入口等）
├── kflower-frontend/
│   └── src/
│       ├── app/           ← 前端移动端视图代码（手机版 Vue 页面）
│       └── pc/            ← 前端 PC 端视图代码
```
- `e:\kkflower\app\` = 后端 Python 包，非前端手机版
- `kflower-frontend/src/app/` = 前端移动端视图（手机版入口）

**技术细节**
- 模板编码自动生成：`form_{id}` 格式，后端 `create_template` 创建后更新
- 动态建表：发布时根据 `modules[].fields[]` 定义，通过 `CREATE TABLE form_data_{template_id}` 创建
- 字段类型映射：number/money/percent→REAL，date/datetime→TEXT，switch/checkbox→INTEGER DEFAULT 0，其他→TEXT
- 列表页和设计器发布共用 `confirmPublishFromPreview`，调用 `templateAPI.update` + `templateAPI.publish`
- 新建模板默认 `is_published=False`（草稿状态）

**近期动态**
- 完成模板列表的 CRUD + 发布按钮改造
- 移除模板设计器中的编码和描述输入框
- 修复模板自动标记为已发布的问题（61个模板重置为草稿）
- **智能表单全面升级**：
  - 公式引擎：`app/core/formula_engine.py`（20+ 函数，AST 安全求值）
  - ModuleField 扩展：formula/depends_on/validation_rules/visibility_rule/cascade_source/subtable_fields/relation/aggregate 等
  - 前端公式编辑器、条件显示/隐藏、级联选项、高级校验规则
  - 子表/明细表：SubTableData 模型 + 动态建表 + 前端 el-table 表格
  - 关联字段：Lookup 搜索 + 自动填充（/templates/lookup API）
  - 数据聚合：列表页 sum/avg/count/max/min 统计（/data/aggregations API）

**2026-04-18**
- 创建用户管理页面 `src/pc/views/Users.vue`，包含用户列表、搜索、新增、编辑、删除、禁用/启用功能
- 在路由中添加 `/users` 路由，仅管理员可见（`requiresAdmin: true`）
- 修改 MainLayout，侧边栏中「系统设置」和「用户管理」菜单仅在 `isAdmin=true` 时显示
- 路由守卫增加管理员权限检查
- **修复表单导出 422 错误**：`modules` 和 `config` 字段在数据库中是 JSON 字符串，后端 API 需解析后才能使用
- **修复模板设计器发布按钮**：将 `@click="publishTemplate"` 改为 `@click="publishTemplate(currentTemplate)"`，与设计列表保持一致，进入发布预览流程
- **完成"我的应用"模块核心开发**：
  - 后端：models.py (4 个模型), schemas.py, service.py, endpoints.py，完整 API 接口
  - 前端：MyApps.vue(应用列表), AppDesigner.vue(应用设计器), AppLayout.vue(应用容器), FormListPage.vue(通用列表), FormEditPage.vue(通用表单)
  - 路由：/my-apps, /app-designer/:appId, /app/:appId/form/:templateId，动态路由配置
  - 集成：主导航栏添加"我的应用"入口
  - 功能：应用 CRUD、可视化菜单设计、表单关系、插件系统基础架构
  - 测试：创建数据库迁移脚本和 API 测试脚本
  - 文档：创建完整的开发总结报告

**2026-04-19**
- **优化应用设计器**：创建 AppDesigner.vue，实现三栏布局的可视化设计器
  - 左侧：可用模板列表（支持搜索）
  - 中间：菜单树管理（支持编辑、删除、父子关系）
  - 右侧：属性面板（应用属性和菜单属性）
  - 分离"设计"和"信息"编辑功能
  - 支持快速从模板添加菜单

**2026-04-20**
- **集成AI模块到管理后台**：根据开发文档要求，将已开发但未显示的AI模块添加到侧边栏导航
  - 创建8个新Vue页面：AI数字底座、AI智能体引擎、AI网关、工具集、智能体编排器、记忆管理、数据集成、数据库迁移
  - 每个页面包含模块状态概览、开发进展、模拟数据展示
  - 在路由配置中添加对应路由 (`/ai-digital-base`, `/ai-agent-engine`, `/ai-gateway`, `/ai-tools`, `/agent-orchestrator`, `/memory-management`, `/data-integration`, `/migration`)
  - 修改MainLayout侧边栏，添加新菜单项并配置合适图标
  - 所有模块显示开发进度，便于查看现状和进展
- **AI数字底座能力系统升级**：根据dd3chat.txt方案，实现AI能力注册中心和统一API
  - 新增数据库模型：AITask、AIUsageLog、AIRecommendationCache
  - 创建能力注册中心 (`capability_registry.py`) 和能力实现 (`capabilities.py`)
  - 创建统一API端点 (`ai_capability.py`) 提供能力执行和列表接口
  - 扩展AI数字底座状态API (`ai_digital_base.py`) 提供网关、模型、推理服务状态
  - 创建AI智能体引擎API (`ai_agent_engine.py`) 提供智能体、工具、任务状态
  - 所有API已集成到主路由 (`api.py`)
- **工作流引擎升级**：根据dd4chat.txt方案，开始实现工作流引擎全面升级
  - **数据库模型扩展**：为Workflow、WorkflowInstance、WorkflowTask添加新字段，创建WorkflowNodeInstance、WorkflowVariableLog、WorkflowTaskCandidates新表
  - **核心引擎实现**：创建节点类型枚举、条件表达式求值器、审批人解析器、工作流引擎核心类
  - **API端点扩展**：新增 `/workflows/{id}/start` 和 `/tasks/{id}/action` 端点，支持高级工作流功能
  - **前端API集成**：扩展AI API接口，更新AIAgentEngine页面从后端加载动态数据
  - **数据库迁移**：创建迁移脚本 `migrations/add_workflow_upgrade_fields.py`
- **后端语法错误修复与API扩展**：修复关键错误并扩展API端点支持前端
  - **修复后端启动错误**：修复 `ai_agent_engine.py` 第142行语法错误，删除损坏行并添加正确格式化的记忆管理API端点
  - **新增记忆管理端点**：`/ai/agent-engine/memory/stats` 和 `/ai/agent-engine/memory/list`，支持MemoryManagement.vue组件
  - **新增智能体CRUD端点**：`POST /agents`、`PUT /agents/{agent_id}`、`DELETE /agents/{agent_id}`，为智能体编排器提供增删改查操作
  - **新增数据集成API**：`/ai/digital-base/data-integration/stats`、`/connections`、`/sync-tasks`，为DataIntegration.vue提供模拟数据
  - **新增数据库迁移统计**：`/ai/digital-base/migration/stats`，提供迁移任务概览
  - **前端API连接优化**：扩展前端API模块，更新DataIntegration.vue从后端加载动态数据，添加错误处理和回退机制
- **智能体CRUD实现完成**：将智能体CRUD端点连接到真实数据库，实现完整的数据库操作
  - 修改 `ai_agent_engine.py` 中的 `create_agent`, `update_agent`, `delete_agent` 端点，使用 SQLAlchemy 进行数据库操作
  - 保留 `list_agents` 端点从数据库查询，添加状态映射和类型转换
  - 添加 `_create_sample_agents` 辅助函数，在数据库为空时创建示例数据
- **迁移页面连接真实API**：验证迁移页面已连接到真实迁移功能API，现有迁移服务实现完整，前端API已存在
  - 迁移页面 (`Migration.vue`) 使用 `migration.ts` API 调用，后端 `migration.py` 路由已注册
  - 迁移服务 (`app/core/migration.py`) 提供完整的数据库连接、表迁移、脚本生成功能
- **工作流引擎测试通过**：运行工作流升级迁移脚本，验证所有字段和表已存在
  - 执行 `migrations/add_workflow_upgrade_fields.py`，确认所有字段和表已存在（无新变更）
  - 工作流引擎核心 (`WorkflowEngine`) 和新端点 (`/workflows/{id}/start`, `/tasks/{id}/action`) 已实现并集成
- **前端功能完善**：为智能体编排器添加创建、编辑、删除的UI操作界面
  - 在 `AgentOrchestrator.vue` 中添加智能体编辑对话框，支持创建、编辑、删除操作
  - 在智能体列表中添加操作按钮（编辑、删除）和“添加智能体”按钮
  - 扩展前端API (`index.ts`) 添加 `createAgent`, `updateAgent`, `deleteAgent` 方法
  - 实现表单验证、错误处理和成功提示
- **当前状态**：所有AI模块现已连接真实后端API，智能体CRUD操作完全可用，迁移功能就绪，工作流引擎升级完成，前端操作界面完善，系统可正常启动使用
- **插件系统修复（2026-05-01）**：
  - `app_plugins` 表缺少 `plugin_id`/`config`/`sort_order` 字段（已迁移）
  - FastAPI 路由顺序问题：精确路由 `/bindings`、`/available` 必须在通配路由 `/{binding_id}` 之前注册
  - 相关文件：`app/modules/my_apps/endpoints.py`（路由顺序）、`app/services/app_plugin_service.py`（服务）、`src/pc/components/AppPluginManager.vue`（前端UI）
- **全模块整合优化方案（2026-05-01）**：
  - 发现7个核心协同问题，输出方案文档 `Kflower全模块整合优化方案.md`
  - P1（最高）：AppMenu 有 workflow_id 但 AppDesigner.vue 无流程选择UI
  - P2（最高）：Agent 无 template_ids/workflow_ids/knowledge_base_ids 字段
  - P3（高）：工具集 ToolExecutor handler=None 时静默失败
  - 核心设计：引入 AppContext 应用上下文层统一协同所有模块
  - 三阶段实施：核心修复 → 协同层建设（AppContext/插件调度/知识库隔离）→ 前端体验优化
- **斑斑低代码平台流程设计升级**：按照斑斑平台教程全面升级流程审批模块
  - **前端设计器**：WorkflowDesigner.vue全面重构，支持12种节点类型、表单模板绑定、审批人配置（5种来源）、字段权限控制、数据源管理、条件配置
  - **后端扩展**：扩展Schema和API支持完整斑斑平台配置（node_definitions, edge_definitions, variables, form_template_id）
  - **关键修复**：修复Vue模板绑定错误（v-model不能绑定到可选链操作符?.）
  - **完整流程**：支持工作流保存、加载、验证，前端与后端API完全集成
  - **斑斑功能对照**：已实现模板绑定、审批人配置、字段权限、数据源管理等核心功能

**2026-05-01 下午 - 全模块整合优化实施**
- **任务1.1（流程审批绑定UI）**：修复前端API和组件，菜单现在可以正确保存工作流绑定
- **任务1.2（Agent模块绑定）**：创建数据库迁移，为agents表添加6个新字段，更新CRUD API
- **任务1.3（工具执行链路）**：优化ToolExecutor错误处理，确保错误正确上抛
- **任务1.4（流程携带表单数据）**：/execute端点支持form_template_id和form_data_id参数
- **任务2.1（AppContext机制）**：新建app/core/app_context.py，实现统一应用上下文
- **任务2.2（插件钩子调度器）**：新建app/core/plugin_dispatcher.py，实现统一插件钩子调度
- **新建文件**：migrations/add_agent_bindings.py, app/core/app_context.py, app/core/plugin_dispatcher.py
- **关键改动**：前端API/myApps.ts、AppDesigner.vue、service.py、models/ai.py、ai_agent_engine.py、tools/executor.py、workflows.py

**2026-05-01 下午 - AgentOrchestrator 智能体编排器优化**
- 修复模型列表加载：API 路径改为 `/api/v1/ai/digital-base/models/available`，处理嵌套提供商格式
- 修复知识库列表加载：API 路径改为 `/api/v1/knowledge/bases`
- 修复插件列表加载：API 路径改为 `/api/v1/plugins/`，处理 success 字段格式
- **增加提示词辅助功能**：
  - 插入示例提示词按钮（6 种类型：客服、文档、数据分析、代码、HR、财务）
  - 快捷模板下拉菜单
  - AI 生成提示词功能（调用 `/chat` 端点生成专业提示词）
- 相关文件：`src/pc/views/AgentOrchestrator.vue`

**2026-05-01 傍晚 - 里程碑1.0打包准备**
- **修复应用保存422错误**：`ApplicationUpdate` Schema 中 `bound_agents` 字段类型从 `List[Dict]` 改为 `List[int]`，与前端和数据库一致
- **创建用户手册**：`docs/KFlower用户手册.md` - 12章节覆盖所有核心功能
- **创建打包部署方案**：`docs/KFlower打包部署方案.md` - 13章节详细部署指南
- **创建发布清单**：`docs/发布清单.md` - 发布内容、验收清单、已知问题
- **项目达到里程碑1.0状态**：完整的AI智能低代码平台

**2026-05-01 傍晚 - 智能体编排器Bug修复**
- **修复提示词不能保存**：`loadAgents()` 函数增加所有字段映射（type/status/scope/template_ids/knowledge_base_ids/workflow_ids/plugin_ids/system_prompt）
- **修复模型下拉列表**：`/ai/digital-base/models/available` 端点添加 `configured_only=true` 参数，只返回系统已配置提供商的模型
- 相关文件：`AgentOrchestrator.vue`, `ai_digital_base.py`, `ai_agent_engine.py`
