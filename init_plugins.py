#!/usr/bin/env python3
"""
初始化插件数据
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "kflower-backend"))

from app.core.database import AsyncSessionLocal
from app.models.plugin import Plugin, PluginHook, BUILTIN_HOOKS, seed_builtin_hooks
from app.core.database import Base, engine


async def init_plugins():
    """初始化插件数据"""
    print("[初始化] 正在初始化插件数据...")
    
    # 创建数据库表（如果不存在）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # 先初始化内置钩子
        from sqlalchemy import select
        for hook_def in BUILTIN_HOOKS:
            result = await session.execute(
                select(PluginHook).where(PluginHook.name == hook_def["name"])
            )
            if not result.scalar_one_or_none():
                session.add(PluginHook(**hook_def))
                print(f"  [+] 添加钩子: {hook_def['name']}")
        
        # 添加一些示例插件
        sample_plugins = [
            {
                "name": "auto_notification",
                "display_name": "自动通知",
                "description": "在数据变更时自动发送通知提醒",
                "version": "1.0.0",
                "author": "Kflower Team",
                "category": "builtin",
                "is_enabled": True,
                "is_built_in": True,
                "hook_code": {
                    "after_form_submit": """def on_event(ctx):
    print(f"数据已提交: {ctx.get('payload')}")
    return {"result": "ok", "message": "通知已发送"}
"""
                }
            },
            {
                "name": "data_validator",
                "display_name": "数据校验器",
                "description": "在提交前对表单数据进行额外校验",
                "version": "1.0.0",
                "author": "Kflower Team",
                "category": "builtin",
                "is_enabled": True,
                "is_built_in": True,
                "hook_code": {
                    "before_form_submit": """def on_event(ctx):
    data = ctx.get("payload", {})
    if not data.get("title"):
        return {"result": "error", "message": "标题不能为空"}
    return {"result": "ok"}
"""
                }
            }
        ]
        
        for plugin_data in sample_plugins:
            from sqlalchemy import select
            result = await session.execute(
                select(Plugin).where(Plugin.name == plugin_data["name"])
            )
            if not result.scalar_one_or_none():
                plugin = Plugin(**plugin_data)
                session.add(plugin)
                print(f"  [+] 添加插件: {plugin_data['name']}")
        
        await session.commit()
    
    print("[OK] 插件数据初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_plugins())
