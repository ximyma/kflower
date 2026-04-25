"""完整模拟仪表盘数据请求流程"""
import sys, os, json, asyncio
sys.path.insert(0, 'kflower-backend')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.modules.my_apps.analytics_engine import analytics_engine

DATABASE_URL = "sqlite+aiosqlite:///kflower-backend/kflower-data/kflower.db"
engine = create_async_engine(DATABASE_URL, echo=False)

async def test():
    async with async_sessionmaker(engine, class_=AsyncSession)() as db:
        # 模拟从数据库加载的旧配置（没有 date_field）
        print("=== 测试1: 旧配置（无 date_field）- COUNT ===")
        config1 = {
            "type": "aggregation",
            "template_id": 14,
            "aggregate": "count",
            "field": "",
            "date_range": "",
            "filters": [],
        }
        result = await analytics_engine.execute_aggregation(db, config1, user_id=1)
        print(f"  结果: {json.dumps(result, ensure_ascii=False)}")

        # 测试2: 旧配置 - 列表查询（无 date_field）
        print("\n=== 测试2: 旧配置（无 date_field）- 列表查询 ===")
        config2 = {
            "type": "query",
            "template_id": 15,
            "aggregate": "count",
            "field": "",
            "date_range": "",
            "order_by": "-created_at",
            "filters": [],
        }
        result = await analytics_engine.execute_aggregation(db, config2, user_id=1)
        print(f"  结果类型: {result.get('type')}, 数量: {result.get('count')}")
        if result.get('data'):
            print(f"  第一条: {json.dumps(result['data'][0], ensure_ascii=False, default=str)[:200]}")

        # 测试3: 用错误的 user_id
        print("\n=== 测试3: 错误的 user_id (user_id=999) ===")
        config3 = {
            "type": "aggregation",
            "template_id": 14,
            "aggregate": "count",
        }
        result = await analytics_engine.execute_aggregation(db, config3, user_id=999)
        print(f"  结果: {json.dumps(result, ensure_ascii=False)}")

        # 测试4: 不用 user_id 过滤
        print("\n=== 测试4: 不用 user_id 过滤 ===")
        result = await analytics_engine.execute_aggregation(db, config3)
        print(f"  结果: {json.dumps(result, ensure_ascii=False)}")

        # 测试5: 验证模板14的 config 在 aiosqlite 下是否真的是字符串
        from sqlalchemy import text as sql_text
        row = (await db.execute(sql_text("SELECT config FROM templates WHERE id=14"))).fetchone()
        print(f"\n=== 测试5: 模板14 config 类型 ===")
        print(f"  类型: {type(row[0]).__name__}, 值: {str(row[0])[:100]}")

    await engine.dispose()
    print("\n=== 全部测试完成 ===")

asyncio.run(test())
