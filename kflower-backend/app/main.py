"""
Kflower 企业智能管理平台 - FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, AsyncSessionLocal, Base, init_db as create_tables
from app.core.security import get_password_hash
from app.api.v1 import api_router


def init_db():
    """导入所有模型"""
    import app.models.user  # noqa
    import app.models.workflow  # noqa
    import app.models.ai  # noqa
    import app.models.permission  # noqa
    import app.models.notification_template  # noqa
    import app.models.data_model  # noqa
    import app.models.plugin  # noqa
    import app.models.plugin_binding  # noqa
    import app.modules.my_apps.models  # noqa


async def create_default_user():
    """创建默认管理员账户"""
    async with AsyncSessionLocal() as db:
        from app.models.user import User
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()
        if not existing:
            admin = User(
                username="admin",
                email="admin@kflower.com",
                full_name="System Administrator",
                password_hash=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            await db.commit()
            print("[Kflower] Default admin created: admin / admin123")
        else:
            print("[Kflower] Admin user already exists")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Kflower] Starting Kflower Enterprise AI Platform...")
    init_db()
    # 创建数据库表
    await create_tables()
    await create_default_user()

    # 初始化插件管理器（注册内置插件 + 加载用户插件）
    try:
        from app.core.plugin_manager import get_plugin_manager
        pm = get_plugin_manager()
        print(f"[PluginManager] 已加载 {len(pm._loaded_plugins)} 个插件: {list(pm._loaded_plugins.keys())}")
    except Exception as e:
        print(f"[PluginManager] 初始化警告: {e}")

    # 同步 AI 工具插件状态到工具注册表
    try:
        from app.core.agent_engine.tools.registry import tool_registry
        synced = tool_registry.sync_from_plugin_system()
        print(f"[ToolRegistry] 同步 AI 工具插件状态完成，共 {synced} 个工具")
    except Exception as e:
        print(f"[ToolRegistry] 同步警告: {e}")

    # 启动 SLA 后台定时巡检
    import asyncio
    from app.core.workflow.sla_manager import SLAManager

    async def sla_periodic_check(interval_minutes: int = 5):
        """每 N 分钟检查一次 SLA 状态（催办+升级）"""
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    sla = SLAManager(db)
                    await sla.process_reminders()
                    await sla.process_escalations()
                    logger.info("[SLA] 定时巡检完成")
            except Exception as e:
                logger.error(f"[SLA] 定时巡检出错: {e}")
            await asyncio.sleep(interval_minutes * 60)

    import logging
    logger = logging.getLogger(__name__)
    sla_task = asyncio.create_task(sla_periodic_check(5))
    print("[Kflower] SLA monitor started")

    yield

    # 关闭后台任务
    sla_task.cancel()
    try:
        await sla_task
    except asyncio.CancelledError:
        pass
    print("[Kflower] SLA monitor stopped")
    print("[Kflower] Shutting down...")


app = FastAPI(
    title="Kflower Enterprise AI Platform",
    version="1.0.0",
    description="AI Agent Platform for Government and Enterprise",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
