"""
迁移脚本：为工作流模块添加升级字段和新表（按照 dd4chat.txt 方案）
执行方式：python -m migrations.add_workflow_upgrade_fields
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, "kflower-backend"))


async def migrate():
    from app.core.database import engine
    from sqlalchemy import text
    import traceback
    
    async with engine.begin() as conn:
        print("开始工作流模块升级迁移...")
        
        # 辅助函数：安全添加字段
        async def safe_add_column(table_name, column_name, column_type):
            try:
                # SQLite兼容的字段检查方式
                # 尝试直接添加字段，如果失败则说明字段已存在
                await conn.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                ))
                print(f"✓ 添加 {column_name} 字段到 {table_name} 表")
                return True
            except Exception as e:
                error_msg = str(e).lower()
                # 检查是否是因为字段已存在的错误
                if "duplicate column" in error_msg or "already exists" in error_msg or "sqlite error" in error_msg:
                    print(f"- {column_name} 字段已存在，跳过")
                    return False
                else:
                    # 其他错误，打印并继续
                    print(f"! 添加 {column_name} 字段时出错: {str(e)[:100]}")
                    return False
        
        # 1. 为 workflows 表添加新字段
        fields_to_add = [
            ("node_definitions", "JSON"),
            ("edge_definitions", "JSON"),
            ("variables", "JSON"),
            ("form_template_id", "INTEGER")
        ]
        
        for field_name, field_type in fields_to_add:
            await safe_add_column("workflows", field_name, field_type)
        
        # 2. 为 workflow_instances 表添加新字段
        instance_fields = [
            ("variables", "JSON"),
            ("parent_instance_id", "INTEGER"),
            ("form_data_id", "INTEGER")
        ]
        
        for field_name, field_type in instance_fields:
            await safe_add_column("workflow_instances", field_name, field_type)
        
        # 3. 为 workflow_tasks 表添加新字段
        task_fields = [
            ("node_config", "JSON"),
            ("due_date", "DATETIME"),
            ("priority", "INTEGER"),
            ("variables", "JSON")
        ]
        
        for field_name, field_type in task_fields:
            await safe_add_column("workflow_tasks", field_name, field_type)
        
        # 4. 创建 workflow_node_instances 表
        try:
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
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- workflow_node_instances 表已存在，跳过")
            else:
                print(f"! 创建 workflow_node_instances 表时出错: {str(e)[:100]}")
        
        # 5. 创建 workflow_variable_logs 表
        try:
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
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- workflow_variable_logs 表已存在，跳过")
            else:
                print(f"! 创建 workflow_variable_logs 表时出错: {str(e)[:100]}")
        
        # 6. 创建 workflow_task_candidates 表
        try:
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
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- workflow_task_candidates 表已存在，跳过")
            else:
                print(f"! 创建 workflow_task_candidates 表时出错: {str(e)[:100]}")
        
        print("\n工作流模块升级迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())