"""
补充缺失列迁移脚本 - 补齐模型定义有但数据库缺的列

只补缺失列，不碰多余列，避免对现有数据造成破坏。
运行方式：python _migrate_add_missing_cols.py
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'kflower-backend', 'kflower-data', 'kflower.db')


# 缺失列定义：(table, column, sql_type, default)
MISSING_COLS = [
    # role_permissions - 缺主键和创建时间
    ('role_permissions', 'id', 'INTEGER', None),
    ('role_permissions', 'created_at', 'DATETIME', "'CURRENT_TIMESTAMP'"),

    # workflow_instances - 缺关键字段
    ('workflow_instances', 'finished_at', 'DATETIME', None),
    ('workflow_instances', 'form_data', 'TEXT', None),
    ('workflow_instances', 'initiator_id', 'INTEGER', None),
    ('workflow_instances', 'started_at', 'DATETIME', None),

    # workflow_tasks - 缺多列
    ('workflow_tasks', 'candidate_roles', 'TEXT', "'[]'"),
    ('workflow_tasks', 'candidate_users', 'TEXT', "'[]'"),
    ('workflow_tasks', 'form_data', 'TEXT', None),
    ('workflow_tasks', 'type', 'VARCHAR(50)', "'manual'"),
    ('workflow_tasks', 'updated_at', 'DATETIME', "'CURRENT_TIMESTAMP'"),
    ('workflow_tasks', 'workflow_id', 'INTEGER', None),

    # workflow_logs - 缺多列
    ('workflow_logs', 'details', 'TEXT', None),
    ('workflow_logs', 'task_id', 'INTEGER', None),
    ('workflow_logs', 'user_id', 'INTEGER', None),

    # workflow_node_instances - 缺多列
    ('workflow_node_instances', 'assignee_id', 'INTEGER', None),
    ('workflow_node_instances', 'entered_at', 'DATETIME', None),
    ('workflow_node_instances', 'exited_at', 'DATETIME', None),
    ('workflow_node_instances', 'updated_at', 'DATETIME', "'CURRENT_TIMESTAMP'"),

    # workflow_variable_logs - 缺多列
    ('workflow_variable_logs', 'new_value', 'TEXT', None),
    ('workflow_variable_logs', 'old_value', 'TEXT', None),
    ('workflow_variable_logs', 'task_id', 'INTEGER', None),
    ('workflow_variable_logs', 'variable_name', 'VARCHAR(100)', None),

    # workflow_task_candidates - 缺多列
    ('workflow_task_candidates', 'role_id', 'INTEGER', None),
    ('workflow_task_candidates', 'status', 'VARCHAR(20)', "'pending'"),
    ('workflow_task_candidates', 'updated_at', 'DATETIME', "'CURRENT_TIMESTAMP'"),
    ('workflow_task_candidates', 'user_id', 'INTEGER', None),

    # templates - 缺 version
    ('templates', 'version', 'INTEGER', '1'),

    # workflows - 缺 type
    ('workflows', 'type', 'VARCHAR(50)', "'approval'"),

    # ai_conversations - 缺 title
    ('ai_conversations', 'title', 'VARCHAR(200)', "'新对话'"),

    # audit_logs - 缺 details/resource
    ('audit_logs', 'details', 'TEXT', None),
    ('audit_logs', 'resource', 'VARCHAR(50)', None),

    # agents - 缺 is_active/type
    ('agents', 'is_active', 'INTEGER', '1'),
    ('agents', 'type', 'VARCHAR(50)', "'general'"),

    # applications - 缺 color/is_active/menu_tree/plugins
    ('applications', 'color', 'VARCHAR(20)', "'#409EFF'"),
    ('applications', 'is_active', 'INTEGER', '1'),
    ('applications', 'menu_tree', 'TEXT', "'[]'"),
    ('applications', 'plugins', 'TEXT', "'[]'"),

    # app_menus - 缺多列
    ('app_menus', 'icon', 'VARCHAR(50)', None),
    ('app_menus', 'is_active', 'INTEGER', '1'),
    ('app_menus', 'name', 'VARCHAR(100)', None),
    ('app_menus', 'path', 'VARCHAR(200)', None),
    ('app_menus', 'sort_order', 'INTEGER', '0'),
    ('app_menus', 'type', 'VARCHAR(20)', "'page'"),

    # app_plugins - 缺多列
    ('app_plugins', 'config', 'TEXT', "'{}'"),
    ('app_plugins', 'is_active', 'INTEGER', '1'),
    ('app_plugins', 'plugin_type', 'VARCHAR(50)', None),

    # form_relations - 缺关键列
    ('form_relations', 'child_template_id', 'INTEGER', None),
    ('form_relations', 'parent_template_id', 'INTEGER', None),

    # knowledge_documents - 缺多列
    ('knowledge_documents', 'embedding', 'TEXT', None),
    ('knowledge_documents', 'kb_id', 'INTEGER', None),
    ('knowledge_documents', 'size', 'INTEGER', '0'),

    # knowledge_notes - 缺 kb_id
    ('knowledge_notes', 'kb_id', 'INTEGER', None),

    # knowledge_document_tags - 缺 doc_id
    ('knowledge_document_tags', 'doc_id', 'INTEGER', None),

    # template_instances - 缺 data/title
    ('template_instances', 'data', 'TEXT', "'{}'"),
    ('template_instances', 'title', 'VARCHAR(200)', None),

    # data_permissions - 缺关键列
    ('data_permissions', 'access_level', 'VARCHAR(20)', "'read'"),
    ('data_permissions', 'resource', 'VARCHAR(50)', None),
    ('data_permissions', 'resource_id', 'INTEGER', None),

    # ai_tasks - 缺多列
    ('ai_tasks', 'error', 'TEXT', None),
    ('ai_tasks', 'input', 'TEXT', None),
    ('ai_tasks', 'name', 'VARCHAR(100)', None),
    ('ai_tasks', 'output', 'TEXT', None),
    ('ai_tasks', 'type', 'VARCHAR(50)', "'general'"),
    ('ai_tasks', 'updated_at', 'DATETIME', "'CURRENT_TIMESTAMP'"),

    # ai_usage_logs - 缺多列
    ('ai_usage_logs', 'cost', 'REAL', '0'),
    ('ai_usage_logs', 'input_tokens', 'INTEGER', '0'),
    ('ai_usage_logs', 'model', 'VARCHAR(50)', None),
    ('ai_usage_logs', 'output_tokens', 'INTEGER', '0'),

    # ai_recommendation_cache - 缺多列
    ('ai_recommendation_cache', 'cache_key', 'VARCHAR(200)', None),
    ('ai_recommendation_cache', 'recommendation', 'TEXT', None),
    ('ai_recommendation_cache', 'score', 'REAL', '0'),
]


def get_existing_cols(conn, table):
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}


def migrate():
    conn = sqlite3.connect(DB_PATH)
    added = []
    skipped = []
    failed = []

    for table, col, col_type, default in MISSING_COLS:
        existing = get_existing_cols(conn, table)
        if col in existing:
            skipped.append(f"{table}.{col}")
            continue

        if default:
            sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}"
        else:
            sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"

        try:
            conn.execute(sql)
            added.append(f"{table}.{col}")
            print(f"  + {table}.{col} ({col_type})")
        except Exception as e:
            failed.append(f"{table}.{col}: {e}")
            print(f"  ! {table}.{col} FAILED: {e}")

    conn.commit()
    conn.close()

    print(f"\n完成: 新增 {len(added)}, 跳过 {len(skipped)}, 失败 {len(failed)}")
    if added:
        print("新增:", added)
    if failed:
        print("失败:", failed)


if __name__ == '__main__':
    migrate()
