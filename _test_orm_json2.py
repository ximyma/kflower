"""测试 aiosqlite + SQLAlchemy ORM 下 JSON 字段的解析行为"""
import asyncio, json, sys
sys.path.insert(0, 'kflower-backend')

async def test():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    
    DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        # 直接 raw SQL 查询，手动处理
        from sqlalchemy import text
        result = await session.execute(text("SELECT modules, config FROM templates WHERE id = 15"))
        row = result.fetchone()
        
        modules_raw = row[0]
        config_raw = row[1]
        
        print(f"modules type: {type(modules_raw)}")
        print(f"config type: {type(config_raw)}")
        
        # 手动解析
        if isinstance(modules_raw, str):
            modules = json.loads(modules_raw)
        else:
            modules = modules_raw
            
        if isinstance(config_raw, str):
            config = json.loads(config_raw)
        else:
            config = config_raw
        
        print(f"\nmodules is list: {isinstance(modules, list)}, len={len(modules)}")
        if isinstance(modules, list):
            for i, mod in enumerate(modules):
                print(f"  mod[{i}]: type={type(mod)}, keys={list(mod.keys()) if isinstance(mod, dict) else 'N/A'}")
                if isinstance(mod, dict) and 'fields' in mod:
                    fields = mod['fields']
                    print(f"    fields count: {len(fields)}")
                    for f in fields:
                        print(f"      {f.get('name')}: formula={f.get('formula')}, is_formula={f.get('is_formula')}")
        
        print(f"\nconfig: {config}")
    
    await engine.dispose()

asyncio.run(test())
