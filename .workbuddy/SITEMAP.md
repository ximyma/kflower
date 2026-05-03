# Kflower 项目导航地图 (Sitemap)

> 本文件是 Kflower 项目的结构导航清单。每次对话开始时应加载此文件，以便快速定位问题和功能模块。
>
> **使用方式**：当你描述问题时，请参考此地图提供相关模块位置和关键词。

---

## 📁 项目结构概览

```
D:\kkflower\
├── kflower-backend/           # 后端 Python 项目 (FastAPI)
│   ├── app/
│   │   ├── api/v1/endpoints/ # API 端点
│   │   ├── core/             # 核心业务逻辑
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── services/          # 业务服务层
│   │   └── utils/             # 工具函数
│   └── main.py                # 应用入口
│
├── kflower-frontend/          # 前端 Vue3 项目
│   └── src/
│       ├── pc/                # PC 端视图
│       ├── app/               # 移动端视图
│       ├── common/             # 公共组件/API
│       └── main.ts            # 前端入口
│
└── .workbuddy/               # AI 工作区配置
```

---

## 🔌 后端 API 端点 (api/v1/endpoints/)

| 端点文件 | 主要功能 | 关键路由 |
|---------|---------|---------|
| **auth.py** | 用户认证、登录注册、令牌管理 | `/auth/login`, `/auth/register`, `/auth/me` |
| **users.py** | 用户管理、个人资料 | `/users/me`, `/users/{id}` |
| **templates.py** | 表单模板 CRUD、发布、导入 | `/templates`, `/templates/{id}/publish` |
| **workflows.py** | 工作流设计、执行、审批 | `/workflows`, `/workflows/{id}/execute` |
| **analytics.py** | 数据分析、统计报表 | `/analytics/*` |
| **knowledge.py** | 知识库管理、RAG 检索 | `/knowledge/*` |
| **plugins.py** | 插件管理、安装卸载 | `/plugins/*` |
| **system.py** | 系统配置、健康检查 | `/system/*`, `/system/health` |
| **ai.py** | AI 通用接口 | `/ai/*` |
| **local_ai.py** | 本地 AI 配置 (OCR/Embedding) | `/local-ai/*` |
| **agent.py** | AI 智能体管理 | `/agent/*` |
| **ai_agent_engine.py** | AI 智能体编排引擎 | `/ai-agent-engine/*` |
| **ai_capability.py** | AI 能力管理 | `/ai-capability/*` |
| **ai_digital_base.py** | AI 数字底座 | `/ai-digital-base/*` |
| **dashboard.py** | 仪表盘数据 | `/dashboard/*` |
| **notifications.py** | 通知管理 | `/notifications/*` |
| **organizations.py** | 组织管理 | `/organizations/*` |
| **permissions.py** | 权限管理 | `/permissions/*` |
| **import_.py** | 数据导入 | `/import/*` |
| **data_model.py** | 数据模型设计 | `/data-model/*` |
| **doc_converter.py** | 文档转换 | `/doc-converter/*` |

---

## 🗄️ 后端数据库模型 (models/)

| 模型文件 | 主要实体 | 关键字段 |
|---------|---------|---------|
| **user.py** | 用户表 | id, username, email, hashed_password |
| **ai.py** | AI 配置表 | id, provider, model_name, config |
| **data_model.py** | 数据模型表 | id, name, fields (JSON) |
| **workflow.py** | 工作流表 | id, name, nodes (JSON), edges (JSON) |
| **plugin.py** | 插件表 | id, name, version, code |
| **plugin_binding.py** | 插件绑定表 | id, plugin_id, target_type, target_id |
| **permission.py** | 权限表 | id, name, resource, action |
| **notification_template.py** | 通知模板表 | id, name, type, content |

---

## ⚙️ 后端核心服务 (services/)

| 服务文件 | 主要功能 | 关键方法 |
|---------|---------|---------|
| **template_service.py** | 模板服务 | create_template, update_template, publish_template |
| **workflow_service.py** | 工作流服务 | create_workflow, execute_workflow |
| **import_service.py** | 导入服务 ⭐ | parse_excel_or_csv, import_template_data |
| **analytics_service.py** | 分析服务 | get_form_stats, get_workflow_stats |
| **permission_service.py** | 权限服务 | check_permission, grant_permission |
| **system_service.py** | 系统服务 | get_system_config, update_config |
| **migration_service.py** | 迁移服务 | migrate, rollback |
| **integration_service.py** | 集成服务 | integrate, sync_data |
| **app_plugin_service.py** | 应用插件服务 | install_plugin, uninstall_plugin |
| **template_plugin_service.py** | 模板插件服务 | load_plugins, execute_plugin |
| **model_to_template.py** | 模型转模板 | convert, generate_template |
| **kflower_table_analyzer.py** | 表格分析 | analyze_table, extract_fields |

---

## 🤖 AI 相关模块 (core/ai_digital_base/, core/agent_engine/)

| 模块 | 路径 | 功能 |
|-----|------|-----|
| **数字底座** | `core/ai_digital_base/` | 本地 AI 服务管理 |
| - capabilities.py | | AI 能力定义和注册 |
| - local_services.py | | 本地 AI 服务实现 |
| - model_manager.py | | 模型加载和管理 |
| - rag.py | | RAG 检索增强生成 |
| - inference.py | | AI 推理接口 |
| - gateway.py | | AI 网关 |
| - conversation.py | | 对话管理 |
| **智能体引擎** | `core/agent_engine/` | AI 智能体编排 |
| - orchestrator.py | | 编排器 |
| - planner.py | | 计划器 |
| - query_agent.py | | 查询智能体 |
| - template_agent.py | | 模板生成智能体 |
| - analytics_agent.py | | 分析智能体 |
| - tools/executor.py | | 工具执行器 |
| - tools/registry.py | | 工具注册表 |

---

## 📱 后端工作流引擎 (core/workflow/)

| 文件 | 功能 |
|-----|------|
| **engine.py** | 工作流引擎核心 |
| **node_types.py** | 节点类型定义 |
| **condition_evaluator.py** | 条件评估器 |
| **assignee_resolver.py** | 审批人解析器 |
| **sla_manager.py** | SLA 管理器 |

---

## 🎨 前端 PC 端视图 (pc/views/)

| 视图文件 | 页面功能 | 路由 |
|---------|---------|------|
| **Home.vue** | 首页仪表盘 | `/home` |
| **Templates.vue** ⭐ | 模板设计/列表 | `/templates` |
| **AppDesigner.vue** | 应用设计器 | `/app-designer` |
| **AppLayout.vue** | 应用布局 | `/app/:id` |
| **FormData.vue** | 表单数据管理 | - |
| **FormListPage.vue** | 表单列表页 | `/form/:templateId` |
| **FormEditPage.vue** | 表单编辑页 | `/form/:templateId/edit/:id` |
| **FormFill.vue** | 表单填写页 | `/form/:templateId/fill` |
| **Workflows.vue** | 工作流管理 | `/workflows` |
| **WorkflowDesigner.vue** | 工作流设计器 | `/workflow/designer/:id` |
| **Knowledge.vue** | 知识库管理 | `/knowledge` |
| **Analytics.vue** | 数据分析 | `/analytics` |
| **Settings.vue** | 系统设置 | `/settings` |
| **Migration.vue** | 数据迁移 | `/migration` |
| **AgentOrchestrator.vue** | AI 智能体编排 | `/agent/orchestrator` |
| **AIAgentEngine.vue** | AI 智能体引擎 | `/ai-agent-engine` |
| **AIDigitalBase.vue** | AI 数字底座 | `/ai-digital-base` |
| **AIGateway.vue** | AI 网关 | `/ai-gateway` |
| **AITools.vue** | AI 工具管理 | `/ai-tools` |
| **DataModeling.vue** | 数据建模 | `/data-modeling` |
| **DataModelDesigner.vue** | 数据模型设计器 | `/data-model/designer` |
| **DataModelImport.vue** | 数据模型导入 | `/data-model/import` |
| **DataIntegration.vue** | 数据集成 | `/data-integration` |
| **MemoryManagement.vue** | 记忆管理 | `/memory` |
| **DocConverter.vue** | 文档转换 | `/doc-converter` |

### 我的应用模块 (pc/views/my-apps/)

| 视图文件 | 功能 |
|---------|-----|
| **AIAppDesigner.vue** | AI 应用设计器 |
| **AppDesigner.vue** | 应用设计器 |
| **AppDashboard.vue** | 应用仪表盘 |

---

## 📱 前端移动端视图 (app/views/)

| 视图文件 | 功能 |
|---------|-----|
| **Home.vue** | 移动端首页 |
| **Templates.vue** | 模板列表 |
| **AppDesigner.vue** | 应用设计 |
| **FormFill.vue** | 表单填写 |
| **Agents.vue** | 智能体 |
| **AIBase.vue** | AI 数字底座 |
| **AITools.vue** | AI 工具 |
| **Chat.vue** | 聊天 |
| **Knowledge.vue** | 知识库 |
| **WorkflowDesigner.vue** | 工作流设计 |
| **Workflows.vue** | 工作流列表 |
| **Workspace.vue** | 工作空间 |
| **Profile.vue** | 个人资料 |

---

## 🔧 前端公共模块 (common/)

| 目录/文件 | 功能 |
|---------|------|
| **api/index.ts** | API 接口定义统一出口 |
| **api/templatePlugin.ts** | 模板插件 API |
| **api/appPlugin.ts** | 应用插件 API |
| **api/myApps.ts** | 我的应用 API |
| **api/migration.ts** | 迁移 API |
| **components/AIChatButton.vue** | AI 聊天按钮 |
| **components/AIChatDialog.vue** | AI 聊天对话框 |
| **store/ai.ts** | AI 状态管理 |
| **store/user.ts** | 用户状态管理 |
| **views/Login.vue** | 登录页 |
| **views/Register.vue** | 注册页 |
| **pc/layouts/MainLayout.vue** | PC 端主布局 |
| **mobile/views/** | 移动端视图 |

---

## 🔑 功能关键词速查

### 用户相关
- **登录/注册**: `auth.py` + `Login.vue` + `Register.vue`
- **权限**: `permissions.py` + `permission_service.py`
- **用户管理**: `users.py`

### 表单/模板
- **模板设计**: `templates.py` + `Templates.vue` + `template_service.py`
- **模板发布**: `publish_template()` in `templates.py`
- **数据导入**: `import_.py` + `import_service.py` + `FormData.vue`
- **表单填写**: `FormFill.vue` + `FormListPage.vue`
- **动态表单**: 模板设计 → 动态建表 → 表单填写

### 工作流
- **工作流设计**: `workflows.py` + `WorkflowDesigner.vue`
- **工作流执行**: `workflow_service.py` + `core/workflow/engine.py`
- **审批流程**: `workflow.py` 模型

### AI 功能
- **OCR 配置**: `local_ai.py` + `Settings.vue` (OCR 部分)
- **Embedding**: `local_ai.py` + `Settings.vue` (Embedding 部分)
- **AI 智能体**: `agent_engine/` + `AgentOrchestrator.vue`
- **RAG 检索**: `rag.py` + `knowledge.py`
- **数字底座**: `ai_digital_base/` + `AIDigitalBase.vue`

### 数据分析
- **统计报表**: `analytics.py` + `analytics_service.py` + `Analytics.vue`
- **仪表盘**: `dashboard.py`

### 插件系统
- **插件管理**: `plugins.py` + `PluginManager.vue`
- **插件执行**: `plugin_executor.py`

---

## 💡 如何描述问题

请按以下格式描述：

1. **功能模块**: 你在做什么操作？（如：模板设计、表单填写、工作流审批）
2. **问题现象**: 出现了什么错误或异常行为？
3. **相关文件**: 如果知道，告诉我相关的文件路径
4. **错误信息**: 控制台或后端的错误日志

### 示例

❌ **不好**: "表单有问题"
✅ **好**: "在模板设计页面上传 Excel 文件时，提示 'CSV 文件编码不受支持'，错误出现在 `import_service.py` 的 `parse_excel_or_csv` 函数"

❌ **不好**: "AI 不工作"
✅ **好**: "配置了本地 Embedding 模型后，系统设置页面仍显示 'Embedding API 未配置'，可能是 `system.py` 的健康检查逻辑有问题"

---

## 📍 快速定位表

| 问题类型 | 优先检查 |
|---------|---------|
| 前端页面报错 | 对应 `.vue` 文件 + 浏览器控制台 |
| 后端 API 报错 | `api/v1/endpoints/` 对应文件 + 终端日志 |
| 数据库问题 | `models/` 对应模型 + `services/` 对应服务 |
| AI 功能异常 | `core/ai_digital_base/` 或 `local_ai.py` |
| 工作流异常 | `core/workflow/` + `workflows.py` |
| 导入导出问题 | `import_service.py` + `FormData.vue` |
| 权限问题 | `permissions.py` + `permission_service.py` |
| 插件问题 | `plugins.py` + `plugin_service.py` |

---

**最后更新**: 2026-05-03
**维护者**: AI Assistant
