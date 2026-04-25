"""模拟后端提交流程 - 直接用 raw SQL"""
import asyncio, json, sys

async def test():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with AsyncSession(engine) as session:
        # 直接查 raw 数据
        result = await session.execute(text("SELECT id, name, modules, config FROM templates WHERE id = 15"))
        row = result.fetchone()
        
        modules_raw = row[2]
        print(f"modules type from raw: {type(modules_raw)}")
        
        # 模拟后端解析 modules
        if isinstance(modules_raw, str):
            modules = json.loads(modules_raw)
        else:
            modules = modules_raw
        
        print(f"modules is list: {isinstance(modules, list)}")
        
        # 获取字段
        all_fields = []
        for mod in (modules or []):
            if isinstance(mod, dict) and 'fields' in mod:
                for f in mod['fields']:
                    if isinstance(f, dict):
                        all_fields.append(f)
        
        print(f"all_fields count: {len(all_fields)}")
        for f in all_fields:
            print(f"  {f.get('name')}: type={f.get('type')}, is_formula={f.get('is_formula')}")
        
        # 模拟提交数据
        data = {
            'field': '测试村',
            'quantity': 10,
            'field_1': 5000,
            'field_2': 250,
            'field_3': 750,
            'field_4': 500,
            'field_5': 600,
            'field_6': 5400,
            'remark': '测试'
        }
        
        # 构建 INSERT
        columns = ["template_id", "created_by"]
        placeholders = [":template_id", ":created_by"]
        values = {"template_id": 15, "created_by": 1}
        
        for field_name, value in data.items():
            safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
            if safe_name[0].isdigit():
                safe_name = 'f_' + safe_name
            columns.append(f'"{safe_name}"')
            placeholders.append(f':{safe_name}')
            values[safe_name] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        
        insert_sql = f"INSERT INTO form_data_15 ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        print(f"\nSQL: {insert_sql}")
        
        try:
            await session.execute(text(insert_sql), values)
            await session.commit()
            print("SUCCESS: row inserted via async raw SQL")
        except Exception as e:
            await session.rollback()
            import traceback
            print(f"ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
    
    await engine.dispose()

asyncio.run(test())
