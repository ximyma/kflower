"""
Kflower 企业智能管理低代码平台 - 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1 import api_router

# 确保所有模型被导入，以便 create_all 创建表
import app.models.user  # noqa: F401
import app.models.workflow  # noqa: F401
import app.models.ai  # noqa: F401
import app.modules.my_apps.models  # noqa: F401
import app.models.plugin  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    
    # 初始化数据库
    await init_db()
    print("[OK] 数据库初始化完成")
    
    # 创建默认管理员账户（如果不存在）
    await _create_default_admin()
    
    yield
    
    # 关闭数据库连接
    await close_db()
    print(f"[停止] {settings.APP_NAME} 已关闭")


async def _create_default_admin():
    """创建默认管理员账户"""
    from app.core.database import AsyncSessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                email="admin@kflower.local",
                password_hash=get_password_hash("admin123"),
                full_name="系统管理员",
                is_superuser=True,
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("[OK] 默认管理员账户已创建 (admin/admin123)")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Kflower 企业智能管理低代码平台

基于 AI 大模型与多智能体系统的企业级低代码开发平台。

### 核心能力
- 🤖 **AI智能对话** - 自然语言交互，智能辅助决策
- 📋 **模板设计** - 对话式应用生成，智能字段推荐
- 🔄 **流程审批** - 智能流程助手，自动推荐审批人
- 📊 **决策分析** - 智能问答分析，预测性洞察
- 🔍 **知识库RAG** - 文档智能解析，向量语义检索
- 🔐 **权限管理** - 智能角色推荐，异常行为检测

### 认证
使用 JWT Token 认证，登录后获取 Token，在请求头中添加：
```
Authorization: Bearer <your_token>
```
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.APP_VERSION}


# 启动命令
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
