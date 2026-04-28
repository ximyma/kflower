# Kflower 数据建模功能 — 详细设计方案

> 为模板设计新增第5种建模方式：从数据库数据表直接生成模板表单

---

## 一、功能定位

### 1.1 与现有4种方式的关系

```
现有方式（模板驱动）:
  1. 手动拖拽设计    → 先设计表单 → 发布时建表
  2. JSON导入       → 先设计表单 → 发布时建表
  3. 文件导入(Excel/Word/PDF/图片) → 解析后设计表单 → 发布时建表
  4. AI对话生成      → 先设计表单 → 发布时建表

新增方式（数据驱动）:
  5. 数据建模        → 先有数据表 → 反向生成模板表单
```

**核心差异：** 前4种是"模板→数据表"，第5种是"数据表→模板"，方向相反、互为补充。

### 1.2 适用场景

| 场景 | 说明 |
|------|------|
| **已有数据库迁移** | 公司有 MySQL/PostgreSQL/SQLite 数据库，想用 Kflower 做管理界面 |
| **系统集成对接** | 外部系统（ERP/CRM/OA）已有数据表，Kflower 需要读写这些表 |
| **专业数据建模** | DBA/架构师需要先设计严格的数据结构，再配管理界面 |
| **快速复制模板** | 已发布的模板表单，一键复制为新模板（微调字段即可） |
| **多表关联建模** | 订单-订单明细-客户等复杂关联，先建模再生成界面 |

### 1.3 核心原则

1. **不改变现有架构** — 新增模块，不修改已有代码
2. **与现有模板体系统一** — 生成的模板和手动创建的模板结构完全一致
3. **AI增强** — 利用 Kflower 的 AI 能力，让建模过程更智能
4. **双向同步** — 建模后的表结构变更可以同步回模板

---

## 二、功能设计

### 2.1 功能全景

```
┌──────────────────────────────────────────────────────────┐
│                   数据建模（Data Modeling）                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ A.连接外部   │  │ B.可视化    │  │ C.AI辅助    │     │
│  │   数据库     │  │   建表      │  │   建模      │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │              │
│         ▼                ▼                ▼              │
│  ┌──────────────────────────────────────────────────┐   │
│  │            数据模型定义层（统一格式）               │   │
│  │  table_name / columns / relations / indexes      │   │
│  └───────────────────────┬──────────────────────────┘   │
│                          │                               │
│         ┌────────────────┼────────────────┐             │
│         ▼                ▼                ▼              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 创建数据表   │  │ 生成Kflower │  │ 一键复制     │     │
│  │ (物理建表)   │  │   模板      │  │ 已有模板     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 2.2 A. 连接外部数据库

#### 功能描述

连接外部 MySQL/PostgreSQL/SQLite 数据库，选择表，一键导入为 Kflower 模板。

#### 用户流程

```
Step 1: 配置数据库连接
  ┌──────────────────────────────────────┐
  │  数据库类型: [MySQL ▼]               │
  │  主机地址:   [192.168.1.100         ]│
  │  端口:       [3306                  ]│
  │  数据库名:   [company_db            ]│
  │  用户名:     [readonly              ]│
  │  密码:       [••••••••              ]│
  │                                      │
  │  [测试连接]  [保存连接]              │
  └──────────────────────────────────────┘

Step 2: 选择数据表
  ┌──────────────────────────────────────┐
  │  ☑ customers     (12字段, 1,523条)   │
  │  ☑ orders        (8字段, 8,921条)    │
  │  ☐ order_items   (6字段, 23,441条)   │
  │  ☐ products      (9字段, 342条)      │
  │  ☐ suppliers     (7字段, 28条)       │
  │                                      │
  │  [全选] [全不选] [导入选中表]         │
  └──────────────────────────────────────┘

Step 3: 字段映射预览
  ┌──────────────────────────────────────┐
  │  表: customers                       │
  │  ┌─────────┬──────┬────────┬──────┐ │
  │  │数据库字段│类型  │模板字段│控件  │ │
  │  ├─────────┼──────┼────────┼──────┤ │
  │  │id       │INT   │✅ ID   │编号  │ │
  │  │name     │VARCHAR│✅ 姓名 │文本  │ │
  │  │phone    │VARCHAR│✅ 电话 │文本  │ │
  │  │type     │ENUM  │✅ 类型 │下拉  │ │
  │  │credit   │DECIMAL│✅ 额度 │数字  │ │
  │  │is_vip   │TINYINT│✅ VIP  │开关  │ │
  │  │remark   │TEXT  │✅ 备注 │多行  │ │
  │  │...      │      │       │      │ │
  │  └─────────┴──────┴────────┴──────┘ │
  │                                      │
  │  [智能映射] [生成模板]               │
  └──────────────────────────────────────┘
```

#### 数据库连接配置表

```python
class DatabaseConnection(Base):
    """数据库连接配置"""
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="连接名称，如：公司ERP库")
    db_type = Column(String(20), nullable=False, comment="数据库类型: mysql/postgresql/sqlite")
    
    # 连接参数
    host = Column(String(200), nullable=True, comment="主机地址")
    port = Column(Integer, nullable=True, comment="端口")
    database = Column(String(200), nullable=True, comment="数据库名/文件路径(SQLite)")
    username = Column(String(100), nullable=True, comment="用户名")
    password_encrypted = Column(Text, nullable=True, comment="加密后的密码")
    
    # 连接配置
    config = Column(JSON, default=dict, comment="额外配置: charset/ssl/timeout等")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否可用")
    last_test_at = Column(DateTime, nullable=True, comment="最后测试连接时间")
    last_test_result = Column(String(20), nullable=True, comment="成功/失败")
    
    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### 外部数据库分析引擎

```python
# app/services/db_analyzer.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ColumnInfo:
    """数据库列信息"""
    name: str
    db_type: str          # 原始数据库类型: VARCHAR(255), INT, DECIMAL(10,2)...
    nullable: bool
    default_value: Any
    is_primary_key: bool
    is_unique: bool
    is_auto_increment: bool
    max_length: Optional[int]
    comment: Optional[str]   # 数据库字段注释
    enum_values: List[str]   # ENUM类型的可选值


@dataclass 
class RelationInfo:
    """外键关系信息"""
    column_name: str
    target_table: str
    target_column: str
    on_delete: str          # CASCADE/SET NULL/RESTRICT
    on_update: str


@dataclass
class TableAnalysis:
    """数据表分析结果"""
    table_name: str
    comment: Optional[str]
    columns: List[ColumnInfo]
    relations: List[RelationInfo]
    indexes: List[Dict]
    row_count: int


class DatabaseAnalyzer:
    """数据库结构分析引擎"""
    
    def __init__(self, db_type: str, connection_params: dict):
        self.db_type = db_type
        self.params = connection_params
    
    async def connect(self) -> bool:
        """测试连接"""
        pass
    
    async def list_tables(self) -> List[Dict]:
        """列出所有表"""
        pass
    
    async def analyze_table(self, table_name: str) -> TableAnalysis:
        """分析单表结构"""
        pass
    
    async def analyze_all_tables(self) -> List[TableAnalysis]:
        """分析所有表"""
        pass
    
    async def preview_data(self, table_name: str, limit: int = 10) -> List[Dict]:
        """预览表数据（前N条）"""
        pass
    
    async def close(self):
        """关闭连接"""
        pass


class MySQLAnalyzer(DatabaseAnalyzer):
    """MySQL 数据库分析"""
    
    async def list_tables(self) -> List[Dict]:
        sql = """
        SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = :db_name
        ORDER BY TABLE_NAME
        """
        # 返回 [{name, comment, row_count}]
    
    async def analyze_table(self, table_name: str) -> TableAnalysis:
        # 1. 查询列信息
        col_sql = """
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
               COLUMN_KEY, EXTRA, CHARACTER_MAXIMUM_LENGTH,
               COLUMN_COMMENT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name
        ORDER BY ORDINAL_POSITION
        """
        
        # 2. 查询外键关系
        fk_sql = """
        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME,
               DELETE_RULE, UPDATE_RULE
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        
        # 3. 查询索引
        idx_sql = """
        SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE, SEQ_IN_INDEX
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name
        """
        
        # 4. 预估行数
        count_sql = "SELECT COUNT(*) FROM {table_name}"
        
        # 整合返回 TableAnalysis


class PostgreSQLAnalyzer(DatabaseAnalyzer):
    """PostgreSQL 数据库分析"""
    
    async def list_tables(self) -> List[Dict]:
        sql = """
        SELECT tablename AS name, 
               obj_description((schemaname||'.'||tablename)::regclass) AS comment
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
        """
    
    async def analyze_table(self, table_name: str) -> TableAnalysis:
        # 查询列: information_schema.columns + pg_description
        # 查询外键: information_schema.table_constraints + key_column_usage
        # 查询索引: pg_indexes
        pass


class SQLiteAnalyzer(DatabaseAnalyzer):
    """SQLite 数据库分析"""
    
    async def list_tables(self) -> List[Dict]:
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    
    async def analyze_table(self, table_name: str) -> TableAnalysis:
        # 1. PRAGMA table_info(table_name)
        # 2. PRAGMA foreign_key_list(table_name)
        # 3. PRAGMA index_list(table_name) + PRAGMA index_info(index_name)
        # 4. SELECT COUNT(*) FROM table_name
        pass
```

### 2.3 B. 可视化建表

#### 功能描述

在 Kflower 界面中直接设计数据表结构，类似数据库管理工具的建表功能。

#### 用户流程

```
Step 1: 新建数据模型
  ┌──────────────────────────────────────────────────┐
  │  数据模型名称: [客户信息表                      ]│
  │  表名(英文):   [customers        ] 自动推荐 ✓    │
  │  描述:         [管理公司客户基本信息              ]│
  │                                                  │
  │  ┌──────────────────────────────────────────────┐│
  │  │ 字段列表                        [+添加字段] ││
  │  ├──────┬──────┬────┬────┬─────┬─────┬────────┤│
  │  │ 字段名│类型  │必填│唯一│默认值│注释 │ 操作  ││
  │  ├──────┼──────┼────┼────┼─────┼─────┼────────┤│
  │  │ id   │INT   │ ✓  │ ✓  │自增 │编号 │ ✎ 🗑 ││
  │  │ name │STR255│ ✓  │    │     │姓名 │ ✎ 🗑 ││
  │  │ phone│STR20 │    │    │     │电话 │ ✎ 🗑 ││
  │  │ type │SELECT│    │    │     │类型 │ ✎ 🗑 ││
  │  │      │      │    │    │     │     │       ││
  │  └──────┴──────┴────┴────┴─────┴─────┴────────┘│
  │                                                  │
  │  [AI推荐字段] [创建并生成模板] [仅创建表]       │
  └──────────────────────────────────────────────────┘

Step 2: 添加字段详情
  ┌──────────────────────────────────────┐
  │  字段名:    [type                  ] │
  │  显示名:    [客户类型              ] │
  │  数据类型:  [下拉选择 ▼]            │
  │  选项值:                              │
  │    ○ 潜在客户                        │
  │    ○ 普通客户                        │
  │    ○ VIP客户                         │
  │    ○ 战略客户                        │
  │    [+添加选项]                       │
  │  必填:  ☑    唯一:  ☐               │
  │  默认值:    [普通客户]               │
  │  [确定] [取消]                       │
  └──────────────────────────────────────┘

Step 3: 设置关联关系
  ┌──────────────────────────────────────┐
  │  关联关系                   [+添加]  │
  │  ┌────────────────────────────────┐  │
  │  │ 本表字段    关联类型   目标表  │  │
  │  │ company_id  →N:1    companies │  │
  │  │ orders      ←1:N    orders   │  │
  │  └────────────────────────────────┘  │
  └──────────────────────────────────────┘
```

#### 数据模型定义表

```python
class DataModel(Base):
    """数据模型定义"""
    __tablename__ = "data_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="表名(英文)")
    title = Column(String(200), nullable=False, comment="显示名(中文)")
    description = Column(Text, nullable=True, comment="描述")
    
    # 来源
    source_type = Column(String(30), default="manual", 
        comment="来源: manual=手动创建, import_db=外部数据库导入, import_kflower=复制Kflower表, ai=AI生成")
    source_connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=True,
        comment="来源数据库连接ID")
    source_table_name = Column(String(200), nullable=True, comment="来源原始表名")
    
    # 关联
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True,
        comment="生成关联的模板ID")
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True,
        comment="所属应用ID")
    
    # 状态
    is_created = Column(Boolean, default=False, comment="是否已创建物理表")
    table_name = Column(String(200), nullable=True, comment="实际数据库表名")
    
    # 配置
    config = Column(JSON, default=dict, comment="模型配置: indexes/constraints等")
    
    # 组织
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DataModelField(Base):
    """数据模型字段定义"""
    __tablename__ = "data_model_fields"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("data_models.id"), nullable=False)
    
    # 字段基本信息
    name = Column(String(100), nullable=False, comment="字段名(英文)")
    title = Column(String(200), nullable=False, comment="显示名(中文)")
    description = Column(Text, nullable=True, comment="字段说明")
    
    # 数据类型
    db_type = Column(String(50), nullable=False, 
        comment="数据库类型: INTEGER/REAL/TEXT/BLOB/BOOLEAN/DATE/DATETIME/JSON")
    ui_type = Column(String(50), nullable=False,
        comment="UI控件类型: text/number/date/select/switch/checkbox/upload/image/relation/subform...")
    
    # 字段属性
    is_primary_key = Column(Boolean, default=False, comment="是否主键")
    is_auto_increment = Column(Boolean, default=False, comment="是否自增")
    is_required = Column(Boolean, default=False, comment="是否必填(NOT NULL)")
    is_unique = Column(Boolean, default=False, comment="是否唯一")
    is_indexed = Column(Boolean, default=False, comment="是否建索引")
    is_system = Column(Boolean, default=False, comment="系统字段(id/created_at等)不可删除")
    
    # 默认值与约束
    default_value = Column(Text, nullable=True, comment="默认值")
    max_length = Column(Integer, nullable=True, comment="最大长度(字符串类型)")
    min_value = Column(REAL, nullable=True, comment="最小值(数字类型)")
    max_value = Column(REAL, nullable=True, comment="最大值(数字类型)")
    
    # UI配置
    options = Column(JSON, default=list, comment="选项列表(select/radio/checkbox): [{label,value}]")
    placeholder = Column(String(200), nullable=True, comment="输入提示")
    width = Column(String(20), default="100%", comment="字段宽度")
    
    # 关联配置
    relation_config = Column(JSON, default=dict, comment="关联配置: {target_model, type, display_field, foreign_key}")
    # relation_config 示例:
    # {
    #   "target_model_id": 5,           # 目标数据模型ID
    #   "relation_type": "belongs_to",  # belongs_to/has_many/many_to_many
    #   "foreign_key": "company_id",    # 外键字段
    #   "display_field": "name",        # 显示字段
    #   "on_delete": "set_null"         # CASCADE/SET NULL/RESTRICT
    # }
    
    # 排序
    sort_order = Column(Integer, default=0, comment="排序序号")
    
    # AI生成标记
    ai_suggested = Column(Boolean, default=False, comment="AI推荐的字段")
    ai_confidence = Column(REAL, nullable=True, comment="AI推荐置信度0-1")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DataModelRelation(Base):
    """数据模型关联关系"""
    __tablename__ = "data_model_relations"

    id = Column(Integer, primary_key=True, index=True)
    from_model_id = Column(Integer, ForeignKey("data_models.id"), nullable=False)
    to_model_id = Column(Integer, ForeignKey("data_models.id"), nullable=False)
    
    relation_type = Column(String(30), nullable=False, 
        comment="关联类型: one_to_one/one_to_many/many_to_many")
    
    from_field = Column(String(100), nullable=False, comment="来源表外键字段")
    to_field = Column(String(100), default="id", comment="目标表关联字段")
    
    # 显示配置
    display_field = Column(String(100), nullable=True, comment="关联显示字段")
    reverse_name = Column(String(100), nullable=True, comment="反向关联名称")
    
    # 级联行为
    on_delete = Column(String(20), default="set_null", comment="CASCADE/set_null/restrict")
    on_update = Column(String(20), default="cascade", comment="cascade/restrict")
    
    created_at = Column(DateTime, server_default=func.now())
```

### 2.4 C. AI辅助建模

#### 功能描述

用户用自然语言描述业务需求，AI自动生成数据表结构，支持多表关联。

#### 用户流程

```
┌──────────────────────────────────────────────────────┐
│  🤖 AI数据建模助手                                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  用户: 我需要设计一个客户订单管理系统                  │
│                                                      │
│  AI: 好的！我为你设计了以下数据模型：                  │
│                                                      │
│  📋 客户表 (customers)                               │
│     ├─ id        INTEGER   主键自增                  │
│     ├─ name      TEXT      客户名称 ⭐必填           │
│     ├─ phone     TEXT      联系电话                  │
│     ├─ type      SELECT    客户类型 [潜在/普通/VIP]  │
│     ├─ credit    REAL      信用额度                  │
│     ├─ source    SELECT    来源 [线上/线下/转介绍]   │
│     └─ remark    TEXT      备注                      │
│                                                      │
│  📋 订单表 (orders)                                  │
│     ├─ id           INTEGER  主键自增               │
│     ├─ order_no     TEXT     订单编号 ⭐必填唯一     │
│     ├─ customer_id  INTEGER  客户ID → customers.id  │
│     ├─ total_amount REAL     订单金额               │
│     ├─ status       SELECT   状态 [待确认/已确认/已完成/已取消] │
│     ├─ order_date   DATE     下单日期               │
│     └─ remark       TEXT     备注                    │
│                                                      │
│  🔗 关联关系:                                        │
│     orders.customer_id → customers.id (N:1)          │
│                                                      │
│  [✅采纳全部] [✏️调整后采纳] [🔄重新生成]            │
│                                                      │
│  提示：你可以说"增加一个订单明细表"继续完善           │
└──────────────────────────────────────────────────────┘
```

#### AI建模Prompt设计

```python
AI_MODEL_BUILD_PROMPT = """你是一个数据建模专家。根据用户的需求描述，设计数据表结构。

要求：
1. 输出JSON格式
2. 每个表包含完整的字段定义
3. 字段类型必须是以下之一: INTEGER, REAL, TEXT, BOOLEAN, DATE, DATETIME, JSON
4. UI控件类型必须是以下之一: text, number, date, select, radio, checkbox, switch, upload, image, relation, subform
5. 合理设置必填、唯一、默认值
6. 为select/radio/checkbox类型提供合理的选项
7. 自动识别表间关联关系

输出格式：
{
  "models": [
    {
      "name": "表名(英文小写)",
      "title": "显示名(中文)",
      "description": "描述",
      "fields": [
        {
          "name": "字段名",
          "title": "显示名",
          "db_type": "数据库类型",
          "ui_type": "UI控件类型",
          "is_primary_key": false,
          "is_auto_increment": false,
          "is_required": true,
          "is_unique": false,
          "default_value": null,
          "options": [],
          "comment": "字段注释"
        }
      ]
    }
  ],
  "relations": [
    {
      "from_model": "orders",
      "to_model": "customers",
      "relation_type": "many_to_one",
      "from_field": "customer_id",
      "to_field": "id",
      "display_field": "name"
    }
  ]
}

用户需求：{user_requirement}
"""
```

### 2.5 核心功能：数据表 → 模板转换引擎

这是整个功能最关键的部分——将数据表结构反向生成为 Kflower 模板。

```python
# app/services/model_to_template.py

class ModelToTemplateConverter:
    """数据模型 → Kflower模板 转换器"""
    
    # ============ 数据库类型 → UI控件 映射 ============
    DB_TYPE_TO_UI = {
        # 数值类
        "INTEGER":   "number",
        "INT":       "number",
        "BIGINT":    "number",
        "SMALLINT":  "number",
        "TINYINT":   "switch",       # 0/1 映射为开关
        "REAL":      "number",
        "FLOAT":     "number",
        "DOUBLE":    "number",
        "DECIMAL":   "number",
        "NUMERIC":   "number",
        
        # 字符串类
        "VARCHAR":   "text",
        "CHAR":      "text",
        "TEXT":      "text",          # 长文本映射为textarea
        "LONGTEXT":  "text",
        "MEDIUMTEXT":"text",
        "CLOB":      "text",
        
        # 日期类
        "DATE":      "date",
        "DATETIME":  "datetime",
        "TIMESTAMP": "datetime",
        "TIME":      "text",
        
        # 布尔类
        "BOOLEAN":   "switch",
        "BOOL":      "switch",
        
        # 二进制
        "BLOB":      "upload",
        "BINARY":    "upload",
        
        # JSON
        "JSON":      "subform",
        "JSONB":     "subform",
    }
    
    # 特殊字段名智能识别
    SMART_TYPE_MAP = {
        "email":     "text",       # 附加 format=email
        "phone":     "text",       # 附加 format=phone  
        "mobile":    "text",
        "url":       "text",       # 附加 format=url
        "website":   "text",
        "password":  "text",       # 附加 inputType=password
        "avatar":    "image",
        "image":     "image",
        "photo":     "image",
        "logo":      "image",
        "icon":      "image",
        "file":      "upload",
        "attachment":"upload",
        "amount":    "number",     # 附加 format=money
        "price":     "number",
        "money":     "number",
        "salary":    "number",
        "percent":   "number",     # 附加 format=percent
        "ratio":     "number",
        "status":    "select",
        "type":      "select",
        "category":  "select",
        "level":     "select",
        "gender":    "radio",      # 附加 options=[男,女]
        "sex":       "radio",
        "color":     "text",       # 附加 format=color
        "remark":    "text",       # 附加 multiline=true
        "note":      "text",
        "description":"text",
        "address":   "text",       # 附加 multiline=true
        "tags":      "checkbox",
        "enabled":   "switch",
        "is_vip":    "switch",
        "is_active": "switch",
    }
    
    # 字段名 → 中文标签 自动翻译
    NAME_TO_LABEL = {
        "id": "编号", "name": "名称", "title": "标题", "code": "编码",
        "phone": "电话", "mobile": "手机", "email": "邮箱", "address": "地址",
        "remark": "备注", "note": "备注", "description": "描述",
        "status": "状态", "type": "类型", "category": "分类", "level": "级别",
        "amount": "金额", "price": "价格", "total": "合计", "quantity": "数量",
        "count": "数量", "date": "日期", "time": "时间", "created_at": "创建时间",
        "updated_at": "更新时间", "created_by": "创建人", "updated_by": "更新人",
        "gender": "性别", "age": "年龄", "avatar": "头像", "logo": "Logo",
        "url": "网址", "website": "网站", "password": "密码",
        "customer": "客户", "supplier": "供应商", "order": "订单",
        "product": "产品", "department": "部门", "position": "职位",
        "salary": "薪资", "score": "分数", "weight": "重量",
        "height": "高度", "width": "宽度", "color": "颜色", "size": "尺寸",
        "enabled": "是否启用", "is_vip": "VIP", "is_active": "是否有效",
        "sort_order": "排序", "parent_id": "上级", "path": "路径",
    }
    
    def convert(self, model: DataModel, fields: List[DataModelField], 
                relations: List[DataModelRelation] = None) -> dict:
        """
        将数据模型转换为 Kflower 模板格式
        
        返回值与 TemplateCreate 的 modules 结构完全兼容
        """
        
        # 1. 构建字段列表
        module_fields = []
        for field in sorted(fields, key=lambda f: f.sort_order):
            if field.is_primary_key and field.is_auto_increment:
                continue  # 自增主键不放入表单
            
            field_dict = self._convert_field(field, relations)
            module_fields.append(field_dict)
        
        # 2. 构建模板 modules 结构
        template_data = {
            "name": model.title or model.name,
            "code": f"dm_{model.id}",
            "description": model.description or f"从数据模型 '{model.name}' 生成",
            "category": "data_model",
            "config": {
                "source_type": "data_model",
                "data_model_id": model.id,
                "table_name": model.table_name or f"form_data_dm_{model.id}",
            },
            "modules": [
                {
                    "name": model.name,
                    "label": model.title or model.name,
                    "fields": module_fields
                }
            ]
        }
        
        return template_data
    
    def _convert_field(self, field: DataModelField, relations: List[DataModelRelation] = None) -> dict:
        """转换单个字段"""
        
        # 确定UI控件类型
        ui_type = self._determine_ui_type(field)
        
        # 构建字段定义
        result = {
            "name": field.name,
            "type": ui_type,
            "label": field.title or self._auto_label(field.name),
            "required": field.is_required,
            "readonly": field.is_primary_key,  # 主键只读
            "hidden": False,
        }
        
        # 添加默认值
        if field.default_value is not None:
            result["defaultValue"] = field.default_value
        
        # 添加选项
        if field.options:
            result["options"] = [opt.get("label", opt.get("value", "")) for opt in field.options]
            result["optionsText"] = "\n".join(
                f"{opt.get('label','')}" for opt in field.options
            )
        
        # 添加长度限制
        if field.max_length:
            result["maxLength"] = field.max_length
        
        # 添加数值范围
        if field.min_value is not None:
            result["min"] = field.min_value
        if field.max_value is not None:
            result["max"] = field.max_value
        
        # 添加关联配置
        if field.relation_config:
            result["relation"] = {
                "target_template": field.relation_config.get("target_model_name", ""),
                "display_field": field.relation_config.get("display_field", "name"),
                "link_field": field.name,
            }
            result["type"] = "relation"
        
        return result
    
    def _determine_ui_type(self, field: DataModelField) -> str:
        """智能确定UI控件类型"""
        
        # 1. 如果已有UI类型，直接使用
        if field.ui_type:
            return field.ui_type
        
        # 2. 如果是关联字段
        if field.relation_config:
            return "relation"
        
        # 3. 字段名智能识别
        field_name_lower = field.name.lower()
        for pattern, ui_type in self.SMART_TYPE_MAP.items():
            if pattern in field_name_lower:
                return ui_type
        
        # 4. 按数据库类型映射
        db_type_upper = field.db_type.upper()
        # 处理带参数的类型如 VARCHAR(255)
        base_type = db_type_upper.split('(')[0]
        return self.DB_TYPE_TO_UI.get(base_type, "text")
    
    def _auto_label(self, field_name: str) -> str:
        """自动将字段名转为中文标签"""
        # 1. 精确匹配
        if field_name in self.NAME_TO_LABEL:
            return self.NAME_TO_LABEL[field_name]
        
        # 2. 去除常见后缀后再匹配
        for suffix in ['_id', '_name', '_code', '_type', '_at', '_by']:
            base = field_name.rstrip(suffix)
            if base in self.NAME_TO_LABEL:
                label = self.NAME_TO_LABEL[base]
                if suffix == '_id':
                    return f"{label}ID"
                elif suffix == '_name':
                    return label
                elif suffix == '_code':
                    return f"{label}编码"
                elif suffix == '_type':
                    return f"{label}类型"
                elif suffix == '_at':
                    return f"{label}时间"
                elif suffix == '_by':
                    return f"{label}人"
                return label
        
        # 3. 下划线转空格 + 首字母大写
        return field_name.replace('_', ' ').title()
```

### 2.6 核心功能：Kflower内部表 → 模板复制

一键从 Kflower 已有的数据表复制生成新模板。

```python
# app/services/kflower_table_analyzer.py

class KflowerTableAnalyzer:
    """分析 Kflower 内部已发布的数据表"""
    
    async def list_published_tables(self, db: AsyncSession) -> List[Dict]:
        """列出所有已发布模板的数据表"""
        result = await db.execute(
            select(Template).where(Template.is_published == True)
        )
        templates = result.scalars().all()
        
        tables = []
        for t in templates:
            config = t.config or {}
            if isinstance(config, str):
                config = json.loads(config)
            table_name = config.get('table_name')
            
            if table_name:
                # 查询行数
                count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar()
                
                tables.append({
                    "template_id": t.id,
                    "template_name": t.name,
                    "table_name": table_name,
                    "category": t.category,
                    "row_count": row_count,
                    "created_by": t.created_by,
                    "created_at": t.created_at,
                })
        
        return tables
    
    async def analyze_kflower_table(self, db: AsyncSession, table_name: str) -> TableAnalysis:
        """分析 Kflower 内部数据表结构"""
        # 使用 PRAGMA 获取表结构
        columns = []
        
        # 获取列信息
        col_result = await db.execute(text(f"PRAGMA table_info({table_name})"))
        for row in col_result:
            columns.append(ColumnInfo(
                name=row[1],
                db_type=row[2],
                nullable=not row[3],
                default_value=row[4],
                is_primary_key=bool(row[5]),
                is_unique=False,
                is_auto_increment=False,
                max_length=None,
                comment=None,
                enum_values=[]
            ))
        
        # 获取索引信息（判断唯一性）
        idx_result = await db.execute(text(f"PRAGMA index_list({table_name})"))
        for idx_row in idx_result:
            idx_name = idx_row[1]
            is_unique = bool(idx_row[2])
            if is_unique:
                idx_info = await db.execute(text(f"PRAGMA index_info({idx_name})"))
                for info_row in idx_info:
                    col_name = info_row[2]
                    for col in columns:
                        if col.name == col_name:
                            col.is_unique = True
        
        return TableAnalysis(
            table_name=table_name,
            comment=None,
            columns=columns,
            relations=[],
            indexes=[],
            row_count=0
        )
    
    async def copy_to_template(self, db: AsyncSession, source_table_name: str, 
                                new_template_name: str, current_user_id: int) -> Template:
        """从已有数据表复制为新模板"""
        
        # 1. 分析源表结构
        analysis = await self.analyze_kflower_table(db, source_table_name)
        
        # 2. 查找源模板（获取关联关系等额外信息）
        source_template = None
        t_result = await db.execute(
            select(Template).where(
                Template.config.contains(source_table_name)
            )
        )
        source_template = t_result.scalar_one_or_none()
        
        # 3. 转换为模板字段
        fields = []
        for col in analysis.columns:
            # 跳过系统字段
            if col.name in ('id', 'template_id', 'created_by', 'created_at', 'updated_at'):
                continue
            
            # 尝试从源模板获取字段配置
            field_config = self._find_field_in_source(source_template, col.name)
            
            if field_config:
                # 保留源模板的UI配置
                fields.append(field_config)
            else:
                # 智能推断
                converter = ModelToTemplateConverter()
                field_dict = converter._convert_field(DataModelField(
                    name=col.name,
                    title=converter._auto_label(col.name),
                    db_type=col.db_type,
                    ui_type=None,
                    is_required=not col.nullable,
                    is_unique=col.is_unique,
                    is_primary_key=col.is_primary_key,
                    default_value=col.default_value,
                ))
                fields.append(field_dict)
        
        # 4. 创建新模板
        new_template = Template(
            name=new_template_name,
            code=f"form_",  # 后续更新
            description=f"从数据表 {source_table_name} 复制创建",
            category="data_model",
            config={
                "source_type": "copy_table",
                "source_table": source_table_name,
            },
            modules=[{
                "name": source_table_name.replace("form_data_", ""),
                "label": new_template_name,
                "fields": fields
            }],
            is_published=False,
            is_public=False,
            created_by=current_user_id,
        )
        
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        # 更新code
        new_template.code = f"form_{new_template.id}"
        await db.commit()
        
        return new_template
    
    def _find_field_in_source(self, template: Template, field_name: str) -> Optional[dict]:
        """从源模板中查找字段配置"""
        if not template or not template.modules:
            return None
        
        modules = template.modules
        if isinstance(modules, str):
            modules = json.loads(modules)
        
        for mod in modules:
            for field in mod.get('fields', []):
                if field.get('name') == field_name:
                    return field
        
        return None
```

---

## 三、API设计

### 3.1 新增API端点

```python
# app/api/v1/endpoints/data_model.py

router = APIRouter(prefix="/data-models", tags=["数据建模"])

# ===== 数据库连接管理 =====

@router.post("/connections")
async def create_connection(request: ConnectionCreate, ...):
    """创建数据库连接"""

@router.get("/connections")
async def list_connections(...):
    """列出数据库连接"""

@router.post("/connections/{id}/test")
async def test_connection(id: int, ...):
    """测试数据库连接"""

@router.delete("/connections/{id}")
async def delete_connection(id: int, ...):
    """删除数据库连接"""

# ===== 外部数据库导入 =====

@router.get("/connections/{id}/tables")
async def list_external_tables(id: int, ...):
    """列出外部数据库的表"""

@router.get("/connections/{id}/tables/{table_name}/schema")
async def get_external_table_schema(id: int, table_name: str, ...):
    """获取外部数据表结构"""

@router.get("/connections/{id}/tables/{table_name}/preview")
async def preview_external_table(id: int, table_name: str, ...):
    """预览外部数据表数据(前20条)"""

@router.post("/connections/{id}/import")
async def import_external_tables(id: int, request: ImportRequest, ...):
    """从外部数据库导入表 → 生成数据模型 → 生成模板"""

# ===== 数据模型CRUD =====

@router.post("/models")
async def create_data_model(request: DataModelCreate, ...):
    """创建数据模型(手动)"""

@router.get("/models")
async def list_data_models(...):
    """列出数据模型"""

@router.get("/models/{id}")
async def get_data_model(id: int, ...):
    """获取数据模型详情(含字段和关联)"""

@router.put("/models/{id}")
async def update_data_model(id: int, request: DataModelUpdate, ...):
    """更新数据模型"""

@router.delete("/models/{id}")
async def delete_data_model(id: int, ...):
    """删除数据模型"""

# ===== 字段管理 =====

@router.post("/models/{id}/fields")
async def add_model_field(id: int, request: FieldCreate, ...):
    """添加字段"""

@router.put("/models/{id}/fields/{field_id}")
async def update_model_field(id: int, field_id: int, request: FieldUpdate, ...):
    """更新字段"""

@router.delete("/models/{id}/fields/{field_id}")
async def delete_model_field(id: int, field_id: int, ...):
    """删除字段"""

@router.post("/models/{id}/fields/sort")
async def sort_model_fields(id: int, request: FieldSortRequest, ...):
    """字段排序"""

# ===== 关联关系 =====

@router.post("/models/{id}/relations")
async def add_model_relation(id: int, request: RelationCreate, ...):
    """添加关联关系"""

@router.delete("/models/{id}/relations/{relation_id}")
async def delete_model_relation(id: int, relation_id: int, ...):
    """删除关联关系"""

# ===== 生成操作 =====

@router.post("/models/{id}/create-table")
async def create_physical_table(id: int, ...):
    """创建物理数据表"""

@router.post("/models/{id}/generate-template")
async def generate_template(id: int, ...):
    """从数据模型生成Kflower模板"""

@router.post("/models/{id}/sync-to-table")
async def sync_model_to_table(id: int, ...):
    """同步模型变更到数据表(ALTER TABLE)"""

# ===== Kflower内部表复制 =====

@router.get("/kflower-tables")
async def list_kflower_tables(...):
    """列出Kflower内部已发布的数据表"""

@router.post("/kflower-tables/{table_name}/copy-to-template")
async def copy_kflower_table(table_name: str, request: CopyRequest, ...):
    """从Kflower内部数据表复制为新模板"""

# ===== AI辅助建模 =====

@router.post("/ai/generate")
async def ai_generate_model(request: AIModelRequest, ...):
    """AI生成数据模型"""

@router.post("/ai/suggest-fields")
async def ai_suggest_fields(request: AIFieldSuggestRequest, ...):
    """AI推荐字段(基于表名或描述)"""
```

### 3.2 Pydantic Schemas

```python
# ============ 数据库连接 ============

class ConnectionCreate(BaseModel):
    name: str
    db_type: str = Field(..., pattern="^(mysql|postgresql|sqlite)$")
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict] = None   # 额外配置

class ConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: Optional[str]
    port: Optional[int]
    database: Optional[str]
    is_active: bool
    last_test_result: Optional[str]


# ============ 数据模型 ============

class FieldCreate(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    title: str
    db_type: str = Field(..., pattern=r"^(INTEGER|REAL|TEXT|BOOLEAN|DATE|DATETIME|JSON|BLOB)$")
    ui_type: Optional[str] = None
    is_required: bool = False
    is_unique: bool = False
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    options: Optional[List[Dict]] = None    # [{label, value}]
    relation_config: Optional[Dict] = None

class FieldUpdate(BaseModel):
    title: Optional[str] = None
    ui_type: Optional[str] = None
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    default_value: Optional[str] = None
    options: Optional[List[Dict]] = None
    relation_config: Optional[Dict] = None

class DataModelCreate(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    title: str
    description: Optional[str] = None
    fields: List[FieldCreate] = []

class DataModelUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


# ============ 导入 ============

class ImportRequest(BaseModel):
    table_names: List[str]              # 要导入的表名列表
    generate_template: bool = True      # 是否自动生成模板
    import_data: bool = False           # 是否导入数据(可选)

class CopyRequest(BaseModel):
    new_template_name: str              # 新模板名称
    copy_structure_only: bool = True    # 仅复制结构(不复制数据)


# ============ AI ============

class AIModelRequest(BaseModel):
    requirement: str                    # 用户需求描述
    model_name_hint: Optional[str] = None   # 模型名提示

class AIFieldSuggestRequest(BaseModel):
    model_name: str                     # 表名
    model_description: Optional[str] = None
    existing_fields: List[str] = []     # 已有字段名
```

---

## 四、前端设计

### 4.1 新增路由

```typescript
// 在 src/common/router/index.ts 中新增

{
  path: 'data-modeling',
  name: 'DataModeling',
  component: () => import('../../pc/views/DataModeling.vue'),
  meta: { title: '数据建模' }
},
{
  path: 'data-modeling/designer/:id?',
  name: 'DataModelDesigner',
  component: () => import('../../pc/views/DataModelDesigner.vue'),
  meta: { title: '模型设计', hideInMenu: true }
},
{
  path: 'data-modeling/import',
  name: 'DataModelImport',
  component: () => import('../../pc/views/DataModelImport.vue'),
  meta: { title: '导入数据表', hideInMenu: true }
},
```

### 4.2 页面结构

```
新增文件:
├── pc/views/
│   ├── DataModeling.vue              # 数据建模主页面(列表+入口)
│   ├── DataModelDesigner.vue         # 模型设计器(可视化建表)
│   └── DataModelImport.vue           # 外部数据库导入向导
├── pc/views/my-apps/components/
│   └── DataModelPanel.vue            # 应用内数据模型管理面板
└── common/components/
    ├── DataModelFieldEditor.vue      # 字段编辑器组件
    ├── DataModelRelationEditor.vue   # 关联关系编辑器
    ├── DatabaseConnectionDialog.vue  # 数据库连接配置对话框
    ├── TableSelectPanel.vue          # 数据表选择面板
    └── FieldMappingPreview.vue       # 字段映射预览组件
```

### 4.3 主页面 DataModeling.vue

```
┌──────────────────────────────────────────────────────────────┐
│  数据建模                                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ ✏️ 可视化 │ │ 🔗 导入  │ │ 📋 复制  │ │ 🤖 AI建模│       │
│  │   建表    │ │  外部数据库│ │ Kflower表│ │   助手   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
│  ── 我的数据模型 ──────────────────────────── [搜索...] ──  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📋 客户信息表     customers    12字段  ✅已建表  ✅已生成│ │
│  │    来源: 外部MySQL    更新: 10分钟前                    │ │
│  │    [编辑] [生成模板] [同步] [删除]                      │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 📋 订单管理       orders      8字段   ✅已建表  ✅已生成│ │
│  │    来源: AI生成        更新: 1小时前                    │ │
│  │    [编辑] [生成模板] [同步] [删除]                      │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 📋 产品目录       products    9字段   ⏳草稿    ❌未生成 │ │
│  │    来源: 手动创建      更新: 3小时前                    │ │
│  │    [编辑] [建表+生成] [删除]                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.4 在模板设计入口处集成

在 `Templates.vue` 页面中，模板创建方式增加"数据建模"入口：

```
  ┌──────────────────────────────────────────────────┐
  │  创建模板                                        │
  ├──────────────────────────────────────────────────┤
  │                                                  │
  │  ┌────────┐  ┌────────┐  ┌────────┐            │
  │  │ 🖱️拖拽 │  │ 📄导入 │  │ 🤖AI   │            │
  │  │  设计  │  │  文件  │  │  生成  │            │
  │  └────────┘  └────────┘  └────────┘            │
  │                                                  │
  │  ┌────────┐  ┌────────┐  ← 新增                │
  │  │ 📊数据 │  │ 📋复制 │                         │
  │  │  建模  │  │  表模板│                         │
  │  └────────┘  └────────┘                         │
  └──────────────────────────────────────────────────┘
```

---

## 五、数据库迁移

### 5.1 新增表SQL

```sql
-- 1. 数据库连接配置表
CREATE TABLE IF NOT EXISTS database_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    db_type VARCHAR(20) NOT NULL,
    host VARCHAR(200),
    port INTEGER,
    database VARCHAR(200),
    username VARCHAR(100),
    password_encrypted TEXT,
    config TEXT DEFAULT '{}',
    is_active BOOLEAN DEFAULT 1,
    last_test_at DATETIME,
    last_test_result VARCHAR(20),
    organization_id INTEGER,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 数据模型定义表
CREATE TABLE IF NOT EXISTS data_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    source_type VARCHAR(30) DEFAULT 'manual',
    source_connection_id INTEGER,
    source_table_name VARCHAR(200),
    template_id INTEGER,
    application_id INTEGER,
    is_created BOOLEAN DEFAULT 0,
    table_name VARCHAR(200),
    config TEXT DEFAULT '{}',
    organization_id INTEGER,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_connection_id) REFERENCES database_connections(id),
    FOREIGN KEY (template_id) REFERENCES templates(id),
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

-- 3. 数据模型字段定义表
CREATE TABLE IF NOT EXISTS data_model_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    db_type VARCHAR(50) NOT NULL,
    ui_type VARCHAR(50),
    is_primary_key BOOLEAN DEFAULT 0,
    is_auto_increment BOOLEAN DEFAULT 0,
    is_required BOOLEAN DEFAULT 0,
    is_unique BOOLEAN DEFAULT 0,
    is_indexed BOOLEAN DEFAULT 0,
    is_system BOOLEAN DEFAULT 0,
    default_value TEXT,
    max_length INTEGER,
    min_value REAL,
    max_value REAL,
    options TEXT DEFAULT '[]',
    placeholder VARCHAR(200),
    width VARCHAR(20) DEFAULT '100%',
    relation_config TEXT DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    ai_suggested BOOLEAN DEFAULT 0,
    ai_confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES data_models(id) ON DELETE CASCADE
);

-- 4. 数据模型关联关系表
CREATE TABLE IF NOT EXISTS data_model_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_model_id INTEGER NOT NULL,
    to_model_id INTEGER NOT NULL,
    relation_type VARCHAR(30) NOT NULL,
    from_field VARCHAR(100) NOT NULL,
    to_field VARCHAR(100) DEFAULT 'id',
    display_field VARCHAR(100),
    reverse_name VARCHAR(100),
    on_delete VARCHAR(20) DEFAULT 'set_null',
    on_update VARCHAR(20) DEFAULT 'cascade',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_model_id) REFERENCES data_models(id) ON DELETE CASCADE,
    FOREIGN KEY (to_model_id) REFERENCES data_models(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_data_models_name ON data_models(name);
CREATE INDEX IF NOT EXISTS idx_data_model_fields_model ON data_model_fields(model_id);
CREATE INDEX IF NOT EXISTS idx_data_model_relations_from ON data_model_relations(from_model_id);
CREATE INDEX IF NOT EXISTS idx_data_model_relations_to ON data_model_relations(to_model_id);
CREATE INDEX IF NOT EXISTS idx_database_connections_type ON database_connections(db_type);
```

### 5.2 SQLAlchemy 模型文件

```python
# app/models/data_model.py

"""数据建模模块 - 数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DatabaseConnection(Base):
    """数据库连接配置"""
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    db_type = Column(String(20), nullable=False, comment="mysql/postgresql/sqlite")
    host = Column(String(200), nullable=True)
    port = Column(Integer, nullable=True)
    database = Column(String(200), nullable=True)
    username = Column(String(100), nullable=True)
    password_encrypted = Column(Text, nullable=True)
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    last_test_at = Column(DateTime, nullable=True)
    last_test_result = Column(String(20), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 反向关系
    data_models = relationship("DataModel", back_populates="source_connection")


class DataModel(Base):
    """数据模型定义"""
    __tablename__ = "data_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(30), default="manual", 
        comment="manual/import_db/import_kflower/ai")
    source_connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=True)
    source_table_name = Column(String(200), nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    is_created = Column(Boolean, default=False)
    table_name = Column(String(200), nullable=True)
    config = Column(JSON, default=dict)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    source_connection = relationship("DatabaseConnection", back_populates="data_models")
    fields = relationship("DataModelField", back_populates="model", 
                          cascade="all, delete-orphan", order_by="DataModelField.sort_order")
    relations = relationship("DataModelRelation", back_populates="from_model",
                            cascade="all, delete-orphan",
                            foreign_keys="DataModelRelation.from_model_id")


class DataModelField(Base):
    """数据模型字段"""
    __tablename__ = "data_model_fields"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("data_models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    db_type = Column(String(50), nullable=False)
    ui_type = Column(String(50), nullable=True)
    is_primary_key = Column(Boolean, default=False)
    is_auto_increment = Column(Boolean, default=False)
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)
    default_value = Column(Text, nullable=True)
    max_length = Column(Integer, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    options = Column(JSON, default=list)
    placeholder = Column(String(200), nullable=True)
    width = Column(String(20), default="100%")
    relation_config = Column(JSON, default=dict)
    sort_order = Column(Integer, default=0)
    ai_suggested = Column(Boolean, default=False)
    ai_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    model = relationship("DataModel", back_populates="fields")


class DataModelRelation(Base):
    """数据模型关联关系"""
    __tablename__ = "data_model_relations"

    id = Column(Integer, primary_key=True, index=True)
    from_model_id = Column(Integer, ForeignKey("data_models.id", ondelete="CASCADE"), nullable=False)
    to_model_id = Column(Integer, ForeignKey("data_models.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(30), nullable=False, 
        comment="one_to_one/one_to_many/many_to_many")
    from_field = Column(String(100), nullable=False)
    to_field = Column(String(100), default="id")
    display_field = Column(String(100), nullable=True)
    reverse_name = Column(String(100), nullable=True)
    on_delete = Column(String(20), default="set_null")
    on_update = Column(String(20), default="cascade")
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    from_model = relationship("DataModel", back_populates="relations",
                              foreign_keys=[from_model_id])
    to_model = relationship("DataModel", foreign_keys=[to_model_id])
```

---

## 六、实施计划

### 第一阶段：核心引擎（1周）

```
Day 1-2: 数据库迁移 + SQLAlchemy模型
  - 新增4张表: database_connections, data_models, data_model_fields, data_model_relations
  - 编写模型文件 data_model.py
  - 注册到 __init__.py 确保自动建表

Day 3-4: 数据模型CRUD API
  - 数据模型增删改查
  - 字段管理API
  - 关联关系API

Day 5: 模板转换引擎
  - ModelToTemplateConverter 核心转换逻辑
  - KflowerTableAnalyzer 内部表分析
  - 创建物理表 + 生成模板 联动API
```

### 第二阶段：导入能力（1周）

```
Day 1-2: SQLite分析器
  - SQLiteAnalyzer 完整实现
  - Kflower内部表分析 + 复制为模板

Day 3-4: MySQL/PostgreSQL分析器
  - MySQLAnalyzer 实现
  - PostgreSQLAnalyzer 实现
  - 数据库连接管理

Day 5: AI辅助建模
  - AI Prompt 调优
  - AI生成 → 数据模型 → 模板 完整链路
```

### 第三阶段：前端界面（1周）

```
Day 1-2: 数据建模主页面 + 设计器
  - DataModeling.vue 列表页
  - DataModelDesigner.vue 可视化建表

Day 3-4: 导入向导 + 复制功能
  - DataModelImport.vue 导入向导
  - 数据库连接对话框
  - 字段映射预览

Day 5: 模板设计入口集成
  - Templates.vue 增加"数据建模"入口
  - 模板详情页增加"关联数据模型"展示
  - AI建模对话框
```

---

## 七、与现有系统的兼容性

### 7.1 对现有代码的修改量

| 文件 | 修改内容 | 影响范围 |
|------|---------|---------|
| `app/models/__init__.py` | 新增 import data_model | 仅注册模型 |
| `app/api/v1/__init__.py` | 新增 data_model router | 仅注册路由 |
| `app/schemas/schemas.py` | 新增相关Schema | 纯新增 |
| `main.py` | 无需修改 | 无 |
| `app/core/database.py` | 无需修改 | 无 |
| `app/api/v1/endpoints/templates.py` | 可选：增加 source_type 标记 | 最小改动 |

### 7.2 生成的模板与手动创建的模板完全一致

```python
# 数据建模生成的模板与手动创建的模板结构完全兼容：
{
    "name": "客户信息表",
    "code": "dm_5",
    "modules": [{
        "name": "customers",
        "label": "客户信息表",
        "fields": [
            {"name": "name", "type": "text", "label": "名称", "required": true},
            {"name": "phone", "type": "text", "label": "电话"},
            {"name": "type", "type": "select", "label": "类型", "options": ["潜在客户","普通客户","VIP"]},
            ...
        ]
    }],
    "config": {
        "source_type": "data_model",     # ← 仅此标记区分来源
        "data_model_id": 5,
        "table_name": "form_data_dm_5"
    }
}
```

**所有后续流程（发布、填写、数据管理、工作流绑定）完全不变。**

---

## 八、安全考量

1. **数据库连接密码加密存储** — 使用 AES-256 加密，密钥从环境变量读取
2. **外部数据库只读连接** — 导入时建议使用 readonly 账户
3. **SQL注入防护** — 所有表名/字段名白名单校验（只允许 `[a-zA-Z0-9_]`）
4. **权限控制** — 数据建模操作需要对应权限点：`data_model:create/read/update/delete`
5. **连接测试限流** — 防止暴力探测外部数据库

---

*设计方案版本: v1.0*
*设计时间: 2026-04-28*
*作者: 小克劳尔 & 笑卿*
