# -*- coding: utf-8 -*-
"""Fix ai_models value_type from string to json"""
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

async def fix():
    async with AsyncSessionLocal() as db:
        # Fix ai_models
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == "ai_models")
        )
        config = result.scalar_one_or_none()
        if config:
            print(f"ai_models: type={config.value_type}, value_len={len(config.value) if config.value else 0}")
            config.value_type = "json"
            print("Fixed ai_models value_type: string -> json")
        
        # Fix ai_params
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == "ai_params")
        )
        config = result.scalar_one_or_none()
        if config:
            print(f"ai_params: type={config.value_type}, value_len={len(config.value) if config.value else 0}")
            config.value_type = "json"
            print("Fixed ai_params value_type: string -> json")
        
        # Fix module_ai_settings
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == "module_ai_settings")
        )
        config = result.scalar_one_or_none()
        if config:
            print(f"module_ai_settings: type={config.value_type}, value_len={len(config.value) if config.value else 0}")
            config.value_type = "json"
            print("Fixed module_ai_settings value_type: string -> json")
        
        await db.commit()
        print("\nAll fixes applied!")

if __name__ == "__main__":
    asyncio.run(fix())
