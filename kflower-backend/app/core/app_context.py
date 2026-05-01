"""
应用上下文 - 统一协同层
每个应用在运行时的完整上下文快照

整合优化 2.1：创建 AppContext 应用上下文机制
用于在用户进入某个"我的应用"时，自动加载该应用绑定的工作流、知识库、智能体、插件，
形成一个统一的应用上下文对象，后续所有功能调用都携带此上下文。
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class AppContext:
    """
    应用上下文 - 统一协同层数据类

    属性：
        app_id: 应用ID
        app_code: 应用编码
        app_name: 应用名称
        workflow_ids: 应用关联的工作流ID列表
        knowledge_base_ids: 应用绑定的知识库ID列表
        bound_agents: 应用绑定的智能体列表
        plugin_ids: 应用绑定的插件ID列表
        user_id: 当前用户ID
        user_name: 当前用户名
        meta: 扩展元数据

    使用场景：
        1. 智能体对话时，携带应用上下文使用专属知识库
        2. 表单提交时，携带应用上下文触发插件钩子
        3. 工作流启动时，携带应用上下文获取关联数据
    """
    app_id: int
    app_code: str
    app_name: str
    # 关联配置
    workflow_ids: List[int] = field(default_factory=list)
    knowledge_base_ids: List[int] = field(default_factory=list)
    bound_agents: List[Dict] = field(default_factory=list)
    plugin_ids: List[int] = field(default_factory=list)
    # 运行时用户
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    # 扩展元数据
    meta: Dict[str, Any] = field(default_factory=dict)
    # 关联的模板ID（从菜单中获取）
    template_ids: List[int] = field(default_factory=list)
    # 创建时间
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "app_code": self.app_code,
            "app_name": self.app_name,
            "workflow_ids": self.workflow_ids,
            "knowledge_base_ids": self.knowledge_base_ids,
            "bound_agents": self.bound_agents,
            "plugin_ids": self.plugin_ids,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "template_ids": self.template_ids,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_agent_context(self) -> Dict[str, Any]:
        """转为智能体上下文格式"""
        return {
            "app_id": self.app_id,
            "app_code": self.app_code,
            "app_name": self.app_name,
            "workflow_ids": self.workflow_ids,
            "knowledge_base_ids": self.knowledge_base_ids,
            "bound_agents": self.bound_agents,
            "template_ids": self.template_ids,
            "user_id": self.user_id,
            "user_name": self.user_name,
        }

    def get_rag_collections(self) -> List[str]:
        """
        获取知识库检索时使用的向量集合名称列表

        格式：
            - 全局知识库：knowledge
            - 应用专属知识库：kb_{knowledge_base_id}
        """
        collections = ["knowledge"]  # 全局知识库
        for kb_id in self.knowledge_base_ids:
            collections.append(f"kb_{kb_id}")
        return list(set(collections))

    def has_workflow(self, workflow_id: int) -> bool:
        """检查应用是否关联指定工作流"""
        return workflow_id in self.workflow_ids

    def get_bound_agent(self, agent_id: int) -> Optional[Dict]:
        """获取绑定的智能体配置"""
        for agent in self.bound_agents:
            if agent.get("agent_id") == agent_id:
                return agent
        return None


async def build_app_context(
    app_id: int,
    user_id: int,
    db
) -> AppContext:
    """
    从数据库构建完整的应用上下文

    Args:
        app_id: 应用ID
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        AppContext 应用上下文对象
    """
    from sqlalchemy import select
    from app.modules.my_apps.models import Application, AppMenu
    from app.models.user import User

    # 获取应用信息
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()

    if not app:
        raise ValueError(f"Application {app_id} not found")

    # 获取用户信息
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    user_name = user.full_name if user else None

    # 获取菜单关联的模板ID
    menu_result = await db.execute(
        select(AppMenu.template_id).where(
            AppMenu.app_id == app_id,
            AppMenu.template_id.isnot(None)
        )
    )
    template_ids = [row[0] for row in menu_result.fetchall() if row[0]]

    # 从应用配置中提取工作流ID列表
    workflow_ids = []
    if app.workflow_ids:
        for wf in (app.workflow_ids if isinstance(app.workflow_ids, list) else []):
            if isinstance(wf, dict) and wf.get("workflow_id"):
                workflow_ids.append(wf["workflow_id"])
            elif isinstance(wf, int):
                workflow_ids.append(wf)

    # 构建应用上下文
    return AppContext(
        app_id=app.id,
        app_code=app.code,
        app_name=app.name,
        workflow_ids=workflow_ids,
        knowledge_base_ids=app.knowledge_base_ids or [],
        bound_agents=app.bound_agents or [],
        plugin_ids=[],  # 插件ID从 app_plugin_bindings 表获取
        user_id=user_id,
        user_name=user_name,
        template_ids=template_ids,
        meta={
            "is_published": app.is_published,
            "theme": app.theme,
            "icon": app.icon,
        },
    )


# 全局应用上下文管理器
class AppContextManager:
    """
    应用上下文管理器
    管理当前请求的应用上下文，支持在请求生命周期内快速访问
    """

    _contexts: Dict[str, AppContext] = {}

    @classmethod
    def set_context(cls, key: str, context: AppContext):
        """设置上下文"""
        cls._contexts[key] = context

    @classmethod
    def get_context(cls, key: str) -> Optional[AppContext]:
        """获取上下文"""
        return cls._contexts.get(key)

    @classmethod
    def clear_context(cls, key: str):
        """清除上下文"""
        cls._contexts.pop(key, None)

    @classmethod
    def clear_all(cls):
        """清除所有上下文"""
        cls._contexts.clear()


# 便捷函数：生成请求上下文键
def get_request_context_key(app_id: int, user_id: int, request_id: str = None) -> str:
    """生成请求上下文键"""
    import uuid
    return f"app_{app_id}_user_{user_id}_{request_id or uuid.uuid4().hex[:8]}"
