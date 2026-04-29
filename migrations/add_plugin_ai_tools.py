"""
迁移脚本：创建插件系统表 + 注册 AI 工具插件

运行方式：
  cd e:\kkflower\kflower-backend
  python ..\migrations\add_plugin_ai_tools.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\kflower-backend")

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "kflower-backend", "kflower.db"
)
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

# ─────────────────────────────────────────────────────────────────────────────
#  确保表存在
# ─────────────────────────────────────────────────────────────────────────────

def ensure_tables():
    insp = inspect(engine)
    existing = set(insp.get_table_names())

    with engine.connect() as conn:
        if "plugins" not in existing:
            conn.execute(text("""
                CREATE TABLE plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    version VARCHAR(50) DEFAULT '1.0.0',
                    author VARCHAR(100),
                    homepage VARCHAR(500),
                    icon VARCHAR(50) DEFAULT 'puzzle-piece',
                    category VARCHAR(50) DEFAULT 'custom',
                    install_type VARCHAR(20) DEFAULT 'builtin',
                    package_name VARCHAR(200),
                    file_path VARCHAR(500),
                    download_url VARCHAR(500),
                    is_enabled BOOLEAN DEFAULT 1,
                    is_built_in BOOLEAN DEFAULT 0,
                    is_installed BOOLEAN DEFAULT 1,
                    config JSON DEFAULT '{}',
                    hook_code JSON DEFAULT '{}',
                    install_count INTEGER DEFAULT 0,
                    last_install_at DATETIME,
                    organization_id INTEGER,
                    created_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("[OK] 创建 plugins 表")
        else:
            print("[已存在] plugins 表")

        if "plugin_versions" not in existing:
            conn.execute(text("""
                CREATE TABLE plugin_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_id INTEGER NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
                    version VARCHAR(50) NOT NULL,
                    changelog TEXT,
                    file_path VARCHAR(500),
                    size_kb INTEGER,
                    download_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("[OK] 创建 plugin_versions 表")
        else:
            print("[已存在] plugin_versions 表")

        if "plugin_hooks" not in existing:
            conn.execute(text("""
                CREATE TABLE plugin_hooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    event VARCHAR(50) NOT NULL,
                    params_schema JSON DEFAULT '{}',
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("[OK] 创建 plugin_hooks 表")
        else:
            print("[已存在] plugin_hooks 表")

        if "template_plugins" not in existing:
            conn.execute(text("""
                CREATE TABLE template_plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
                    plugin_id INTEGER NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
                    config JSON DEFAULT '{}',
                    is_enabled BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("[OK] 创建 template_plugins 表")
        else:
            print("[已存在] template_plugins 表")

        if "app_plugins" not in existing:
            conn.execute(text("""
                CREATE TABLE app_plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
                    plugin_id INTEGER NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
                    config JSON DEFAULT '{}',
                    is_enabled BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("[OK] 创建 app_plugins 表")
        else:
            print("[已存在] app_plugins 表")


# ─────────────────────────────────────────────────────────────────────────────
#  注册 AI 工具插件
# ─────────────────────────────────────────────────────────────────────────────

AI_TOOL_PLUGINS = [
    ("tool-create-template", "创建模板工具", "AI 工具：创建业务模板", "ai_tool",
     '{"tool_name": "create_template", "tool_type": "template"}', "document-add"),
    ("tool-list-templates", "查询模板工具", "AI 工具：列出所有模板", "ai_tool",
     '{"tool_name": "list_templates", "tool_type": "template"}', "document"),
    ("tool-create-workflow", "创建工作流工具", "AI 工具：创建工作流程", "ai_tool",
     '{"tool_name": "create_workflow", "tool_type": "workflow"}', "connection"),
    ("tool-execute-workflow", "执行工作流工具", "AI 工具：执行工作流程", "ai_tool",
     '{"tool_name": "execute_workflow", "tool_type": "workflow"}', "video-play"),
    ("tool-query-data", "查询数据工具", "AI 工具：查询业务数据", "ai_tool",
     '{"tool_name": "query_data", "tool_type": "query"}', "search"),
    ("tool-get-statistics", "统计分析工具", "AI 工具：获取统计数据", "ai_tool",
     '{"tool_name": "get_statistics", "tool_type": "analytics"}', "data-analysis"),
    ("tool-send-notification", "发送通知工具", "AI 工具：发送系统通知", "ai_tool",
     '{"tool_name": "send_notification", "tool_type": "notification"}', "bell"),
    ("tool-convert-document", "文档转换工具", "AI 工具：文档格式转换", "ai_tool",
     '{"tool_name": "convert_document", "tool_type": "file"}', "copy-document"),
    ("tool-extract-excel-json", "Excel提取工具", "AI 工具：Excel/CSV 提取为 JSON", "ai_tool",
     '{"tool_name": "extract_excel_json", "tool_type": "file"}', "grid"),
    ("tool-auto-convert-upload", "自动转换上传工具", "AI 工具：旧格式文档自动转换", "ai_tool",
     '{"tool_name": "auto_convert_upload", "tool_type": "file"}', "upload"),
]

BUILTIN_PLUGINS = [
    ("kflower-calc", "计算字段", "在表单中添加计算字段，支持公式", "builtin", "{}", "calculator"),
    ("kflower-notify", "通知提醒", "支持企业微信、邮件、站内信通知", "builtin", "{}", "bell"),
    ("kflower-workflow", "审批流程", "为表单添加审批流程", "builtin", "{}", "set-up"),
    ("kflower-report", "数据报表", "生成图表报表，支持导出", "builtin", "{}", "data-analysis"),
    ("kflower-ai", "AI 助手", "接入大语言模型，支持智能填表", "builtin",
     '{"model": "qwen-turbo", "max_tokens": 2000}', "magic-stick"),
]


def register_plugins():
    db = Session()
    try:
        all_plugins = BUILTIN_PLUGINS + AI_TOOL_PLUGINS
        inserted = 0
        skipped = 0

        for row in all_plugins:
            name, display_name, description, category, config, icon = row
            existing = db.execute(
                text("SELECT id FROM plugins WHERE name = :name"),
                {"name": name}
            ).fetchone()

            if not existing:
                db.execute(text("""
                    INSERT INTO plugins
                        (name, display_name, description, category, install_type,
                         config, hook_code, is_enabled, is_built_in, is_installed, icon, version, author)
                    VALUES
                        (:name, :display_name, :description, :category, 'builtin',
                         :config, '{}', 1, 1, 1, :icon, '1.0.0', 'KFlower')
                """), {
                    "name": name,
                    "display_name": display_name,
                    "description": description,
                    "category": category,
                    "config": config,
                    "icon": icon,
                })
                inserted += 1
            else:
                skipped += 1

        db.commit()
        print(f"[OK] 插件注册完成：新增 {inserted} 个，跳过 {skipped} 个")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 注册插件失败: {e}")
        raise
    finally:
        db.close()


def seed_builtin_hooks():
    hooks = [
        ("before_form_render", "表单渲染前", "form.render"),
        ("after_form_submit", "表单提交后", "form.submit"),
        ("before_form_submit", "表单提交前", "form.submit"),
        ("after_data_delete", "数据删除后", "data.delete"),
        ("on_list_load", "列表加载时", "list.load"),
        ("on_field_change", "字段值变更时", "field.change"),
        ("on_cron_schedule", "定时任务", "cron.schedule"),
        ("on_api_called", "API调用时", "api.called"),
    ]
    db = Session()
    try:
        inserted = 0
        for name, display_name, event in hooks:
            existing = db.execute(
                text("SELECT id FROM plugin_hooks WHERE name = :name"),
                {"name": name}
            ).fetchone()
            if not existing:
                db.execute(text("""
                    INSERT INTO plugin_hooks (name, display_name, event, is_active)
                    VALUES (:name, :display_name, :event, 1)
                """), {"name": name, "display_name": display_name, "event": event})
                inserted += 1
        db.commit()
        print(f"[OK] 内置钩子注册完成：新增 {inserted} 个")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"数据库路径: {DB_PATH}")
    print("=" * 50)
    ensure_tables()
    seed_builtin_hooks()
    register_plugins()
    print("=" * 50)
    print("迁移完成！")
