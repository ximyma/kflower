# -*- coding: utf-8 -*-
"""Check system_configs table"""
import asyncio
import sys
sys.path.insert(0, r'D:\kflower\kflower-backend')

import app.models.user
import app.models.workflow
import app.models.ai
import app.models.permission

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.ai import SystemConfig
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SystemConfig))
        configs = result.scalars().all()
        print(f"Total configs: {len(configs)}")
        for c in configs:
            val = c.value[:80] if c.value and len(c.value) > 80 else c.value
            print(f"  Key: {c.key} | Type: {c.value_type} | Org: {c.organization_id} | Val: {val}")

if __name__ == "__main__":
    asyncio.run(check())
