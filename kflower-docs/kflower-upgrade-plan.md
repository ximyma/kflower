# Kflower 企业智能管理平台 — 升级优化方案

> 版本：v2.0 规划  
> 日期：2026-04-22  
> 目标：通过组合 AI 能力、智能表单、流程审批、知识库、智能体等核心模块，创建复杂功能的 AI 应用

---

## 目录

1. [现状分析与差距评估](#1-现状分析与差距评估)
2. [升级愿景与架构蓝图](#2-升级愿景与架构蓝图)
3. [模块一：智能表单系统升级](#3-模块一智能表单系统升级)
4. [模块二：流程审批引擎升级](#4-模块二流程审批引擎升级)
5. [模块三：应用设计器升级](#5-模块三应用设计器升级)
6. [模块四：AI 能力深度融合](#6-模块四ai-能力深度融合)
7. [模块五：知识库与 RAG 升级](#7-模块五知识库与-rag-升级)
8. [模块六：智能体引擎升级](#8-模块六智能体引擎升级)
9. [AI 复合应用构建方案](#9-ai-复合应用构建方案)
10. [实施路线图](#10-实施路线图)

---

## 1. 现状分析与差距评估

### 1.1 当前已实现的能力

| 模块 | 已实现 | 完成度 |
|------|--------|--------|
| **智能表单** | 模板 CRUD、动态建表、数据提交/查询/导出/导入、AI 生成模板、字段推荐 | 70% |
| **流程审批** | 流程设计器(12种节点)、审批/条件/并行/子流程、条件表达式求值、审批人解析 | 60% |
| **我的应用** | 应用 CRUD、菜单树管理、表单关系(belongs_to/has_many/many_to_many)、插件系统、AI 设计助手 | 40% |
| **AI 能力** | 能力注册中心(20种能力)、AI 网关(多模型切换)、RAG 检索、智能体编排器 | 50% |
| **知识库** | CRUD、文档上传/解析/向量化、检索/重排、标签、笔记、知识图谱 | 65% |
| **智能体** | 智能体 CRUD、工具注册、任务编排(顺序/并行/分层) | 35% |

### 1.2 核心差距清单

#### 智能表单
- ❌ **缺少公式/函数系统**：字段无法进行计算联动（如：`单价 × 数量 = 总价`）
- ❌ **缺少字段关联**：无法实现跨模块/跨模板的自动填充和联动
- ❌ **缺少多表关联查询**：子表/明细表未实现（如订单-订单明细）
- ❌ **字段属性简单**：缺少校验规则组、条件显示/隐藏、级联选项、字段权限
- ❌ **缺少数据聚合**：无法在列表页显示汇总统计

#### 流程审批
- ❌ **与应用未集成**：应用内表单无法直接发起审批流程
- ❌ **缺少智能审批**：AI 自动审批、审批建议、风险识别
- ❌ **并行节点不完善**：仅实现了简化版并行分支
- ❌ **缺少表单权限控制**：审批时无法根据节点配置字段可编辑/只读
- ❌ **缺少催办/超时/自动流转**：无定时器和 SLA 管理

#### 我的应用
- ❌ **未接入流程审批**：应用中的表单无法关联和触发工作流
- ❌ **未接入智能体**：应用无法绑定智能体提供 AI 辅助
- ❌ **未接入知识库**：应用无上下文知识支撑
- ❌ **仪表盘未实现**：仅有 UI 骨架，无真实图表渲染
- ❌ **应用间隔离弱**：缺少独立数据空间和版本管理

---

## 2. 升级愿景与架构蓝图

### 2.1 核心理念

将 Kflower 从「低代码表单平台」升级为 **「AI 驱动的复合应用构建平台」**。

关键转变：

```
旧模式：用户手动设计表单 → 手动配置流程 → 手动关联
新模式：AI 理解需求 → 自动生成复合应用（表单 + 流程 + 智能体 + 知识库）
```

### 2.2 架构蓝图

```
┌──────────────────────────────────────────────────────────────┐
│                      AI 应用构建引擎                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐   │
│  │ 需求理解 │→│ 方案设计  │→│ 自动生成  │→│ 测试与发布  │   │
│  └─────────┘  └──────────┘  └──────────┘  └─────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                       复合应用运行时                          │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  智能表单引擎                                          │     │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │     │
│  │  │公式系统│ │字段关联│ │多表关联│ │子表支持│ │数据聚合│      │     │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │     │
│  └─────────────────────────────────────────────────────┘     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐     │
│  │ 流程审批引擎  │  │  智能体引擎   │  │   知识库/RAG  │     │
│  │ (表单集成)    │  │  (上下文感知)  │  │  (语义检索)   │     │
│  └──────────────┘  └───────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 模块一：智能表单系统升级

### 3.1 公式/函数引擎

**目标**：字段值可通过公式自动计算，类似 Excel 的 `=A1*B1`。

#### 3.1.1 数据模型扩展

在 `ModuleField` 中新增属性：

```python
class ModuleField(BaseModel):
    # ... 原有属性 ...
    
    # 新增：公式计算
    formula: Optional[str] = None       # 公式表达式，如 "price * quantity"
    formula_type: Optional[str] = None  # "calculated" | "aggregate"
    
    # 新增：字段联动
    depends_on: Optional[List[str]] = None  # 依赖的字段列表
    cascade_update: bool = False            # 依赖字段变化时自动重算
    
    # 新增：聚合计算
    aggregate: Optional[Dict] = None  # {"type": "sum|avg|count|max|min", "target_field": "amount", "filter": "..."}
    
    # 新增：校验规则
    validation_rules: Optional[List[Dict]] = None  # [{"rule": "regex", "pattern": "^\\d+$", "message": "..."}]
    
    # 新增：条件显示
    visible_when: Optional[Dict] = None  # {"field": "type", "op": "eq", "value": "VIP"}
    
    # 新增：条件必填
    required_when: Optional[Dict] = None
    
    # 新增：默认值公式
    default_formula: Optional[str] = None  # "NOW()" | "{{current_user.name}}"
    
    # 新增：子表/明细表
    is_subtable: bool = False
    subtable_fields: Optional[List["ModuleField"]] = None
    subtable_of: Optional[str] = None  # 所属主表字段名
    
    # 新增：关联字段
    relation: Optional[Dict] = None  # {"target_template": "customers", "display_field": "name", "link_field": "customer_id"}
```

#### 3.1.2 公式求值器（后端）

```python
# app/core/formula_engine/evaluator.py

class FormulaEngine:
    """
    安全的公式求值引擎
    支持：算术运算、字符串拼接、日期计算、聚合函数、条件表达式
    """
    
    # 内置函数
    FUNCTIONS = {
        "SUM": lambda *args: sum(args),
        "AVG": lambda *args: sum(args) / len(args) if args else 0,
        "COUNT": lambda *args: len([a for a in args if a is not None]),
        "MAX": max, "MIN": min,
        "IF": lambda condition, true_val, false_val: true_val if condition else false_val,
        "CONCAT": lambda *args: "".join(str(a) for a in args),
        "NOW": lambda: datetime.now(),
        "TODAY": lambda: date.today(),
        "DATEDIFF": lambda d1, d2: (d2 - d1).days,
        "ROUND": lambda v, d=2: round(v, d),
        "ABS": abs,
        "UPPER": str.upper, "LOWER": str.lower,
        "TRIM": str.strip,
        "SUBSTR": lambda s, start, end=None: s[start:end],
        "LENGTH": len,
        "CONTAINS": lambda s, sub: sub in str(s),
        "FORMAT_MONEY": lambda v: f"¥{v:,.2f}",
        "FORMAT_PERCENT": lambda v: f"{v*100:.1f}%",
        "USER": lambda key=None: get_current_user_field(key),  # 当前用户信息
        "LOOKUP": lambda template, field, condition: lookup_value(template, field, condition),
    }
    
    async def evaluate(self, formula: str, context: Dict[str, Any]) -> Any:
        """安全求值公式"""
        # 1. 替换字段引用 {{field_name}} 为实际值
        # 2. 替换函数调用
        # 3. 安全执行（使用 ast 解析，禁止危险操作）
        pass
```

#### 3.1.3 前端公式编辑器

在模板设计器中为字段添加「公式」配置面板：

- 公式输入框 + 字段选择器（点选即插入字段引用）
- 函数列表侧栏（SUM/AVG/IF/CONCAT 等，带参数提示）
- 实时预览公式计算结果
- 公式依赖可视化（高亮依赖字段）

### 3.2 字段关联与跨模板联动

#### 3.2.1 关联类型设计

```
一对一关联 (1:1)
├── 主表字段存储外键 ID
├── 选择器组件：下拉搜索 → 显示关联记录
└── 示例：订单 ↔ 合同（一个订单对应一个合同）

一对多关联 (1:N)
├── 子表嵌入主表（子表/明细表模式）
├── 支持动态增删行
└── 示例：订单 ↔ 订单明细（一个订单包含多个明细项）

多对多关联 (M:N)
├── 通过中间表关联
├── 支持标签选择和多选
└── 示例：员工 ↔ 项目（一个员工参与多个项目）

查找关联 (Lookup)
├── 跨模板自动获取数据
├── 支持条件过滤和字段映射
└── 示例：选择客户后自动填充客户地址、联系方式
```

#### 3.2.2 数据模型扩展

新增 `SubTableField` 模型：

```python
class SubTableField(Base):
    """子表/明细表字段"""
    __tablename__ = "subtable_fields"
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("templates.id"))
    parent_field_name = Column(String(100))  # 主表中子表字段名
    child_template_id = Column(Integer, ForeignKey("templates.id"))  # 子表对应的模板
    # 子表的行级权限：允许查看/编辑/删除
    row_permissions = Column(JSON, default=dict)
```

### 3.3 数据聚合与列表视图

#### 3.3.1 列表页配置增强

```python
# AppMenu.list_page_config 扩展
{
    "columns": [...],
    "filters": [...],         # 筛选条件
    "sort": {"field": "...", "order": "desc"},
    "aggregations": [        # 列表底部汇总行
        {"field": "amount", "type": "sum", "label": "总金额"},
        {"field": "amount", "type": "avg", "label": "平均金额"},
        {"field": "id", "type": "count", "label": "记录数"}
    ],
    "group_by": "category",  # 分组展示
    "chart_widget": {        # 内嵌图表
        "type": "bar",
        "x_field": "category",
        "y_field": "amount",
        "y_agg": "sum"
    }
}
```

### 3.4 实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| P1 | 公式引擎（后端 evaluator + 前端公式编辑器） | 3天 |
| P2 | 字段联动（依赖检测、自动重算、级联选项） | 2天 |
| P3 | 子表/明细表（模型 + 前端表格组件） | 3天 |
| P4 | 关联字段（查找、下拉搜索） | 2天 |
| P5 | 数据聚合与列表增强 | 2天 |

---

## 4. 模块二：流程审批引擎升级

### 4.1 与应用/表单深度集成

#### 4.1.1 应用-流程绑定机制

在 `Application` 模型中新增：

```python
class Application(Base):
    # ... 原有字段 ...
    
    # 关联工作流
    workflows = Column(JSON, default=list)  # [{"template_id": 1, "workflow_id": 2, "trigger": "on_submit"}]
    
    # 流程配置
    workflow_config = Column(JSON, default=dict)  # 全局审批超时、通知方式等
```

在 `AppMenu` 中扩展：

```python
class AppMenu(Base):
    # ... 原有字段 ...
    
    # 菜单项关联的工作流
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=True)
    workflow_trigger = Column(String(20), nullable=True)  # "on_submit" | "on_update" | "on_delete" | "manual"
    
    # 流程中的字段权限
    workflow_field_permissions = Column(JSON, default=dict)
    # {"node_id": {"amount": "readonly", "remark": "hidden"}}
```

#### 4.1.2 表单提交流程

```
用户提交表单数据
    ↓
自动检测是否关联工作流
    ↓ (是)
创建工作流实例，绑定表单数据
    ↓
流程引擎接管 → 逐节点执行审批
    ↓
审批通过 → 数据状态更新
    ↓
触发后续事件（通知、插件、智能体）
```

### 4.2 智能审批节点

#### 4.2.1 新增 AI 审批节点类型

```python
class NodeType(str, Enum):
    # ... 原有类型 ...
    AI_APPROVAL = "ai_approval"    # AI 自动审批
    AI_REVIEW = "ai_review"        # AI 审核建议（人工最终确认）
    AI_CLASSIFY = "ai_classify"    # AI 分类路由（根据内容自动选择分支）
```

#### 4.2.2 AI 审批实现

```python
async def _handle_ai_approval_node(self, instance_id: int, node: Dict, variables: Dict):
    """AI 自动审批节点"""
    config = node.get("config", {})
    
    # 获取表单数据
    form_data = variables.get("form_data", {})
    
    # 构建审批上下文
    context = {
        "applicant": variables.get("applicant_name", ""),
        "amount": form_data.get("amount", 0),
        "reason": form_data.get("reason", ""),
        "history": self._get_approval_history(instance_id),
        "rules": config.get("rules", []),  # 审批规则
    }
    
    # 调用 AI 审批能力
    result = await capability_registry.execute(
        AICapability.AI_APPROVE,
        {
            "action": "approve",
            "context": context,
            "knowledge_base_id": config.get("knowledge_base_id"),  # 可引用知识库
        }
    )
    
    decision = result.get("decision")  # "approve" | "reject" | "escalate"
    ai_opinion = result.get("opinion", "")
    confidence = result.get("confidence", 0)
    
    # 低置信度时转人工
    if confidence < config.get("confidence_threshold", 0.8):
        # 转人工审批
        await self._create_manual_task(instance_id, node, variables)
    else:
        # AI 直接审批
        await self._auto_approve(instance_id, node, decision, ai_opinion)
```

### 4.3 流程条件增强

#### 4.3.1 高级条件表达式

升级 `ConditionEvaluator`，支持更丰富的表达式：

```
# 当前支持
{{amount}} > 1000 and {{status}} == 'approved'

# 升级后支持
{{amount}} > 1000 AND {{department}} IN ['销售部', '市场部']
{{apply_date}} >= TODAY() - 30
LOOKUP(employee, level) >= 3
SUM({{items.*.price}}) > 50000
{{content}} CONTAINS '紧急'
COUNT({{approvers}}) > 0
```

### 4.4 SLA 与超时管理

```python
class WorkflowTask(Base):
    # ... 原有字段 ...
    
    # SLA 管理
    sla_config = Column(JSON, default=dict)
    # {"deadline_hours": 24, "reminder_at": [4, 8, 20], "escalate_to": "manager"}
    sla_deadline = Column(DateTime, nullable=True)
    sla_status = Column(String(20), default="normal")  # normal/warning/overdue/escalated
    reminder_sent = Column(JSON, default=list)  # 已发送的提醒时间戳
```

### 4.5 实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| P1 | 应用-流程绑定 + 表单提交触发流程 | 3天 |
| P2 | 流程中字段权限控制 | 2天 |
| P3 | AI 审批节点 | 3天 |
| P4 | 条件表达式增强 | 2天 |
| P5 | SLA 超时/催办/自动升级 | 2天 |

---

## 5. 模块三：应用设计器升级

### 5.1 接入流程审批

#### 5.1.1 应用设计器新增「流程」标签页

```
标签页扩展：
├── 菜单设计（现有）
├── 表单关系（现有）
├── 流程设计（新增）    ← 关联工作流到菜单/表单
├── 业务插件（现有）
├── 仪表盘（增强）
├── 权限配置（现有）
├── AI 助手（增强）
└── 发布管理（新增）    ← 版本管理、灰度发布
```

#### 5.1.2 流程集成界面

- **表单-流程绑定面板**：为每个菜单项配置关联的工作流
- **触发方式选择**：提交时自动发起 / 手动发起 / 定时触发 / 事件触发
- **流程预览**：在应用内预览完整审批流
- **待办列表**：应用内统一查看所有待办任务

### 5.2 接入智能体

#### 5.2.1 应用绑定智能体

```python
class Application(Base):
    # ... 原有字段 ...
    
    # 关联智能体
    bound_agents = Column(JSON, default=list)
    # [{"agent_id": 1, "context": "应用助手", "trigger": "on_demand"}]
```

#### 5.2.2 智能体在应用中的使用场景

| 场景 | 说明 |
|------|------|
| **AI 表单助手** | 填写表单时，智能体实时提供字段建议和数据校验 |
| **AI 审批助手** | 审批时，智能体自动总结审批内容、给出审批建议 |
| **AI 数据分析** | 查看列表数据时，智能体自动生成洞察和建议 |
| **AI 搜索助手** | 应用内搜索，支持自然语言查询和知识库检索 |
| **AI 通知助手** | 自动生成通知内容，智能推荐通知对象 |

### 5.3 仪表盘实现

#### 5.3.1 仪表盘组件系统

```json
{
  "layout": "grid",
  "widgets": [
    {
      "id": "w1",
      "type": "kpi_card",
      "title": "本月订单数",
      "source": {"template_id": 1, "aggregate": "count", "filter": "created_at >= THIS_MONTH()"},
      "style": {"color": "#409EFF"}
    },
    {
      "id": "w2",
      "type": "chart",
      "chart_type": "line",
      "title": "销售趋势",
      "source": {"template_id": 1, "x_field": "created_at", "y_field": "amount", "y_agg": "sum", "group_by": "day"},
      "ai_insight": true  // 启用 AI 洞察
    },
    {
      "id": "w3",
      "type": "table",
      "title": "最新订单",
      "source": {"template_id": 1, "sort": "-created_at", "limit": 10},
      "columns": ["name", "amount", "status"]
    },
    {
      "id": "w4",
      "type": "pending_tasks",
      "title": "我的待办"
    },
    {
      "id": "w5",
      "type": "ai_summary",
      "title": "AI 工作日报",
      "source": "app_analytics"
    }
  ]
}
```

### 5.4 版本管理与发布

```python
class AppVersion(Base):
    """应用版本"""
    __tablename__ = "app_versions"
    
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("applications.id"))
    version = Column(String(20))  # "1.0.0"
    snapshot = Column(JSON)       # 完整快照（菜单+关系+插件+流程+配置）
    changelog = Column(Text)
    published_at = Column(DateTime)
    published_by = Column(Integer, ForeignKey("users.id"))
```

### 5.5 实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| P1 | 流程集成（绑定、触发、待办） | 3天 |
| P2 | 智能体集成（上下文感知、场景绑定） | 3天 |
| P3 | 仪表盘实现（KPI/图表/表格/待办） | 4天 |
| P4 | 版本管理与发布 | 2天 |

---

## 6. 模块四：AI 能力深度融合

### 6.1 AI 能力扩展清单

在现有 20 种能力基础上新增：

```python
class AICapability(str, Enum):
    # ... 原有能力 ...
    
    # 新增：表单增强
    FORMULA_GENERATE = "formula_generate"       # 根据自然语言生成公式
    VALIDATION_GENERATE = "validation_generate" # 生成校验规则
    
    # 新增：流程增强
    AI_APPROVE = "ai_approve"                   # AI 自动审批
    AI_CLASSIFY = "ai_classify"                 # AI 内容分类
    AI_SUMMARIZE_WORKFLOW = "ai_summarize_workflow"  # 总结流程执行情况
    
    # 新增：应用增强
    APP_GENERATE = "app_generate"               # 从描述生成完整应用
    APP_OPTIMIZE = "app_optimize"               # 优化应用设计
    APP_TEST = "app_test"                       # 测试应用逻辑
    
    # 新增：数据增强
    DATA_CLEANSE = "data_cleanse"               # 数据清洗
    DATA_ENRICH = "data_enrich"                 # 数据增强（自动补全）
    ANOMALY_DETECT_ADVANCED = "anomaly_detect_advanced"  # 高级异常检测
    
    # 新增：智能体增强
    AGENT_COMPOSE = "agent_compose"             # 组合多个智能体
    AGENT_TRAIN = "agent_train"                 # 微调智能体行为
```

### 6.2 上下文感知的 AI 调用

所有 AI 能力调用均携带应用上下文：

```python
class AIContext:
    """AI 调用上下文"""
    
    app_id: int                    # 当前应用
    template_id: int               # 当前模板
    workflow_instance_id: int      # 当前流程实例
    user_id: int                   # 当前用户
    user_role: str                 # 用户角色
    organization_id: int           # 组织
    knowledge_base_ids: List[int]  # 关联知识库
    form_data: Dict                # 当前表单数据
    history: List[Dict]            # 历史交互
```

### 6.3 Function Calling 与工具系统

升级智能体工具系统，支持 OpenAI 兼容的 Function Calling：

```python
# app/core/agent_engine/tools/schema.py

class ToolDefinition(BaseModel):
    """工具定义（OpenAI Function Calling 格式）"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    
    # 内置工具
class BuiltInTools:
    TOOLS = [
        {
            "name": "query_form_data",
            "description": "查询表单数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_id": {"type": "integer"},
                    "filters": {"type": "object"},
                    "fields": {"type": "array"}
                }
            }
        },
        {
            "name": "submit_form_data",
            "description": "提交表单数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_id": {"type": "integer"},
                    "data": {"type": "object"}
                }
            }
        },
        {
            "name": "start_workflow",
            "description": "启动审批流程",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "form_data_id": {"type": "integer"}
                }
            }
        },
        {
            "name": "search_knowledge",
            "description": "搜索知识库",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "knowledge_base_ids": {"type": "array"}
                }
            }
        },
        {
            "name": "send_notification",
            "description": "发送通知",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_ids": {"type": "array"},
                    "message": {"type": "string"},
                    "channel": {"type": "string"}  # "in_app" | "email"
                }
            }
        },
        {
            "name": "get_user_info",
            "description": "获取用户信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer"}
                }
            }
        }
    ]
```

### 6.4 实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| P1 | 上下文感知 + AI Context 传递 | 2天 |
| P2 | 新增 AI 能力（审批、分类、应用生成） | 4天 |
| P3 | Function Calling 工具系统 | 3天 |

---

## 7. 模块五：知识库与 RAG 升级

### 7.1 应用级知识库

```python
class Application(Base):
    # ... 原有字段 ...
    
    # 应用绑定的知识库
    knowledge_base_ids = Column(JSON, default=list)  # [1, 2, 3]
    knowledge_config = Column(JSON, default=dict)
    # {
    #   "auto_index": true,         # 新提交数据自动索引
    #   "search_scope": "app",      # 搜索范围
    #   "chunk_size": 500,
    #   "chunk_overlap": 50
    # }
```

### 7.2 业务数据自动索引

当应用开启了知识库集成：

```python
# 插件示例：表单提交后自动索引
async def on_form_submit_auto_index(context: PluginContext):
    """表单提交后自动将数据添加到知识库"""
    if not context.app.config.get("knowledge_config", {}).get("auto_index"):
        return
    
    template_id = context.template_id
    data = context.data
    
    # 将表单数据转换为文本
    text = f"模板ID:{template_id} 数据："
    for key, value in data.items():
        if value:
            text += f"\n{key}: {value}"
    
    # 添加到知识库
    kb_ids = context.app.knowledge_base_ids
    for kb_id in kb_ids:
        await rag_retriever.add_document(
            collection_name=f"app_{context.app_id}",
            doc_id=f"form_{template_id}_{data.get('id', '')}",
            text=text,
            metadata={"type": "form_data", "template_id": template_id},
            kb_id=kb_id
        )
```

### 7.3 知识库在应用中的使用

- **审批时参考知识库**：AI 审批节点可引用知识库中的政策和规定
- **表单填写时智能推荐**：根据知识库中的历史数据推荐字段值
- **应用内搜索**：支持自然语言搜索，结合知识库和应用数据
- **智能体上下文**：应用绑定的智能体自动加载知识库

### 7.4 实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| P1 | 应用-知识库绑定 + 自动索引 | 2天 |
| P2 | 知识库在流程/表单中的集成 | 2天 |

---

## 8. 模块六：智能体引擎升级

### 8.1 应用专用智能体

```python
class Agent(Base):
    """智能体配置"""
    # ... 原有字段 ...
    
    # 新增
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=True)  # 绑定应用
    scope = Column(String(20), default="global")  # "global" | "app"
    system_prompt_template = Column(Text)  # 系统提示词模板（支持变量）
    # "你是 {app_name} 的审批助手。当前用户是 {user_name}，角色是 {user_role}。"
    
    # 工具权限
    allowed_tools = Column(JSON, default=list)    # 允许使用的工具
    data_scope = Column(JSON, default=dict)       # 数据访问范围
    
    # 记忆配置
    memory_config = Column(JSON, default=dict)
    # {"enabled": true, "max_turns": 10, "summarize_after": 5}
```

### 8.2 智能体编排升级

支持更复杂的编排模式：

```
顺序编排：Agent A → Agent B → Agent C
并行编排：Agent A ─┬→ Agent B
             └→ Agent C
条件编排：IF 条件 THEN Agent A ELSE Agent B
循环编排：Agent A → (检查结果) → Agent A（直到满足条件）
人机协作：Agent A → 等待用户输入 → Agent B
子流程：Agent A → 启动子工作流 → Agent B
```

### 8.3 实施计划

| 阶段 | 内容 | 预估 |
|------|------|------|
| P1 | 应用级智能体 + 作用域 | 2天 |
| P2 | 智能体编排升级（条件/循环/人机协作） | 4天 |
| P3 | 记忆增强（对话记忆 + 长期记忆） | 2天 |

---

## 9. AI 复合应用构建方案

这是升级的核心价值：通过组合所有模块，让用户可以用自然语言描述需求，系统自动生成完整的应用。

### 9.1 场景一：AI 自动创建「采购审批系统」

**用户输入**：  
> "帮我创建一个采购审批系统，需要采购申请表、供应商管理、审批流程（金额>1万需要经理审批，>5万需要总监审批），关联供应商知识库作为审批参考"

**系统自动执行**：

```
Step 1: 需求理解
├── AI 解析用户需求，提取关键信息
├── 识别需要 2 个表单模板：采购申请、供应商
└── 识别审批规则：1万/5万 分级审批

Step 2: 智能表单生成
├── 自动创建「采购申请」模板
│   ├── 字段：物品名称、数量、单价、总价（公式）、供应商（关联字段）、
│   │         申请理由、附件上传、紧急程度
│   └── 公式：总价 = 数量 × 单价
├── 自动创建「供应商」模板
│   └── 字段：供应商名称、联系方式、合作状态、评级
└── 建立关联：采购申请.供应商 → 供应商.名称

Step 3: 流程审批生成
├── 创建采购审批工作流
│   ├── 开始 → 填写采购申请 → 条件判断(金额>1万?)
│   │   ├── 是 → 条件判断(金额>5万?)
│   │   │   ├── 是 → 总监审批 → 结束
│   │   │   └── 否 → 经理审批 → 结束
│   │   └── 否 → 直接主管审批 → 结束
│   └── AI 审核节点：审批时参考知识库中的采购政策
└── 绑定到采购申请模板（提交时触发）

Step 4: 知识库集成
├── 创建「采购政策」知识库
├── 上传采购管理制度文档
└── 绑定到审批流程（AI 审批时参考）

Step 5: 仪表盘生成
├── KPI 卡片：本月采购申请数、待审批数、总金额
├── 趋势图：月度采购金额趋势
├── 分布图：按供应商统计采购金额
└── AI 洞察：自动生成采购分析摘要

Step 6: 应用组装
├── 创建应用「采购管理系统」
├── 菜单：采购申请、供应商管理、审批中心、数据分析
├── 绑定审批流程到「采购申请」菜单
└── 绑定知识库和智能体
```

### 9.2 场景二：AI 自动创建「合同管理系统」

**核心特性组合**：
- **智能表单**：合同信息（含甲乙方关联）+ 合同条款（子表）+ 付款计划（子表）
- **流程审批**：合同签订流程（法务审核 → 财务审核 → 总经理审批）
- **知识库**：合同模板库、法律法规知识库
- **智能体**：合同审查助手（自动检查条款合规性）
- **AI 能力**：合同摘要生成、风险识别、到期提醒

### 9.3 场景三：AI 自动创建「客户服务工单系统」

**核心特性组合**：
- **智能表单**：工单信息 + 处理记录（子表）
- **流程审批**：工单派单 → 处理 → 审核 → 关单
- **智能体**：客服智能助手（自动分类、建议回复、满意度分析）
- **知识库**：产品手册、FAQ、历史工单
- **AI 能力**：情感分析、工单分类、自动回复

### 9.4 AI 应用生成引擎架构

```python
class AIAppGenerator:
    """AI 应用生成引擎"""
    
    async def generate_from_description(self, description: str, user_id: int) -> Dict:
        """从自然语言描述生成完整应用"""
        
        # 1. 意图理解与需求分析
        analysis = await self._analyze_requirements(description)
        # → {"forms": [...], "workflows": [...], "relations": [...], "agents": [...], "kb_needed": true}
        
        # 2. 生成表单模板
        templates = []
        for form_spec in analysis["forms"]:
            template = await self._generate_template(form_spec, user_id)
            templates.append(template)
        
        # 3. 生成工作流
        workflows = []
        for wf_spec in analysis["workflows"]:
            workflow = await self._generate_workflow(wf_spec, templates, user_id)
            workflows.append(workflow)
        
        # 4. 建立表单关系
        relations = self._generate_relations(analysis["relations"], templates)
        
        # 5. 生成仪表盘
        dashboard = self._generate_dashboard(templates)
        
        # 6. 创建智能体
        agents = []
        for agent_spec in analysis.get("agents", []):
            agent = await self._generate_agent(agent_spec, templates)
            agents.append(agent)
        
        # 7. 组装应用
        app = await self._assemble_app(
            name=analysis["app_name"],
            templates=templates,
            workflows=workflows,
            relations=relations,
            dashboard=dashboard,
            agents=agents,
            user_id=user_id
        )
        
        return app
    
    async def _analyze_requirements(self, description: str) -> Dict:
        """AI 分析需求"""
        system_prompt = """你是一个应用架构师。根据用户描述，分析并输出应用结构。

输出 JSON 格式：
{
    "app_name": "应用名称",
    "forms": [
        {"name": "表单名", "fields": [{"name": "字段名", "type": "text", "required": true}]},
        ...
    ],
    "workflows": [
        {"name": "流程名", "trigger_form": "表单名", "nodes": [...], "rules": [...]},
        ...
    ],
    "relations": [{"from": "表单A", "to": "表单B", "type": "many_to_one", "field": "外键字段"}],
    "agents": [{"name": "智能体名", "role": "助手角色描述", "tools": [...]}],
    "kb_needed": true,
    "kb_description": "知识库描述"
}"""
        
        response = await ai_gateway.chat_with_system_prompt(system_prompt, description)
        return json.loads(response["content"])
```

---

## 10. 实施路线图

### 10.1 分阶段实施

```
Phase 1（第 1-2 周）：基础能力升级
├── 智能表单：公式引擎 + 字段联动
├── 流程审批：条件表达式增强 + SLA 基础
└── 应用设计器：流程集成（绑定 + 触发）

Phase 2（第 3-4 周）：核心集成
├── 智能表单：子表/明细表 + 关联字段
├── 流程审批：AI 审批节点 + 字段权限
├── 应用设计器：智能体集成 + 仪表盘
└── 知识库：应用级知识库 + 自动索引

Phase 3（第 5-6 周）：AI 融合
├── AI 能力：新增审批/分类/应用生成能力
├── 智能体：编排升级 + Function Calling
├── AI 应用生成引擎
└── 端到端测试与优化

Phase 4（第 7-8 周）：打磨发布
├── 移动端适配
├── 性能优化
├── 文档编写
└── 灰度发布
```

### 10.2 优先级矩阵

```
              高价值
               │
    ┌──────────┼──────────┐
    │ 公式引擎  │ AI审批节点 │
    │ 字段联动  │ 应用生成   │
    │ 流程集成  │ 智能体集成 │
低 ├──────────┼──────────┤ 高
易  │ 子表支持  │ 仪表盘    │  难
    │ 关联字段  │ 版本管理   │
    │ 条件增强  │ 编排升级   │
    └──────────┴──────────┘
               │
              低价值
```

### 10.3 技术风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| 公式引擎安全性 | 用户注入恶意代码 | 使用 AST 解析器，禁止 eval；白名单机制 |
| AI 审批准确性 | 误判导致流程错误 | 低置信度转人工；审批日志完整记录 |
| 并行节点状态管理 | 分支同步复杂 | 使用事件驱动架构 + 状态机 |
| 移动端性能 | 复杂表单渲染慢 | 虚拟滚动 + 懒加载 + 分页 |
| SQLite 并发限制 | 多人审批冲突 | WAL 模式 + 乐观锁 + 连接池 |

---

## 附录

### A. 字段类型完整列表（升级后）

| 类型 | 说明 | 特殊属性 |
|------|------|---------|
| text | 单行文本 | maxLength, regex |
| textarea | 多行文本 | maxLength |
| number | 数字 | min, max, step, precision |
| money | 金额 | min, max, precision=2 |
| percent | 百分比 | min=0, max=100 |
| date | 日期 | format |
| datetime | 日期时间 | format |
| select | 下拉选择 | options, multiple |
| radio | 单选 | options |
| checkbox | 多选 | options |
| email | 邮箱 | 自动验证 |
| phone | 电话 | 自动验证 |
| file | 文件上传 | accept, maxSize, multiple |
| image | 图片上传 | accept, maxSize, multiple |
| user | 人员选择 | 多选, 角色过滤 |
| dept | 部门选择 | 多选 |
| relation | 关联字段 | target, display, filters |
| subtable | 子表/明细表 | sub_fields |
| formula | 计算字段 | expression, depends_on |
| lookup | 查找字段 | target, return_field |
| switch | 开关 | default |
| richtext | 富文本 | toolbar |

### B. 节点类型完整列表（升级后）

| 类型 | 说明 | 配置项 |
|------|------|--------|
| start | 开始 | 无 |
| end | 结束 | 无 |
| approval | 人工审批 | 审批人、多人会签/或签、字段权限、截止时间 |
| ai_approval | AI 自动审批 | 规则、知识库、置信度阈值、兜底审批人 |
| ai_review | AI 审核（人确认） | 同上 |
| ai_classify | AI 分类路由 | 分类规则、路由映射 |
| task | 办理任务 | 办理人 |
| cc | 抄送 | 抄送人 |
| data_fill | 数据填报 | 目标表单、字段映射 |
| data_change | 数据变更 | 操作类型、目标、映射 |
| condition | 条件分支 | 条件表达式 |
| parallel | 并行分支 | 分支数 |
| trigger | 触发插件 | 插件ID |
| delay | 延时等待 | 延时时间 |
| sub_process | 子流程 | 子流程ID |
| notification | 通知 | 通知方式、接收人、消息模板 |
| end_event | 结束事件 | 触发后续动作 |
