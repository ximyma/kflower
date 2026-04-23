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
    yield
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
