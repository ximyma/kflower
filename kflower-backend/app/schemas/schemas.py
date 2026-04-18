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
class ModuleField(BaseModel):
    name: str
    type: str  # text/number/date/select/radio/checkbox
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
    type: str  # start/end/task/condition/approval
    name: str
    config: Dict = {}


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    flow_type: str = "normal"
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    is_active: Optional[bool] = None


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


# ============ AI对话 ============
class ChatMessage(BaseModel):
    role: str  # user/assistant/system
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    ai_type: str = "general"  # general/template/workflow/analytics
    related_type: Optional[str] = None
    related_id: Optional[int] = None


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


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    rerank_model: Optional[str] = None
    rerank_enabled: Optional[bool] = None


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
