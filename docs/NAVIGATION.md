# Kflower 程序导航地图

> **项目名称**: Kflower 企业智能管理低代码平台  
> **创建日期**: 2026-05-04  
> **最后更新**: 2026-05-04  
> **用途**: 项目文档和代码结构的导航索引

---

## 📁 文档目录

本文档提供 Kflower 项目的完整导航，包括：
- 项目概述
- 文档索引
- 代码结构设计
- 开发指南
- 常见问题

---

## 📋 文档索引

| 文档名称 | 文件路径 | 描述 |
|-----------|-----------|-----------|
| **项目 README** | `D:\kkflower\README.md` | 项目概述、快速启动、功能模块 |
| **Templates.vue 代码结构** | `D:\kkflower\docs\Templates_Vue_Structure.md` | Templates.vue 完整函数清单和代码结构 |
| **程序导航地图** | `D:\kkflower\docs\NAVIGATION.md` | 本文档 - 项目导航索引 |

---

## 🏗️ 项目结构概览

```
D:\kkflower\
├── kflower-backend/       ← 后端项目根（main.py 启动入口）
│   └── app/              ← 后端 Python 包
│       ├── api/         ← API 端点（FastAPI 路由）
│       ├── core/        ← 核心模块（AI 数字底座、智能体引擎）
│       ├── models/      ← 数据库模型（SQLAlchemy）
│       ├── schemas/     ← Pydantic Schema
│       ├── services/    ← 业务逻辑层
│       └── migrations/  ← 数据库迁移脚本
│
├── kflower-frontend/
│   └── src/
│       ├── app/        ← 前端移动端视图（手机版）
│       ├── common/      ← 公共组件和 API
│       └── pc/         ← 前端 PC 端视图
│           ├── views/    ← 页面组件（Templates.vue 等）
│           └── components/ ← 公共组件
│
├── .workbuddy/          ← WorkBuddy 工作区（勿删）
│   └── memory/        ← 工作记忆文件
│
├── docs/                ← 项目文档（新建）
│   ├── Templates_Vue_Structure.md
│   └── NAVIGATION.md（本文档）
│
└── README.md           ← 项目说明文档
```

---

## 🎨 前端代码结构

### 页面视图（PC 端）

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **Templates.vue** | `kflower-frontend/src/pc/views/Templates.vue` | 模板设计器主页面（列表 + 设计器） |
| **FormListPage.vue** | `kflower-frontend/src/pc/views/FormListPage.vue` | 表单数据列表页面 |
| **DataModeling.vue** | `kflower-frontend/src/pc/views/DataModeling.vue` | 数据建模页面 |

### 公共组件

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **TemplatePluginManager.vue** | `kflower-frontend/src/pc/components/TemplatePluginManager.vue` | 模板插件管理器 |
| **MatrixView.vue** | `kflower-frontend/src/pc/components/MatrixView.vue` | 矩阵数据查看组件 |
| **MatrixInput.vue** | `kflower-frontend/src/pc/components/MatrixInput.vue` | 矩阵数据输入组件 |

### 公共 API 和 Store

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **api/index.ts** | `kflower-frontend/src/common/api/index.ts` | API 接口定义 |
| **ai.ts** | `kflower-frontend/src/common/store/ai.ts` | AI Store（Pinia） |
| **user.ts** | `kflower-frontend/src/common/store/user.ts` | User Store（Pinia） |

---

## 🔧 后端代码结构

### API 端点

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **templates.py** | `kflower-backend/app/api/v1/endpoints/templates.py` | 模板相关 API |
| **import.py** | `kflower-backend/app/api/v1/endpoints/import.py` | 导入功能 API（Excel/图片/矩阵） |
| **data.py** | `kflower-backend/app/api/v1/endpoints/data.py` | 数据提交和管理 API |

### 服务层

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **template_service.py** | `kflower-backend/app/services/template_service.py` | 模板业务逻辑 |
| **import_matrix_service.py** | `kflower-backend/app/services/import_matrix_service.py` | 矩阵表格导入服务 |
| **formula_service.py** | `kflower-backend/app/services/formula_service.py` | 公式解析和计算服务 |

### 模型层

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **template.py** | `kflower-backend/app/models/template.py` | 模板数据库模型 |
| **form_data.py** | `kflower-backend/app/models/form_data.py` | 表单数据模型 |

---

## 📚 常用功能修改指南

### 1. 添加新的字段类型

**涉及文件**：
- `Templates.vue`（字段类型定义、属性面板）
- `FormListPage.vue`（数据输入组件）
- 后端 `template_service.py`（字段验证）
- 后端 `form_data.py`（数据存储）

**步骤**：
1. 在 `Templates.vue` 的 `fieldTypes` 数组中添加新类型
2. 在属性面板（Template）中添加对应的配置项
3. 在 `FormListPage.vue` 中添加对应的输入组件
4. 更新后端服务和模型（如需要）

### 2. 修改导入逻辑

**涉及文件**：
- `Templates.vue`（前端导入函数）
- `import.py`（后端导入 API）
- `import_matrix_service.py`（矩阵导入服务）

**关键函数**：
- 前端：`doParseFile()`, `applyHeaderRow()`, `applyMatrixHeader()`
- 后端：`/api/v1/import/parse`, `/api/v1/import/matrix/apply-header`

### 3. 修改公式功能

**涉及文件**：
- `Templates.vue`（公式编辑器、验证、计算）
- `formula_service.py`（后端公式解析器）

**关键函数**：
- 前端：`validateFieldFormula()`, `evaluateFormula()`, `computeDataFormulas()`
- 后端：公式解析服务（如有）

---

## 🔍 快速查找代码

### 在 VS Code 中

1. **查找文件**：`Ctrl+P`（Windows/Linux）或 `Cmd+P`（Mac）
2. **查找符号**：`Ctrl+Shift+O` 或 `Cmd+Shift+O`
3. **全局搜索**：`Ctrl+Shift+F` 或 `Cmd+Shift+F`

### 在本文档中

使用 `Ctrl+F` 搜索关键词：
- 文件名（如 `Templates.vue`）
- 函数名（如 `loadTemplates`）
- 功能描述（如 "导入"、"公式"）

---

## 📝 工作记忆文件

| 文件 | 路径 | 描述 |
|------|------|-----------|
| **MEMORY.md** | `.workbuddy/memory/MEMORY.md` | 长期记忆（项目背景、规范、重要修改） |
| **日期记忆文件** | `.workbuddy/memory/YYYY-MM-DD.md` | 每日工作记录 |

**读取时机**：
- 任务涉及 prior context 时，先读取 `MEMORY.md` 和最近的日记文件
- 提交实质性工作后，追加记录到当天的记忆文件

---

## 🚀 快速启动

### 一键启动（推荐）

双击运行 `start_all.bat`

### 分别启动

**后端**：
```bash
cd kflower-backend
python -m uvicorn main:app --host 0.0.0.0 --port 8898 --reload
```

**前端**：
```bash
cd kflower-frontend
npm run dev
```

**访问**：
- 后端 API 文档：http://localhost:8898/docs
- 前端页面：http://localhost:5111

---

## 📊 常见问题

### 1. 后端启动失败

**检查**：
- Python 版本（需要 3.11.3）
- 依赖是否安装（`pip install -r requirements.txt`）
- 端口 8898 是否被占用

### 2. 前端启动失败

**检查**：
- Node 版本（需要 22.22.2）
- 依赖是否安装（`npm install`）
- 端口 5111 是否被占用

### 3. 模板设计器加载失败

**检查**：
- 后端服务是否正常运行
- `templateAPI.list()` 接口是否返回正确格式
- 浏览器控制台是否有错误

### 4. 导入 Excel 失败

**检查**：
- 是否安装 `openpyxl` 和 `pandas`
- 浏览器控制台查看 API 请求是否成功
- 后端日志是否有错误

---

## 📖 文档维护

### 更新本文档

当以下情况发生时，请更新本文档：
1. 添加新的重要文档
2. 修改项目结构
3. 添加新的功能模块
4. 更新常用功能修改指南

### 文档格式规范

- 使用 Markdown 格式
- 包含文件路径（绝对路径）
- 包含函数清单和描述
- 包含更新记录和日期

---

## 📞 联系方式

**项目维护者**：[待填写]  
**创建日期**：2026-05-04  
**最后更新**：2026-05-04  

---

**文档版本**: 1.0  
**项目版本**: Milestone 1.0
