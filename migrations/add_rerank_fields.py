"""
迁移脚本：为知识库添加 rerank_model 和 rerank_enabled 字段
执行方式：python -m migrations.add_rerank_fields
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
        # 检查字段是否已存在
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'knowledge_bases' AND column_name = 'rerank_model'"
        ))
        if result.fetchone() is None:
            await conn.execute(text(
                "ALTER TABLE knowledge_bases ADD COLUMN rerank_model VARCHAR(200) NULL"
            ))
            print("✓ 添加 rerank_model 字段")
        else:
            print("- rerank_model 字段已存在，跳过")
        
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'knowledge_bases' AND column_name = 'rerank_enabled'"
        ))
        if result.fetchone() is None:
            await conn.execute(text(
                "ALTER TABLE knowledge_bases ADD COLUMN rerank_enabled BOOLEAN DEFAULT FALSE"
            ))
            print("✓ 添加 rerank_enabled 字段")
        else:
            print("- rerank_enabled 字段已存在，跳过")
    
    print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
