"""
迁移脚本：为工作流模块添加升级字段和新表（按照 dd4chat.txt 方案）
执行方式：python -m migrations.add_workflow_upgrade_fields
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def migrate():
    from app.core.database import engine
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        print("开始工作流模块升级迁移...")
        
        # 1. 为 workflows 表添加新字段
        fields_to_add = [
            ("node_definitions", "JSON", "[]"),
            ("edge_definitions", "JSON", "[]"),
            ("variables", "JSON", "{}"),
            ("form_template_id", "INTEGER", "NULL")
        ]
        
        for field_name, field_type, default_value in fields_to_add:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_name = 'workflows' AND column_name = '{field_name}'"
            ))
            if result.fetchone() is None:
                await conn.execute(text(
                    f"ALTER TABLE workflows ADD COLUMN {field_name} {field_type}"
                ))
                print(f"✓ 添加 {field_name} 字段到 workflows 表")
            else:
                print(f"- {field_name} 字段已存在，跳过")
        
        # 2. 为 workflow_instances 表添加新字段
        instance_fields = [
            ("variables", "JSON", "{}"),
            ("parent_instance_id", "INTEGER", "NULL"),
            ("form_data_id", "INTEGER", "NULL")
        ]
        
        for field_name, field_type, default_value in instance_fields:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_name = 'workflow_instances' AND column_name = '{field_name}'"
            ))
            if result.fetchone() is None:
                await conn.execute(text(
                    f"ALTER TABLE workflow_instances ADD COLUMN {field_name} {field_type}"
                ))
                print(f"✓ 添加 {field_name} 字段到 workflow_instances 表")
            else:
                print(f"- {field_name} 字段已存在，跳过")
        
        # 3. 为 workflow_tasks 表添加新字段
        task_fields = [
            ("node_config", "JSON", "{}"),
            ("due_date", "DATETIME", "NULL"),
            ("priority", "INTEGER", "0"),
            ("variables", "JSON", "{}")
        ]
        
        for field_name, field_type, default_value in task_fields:
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_name = 'workflow_tasks' AND column_name = '{field_name}'"
            ))
            if result.fetchone() is None:
                await conn.execute(text(
                    f"ALTER TABLE workflow_tasks ADD COLUMN {field_name} {field_type}"
                ))
                print(f"✓ 添加 {field_name} 字段到 workflow_tasks 表")
            else:
                print(f"- {field_name} 字段已存在，跳过")
        
        # 4. 创建 workflow_node_instances 表
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_node_instances'"
        ))
        if result.fetchone() is None:
            await conn.execute(text("""
                CREATE TABLE workflow_node_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id INTEGER NOT NULL,
                    node_id VARCHAR(100) NOT NULL,
                    node_name VARCHAR(200),
                    node_type VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending',
                    start_time DATETIME,
                    end_time DATETIME,
                    variables JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instance_id) REFERENCES workflow_instances (id)
                )
            """))
            print("✓ 创建 workflow_node_instances 表")
        else:
            print("- workflow_node_instances 表已存在，跳过")
        
        # 5. 创建 workflow_variable_logs 表
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_variable_logs'"
        ))
        if result.fetchone() is None:
            await conn.execute(text("""
                CREATE TABLE workflow_variable_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id INTEGER,
                    var_name VARCHAR(100) NOT NULL,
                    var_value TEXT,
                    changed_by INTEGER,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (instance_id) REFERENCES workflow_instances (id),
                    FOREIGN KEY (changed_by) REFERENCES users (id)
                )
            """))
            print("✓ 创建 workflow_variable_logs 表")
        else:
            print("- workflow_variable_logs 表已存在，跳过")
        
        # 6. 创建 workflow_task_candidates 表
        result = await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_task_candidates'"
        ))
        if result.fetchone() is None:
            await conn.execute(text("""
                CREATE TABLE workflow_task_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    candidate_type VARCHAR(20) NOT NULL,
                    candidate_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES workflow_tasks (id)
                )
            """))
            print("✓ 创建 workflow_task_candidates 表")
        else:
            print("- workflow_task_candidates 表已存在，跳过")
        
        print("\n工作流模块升级迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())