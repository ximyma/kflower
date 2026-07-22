"""
迁移脚本: WorkflowTask 添加 node_type 字段
日期: 2026-06-23
用途: 修复 engine.py 设置 node_type 但模型缺字段的bug
影响: workflow_tasks 表新增 node_type 列
"""
from sqlalchemy import text


async def upgrade(engine):
    """执行迁移"""
    async with engine.begin() as conn:
        # 添加 node_type 列
        await conn.execute(text(
            "ALTER TABLE workflow_tasks ADD COLUMN node_type VARCHAR(50)"
        ))
    print("✅ workflow_tasks.node_type 字段添加成功")


async def downgrade(engine):
    """回滚迁移（SQLite 不支持 DROP COLUMN，仅记录）"""
    print("⚠️ SQLite 不支持 DROP COLUMN，回滚需手动操作")
