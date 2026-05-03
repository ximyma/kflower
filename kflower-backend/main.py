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
    
    # AI 服务健康检查
    await _check_ai_services()
    
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


async def _check_ai_services():
    """检查 AI 服务配置状态"""
    print("\n" + "="*60)
    print("🔍 AI 服务健康检查")
    print("="*60)
    
    issues = []
    
    # 1. 检查 OCR
    try:
        from app.core.ai_digital_base.local_services import ocr_service, TESSERACT_AVAILABLE
        if not TESSERACT_AVAILABLE:
            issues.append("⚠️ pytesseract 未安装，OCR 功能不可用")
            print("❌ OCR: pytesseract 未安装")
        elif not ocr_service.tesseract_path:
            issues.append("⚠️ OCR 未配置 Tesseract 路径，请到系统设置中配置")
            print("❌ OCR: Tesseract 路径未配置")
        elif ocr_service.is_configured():
            print(f"✅ OCR: 已配置 ({ocr_service.tesseract_path})")
        else:
            issues.append("⚠️ OCR Tesseract 不可用，请检查路径是否正确")
            print(f"❌ OCR: Tesseract 不可用 ({ocr_service.tesseract_path})")
    except Exception as e:
        issues.append(f"⚠️ OCR 服务加载失败: {e}")
        print(f"❌ OCR: 加载失败 - {e}")
    
    # 2. 检查 Embedding
    try:
        from app.core.ai_digital_base.local_services import get_embedding_service, ST_AVAILABLE
        embed_svc = get_embedding_service()
        
        if not ST_AVAILABLE:
            issues.append("⚠️ sentence-transformers 未安装，本地 Embedding 模型不可用")
            print("❌ Embedding: sentence-transformers 未安装")
        else:
            print("✅ Embedding: sentence-transformers 已安装")
            
            # 检查配置的模型
            provider = embed_svc.embedding_provider
            model = embed_svc.embedding_model
            
            if provider == "local":
                # 检查本地模型
                custom_models = embed_svc._custom_models
                if custom_models:
                    print(f"✅ Embedding: 已配置 {len(custom_models)} 个本地模型")
                else:
                    print("⚠️ Embedding: 未配置本地模型")
            elif provider == "api":
                if embed_svc.embedding_api_key:
                    print(f"✅ Embedding: API 模型已配置 ({model})")
                else:
                    issues.append("⚠️ Embedding API 未配置 API Key，请到系统设置中配置")
                    print("❌ Embedding: API Key 未配置")
            else:
                issues.append(f"⚠️ Embedding provider 配置异常: {provider}")
                print(f"❌ Embedding: provider 配置异常 ({provider})")
    except Exception as e:
        issues.append(f"⚠️ Embedding 服务加载失败: {e}")
        print(f"❌ Embedding: 加载失败 - {e}")
    
    # 3. 检查 Jieba
    try:
        from app.core.ai_digital_base.local_services import text_parser_service, JIEBA_AVAILABLE
        if not JIEBA_AVAILABLE:
            issues.append("⚠️ jieba 未安装，中文分词功能不可用")
            print("❌ Jieba: 未安装")
        else:
            print("✅ Jieba: 已安装并初始化")
    except Exception as e:
        issues.append(f"⚠️ Jieba 服务加载失败: {e}")
        print(f"❌ Jieba: 加载失败 - {e}")
    
    # 4. 检查 Reranker
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.ai import SystemConfig
        from sqlalchemy import select
        import json
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == "rerank_models")
            )
            cfg = result.scalar_one_or_none()
            if cfg and cfg.value:
                rerank_models = json.loads(cfg.value)
                enabled_models = [m for m in rerank_models if m.get("enabled")]
                if enabled_models:
                    print(f"✅ Reranker: 已配置 {len(enabled_models)} 个可用模型")
                else:
                    print("⚠️ Reranker: 已配置但无可用模型（全部禁用）")
            else:
                print("⚠️ Reranker: 未配置")
    except Exception as e:
        print(f"⚠️ Reranker: 检查失败 - {e}")
    
    # 总结
    print("="*60)
    if issues:
        print("⚠️  发现以下问题：")
        for issue in issues:
            print(f"   {issue}")
        print("="*60)
        print("💡 提示：请到「系统设置」→「本地模型」中配置相关服务")
    else:
        print("✅ 所有 AI 服务已就绪！")
    print("="*60 + "\n")


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
