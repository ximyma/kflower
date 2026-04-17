"""
数据迁移服务
支持 SQLite <-> MySQL/PostgreSQL 迁移
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import sqlite3

from app.core.database import Base
from app.core.config import settings


class MigrationService:
    """数据迁移服务"""
    
    def __init__(self):
        self.source_engine: Optional[Engine] = None
        self.target_engine: Optional[Engine] = None
        self.progress_callback: Optional[Callable] = None
        
    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self.progress_callback = callback
        
    def _notify_progress(self, message: str, percent: int):
        """通知进度"""
        if self.progress_callback:
            self.progress_callback(message, percent)
            
    def connect_source(self, db_type: str, connection_string: str):
        """连接源数据库"""
        self.source_engine = create_engine(connection_string)
        return self._test_connection(self.source_engine)
        
    def connect_target(self, db_type: str, connection_string: str):
        """连接目标数据库"""
        self.target_engine = create_engine(connection_string)
        return self._test_connection(self.target_engine)
        
    def _test_connection(self, engine: Engine) -> bool:
        """测试数据库连接"""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            raise Exception(f"数据库连接失败: {str(e)}")
            
    def get_tables(self, engine: Engine) -> List[str]:
        """获取数据库中的所有表"""
        inspector = inspect(engine)
        return inspector.get_table_names()
        
    def get_table_info(self, engine: Engine, table_name: str) -> Dict:
        """获取表信息"""
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        indexes = inspector.get_indexes(table_name)
        
        return {
            "name": table_name,
            "columns": [{"name": c["name"], "type": str(c["type"])} for c in columns],
            "indexes": indexes,
            "row_count": self._get_row_count(engine, table_name)
        }
        
    def _get_row_count(self, engine: Engine, table_name: str) -> int:
        """获取表行数"""
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
            
    async def migrate_data(
        self,
        tables: List[str],
        batch_size: int = 1000,
        skip_existing: bool = False
    ) -> Dict:
        """
        执行数据迁移
        
        Args:
            tables: 要迁移的表列表
            batch_size: 每批处理的数据量
            skip_existing: 是否跳过已存在的表
            
        Returns:
            迁移结果统计
        """
        if not self.source_engine or not self.target_engine:
            raise Exception("请先配置源数据库和目标数据库")
            
        results = {
            "start_time": datetime.now().isoformat(),
            "tables": {},
            "total_rows": 0,
            "errors": []
        }
        
        total_tables = len(tables)
        
        for idx, table_name in enumerate(tables):
            progress = int((idx / total_tables) * 100)
            self._notify_progress(f"正在迁移表: {table_name}", progress)
            
            try:
                table_result = await self._migrate_table(
                    table_name, batch_size, skip_existing
                )
                results["tables"][table_name] = table_result
                results["total_rows"] += table_result["rows_migrated"]
            except Exception as e:
                error_msg = f"迁移表 {table_name} 失败: {str(e)}"
                results["errors"].append(error_msg)
                self._notify_progress(error_msg, progress)
                
        results["end_time"] = datetime.now().isoformat()
        self._notify_progress("数据迁移完成", 100)
        
        return results
        
    async def _migrate_table(
        self,
        table_name: str,
        batch_size: int,
        skip_existing: bool
    ) -> Dict:
        """迁移单个表"""
        result = {
            "rows_migrated": 0,
            "rows_skipped": 0,
            "errors": []
        }
        
        # 检查目标表是否存在
        target_tables = self.get_tables(self.target_engine)
        if table_name in target_tables and skip_existing:
            result["rows_skipped"] = self._get_row_count(self.target_engine, table_name)
            return result
            
        # 获取源表数据
        source_session = sessionmaker(bind=self.source_engine)()
        target_session = sessionmaker(bind=self.target_engine)()
        
        try:
            # 获取列信息
            inspector = inspect(self.source_engine)
            columns = inspector.get_columns(table_name)
            column_names = [c["name"] for c in columns]
            
            # 读取数据
            offset = 0
            while True:
                query = text(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
                rows = source_session.execute(query).fetchall()
                
                if not rows:
                    break
                    
                # 插入目标数据库
                for row in rows:
                    try:
                        row_dict = dict(zip(column_names, row))
                        # 处理特殊字段
                        row_dict = self._process_row_data(row_dict)
                        
                        # 构建插入语句
                        columns_str = ", ".join(row_dict.keys())
                        values_str = ", ".join([f":{k}" for k in row_dict.keys()])
                        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"
                        
                        target_session.execute(text(insert_sql), row_dict)
                        result["rows_migrated"] += 1
                    except Exception as e:
                        result["errors"].append(str(e))
                        
                target_session.commit()
                offset += batch_size
                
        finally:
            source_session.close()
            target_session.close()
            
        return result
        
    def _process_row_data(self, row: Dict) -> Dict:
        """处理行数据，转换特殊类型"""
        processed = {}
        for key, value in row.items():
            if value is None:
                processed[key] = None
            elif isinstance(value, datetime):
                processed[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                processed[key] = json.dumps(value, ensure_ascii=False)
            else:
                processed[key] = value
        return processed
        
    def generate_migration_script(self, source_type: str, target_type: str) -> str:
        """生成迁移脚本"""
        script = f"""#!/usr/bin/env python3
\"\"\"
数据迁移脚本
从 {source_type} 迁移到 {target_type}
生成时间: {datetime.now().isoformat()}
\"\"\"

import asyncio
from app.core.migration import MigrationService

async def main():
    service = MigrationService()
    
    # 配置源数据库
    source_conn = "{self.source_engine.url if self.source_engine else ''}"
    service.connect_source("{source_type}", source_conn)
    
    # 配置目标数据库
    target_conn = "{self.target_engine.url if self.target_engine else ''}"
    service.connect_target("{target_type}", target_conn)
    
    # 获取所有表
    tables = service.get_tables(service.source_engine)
    
    # 执行迁移
    results = await service.migrate_data(tables)
    
    print(f"迁移完成，共迁移 {{results['total_rows']}} 行数据")
    if results['errors']:
        print(f"错误: {{len(results['errors'])}}")
        for error in results['errors']:
            print(f"  - {{error}}")

if __name__ == "__main__":
    asyncio.run(main())
"""
        return script


# 全局迁移服务实例
migration_service = MigrationService()
