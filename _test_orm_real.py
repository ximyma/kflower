"""测试真实 ORM 查询下 template.modules 的类型 - 绕过关系"""
import asyncio, json, sys
sys.path.insert(0, 'kflower-backend')

async def test():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy import select, text
    
    DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        # 直接用 raw SQL 查，模拟 ORM 的 JSON 列处理
        result = await session.execute(text("SELECT id, name, modules, config FROM templates WHERE id = 15"))
        row = result.fetchone()
        
        modules_raw = row[2]
        config_raw = row[3]
        
        print(f"Raw SQL - modules type: {type(modules_raw)}")
        print(f"Raw SQL - config type: {type(config_raw)}")
        
        # 模拟后端代码中的处理
        # 第 285 行: for mod in (template.modules or []):
        # 如果 template.modules 是字符串，这里遍历的是字符
        template_modules = modules_raw  # 模拟 ORM 返回的值
        all_fields = []
        for mod in (template_modules or []):
            print(f"  iterating: {type(mod)} = {repr(mod)[:50]}")
            if isinstance(mod, dict) and 'fields' in mod:
                for f in mod['fields']:
                    if isinstance(f, dict):
                        all_fields.append(f)
        
        print(f"\nall_fields count: {len(all_fields)}")
        
        # 模拟 config 处理
        # 第 363 行: config = template.config or {}
        config = config_raw or {}
        print(f"\nconfig type: {type(config)}")
        print(f"config has .get: {hasattr(config, 'get')}")
        
        if hasattr(config, 'get'):
            table_name = config.get('table_name', 'form_data_15')
            print(f"table_name: {table_name}")
        else:
            print(f"ERROR: config is {type(config)}, no .get() method!")
            print(f"config value: {config}")
    
    await engine.dispose()

asyncio.run(test())
