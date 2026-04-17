# -*- coding: utf-8 -*-
import asyncio, sys, json
sys.path.insert(0, r'D:\kflower\kflower-backend')
import app.models.user, app.models.workflow, app.models.ai, app.models.permission
from app.core.database import AsyncSessionLocal
from app.models.ai import SystemConfig
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == 'ai_models'))
        config = result.scalar_one_or_none()
        if config:
            models = json.loads(config.value) if config.value else []
            for m in models:
                params = m.get('params', {})
                print(f"Provider: {m.get('provider')} | ModelId: {m.get('modelId')} | Timeout: {params.get('timeout', 'NOT SET')}")

asyncio.run(check())
