# Kflower 全模块整合优化方案

> 版本：v1.0 | 日期：2026-05-01 | 状态：待实施

---

## 一、现状全面诊断

### 1.1 系统模块清单（已存在）

| 模块 | 后端文件 | 前端页面 | 状态 |
|------|---------|---------|------|
| 模板设计 | `app/models/workflow.py::Template` | `Templates.vue` | 功能完整 |
| 流程审批 | `app/models/workflow.py::Workflow` | `WorkflowDesigner.vue` | 设计器完整，绑定不完整 |
| 我的应用 | `app/modules/my_apps/` | `MyApps.vue / AppDesigner.vue` | 基础功能，协同缺失 |
| 智能体 | `app/models/ai.py::Agent` | `AgentOrchestrator.vue` | 数据库CRUD有，协同无 |
| 知识库 | `app/models/ai.py::KnowledgeBase` | `Knowledge.vue` | 独立运行，未接入协同 |
| 插件系统 | `app/models/plugin.py::Plugin` | `AppPluginManager.vue` | 已修复绑定Bug |
| 工具集 | `app/core/agent_engine/tools/` | `AITools.vue` | 注册完成，执行断层 |
| AI 网关 | `app/core/ai_digital_base/gateway.py` | `AIGateway.vue` | 运行正常 |

### 1.2 核心问题清单（7 个）

#### 问题 P1【最高优先】：流程审批无法绑定到应用菜单
- **位置**：`AppMenu` 模型有 `workflow_id` 字段，`AppDesigner.vue` 菜单配置面板**没有**流程选择 UI
- **表现**：在"我的应用 → 设计 → 菜单配置"中无法选择/关联流程
- **影响**：表单提交后无法自动触发审批流程，整个流程审批功能对"我的应用"完全不可用

#### 问题 P2【最高优先】：智能体无法与模块绑定
- **位置**：`Agent` 模型（`app/models/ai.py`）无 `template_ids`、`workflow_ids`、`knowledge_base_ids` 字段
- **表现**：无法为智能体指定"它负责哪个模板/哪个流程/用哪个知识库"
- **影响**：智能体是孤立的通用对话，不能成为具体业务的专属助手

#### 问题 P3【高优先】：工具集与智能体执行断层
- **位置**：`ToolExecutor.execute()` 方法（`tools/executor.py`）逻辑需核查
- **表现**：工具已注册（`tool_registry`），但 `agent_service._chat_with_tools()` 中工具执行结果不上抛错误，部分工具 handler 为 None
- **影响**：AI 调用工具后结果无效，`create_template`、`execute_workflow` 等工具调用不生效

#### 问题 P4【高优先】：流程审批与表单数据无运行时关联
- **位置**：`WorkflowInstance` 有 `form_data_id` 字段，但 `workflows.py` 的 `/execute` 端点不传入表单数据
- **表现**：发起审批时不携带表单填写数据，审批人看不到被审批的表单内容
- **影响**：审批流程无实际意义

#### 问题 P5【中优先】：知识库只被 RAG 通用检索，无应用级隔离
- **位置**：`agent_service.py` 中 `rag_retriever.search(collection_name="knowledge", ...)` 硬编码
- **表现**：所有智能体对话都搜全量知识库，无法按应用/业务域隔离
- **影响**：不同应用的智能体会互相"污染"知识，无法构建专属知识空间

#### 问题 P6【中优先】：插件钩子无统一执行调度
- **位置**：`app_plugin_service.py` 中 `bind_plugin` 已实现，但无统一的"在表单提交时触发应用插件"调度器
- **表现**：插件绑定到应用后，插件的 `after_form_submit`/`before_form_submit` 钩子从未被触发
- **影响**：所有插件绑定配置形同虚设

#### 问题 P7【中优先】：前端模块间跳转链路断裂
- **位置**：各页面间无统一的跳转参数传递机制
- **表现**：从"流程列表"无法跳转到"关联的应用"，从"智能体"无法跳转到"相关模板"
- **影响**：用户在使用时必须手动记忆关联关系，体验割裂

---

## 二、整合优化方案（分优先级）

### 阶段一：核心协同修复（P1-P4，约 2-3 天工作量）

---

#### 任务 1.1：流程审批绑定到应用菜单 UI

**目标**：让用户在"我的应用 → 设计 → 菜单配置"中选择流程，提交时自动发起审批。

**后端改动**（`app/modules/my_apps/endpoints.py`）：

1. 新增 API：`GET /apps/{app_id}/workflows/available` — 返回可绑定的工作流列表（用于菜单配置下拉）

```python
@router.get("/{app_id}/workflows/available")
async def get_available_workflows(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取应用可绑定的工作流列表"""
    result = await db.execute(select(Workflow).where(Workflow.is_active == True))
    workflows = result.scalars().all()
    return [{"id": w.id, "name": w.name, "code": w.code, "description": w.description} for w in workflows]
```

2. 新增 API：`POST /apps/{app_id}/menus/{menu_id}/bind-workflow` — 将菜单与流程绑定

```python
@router.post("/{app_id}/menus/{menu_id}/bind-workflow")
async def bind_menu_workflow(
    app_id: int,
    menu_id: int,
    data: Dict[str, Any],  # {workflow_id, trigger, auto_approve}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """绑定菜单与工作流"""
    result = await db.execute(select(AppMenu).where(AppMenu.id == menu_id, AppMenu.app_id == app_id))
    menu = result.scalar_one_or_none()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    menu.workflow_id = data.get("workflow_id")
    menu.workflow_trigger = data.get("trigger", "submit")
    menu.workflow_auto_approve = data.get("auto_approve", False)
    flag_modified(menu, "workflow_field_permissions")
    await db.commit()
    return {"success": True, "message": "流程绑定成功"}
```

**前端改动**（`kflower-frontend/src/pc/views/AppDesigner.vue`）：

在"菜单属性"面板中，新增"流程配置"折叠卡片：

```vue
<!-- 在菜单属性面板 el-card 中添加 -->
<el-collapse-item title="流程审批配置" name="workflow">
  <el-form-item label="关联流程">
    <el-select v-model="selectedMenu.workflow_id" placeholder="选择流程（可选）" clearable
               @change="onWorkflowChange" style="width: 100%">
      <el-option v-for="wf in availableWorkflows" :key="wf.id"
                 :label="wf.name" :value="wf.id">
        <span>{{ wf.name }}</span>
        <span style="color: #999; font-size: 12px; margin-left: 8px">{{ wf.code }}</span>
      </el-option>
    </el-select>
  </el-form-item>
  <el-form-item label="触发时机" v-if="selectedMenu.workflow_id">
    <el-radio-group v-model="selectedMenu.workflow_trigger">
      <el-radio value="submit">表单提交时</el-radio>
      <el-radio value="update">数据更新时</el-radio>
      <el-radio value="manual">手动触发</el-radio>
    </el-radio-group>
  </el-form-item>
  <el-form-item label="自动发起" v-if="selectedMenu.workflow_id">
    <el-switch v-model="selectedMenu.workflow_auto_approve" />
    <span class="hint-text">开启后，提交即自动发起审批流程</span>
  </el-form-item>
</el-collapse-item>
```

**前端 API 新增**（`src/pc/common/api/index.ts`）：

```typescript
// 在 myAppsAPI 中添加
getAvailableWorkflows: (appId: number) =>
  request.get(`/apps/${appId}/workflows/available`),

bindMenuWorkflow: (appId: number, menuId: number, data: object) =>
  request.post(`/apps/${appId}/menus/${menuId}/bind-workflow`, data),
```

---

#### 任务 1.2：智能体与各模块绑定（数据库 + API + UI）

**目标**：Agent 可以绑定到特定模板、流程、知识库，成为专属业务助手。

**后端数据库迁移**（`migrations/add_agent_bindings.py`）：

```python
"""新增 Agent 模块绑定字段"""
import sqlite3

DB_PATH = "kflower-backend/kflower.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查并添加字段
    cursor.execute("PRAGMA table_info(agents)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "template_ids" not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN template_ids TEXT DEFAULT '[]'")
    if "workflow_ids" not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN workflow_ids TEXT DEFAULT '[]'")
    if "knowledge_base_ids" not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN knowledge_base_ids TEXT DEFAULT '[]'")
    if "plugin_ids" not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN plugin_ids TEXT DEFAULT '[]'")
    if "system_prompt" not in columns:
        cursor.execute("ALTER TABLE agents ADD COLUMN system_prompt TEXT DEFAULT ''")
    if "scope" not in columns:
        cursor.execute(
            "ALTER TABLE agents ADD COLUMN scope TEXT DEFAULT 'global' "
            "-- global/app/template/workflow"
        )
    
    conn.commit()
    conn.close()
    print("Agent 绑定字段迁移完成")

if __name__ == "__main__":
    migrate()
```

**后端模型更新**（`app/models/ai.py` Agent 类追加字段）：

```python
# 在 Agent 类中追加
template_ids = Column(JSON, default=list, comment="绑定的模板ID列表")
workflow_ids = Column(JSON, default=list, comment="绑定的工作流ID列表")
knowledge_base_ids = Column(JSON, default=list, comment="绑定的知识库ID列表")
plugin_ids = Column(JSON, default=list, comment="使用的插件列表")
system_prompt = Column(Text, nullable=True, comment="专属系统提示词，覆盖默认提示词")
scope = Column(String(20), default="global", comment="作用域: global/app/template/workflow")
```

**后端 API 更新**（`app/api/v1/endpoints/ai_agent_engine.py` 的 create/update agent）：

在 create_agent 和 update_agent 的请求体 Schema 中增加上述字段，并在保存时序列化。

**前端 UI 更新**（`AgentOrchestrator.vue`）：

在智能体创建/编辑对话框中，新增"模块绑定"标签页：

```vue
<el-tabs v-model="activeTab" class="agent-tabs">
  <el-tab-pane label="基本信息" name="basic">
    <!-- 原有字段：名称、类型、描述 -->
  </el-tab-pane>
  
  <el-tab-pane label="模块绑定" name="bindings">
    <el-form-item label="绑定模板">
      <el-select v-model="agentForm.template_ids" multiple placeholder="选择模板"
                 filterable style="width: 100%">
        <el-option v-for="t in templates" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="绑定流程">
      <el-select v-model="agentForm.workflow_ids" multiple placeholder="选择流程"
                 filterable style="width: 100%">
        <el-option v-for="w in workflows" :key="w.id" :label="w.name" :value="w.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="知识库">
      <el-select v-model="agentForm.knowledge_base_ids" multiple placeholder="选择知识库"
                 filterable style="width: 100%">
        <el-option v-for="kb in knowledgeBases" :key="kb.id" :label="kb.name" :value="kb.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="作用域">
      <el-radio-group v-model="agentForm.scope">
        <el-radio value="global">全局</el-radio>
        <el-radio value="app">应用级</el-radio>
        <el-radio value="template">模板级</el-radio>
      </el-radio-group>
    </el-form-item>
  </el-tab-pane>
  
  <el-tab-pane label="提示词配置" name="prompt">
    <el-form-item label="专属提示词">
      <el-input v-model="agentForm.system_prompt" type="textarea" :rows="8"
                placeholder="留空则使用系统默认提示词" />
    </el-form-item>
  </el-tab-pane>
</el-tabs>
```

---

#### 任务 1.3：工具集执行链路修复

**目标**：修复工具 handler 为 None 时的静默失败，补全 `create_template`/`execute_workflow` 等核心工具的实际实现。

**后端改动**（`app/core/agent_engine/tools/executor.py`）：

```python
class ToolExecutor:
    async def execute(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return {"error": f"工具 '{tool_name}' 不存在", "success": False}
        if not tool.is_enabled:
            return {"error": f"工具 '{tool_name}' 已被禁用", "success": False}
        if tool.handler is None:
            # 尝试内置实现
            result = await self._execute_builtin(tool_name, arguments, context)
            if result is not None:
                return result
            return {"error": f"工具 '{tool_name}' 没有可用的执行器", "success": False}
        try:
            return await tool.handler(arguments, context)
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution error: {e}", exc_info=True)
            return {"error": str(e), "success": False}  # 必须上抛错误

    async def _execute_builtin(self, tool_name: str, arguments: Dict, context: Dict) -> Optional[Dict]:
        """内置工具实现映射"""
        handlers = {
            "create_template": self._handle_create_template,
            "list_templates": self._handle_list_templates,
            "execute_workflow": self._handle_execute_workflow,
            "query_data": self._handle_query_data,
            "send_notification": self._handle_send_notification,
        }
        handler = handlers.get(tool_name)
        if handler:
            return await handler(arguments, context)
        return None
    
    async def _handle_create_template(self, arguments: Dict, context: Dict) -> Dict:
        """实际调用模板服务创建模板"""
        from app.core.database import _get_sync_session
        from app.services.template_service import TemplateService
        db = _get_sync_session()
        try:
            # 调用真实的模板创建服务
            service = TemplateService()
            result = service.create_from_agent(db, arguments, context)
            return {"success": True, "template_id": result.id, "name": result.name}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()
```

---

#### 任务 1.4：流程审批携带表单数据

**目标**：发起审批时传入表单数据，审批节点可显示、校验表单内容。

**后端改动**（`app/api/v1/endpoints/workflows.py` 的 `/execute` 端点）：

```python
class WorkflowExecuteRequest(BaseModel):
    title: str
    data: Dict[str, Any] = {}
    form_template_id: Optional[int] = None   # 关联的表单模板
    form_data_id: Optional[int] = None        # 关联的表单数据行 ID
    initiator_note: Optional[str] = None      # 发起人备注

@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: int, request: WorkflowExecuteRequest, ...):
    instance = WorkflowInstance(
        workflow_id=workflow_id,
        title=request.title,
        data=request.data,
        form_template_id=request.form_template_id,  # 新增传入
        form_data_id=request.form_data_id,           # 新增传入
        status="running",
        created_by=current_user.id,
    )
    ...
```

---

### 阶段二：协同层建设（约 2-3 天工作量）

---

#### 任务 2.1：应用上下文注入机制

**核心思想**：在用户进入某个"我的应用"时，系统自动加载该应用绑定的工作流、知识库、智能体、插件，
形成一个**应用上下文对象（AppContext）**，后续所有功能调用都携带此上下文。

**后端改动**（新建 `app/core/app_context.py`）：

```python
"""
应用上下文 - 统一协同层
每个应用在运行时的完整上下文快照
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class AppContext:
    app_id: int
    app_code: str
    app_name: str
    # 关联配置
    workflow_ids: List[int] = field(default_factory=list)
    knowledge_base_ids: List[int] = field(default_factory=list)
    bound_agents: List[Dict] = field(default_factory=list)  # [{agent_id, trigger, context}]
    plugin_ids: List[int] = field(default_factory=list)
    # 运行时用户
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    # 扩展元数据
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_agent_context(self) -> Dict[str, Any]:
        """转为智能体上下文格式"""
        return {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "workflow_ids": self.workflow_ids,
            "knowledge_base_ids": self.knowledge_base_ids,
            "user_id": self.user_id,
            "user_name": self.user_name,
        }

async def build_app_context(app_id: int, user_id: int, db) -> AppContext:
    """从数据库构建完整的应用上下文"""
    from app.modules.my_apps.models import Application
    from sqlalchemy import select
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise ValueError(f"Application {app_id} not found")
    return AppContext(
        app_id=app.id,
        app_code=app.code,
        app_name=app.name,
        workflow_ids=[w.get("workflow_id") for w in (app.workflow_ids or []) if w.get("workflow_id")],
        knowledge_base_ids=app.knowledge_base_ids or [],
        bound_agents=app.bound_agents or [],
        plugin_ids=[],
        user_id=user_id,
    )
```

**后端：智能体服务使用应用上下文**（`agent_service.py` 中更新 chat 方法）：

```python
async def chat(self, message: str, ..., app_context: Optional[AppContext] = None):
    # 如果有应用上下文，使用应用绑定的知识库而不是全量
    rag_collections = ["knowledge"]  # 默认
    if app_context and app_context.knowledge_base_ids:
        rag_collections = [f"kb_{kb_id}" for kb_id in app_context.knowledge_base_ids]
    
    for collection in rag_collections:
        docs = await rag_retriever.search(collection_name=collection, query=message, top_k=3)
        # ... 合并结果
```

---

#### 任务 2.2：插件钩子统一调度器

**目标**：表单提交/删除/列表加载时，自动触发绑定到该应用的插件对应钩子。

**后端新建**（`app/core/plugin_dispatcher.py`）：

```python
"""
插件钩子调度器
在业务事件触发时，查找并执行绑定的插件钩子
"""
import logging
from typing import Optional, Dict, Any
logger = logging.getLogger(__name__)

class PluginDispatcher:
    """插件事件调度器"""
    
    async def dispatch(
        self,
        event: str,            # 事件名，如 "form.submit"
        app_id: int,
        template_id: Optional[int],
        payload: Dict[str, Any],
        db
    ) -> Dict[str, Any]:
        """
        触发指定事件，执行所有匹配的插件钩子
        返回经过插件处理后的 payload（插件可修改数据）
        """
        from app.services.app_plugin_service import AppPluginService
        
        # 获取该应用绑定的插件及其钩子
        bindings = AppPluginService.get_bindings_for_event(app_id, event, db)
        
        result = payload.copy()
        for binding in bindings:
            try:
                modified = await self._execute_hook(binding, result)
                if modified is not None:
                    result = modified
            except Exception as e:
                logger.error(f"Plugin hook error [{binding.plugin_id} / {event}]: {e}")
        
        return result
    
    async def _execute_hook(self, binding, payload: Dict) -> Optional[Dict]:
        """执行单个插件钩子（沙箱执行）"""
        from app.core.plugin_sandbox import PluginSandbox
        hook_code = binding.plugin.hook_code or {}
        # 找到匹配事件的钩子代码
        event = binding.trigger_event
        code = hook_code.get(event, "")
        if not code:
            return None
        sandbox = PluginSandbox()
        return await sandbox.execute(code, {"payload": payload, "config": binding.config or {}})

plugin_dispatcher = PluginDispatcher()
```

**后端：在模板数据提交端点中触发**（`app/api/v1/endpoints/templates.py`，数据提交处添加）：

```python
# 在数据保存成功后
from app.core.plugin_dispatcher import plugin_dispatcher
# 触发 after_form_submit 钩子
await plugin_dispatcher.dispatch(
    event="form.submit",
    app_id=app_id,           # 从 request header 或 session 获取
    template_id=template_id,
    payload={"data": form_data, "user_id": current_user.id},
    db=db
)
```

---

#### 任务 2.3：知识库应用级隔离

**目标**：不同应用的智能体只检索自己绑定的知识库，不互相干扰。

**后端改动**：

1. 知识库向量集合命名改为 `kb_{knowledge_base_id}` 而非统一的 `knowledge`
2. 应用绑定知识库时，在 RAG 中建立对应集合
3. 智能体对话时，根据 `app_context.knowledge_base_ids` 指定检索集合

**知识库端点增加**（`endpoints/knowledge.py`）：

```python
@router.post("/{kb_id}/activate-for-app/{app_id}")
async def activate_knowledge_for_app(kb_id: int, app_id: int, ...):
    """激活知识库在应用中的使用（建立专属向量集合）"""
    # 为该应用创建专属检索集合
    collection_name = f"kb_{kb_id}_app_{app_id}"
    await rag_retriever.create_collection(collection_name)
    # 将现有知识库文档的向量同步到新集合
    await rag_retriever.sync_collection(source=f"kb_{kb_id}", target=collection_name)
    return {"success": True, "collection": collection_name}
```

---

### 阶段三：前端协同体验优化（约 1-2 天工作量）

---

#### 任务 3.1：应用设计器整合面板

在 `AppDesigner.vue` 中，新增"协同配置"选项卡，集中管理应用与各模块的绑定关系：

```
应用设计器
├── 基本信息
├── 菜单设计      ← 每个菜单可绑定流程（任务 1.1 UI）
├── 协同配置  ← 新增
│   ├── 关联流程    → 从 Workflow 列表选择，设置全局流程策略
│   ├── 知识库      → 从 KnowledgeBase 列表选择，配置检索参数
│   ├── 智能体      → 从 Agent 列表选择，设置触发场景
│   └── 插件        → AppPluginManager 组件（已存在）
├── 表单关系
└── 版本管理
```

#### 任务 3.2：跨模块跳转链路

在各列表页面添加"打开相关"快捷操作：

- 流程列表 → 点击"查看关联应用"，跳转到使用该流程的应用
- 模板列表 → 点击"AI 助手"，跳转到绑定了该模板的智能体对话页
- 智能体详情 → 显示"关联模板 N 个，关联流程 M 个，知识库 K 个"，可点击跳转

#### 任务 3.3：我的应用运行时页面集成智能体助手

在 `AppLayout.vue` 中，右下角添加浮动 AI 助手按钮：

```vue
<!-- AppLayout.vue 中添加 -->
<div class="app-ai-assistant" v-if="appContext.bound_agents.length > 0">
  <el-button circle type="primary" @click="openAssistant">
    <el-icon><ChatDotRound /></el-icon>
  </el-button>
  <!-- 智能体对话抽屉 -->
  <el-drawer v-model="assistantVisible" title="AI 助手" size="380px" direction="rtl">
    <AgentChat :agent-id="appContext.bound_agents[0].agent_id"
               :app-context="appContext" />
  </el-drawer>
</div>
```

---

## 三、实施路线图

```
阶段一（P1-P4 核心修复）：约 2-3 天
├── Day 1：流程审批绑定 UI（任务 1.1）+ 数据库迁移（任务 1.2 DB 部分）
├── Day 2：智能体模块绑定 API + 前端 UI（任务 1.2）
└── Day 3：工具集执行修复（任务 1.3）+ 流程携带表单数据（任务 1.4）

阶段二（协同层建设）：约 2-3 天
├── Day 4：AppContext 核心类 + agent_service 接入上下文
├── Day 5：插件钩子调度器（任务 2.2）
└── Day 6：知识库应用级隔离（任务 2.3）

阶段三（前端体验）：约 1-2 天
├── Day 7：应用设计器整合面板（任务 3.1）+ 跨模块跳转
└── Day 8：运行时 AI 助手浮窗（任务 3.3）
```

---

## 四、关键数据库迁移汇总

需新建或执行以下迁移脚本：

| 脚本文件 | 操作 | 影响表 |
|---------|------|-------|
| `migrations/add_agent_bindings.py` | 新增 Agent 绑定字段 | `agents` |
| `migrations/add_workflow_form_data.py` | WorkflowInstance 确保有 form_data_id 字段 | `workflow_instances` |
| `migrations/add_app_menu_workflow.py` | 确认 AppMenu 有 workflow_id 等字段（已有，仅验证） | `app_menus` |

---

## 五、优先执行顺序建议

1. **立刻执行**：运行数据库迁移 `add_agent_bindings.py`
2. **第一步**：完成任务 1.1（流程审批绑定到应用菜单 UI），这是最核心的用户痛点
3. **第二步**：完成任务 1.2（智能体模块绑定），解除智能体的功能孤岛状态
4. **第三步**：完成任务 1.3（工具集执行修复），让 AI 真正能调用系统功能
5. **后续**：按阶段二、三顺序推进

---

## 六、附：各模块现有 API 资产（复用清单）

| 接口 | 现状 | 可复用用途 |
|------|------|----------|
| `GET /workflows/` | 已有 | 流程选择下拉数据源 |
| `GET /knowledge/bases` | 已有 | 知识库绑定选择 |
| `GET /agent/agents` | 已有 | 智能体绑定选择 |
| `GET /apps/{id}/plugins/available` | 已修复 | 插件选择（已可用） |
| `POST /workflows/{id}/execute` | 已有 | 从菜单触发审批 |
| `POST /agent/chat` | 已有 | AI 助手对话（接入 AppContext 后增强） |

---

*本方案已完整覆盖 P1-P7 所有问题，可按阶段逐步实施，每个任务相互独立，不存在强依赖的阻塞关系。*
