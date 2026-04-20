# MEMORY.md

**项目背景**
- 用户开发基于 FastAPI/Flask 的办公自动化系统 kflower
- 前端 Vue 3 + Element Plus，后端 FastAPI + SQLAlchemy + SQLite
- 当前专注动态表单系统：模板设计 → 发布 → 动态建表 → 表单填写

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
