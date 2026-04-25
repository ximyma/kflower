"""测试 aiosqlite + SQLAlchemy ORM 下 JSON 字段的解析行为"""
import asyncio, json, sys
sys.path.insert(0, 'kflower-backend')

async def test():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select, text
    
    DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        # 用 raw SQL 查，看 aiosqlite 返回什么
        result = await session.execute(text("SELECT modules, config FROM templates WHERE id = 15"))
        row = result.fetchone()
        
        modules_raw = row[0]
        config_raw = row[1]
        
        print(f"=== Raw SQL results ===")
        print(f"modules type: {type(modules_raw)}")
        print(f"modules is str: {isinstance(modules_raw, str)}")
        print(f"modules is dict: {isinstance(modules_raw, (list, dict))}")
        
        print(f"config type: {type(config_raw)}")
        print(f"config is str: {isinstance(config_raw, str)}")
        print(f"config is dict: {isinstance(config_raw, dict)}")
        
        # 如果 aiosqlite 返回字符串，手动解析
        if isinstance(modules_raw, str):
            try:
                modules = json.loads(modules_raw)
                print(f"\nManual parsed modules: list={isinstance(modules, list)}, len={len(modules)}")
            except:
                print(f"\nFailed to parse modules string")
        
        if isinstance(config_raw, str):
            try:
                config = json.loads(config_raw)
                print(f"Manual parsed config: dict={isinstance(config, dict)}")
            except:
                print(f"Failed to parse config string")
    
    await engine.dispose()

asyncio.run(test())
