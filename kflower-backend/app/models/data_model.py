"""
数据建模模块 - 数据库模型
支持从外部数据库导入、可视化建表、AI辅助建模
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DatabaseConnection(Base):
    """数据库连接配置"""
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="连接名称")
    db_type = Column(String(20), nullable=False, comment="mysql/postgresql/sqlite")
    host = Column(String(200), nullable=True, comment="主机地址")
    port = Column(Integer, nullable=True, comment="端口")
    database = Column(String(200), nullable=True, comment="数据库名/文件路径")
    username = Column(String(100), nullable=True, comment="用户名")
    password_encrypted = Column(Text, nullable=True, comment="加密后的密码")
    config = Column(JSON, default=dict, comment="额外配置: charset/ssl/timeout等")
    is_active = Column(Boolean, default=True, comment="是否可用")
    last_test_at = Column(DateTime, nullable=True, comment="最后测试时间")
    last_test_result = Column(String(20), nullable=True, comment="success/failed")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DataModel(Base):
    """数据模型定义"""
    __tablename__ = "data_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="表名(英文)")
    title = Column(String(200), nullable=False, comment="显示名(中文)")
    description = Column(Text, nullable=True, comment="描述")
    source_type = Column(String(30), default="manual",
        comment="来源: manual/import_db/copy_kflower/ai")
    source_connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=True)
    source_table_name = Column(String(200), nullable=True, comment="来源原始表名")
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True, comment="生成的模板ID")
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    is_created = Column(Boolean, default=False, comment="是否已创建物理表")
    table_name = Column(String(200), nullable=True, comment="实际数据库表名")
    config = Column(JSON, default=dict, comment="模型配置: indexes/constraints等")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DataModelField(Base):
    """数据模型字段定义"""
    __tablename__ = "data_model_fields"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("data_models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="字段名(英文)")
    title = Column(String(200), nullable=False, comment="显示名(中文)")
    description = Column(Text, nullable=True, comment="字段说明")
    db_type = Column(String(50), nullable=False,
        comment="数据库类型: INTEGER/REAL/TEXT/BOOLEAN/DATE/DATETIME/JSON/BLOB")
    ui_type = Column(String(50), nullable=True,
        comment="UI控件类型: text/number/date/select/switch/checkbox/upload/image/relation/subform")
    is_primary_key = Column(Boolean, default=False, comment="是否主键")
    is_auto_increment = Column(Boolean, default=False, comment="是否自增")
    is_required = Column(Boolean, default=False, comment="是否必填")
    is_unique = Column(Boolean, default=False, comment="是否唯一")
    is_indexed = Column(Boolean, default=False, comment="是否建索引")
    is_system = Column(Boolean, default=False, comment="系统字段不可删除")
    default_value = Column(Text, nullable=True, comment="默认值")
    max_length = Column(Integer, nullable=True, comment="最大长度")
    min_value = Column(Float, nullable=True, comment="最小值")
    max_value = Column(Float, nullable=True, comment="最大值")
    options = Column(JSON, default=list, comment="选项列表: [{label,value}]")
    placeholder = Column(String(200), nullable=True, comment="输入提示")
    width = Column(String(20), default="100%", comment="字段宽度")
    relation_config = Column(JSON, default=dict, comment="关联配置")
    sort_order = Column(Integer, default=0, comment="排序序号")
    ai_suggested = Column(Boolean, default=False, comment="AI推荐的字段")
    ai_confidence = Column(Float, nullable=True, comment="AI推荐置信度0-1")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DataModelRelation(Base):
    """数据模型关联关系"""
    __tablename__ = "data_model_relations"

    id = Column(Integer, primary_key=True, index=True)
    from_model_id = Column(Integer, ForeignKey("data_models.id", ondelete="CASCADE"), nullable=False)
    to_model_id = Column(Integer, ForeignKey("data_models.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(30), nullable=False,
        comment="one_to_one/one_to_many/many_to_many")
    from_field = Column(String(100), nullable=False, comment="来源表外键字段")
    to_field = Column(String(100), default="id", comment="目标表关联字段")
    display_field = Column(String(100), nullable=True, comment="关联显示字段")
    reverse_name = Column(String(100), nullable=True, comment="反向关联名称")
    on_delete = Column(String(20), default="set_null", comment="cascade/set_null/restrict")
    on_update = Column(String(20), default="cascade", comment="cascade/restrict")
    created_at = Column(DateTime, server_default=func.now())
