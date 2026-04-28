"""
API路由 - 数据建模
支持数据模型CRUD、字段管理、关联关系、物理建表、生成模板、Kflower内部表复制、AI辅助建模
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sa_func, delete as sa_delete
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.data_model import DatabaseConnection, DataModel, DataModelField, DataModelRelation
from app.models.workflow import Template
from app.services.model_to_template import ModelToTemplateConverter
from app.services.kflower_table_analyzer import KflowerTableAnalyzer
from sqlalchemy import text

router = APIRouter(prefix="/data-models", tags=["数据建模"])


# ============ Pydantic Schemas ============

class FieldCreate(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    title: str
    db_type: str = Field(..., pattern=r"^(INTEGER|REAL|TEXT|BOOLEAN|DATE|DATETIME|JSON|BLOB)$")
    ui_type: Optional[str] = None
    is_primary_key: bool = False
    is_auto_increment: bool = False
    is_required: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: Optional[List[Dict]] = None
    placeholder: Optional[str] = None
    width: str = "100%"
    relation_config: Optional[Dict] = None


class FieldUpdate(BaseModel):
    title: Optional[str] = None
    ui_type: Optional[str] = None
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_indexed: Optional[bool] = None
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    options: Optional[List[Dict]] = None
    placeholder: Optional[str] = None
    width: Optional[str] = None
    relation_config: Optional[Dict] = None
    sort_order: Optional[int] = None


class RelationCreate(BaseModel):
    to_model_id: int
    relation_type: str = Field(..., pattern=r"^(one_to_one|one_to_many|many_to_many)$")
    from_field: str
    to_field: str = "id"
    display_field: Optional[str] = None
    reverse_name: Optional[str] = None
    on_delete: str = "set_null"
    on_update: str = "cascade"


class DataModelCreate(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    title: str
    description: Optional[str] = None
    fields: List[FieldCreate] = []


class DataModelUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class CopyTableRequest(BaseModel):
    new_template_name: str
    copy_structure_only: bool = True


class AIModelRequest(BaseModel):
    requirement: str
    model_name_hint: Optional[str] = None


class ConnectionCreate(BaseModel):
    name: str
    db_type: str = Field(..., pattern=r"^(mysql|postgresql|sqlite)$")
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict] = None


# ============ 数据模型 CRUD ============

@router.get("/models")
async def list_data_models(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出数据模型"""
    result = await db.execute(
        select(DataModel)
        .where(DataModel.created_by == current_user.id)
        .order_by(DataModel.updated_at.desc())
        .offset(skip).limit(limit)
    )
    models = result.scalars().all()

    items = []
    for m in models:
        # 统计字段数
        field_count_result = await db.execute(
            select(sa_func.count(DataModelField.id)).where(DataModelField.model_id == m.id)
        )
        field_count = field_count_result.scalar() or 0

        # 关联模板名
        template_name = None
        if m.template_id:
            t_result = await db.execute(select(Template).where(Template.id == m.template_id))
            t = t_result.scalar_one_or_none()
            template_name = t.name if t else None

        items.append({
            "id": m.id,
            "name": m.name,
            "title": m.title,
            "description": m.description,
            "source_type": m.source_type,
            "is_created": m.is_created,
            "table_name": m.table_name,
            "template_id": m.template_id,
            "template_name": template_name,
            "field_count": field_count,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        })

    # 总数
    count_result = await db.execute(
        select(sa_func.count(DataModel.id)).where(DataModel.created_by == current_user.id)
    )
    total = count_result.scalar() or 0

    return {"success": True, "data": items, "total": total}


@router.get("/models/{model_id}")
async def get_data_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据模型详情"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问")

    # 字段列表
    fields_result = await db.execute(
        select(DataModelField)
        .where(DataModelField.model_id == model_id)
        .order_by(DataModelField.sort_order, DataModelField.id)
    )
    fields = fields_result.scalars().all()

    # 关联关系
    rels_result = await db.execute(
        select(DataModelRelation).where(
            (DataModelRelation.from_model_id == model_id) |
            (DataModelRelation.to_model_id == model_id)
        )
    )
    relations = rels_result.scalars().all()

    # 关联模板信息
    template_name = None
    if model.template_id:
        t_result = await db.execute(select(Template).where(Template.id == model.template_id))
        t = t_result.scalar_one_or_none()
        template_name = t.name if t else None

    return {
        "success": True,
        "data": {
            "id": model.id,
            "name": model.name,
            "title": model.title,
            "description": model.description,
            "source_type": model.source_type,
            "source_table_name": model.source_table_name,
            "is_created": model.is_created,
            "table_name": model.table_name,
            "template_id": model.template_id,
            "template_name": template_name,
            "config": model.config or {},
            "fields": [
                {
                    "id": f.id,
                    "name": f.name,
                    "title": f.title,
                    "description": f.description,
                    "db_type": f.db_type,
                    "ui_type": f.ui_type,
                    "is_primary_key": f.is_primary_key,
                    "is_auto_increment": f.is_auto_increment,
                    "is_required": f.is_required,
                    "is_unique": f.is_unique,
                    "is_indexed": f.is_indexed,
                    "is_system": f.is_system,
                    "default_value": f.default_value,
                    "max_length": f.max_length,
                    "min_value": f.min_value,
                    "max_value": f.max_value,
                    "options": f.options or [],
                    "placeholder": f.placeholder,
                    "width": f.width,
                    "relation_config": f.relation_config or {},
                    "sort_order": f.sort_order,
                    "ai_suggested": f.ai_suggested,
                }
                for f in fields
            ],
            "relations": [
                {
                    "id": r.id,
                    "from_model_id": r.from_model_id,
                    "to_model_id": r.to_model_id,
                    "relation_type": r.relation_type,
                    "from_field": r.from_field,
                    "to_field": r.to_field,
                    "display_field": r.display_field,
                    "reverse_name": r.reverse_name,
                    "on_delete": r.on_delete,
                }
                for r in relations
            ],
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }
    }


@router.post("/models")
async def create_data_model(
    request: DataModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建数据模型"""
    model = DataModel(
        name=request.name,
        title=request.title,
        description=request.description,
        source_type="manual",
        created_by=current_user.id,
        organization_id=current_user.organization_id,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    # 创建字段
    for idx, f in enumerate(request.fields):
        field = DataModelField(
            model_id=model.id,
            name=f.name,
            title=f.title,
            db_type=f.db_type,
            ui_type=f.ui_type,
            is_primary_key=f.is_primary_key,
            is_auto_increment=f.is_auto_increment,
            is_required=f.is_required,
            is_unique=f.is_unique,
            is_indexed=f.is_indexed,
            default_value=f.default_value,
            max_length=f.max_length,
            min_value=f.min_value,
            max_value=f.max_value,
            options=f.options or [],
            placeholder=f.placeholder,
            width=f.width,
            relation_config=f.relation_config or {},
            sort_order=idx,
        )
        db.add(field)

    await db.commit()

    return {"success": True, "message": "数据模型创建成功", "data": {"id": model.id}}


@router.put("/models/{model_id}")
async def update_data_model(
    model_id: int,
    request: DataModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据模型基本信息"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    if request.title is not None:
        model.title = request.title
    if request.description is not None:
        model.description = request.description

    await db.commit()
    return {"success": True, "message": "更新成功"}


@router.delete("/models/{model_id}")
async def delete_data_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据模型（同时删除字段和关联关系）"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除")

    # 级联删除字段和关联
    await db.execute(sa_delete(DataModelField).where(DataModelField.model_id == model_id))
    await db.execute(sa_delete(DataModelRelation).where(
        (DataModelRelation.from_model_id == model_id) |
        (DataModelRelation.to_model_id == model_id)
    ))
    await db.delete(model)
    await db.commit()

    return {"success": True, "message": "删除成功"}


# ============ 字段管理 ============

@router.post("/models/{model_id}/fields")
async def add_model_field(
    model_id: int,
    request: FieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加字段（如果已建表则自动 ALTER TABLE ADD COLUMN）"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    # 获取当前最大排序号
    max_order_result = await db.execute(
        select(sa_func.max(DataModelField.sort_order)).where(DataModelField.model_id == model_id)
    )
    max_order = max_order_result.scalar() or 0

    field = DataModelField(
        model_id=model_id,
        name=request.name,
        title=request.title,
        db_type=request.db_type,
        ui_type=request.ui_type,
        is_primary_key=request.is_primary_key,
        is_auto_increment=request.is_auto_increment,
        is_required=request.is_required,
        is_unique=request.is_unique,
        is_indexed=request.is_indexed,
        default_value=request.default_value,
        max_length=request.max_length,
        min_value=request.min_value,
        max_value=request.max_value,
        options=request.options or [],
        placeholder=request.placeholder,
        width=request.width,
        relation_config=request.relation_config or {},
        sort_order=max_order + 1,
    )
    db.add(field)
    await db.commit()
    await db.refresh(field)

    # 如果已建表，同步 ALTER TABLE ADD COLUMN
    base_column_names = {'id', 'template_id', 'created_by', 'created_at', 'updated_by', 'updated_at'}
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in request.name)
    if safe_name[0].isdigit():
        safe_name = 'f_' + safe_name

    if model.is_created and model.table_name and safe_name not in base_column_names and request.db_type.upper() != 'JSON':
        try:
            converter = ModelToTemplateConverter()
            sqlite_type = converter.db_type_to_sqlite(request.db_type, request.max_length)
            alter_sql = f'ALTER TABLE {model.table_name} ADD COLUMN "{safe_name}" {sqlite_type}'
            if request.default_value is not None:
                alter_sql += f" DEFAULT '{request.default_value}'"
            elif not request.is_required:
                # SQLite ADD COLUMN: 非必填字段不加约束，用默认NULL
                pass
            await db.execute(text(alter_sql))
            await db.commit()
        except Exception as e:
            # ALTER失败不阻塞字段添加，只记录警告
            import logging
            logging.getLogger(__name__).warning(f"ALTER TABLE ADD COLUMN failed for {safe_name}: {e}")

    # 如果已生成模板，同步更新模板
    if model.template_id:
        await _sync_template_after_field_change(model, db)

    return {"success": True, "message": "字段添加成功" + ("，物理表已同步" if model.is_created else ""), "data": {"id": field.id}}


@router.put("/models/{model_id}/fields/{field_id}")
async def update_model_field(
    model_id: int,
    field_id: int,
    request: FieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新字段"""
    result = await db.execute(
        select(DataModelField).where(
            DataModelField.id == field_id,
            DataModelField.model_id == model_id
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")

    # 更新非None字段
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(field, key, value)

    await db.commit()

    # 如果已生成模板，同步更新模板（UI类型、选项等变更会影响表单渲染）
    model_result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = model_result.scalar_one_or_none()
    if model and model.template_id:
        await _sync_template_after_field_change(model, db)

    return {"success": True, "message": "字段更新成功"}


@router.delete("/models/{model_id}/fields/{field_id}")
async def delete_model_field(
    model_id: int,
    field_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除字段（SQLite不支持DROP COLUMN，但保留元数据不阻塞）"""
    result = await db.execute(
        select(DataModelField).where(
            DataModelField.id == field_id,
            DataModelField.model_id == model_id
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")
    if field.is_system:
        raise HTTPException(status_code=400, detail="系统字段不可删除")

    # 获取模型信息
    model_result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = model_result.scalar_one_or_none()

    field_name = field.name
    await db.delete(field)
    await db.commit()

    # SQLite < 3.35 不支持 DROP COLUMN，3.35+ 支持
    # 尝试 ALTER TABLE DROP COLUMN，失败则跳过（列留在物理表中但不再显示）
    if model and model.is_created and model.table_name:
        base_column_names = {'id', 'template_id', 'created_by', 'created_at', 'updated_by', 'updated_at'}
        if field_name not in base_column_names:
            try:
                alter_sql = f'ALTER TABLE {model.table_name} DROP COLUMN "{field_name}"'
                await db.execute(text(alter_sql))
                await db.commit()
            except Exception as e:
                # SQLite版本过低不支持DROP COLUMN，不阻塞，列留在表中但不映射
                import logging
                logging.getLogger(__name__).warning(f"ALTER TABLE DROP COLUMN failed for {field_name}: {e}")

    # 同步更新模板
    if model and model.template_id:
        await _sync_template_after_field_change(model, db)

    return {"success": True, "message": "字段删除成功"}


# ============ 关联关系 ============

@router.post("/models/{model_id}/relations")
async def add_model_relation(
    model_id: int,
    request: RelationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加关联关系"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改")

    # 验证目标模型存在
    target_result = await db.execute(select(DataModel).where(DataModel.id == request.to_model_id))
    if not target_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="目标数据模型不存在")

    relation = DataModelRelation(
        from_model_id=model_id,
        to_model_id=request.to_model_id,
        relation_type=request.relation_type,
        from_field=request.from_field,
        to_field=request.to_field,
        display_field=request.display_field,
        reverse_name=request.reverse_name,
        on_delete=request.on_delete,
        on_update=request.on_update,
    )
    db.add(relation)
    await db.commit()
    await db.refresh(relation)

    return {"success": True, "message": "关联关系添加成功", "data": {"id": relation.id}}


@router.delete("/models/{model_id}/relations/{relation_id}")
async def delete_model_relation(
    model_id: int,
    relation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除关联关系"""
    result = await db.execute(
        select(DataModelRelation).where(DataModelRelation.id == relation_id)
    )
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=404, detail="关联关系不存在")

    await db.delete(relation)
    await db.commit()
    return {"success": True, "message": "关联关系删除成功"}


# ============ 模板同步辅助 ============

async def _sync_template_after_field_change(model: DataModel, db: AsyncSession):
    """字段变更后同步更新已生成的模板"""
    if not model.template_id:
        return

    # 获取模板
    t_result = await db.execute(select(Template).where(Template.id == model.template_id))
    template = t_result.scalar_one_or_none()
    if not template:
        return

    # 获取当前字段
    fields_result = await db.execute(
        select(DataModelField).where(DataModelField.model_id == model.id)
        .order_by(DataModelField.sort_order)
    )
    fields = fields_result.scalars().all()

    # 获取关联关系
    rels_result = await db.execute(
        select(DataModelRelation).where(DataModelRelation.from_model_id == model.id)
    )
    relations = rels_result.scalars().all()

    # 重新转换
    converter = ModelToTemplateConverter()
    template_data = converter.convert(model, fields, relations)

    # 保留原有表名和发布状态
    old_config = template.config or {}
    if isinstance(old_config, str):
        old_config = json.loads(old_config)
    template_data["config"]["table_name"] = old_config.get("table_name", model.table_name)

    # 更新模板
    template.config = template_data["config"]
    template.modules = template_data["modules"]
    template.name = template_data["name"]
    if template_data.get("description"):
        template.description = template_data["description"]

    await db.commit()


@router.post("/models/{model_id}/sync-table")
async def sync_physical_table(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同步物理表：将模型当前字段与物理表对齐（添加缺失列）"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if not model.is_created or not model.table_name:
        raise HTTPException(status_code=400, detail="尚未建表，无法同步")

    # 获取当前字段
    fields_result = await db.execute(
        select(DataModelField).where(DataModelField.model_id == model_id)
        .order_by(DataModelField.sort_order)
    )
    fields = fields_result.scalars().all()

    # 获取物理表现有列
    try:
        pragma_result = await db.execute(text(f"PRAGMA table_info({model.table_name})"))
        existing_columns = {row[1] for row in pragma_result.fetchall()}
    except Exception:
        existing_columns = set()

    converter = ModelToTemplateConverter()
    base_column_names = {'id', 'template_id', 'created_by', 'created_at', 'updated_by', 'updated_at'}
    added = []

    for f in fields:
        if f.is_primary_key and f.is_auto_increment:
            continue
        if f.db_type.upper() == 'JSON':
            continue
        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in f.name)
        if safe_name[0].isdigit():
            safe_name = 'f_' + safe_name
        if safe_name in base_column_names:
            continue
        if safe_name in existing_columns:
            continue  # 列已存在，跳过

        # 添加缺失的列
        sqlite_type = converter.db_type_to_sqlite(f.db_type, f.max_length)
        alter_sql = f'ALTER TABLE {model.table_name} ADD COLUMN "{safe_name}" {sqlite_type}'
        if f.default_value is not None:
            alter_sql += f" DEFAULT '{f.default_value}'"
        try:
            await db.execute(text(alter_sql))
            added.append(safe_name)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"ALTER TABLE ADD COLUMN failed for {safe_name}: {e}")

    if added:
        await db.commit()

    # 同步模板
    if model.template_id:
        await _sync_template_after_field_change(model, db)

    return {
        "success": True,
        "message": f"同步完成，新增 {len(added)} 个列" + (f": {', '.join(added)}" if added else ""),
        "data": {"added_columns": added},
    }


# ============ 生成操作 ============

@router.post("/models/{model_id}/create-table")
async def create_physical_table(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建物理数据表"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")

    if model.is_created and model.table_name:
        return {"success": True, "message": "数据表已存在", "data": {"table_name": model.table_name}}

    # 获取字段
    fields_result = await db.execute(
        select(DataModelField).where(DataModelField.model_id == model_id)
        .order_by(DataModelField.sort_order)
    )
    fields = fields_result.scalars().all()

    if not fields:
        raise HTTPException(status_code=400, detail="数据模型没有字段，无法建表")

    # 构建表名
    table_name = f"form_data_dm_{model_id}"
    converter = ModelToTemplateConverter()

    # 构建CREATE TABLE
    columns = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "template_id INTEGER",
        "created_by INTEGER",
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
    ]

    # 基础列名集合，跳过与基础列同名的用户字段
    base_column_names = {'id', 'template_id', 'created_by', 'created_at', 'updated_by', 'updated_at'}

    for f in fields:
        if f.is_primary_key and f.is_auto_increment:
            continue  # 主键自增由id列承担
        if f.db_type.upper() == 'JSON':
            continue  # JSON类型暂不入主表

        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in f.name)
        if safe_name[0].isdigit():
            safe_name = 'f_' + safe_name
        if safe_name in base_column_names:
            continue  # 跳过与基础列同名的字段，避免重复

        sqlite_type = converter.db_type_to_sqlite(f.db_type, f.max_length)
        col_def = f'"{safe_name}" {sqlite_type}'

        if f.is_required and not f.is_primary_key:
            col_def += ' NOT NULL'
        if f.is_unique:
            col_def += ' UNIQUE'
        if f.default_value is not None:
            col_def += f" DEFAULT '{f.default_value}'"

        columns.append(col_def)

    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

    try:
        await db.execute(text(create_sql))
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建数据表失败: {str(e)}")

    # 更新模型状态
    model.is_created = True
    model.table_name = table_name
    config = model.config or {}
    if isinstance(config, str):
        config = json.loads(config)
    config['table_name'] = table_name
    model.config = config

    await db.commit()

    return {"success": True, "message": "数据表创建成功", "data": {"table_name": table_name}}


@router.post("/models/{model_id}/generate-template")
async def generate_template_from_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从数据模型生成 Kflower 模板"""
    result = await db.execute(select(DataModel).where(DataModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="数据模型不存在")
    if model.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")

    # 获取字段和关联
    fields_result = await db.execute(
        select(DataModelField).where(DataModelField.model_id == model_id)
        .order_by(DataModelField.sort_order)
    )
    fields = fields_result.scalars().all()

    rels_result = await db.execute(
        select(DataModelRelation).where(DataModelRelation.from_model_id == model_id)
    )
    relations = rels_result.scalars().all()

    if not fields:
        raise HTTPException(status_code=400, detail="数据模型没有字段，无法生成模板")

    # 先创建物理表（如果还没创建）
    if not model.is_created:
        table_name = f"form_data_dm_{model_id}"
    else:
        table_name = model.table_name

    # 转换
    converter = ModelToTemplateConverter()
    template_data = converter.convert(model, fields, relations)

    # 确保表名写入config
    template_data["config"]["table_name"] = table_name

    # 创建模板
    new_template = Template(
        name=template_data["name"],
        code=f"dm_{model_id}",
        description=template_data.get("description", ""),
        category="data_model",
        config=template_data["config"],
        modules=template_data["modules"],
        is_published=True,  # 数据建模生成的模板直接发布（已有物理表）
        is_public=False,
        created_by=current_user.id,
        organization_id=current_user.organization_id,
    )
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    # 更新code
    new_template.code = f"form_{new_template.id}"
    await db.commit()

    # 如果还没建表，先建表
    if not model.is_created:
        columns = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "template_id INTEGER",
            "created_by INTEGER",
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        ]
        base_column_names = {'id', 'template_id', 'created_by', 'created_at', 'updated_by', 'updated_at'}
        for f in fields:
            if f.is_primary_key and f.is_auto_increment:
                continue
            if f.db_type.upper() == 'JSON':
                continue
            safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in f.name)
            if safe_name[0].isdigit():
                safe_name = 'f_' + safe_name
            if safe_name in base_column_names:
                continue  # 跳过与基础列同名的字段
            sqlite_type = converter.db_type_to_sqlite(f.db_type, f.max_length)
            col_def = f'"{safe_name}" {sqlite_type}'
            if f.is_required and not f.is_primary_key:
                col_def += ' NOT NULL'
            if f.is_unique:
                col_def += ' UNIQUE'
            columns.append(col_def)

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        try:
            await db.execute(text(create_sql))
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建数据表失败: {str(e)}")

        # 更新模板config中的table_name
        t_config = new_template.config or {}
        if isinstance(t_config, str):
            t_config = json.loads(t_config)
        t_config['table_name'] = table_name
        new_template.config = t_config
        await db.commit()

        model.is_created = True
        model.table_name = table_name

    # 关联模板
    model.template_id = new_template.id
    await db.commit()

    return {
        "success": True,
        "message": "模板生成成功",
        "data": {
            "template_id": new_template.id,
            "template_name": new_template.name,
            "table_name": table_name,
        }
    }


# ============ Kflower 内部表复制 ============

@router.get("/kflower-tables")
async def list_kflower_tables(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出 Kflower 内部已发布的数据表"""
    analyzer = KflowerTableAnalyzer()
    tables = await analyzer.list_published_tables(db, current_user.id)
    return {"success": True, "data": tables}


@router.post("/kflower-tables/{table_name}/copy-to-template")
async def copy_kflower_table(
    table_name: str,
    request: CopyTableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从 Kflower 内部数据表复制为新模板"""
    # 安全检查：只允许 form_data_ 开头的表名
    if not table_name.startswith("form_data_"):
        raise HTTPException(status_code=400, detail="只允许复制 Kflower 内部数据表")

    analyzer = KflowerTableAnalyzer()
    try:
        new_template = await analyzer.copy_to_template(
            db, table_name, request.new_template_name,
            current_user.id, current_user.organization_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"复制失败: {str(e)}")

    return {
        "success": True,
        "message": "复制成功",
        "data": {"template_id": new_template.id, "template_name": new_template.name}
    }


# ============ 数据库连接管理 ============

@router.post("/connections")
async def create_connection(
    request: ConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建数据库连接"""
    # 简单加密密码（生产环境应使用AES）
    pwd_encrypted = request.password if request.password else None

    conn = DatabaseConnection(
        name=request.name,
        db_type=request.db_type,
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password_encrypted=pwd_encrypted,
        config=request.config or {},
        created_by=current_user.id,
        organization_id=current_user.organization_id,
    )
    db.add(conn)
    await db.commit()
    await db.refresh(conn)

    return {"success": True, "message": "连接创建成功", "data": {"id": conn.id}}


@router.get("/connections")
async def list_connections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出数据库连接"""
    result = await db.execute(
        select(DatabaseConnection)
        .where(DatabaseConnection.created_by == current_user.id)
        .order_by(DatabaseConnection.updated_at.desc())
    )
    connections = result.scalars().all()

    items = []
    for c in connections:
        items.append({
            "id": c.id,
            "name": c.name,
            "db_type": c.db_type,
            "host": c.host,
            "port": c.port,
            "database": c.database,
            "username": c.username,
            "is_active": c.is_active,
            "last_test_result": c.last_test_result,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"success": True, "data": items}


@router.post("/connections/{conn_id}/test")
async def test_connection(
    conn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试数据库连接"""
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")

    try:
        if conn.db_type == "sqlite":
            import sqlite3
            c = sqlite3.connect(conn.database or conn.host)
            c.execute("SELECT 1")
            c.close()
        elif conn.db_type == "mysql":
            import pymysql
            c = pymysql.connect(
                host=conn.host, port=conn.port or 3306,
                user=conn.username, password=conn.password_encrypted or '',
                database=conn.database
            )
            c.close()
        elif conn.db_type == "postgresql":
            import psycopg2
            c = psycopg2.connect(
                host=conn.host, port=conn.port or 5432,
                user=conn.username, password=conn.password_encrypted or '',
                dbname=conn.database
            )
            c.close()
        else:
            raise Exception(f"不支持的数据库类型: {conn.db_type}")

        conn.last_test_at = datetime.now()
        conn.last_test_result = "success"
        conn.is_active = True
        await db.commit()

        return {"success": True, "message": "连接测试成功"}
    except Exception as e:
        conn.last_test_at = datetime.now()
        conn.last_test_result = "failed"
        await db.commit()

        return {"success": False, "message": f"连接测试失败: {str(e)}"}


@router.delete("/connections/{conn_id}")
async def delete_connection(
    conn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据库连接"""
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")

    await db.delete(conn)
    await db.commit()
    return {"success": True, "message": "连接删除成功"}


# ============ 外部数据库导入 ============

@router.get("/connections/{conn_id}/tables")
async def list_external_tables(
    conn_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出外部数据库的表"""
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")

    try:
        if conn.db_type == "sqlite":
            import sqlite3
            c = sqlite3.connect(conn.database or conn.host)
            cursor = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = [{"name": row[0], "comment": "", "row_count": 0} for row in cursor.fetchall()]
            # 获取行数
            for t in tables:
                try:
                    cnt = c.execute(f"SELECT COUNT(*) FROM [{t['name']}]").fetchone()
                    t["row_count"] = cnt[0] if cnt else 0
                except Exception:
                    pass
            c.close()
        elif conn.db_type == "mysql":
            try:
                import pymysql
                c = pymysql.connect(
                    host=conn.host, port=conn.port or 3306,
                    user=conn.username, password=conn.password_encrypted or '',
                    database=conn.database, charset='utf8mb4'
                )
                cursor = c.cursor()
                cursor.execute("""
                    SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME
                """, (conn.database,))
                tables = [
                    {"name": row[0], "comment": row[1] or "", "row_count": row[2] or 0}
                    for row in cursor.fetchall()
                ]
                c.close()
            except ImportError:
                raise HTTPException(status_code=500, detail="需要安装 pymysql: pip install pymysql")
        elif conn.db_type == "postgresql":
            try:
                import psycopg2
                c = psycopg2.connect(
                    host=conn.host, port=conn.port or 5432,
                    user=conn.username, password=conn.password_encrypted or '',
                    dbname=conn.database
                )
                cursor = c.cursor()
                cursor.execute("""
                    SELECT tablename,
                           obj_description((schemaname||'.'||tablename)::regclass) AS comment
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)
                tables = [
                    {"name": row[0], "comment": row[1] or "", "row_count": 0}
                    for row in cursor.fetchall()
                ]
                c.close()
            except ImportError:
                raise HTTPException(status_code=500, detail="需要安装 psycopg2: pip install psycopg2-binary")
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据库类型: {conn.db_type}")

        return {"success": True, "data": tables}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据表列表失败: {str(e)}")


@router.get("/connections/{conn_id}/tables/{table_name}/schema")
async def get_external_table_schema(
    conn_id: int,
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取外部数据表结构"""
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")

    converter = ModelToTemplateConverter()

    try:
        if conn.db_type == "sqlite":
            import sqlite3
            c = sqlite3.connect(conn.database or conn.host)
            # 获取列信息
            col_cursor = c.execute(f"PRAGMA table_info([{table_name}])")
            columns = []
            for row in col_cursor.fetchall():
                db_type_upper = (row[2] or '').upper().split('(')[0].strip()
                col = {
                    "name": row[1],
                    "db_type": db_type_upper,
                    "nullable": not row[3],
                    "default_value": str(row[4]) if row[4] is not None else None,
                    "is_primary_key": bool(row[5]),
                    "ui_type": None,
                    "title": converter._auto_label(row[1]),
                }
                # 智能推断UI类型
                from app.models.data_model import DataModelField
                dummy = DataModelField(name=col["name"], db_type=col["db_type"])
                col["ui_type"] = converter._determine_ui_type(dummy)
                columns.append(col)
            c.close()

        elif conn.db_type == "mysql":
            try:
                import pymysql
                c = pymysql.connect(
                    host=conn.host, port=conn.port or 3306,
                    user=conn.username, password=conn.password_encrypted or '',
                    database=conn.database, charset='utf8mb4'
                )
                cursor = c.cursor()
                cursor.execute("""
                    SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
                           COLUMN_KEY, COLUMN_COMMENT
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (conn.database, table_name))
                columns = []
                for row in cursor.fetchall():
                    db_type_raw = (row[1] or '').upper()
                    db_type_upper = db_type_raw.split('(')[0].strip()
                    col = {
                        "name": row[0],
                        "db_type": db_type_upper,
                        "nullable": row[2] == 'YES',
                        "default_value": str(row[3]) if row[3] is not None else None,
                        "is_primary_key": row[4] == 'PRI',
                        "ui_type": None,
                        "title": row[5] or converter._auto_label(row[0]),
                        "comment": row[5],
                    }
                    from app.models.data_model import DataModelField
                    dummy = DataModelField(name=col["name"], db_type=col["db_type"])
                    col["ui_type"] = converter._determine_ui_type(dummy)
                    columns.append(col)
                c.close()
            except ImportError:
                raise HTTPException(status_code=500, detail="需要安装 pymysql")
        else:
            raise HTTPException(status_code=400, detail=f"暂不支持 {conn.db_type}")

        return {"success": True, "data": {"table_name": table_name, "columns": columns}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表结构失败: {str(e)}")


@router.post("/connections/{conn_id}/import")
async def import_external_tables(
    conn_id: int,
    table_names: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从外部数据库导入表 → 生成数据模型 → 生成模板"""
    result = await db.execute(select(DatabaseConnection).where(DatabaseConnection.id == conn_id))
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="连接不存在")

    converter = ModelToTemplateConverter()
    imported = []

    for tbl_name in table_names:
        # 获取表结构
        schema_result = await get_external_table_schema(conn_id, tbl_name, db, current_user)
        schema_data = schema_result.get("data", {})
        columns = schema_data.get("columns", [])

        # 创建数据模型
        model = DataModel(
            name=tbl_name,
            title=converter._auto_label(tbl_name),
            source_type="import_db",
            source_connection_id=conn_id,
            source_table_name=tbl_name,
            created_by=current_user.id,
            organization_id=current_user.organization_id,
        )
        db.add(model)
        await db.commit()
        await db.refresh(model)

        # 创建字段
        db_type_map = {
            "INT": "INTEGER", "INTEGER": "INTEGER", "BIGINT": "INTEGER",
            "REAL": "REAL", "FLOAT": "REAL", "DOUBLE": "REAL",
            "DECIMAL": "REAL", "NUMERIC": "REAL",
            "VARCHAR": "TEXT", "CHAR": "TEXT", "TEXT": "TEXT",
            "LONGTEXT": "TEXT", "MEDIUMTEXT": "TEXT",
            "DATE": "DATE", "DATETIME": "DATETIME", "TIMESTAMP": "DATETIME",
            "BOOLEAN": "BOOLEAN", "BOOL": "BOOLEAN",
            "BLOB": "BLOB", "JSON": "JSON",
        }

        for idx, col in enumerate(columns):
            raw_type = col.get("db_type", "TEXT").upper()
            mapped_type = db_type_map.get(raw_type, "TEXT")

            field = DataModelField(
                model_id=model.id,
                name=col["name"],
                title=col.get("title") or converter._auto_label(col["name"]),
                db_type=mapped_type,
                ui_type=col.get("ui_type", "text"),
                is_primary_key=col.get("is_primary_key", False),
                is_required=not col.get("nullable", True),
                default_value=col.get("default_value"),
                sort_order=idx,
            )
            db.add(field)

        await db.commit()
        imported.append({"model_id": model.id, "name": tbl_name})

    return {"success": True, "message": f"成功导入 {len(imported)} 个数据表", "data": imported}


# ============ AI 辅助建模 ============

@router.post("/ai/generate")
async def ai_generate_model(
    request: AIModelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI生成数据模型"""
    from app.core.config import settings
    import httpx

    prompt = f"""你是一个数据建模专家。根据用户的需求描述，设计数据表结构。

要求：
1. 输出严格的JSON格式，不要包含markdown代码块标记
2. 每个表包含完整的字段定义
3. 字段类型必须是以下之一: INTEGER, REAL, TEXT, BOOLEAN, DATE, DATETIME, JSON, BLOB
4. ui_type必须是以下之一: text, number, date, datetime, select, radio, checkbox, switch, upload, image, relation, subform
5. 合理设置必填、唯一、默认值
6. 为select/radio/checkbox类型提供合理的options
7. 自动识别表间关联关系

输出格式：
{{
  "models": [
    {{
      "name": "表名(英文小写下划线)",
      "title": "显示名(中文)",
      "description": "描述",
      "fields": [
        {{
          "name": "字段名",
          "title": "显示名",
          "db_type": "数据库类型",
          "ui_type": "UI控件类型",
          "is_primary_key": false,
          "is_auto_increment": false,
          "is_required": true,
          "is_unique": false,
          "default_value": null,
          "options": [],
          "description": "字段说明"
        }}
      ]
    }}
  ],
  "relations": [
    {{
      "from_model": "orders",
      "to_model": "customers",
      "relation_type": "one_to_many",
      "from_field": "customer_id",
      "to_field": "id",
      "display_field": "name"
    }}
  ]
}}

用户需求：{request.requirement}"""

    # 调用AI
    try:
        ai_base = settings.SILICONFLOW_API_BASE
        ai_key = settings.SILICONFLOW_API_KEY
        ai_model = settings.SILICONFLOW_MODEL

        if not ai_key:
            # 尝试其他提供商
            if settings.DEEPSEEK_API_KEY:
                ai_base = settings.DEEPSEEK_API_BASE
                ai_key = settings.DEEPSEEK_API_KEY
                ai_model = settings.DEEPSEEK_MODEL
            elif settings.QWEN_API_KEY:
                ai_base = settings.QWEN_API_BASE
                ai_key = settings.QWEN_API_KEY
                ai_model = settings.QWEN_MODEL

        if not ai_key:
            raise HTTPException(status_code=500, detail="未配置AI API Key")

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{ai_base}/chat/completions",
                headers={"Authorization": f"Bearer {ai_key}"},
                json={
                    "model": ai_model,
                    "messages": [
                        {"role": "system", "content": "你是数据建模专家，只输出纯JSON，不要任何解释或markdown标记。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                }
            )
            resp.raise_for_status()
            ai_result = resp.json()

        content = ai_result["choices"][0]["message"]["content"].strip()
        # 去掉可能的markdown代码块标记
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        import json as _json
        model_data = _json.loads(content)

        # 创建数据模型和字段
        created_models = []
        model_name_map = {}  # name → id 映射，用于后续创建关联

        for md in model_data.get("models", []):
            model_name = md.get("name", request.model_name_hint or "table_1")
            model = DataModel(
                name=model_name,
                title=md.get("title", model_name),
                description=md.get("description", ""),
                source_type="ai",
                created_by=current_user.id,
                organization_id=current_user.organization_id,
            )
            db.add(model)
            await db.commit()
            await db.refresh(model)
            model_name_map[model_name] = model.id

            # 创建字段
            for idx, fd in enumerate(md.get("fields", [])):
                field = DataModelField(
                    model_id=model.id,
                    name=fd.get("name", f"field_{idx}"),
                    title=fd.get("title", fd.get("name", f"字段{idx}")),
                    description=fd.get("description", ""),
                    db_type=fd.get("db_type", "TEXT"),
                    ui_type=fd.get("ui_type", "text"),
                    is_primary_key=fd.get("is_primary_key", False),
                    is_auto_increment=fd.get("is_auto_increment", False),
                    is_required=fd.get("is_required", False),
                    is_unique=fd.get("is_unique", False),
                    default_value=str(fd["default_value"]) if fd.get("default_value") is not None else None,
                    options=fd.get("options", []),
                    ai_suggested=True,
                    ai_confidence=0.8,
                    sort_order=idx,
                )
                db.add(field)

            created_models.append({"model_id": model.id, "name": model_name, "title": md.get("title", model_name)})

        await db.commit()

        # 创建关联关系
        created_relations = []
        for rel in model_data.get("relations", []):
            from_name = rel.get("from_model", "")
            to_name = rel.get("to_model", "")
            from_id = model_name_map.get(from_name)
            to_id = model_name_map.get(to_name)
            if from_id and to_id:
                relation = DataModelRelation(
                    from_model_id=from_id,
                    to_model_id=to_id,
                    relation_type=rel.get("relation_type", "one_to_many"),
                    from_field=rel.get("from_field", f"{to_name}_id"),
                    to_field=rel.get("to_field", "id"),
                    display_field=rel.get("display_field", "name"),
                )
                db.add(relation)
                created_relations.append({
                    "from": from_name, "to": to_name,
                    "type": rel.get("relation_type", "one_to_many")
                })

        await db.commit()

        return {
            "success": True,
            "message": f"AI建模成功，生成 {len(created_models)} 个数据模型",
            "data": {
                "models": created_models,
                "relations": created_relations,
            }
        }

    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI返回的数据格式错误: {str(e)}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"AI服务调用失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI建模失败: {str(e)}")


# ============ 统计信息 ============

@router.get("/stats")
async def get_data_modeling_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据建模统计"""
    # 模型总数
    model_count = await db.execute(
        select(sa_func.count(DataModel.id)).where(DataModel.created_by == current_user.id)
    )
    total_models = model_count.scalar() or 0

    # 已建表数
    created_count = await db.execute(
        select(sa_func.count(DataModel.id)).where(
            DataModel.created_by == current_user.id,
            DataModel.is_created == True
        )
    )
    total_created = created_count.scalar() or 0

    # 已生成模板数
    template_count = await db.execute(
        select(sa_func.count(DataModel.id)).where(
            DataModel.created_by == current_user.id,
            DataModel.template_id != None
        )
    )
    total_templates = template_count.scalar() or 0

    # 连接数
    conn_count = await db.execute(
        select(sa_func.count(DatabaseConnection.id)).where(DatabaseConnection.created_by == current_user.id)
    )
    total_connections = conn_count.scalar() or 0

    return {
        "success": True,
        "data": {
            "total_models": total_models,
            "total_created": total_created,
            "total_templates": total_templates,
            "total_connections": total_connections,
        }
    }
