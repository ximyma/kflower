# KFlower 插件系统迁移计划
## 将 NocoBase 插件架构迁移到 KFlower

---

## 一、现状分析

### 1.1 NocoBase 插件系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      NocoBase Plugin System                  │
├─────────────────────────────────────────────────────────────┤
│  PluginManager (生命周期管理)                                │
│  ├── load()     加载插件                                     │
│  ├── enable()   启用插件                                     │
│  ├── disable()  禁用插件                                     │
│  └── uninstall() 卸载插件                                    │
│                                                              │
│  Plugin Repository (持久化层)                                 │
│  ├── PluginManagerRepository                                 │
│  └── DB: plugins 表                                          │
│                                                              │
│  Plugin 结构                                                 │
│  ├── package.json    元信息                                  │
│  ├── server/         后端代码                                │
│  │   └── plugin.ts   主入口 (Application 扩展)              │
│  ├── client/         前端代码                                │
│  │   └── index.ts    前端入口 (Plugin 扩展)                  │
│  └── dist/           编译产物                                │
│                                                              │
│  插件类型                                                    │
│  ├── 内置插件 (builtIn=true, 不可卸载)                       │
│  ├── NPM 插件 (npm install)                                 │
│  ├── 上传插件 (.tar.gz 包)                                   │
│  └── URL 插件 (远程下载)                                     │
│                                                              │
│  已安装插件示例 (100+个)                                     │
│  ├── plugin-users, plugin-acl (用户权限)                     │
│  ├── plugin-workflow-* (工作流系列)                          │
│  ├── plugin-block-* (区块系列)                               │
│  ├── plugin-field-* (字段类型系列)                           │
│  ├── plugin-collection-* (集合管理)                          │
│  ├── plugin-data-visualization (可视化)                      │
│  └── plugin-ai-* (AI 系列)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 KFlower 现有插件系统

```
┌─────────────────────────────────────────────────────────────┐
│                  KFlower 当前 my_apps 模块                   │
├─────────────────────────────────────────────────────────────┤
│  后端: app/modules/my_apps/                                 │
│  ├── models.py          AppPlugin 模型 (基础)                │
│  ├── plugin_executor.py 脚本执行器 (RestrictedPython)        │
│  ├── endpoints_plugins.py 插件 CRUD API                     │
│  └── service.py         业务逻辑                            │
│                                                              │
│  前端: 散落在各个页面                                         │
│  ├── my-apps/           应用列表                            │
│  └── AppDesigner.vue    应用设计器                          │
│                                                              │
│  功能:                                                       │
│  ├── 插件 CRUD                                                │
│  ├── 代码片段库 (snippets)                                   │
│  ├── 脚本执行 (before_save, after_save, etc.)                │
│  └── App-插件关联                                             │
│                                                              │
│  ⚠️ 缺失核心功能:                                             │
│  ├── ❌ 插件市场/商店                                        │
│  ├── ❌ 插件安装/升级/卸载                                   │
│  ├── ❌ 模板级插件配置 (嵌入模板)                            │
│  ├── ❌ 可视化插件开发工具                                    │
│  └── ❌ 插件市场浏览                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、迁移目标

### 2.1 最终目标
将 NocoBase 的插件架构精髓迁移到 KFlower，让用户可以：
1. **安装插件** - 从本地/NPM/URL 安装扩展
2. **模板绑定** - 将插件绑定到模板，实现模板级功能扩展
3. **应用集成** - 将插件打包进"我的应用"
4. **工具集市场** - 统一的插件市场，支持浏览/搜索/安装

### 2.2 分阶段目标

| 阶段 | 目标 | 核心功能 |
|------|------|---------|
| Phase 1 | 插件系统基础设施 | 数据库模型、生命周期管理、插件加载器 |
| Phase 2 | 模板级插件嵌入 | 将插件配置嵌入模板，表单/列表自动触发 |
| Phase 3 | 我的应用集成 | 插件与"我的应用"绑定，应用发布时打包 |
| Phase 4 | 可视化插件开发 | 拖拽创建插件、代码编辑器、在线调试 |
| Phase 5 | 插件市场 | 插件市场页面、在线安装、NPM 支持 |

---

## 三、详细实施计划

### Phase 1: 插件系统基础设施 ⭐ (预计 4-6 小时)

#### 1.1 数据库模型设计

```python
# app/models/plugin.py

class Plugin(Base):
    """插件元信息"""
    __tablename__ = "plugins"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # 英文标识
    display_name = Column(String(200))                         # 显示名称
    description = Column(Text)                                # 描述
    version = Column(String(50), default="1.0.0")              # 版本
    author = Column(String(100))                              # 作者
    homepage = Column(String(500))                            # 主页
    
    # 安装类型
    install_type = Column(String(20))  # local/npm/url/builtIn
    package_name = Column(String(200)) # NPM 包名 (可选)
    file_path = Column(String(500))    # 本地路径 (可选)
    download_url = Column(String(500)) # 远程 URL (可选)
    
    # 状态
    is_enabled = Column(Boolean, default=True)
    is_built_in = Column(Boolean, default=False)  # 内置不可卸载
    is_installed = Column(Boolean, default=True)
    
    # 配置
    config = Column(JSON, default=dict)  # 插件配置
    
    # 关联
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    template_plugins = relationship("TemplatePlugin", back_populates="plugin")


class PluginVersion(Base):
    """插件版本历史"""
    __tablename__ = "plugin_versions"
    
    id = Column(Integer, primary_key=True)
    plugin_id = Column(Integer, ForeignKey("plugins.id"))
    version = Column(String(50))
    changelog = Column(Text)
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.now)


class PluginHook(Base):
    """插件钩子定义"""
    __tablename__ = "plugin_hooks"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)  # before_form_render, after_data_submit, etc.
    display_name = Column(String(200))
    description = Column(Text)
    params_schema = Column(JSON)  # 钩子参数 JSON Schema
```

```python
# app/models/plugin_binding.py

class TemplatePlugin(Base):
    """模板-插件绑定表"""
    __tablename__ = "template_plugins"
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("templates.id"))
    plugin_id = Column(Integer, ForeignKey("plugins.id"))
    config = Column(JSON, default=dict)  # 该插件在此模板的配置
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    template = relationship("Template", back_populates="plugins")
    plugin = relationship("Plugin", back_populates="template_plugins")


class AppPlugin(Base):
    """应用-插件绑定表 (现有模型扩展)"""
    __tablename__ = "app_plugins"
    
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("applications.id"))
    plugin_id = Column(Integer, ForeignKey("plugins.id"))
    config = Column(JSON, default=dict)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
```

#### 1.2 插件加载器

```python
# app/core/plugin_manager.py

class PluginLoader:
    """插件加载器"""
    
    BUILT_IN_PLUGINS = [
        "kflower-calc",      # 计算字段插件
        "kflower-workflow",  # 审批流插件
        "kflower-notify",    # 通知插件
        "kflower-report",    # 报表插件
        "kflower-ai",        # AI 助手插件
    ]
    
    def __init__(self, app):
        self.app = app
        self.plugins = {}  # name -> PluginInstance
    
    async def load_all(self):
        """加载所有已安装且启用的插件"""
        # 1. 加载内置插件
        for name in self.BUILT_IN_PLUGINS:
            await self.load_plugin(name, is_built_in=True)
        
        # 2. 从数据库加载用户安装的插件
        plugins = await Plugin.get_all(where={"is_installed": True, "is_enabled": True})
        for plugin_data in plugins:
            await self.load_plugin(plugin_data["name"])
    
    async def load_plugin(self, name: str, **options):
        """加载单个插件"""
        # 获取插件元信息
        plugin_meta = await self._get_plugin_meta(name)
        if not plugin_meta:
            raise PluginNotFoundError(f"Plugin {name} not found")
        
        # 创建插件实例
        instance = PluginInstance(plugin_meta, self.app, **options)
        
        # 调用插件的 onLoad 钩子
        await instance.on_load()
        
        # 注册路由
        await instance.register_routes()
        
        # 注册钩子
        await instance.register_hooks()
        
        self.plugins[name] = instance
        return instance
    
    async def enable_plugin(self, name: str):
        """启用插件"""
        if name in self.plugins:
            await self.plugins[name].on_enable()
        await Plugin.update(name=name, {"is_enabled": True})
    
    async def disable_plugin(self, name: str):
        """禁用插件"""
        if name in self.plugins:
            await self.plugins[name].on_disable()
        await Plugin.update(name=name, {"is_enabled": False})


class PluginInstance:
    """插件实例"""
    
    def __init__(self, meta, app, is_built_in=False):
        self.meta = meta
        self.app = app
        self.is_built_in = is_built_in
        self._hooks = {}
    
    async def on_load(self):
        """插件加载时调用"""
        # 执行插件的 setup 逻辑
        pass
    
    async def on_enable(self):
        """插件启用时调用"""
        pass
    
    async def on_disable(self):
        """插件禁用时调用"""
        pass
    
    def register_hook(self, event: str, handler: Callable):
        """注册钩子"""
        self._hooks[event] = handler
    
    async def trigger_hook(self, event: str, context: dict):
        """触发钩子"""
        if event in self._hooks:
            return await self._hooks[event](context)
```

#### 1.3 内置插件实现

```python
# app/plugins/kflower_calc/__init__.py

"""
KFlower 计算字段插件
功能：在表单中添加计算类型字段，支持公式计算
"""

class KFlowerCalcPlugin:
    version = "1.0.0"
    
    def on_load(self, app):
        """注册计算字段类型"""
        app.register_field_type("formula", FormulaField)
        app.register_hook("before_form_render", self.render_formula_fields)
    
    def render_formula_fields(self, context):
        """渲染公式字段（只读显示计算结果）"""
        pass
```

---

### Phase 2: 模板级插件嵌入 ⭐⭐ (预计 3-4 小时)

#### 2.1 模板插件管理界面

```
┌─────────────────────────────────────────────────────────────┐
│  📋 客户管理模板 [编辑]                                       │
├─────────────────────────────────────────────────────────────┤
│  [基本信息] [字段设计] [表单设计] [列表设计] [⚡插件管理] [权限] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚡ 已启用的插件                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🧮 计算字段插件     v1.0.0   [配置] [禁用] [卸载]     │   │
│  │    自动计算订单合计和毛利率                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔔 审批通知插件    v1.0.0   [配置] [禁用] [卸载]     │   │
│  │    订单提交后自动发送通知                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ➕ 安装新插件                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [本地安装] [从 NPM 安装] [从 URL 导入] [浏览市场]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2 插件触发时机

```python
# app/services/template_plugin_service.py

class TemplatePluginService:
    """模板插件服务"""
    
    # 钩子定义
    HOOK_POINTS = {
        "form_load": "表单加载前",
        "form_render": "表单渲染前",
        "form_submit_before": "表单提交前",
        "form_submit_after": "表单提交后",
        "form_delete_before": "删除前",
        "form_delete_after": "删除后",
        "list_load": "列表加载前",
        "list_render": "列表渲染前",
        "field_change": "字段值变更时",
    }
    
    async def trigger_hook(
        self, 
        template_id: int, 
        hook_name: str, 
        context: dict
    ):
        """触发模板绑定的所有插件钩子"""
        # 1. 获取模板绑定的插件
        bindings = await TemplatePlugin.get_all(
            where={
                "template_id": template_id,
                "is_enabled": True
            },
            include=["plugin"]
        )
        
        # 2. 按 sort_order 排序
        bindings.sort(key=lambda x: x.sort_order)
        
        # 3. 依次执行
        results = []
        for binding in bindings:
            plugin = PluginLoader.get(binding.plugin_id)
            if plugin and hook_name in plugin.hooks:
                result = await plugin.hooks[hook_name](context, binding.config)
                results.append({"plugin": plugin.name, "result": result})
        
        return results
```

---

### Phase 3: 我的应用集成 ⭐⭐ (预计 2-3 小时)

#### 3.1 应用插件打包

```
┌─────────────────────────────────────────────────────────────┐
│  🖥️ 客户管理系统 [我的应用]                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📦 应用包信息                                               │
│  ├── 应用名称: 客户管理系统                                   │
│  ├── 版本: v1.0.0                                           │
│  ├── 包含模板: [客户资料] [跟进记录] [合同管理]               │
│  └── 包含插件: [🔔审批通知] [📊数据报表] [🤖AI助手]          │
│                                                             │
│  ⚡ 插件管理                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔔 审批通知插件    [已安装] [移除]                   │   │
│  │    配置: 审批人=部门主管, 通知方式=企业微信            │   │
│  │                                                     │   │
│  │ 📊 数据报表插件    [已安装] [移除]                   │   │
│  │    配置: 报表模板=月度汇总, 刷新频率=每日             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ➕ 添加更多插件 → 跳转到插件市场                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Phase 4: 可视化插件开发 ⭐⭐⭐ (预计 6-8 小时)

#### 4.1 插件可视化编辑器

```
┌─────────────────────────────────────────────────────────────┐
│  🎨 新建插件                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  基础信息                                                    │
│  ├── 插件名称: [my-custom-plugin        ]                   │
│  ├── 显示名称: [我的自定义插件        ]                     │
│  ├── 版本:     [1.0.0                 ]                   │
│  └── 描述:     [                      ]                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⚙️ 插件配置 (JSON Schema)                           │   │
│  │                                                     │   │
│  │ {                                                   │   │
│  │   "type": "object",                                 │   │
│  │   "properties": {                                   │   │
│  │     "webhook_url": {                                │   │
│  │       "type": "string",                             │   │
│  │       "title": "Webhook URL"                        │   │
│  │     },                                              │   │
│  │     "retry_count": {                                │   │
│  │       "type": "number",                             │   │
│  │       "title": "重试次数"                           │   │
│  │       "default": 3                                  │   │
│  │     }                                               │   │
│  │   }                                                 │   │
│  │ }                                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🔌 钩子实现                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ after_save:  [编辑器]                                 │   │
│  │ ───────────────────────────────────────────────────│   │
│  │ 1 │ def after_save(context):                        │   │
│  │ 2 │     data = context.data                        │   │
│  │ 3 │     # 发送 webhook 通知                         │   │
│  │ 4 │     requests.post(config.webhook_url, data)    │   │
│  │ 5 │     return {"status": "ok"}                    │   │
│  │ ───────────────────────────────────────────────────│   │
│  │                              [▶ 测试] [💾 保存]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 4.2 在线调试功能

```python
# 插件测试运行器
class PluginTester:
    """在线测试插件"""
    
    async def test_hook(
        self,
        plugin_id: int,
        hook_name: str,
        mock_data: dict
    ) -> TestResult:
        """执行插件钩子并返回执行结果"""
        
        # 1. 加载插件代码
        plugin = await Plugin.get(plugin_id)
        code = plugin.get_hook_code(hook_name)
        
        # 2. 创建测试上下文
        context = PluginContext(
            data=mock_data,
            old_data={},
            db=self.db,  # 测试数据库
            user_id=1,
            template_id=1,
            event=hook_name,
            app_id=1
        )
        
        # 3. 在沙箱中执行
        result = await PluginSandbox.execute(code, context)
        
        # 4. 返回执行日志和结果
        return TestResult(
            success=result.error is None,
            output=result.logs,
            error=result.error,
            execution_time=result.duration
        )
```

---

### Phase 5: 插件市场 ⭐⭐⭐⭐ (预计 4-6 小时)

#### 5.1 插件市场页面

```
┌─────────────────────────────────────────────────────────────┐
│  🏪 插件市场                           [搜索: ________] [🔍] │
├─────────────────────────────────────────────────────────────┤
│  [全部] [官方] [社区] [AI相关] [报表] [通知] [工作流]         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ 🧮 计算字段   │  │ 📊 数据报表   │  │ 🔔 消息通知   │   │
│  │               │  │               │  │               │   │
│  │ KFlower官方   │  │ KFlower官方   │  │ 社区插件      │   │
│  │ ⭐4.8 (256)   │  │ ⭐4.9 (128)   │  │ ⭐4.5 (64)    │   │
│  │ 免费          │  │ 免费          │  │ 免费          │   │
│  │               │  │               │  │               │   │
│  │ [安装]        │  │ [安装]        │  │ [安装]        │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ 🤖 AI助手     │  │ 📄 PDF生成    │  │ 🔗 API集成    │   │
│  │               │  │               │  │               │   │
│  │ KFlower官方   │  │ 社区插件      │  │ 社区插件      │   │
│  │ ⭐4.7 (512)   │  │ ⭐4.3 (32)    │  │ ⭐4.6 (89)    │   │
│  │ 免费          │  │ ¥29/月        │  │ 免费          │   │
│  │               │  │               │  │               │   │
│  │ [安装]        │  │ [安装]        │  │ [安装]        │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 5.2 市场 API 设计

```python
# app/api/v1/market.py

@router.get("/market/plugins")
async def list_market_plugins(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """获取插件市场列表"""
    # 本地市场数据 (可扩展为远程市场)
    pass

@router.post("/market/plugins/{plugin_id}/install")
async def install_from_market(plugin_id: int):
    """从市场安装插件"""
    # 1. 下载插件包
    # 2. 解压到 plugins 目录
    # 3. 创建 Plugin 记录
    # 4. 执行安装钩子
    pass
```

---

## 四、技术架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           KFlower Plugin System                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        Frontend (Vue3)                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │  │
│  │  │ PluginStore │  │MarketPage   │  │ PluginDesigner     │   │  │
│  │  │ (Pinia)     │  │(插件市场)   │  │ (可视化编辑器)      │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │  │
│  └─────────┼────────────────┼────────────────────┼───────────────┘  │
│            │                │                    │                    │
│            └────────────────┼────────────────────┘                    │
│                             │ REST API                                │
│  ┌──────────────────────────┼────────────────────────────────────┐  │
│  │                     Backend (FastAPI)                          │  │
│  │  ┌────────────────┐  ┌──┴───────────────┐  ┌────────────────┐  │  │
│  │  │ PluginManager  │  │  TemplatePlugin  │  │ MarketService │  │  │
│  │  │ (生命周期)      │  │  Service         │  │ (市场服务)     │  │  │
│  │  │ - load()       │  │  - trigger_hook()│  │ - list()      │  │  │
│  │  │ - enable()     │  │  - bind()        │  │ - install()   │  │  │
│  │  │ - disable()    │  │  - unbind()      │  │ - update()    │  │  │
│  │  └───────┬────────┘  └────────┬─────────┘  └────────────────┘  │  │
│  │          │                    │                                  │  │
│  │  ┌───────┴────────────────────┴────────────────────────────┐   │  │
│  │  │                   PluginSandbox                          │   │  │
│  │  │              (安全的 Python 代码执行环境)                  │   │  │
│  │  │  - RestrictedPython 隔离                                 │   │  │
│  │  │  - 超时控制                                               │   │  │
│  │  │  - 内存限制                                               │   │  │
│  │  └───────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                      Database (SQLite)                         │  │
│  │  ┌────────────┐  ┌────────────────┐  ┌────────────────────┐    │  │
│  │  │  plugins   │  │ template_plugins│  │   app_plugins     │    │  │
│  │  │ (插件元信息) │  │ (模板-插件绑定) │  │  (应用-插件绑定)   │    │  │
│  │  └────────────┘  └────────────────┘  └────────────────────┘    │  │
│  │  ┌────────────────┐  ┌────────────────┐                        │  │
│  │  │ plugin_hooks   │  │ plugin_versions │                        │  │
│  │  │ (钩子定义)     │  │ (版本历史)       │                        │  │
│  │  └────────────────┘  └────────────────┘                        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 五、文件清单

### 新增后端文件

| 文件路径 | 说明 |
|---------|------|
| `app/models/plugin.py` | Plugin, PluginVersion, PluginHook 模型 |
| `app/models/plugin_binding.py` | TemplatePlugin, AppPlugin 模型 |
| `app/core/plugin_manager.py` | 插件管理器 (加载/启用/禁用) |
| `app/core/plugin_sandbox.py` | 插件沙箱 (安全执行) |
| `app/api/v1/plugin_market.py` | 插件市场 API |
| `app/api/v1/plugins.py` | 插件管理 API |
| `app/services/plugin_service.py` | 插件业务逻辑服务 |
| `app/services/template_plugin_service.py` | 模板插件绑定服务 |
| `app/services/market_service.py` | 市场服务 |
| `app/plugins/kflower_calc/` | 内置计算字段插件 |
| `app/plugins/kflower_notify/` | 内置通知插件 |
| `app/plugins/kflower_workflow/` | 内置审批流插件 |
| `app/plugins/kflower_report/` | 内置报表插件 |
| `app/plugins/kflower_ai/` | 内置 AI 助手插件 |

### 新增前端文件

| 文件路径 | 说明 |
|---------|------|
| `src/pc/views/PluginMarket.vue` | 插件市场页面 |
| `src/pc/views/PluginDesigner.vue` | 插件可视化编辑器 |
| `src/pc/views/PluginList.vue` | 我的插件列表 |
| `src/pc/components/PluginCard.vue` | 插件卡片组件 |
| `src/pc/components/PluginConfigDialog.vue` | 插件配置对话框 |
| `src/pc/components/CodeEditor.vue` | 代码编辑器组件 |
| `src/stores/plugin.ts` | 插件状态管理 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `app/models/__init__.py` | 注册新模型 |
| `app/api/v1/api.py` | 注册插件路由 |
| `app/main.py` | 初始化插件管理器 |
| `src/common/router/index.ts` | 添加插件页面路由 |
| `src/common/api/index.ts` | 添加插件 API |
| `src/pc/views/Templates.vue` | 添加插件管理入口 |
| `src/pc/views/AppDesigner.vue` | 添加应用插件配置 |

---

## 六、实施优先级

### P0 - 必须实现
1. ✅ Plugin 模型和数据库表
2. ✅ PluginManager 加载器
3. ✅ 模板插件绑定 API
4. ✅ 模板设计器中的插件管理界面

### P1 - 重要功能
5. 🔧 内置插件实现 (计算/通知)
6. 🔧 插件启用/禁用
7. 🔧 插件配置界面

### P2 - 增强功能
8. 📦 插件安装/卸载
9. 📦 可视化插件编辑器
10. 📦 插件市场页面

---

## 七、风险与注意事项

### 7.1 安全风险
- ⚠️ 用户代码执行必须使用 RestrictedPython 隔离
- ⚠️ 设置代码执行超时 (建议 5 秒)
- ⚠️ 限制内存使用
- ⚠️ 禁止危险操作 (文件 IO, 网络请求需白名单)

### 7.2 兼容性
- ⚠️ 插件升级需要考虑版本兼容
- ⚠️ 模板迁移时插件绑定关系需要一起迁移

### 7.3 性能
- ⚠️ 插件加载应延迟加载，按需启用
- ⚠️ 钩子执行应有熔断机制，避免一个插件拖垮整个系统

---

## 八、参考资源

- NocoBase 插件源码: `E:\myapps\nocobase\node_modules\@nocobase\server\lib\plugin-manager\`
- KFlower 现有插件: `E:\kkflower\kflower-backend\app\modules\my_apps\endpoints_plugins.py`
- RestrictedPython 文档: https://pypi.org/project/RestrictedPython/

---

*文档版本: v1.0*
*创建时间: 2026-04-28*
*预计工期: 15-25 小时 (分 5 个 Phase)*
