"""
迁移脚本：添加智能体配置表
执行方式：python -m migrations.add_agents_table
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
        print("开始添加智能体配置表...")
        
        # 1. 创建 agents 表
        try:
            await conn.execute(text("""
                CREATE TABLE agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    agent_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    config JSON,
                    tools JSON,
                    status VARCHAR(20) DEFAULT 'offline',
                    task_count INTEGER DEFAULT 0,
                    organization_id INTEGER,
                    created_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """))
            print("[OK] 创建 agents 表")
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate table" in error_msg:
                print("- agents 表已存在，跳过")
            else:
                print(f"! 创建 agents 表时出错: {str(e)[:100]}")
                traceback.print_exc()
        
        # 2. 创建索引
        try:
            await conn.execute(text("CREATE INDEX idx_agents_org ON agents (organization_id)"))
            print("[OK] 创建 organization_id 索引")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- idx_agents_org 索引已存在，跳过")
            else:
                print(f"! 创建索引时出错: {str(e)[:100]}")
        
        try:
            await conn.execute(text("CREATE INDEX idx_agents_type ON agents (agent_type)"))
            print("[OK] create agent_type index")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- idx_agents_type 索引已存在，跳过")
            else:
                print(f"! 创建索引时出错: {str(e)[:100]}")
        
        try:
            await conn.execute(text("CREATE INDEX idx_agents_status ON agents (status)"))
            print("[OK] 创建 status 索引")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("- idx_agents_status 索引已存在，跳过")
            else:
                print(f"! 创建索引时出错: {str(e)[:100]}")
        
        print("\n智能体配置表迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())