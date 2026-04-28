"""
Kflower 内部数据表分析器
分析已发布模板的数据表结构，支持一键复制为新模板
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.sql import func
import json

from app.models.workflow import Template
from app.services.model_to_template import ModelToTemplateConverter


@dataclass
class ColumnInfo:
    """数据库列信息"""
    name: str
    db_type: str
    nullable: bool = True
    default_value: Any = None
    is_primary_key: bool = False
    is_unique: bool = False
    is_auto_increment: bool = False
    max_length: Optional[int] = None
    comment: Optional[str] = None


@dataclass
class TableAnalysis:
    """数据表分析结果"""
    table_name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    row_count: int = 0


class KflowerTableAnalyzer:
    """分析 Kflower 内部已发布的数据表"""

    async def list_published_tables(self, db: AsyncSession, user_id: int) -> List[Dict]:
        """列出所有已发布模板的数据表"""
        result = await db.execute(
            select(Template).where(Template.is_published == True)
        )
        templates = result.scalars().all()

        tables = []
        for t in templates:
            config = t.config or {}
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except Exception:
                    config = {}
            table_name = config.get('table_name')

            if table_name:
                try:
                    count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.scalar() or 0
                except Exception:
                    row_count = 0

                tables.append({
                    "template_id": t.id,
                    "template_name": t.name,
                    "table_name": table_name,
                    "category": t.category,
                    "field_count": self._count_fields(t),
                    "row_count": row_count,
                    "is_owner": t.created_by == user_id,
                    "created_by": t.created_by,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                })

        return tables

    async def analyze_kflower_table(self, db: AsyncSession, table_name: str) -> TableAnalysis:
        """分析 Kflower 内部数据表结构"""
        columns = []

        # PRAGMA table_info
        try:
            col_result = await db.execute(text(f"PRAGMA table_info({table_name})"))
            for row in col_result:
                col = ColumnInfo(
                    name=row[1],
                    db_type=row[2],
                    nullable=not row[3],
                    default_value=row[4],
                    is_primary_key=bool(row[5]),
                )
                # 解析类型参数
                db_type_upper = (row[2] or '').upper()
                if '(' in db_type_upper:
                    base = db_type_upper.split('(')[0].strip()
                    param = db_type_upper.split('(')[1].split(')')[0].strip()
                    if param.isdigit():
                        col.max_length = int(param)
                columns.append(col)
        except Exception:
            pass

        # 判断唯一性（通过索引）
        try:
            idx_result = await db.execute(text(f"PRAGMA index_list({table_name})"))
            for idx_row in idx_result:
                idx_name = idx_row[1]
                is_unique = bool(idx_row[2])
                if is_unique:
                    idx_info = await db.execute(text(f"PRAGMA index_info({idx_name})"))
                    for info_row in idx_info:
                        col_name = info_row[2]
                        for col in columns:
                            if col.name == col_name:
                                col.is_unique = True
        except Exception:
            pass

        # 行数
        row_count = 0
        try:
            count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar() or 0
        except Exception:
            pass

        return TableAnalysis(
            table_name=table_name,
            columns=columns,
            row_count=row_count,
        )

    async def copy_to_template(self, db: AsyncSession, source_table_name: str,
                                new_template_name: str, current_user_id: int,
                                organization_id: int = None) -> Template:
        """从已有数据表复制为新模板"""

        # 1. 分析源表结构
        analysis = await self.analyze_kflower_table(db, source_table_name)

        # 2. 查找源模板（获取UI配置）
        source_template = None
        try:
            t_result = await db.execute(select(Template))
            for t in t_result.scalars().all():
                config = t.config or {}
                if isinstance(config, str):
                    try:
                        config = json.loads(config)
                    except Exception:
                        config = {}
                if config.get('table_name') == source_table_name:
                    source_template = t
                    break
        except Exception:
            pass

        # 3. 转换字段
        converter = ModelToTemplateConverter()
        fields = []

        for col in analysis.columns:
            # 跳过系统字段
            if col.name in ('id', 'template_id', 'created_by', 'created_at', 'updated_at'):
                continue

            # 尝试从源模板获取字段配置
            field_config = self._find_field_in_source(source_template, col.name)

            if field_config:
                fields.append(field_config)
            else:
                # 智能推断
                from app.models.data_model import DataModelField
                dummy_field = DataModelField(
                    name=col.name,
                    title=converter._auto_label(col.name),
                    db_type=col.db_type.upper().split('(')[0].strip(),
                    ui_type=None,
                    is_required=not col.nullable,
                    is_unique=col.is_unique,
                    is_primary_key=col.is_primary_key,
                    default_value=str(col.default_value) if col.default_value is not None else None,
                )
                field_dict = converter._convert_field(dummy_field)
                fields.append(field_dict)

        # 4. 创建新模板
        new_template = Template(
            name=new_template_name,
            code="form_",
            description=f"从数据表 {source_table_name} 复制创建",
            category="data_model",
            config={
                "source_type": "copy_table",
                "source_table": source_table_name,
            },
            modules=[{
                "name": source_table_name.replace("form_data_", ""),
                "label": new_template_name,
                "fields": fields
            }],
            is_published=False,
            is_public=False,
            created_by=current_user_id,
            organization_id=organization_id,
        )

        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)

        # 更新code
        new_template.code = f"form_{new_template.id}"
        await db.commit()

        return new_template

    def _find_field_in_source(self, template: Template, field_name: str) -> Optional[dict]:
        """从源模板中查找字段配置"""
        if not template or not template.modules:
            return None

        modules = template.modules
        if isinstance(modules, str):
            try:
                modules = json.loads(modules)
            except Exception:
                return None

        for mod in modules:
            if not isinstance(mod, dict):
                continue
            for f in mod.get('fields', []):
                if isinstance(f, dict) and f.get('name') == field_name:
                    return f

        return None

    @staticmethod
    def _count_fields(template: Template) -> int:
        """统计模板字段数"""
        modules = template.modules or []
        if isinstance(modules, str):
            try:
                modules = json.loads(modules)
            except Exception:
                return 0
        count = 0
        for mod in modules:
            if isinstance(mod, dict):
                count += len(mod.get('fields', []))
        return count
