"""
Agent 模块绑定字段迁移脚本
为 agents 表添加 template_ids, workflow_ids, knowledge_base_ids, plugin_ids, system_prompt, scope 字段

执行方式：cd kflower-backend && python -m migrations.add_agent_bindings
"""
import sqlite3
import os
import sys

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kflower-data", "kflower.db")


def migrate():
    """执行迁移"""
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件不存在: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查 agents 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
    if not cursor.fetchone():
        print("错误：agents 表不存在")
        conn.close()
        sys.exit(1)

    # 检查现有字段
    cursor.execute("PRAGMA table_info(agents)")
    columns = {row[1]: row for row in cursor.fetchall()}

    new_columns = [
        ("template_ids", "TEXT DEFAULT '[]'"),
        ("workflow_ids", "TEXT DEFAULT '[]'"),
        ("knowledge_base_ids", "TEXT DEFAULT '[]'"),
        ("plugin_ids", "TEXT DEFAULT '[]'"),
        ("system_prompt", "TEXT DEFAULT ''"),
        ("scope", "TEXT DEFAULT 'global'"),
    ]

    added = []
    for col_name, col_def in new_columns:
        if col_name not in columns:
            sql = f"ALTER TABLE agents ADD COLUMN {col_name} {col_def}"
            cursor.execute(sql)
            added.append(col_name)
            print(f"  + 添加字段: {col_name}")

    conn.commit()
    conn.close()

    if added:
        print(f"\n迁移完成！已添加 {len(added)} 个字段: {', '.join(added)}")
    else:
        print("\n迁移完成！所有字段已存在，无需修改。")


if __name__ == "__main__":
    migrate()
