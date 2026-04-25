import sys, os
sys.path.insert(0, r'E:\kkflower\kflower-backend')
os.chdir(r'E:\kkflower\kflower-backend')

import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, text

async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT config FROM applications LIMIT 1"))
        row = result.fetchone()
        print('Raw config:', repr(row[0]))
        print('Type:', type(row[0]))

asyncio.run(test())
