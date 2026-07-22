"""
迁移脚本: 创建审计日志表
日期: 2026-06-23
用途: 参考 NocoBase 审计日志，支持字段级变更追踪
影响: 新建 audit_logs + audit_changes 表
"""
from sqlalchemy import text


async def upgrade(engine):
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type VARCHAR(20) NOT NULL,
                collection_name VARCHAR(100) NOT NULL,
                record_id INTEGER NOT NULL,
                record_title VARCHAR(500),
                user_id INTEGER REFERENCES users(id),
                remote_addr VARCHAR(50),
                user_agent VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id INTEGER NOT NULL REFERENCES audit_logs(id),
                field JSON,
                before JSON,
                after JSON
            )
        """))
    print("✅ 审计日志表创建成功")


async def downgrade(engine):
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS audit_changes"))
        await conn.execute(text("DROP TABLE IF EXISTS audit_logs"))
    print("✅ 审计日志表已删除")
