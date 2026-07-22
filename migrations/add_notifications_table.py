"""
迁移脚本: 创建通知记录表
日期: 2026-06-23
用途: 支持工作流/智能体的通知持久化存储
影响: 新增 notifications 表
"""
from sqlalchemy import text


async def upgrade(engine):
    """执行迁移"""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                title VARCHAR(500) NOT NULL,
                content TEXT,
                type VARCHAR(50) DEFAULT 'system',
                channel VARCHAR(50) DEFAULT 'system',
                source_type VARCHAR(50),
                source_id INTEGER,
                is_read BOOLEAN DEFAULT 0,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
    print("✅ 通知记录表创建成功")


async def downgrade(engine):
    """回滚迁移"""
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS notifications"))
    print("✅ 通知记录表已删除")
