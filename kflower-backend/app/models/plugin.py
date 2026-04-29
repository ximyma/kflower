"""
插件系统 - 数据库模型
支持插件安装、模板绑定、应用集成
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Plugin(Base):
    """插件元信息"""
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="插件标识(英文)")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="插件描述")
    version = Column(String(50), default="1.0.0", comment="版本号")
    author = Column(String(100), nullable=True, comment="作者")
    homepage = Column(String(500), nullable=True, comment="官网URL")
    icon = Column(String(50), default="puzzle-piece", comment="图标名称")
    category = Column(String(50), default="custom", comment="分类: custom/builtin/market")

    # 安装类型
    install_type = Column(String(20), default="builtin",
        comment="安装方式: builtin/local/npm/url")
    package_name = Column(String(200), nullable=True, comment="NPM包名")
    file_path = Column(String(500), nullable=True, comment="本地文件路径")
    download_url = Column(String(500), nullable=True, comment="远程下载地址")

    # 状态
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    is_built_in = Column(Boolean, default=False, comment="内置插件不可卸载")
    is_installed = Column(Boolean, default=True, comment="是否已安装")

    # 配置与代码
    config = Column(JSON, default=dict, comment="插件配置JSON")
    hook_code = Column(JSON, default=dict, comment="各钩子的Python代码 {hook_name: code}")

    # 统计
    install_count = Column(Integer, default=0, comment="安装次数")
    last_install_at = Column(DateTime, nullable=True, comment="最后安装时间")

    organization_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    template_plugins = relationship("TemplatePlugin", back_populates="plugin", cascade="all, delete-orphan")
    app_plugins = relationship("AppPlugin", back_populates="plugin", cascade="all, delete-orphan")


class PluginVersion(Base):
    """插件版本历史"""
    __tablename__ = "plugin_versions"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    changelog = Column(Text, nullable=True, comment="版本更新说明")
    file_path = Column(String(500), nullable=True, comment="安装包路径")
    size_kb = Column(Integer, nullable=True, comment="包大小KB")
    download_count = Column(Integer, default=0, comment="下载次数")
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    plugin = relationship("Plugin", backref="versions")


class PluginHook(Base):
    """插件钩子定义（系统预置）"""
    __tablename__ = "plugin_hooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="钩子名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, nullable=True, comment="钩子说明")
    event = Column(String(50), nullable=False, comment="触发事件")
    params_schema = Column(JSON, default=dict, comment="参数JSON Schema")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now())


# ─────────────────────────────────────────────────────────────────────────────
#  内置钩子定义（安装插件时自动创建）
# ─────────────────────────────────────────────────────────────────────────────
BUILTIN_HOOKS = [
    {
        "name": "before_form_render",
        "display_name": "表单渲染前",
        "description": "在表单加载渲染之前执行，可修改字段值或添加自定义字段",
        "event": "form.render",
        "params_schema": {"type": "object", "properties": {"fields": {"type": "array"}}}
    },
    {
        "name": "after_form_submit",
        "display_name": "表单提交后",
        "description": "数据保存成功后执行，可用于发送通知、更新关联数据",
        "event": "form.submit",
        "params_schema": {"type": "object", "properties": {"data": {"type": "object"}}}
    },
    {
        "name": "before_form_submit",
        "display_name": "表单提交前",
        "description": "数据保存之前执行，可用于数据校验或修改提交值",
        "event": "form.submit",
        "params_schema": {"type": "object", "properties": {"data": {"type": "object"}}}
    },
    {
        "name": "after_data_delete",
        "display_name": "数据删除后",
        "description": "数据删除成功后执行，可用于清理关联数据或发送通知",
        "event": "data.delete",
        "params_schema": {"type": "object", "properties": {"data": {"type": "object"}}}
    },
    {
        "name": "on_list_load",
        "display_name": "列表加载时",
        "description": "列表数据加载时执行，可用于动态过滤或添加计算列",
        "event": "list.load",
        "params_schema": {"type": "object", "properties": {"filters": {"type": "object"}}}
    },
    {
        "name": "on_field_change",
        "display_name": "字段值变更时",
        "description": "字段值变化时触发，可用于联动计算或显示隐藏",
        "event": "field.change",
        "params_schema": {"type": "object", "properties": {"field": {"type": "string"}, "value": {}}}
    },
    {
        "name": "on_cron_schedule",
        "display_name": "定时任务",
        "description": "按配置的 cron 表达式定时执行",
        "event": "cron.schedule",
        "params_schema": {"type": "object", "properties": {"cron": {"type": "string"}}}
    },
    {
        "name": "on_api_called",
        "display_name": "API调用时",
        "description": "当模板的 API 被外部调用时触发",
        "event": "api.called",
        "params_schema": {"type": "object", "properties": {"path": {"type": "string"}, "method": {"type": "string"}}}
    },
]


def seed_builtin_hooks(db):
    """初始化内置钩子"""
    for hook_def in BUILTIN_HOOKS:
        exists = db.query(PluginHook).filter_by(name=hook_def["name"]).first()
        if not exists:
            db.add(PluginHook(**hook_def))
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
#  to_dict 方法扩展
# ─────────────────────────────────────────────────────────────────────────────

def _plugin_to_dict(self):
    """Plugin 模型序列化"""
    hook_code_dict = self.hook_code or {}
    return {
        "id": self.id,
        "name": self.name,
        "display_name": self.display_name,
        "description": self.description,
        "version": self.version,
        "author": self.author,
        "homepage": self.homepage,
        "icon": self.icon,
        "category": self.category,
        "install_type": self.install_type,
        "package_name": self.package_name,
        "is_enabled": self.is_enabled,
        "is_built_in": self.is_built_in,
        "is_installed": self.is_installed,
        "config": self.config or {},
        "hook_code": hook_code_dict,
        "hook_events": list(hook_code_dict.keys()),
        "code_snippet": list(hook_code_dict.values())[0] if hook_code_dict else "",
        "install_count": self.install_count or 0,
        "last_install_at": self.last_install_at.isoformat() if self.last_install_at else None,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }


def _plugin_version_to_dict(self):
    return {
        "id": self.id,
        "plugin_id": self.plugin_id,
        "version": self.version,
        "changelog": self.changelog,
        "size_kb": self.size_kb,
        "download_count": self.download_count or 0,
        "created_at": self.created_at.isoformat() if self.created_at else None,
    }


def _plugin_hook_to_dict(self):
    return {
        "id": self.id,
        "name": self.name,
        "display_name": self.display_name,
        "description": self.description,
        "event": self.event,
        "params_schema": self.params_schema or {},
        "is_active": self.is_active,
        "created_at": self.created_at.isoformat() if self.created_at else None,
    }


# 动态绑定 to_dict 方法
Plugin.to_dict = _plugin_to_dict
PluginVersion.to_dict = _plugin_version_to_dict
PluginHook.to_dict = _plugin_hook_to_dict
