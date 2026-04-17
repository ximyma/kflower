"""
数据迁移API路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.migration import migration_service
from app.models.user import User

router = APIRouter(prefix="/migration", tags=["数据迁移"])


class DatabaseConnection(BaseModel):
    """数据库连接配置"""
    db_type: str  # sqlite, mysql, postgresql
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_connection_string(self) -> str:
        """转换为SQLAlchemy连接字符串"""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.database}"
        elif self.db_type == "mysql":
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "postgresql":
            return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")


class MigrationRequest(BaseModel):
    """迁移请求"""
    source: DatabaseConnection
    target: DatabaseConnection
    tables: List[str]
    batch_size: int = 1000
    skip_existing: bool = False


class MigrationResponse(BaseModel):
    """迁移响应"""
    success: bool
    message: str
    results: Optional[Dict] = None


@router.post("/test-connection")
async def test_connection(
    config: DatabaseConnection,
    current_user: User = Depends(get_current_user)
):
    """测试数据库连接"""
    try:
        conn_str = config.to_connection_string()
        engine = migration_service.connect_source(config.db_type, conn_str)
        tables = migration_service.get_tables(engine)
        return {
            "success": True,
            "message": "连接成功",
            "tables": tables
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/table-info")
async def get_table_info(
    config: DatabaseConnection,
    table_name: str,
    current_user: User = Depends(get_current_user)
):
    """获取表信息"""
    try:
        conn_str = config.to_connection_string()
        engine = migration_service.connect_source(config.db_type, conn_str)
        info = migration_service.get_table_info(engine, table_name)
        return {
            "success": True,
            "data": info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute")
async def execute_migration(
    request: MigrationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """执行数据迁移"""
    try:
        # 连接源数据库
        source_conn = request.source.to_connection_string()
        migration_service.connect_source(request.source.db_type, source_conn)
        
        # 连接目标数据库
        target_conn = request.target.to_connection_string()
        migration_service.connect_target(request.target.db_type, target_conn)
        
        # 执行迁移
        results = await migration_service.migrate_data(
            tables=request.tables,
            batch_size=request.batch_size,
            skip_existing=request.skip_existing
        )
        
        return {
            "success": True,
            "message": "迁移完成",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-script")
async def generate_migration_script(
    request: MigrationRequest,
    current_user: User = Depends(get_current_user)
):
    """生成迁移脚本"""
    try:
        script = migration_service.generate_migration_script(
            request.source.db_type,
            request.target.db_type
        )
        return {
            "success": True,
            "script": script
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
