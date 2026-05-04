# Kflower 多维表格系统设计方案

> 版本：v1.0
> 日期：2026-05-04
> 状态：草稿（待评审）

---

## 一、项目背景与目标

### 1.1 当前问题分析

| 问题 | 现状 | 影响 |
|------|------|------|
| 缺乏顶层设计 | 矩阵模板是临时添加的功能，没有统一的架构规划 | 导致后续维护困难，bug频发 |
| 数据模型混乱 | 一维表格和矩阵数据混在一起，边界不清晰 | 逻辑复杂，难以扩展 |
| 存储方案不统一 | JSON存储 vs 动态表存储 vs 子表存储，策略不一致 | 查询效率低，数据一致性差 |
| 缺少公式引擎 | 无法实现字段间的计算和聚合 | 功能受限 |
| 缺少表间关联 | 模板之间相互独立，无法建立主从/关联关系 | 无法满足复杂业务场景 |

### 1.2 设计目标

```
┌─────────────────────────────────────────────────────────────────┐
│                        多维表格系统 v2.0                          │
├─────────────────────────────────────────────────────────────────┤
│  ✅ 统一的数据模型        支持一维/二维/多维数据                   │
│  ✅ 灵活的视图展示        表格/矩阵/看板/日历/图表                │
│  ✅ 强大的公式引擎        支持跨字段、跨表计算                     │
│  ✅ 清晰的表间关系        主从表/父子表/关联表                    │
│  ✅ 完善的数据验证        字段级/记录级/跨表级验证                 │
│  ✅ 高效的存储方案        动态建表+智能压缩+索引优化               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 设计原则

1. **渐进式演进**：新架构与现有系统并行，存量模板继续兼容
2. **数据模型优先**：先设计数据结构，再设计界面和流程
3. **配置驱动**：通过元数据配置而非硬编码实现功能
4. **性能导向**：选择合适的存储策略，避免过度设计
5. **可扩展性**：预留插件和自定义字段的扩展点

---

## 二、核心概念与术语

### 2.1 基础概念

```
┌─────────────────────────────────────────────────────────────────┐
│                          多维表格核心概念                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   数据集      │────▶│   视图       │────▶│   界面       │   │
│  │  (Dataset)   │     │  (View)      │     │  (UI)        │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│         │                   │                                     │
│         ▼                   ▼                                     │
│  ┌──────────────┐     ┌──────────────┐                        │
│  │   字段定义    │     │   视图配置    │                        │
│  │  (Fields)    │     │  (ViewConfig) │                        │
│  └──────────────┘     └──────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| 术语 | 定义 | 示例 |
|------|------|------|
| **数据集** | 同一数据源的不同展示形式 | "订单管理"数据集，包含订单列表、统计图表、日历视图 |
| **视图** | 数据的展示方式和交互形式 | 表格视图、矩阵视图、看板视图、日历视图、表单视图 |
| **字段** | 数据集中的一列定义 | 订单号、客户名、金额、日期 |
| **记录** | 数据集中的一行数据 | 订单编号ORD-2024-001的完整信息 |
| **主表** | 包含主键的一方（1端） | 订单主表 |
| **从表** | 包含外键的一方（N端） | 订单明细表 |
| **关联表** | 实现多对多关系的中间表 | 订单与商品的关联 |
| **公式字段** | 根据其他字段计算得出的值 | 总金额 = 单价 × 数量 |

### 2.2 数据维度分类

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据维度分类                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  一维数据（列表型）                                                │
│  ┌─────┬─────┬─────┬─────┐                                     │
│  │ ID  │姓名  │部门  │职位  │  ← 普通表单，每行是一个完整记录    │
│  ├─────┼─────┼─────┼─────┤                                     │
│  │ 1  │张三  │技术部 │工程师 │                                     │
│  │ 2  │李四  │销售部 │经理   │                                     │
│  └─────┴─────┴─────┴─────┘                                     │
│                                                                  │
│  二维数据（矩阵型）                                                │
│  ┌────────┬──────┬──────┬──────┐                               │
│  │        │ Q1   │ Q2   │ Q3   │  ← 矩阵表，行×列交叉定位      │
│  ├────────┼──────┼──────┼──────┤                               │
│  │ 产品A  │ 100  │ 150  │ 200  │                               │
│  │ 产品B  │ 80   │ 90   │ 120  │                               │
│  └────────┴──────┴──────┴──────┘                               │
│                                                                  │
│  多维数据（主从型）                                                │
│  ┌──────────────────────────┐                                   │
│  │ 主表：订单 #001           │ ← 一个订单可有多条明细           │
│  │  ├── 明细1：产品A × 10    │ ← 明细记录通过外键关联          │
│  │  ├── 明细2：产品B × 5     │                                   │
│  │  └── 明细3：产品C × 3     │                                   │
│  └──────────────────────────┘                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、数据模型设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       数据模型分层架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    表现层 (View Layer)                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │表格视图 │ │矩阵视图 │ │看板视图 │ │日历视图 │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    业务逻辑层 (Logic Layer)              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │字段服务  │ │公式引擎 │ │权限服务 │ │验证服务 │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    数据访问层 (Data Layer)               │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │
│  │  │数据集   │ │关联管理  │ │存储管理  │ │索引管理  │        │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   存储层 (Storage Layer)                 │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │  主表数据   │ │  从表数据   │ │  附件存储   │        │   │
│  │  │ (Dynamic)   │ │ (SubTable)  │ │  (Files)   │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心表结构

#### 3.2.1 数据集表 (dataset)

```sql
CREATE TABLE dataset (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(255) NOT NULL COMMENT '数据集名称',
    description     TEXT COMMENT '数据集描述',
    table_name      VARCHAR(255) UNIQUE NOT NULL COMMENT '物理表名',

    -- 数据集元信息
    dimension_type  VARCHAR(50) NOT NULL DEFAULT 'list'
                    COMMENT '维度类型: list-一维, matrix-二维, master-detail-主从',
    row_dimension   JSON COMMENT '行维度定义（用于矩阵）',
    col_dimension   JSON COMMENT '列维度定义（用于矩阵）',

    -- 配置
    config          JSON COMMENT '数据集配置',
    default_view    VARCHAR(50) DEFAULT 'table'
                    COMMENT '默认视图: table,matrix,kanban,calendar,gallery,form',

    -- 权限
    is_public       BOOLEAN DEFAULT FALSE,
    allowed_roles   JSON COMMENT '允许访问的角色列表',

    -- 审计字段
    created_by      INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by      INTEGER,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX idx_dataset_table_name ON dataset(table_name);
CREATE INDEX idx_dataset_dimension ON dataset(dimension_type);
```

#### 3.2.2 字段定义表 (dataset_field)

```sql
CREATE TABLE dataset_field (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id       INTEGER NOT NULL,

    name            VARCHAR(255) NOT NULL COMMENT '字段名（英文标识）',
    label           VARCHAR(255) NOT NULL COMMENT '显示名称',
    description     TEXT COMMENT '字段说明',

    -- 类型体系
    field_category  VARCHAR(50) NOT NULL COMMENT '字段分类',
    field_type      VARCHAR(50) NOT NULL COMMENT '字段类型',
    ui_type         VARCHAR(50) NOT NULL COMMENT 'UI控件类型',

    -- 数据存储
    data_type       VARCHAR(50) NOT NULL COMMENT '数据库类型',
    storage_type    VARCHAR(50) DEFAULT 'column'
                    COMMENT '存储方式: column-独立列, json-JSON嵌套',

    -- 字段配置
    config          JSON COMMENT '字段详细配置',
    options         JSON COMMENT '选项值（用于select/radio/checkbox等）',
    validation      JSON COMMENT '验证规则',

    -- 公式相关（用于计算字段）
    formula         TEXT COMMENT '公式表达式',
    formula_config  JSON COMMENT '公式配置',

    -- 关联相关（用于关联字段）
    relation_type   VARCHAR(50) COMMENT '关联类型: has_many, belongs_to, many_to_many',
    target_dataset  INTEGER COMMENT '目标数据集ID',
    target_field    VARCHAR(255) COMMENT '目标字段',
    junction_table  VARCHAR(255) COMMENT '中间表名（多对多时）',

    -- 显示控制
    is_visible      BOOLEAN DEFAULT TRUE,
    is_editable     BOOLEAN DEFAULT TRUE,
    is_required     BOOLEAN DEFAULT FALSE,
    width           INTEGER COMMENT '列宽',
    order_index     INTEGER DEFAULT 0,

    -- 高级属性
    conditional_display JSON COMMENT '条件显示规则',
    conditional_required JSON COMMENT '条件必填规则',
    computed_when    JSON COMMENT '计算触发时机',

    -- 审计
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (dataset_id) REFERENCES dataset(id) ON DELETE CASCADE,
    FOREIGN KEY (target_dataset) REFERENCES dataset(id) ON DELETE SET NULL,
    UNIQUE(dataset_id, name)
);

CREATE INDEX idx_field_dataset ON dataset_field(dataset_id);
CREATE INDEX idx_field_type ON dataset_field(field_type);
```

#### 3.2.3 视图定义表 (dataset_view)

```sql
CREATE TABLE dataset_view (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id       INTEGER NOT NULL,
    name            VARCHAR(255) NOT NULL COMMENT '视图名称',

    view_type       VARCHAR(50) NOT NULL COMMENT '视图类型',
    config          JSON NOT NULL COMMENT '视图配置（JSON结构）',

    -- 视图内容
    columns         JSON COMMENT '列配置',
    filters         JSON COMMENT '默认筛选条件',
    sort_rules      JSON COMMENT '默认排序规则',
    group_by        JSON COMMENT '默认分组',

    -- 权限
    is_default      BOOLEAN DEFAULT FALSE,
    allowed_roles   JSON,

    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (dataset_id) REFERENCES dataset(id) ON DELETE CASCADE,
    UNIQUE(dataset_id, name)
);

CREATE INDEX idx_view_dataset ON dataset_view(dataset_id);
```

#### 3.2.4 表间关系表 (dataset_relation)

```sql
CREATE TABLE dataset_relation (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(255) NOT NULL COMMENT '关系名称',
    description     TEXT,

    -- 关系两端
    source_dataset  INTEGER NOT NULL COMMENT '源数据集',
    source_field    VARCHAR(255) COMMENT '源字段（为空则用主键）',
    target_dataset  INTEGER NOT NULL COMMENT '目标数据集',
    target_field    VARCHAR(255) COMMENT '目标字段（为空则用主键）',

    -- 关系类型
    relation_type   VARCHAR(50) NOT NULL
                    COMMENT 'one_to_one, one_to_many, many_to_many',

    -- 多对多配置
    junction_table  VARCHAR(255) COMMENT '中间表名',

    -- 关联动作（CASCADE/SET NULL/RESTRICT）
    on_delete       VARCHAR(50) DEFAULT 'CASCADE',
    on_update       VARCHAR(50) DEFAULT 'CASCADE',

    -- 反向关系名称
    reverse_name    VARCHAR(255) COMMENT '反向关系名',

    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_dataset) REFERENCES dataset(id) ON DELETE CASCADE,
    FOREIGN KEY (target_dataset) REFERENCES dataset(id) ON DELETE CASCADE,
    UNIQUE(source_dataset, target_dataset, source_field, target_field)
);
```

#### 3.2.5 记录主表 (dynamic_record)

```sql
-- 通用记录表（用于动态数据集）
CREATE TABLE dynamic_record (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id       INTEGER NOT NULL,
    record_key      VARCHAR(255) UNIQUE NOT NULL COMMENT '记录唯一标识',

    -- 数据内容（JSON格式存储所有字段值）
    data            JSON NOT NULL COMMENT '字段值JSON',

    -- 元数据
    record_status   VARCHAR(50) DEFAULT 'active'
                    COMMENT '记录状态: active, archived, deleted',
    version         INTEGER DEFAULT 1 COMMENT '版本号',
    lock_version    INTEGER DEFAULT 0 COMMENT '乐观锁版本',

    -- 审计
    created_by      INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by      INTEGER,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (dataset_id) REFERENCES dataset(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX idx_record_dataset ON dynamic_record(dataset_id);
CREATE INDEX idx_record_key ON dynamic_record(record_key);
CREATE INDEX idx_record_status ON dynamic_record(record_status);
```

#### 3.2.6 主从关系表 (master_detail_record)

```sql
-- 主从关系表（用于主从表结构）
CREATE TABLE master_detail_relation (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    master_dataset  INTEGER NOT NULL COMMENT '主表数据集',
    detail_dataset  INTEGER NOT NULL COMMENT '从表数据集',
    relation_field  VARCHAR(255) NOT NULL COMMENT '关联字段（从表的外键字段）',

    -- 级联配置
    cascade_create  BOOLEAN DEFAULT TRUE COMMENT '创建主记录时自动创建从记录',
    cascade_delete  VARCHAR(50) DEFAULT 'cascade'
                    COMMENT '删除主记录时: cascade, set_null, restrict',
    min_details     INTEGER DEFAULT 0 COMMENT '最少明细数量',
    max_details     INTEGER COMMENT '最大明细数量',

    FOREIGN KEY (master_dataset) REFERENCES dataset(id) ON DELETE CASCADE,
    FOREIGN KEY (detail_dataset) REFERENCES dataset(id) ON DELETE CASCADE
);

-- 主从表记录（独立存储从表数据）
CREATE TABLE master_detail_record (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_id     INTEGER NOT NULL COMMENT '关联关系ID',
    master_record_id INTEGER NOT NULL COMMENT '主记录ID',

    -- 索引优化字段
    master_key      VARCHAR(255) NOT NULL COMMENT '主记录Key（冗余存储加速查询）',
    order_index     INTEGER DEFAULT 0 COMMENT '显示顺序',

    -- 数据内容
    data            JSON NOT NULL COMMENT '字段值JSON',

    -- 审计
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (relation_id) REFERENCES master_detail_relation(id) ON DELETE CASCADE,
    FOREIGN KEY (master_record_id) REFERENCES dynamic_record(id) ON DELETE CASCADE
);

CREATE INDEX idx_md_relation ON master_detail_record(relation_id);
CREATE INDEX idx_md_master ON master_detail_record(master_key);
```

### 3.3 字段类型体系

```
┌─────────────────────────────────────────────────────────────────┐
│                        字段类型分类体系                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    基础字段类型                            │    │
│  ├──────────────┬────────────────────────────────────────┤    │
│  │ text         │ 单行文本                                │    │
│  │ textarea     │ 多行文本                                │    │
│  │ number       │ 数字（支持精度、小数位、格式化）           │    │
│  │ currency     │ 货币（带货币符号、精度控制）               │    │
│  │ percent      │ 百分比                                  │    │
│  │ date         │ 日期                                    │    │
│  │ datetime     │ 日期时间                                │    │
│  │ time         │ 时间                                    │    │
│  │ boolean      │ 是/否开关                               │    │
│  │ select       │ 单选下拉                                │    │
│  │ multi_select │ 多选下拉                                │    │
│  │ radio        │ 单选按钮                                │    │
│  │ checkbox     │ 多选按钮                                │    │
│  │ rating       │ 评分（星级）                             │    │
│  │ progress     │ 进度条                                  │    │
│  └──────────────┴────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    高级字段类型                            │    │
│  ├──────────────┬────────────────────────────────────────┤    │
│  │ formula      │ 公式计算字段（只读）                       │    │
│  │ auto_number  │ 自动编号                                │    │
│  │ guid         │ 全局唯一标识                             │    │
│  │ user         │ 用户选择（单选）                         │    │
│  │ users        │ 用户选择（多选）                         │    │
│  │ attachment   │ 附件上传                                │    │
│  │ image        │ 图片                                    │    │
│  │ url          │ 网址链接                                │    │
│  │ email        │ 邮箱                                    │    │
│  │ phone        │ 电话                                    │    │
│  │ address      │ 地址（省市区联动）                       │    │
│  └──────────────┴────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    关联字段类型                           │    │
│  ├──────────────┬────────────────────────────────────────┤    │
│  │ relation     │ 关联记录（显示关联字段）                   │    │
│  │ lookup       │ 跨表查找（获取关联记录指定字段）             │    │
│  │ count        │ 计数聚合（统计关联记录数量）                │    │
│  │ sum          │ 求和聚合（汇总关联记录数值字段）            │    │
│  │ average      │ 平均聚合                                 │    │
│  └──────────────┴────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    特殊字段类型                           │    │
│  ├──────────────┬────────────────────────────────────────┤    │
│  │ subform      │ 子表单（嵌入另一个数据集）                 │    │
│  │ signature    │ 手写签名                                 │    │
│  │ barcode      │ 条形码                                  │    │
│  │ qrcode       │ 二维码                                  │    │
│  │ location     │ 地理位置                                │    │
│  └──────────────┴────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 字段配置结构

```typescript
// 字段完整配置示例
interface FieldConfig {
  // ========== 基础配置 ==========
  name: string;                    // 字段标识
  label: string;                   // 显示名称
  description?: string;            // 字段说明
  placeholder?: string;             // 占位文本

  // ========== 类型配置 ==========
  type: FieldType;                 // 字段类型
  uiType: UIType;                  // UI控件类型

  // ========== 数据配置 ==========
  defaultValue?: any;              // 默认值
  options?: Array<{               // 选项配置（select/radio等）
    value: string | number;
    label: string;
    color?: string;
  }>;
  min?: number;                    // 最小值
  max?: number;                    // 最大值
  precision?: number;             // 数值精度
  prefix?: string;                 // 前缀（如货币符号）
  suffix?: string;                 // 后缀

  // ========== 验证规则 ==========
  validation: {
    required?: boolean;            // 是否必填
    minLength?: number;            // 最小长度
    maxLength?: number;            // 最大长度
    pattern?: string;              // 正则表达式
    customRules?: Array<{          // 自定义规则
      name: string;
      message: string;
      handler: string;             // 规则函数
    }>;
  };

  // ========== 显示控制 ==========
  display: {
    width?: number;                // 列宽
    align?: 'left' | 'center' | 'right';
    sortable?: boolean;            // 是否可排序
    filterable?: boolean;          // 是否可筛选
    groupable?: boolean;           // 是否可分组
    frozen?: boolean;              // 是否冻结列
    visible?: boolean;             // 是否显示
  };

  // ========== 权限控制 ==========
  permission: {
    editable?: boolean;            // 是否可编辑
    deletable?: boolean;           // 是否可删除
    rolePermissions?: {           // 角色权限
      [roleId: string]: {
        view: boolean;
        edit: boolean;
      };
    };
  };

  // ========== 条件逻辑 ==========
  conditional: {
    display?: ConditionRule[];     // 条件显示
    required?: ConditionRule[];    // 条件必填
    value?: Array<{                // 条件赋值
      when: ConditionRule;
      then: any;
    }>;
  };

  // ========== 公式配置 ==========
  formula?: {
    expression: string;            // 公式表达式
    dependencies: string[];       // 依赖字段
    aggregate?: {                  // 聚合配置（关联字段）
      targetDataset: number;
      relationField: string;
      aggregateField: string;
      aggregateType: 'sum' | 'avg' | 'count' | 'max' | 'min';
      conditions?: ConditionRule[];
    };
  };

  // ========== 关联配置 ==========
  relation?: {
    type: 'has_one' | 'has_many' | 'belongs_to' | 'many_to_many';
    targetDataset: number;
    targetField: string;
    displayField?: string;         // 显示字段
    filter?: FilterRule[];
  };
}

// 条件规则
interface ConditionRule {
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte'
           | 'contains' | 'not_contains' | 'starts_with' | 'ends_with'
           | 'is_empty' | 'is_not_empty' | 'in' | 'not_in';
  value: any;
  logic?: 'AND' | 'OR';
  children?: ConditionRule[];
}
```

---

## 四、公式引擎设计

### 4.1 公式语法设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        公式语法规范                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 字段引用                                                     │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ {字段名}          引用当前记录的字段值                  │   │
│     │ {明细表.字段名}    引用主从表中的从表字段                │   │
│     │ {关联表.字段名}    引用关联表的字段值                    │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                  │
│  2. 运算符                                                       │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ + - * /       四则运算                                  │   │
│     │ ^             乘方                                     │   │
│     │ %             取模                                     │   │
│     │ &             字符串连接                               │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                  │
│  3. 函数调用                                                     │
│     ┌──────────────────────────────────────────────────────┐   │
│     │ SUMIF({字段}, ">100")        条件求和                  │   │
│     │ IF({状态}="已完成", 1, 0)     条件判断                  │   │
│     │ CONCAT({姓}, {名})           字符串连接               │   │
│     │ VLOOKUP({编号}, {表格}, 2)   查找引用                  │   │
│     └──────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 内置函数库

```typescript
// 数学函数
const MATH_FUNCTIONS = {
  SUM: (...args) => args.reduce((a, b) => a + b, 0),           // 求和
  AVG: (...args) => args.reduce((a, b) => a + b, 0) / args.length, // 平均值
  ROUND: (num, precision) => Math.round(num * 10 ** precision) / 10 ** precision, // 四舍五入
  CEIL: (num) => Math.ceil(num),                               // 向上取整
  FLOOR: (num) => Math.floor(num),                            // 向下取整
  ABS: (num) => Math.abs(num),                                // 绝对值
  MAX: (...args) => Math.max(...args),                         // 最大值
  MIN: (...args) => Math.min(...args),                         // 最小值
  SQRT: (num) => Math.sqrt(num),                              // 平方根
  POWER: (base, exp) => Math.pow(base, exp),                  // 幂运算
  MOD: (num, divisor) => num % divisor,                       // 取模
};

// 文本函数
const TEXT_FUNCTIONS = {
  CONCAT: (...args) => args.join(''),                         // 字符串连接
  LEFT: (str, len) => str.substring(0, len),                  // 左侧取字符
  RIGHT: (str, len) => str.substring(str.length - len),       // 右侧取字符
  MID: (str, start, len) => str.substring(start - 1, start - 1 + len), // 中间取字符
  LEN: (str) => str.length,                                   // 字符串长度
  FIND: (search, str) => str.indexOf(search) + 1,             // 查找位置
  SUBSTITUTE: (str, old, new) => str.replace(old, new),      // 替换
  TRIM: (str) => str.trim(),                                  // 去除空格
  UPPER: (str) => str.toUpperCase(),                         // 转大写
  LOWER: (str) => str.toLowerCase(),                         // 转小写
};

// 日期函数
const DATE_FUNCTIONS = {
  TODAY: () => new Date().toISOString().split('T')[0],       // 今天
  NOW: () => new Date().toISOString(),                        // 现在
  YEAR: (date) => new Date(date).getFullYear(),              // 年份
  MONTH: (date) => new Date(date).getMonth() + 1,            // 月份
  DAY: (date) => new Date(date).getDate(),                   // 日期
  DATEDIF: (start, end, unit) => {                           // 日期差
    const diff = new Date(end) - new Date(start);
    const units = { Y: 365, M: 30, D: 1 };
    return Math.floor(diff / (units[unit] * 86400000));
  },
  DATEADD: (date, num, unit) => {                             // 日期加减
    const d = new Date(date);
    const units = { Y: 'FullYear', M: 'Month', D: 'Date' };
    d[`set${units[unit]}`](d[`get${units[unit]}`]() + num);
    return d.toISOString().split('T')[0];
  },
};

// 逻辑函数
const LOGIC_FUNCTIONS = {
  IF: (condition, trueVal, falseVal) => condition ? trueVal : falseVal, // 条件
  AND: (...args) => args.every(Boolean),                      // 与
  OR: (...args) => args.some(Boolean),                        // 或
  NOT: (val) => !val,                                         // 非
  SWITCH: (expr, ...cases) => {                              // 多条件
    for (let i = 0; i < cases.length; i += 2) {
      if (expr === cases[i]) return cases[i + 1];
    }
    return cases[cases.length - 1];
  },
  ISEMPTY: (val) => val === null || val === '' || val === undefined, // 是否为空
  IFERROR: (expr, fallback) => {                             // 错误处理
    try { return expr; } catch { return fallback; }
  },
};

// 统计函数
const STAT_FUNCTIONS = {
  COUNT: (...args) => args.filter(v => v !== null && v !== '').length, // 计数
  COUNTA: (...args) => args.filter(v => v !== null && v !== undefined).length, // 非空计数
  COUNTIF: (arr, condition) => arr.filter(condition).length,  // 条件计数
  SUMIF: (arr, criteria, sumArr) => {                         // 条件求和
    return arr.reduce((sum, val, i) =>
      condition(val) ? sum + sumArr[i] : sum, 0);
  },
  AVERAGEIF: (arr, criteria, avgArr) => {                     // 条件平均
    const matches = arr.filter(criteria);
    if (matches.length === 0) return 0;
    const sum = matches.reduce((s, _, i) => s + avgArr[i], 0);
    return sum / matches.length;
  },
};
```

### 4.3 公式解析器

```typescript
// 公式解析器实现
class FormulaParser {
  private functions = { ...MATH_FUNCTIONS, ...TEXT_FUNCTIONS,
                         ...DATE_FUNCTIONS, ...LOGIC_FUNCTIONS,
                         ...STAT_FUNCTIONS };

  // 解析公式表达式
  parse(expression: string, context: Record<string, any>): any {
    // 1. 替换字段引用 {字段名} -> context[字段名]
    let formula = expression.replace(/\{([^}]+)\}/g, (match, field) => {
      const value = this.getNestedValue(context, field);
      return this.formatValue(value);
    });

    // 2. 替换函数调用 SUM(...) -> this.functions.SUM(...)
    formula = formula.replace(/(\w+)\s*\(([^)]*)\)/g, (match, fn, args) => {
      if (this.functions[fn]) {
        const parsedArgs = this.parseArguments(args, context);
        return `this.functions.${fn}(${parsedArgs})`;
      }
      return match;
    });

    // 3. 安全执行
    return this.safeEvaluate(formula);
  }

  // 获取嵌套字段值
  private getNestedValue(obj: any, path: string): any {
    const parts = path.split('.');
    let value = obj;
    for (const part of parts) {
      if (value === null || value === undefined) return null;
      value = value[part];
    }
    return value;
  }

  // 安全求值
  private safeEvaluate(formula: string): any {
    try {
      // 白名单验证：只允许数字、运算符、函数调用
      if (!/^[\d\s+\-*/().,']+$/.test(formula)) {
        throw new Error('Invalid formula');
      }
      return new Function(`return (${formula})`).call(this);
    } catch (e) {
      return null;
    }
  }
}
```

---

## 五、视图系统设计

### 5.1 视图类型定义

```
┌─────────────────────────────────────────────────────────────────┐
│                          视图类型体系                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   表格视图   │  │   矩阵视图   │  │   看板视图   │           │
│  │  TableView  │  │ MatrixView  │  │ KanbanView  │           │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤           │
│  │ 行列式数据   │  │ 二维交叉表   │  │ 按状态分组   │           │
│  │ 批量编辑    │  │ 行列维度    │  │ 卡片拖拽    │           │
│  │ 筛选排序    │  │ 数据汇总    │  │ 快速移动    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   日历视图   │  │   画廊视图   │  │   表单视图   │           │
│  │ CalendarView │  │ GalleryView │  │  FormView   │           │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤           │
│  │ 日/周/月    │  │ 图片卡片    │  │ 填写表单    │           │
│  │ 时间轴显示  │  │ 瀑布流布局   │  │ 查看详情    │           │
│  │ 拖拽调整    │  │ 快速预览    │  │ 数据新增    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                             │
│  │   图表视图   │  │   分组视图   │                             │
│  │  ChartView  │  │  GroupView  │                             │
│  ├─────────────┤  ├─────────────┤                             │
│  │ 柱/折/饼图  │  │ 折叠分组    │                             │
│  │ 数据透视    │  │ 分组统计    │                             │
│  │ 仪表盘     │  │ 树形展开    │                             │
│  └─────────────┘  └─────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 视图配置结构

```typescript
// 视图基础配置
interface ViewConfig {
  id: string;
  name: string;
  type: ViewType;
  datasetId: number;

  // 通用配置
  columns?: ColumnConfig[];           // 列配置
  filters?: FilterRule[];            // 筛选条件
  sort?: SortRule[];                  // 排序规则
  groupBy?: GroupRule;               // 分组规则

  // 权限配置
  permissions?: ViewPermissions;

  // 快捷操作
  quickActions?: QuickAction[];
}

// 表格视图配置
interface TableViewConfig extends ViewConfig {
  type: 'table';
  rowHeight?: number;                // 行高
  frozenColumns?: string[];          // 冻结列
  showRowNumber?: boolean;           // 显示行号
  showCheckboxes?: boolean;          // 显示复选框
  virtualScroll?: boolean;           // 虚拟滚动
  editable?: boolean;                // 是否可编辑
}

// 矩阵视图配置
interface MatrixViewConfig extends ViewConfig {
  type: 'matrix';
  rowDimension: {
    field: string;                    // 行维度字段
    options?: Option[];               // 行选项（静态）
    dynamicSource?: string;          // 动态数据源
  };
  colDimension: {
    field: string;                    // 列维度字段
    options?: Option[];               // 列选项
    dynamicSource?: string;
  };
  valueField: string;                 // 值字段
  aggregateType?: 'sum' | 'avg' | 'count' | 'max' | 'min';
  showTotals?: boolean;              // 显示汇总
  cellConfig?: CellStyleConfig;      // 单元格样式
}

// 看板视图配置
interface KanbanViewConfig extends ViewConfig {
  type: 'kanban';
  groupField: string;                 // 分组字段（通常是状态/阶段）
  cardFields?: string[];              // 卡片显示字段
  swimlanes?: {                      // 泳道配置
    field: string;
    direction: 'horizontal' | 'vertical';
  };
  limitPerColumn?: number;           // 每列数量限制
}

// 日历视图配置
interface CalendarViewConfig extends ViewConfig {
  type: 'calendar';
  startDateField: string;             // 开始日期字段
  endDateField?: string;             // 结束日期字段
  titleField: string;                 // 标题字段
  colorField?: string;                // 颜色字段
  defaultView?: 'day' | 'week' | 'month';
  showWeekNumbers?: boolean;
}

// 列配置
interface ColumnConfig {
  field: string;
  label: string;
  width?: number;
  minWidth?: number;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  frozen?: boolean;
  hidden?: boolean;
  renderer?: string;                  // 自定义渲染器
}
```

---

## 六、表间关系设计

### 6.1 关系类型

```
┌─────────────────────────────────────────────────────────────────┐
│                         表间关系类型                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 一对一关系 (One-to-One)                                      │
│     ┌──────────┐         ┌──────────┐                           │
│     │   员工表   │ 1 ─── 1 │  简历表   │                           │
│     │ employee │─────────│  resume  │                           │
│     └──────────┘         └──────────┘                           │
│     每个员工有且仅有一条简历记录                                   │
│                                                                  │
│  2. 一对多关系 (One-to-Many)                                     │
│     ┌──────────┐         ┌──────────┐                           │
│     │   部门表   │ 1 ──┬──│  员工表   │                           │
│     │  dept   │─────┘  │ │ employee │                           │
│     └──────────┘        └└──────────┘                           │
│     一个部门有多个员工，员工属于一个部门                            │
│                                                                  │
│  3. 多对多关系 (Many-to-Many)                                    │
│     ┌──────────┐  ┌──────────────┐  ┌──────────┐               │
│     │   订单表   │──│   订单商品表   │──│   商品表   │               │
│     │  orders  │  │order_products │  │ products │               │
│     └──────────┘  └──────────────┘  └──────────┘               │
│     一个订单包含多个商品，一个商品可被多个订单包含                   │
│                                                                  │
│  4. 自引用关系 (Self-Reference)                                  │
│     ┌──────────┐                                               │
│     │   组织表   │                                               │
│     │  orgs   │                                               │
│     │ parent_id│─────────────────────────────────────────┐     │
│     └──────────┘                                             │     │
│                              树形结构 ◀─────────────────────┘     │
│     上级部门                                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 关系配置示例

```typescript
// 一对多关系示例（部门-员工）
const deptEmployeeRelation: RelationConfig = {
  id: 'rel_dept_employee',
  name: '部门员工关系',
  sourceDataset: 'department',
  sourceField: 'id',
  targetDataset: 'employee',
  targetField: 'dept_id',
  relationType: 'one_to_many',

  // 关联字段配置
  sourceLabel: '部门名称',
  targetLabel: '员工姓名',
  displayTemplate: '{dept_name} 的员工',

  // 级联操作
  cascade: {
    onSourceDelete: 'restrict',    // 删除部门前检查是否有员工
    onSourceUpdate: 'cascade',     // 部门ID变更时同步更新员工
  },

  // 反向关系
  reverseRelation: {
    name: '所属部门',
    type: 'belongs_to',
    label: '部门',
  },
};

// 多对多关系示例（订单-商品）
const orderProductRelation: RelationConfig = {
  id: 'rel_order_product',
  name: '订单商品关系',
  sourceDataset: 'order',
  sourceField: 'id',
  targetDataset: 'product',
  targetField: 'id',
  relationType: 'many_to_many',

  // 中间表配置
  junctionTable: 'order_product',
  junctionFields: {
    sourceFK: 'order_id',
    targetFK: 'product_id',
  },
  // 中间表额外字段
  junctionExtraFields: [
    { name: 'quantity', type: 'number', label: '数量' },
    { name: 'unit_price', type: 'currency', label: '单价' },
    { name: 'discount', type: 'percent', label: '折扣' },
  ],

  // 级联操作
  cascade: {
    onSourceDelete: 'cascade',     // 删除订单时删除关联
    onTargetDelete: 'restrict',    // 删除商品前检查是否有订单
  },
};

// 自引用关系示例（组织架构）
const orgTreeRelation: RelationConfig = {
  id: 'rel_org_tree',
  name: '组织架构',
  sourceDataset: 'organization',
  sourceField: 'id',
  targetDataset: 'organization',
  targetField: 'parent_id',
  relationType: 'one_to_many',

  // 自引用配置
  selfReference: {
    enabled: true,
    rootValue: null,               // 根节点标识值
    levelLimit: 10,                // 最大层级
    rootLabel: '顶级组织',
  },

  // 树形显示配置
  treeDisplay: {
    parentField: 'parent_id',
    orderField: 'order_index',
    levelField: 'level',
    pathField: 'path',             // 路径存储（冗余加速）
  },
};
```

### 6.3 主从表实现

```typescript
// 主从表关系配置
interface MasterDetailConfig {
  id: string;
  name: string;

  // 主表配置
  masterDataset: {
    id: number;
    name: string;
    keyField: string;              // 主表主键
    labelField: string;            // 显示字段
  };

  // 从表配置
  detailDataset: {
    id: number;
    name: string;
    foreignKey: string;             // 从表外键
    labelField: string;
    defaultFields: string[];        // 默认显示字段
  };

  // 约束配置
  constraints: {
    minDetails: number;             // 最少明细数
    maxDetails: number;            // 最大明细数
    allowEmpty: boolean;           // 是否允许空明细
  };

  // UI配置
  uiConfig: {
    layout: 'table' | 'cards' | 'matrix';
    inlineEdit: boolean;           // 是否支持行内编辑
    dragSort: boolean;             // 是否支持拖拽排序
    addButtonText: string;
    deleteConfirm: boolean;
  };
}

// 主从表数据结构
interface MasterDetailData {
  master: {
    id: number;
    key: string;
    data: Record<string, any>;
  };
  details: Array<{
    id: number;
    key: string;
    data: Record<string, any>;
    orderIndex: number;
  }>;
  // 聚合计算结果
  aggregates?: {
    detailCount: number;
    [fieldName: string]: {
      sum?: number;
      avg?: number;
      min?: number;
      max?: number;
    };
  };
}
```

---

## 七、界面设计规范

### 7.1 整体界面结构

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    多维表格容器 (MultiTableContainer)        │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  ┌─────────┐                                             │  │
│  │  │工具栏    │  新建 | 导入 | 导出 | 分享 | 筛选 | 视图切换 │  │
│  │  └─────────┘                                             │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  ┌─────────┐  ┌───────────────────────────────────────┐ │  │
│  │  │侧边栏    │  │              主视图区域                 │ │  │
│  │  │         │  │                                       │ │  │
│  │  │数据集列表 │  │   表格视图 / 矩阵视图 / 看板视图        │ │  │
│  │  │视图切换  │  │   日历视图 / 画廊视图 / 图表视图         │ │  │
│  │  │字段配置  │  │                                       │ │  │
│  │  │权限配置  │  │                                       │ │  │
│  │  │         │  │                                       │ │  │
│  │  └─────────┘  └───────────────────────────────────────┘ │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  ┌─────────┐                                             │  │
│  │  │状态栏    │  共 1256 条记录 | 已选择 3 条 | 当前视图    │  │
│  │  └─────────┘                                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 矩阵视图设计

```
┌─────────────────────────────────────────────────────────────────┐
│ 矩阵编辑界面                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  工具栏：[保存] [取消] [插入行] [插入列] [删除选中] [清空]          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │        │ Q1销售  │ Q2销售  │ Q3销售  │ Q4销售  │ 合计   │    │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼───────┤    │
│  │ 产品A   │  [100]  │  [150]  │  [200]  │  [180]  │  630  │    │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼───────┤    │
│  │ 产品B   │  [80]   │  [90]   │  [120]  │  [110]  │  400  │    │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼───────┤    │
│  │ 产品C   │  [200]  │  [180]  │  [220]  │  [250]  │  850  │    │
│  ├────────┼─────────┼─────────┼─────────┼─────────┼───────┤    │
│  │ 合计    │  380    │  420    │  540    │  540    │ 1880  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  说明：                                                           │
│  - 点击单元格可直接编辑                                           │
│  - 行/列合计自动计算                                              │
│  - 支持 Ctrl+C/V 复制粘贴                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 主从表表单设计

```
┌─────────────────────────────────────────────────────────────────┐
│ 主从表编辑界面                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 主表信息                                                   │   │
│  ├───────────────────────┬─────────────────────────────────┤   │
│  │  订单编号：ORD-001     │  客户：ABC公司                    │   │
│  │  订单日期：2024-01-15  │  负责人：张三                     │   │
│  └───────────────────────┴─────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 订单明细                              [新增明细]           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ # │ 商品名称   │ 规格    │ 单价   │ 数量 │ 小计   │ 操作  │   │
│  ├──┼───────────┼────────┼────────┼──────┼───────┼──────┤   │
│  │ 1 │ 笔记本电脑 │ 16G/512G │ ¥8000 │  2   │ ¥16000 │ 删除  │   │
│  │ 2 │ 无线鼠标  │ 静音版  │ ¥200  │  5   │ ¥1000  │ 删除  │   │
│  │ 3 │ 键盘      │ 机械键盘 │ ¥500  │  3   │ ¥1500  │ 删除  │   │
│  ├──┴───────────┴────────┴────────┴──────┴───────┴──────┤   │
│  │                              合计：¥18500      [添加行] │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [保存] [取消] [删除订单]                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 八、API 接口设计

### 8.1 RESTful API 规范

```typescript
// ========== 数据集管理 ==========
// GET    /api/v1/datasets                    获取数据集列表
// POST   /api/v1/datasets                    创建数据集
// GET    /api/v1/datasets/:id                获取数据集详情
// PUT    /api/v1/datasets/:id                更新数据集
// DELETE /api/v1/datasets/:id                删除数据集
// POST   /api/v1/datasets/:id/duplicate      复制数据集

// ========== 字段管理 ==========
// GET    /api/v1/datasets/:id/fields         获取字段列表
// POST   /api/v1/datasets/:id/fields         添加字段
// PUT    /api/v1/datasets/:id/fields/:fid    更新字段
// DELETE /api/v1/datasets/:id/fields/:fid    删除字段
// PUT    /api/v1/datasets/:id/fields/reorder 重新排序字段

// ========== 视图管理 ==========
// GET    /api/v1/datasets/:id/views          获取视图列表
// POST   /api/v1/datasets/:id/views          创建视图
// PUT    /api/v1/datasets/:id/views/:vid     更新视图
// DELETE /api/v1/datasets/:id/views/:vid    删除视图
// PUT    /api/v1/datasets/:id/views/:vid/set-default 设置默认视图

// ========== 记录操作 ==========
// GET    /api/v1/datasets/:id/records       查询记录列表
// POST   /api/v1/datasets/:id/records       创建记录
// GET    /api/v1/datasets/:id/records/:rid  获取记录详情
// PUT    /api/v1/datasets/:id/records/:rid  更新记录
// DELETE /api/v1/datasets/:id/records/:rid  删除记录
// POST   /api/v1/datasets/:id/records/batch 批量操作

// ========== 主从表操作 ==========
// GET    /api/v1/datasets/:id/master-detail/:rid     获取主从数据
// POST   /api/v1/datasets/:id/master-detail/:rid    创建主从数据
// PUT    /api/v1/datasets/:id/master-detail/:rid    更新主从数据
// DELETE /api/v1/datasets/:id/master-detail/:rid    删除主从数据

// ========== 关联操作 ==========
// GET    /api/v1/datasets/:id/relations/:rid/related 获取关联记录
// POST   /api/v1/datasets/:id/relations/:rid/link     关联记录
// POST   /api/v1/datasets/:id/relations/:rid/unlink   取消关联

// ========== 矩阵数据 ==========
// GET    /api/v1/datasets/:id/matrix         获取矩阵数据
// PUT    /api/v1/datasets/:id/matrix         更新矩阵数据
// GET    /api/v1/datasets/:id/matrix/cell/:row/:col 获取单元格

// ========== 导入导出 ==========
// POST   /api/v1/datasets/:id/import        导入数据
// GET    /api/v1/datasets/:id/export        导出数据
```

### 8.2 请求/响应示例

```typescript
// 创建数据集
POST /api/v1/datasets
Request:
{
  "name": "订单管理",
  "description": "管理客户订单信息",
  "dimensionType": "master_detail",
  "fields": [
    { "name": "order_no", "label": "订单号", "type": "text", "required": true },
    { "name": "customer", "label": "客户", "type": "text", "required": true },
    { "name": "amount", "label": "金额", "type": "currency", "formula": "SUM({明细.小计})" }
  ]
}

Response:
{
  "id": 1,
  "name": "订单管理",
  "tableName": "dataset_1",
  "createdAt": "2024-01-15T10:30:00Z"
}

// 查询记录（支持筛选、排序、分页）
GET /api/v1/datasets/1/records
  ?filters=[{"field":"status","operator":"eq","value":"pending"}]
  &sort=[{"field":"createdAt","order":"desc"}]
  &page=1&pageSize=20
  &include=details,aggregates

Response:
{
  "data": [
    {
      "id": 1,
      "recordKey": "ORD-2024-001",
      "data": {
        "order_no": "ORD-2024-001",
        "customer": "ABC公司",
        "amount": 18500
      },
      "details": [...],
      "aggregates": {
        "detailCount": 3,
        "amount": { "sum": 18500 }
      }
    }
  ],
  "pagination": {
    "total": 156,
    "page": 1,
    "pageSize": 20,
    "totalPages": 8
  }
}

// 主从表数据操作
POST /api/v1/datasets/1/master-detail
Request:
{
  "master": {
    "order_no": "ORD-2024-002",
    "customer": "XYZ公司",
    "order_date": "2024-01-15"
  },
  "details": [
    { "product": "产品A", "quantity": 10, "unit_price": 100 },
    { "product": "产品B", "quantity": 5, "unit_price": 200 }
  ]
}

Response:
{
  "id": 2,
  "recordKey": "ORD-2024-002",
  "master": { "id": 2, ... },
  "details": [
    { "id": 10, "product": "产品A", ... },
    { "id": 11, "product": "产品B", ... }
  ],
  "aggregates": {
    "detailCount": 2,
    "subtotal": { "sum": 2000 }
  }
}
```

---

## 九、技术实现方案

### 9.1 技术栈选择

```
┌─────────────────────────────────────────────────────────────────┐
│                        技术栈选型                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      前端技术栈                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 框架        Vue 3.5+ (Composition API)                   │   │
│  │ 语言        TypeScript 5.x                              │   │
│  │ 构建        Vite 5.x                                    │   │
│  │ UI库        Element Plus 2.x                            │   │
│  │ 状态管理    Pinia 2.x                                   │   │
│  │ 表格组件    Vxe-Table / Luckysheet                      │   │
│  │ 图表        ECharts 5.x                                 │   │
│  │ 拖拽        SortableJS / VueDraggable                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      后端技术栈                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ 框架        FastAPI 0.110+                               │   │
│  │ 语言        Python 3.11+                                │   │
│  │ ORM         SQLAlchemy 2.0                              │   │
│  │ 数据库      SQLite / PostgreSQL                         │   │
│  │ 验证        Pydantic v2                                  │   │
│  │ 任务队列    Celery (可选)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 核心模块实现

```python
# ========== 字段类型注册中心 ==========
class FieldTypeRegistry:
    """字段类型注册中心"""

    _types: Dict[str, FieldTypeHandler] = {}

    @classmethod
    def register(cls, field_type: str, handler: FieldTypeHandler):
        cls._types[field_type] = handler

    @classmethod
    def get_handler(cls, field_type: str) -> FieldTypeHandler:
        handler = cls._types.get(field_type)
        if not handler:
            raise ValueError(f"Unknown field type: {field_type}")
        return handler

    @classmethod
    def get_all_types(cls) -> List[str]:
        return list(cls._types.keys())


# 字段处理器基类
class FieldTypeHandler(ABC):
    def __init__(self, field_def: dict):
        self.field_def = field_def

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult:
        """验证字段值"""
        pass

    @abstractmethod
    def serialize(self, value: Any) -> Any:
        """序列化值用于存储"""
        pass

    @abstractmethod
    def deserialize(self, value: Any) -> Any:
        """反序列化值用于显示"""
        pass

    @abstractmethod
    def get_sql_type(self) -> str:
        """获取SQL类型"""
        pass


# 注册内置字段类型
FieldTypeRegistry.register('text', TextFieldHandler)
FieldTypeRegistry.register('number', NumberFieldHandler)
FieldTypeRegistry.register('currency', CurrencyFieldHandler)
FieldTypeRegistry.register('date', DateFieldHandler)
FieldTypeRegistry.register('select', SelectFieldHandler)
FieldTypeRegistry.register('formula', FormulaFieldHandler)
FieldTypeRegistry.register('relation', RelationFieldHandler)
```

```python
# ========== 公式引擎服务 ==========
class FormulaEngine:
    """公式计算引擎"""

    def __init__(self):
        self.parser = FormulaParser()
        self.functions = {
            'SUM': lambda *args: sum(filter(None, args)),
            'AVG': lambda *args: sum(filter(None, args)) / len(filter(None, args)),
            'IF': lambda cond, t, f: t if cond else f,
            'AND': lambda *args: all(args),
            'OR': lambda *args: any(args),
            'CONCAT': lambda *args: ''.join(str(a) for a in args),
            'ROUND': lambda num, p=0: round(num, p),
            # ... 更多函数
        }

    def calculate(self, formula: str, context: dict) -> Any:
        """计算公式"""
        try:
            # 解析字段引用
            resolved = self._resolve_fields(formula, context)

            # 替换函数调用
            resolved = self._resolve_functions(resolved)

            # 安全执行
            return self._safe_eval(resolved, context)
        except Exception as e:
            return {'#ERROR#': str(e)}

    def _resolve_fields(self, formula: str, context: dict) -> str:
        """解析字段引用 {字段名}"""
        def replacer(match):
            field_path = match.group(1)
            value = self._get_nested_value(context, field_path)
            return f'"{value}"' if isinstance(value, str) else str(value)

        return re.sub(r'\{([^}]+)\}', replacer, formula)
```

### 9.3 存储策略选择

```typescript
// 存储策略决策树
function selectStorageStrategy(dataset: DatasetConfig): StorageStrategy {
  const { dimensionType, fieldCount, expectedRecords, hasAttachments } = dataset;

  // 策略1: JSON列存储（适用于记录数少、字段变化频繁）
  if (expectedRecords < 10000 && fieldCount < 50 && !hasAttachments) {
    return {
      type: 'json_column',
      table: 'dynamic_record',
      dataColumn: 'data',
      indexStrategy: 'field_index',  // 需要频繁查询的字段建立索引
    };
  }

  // 策略2: 动态列存储（适用于记录数多、字段相对固定）
  if (expectedRecords >= 10000 || hasAttachments) {
    return {
      type: 'dynamic_columns',
      table: `data_${dataset.id}`,
      dataColumn: null,
      indexStrategy: 'full_index',
    };
  }

  // 策略3: 混合存储（主表用动态列，从表用JSON）
  if (dimensionType === 'master_detail') {
    return {
      type: 'hybrid',
      masterStrategy: { type: 'dynamic_columns', table: `master_${dataset.id}` },
      detailStrategy: { type: 'json_column', table: `detail_${dataset.id}` },
    };
  }

  // 默认策略
  return { type: 'json_column' };
}
```

---

## 十、实施计划

### 10.1 实施阶段

```
┌─────────────────────────────────────────────────────────────────┐
│                         实施路线图                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: 基础架构（2周）                                        │
│  ├──────────────────────────────────────────────────────────┐  │
│  │ • 数据集表结构设计 & 迁移脚本                              │  │
│  │ • 字段类型注册中心实现                                      │  │
│  │ • RESTful API 基础框架                                     │  │
│  │ • 前端数据集管理页面                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Phase 2: 核心功能（3周）                                        │
│  ├──────────────────────────────────────────────────────────┐  │
│  │ • 字段定义系统 & 字段配置面板                              │  │
│  │ • 表格视图 & 行内编辑                                      │  │
│  │ • 公式引擎基础版（数学/文本/逻辑函数）                      │  │
│  │ • 记录CRUD & 筛选排序                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Phase 3: 高级功能（2周）                                        │
│  ├──────────────────────────────────────────────────────────┐  │
│  │ • 矩阵视图 & 矩阵编辑                                       │  │
│  │ • 主从表结构 & 主从表单                                     │  │
│  │ • 表间关系管理 & 关联查询                                   │  │
│  │ • 导入/导出功能                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Phase 4: 扩展功能（2周）                                        │
│  ├──────────────────────────────────────────────────────────┐  │
│  │ • 看板视图                                                 │  │
│  │ • 日历视图                                                 │  │
│  │ • 图表视图                                                 │  │
│  │ • 高级公式函数 & 跨表计算                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Phase 5: 优化上线（1周）                                        │
│  ├──────────────────────────────────────────────────────────┐  │
│  │ • 性能优化 & 缓存                                          │  │
│  │ • 权限系统完善                                             │  │
│  │ • 文档 & 用户指南                                          │  │
│  │ • 数据迁移 & 灰度上线                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 优先级矩阵

| 功能模块 | 用户价值 | 技术复杂度 | 优先级 | 说明 |
|---------|---------|-----------|--------|------|
| 数据集管理 | ★★★ | ★★☆ | P0 | 核心基础 |
| 字段定义 | ★★★ | ★★☆ | P0 | 核心基础 |
| 表格视图 | ★★★ | ★★☆ | P0 | 核心入口 |
| 记录CRUD | ★★★ | ★☆☆ | P0 | 核心功能 |
| 公式引擎 | ★★★ | ★★★ | P1 | 差异化功能 |
| 矩阵视图 | ★★★ | ★★★ | P1 | 复杂场景 |
| 主从表 | ★★★ | ★★★ | P1 | 复杂场景 |
| 看板视图 | ★★☆ | ★★☆ | P2 | 扩展视图 |
| 日历视图 | ★★☆ | ★★☆ | P2 | 扩展视图 |
| 图表视图 | ★★☆ | ★★☆ | P2 | 扩展视图 |

---

## 十一、风险与应对

| 风险 | 影响 | 概率 | 应对策略 |
|------|------|------|----------|
| 公式引擎解析错误 | 高 | 中 | 分阶段实现，先覆盖常用函数，加强单元测试 |
| 性能问题（大数据量） | 高 | 中 | 设计索引策略，实现虚拟滚动，考虑分页加载 |
| 动态表结构变更 | 中 | 低 | 使用数据库迁移工具，保留数据兼容逻辑 |
| 公式循环依赖 | 中 | 低 | 静态分析依赖图，运行时检测循环 |
| 主从表数据一致性 | 高 | 中 | 使用事务保证，乐观锁并发控制 |

---

## 十二、附录

### 12.1 参考项目

| 项目 | 特点 | GitHub |
|------|------|--------|
| [SmartTable](https://github.com/ldbinac/smart_table) | 对标飞书/Airtable，Vue3+Flask，22种字段类型，6种视图 | ⭐2.3k |
| [NocoBase](https://github.com/nocobase/nocobase) | 插件化架构，企业级扩展，21k Star | ⭐21.3k |
| [Grist](https://github.com/gristlabs/grist-core) | 成熟的开源表格，公式引擎强大 | ⭐11k |
| [Luckysheet](https://github.com/dream-num/Luckysheet) | 类Excel体验，功能全面 | ⭐20k |
| [NocoDB](https://github.com/nocodb/nocodb) | 表格界面数据库 | ⭐60k |

### 12.2 字段类型完整列表

| 类型 | 存储类型 | UI控件 | 说明 |
|------|---------|--------|------|
| text | TEXT | el-input | 单行文本 |
| textarea | TEXT | el-input type=textarea | 多行文本 |
| richtext | TEXT | 富文本编辑器 | 富文本 |
| number | REAL | el-input-number | 数字 |
| currency | REAL | 带货币符号输入 | 货币 |
| percent | REAL | 带%输入 | 百分比 |
| integer | INTEGER | el-input-number | 整数 |
| boolean | INTEGER | el-switch | 开关 |
| date | TEXT | el-date-picker | 日期 |
| datetime | TEXT | el-date-picker | 日期时间 |
| time | TEXT | el-time-picker | 时间 |
| select | TEXT | el-select | 单选 |
| multi_select | TEXT(JSON) | el-select multiple | 多选 |
| radio | TEXT | el-radio-group | 单选按钮 |
| checkbox | TEXT(JSON) | el-checkbox-group | 多选按钮 |
| rating | INTEGER | 星级评分 | 评分 |
| progress | INTEGER | 进度条 | 进度 |
| auto_number | TEXT | 只读 | 自动编号 |
| guid | TEXT | 只读 | 全局唯一ID |
| user | INTEGER | 用户选择器 | 单用户 |
| users | TEXT(JSON) | 用户选择器 | 多用户 |
| attachment | TEXT(JSON) | 文件上传 | 附件 |
| image | TEXT(JSON) | 图片上传 | 图片 |
| url | TEXT | 带链接输入 | 网址 |
| email | TEXT | 邮箱验证输入 | 邮箱 |
| phone | TEXT | 电话输入 | 电话 |
| address | TEXT | 省市区选择 | 地址 |
| formula | - | 只读显示 | 公式计算 |
| relation | INTEGER | 关联选择 | 关联记录 |
| lookup | - | 只读显示 | 跨表查找 |
| count | INTEGER | 只读显示 | 计数聚合 |
| sum | REAL | 只读显示 | 求和聚合 |
| subform | TEXT(JSON) | 子表单列表 | 子表单 |

---

## 十三、决策要点（待确认）

> 以下问题需要在开发前与您确认：

1. **存量模板兼容策略**
   - 现有模板是否需要迁移到新架构？
   - 还是新架构完全独立，存量模板继续使用旧逻辑？

2. **存储策略选择**
   - 优先 JSON 列存储（灵活）还是动态列存储（性能）？
   - 是否需要支持 PostgreSQL 切换？

3. **功能优先级**
   - Phase 1-2 是基础，必须完成
   - Phase 3-4 请确认哪些是必需的，哪些可以后续迭代

4. **公式引擎深度**
   - 是否需要支持跨表关联计算？
   - 是否需要支持脚本自定义函数？

5. **视图类型**
   - 必须实现：表格视图、矩阵视图
   - 请确认：看板视图、日历视图、图表视图是否需要

---

**文档版本历史**
| 版本 | 日期 | 修改内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-05-04 | 初始版本 | AI Assistant |
