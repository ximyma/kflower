"""
Pydantic Schemas - 请求/响应模型
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 通用 ============
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class PageResult(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


# ============ 认证 ============
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str


# ============ 组织架构 ============
class OrganizationCreate(BaseModel):
    name: str
    code: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    parent_id: Optional[int]
    level: int
    path: Optional[str]
    is_active: bool
    created_at: datetime


# ============ 用户 ============
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    organization_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[datetime] = None


# ============ 角色 ============
class RoleCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    permissions: List[str]
    is_system: bool
    created_at: datetime


# ============ 模板 ============
class ValidationRule(BaseModel):
    """字段校验规则"""
    type: str  # required/min_value/max_value/min_length/max_length/regex/in_list/not_in_list/custom_formula
    value: Optional[Any] = None  # 规则参数值
    message: Optional[str] = None  # 自定义错误消息

    class Config:
        extra = "allow"


class CascadeSource(BaseModel):
    """级联选项配置"""
    parent_field: str  # 父字段名
    options_map: Dict[str, List[str]] = {}  # 父字段值 -> 子选项列表

    class Config:
        extra = "allow"


class VisibilityRule(BaseModel):
    """条件显示/隐藏规则"""
    type: str = "simple"  # simple / formula
    formula: Optional[str] = None  # 公式模式
    field: Optional[str] = None  # 简单模式：目标字段
    operator: Optional[str] = "eq"  # eq/neq/gt/lt/gte/lte/contains/in/not_in/is_empty/not_empty
    value: Optional[Any] = None  # 期望值

    class Config:
        extra = "allow"


class SubTableConfig(BaseModel):
    """子表/明细表配置"""
    enabled: bool = False  # 是否是子表字段
    parent_template_id: Optional[int] = None  # 父模板ID（在明细表中使用）
    foreign_key: Optional[str] = None  # 外键字段名
    display_fields: Optional[List[str]] = None  # 列表显示的字段名

    class Config:
        extra = "allow"


class ModuleField(BaseModel):
    name: str
    type: str  # text/number/date/select/radio/checkbox/formula/subform/relation/...
    label: Optional[str] = None
    required: bool = False
    readonly: bool = False
    hidden: bool = False
    placeholder: Optional[str] = None
    width: Optional[str] = '100%'
    defaultValue: Optional[str] = None
    description: Optional[str] = None
    options: Optional[List[str]] = None  # for select/radio/checkbox
    optionsText: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    maxLength: Optional[int] = None
    format: Optional[str] = None

    # === 公式/计算 ===
    formula: Optional[str] = None  # 公式表达式，例如 "{单价} * {数量}"
    formula_type: Optional[str] = None  # "calculated" | "aggregate"
    is_formula: Optional[bool] = False  # 是否为公式字段（计算字段，只读）

    # === 字段依赖与联动 ===
    depends_on: Optional[List[str]] = None  # 依赖的字段名列表（依赖字段变化时自动重算）
    cascade_update: bool = False  # 依赖字段变化时自动重算此字段

    # === 聚合计算 ===
    aggregate: Optional[Dict] = None  # {"type": "sum"|"avg"|"count"|"max"|"min", "source_field": str, "filter": "..."}

    # === 校验规则 ===
    validation_rules: Optional[List[Dict]] = None  # 高级校验规则组

    # === 条件显示/隐藏 ===
    visibility_rule: Optional[Dict] = None  # 条件显示规则

    # === 条件必填 ===
    required_when: Optional[Dict] = None  # {"field": "type", "op": "eq", "value": "VIP"} — 满足条件时变为必填

    # === 默认值公式 ===
    default_formula: Optional[str] = None  # "NOW()" | "CONCAT({prefix}, '-', {seq})" 等

    # === 级联选项 ===
    cascade_source: Optional[Dict] = None  # 级联选项配置

    # === 子表/明细表 ===
    # type=subform 时生效
    subtable_fields: Optional[List[Dict]] = None  # 子表字段定义列表（递归 ModuleField 结构）
    subtable_of: Optional[str] = None  # 所属主表字段名（在子表字段上标记）

    # === 字段权限 ===
    field_permissions: Optional[Dict] = None  # {角色/用户: "read"|"write"|"hidden"}

    # === 字段关联（跨模板自动填充 / Lookup） ===
    relation: Optional[Dict] = None  # {"target_template": "customers", "display_field": "name", "link_field": "customer_id", "auto_fill_fields": ["address", "phone"]}
    auto_fill: Optional[Dict] = None  # 兼容旧名：{"source_template_id": int, "source_field": str, "match_by": str}

    # Allow extra fields from frontend (e.g. _key, etc)
    class Config:
        extra = "allow"


class ModuleCreate(BaseModel):
    name: str
    label: Optional[str] = None
    fields: List[ModuleField]


class TemplateCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict] = None
    modules: List[ModuleCreate] = []
    ai_generated: bool = False
    ai_prompt: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict] = None
    modules: Optional[List[Dict]] = None
    is_published: Optional[bool] = None
    is_public: Optional[bool] = None  # 是否公开共享


class TemplateResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    description: Optional[str]
    category: Optional[str]
    config: Dict
    modules: List[Dict]
    ai_generated: bool
    is_published: bool
    is_public: bool = False  # 是否公开共享
    created_at: datetime
    created_by: Optional[int] = None


# ============ 模板数据提交 ============
class TemplateDataSubmit(BaseModel):
    data: Dict[str, Any]


class TemplateDataUpdate(BaseModel):
    data: Dict[str, Any]


class TemplateDataResponse(BaseModel):
    id: int
    template_id: int
    name: str
    config: Dict
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TemplateStatsResponse(BaseModel):
    total_count: int = 0
    today_count: int = 0
    field_stats: Dict[str, Any] = {}


# ============ 工作流 ============
class WorkflowNode(BaseModel):
    id: str
    type: str  # start/end/task/condition/approval/cc/data_fill/add_data/update_data/delete_data/parallel_branch/condition_branch
    name: str
    config: Dict = {}


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    condition: Optional[Dict] = None  # 连线条件


class WorkflowCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    flow_type: str = "normal"
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []
    # 斑斑低代码平台扩展字段
    node_definitions: Optional[List[Dict]] = None
    edge_definitions: Optional[List[Dict]] = None
    variables: Optional[Dict] = None
    form_template_id: Optional[int] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    is_active: Optional[bool] = None
    # 斑斑低代码平台扩展字段
    node_definitions: Optional[List[Dict]] = None
    edge_definitions: Optional[List[Dict]] = None
    variables: Optional[Dict] = None
    form_template_id: Optional[int] = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    description: Optional[str]
    flow_type: str
    nodes: List[Dict]
    edges: List[Dict]
    is_active: bool
    created_at: datetime
    # 斑斑低代码平台扩展字段
    node_definitions: Optional[List[Dict]] = None
    edge_definitions: Optional[List[Dict]] = None
    variables: Optional[Dict] = None
    form_template_id: Optional[int] = None


class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    title: str
    variables: Dict[str, Any] = {}
    form_data_id: Optional[int] = None


class WorkflowTaskActionRequest(BaseModel):
    """工作流任务操作请求"""
    action: str  # approve, reject, transfer
    opinion: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    transfer_to: Optional[int] = None  # 转交目标用户ID


# ============ AI对话 ============
class ChatMessage(BaseModel):
    role: str  # user/assistant/system
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    ai_type: Optional[str] = "general"  # general/template/workflow/analytics
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    use_rag: Optional[bool] = True      # 是否启用RAG检索增强
    enable_tools: Optional[bool] = True  # 是否启用工具调用
    model: Optional[str] = None          # 可选：指定模型
    provider: Optional[str] = None       # 可选：指定提供商
    app_id: Optional[int] = None         # 可选：应用ID，用于应用上下文感知


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    ai_type: str
    suggestions: List[str] = []
    template_data: Optional[Dict] = None  # AI生成的可直接创建模板的数据
    workflow_data: Optional[Dict] = None  # AI生成的可直接创建工作流的数据


# ============ 知识库 ============
class KnowledgeBaseCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = "text-embedding-v2"
    rerank_model: Optional[str] = None
    rerank_enabled: Optional[bool] = False
    # 扩展配置
    config: Optional[Dict[str, Any]] = None  # 包含 vectorization_enabled, search_method 等


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    rerank_model: Optional[str] = None
    rerank_enabled: Optional[bool] = None
    # 扩展配置
    config: Optional[Dict[str, Any]] = None


class DocumentUploadResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_size: int
    parsing_status: str


class DocumentQueryRequest(BaseModel):
    query: str
    knowledge_base_id: Optional[int] = None
    top_k: int = 5


# ============ 知识库标签 ============
class KnowledgeTagCreate(BaseModel):
    name: str
    color: Optional[str] = "#1890ff"
    description: Optional[str] = None
    kb_id: Optional[int] = None

class KnowledgeTagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

class DocumentTagRequest(BaseModel):
    tag_id: int

# ============ 知识笔记 ============
class KnowledgeNoteCreate(BaseModel):
    title: str
    content: Optional[str] = ""
    tags: Optional[List[str]] = []
    is_daily: Optional[bool] = False
    note_date: Optional[str] = None
    knowledge_base_id: Optional[int] = None

class KnowledgeNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_daily: Optional[bool] = None

# ============ 系统配置 ============
class SystemConfigUpdate(BaseModel):
    value: str
    description: Optional[str] = None


# ============ 数据迁移 ============
class MigrationConfig(BaseModel):
    source_type: str  # sqlite/mysql/postgresql
    source_url: str
    target_type: str  # mysql/postgresql
    target_url: str
    target_username: str
    target_password: str


class MigrationPreview(BaseModel):
    total_tables: int
    total_records: int
    estimated_time: str
    tables: List[Dict[str, Any]]
