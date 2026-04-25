"""测试 SQLAlchemy JSON 类型在 aiosqlite 下的行为"""
import asyncio, json, sys
sys.path.insert(0, 'kflower-backend')

async def test():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import Column, Integer, String, JSON, text
    from sqlalchemy.orm import declarative_base
    
    Base = declarative_base()
    
    class TestModel(Base):
        __tablename__ = 'templates'
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True)
        name = Column(String)
        modules = Column(JSON)
        config = Column(JSON)
    
    DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        result = await session.execute(text("SELECT id, name, modules, config FROM templates WHERE id = 15"))
        row = result.fetchone()
        print(f"Raw SQL - modules type: {type(row[2])}, config type: {type(row[3])}")
        
        # 用 ORM 查
        result2 = await session.execute(
            text("SELECT id, name, modules, config FROM templates WHERE id = 15")
        )
        row2 = result2.fetchone()
        
        # 手动构建对象
        t = TestModel(
            id=row2[0],
            name=row2[1],
            modules=row2[2],
            config=row2[3]
        )
        
        print(f"\nORM-like - modules type: {type(t.modules)}")
        print(f"ORM-like - config type: {type(t.config)}")
        
        if isinstance(t.modules, str):
            print("modules is STILL a string after ORM assignment!")
        elif isinstance(t.modules, list):
            print("modules is correctly a list")
            print(f"  len={len(t.modules)}")
            for mod in t.modules:
                if isinstance(mod, dict) and 'fields' in mod:
                    print(f"  fields count: {len(mod['fields'])}")
    
    await engine.dispose()

asyncio.run(test())
