"""
数据库连接模块
SQLite 优化配置：
- PRAGMA synchronous=NORMAL  # 平衡性能与安全
- PRAGMA journal_mode=WAL     # Write-Ahead Logging 并发优化
- PRAGMA cache_size=10000      # 10MB 缓存
- PRAGMA temp_store=MEMORY    # 临时表存储在内存
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# SQLite 连接参数
sqlite_kwargs = {}
if "sqlite" in settings.DATABASE_URL:
    sqlite_kwargs = {
        "check_same_thread": False,
    }

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=sqlite_kwargs,
)

# 创建同步引擎（供插件管理等需要同步 session 的模块使用）
# 注意：使用 AUTOCOMMIT 避免与 aiosqlite 异步引擎的 WAL 锁冲突
_sync_url = settings.DATABASE_URL
if _sync_url.startswith('sqlite+aiosqlite://'):
    _sync_url = _sync_url.replace('sqlite+aiosqlite://', 'sqlite://', 1)
engine_sync = create_sync_engine(
    _sync_url,
    echo=settings.DB_ECHO,
    connect_args=sqlite_kwargs,
    isolation_level="AUTOCOMMIT",
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基类
Base = declarative_base()


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        # 为 SQLite 应用优化参数
        if "sqlite" in settings.DATABASE_URL:
            from sqlalchemy import text
            await conn.execute(text("PRAGMA encoding='UTF-8'"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA cache_size=10000"))
            await conn.execute(text("PRAGMA temp_store=MEMORY"))
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    engine_sync.dispose()
