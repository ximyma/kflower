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
