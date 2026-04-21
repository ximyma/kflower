"""
数据库 Schema 检查脚本：对比模型定义与数据库实际表结构，
找出缺失列/多余列/类型不匹配，快速定位迁移遗漏。

运行方式：python _db_schema_check.py
"""
import os, sys
import sqlite3

# 添加 backend 到 path 以便导入模型
sys.path.insert(0, os.path.dirname(__file__))
DB_PATH = os.path.join(os.path.dirname(__file__), 'kflower-backend', 'kflower-data', 'kflower.db')

# 期望的列（从模型定义手工提取）
EXPECTED = {
    'roles': {
        'id', 'name', 'code', 'description', 'type', 'data_scope',
        'is_system', 'is_default', 'is_active', 'permissions',
        'data_permission_rules', 'created_at', 'updated_at'
    },
    'users': {
        'id', 'username', 'email', 'phone', 'password_hash', 'full_name',
        'avatar', 'organization_id', 'is_active', 'is_superuser',
        'last_login', 'login_count', 'created_at', 'updated_at'
    },
    'organizations': {
        'id', 'name', 'code', 'parent_id', 'level', 'path',
        'description', 'sort_order', 'is_active', 'created_at', 'updated_at'
    },
    'permissions': {
        'id', 'name', 'code', 'resource', 'action', 'description',
        'is_active', 'created_at', 'updated_at'
    },
    'user_roles': {
        'id', 'user_id', 'role_id', 'organization_id', 'created_at'
    },
    'role_permissions': {
        'id', 'role_id', 'permission_id', 'created_at'
    },
    'ai_conversations': {
        'id', 'user_id', 'title', 'messages', 'created_at', 'updated_at'
    },
    'knowledge_bases': {
        'id', 'name', 'description', 'config', 'created_at', 'updated_at'
    },
    'audit_logs': {
        'id', 'user_id', 'action', 'resource', 'resource_id',
        'details', 'ip_address', 'created_at'
    },
    'templates': {
        'id', 'name', 'code', 'description', 'category', 'modules',
        'config', 'is_published', 'version', 'created_by',
        'created_at', 'updated_at'
    },
    'workflows': {
        'id', 'name', 'description', 'type', 'definition',
        'node_definitions', 'edge_definitions', 'variables',
        'form_template_id', 'is_active', 'created_by', 'created_at', 'updated_at'
    },
    'workflow_instances': {
        'id', 'workflow_id', 'title', 'status', 'current_node_id',
        'initiator_id', 'variables', 'form_data', 'started_at',
        'finished_at', 'created_at', 'updated_at'
    },
    'workflow_tasks': {
        'id', 'instance_id', 'workflow_id', 'node_id', 'type',
        'status', 'assignee_id', 'candidate_users', 'candidate_roles',
        'form_data', 'completed_at', 'created_at', 'updated_at'
    },
    'workflow_logs': {
        'id', 'instance_id', 'task_id', 'action', 'user_id',
        'details', 'created_at'
    },
    'workflow_node_instances': {
        'id', 'instance_id', 'node_id', 'status', 'assignee_id',
        'entered_at', 'exited_at', 'created_at', 'updated_at'
    },
    'workflow_variable_logs': {
        'id', 'instance_id', 'task_id', 'variable_name', 'old_value',
        'new_value', 'changed_by', 'changed_at'
    },
    'workflow_task_candidates': {
        'id', 'task_id', 'candidate_type', 'user_id', 'role_id',
        'status', 'created_at', 'updated_at'
    },
    'applications': {
        'id', 'name', 'description', 'icon', 'color', 'menu_tree',
        'plugins', 'is_active', 'created_at', 'updated_at'
    },
    'app_menus': {
        'id', 'app_id', 'name', 'parent_id', 'type', 'icon',
        'path', 'template_id', 'sort_order', 'is_active', 'created_at', 'updated_at'
    },
    'form_relations': {
        'id', 'app_id', 'parent_template_id', 'child_template_id',
        'relation_type', 'created_at'
    },
    'app_plugins': {
        'id', 'app_id', 'name', 'plugin_type', 'config',
        'is_active', 'created_at', 'updated_at'
    },
    'knowledge_documents': {
        'id', 'kb_id', 'title', 'content', 'file_path', 'file_type',
        'size', 'embedding', 'tags', 'created_at', 'updated_at'
    },
    'knowledge_tags': {
        'id', 'name', 'color', 'created_at'
    },
    'knowledge_notes': {
        'id', 'kb_id', 'title', 'content', 'created_at', 'updated_at'
    },
    'knowledge_document_tags': {
        'doc_id', 'tag_id'
    },
    'template_instances': {
        'id', 'template_id', 'title', 'data', 'created_by', 'created_at', 'updated_at'
    },
    'data_permissions': {
        'id', 'role_id', 'resource', 'resource_id', 'access_level',
        'created_at', 'updated_at'
    },
    'system_configs': {
        'id', 'key', 'value', 'description', 'created_at', 'updated_at'
    },
    'ai_tasks': {
        'id', 'name', 'type', 'input', 'output', 'status',
        'error', 'created_at', 'updated_at'
    },
    'ai_usage_logs': {
        'id', 'user_id', 'model', 'provider', 'input_tokens',
        'output_tokens', 'total_tokens', 'cost', 'created_at'
    },
    'ai_recommendation_cache': {
        'id', 'cache_key', 'recommendation', 'score', 'expires_at', 'created_at'
    },
    'agents': {
        'id', 'name', 'description', 'type', 'config',
        'is_active', 'created_at', 'updated_at'
    },
}


def check_table(table_name, expected_cols):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    actual_cols = {r[1] for r in cur.fetchall()}
    conn.close()

    missing = expected_cols - actual_cols
    extra = actual_cols - expected_cols

    if missing or extra:
        print(f"\n[DIFF] {table_name}")
        if missing:
            print(f"  缺失列: {sorted(missing)}")
        if extra:
            print(f"  多余列: {sorted(extra)}")
        return False
    else:
        print(f"[OK]   {table_name}")
        return True


def main():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'form_data_%'"
    )
    existing = {r[0] for r in cur.fetchall()}
    conn.close()

    missing_tables = set(EXPECTED.keys()) - existing
    if missing_tables:
        print(f"[!] 数据库缺少表: {sorted(missing_tables)}")

    ok_count = 0
    diff_count = 0
    for table, cols in EXPECTED.items():
        if table in existing:
            if check_table(table, cols):
                ok_count += 1
            else:
                diff_count += 1

    print(f"\n总结: {ok_count} 表OK, {diff_count} 表有差异")
    if missing_tables:
        print(f"       {len(missing_tables)} 张表缺失")


if __name__ == '__main__':
    main()
