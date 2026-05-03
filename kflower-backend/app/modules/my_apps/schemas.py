"""
我的应用模块 - Pydantic 请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Application ============
class ApplicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    theme: Optional[str] = "light"
    config: Optional[Dict] = {}


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    theme: Optional[str] = None
    config: Optional[Dict] = None
    is_published: Optional[bool] = None
    is_public: Optional[bool] = None
    knowledge_base_ids: Optional[List[int]] = None
    knowledge_config: Optional[Dict] = None
    workflow_ids: Optional[List[int]] = None
    workflow_config: Optional[Dict] = None
    bound_agents: Optional[List[int]] = None  # 改为 List[int] 与前端一致


class ApplicationResponse(ApplicationBase):
    id: int
    code: str
    is_published: bool
    is_public: bool
    created_by: int
    organization_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # ===== 添加缺失的字段 =====
    workflow_ids: Optional[List[int]] = None
    workflow_config: Optional[Dict] = None
    knowledge_base_ids: Optional[List[int]] = None
    knowledge_config: Optional[Dict] = None
    bound_agents: Optional[List[int]] = None
    
    class Config:
        from_attributes = True


# ============ AppMenu ============
class AppMenuBase(BaseModel):
    template_id: Optional[int] = None  # 允许为空，支持文件夹类型菜单
    menu_label: Optional[str] = None
    menu_icon: Optional[str] = None
    menu_order: int = 0
    is_visible: bool = True
    list_page_config: Optional[Dict] = {}
    form_page_config: Optional[Dict] = {}
    
    # ===== 流程审批集成（升级方案 4.1） =====
    workflow_id: Optional[int] = None
    workflow_trigger: Optional[str] = "manual"
    workflow_auto_approve: Optional[bool] = False
    workflow_field_permissions: Optional[Dict] = {}
    workflow_node_mapping: Optional[List[Dict]] = []


class AppMenuCreate(AppMenuBase):
    parent_id: Optional[int] = None


class AppMenuUpdate(BaseModel):
    parent_id: Optional[int] = None
    template_id: Optional[int] = None
    menu_label: Optional[str] = None
    menu_icon: Optional[str] = None
    menu_order: Optional[int] = None
    is_visible: Optional[bool] = None
    list_page_config: Optional[Dict] = None
    form_page_config: Optional[Dict] = None
    # ===== 流程审批集成 =====
    workflow_id: Optional[int] = None
    workflow_trigger: Optional[str] = None
    workflow_auto_approve: Optional[bool] = None
    workflow_field_permissions: Optional[Dict] = None
    workflow_node_mapping: Optional[List[Dict]] = None


class AppMenuResponse(AppMenuBase):
    id: int
    app_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    # 注意：children 在此处始终为空数组，由 MenuTreeNode 端点提供树形结构
    # 避免在序列化 ORM 对象时触发 lazy-load 导致 500 错误
    children: List["AppMenuResponse"] = []

    class Config:
        from_attributes = True
        # 序列化时排除 children 字段，避免触发 SQLAlchemy lazy-load
        populate_by_name = True


# 简化版菜单响应（用于单条 CRUD，不含 children，避免 lazy-load 问题）
class AppMenuSimple(BaseModel):
    id: int
    app_id: int
    parent_id: Optional[int] = None
    template_id: Optional[int] = None
    menu_label: Optional[str] = None
    menu_icon: Optional[str] = None
    menu_order: int = 0
    is_visible: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ FormRelation ============
class FormRelationBase(BaseModel):
    from_template_id: int
    from_field_name: str
    to_template_id: int
    relation_type: str  # belongs_to, has_many, many_to_many
    display_field: Optional[str] = None
    on_delete: str = "set_null"
    reverse_name: Optional[str] = None
    auto_fill_fields: Optional[List[Dict[str, str]]] = None  # [{"from": "name", "to": "customer_name"}]


class FormRelationCreate(FormRelationBase):
    pass


class FormRelationUpdate(BaseModel):
    from_field_name: Optional[str] = None
    relation_type: Optional[str] = None
    display_field: Optional[str] = None
    on_delete: Optional[str] = None
    reverse_name: Optional[str] = None
    auto_fill_fields: Optional[List[Dict[str, str]]] = None  # [{"from": "name", "to": "customer_name"}]


class FormRelationResponse(FormRelationBase):
    id: int
    app_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ AppPlugin ============
class AppPluginBase(BaseModel):
    name: str
    trigger_event: str
    target_template_id: Optional[int] = None
    script_code: str
    is_enabled: bool = True


class AppPluginCreate(AppPluginBase):
    pass


class AppPluginUpdate(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    target_template_id: Optional[int] = None
    script_code: Optional[str] = None
    is_enabled: Optional[bool] = None


class AppPluginResponse(AppPluginBase):
    id: int
    app_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 应用完整详情 ============
class AppDetailResponse(ApplicationResponse):
    menus: List[AppMenuResponse] = []
    relations: List[FormRelationResponse] = []
    plugins: List[AppPluginResponse] = []


# ============ 菜单树 ============
class MenuTreeNode(BaseModel):
    id: int
    label: str
    icon: Optional[str] = None
    path: Optional[str] = None  # 当没有模板时可能为空
    template_id: Optional[int] = None  # 允许为空，支持文件夹类型菜单
    workflow_id: Optional[int] = None
    workflow_trigger: Optional[str] = None
    workflow_auto_approve: Optional[bool] = None
    workflow_node_mapping: Optional[List[Dict]] = None
    children: List["MenuTreeNode"] = []


# ============ AppVersion (升级方案 5.4) ============
class VersionCreate(BaseModel):
    version: str = Field(..., description="版本号如1.0.0")
    changelog: Optional[str] = None
    is_stable: bool = False

class VersionResponse(BaseModel):
    id: int
    app_id: int
    version: str
    changelog: Optional[str] = None
    is_stable: bool
    is_current: bool
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None  # 数据库无 updated_at 列，只保留 created_at

    class Config:
        from_attributes = True

# 解决循环引用
AppMenuResponse.model_rebuild()
MenuTreeNode.model_rebuild()
