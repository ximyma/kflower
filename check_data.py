# -*- coding: utf-8 -*-
"""
检查数据库中的模板和工作流
"""
import asyncio
import sys
sys.path.insert(0, r'D:\kflower\kflower-backend')

import app.models.user
import app.models.workflow
import app.models.ai
import app.models.permission

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.workflow import Template, Workflow
from sqlalchemy import select, func

async def check_data():
    async with AsyncSessionLocal() as db:
        # 统计模板数量
        result = await db.execute(select(func.count()).select_from(Template))
        template_count = result.scalar()
        
        # 统计工作流数量
        result = await db.execute(select(func.count()).select_from(Workflow))
        workflow_count = result.scalar()
        
        print(f"Templates count: {template_count}")
        print(f"Workflows count: {workflow_count}")
        
        # 列出所有模板
        print("\n=== All Templates ===")
        result = await db.execute(select(Template).order_by(Template.id))
        templates = result.scalars().all()
        for t in templates:
            print(f"  ID:{t.id} | {t.name} | Code:{t.code} | Category:{t.category} | Published:{t.is_published}")
        
        # 列出所有工作流
        print("\n=== All Workflows ===")
        result = await db.execute(select(Workflow).order_by(Workflow.id))
        workflows = result.scalars().all()
        for w in workflows:
            print(f"  ID:{w.id} | {w.name} | Code:{w.code}")

if __name__ == "__main__":
    asyncio.run(check_data())
