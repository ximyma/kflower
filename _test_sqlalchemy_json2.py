"""测试 SQLAlchemy JSON 在 aiosqlite 下是否自动解析"""
import asyncio, json, sys
sys.path.insert(0, 'kflower-backend')

async def test():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import Column, Integer, String, JSON, text
    from sqlalchemy.orm import declarative_base
    
    Base = declarative_base()
    
    # 完全重新定义，不依赖 app 的模型
    class TestTemplate(Base):
        __tablename__ = 'templates'
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True)
        name = Column(String)
        modules = Column(JSON)
        config = Column(JSON)
    
    DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        # 用 ORM 查询
        result = await session.execute(
            text("SELECT id, name, modules, config FROM templates WHERE id = 15")
        )
        row = result.fetchone()
        
        # 手动赋值给 ORM 对象
        t = TestTemplate()
        t.id = row[0]
        t.name = row[1]
        t.modules = row[2]
        t.config = row[3]
        
        print(f"After ORM assignment:")
        print(f"  modules type: {type(t.modules)}")
        print(f"  config type: {type(t.config)}")
        
        # 测试 .get() 是否可用
        if hasattr(t.config, 'get'):
            print(f"  config.get('table_name'): {t.config.get('table_name', 'default')}")
        else:
            print(f"  config has NO .get() method!")
        
        # 模拟 submit_template_data 中的代码
        print(f"\n=== Simulating submit_template_data ===")
        
        # 第 285 行
        all_fields = []
        for mod in (t.modules or []):
            if isinstance(mod, dict) and 'fields' in mod:
                for f in mod['fields']:
                    if isinstance(f, dict):
                        all_fields.append(f)
        print(f"all_fields count: {len(all_fields)}")
        
        # 第 363-364 行
        config = t.config or {}
        print(f"config type: {type(config)}")
        if hasattr(config, 'get'):
            table_name = config.get('table_name', f'form_data_15')
            print(f"table_name: {table_name}")
        else:
            print(f"CRASH: config is {type(config)}, .get() will fail!")
    
    await engine.dispose()

asyncio.run(test())
