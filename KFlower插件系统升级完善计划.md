# KFlower 插件系统升级完善计划

## 一、现状分析

### 1.1 已完成的功能（Phase 1 基本完成）

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KFlower 插件系统现状                              │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ 已实现功能                                                      │
│  ├── 数据库模型 (app/models/plugin.py)                              │
│  │   ├── Plugin 模型 - 插件元信息                                  │
│  │   ├── PluginVersion 模型 - 版本历史                              │
│  │   ├── PluginHook 模型 - 钩子定义                                 │
│  │   └── plugin_binding.py - 模板/应用绑定                         │
│  │                                                                  │
│  ├── 插件管理器 (app/core/plugin_manager.py)                        │
│  │   ├── PluginManager - 生命周期管理                               │
│  │   ├── PluginInstance - 插件实例                                  │
│  │   ├── 内置插件注册 (BUILTIN_PLUGINS)                            │
│  │   └── 钩子触发机制 (trigger_hook)                                │
│  │                                                                  │
│  ├── 插件沙箱 (app/core/plugin_sandbox.py)                          │
│  │   ├── RestrictedPython 隔离执行                                  │
│  │   ├── 超时控制 (5秒)                                            │
│  │   └── 日志收集                                                  │
│  │                                                                  │
│  ├── API 接口 (app/api/v1/endpoints/plugins.py)                    │
│  │   ├── 插件 CRUD                                                 │
│  │   ├── 启用/禁用                                                 │
│  │   ├── 模板绑定/解绑                                             │
│  │   └── 钩子测试                                                  │
│  │                                                                  │
│  ├── 前端界面 (src/pc/views/PluginManager.vue)                     │
│  │   ├── 插件列表/筛选                                             │
│  │   ├── 统计卡片                                                  │
│  │   ├── 创建/编辑对话框                                           │
│  │   └── 钩子测试                                                 │
│  │                                                                  │
│  └── 内置插件 (13个)                                               │
│      ├── kflower-calc (计算字段)                                   │
│      ├── kflower-notify (通知提醒)                                 │
│      ├── kflower-workflow (审批流程)                               │
│      ├── kflower-report (数据报表)                                 │
│      ├── kflower-ai (AI助手)                                       │
│      └── tool-* (AI工具集 8个)                                     │
│                                                                      │
│  ⚠️ 待完善功能                                                      │
│  ├── ❌ 模板设计器中集成插件管理                                    │
│  ├── ❌ 应用发布时打包插件                                         │
│  ├── ❌ 可视化插件编辑器                                           │
│  └── ❌ 插件市场                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 迁移计划进度

| 阶段 | 任务 | 状态 | 工时 |
|------|------|------|------|
| Phase 1 | 插件基础设施 | ✅ 基本完成 | 4-6h |
| Phase 2 | 模板级插件嵌入 | ❌ 未开始 | 3-4h |
| Phase 3 | 我的应用集成 | ❌ 未开始 | 2-3h |
| Phase 4 | 可视化插件开发 | ❌ 未开始 | 6-8h |
| Phase 5 | 插件市场 | ❌ 未开始 | 4-6h |

---

## 二、升级完善计划

### 2.1 Phase 2: 模板级插件嵌入（预计 3-4 小时）

#### 目标
在模板设计器中集成插件管理功能，允许用户将插件绑定到特定模板，实现模板级别的功能扩展。

#### 任务清单

**后端任务 (1.5h)**
- [ ] 创建 `app/services/template_plugin_service.py` 服务
  - 模板插件绑定/解绑
  - 模板级别钩子触发
  - 插件配置继承
- [ ] 扩展 `app/api/v1/endpoints/templates.py` 添加插件相关API
  - `GET /templates/{id}/plugins` - 获取模板插件列表
  - `POST /templates/{id}/plugins/bind` - 绑定插件到模板
  - `DELETE /templates/{id}/plugins/{binding_id}` - 解绑插件
  - `PUT /templates/{id}/plugins/{binding_id}` - 更新插件配置

**前端任务 (1.5h)**
- [ ] 在模板设计器中添加插件管理Tab
  - 位置：模板编辑页面 → [基本信息] [字段设计] [表单设计] [列表设计] **[插件管理]** [权限]
  - 功能：查看已绑定插件、添加新插件、配置插件、启用/禁用
- [ ] 创建 `src/pc/views/TemplatePluginManager.vue` 组件
- [ ] 创建 `src/pc/components/PluginBindDialog.vue` 插件绑定对话框

**集成测试 (1h)**
- [ ] 测试插件在表单提交时的触发
- [ ] 测试插件配置的保存和加载
- [ ] 测试内置插件（通知、计算字段）的实际效果

---

### 2.2 Phase 3: 我的应用集成（预计 2-3 小时）

#### 目标
将插件与"我的应用"绑定，在应用发布时自动打包所选插件，实现应用级别的功能扩展。

#### 任务清单

**后端任务 (1h)**
- [ ] 扩展 `AppPlugin` 模型支持插件配置
- [ ] 创建 `app/services/app_plugin_service.py` 服务
- [ ] 扩展应用发布逻辑，自动收集依赖插件

**前端任务 (1h)**
- [ ] 在应用详情页面添加插件管理区域
- [ ] 创建 `src/pc/views/AppPluginManager.vue` 组件
- [ ] 添加应用发布时的插件依赖检查

**数据迁移 (0.5h)**
- [ ] 编写数据迁移脚本，将现有应用与插件关系迁移到新模型

---

### 2.3 Phase 4: 可视化插件开发（预计 6-8 小时）

#### 目标
提供可视化的插件开发工具，降低插件开发门槛，支持在线编写、测试和调试插件代码。

#### 任务清单

**后端任务 (2h)**
- [ ] 增强 `plugin_sandbox.py` 的测试功能
  - 支持模拟不同的触发时机（form_load, form_submit等）
  - 支持预设测试数据
  - 详细的执行日志输出
- [ ] 创建 `app/api/v1/plugin_developer.py` API
  - 代码片段保存/加载
  - 版本历史管理
  - 模板市场发布

**前端任务 (4h)**
- [ ] 创建插件可视化编辑器 `src/pc/views/PluginDesigner.vue`
  - 基础信息配置表单
  - JSON Schema 配置编辑器（使用 `vue-json-schema-form` 或类似库）
  - 代码编辑器（使用 `monaco-editor` 或 `@guolao/vue-monaco-editor`）
  - 钩子函数模板生成
- [ ] 创建在线调试界面
  - 测试数据输入
  - 执行结果展示
  - 错误信息高亮

**辅助功能 (2h)**
- [ ] 代码片段库管理
- [ ] 插件模板市场（预置常用插件模板）
- [ ] 插件导出/导入功能（.tar.gz 包）

---

### 2.4 Phase 5: 插件市场（预计 4-6 小时）

#### 目标
建立统一的插件市场，支持插件的浏览、搜索、安装、更新和评分。

#### 任务清单

**后端任务 (2h)**
- [ ] 创建 `app/services/market_service.py` 市场服务
  - 插件列表（分类、搜索、分页）
  - 插件详情和评分
  - 安装/更新逻辑
- [ ] 创建本地插件市场数据
  - 官方插件列表
  - 社区插件列表
  - 插件分类和标签
- [ ] 支持 NPM 包安装（可选，作为进阶功能）

**前端任务 (2h)**
- [ ] 创建插件市场页面 `src/pc/views/PluginMarket.vue`
  - 分类侧边栏
  - 插件卡片网格
  - 搜索和筛选
  - 插件详情弹窗
- [ ] 创建插件安装向导
  - 选择安装源（本地/NPM/URL）
  - 安装进度显示
  - 安装后配置

---

## 三、技术架构（当前 vs 目标）

### 3.1 当前架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        当前架构                                      │
├─────────────────────────────────────────────────────────────────────┤
│  前端层                                                             │
│  └── PluginManager.vue (独立的插件管理页面)                         │
│                                                                      │
│  API 层                                                             │
│  └── /api/v1/plugins/* (插件CRUD + 测试)                           │
│                                                                      │
│  服务层                                                             │
│  └── PluginManager (生命周期管理)                                  │
│  └── PluginSandbox (代码执行)                                       │
│                                                                      │
│  数据层                                                             │
│  └── Plugin, PluginHook, TemplatePlugin, AppPlugin                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 目标架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        目标架构                                      │
├─────────────────────────────────────────────────────────────────────┤
│  前端层                                                             │
│  ├── PluginManager.vue (独立插件管理)                               │
│  ├── TemplatePluginManager.vue (模板级插件管理)                     │
│  ├── AppPluginManager.vue (应用级插件管理)                          │
│  ├── PluginDesigner.vue (可视化插件开发)                            │
│  └── PluginMarket.vue (插件市场)                                   │
│                                                                      │
│  API 层                                                             │
│  ├── /api/v1/plugins/* (插件CRUD + 测试)                           │
│  ├── /api/v1/template/{id}/plugins/* (模板插件绑定)                │
│  ├── /api/v1/app/{id}/plugins/* (应用插件绑定)                     │
│  └── /api/v1/market/* (插件市场)                                   │
│                                                                      │
│  服务层                                                             │
│  ├── PluginManager (生命周期管理)                                  │
│  ├── PluginSandbox (代码执行)                                       │
│  ├── TemplatePluginService (模板插件服务)                          │
│  ├── AppPluginService (应用插件服务)                               │
│  └── MarketService (市场服务)                                      │
│                                                                      │
│  数据层                                                             │
│  ├── Plugin, PluginHook, PluginVersion                            │
│  ├── TemplatePlugin (模板-插件绑定)                                │
│  ├── AppPlugin (应用-插件绑定)                                     │
│  └── PluginRating (插件评分) - 新增                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、优先级与里程碑

### 4.1 第一优先级（当前阶段）- 模板级插件嵌入

**目标**：让插件能够在模板层面生效，实现表单/列表的扩展功能

**里程碑**：
- [ ] M1.1: 模板设计器中添加插件管理Tab（1h）
- [ ] M1.2: 实现插件与模板的绑定API（1h）
- [ ] M1.3: 完成插件在表单提交时的触发测试（1h）
- [ ] M1.4: 通知插件的实际效果验证（1h）

### 4.2 第二优先级 - 我的应用集成

**目标**：支持将插件打包进应用，实现应用级别的功能复用

**里程碑**：
- [ ] M2.1: 应用详情页面添加插件区域（0.5h）
- [ ] M2.2: 应用发布时自动打包插件（1h）
- [ ] M2.3: 数据迁移脚本（0.5h）

### 4.3 第三优先级 - 可视化插件开发

**目标**：降低插件开发门槛，提供在线开发和调试工具

**里程碑**：
- [ ] M3.1: 插件代码编辑器集成（2h）
- [ ] M3.2: 在线调试功能（2h）
- [ ] M3.3: 代码片段库（2h）

### 4.4 第四优先级 - 插件市场

**目标**：建立统一的插件分发平台

**里程碑**：
- [ ] M4.1: 本地插件市场数据（1h）
- [ ] M4.2: 插件市场页面（2h）
- [ ] M4.3: 插件安装向导（2h）

---

## 五、风险评估与应对

### 5.1 安全风险

| 风险 | 等级 | 应对措施 |
|------|------|---------|
| 用户代码执行破坏系统 | 高 | RestrictedPython隔离 + 5秒超时 + 内存限制 |
| SQL注入攻击 | 中 | 使用SQLAlchemy ORM，参数化查询 |
| XSS攻击 | 中 | 前端输出转义，Content-Security-Policy |
| 插件权限滥用 | 中 | 插件权限分级，应用级别隔离 |

### 5.2 兼容性风险

| 风险 | 等级 | 应对措施 |
|------|------|---------|
| 插件升级破坏现有功能 | 中 | 版本号管理，升级前备份配置 |
| 模板迁移丢失插件绑定 | 中 | 导出时包含插件配置，导入时提示 |
| 不同版本插件不兼容 | 低 | 插件市场标注兼容性要求 |

### 5.3 性能风险

| 风险 | 等级 | 应对措施 |
|------|------|---------|
| 插件加载拖慢启动 | 低 | 延迟加载，仅加载已启用插件 |
| 钩子执行超时 | 中 | 5秒超时，熔断机制 |
| 大量插件并发执行 | 低 | 钩子执行队列，限流控制 |

---

## 六、文件清单与工作量

### 6.1 新增后端文件

| 文件路径 | 说明 | 阶段 |
|---------|------|------|
| `app/services/template_plugin_service.py` | 模板插件服务 | Phase 2 |
| `app/services/app_plugin_service.py` | 应用插件服务 | Phase 3 |
| `app/services/market_service.py` | 市场服务 | Phase 5 |
| `app/api/v1/plugin_developer.py` | 插件开发API | Phase 4 |
| `app/api/v1/market.py` | 市场API | Phase 5 |

### 6.2 新增前端文件

| 文件路径 | 说明 | 阶段 |
|---------|------|------|
| `src/pc/views/TemplatePluginManager.vue` | 模板插件管理 | Phase 2 |
| `src/pc/views/AppPluginManager.vue` | 应用插件管理 | Phase 3 |
| `src/pc/views/PluginDesigner.vue` | 插件可视化编辑器 | Phase 4 |
| `src/pc/views/PluginMarket.vue` | 插件市场 | Phase 5 |
| `src/pc/components/PluginBindDialog.vue` | 插件绑定对话框 | Phase 2 |
| `src/pc/components/PluginConfigForm.vue` | 插件配置表单 | Phase 4 |

### 6.3 修改文件

| 文件路径 | 修改内容 | 阶段 |
|---------|---------|------|
| `app/api/v1/endpoints/templates.py` | 添加插件绑定API | Phase 2 |
| `app/api/v1/endpoints/apps.py` | 添加应用插件API | Phase 3 |
| `src/common/router/index.ts` | 添加新页面路由 | Phase 2-5 |
| `src/common/api/index.ts` | 添加新API | Phase 2-5 |
| `src/pc/views/TemplateEditPage.vue` | 集成插件管理Tab | Phase 2 |
| `src/pc/views/AppDetail.vue` | 集成插件管理区域 | Phase 3 |

---

## 七、总工期估算

| 阶段 | 后端 | 前端 | 测试 | 总计 |
|------|------|------|------|------|
| Phase 1 | ✅ 已完成 | ✅ 已完成 | ✅ 已完成 | 4-6h |
| Phase 2 | 1.5h | 1.5h | 1h | **3-4h** |
| Phase 3 | 1h | 1h | 0.5h | **2-3h** |
| Phase 4 | 2h | 4h | 2h | **6-8h** |
| Phase 5 | 2h | 2h | 1h | **4-6h** |
| **总计** | **6.5h** | **8.5h** | **4.5h** | **19-27h** |

---

## 八、下一步行动计划

### 立即执行（本周）

1. **Phase 2.1**: 在模板设计器中添加插件管理Tab
   - 创建 `TemplatePluginManager.vue` 组件
   - 修改模板编辑页面，添加Tab
   - 实现插件绑定/解绑API

2. **Phase 2.2**: 完成插件在表单提交时的触发测试
   - 扩展表单提交逻辑，调用 `plugin_manager.trigger_hook`
   - 测试通知插件的实际效果
   - 验证钩子执行结果展示

### 后续计划（两周内）

3. **Phase 3**: 我的应用集成
4. **Phase 4**: 可视化插件开发（可并行进行）
5. **Phase 5**: 插件市场（可并行进行）

---

*文档版本: v2.0*
*更新时间: 2026-04-29*
*基于迁移计划: KFlower-NocoBase插件迁移计划.md*
