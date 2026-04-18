"""
API路由 - 模板管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete as sa_delete, String
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Template, TemplateInstance
from app.schemas.schemas import (
    TemplateCreate, TemplateUpdate, TemplateResponse, BaseResponse,
    TemplateDataSubmit, TemplateDataUpdate, TemplateDataResponse, TemplateStatsResponse
)
from pydantic import BaseModel as PydanticBaseModel

router = APIRouter(prefix="/templates", tags=["模板管理"])


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板列表 - 只显示自己有权限访问的模板"""
    # 权限规则：自己创建的 OR (已发布且公开的)
    query = select(Template).where(
        (Template.created_by == current_user.id) | 
        ((Template.is_published == True) & (Template.is_public == True))
    )
    
    if category:
        query = query.where(Template.category == category)
    
    if search:
        query = query.where(
            (Template.name.contains(search)) | 
            (Template.description.contains(search))
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            code=t.code,
            description=t.description,
            category=t.category,
            config=t.config or {},
            modules=t.modules or [],
            ai_generated=t.ai_generated,
            is_published=t.is_published,
            is_public=t.is_public,
            created_at=t.created_at,
            created_by=t.created_by
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        code=template.code,
        description=template.description,
        category=template.category,
        config=template.config or {},
        modules=template.modules or [],
        ai_generated=template.ai_generated,
        is_published=template.is_published,
        created_at=template.created_at,
        created_by=template.created_by
    )


@router.post("/", response_model=TemplateResponse)
async def create_template(
    request: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模板 - 编码自动生成"""
    # 生成编码：form_{id}，先占位，创建后再更新
    code = f"form_"  # 临时编码，创建后更新为 form_{id}
    
    # 处理 modules - 支持字段级别的完整属性
    modules_data = []
    if request.modules:
        for m in request.modules:
            mod_dict = {
                "name": m.name,
                "label": getattr(m, 'label', None) or m.name,
            }
            fields_list = []
            for f in m.fields:
                field_dict = f.dict()
                # 移除前端专用字段 _key
                field_dict.pop('_key', None)
                field_dict.pop('_value', None)
                fields_list.append(field_dict)
            mod_dict["fields"] = fields_list
            modules_data.append(mod_dict)
    
    template = Template(
        name=request.name,
        code=code,
        description=request.description,
        category=request.category,
        config=request.config or {},
        modules=modules_data,
        ai_generated=request.ai_generated,
        ai_prompt=request.ai_prompt,
        is_published=False,  # 默认草稿状态，点发布后才为True
        is_public=False,     # 默认私有，点共享后才公开
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    # 创建后更新编码为 form_{id}
    template.code = f"form_{template.id}"
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        code=template.code,
        description=template.description,
        category=template.category,
        config=template.config or {},
        modules=template.modules or [],
        ai_generated=template.ai_generated,
        is_published=template.is_published,
        is_public=template.is_public,
        created_at=template.created_at,
        created_by=template.created_by
    )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    request: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模板"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.category is not None:
        template.category = request.category
    if request.config is not None:
        template.config = request.config
    if request.modules is not None:
        # 清理 modules 中字段的前端专用属性
        cleaned_modules = []
        for mod in request.modules:
            if isinstance(mod, dict):
                clean_mod = {k: v for k, v in mod.items() if k != '_key'}
                if 'fields' in clean_mod and isinstance(clean_mod['fields'], list):
                    clean_fields = []
                    for f in clean_mod['fields']:
                        if isinstance(f, dict):
                            clean_f = {k: v for k, v in f.items() if k not in ('_key', '_value', 'optionsText')}
                            clean_fields.append(clean_f)
                        else:
                            clean_fields.append(f)
                    clean_mod['fields'] = clean_fields
                cleaned_modules.append(clean_mod)
            else:
                cleaned_modules.append(mod)
        template.modules = cleaned_modules
    if request.is_published is not None:
        template.is_published = request.is_published
    if hasattr(request, 'is_public') and request.is_public is not None:
        template.is_public = request.is_public
    
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse(
        id=template.id,
        name=template.name,
        code=template.code,
        description=template.description,
        category=template.category,
        config=template.config or {},
        modules=template.modules or [],
        ai_generated=template.ai_generated,
        is_published=template.is_published,
        is_public=template.is_public,
        created_at=template.created_at,
        created_by=template.created_by
    )


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模板"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    await db.delete(template)
    await db.commit()
    
    return BaseResponse(message="模板已删除")


# ============ 模板数据提交和管理 ============

@router.post("/{template_id}/submit", response_model=TemplateDataResponse)
async def submit_template_data(
    template_id: int,
    request: TemplateDataSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交模板数据 - 验证并保存到动态表"""
    from sqlalchemy import text
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if not template.is_published:
        raise HTTPException(status_code=400, detail="模板未发布，无法提交数据")
    
    # 获取字段定义用于验证
    all_fields = []
    field_map = {}  # name -> field
    for mod in (template.modules or []):
        if isinstance(mod, dict) and 'fields' in mod:
            for f in mod['fields']:
                if isinstance(f, dict):
                    all_fields.append(f)
                    field_map[f.get('name', '')] = f
    
    # 验证必填字段
    data = request.data
    for field in all_fields:
        if isinstance(field, dict) and field.get('required'):
            field_name = field.get('name', '')
            if field_name and not data.get(field_name):
                raise HTTPException(
                    status_code=400, 
                    detail=f"必填字段「{field.get('label', field_name)}」不能为空"
                )
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    # 构建字段名映射（原始名称 -> 安全名称）
    name_to_safe = {}
    safe_to_name = {}
    for field_name in data.keys():
        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
        if safe_name[0].isdigit():
            safe_name = 'f_' + safe_name
        name_to_safe[field_name] = safe_name
        safe_to_name[safe_name] = field_name
    
    # 构建 INSERT 语句
    columns = ["template_id", "created_by"]
    placeholders = [":template_id", ":created_by"]
    values = {"template_id": template_id, "created_by": current_user.id}
    
    for field_name, value in data.items():
        safe_name = name_to_safe.get(field_name, field_name)
        columns.append(f'"{safe_name}"')
        placeholders.append(f':{safe_name}')
        values[safe_name] = value
    
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    try:
        await db.execute(text(insert_sql), values)
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存数据失败: {str(e)}")
    
    # 获取刚插入的ID
    result = await db.execute(text(f"SELECT last_insert_rowid()"))
    row_id = result.scalar()
    
    return TemplateDataResponse(
        id=row_id,
        template_id=template_id,
        name=f"{template.name}_数据_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        config={"data": data, "table_name": table_name},
        created_by=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@router.get("/{template_id}/data", response_model=List[TemplateDataResponse])
async def get_template_data_list(
    template_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询模板提交的数据列表 - 从动态表读取"""
    from sqlalchemy import text
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    # 构建查询
    count_sql = f"SELECT COUNT(*) FROM {table_name}"
    if search:
        count_sql += f" WHERE template_id = {template_id}"
    else:
        count_sql += f" WHERE template_id = {template_id}"
    
    # 搜索
    data_sql = f"SELECT * FROM {table_name} WHERE template_id = :template_id"
    if search:
        # 模糊搜索所有文本列
        data_sql = f"""SELECT * FROM {table_name} WHERE template_id = :template_id 
                       AND (CAST(id AS TEXT) LIKE :search 
                            OR CAST(created_by AS TEXT) LIKE :search)"""
    
    data_sql += " ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
    
    try:
        # 获取总数
        count_result = await db.execute(text(count_sql))
        total = count_result.scalar() or 0
        
        # 获取数据列表
        params = {"template_id": template_id, "skip": skip, "limit": limit}
        if search:
            params["search"] = f"%{search}%"
        
        result = await db.execute(text(data_sql), params)
        rows = result.fetchall()
        
        # 获取列名
        columns = result.keys()
        
        return [
            {
                "id": row._mapping.get("id"),
                "template_id": row._mapping.get("template_id"),
                "name": f"{template.name}_数据_{row._mapping.get('id')}",
                "config": {"data": {k: row._mapping.get(k) for k in columns if k not in ['id', 'template_id', 'created_by', 'created_at', 'updated_at']}, "table_name": table_name},
                "created_by": row._mapping.get("created_by"),
                "created_at": row._mapping.get("created_at"),
                "updated_at": row._mapping.get("updated_at")
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")


@router.get("/{template_id}/data/count")
async def get_template_data_count(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板数据总数 - 从动态表读取"""
    from sqlalchemy import text
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    try:
        count_sql = f"SELECT COUNT(*) FROM {table_name} WHERE template_id = :template_id"
        result = await db.execute(text(count_sql), {"template_id": template_id})
        count = result.scalar() or 0
        return {"total": count}
    except Exception:
        return {"total": 0}


@router.get("/{template_id}/data/{data_id}", response_model=TemplateDataResponse)
async def get_template_data_detail(
    template_id: int,
    data_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条数据详情 - 从动态表读取"""
    from sqlalchemy import text
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    try:
        sql = f"SELECT * FROM {table_name} WHERE id = :id AND template_id = :template_id"
        result = await db.execute(text(sql), {"id": data_id, "template_id": template_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="数据不存在")
        
        # 获取列名
        columns = result.keys()
        
        return {
            "id": row._mapping.get("id"),
            "template_id": row._mapping.get("template_id"),
            "name": f"{template.name}_数据_{row._mapping.get('id')}",
            "config": {"data": {k: row._mapping.get(k) for k in columns if k not in ['id', 'template_id', 'created_by', 'created_at', 'updated_at']}, "table_name": table_name},
            "created_by": row._mapping.get("created_by"),
            "created_at": row._mapping.get("created_at"),
            "updated_at": row._mapping.get("updated_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")


@router.put("/{template_id}/data/{data_id}", response_model=TemplateDataResponse)
async def update_template_data(
    template_id: int,
    data_id: int,
    request: TemplateDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据 - 更新动态表"""
    from sqlalchemy import text
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    # 构建更新语句
    data = request.data
    if not data:
        raise HTTPException(status_code=400, detail="没有要更新的数据")
    
    # 构建字段名映射
    name_to_safe = {}
    for field_name in data.keys():
        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
        if safe_name[0].isdigit():
            safe_name = 'f_' + safe_name
        name_to_safe[field_name] = safe_name
    
    set_clauses = []
    values = {"id": data_id, "template_id": template_id}
    for field_name, value in data.items():
        safe_name = name_to_safe.get(field_name, field_name)
        set_clauses.append(f'"{safe_name}" = :{safe_name}')
        values[safe_name] = value
    
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    
    update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = :id AND template_id = :template_id"
    
    try:
        result = await db.execute(text(update_sql), values)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="数据不存在")
        
        # 返回更新后的数据
        select_sql = f"SELECT * FROM {table_name} WHERE id = :id"
        result = await db.execute(text(select_sql), {"id": data_id})
        row = result.fetchone()
        
        if row:
            columns = result.keys()
            return {
                "id": row._mapping.get("id"),
                "template_id": row._mapping.get("template_id"),
                "name": f"{template.name}_数据_{row._mapping.get('id')}",
                "config": {"data": {k: row._mapping.get(k) for k in columns if k not in ['id', 'template_id', 'created_by', 'created_at', 'updated_at']}, "table_name": table_name},
                "created_by": row._mapping.get("created_by"),
                "created_at": row._mapping.get("created_at"),
                "updated_at": row._mapping.get("updated_at")
            }
        
        raise HTTPException(status_code=404, detail="数据不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新数据失败: {str(e)}")


@router.delete("/{template_id}/data/{data_id}")
async def delete_template_data(
    template_id: int,
    data_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据 - 从动态表删除"""
    from sqlalchemy import text
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    try:
        delete_sql = f"DELETE FROM {table_name} WHERE id = :id AND template_id = :template_id"
        result = await db.execute(text(delete_sql), {"id": data_id, "template_id": template_id})
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="数据不存在")
        
        return BaseResponse(message="数据已删除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据失败: {str(e)}")


@router.get("/{template_id}/stats", response_model=TemplateStatsResponse)
async def get_template_stats(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板数据汇总统计"""
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 总数
    count_result = await db.execute(
        select(func.count(TemplateInstance.id)).where(TemplateInstance.template_id == template_id)
    )
    total_count = count_result.scalar() or 0
    
    # 今日提交数
    today = date.today()
    today_result = await db.execute(
        select(func.count(TemplateInstance.id)).where(
            TemplateInstance.template_id == template_id,
            func.date(TemplateInstance.created_at) == today
        )
    )
    today_count = today_result.scalar() or 0
    
    # 字段级统计（获取最近100条数据进行统计）
    data_result = await db.execute(
        select(TemplateInstance.config).where(
            TemplateInstance.template_id == template_id
        ).limit(100)
    )
    configs = data_result.scalars().all()
    
    field_stats = {}
    all_fields = []
    for mod in (template.modules or []):
        if isinstance(mod, dict) and 'fields' in mod:
            all_fields.extend(mod['fields'])
    
    for field in all_fields:
        if not isinstance(field, dict):
            continue
        field_name = field.get('name', '')
        field_type = field.get('type', 'text')
        if not field_name:
            continue
        
        values = []
        for cfg in configs:
            if isinstance(cfg, dict):
                data = cfg.get('data', {})
                if field_name in data:
                    values.append(data[field_name])
        
        stat = {"total": len(values), "filled": sum(1 for v in values if v and str(v).strip())}
        
        if field_type in ('number', 'money') and values:
            numeric_vals = []
            for v in values:
                try:
                    numeric_vals.append(float(str(v).replace(',', '').replace('¥', '').replace('$', '')))
                except (ValueError, TypeError):
                    pass
            if numeric_vals:
                stat["sum"] = sum(numeric_vals)
                stat["avg"] = round(sum(numeric_vals) / len(numeric_vals), 2)
                stat["min"] = min(numeric_vals)
                stat["max"] = max(numeric_vals)
        
        if field_type in ('select', 'radio') and values:
            from collections import Counter
            counter = Counter(str(v) for v in values if v and str(v).strip())
            stat["distribution"] = dict(counter.most_common(20))
        
        field_stats[field_name] = stat
    
    return TemplateStatsResponse(
        total_count=total_count,
        today_count=today_count,
        field_stats=field_stats
    )

@router.post("/{template_id}/publish")
async def publish_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发布模板 - 创建数据库表并发布"""
    from sqlalchemy import text
    
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限：只有创建者可以发布
    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有模板创建者可以发布")
    
    # 检查是否需要创建表：如果 config 里没有 table_name，需要创建
    config = template.config or {}
    table_name = config.get('table_name')
    
    if template.is_published and table_name:
        return BaseResponse(
            success=True,
            message="模板已是发布状态",
            data={"template_id": template.id, "is_published": True, "table_name": table_name}
        )
    
    # 获取所有字段定义
    all_fields = []
    for mod in (template.modules or []):
        if isinstance(mod, dict) and 'fields' in mod:
            for f in mod['fields']:
                if isinstance(f, dict):
                    all_fields.append(f)
    
    # 构建动态表名
    table_name = f"form_data_{template_id}"
    
    # 构建 CREATE TABLE 语句
    columns = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "template_id INTEGER NOT NULL",
        "created_by INTEGER",
        "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP",
    ]
    
    for field in all_fields:
        field_name = field.get('name', '')
        if not field_name:
            continue
        
        # 字段名只能是字母、数字、下划线
        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
        if safe_name[0].isdigit():
            safe_name = 'f_' + safe_name
        
        field_type = field.get('type', 'text')
        
        # 类型映射
        if field_type in ('number', 'money', 'percent'):
            col_type = 'REAL'
        elif field_type in ('date', 'datetime'):
            col_type = 'TEXT'
        elif field_type in ('switch', 'checkbox'):
            col_type = 'INTEGER DEFAULT 0'
        elif field_type in ('upload', 'image'):
            col_type = 'TEXT'
        else:
            col_type = 'TEXT'
        
        columns.append(f'"{safe_name}" {col_type}')
    
    # 执行创建表
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
    
    try:
        await db.execute(text(create_sql))
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建数据表失败: {str(e)}")
    
    # 保存表名到配置
    config = template.config or {}
    config['table_name'] = table_name
    template.config = config
    
    # 设置为已发布
    template.is_published = True
    template.organization_id = current_user.organization_id
    
    await db.commit()
    await db.refresh(template)
    
    return BaseResponse(
        success=True,
        message="模板发布成功，数据表已创建",
        data={"template_id": template.id, "is_published": True, "table_name": table_name}
    )


# ============ 导入导出功能 ============

@router.get("/{template_id}/data/export", response_model=None)
async def export_template_data(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出模板数据为JSON格式（供前端Excel转换）"""
    from sqlalchemy import text
    import json
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 解析 config（可能是字符串或字典）
    config_raw = template.config
    if isinstance(config_raw, str):
        config = json.loads(config_raw) if config_raw else {}
    else:
        config = config_raw or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    # 解析 modules（可能是字符串或列表）
    modules_raw = template.modules
    if isinstance(modules_raw, str):
        modules_list = json.loads(modules_raw) if modules_raw else []
    else:
        modules_list = modules_raw or []
    
    # 获取字段定义
    all_fields = []
    for mod in modules_list:
        if isinstance(mod, dict) and 'fields' in mod:
            all_fields.extend(mod['fields'])
    
    # 从动态表查询数据
    try:
        query = text(f"SELECT * FROM {table_name} ORDER BY created_at DESC")
        result = await db.execute(query)
        rows = result.fetchall()
        columns = result.keys()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"数据表不存在或查询失败: {str(e)}")
    
    # 构建导出数据
    export_data = []
    for row in rows:
        row_dict = dict(zip(columns, row))
        export_row = {
            "_id": row_dict.get('id'),
            "_created_at": row_dict.get('created_at'),
            "_updated_at": row_dict.get('updated_at'),
        }
        # 只导出模板定义的字段
        for field in all_fields:
            if isinstance(field, dict):
                field_name = field.get('name', '')
                export_row[field.get('label', field_name)] = row_dict.get(field_name, '')
        export_data.append(export_row)
    
    return {
        "template_name": template.name,
        "fields": [{"name": f.get('name'), "label": f.get('label')} for f in all_fields if isinstance(f, dict)],
        "data": export_data,
        "total": len(export_data)
    }


class ImportDataRequest(PydanticBaseModel):
    data: List[Dict[str, Any]]


@router.post("/{template_id}/data/import", response_model=None)
async def import_template_data(
    template_id: int,
    request: ImportDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量导入模板数据"""
    from sqlalchemy import text
    import json
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 解析 config（可能是字符串或字典）
    config_raw = template.config
    if isinstance(config_raw, str):
        config = json.loads(config_raw) if config_raw else {}
    else:
        config = config_raw or {}
    table_name = config.get('table_name', f'form_data_{template_id}')
    
    # 解析 modules（可能是字符串或列表）
    modules_raw = template.modules
    if isinstance(modules_raw, str):
        modules_list = json.loads(modules_raw) if modules_raw else []
    else:
        modules_list = modules_raw or []
    
    # 获取字段定义
    all_fields = []
    field_map = {}  # label -> name 映射
    for mod in modules_list:
        if isinstance(mod, dict) and 'fields' in mod:
            for f in mod['fields']:
                if isinstance(f, dict):
                    all_fields.append(f)
                    if f.get('label'):
                        field_map[f['label']] = f['name']
    
    imported_count = 0
    errors = []
    
    for idx, row in enumerate(request.data):
        try:
            # 将标签转换为字段名
            data = {}
            for label, name in field_map.items():
                if label in row:
                    data[name] = row[label]
            
            # 验证必填字段
            for field in all_fields:
                if isinstance(field, dict) and field.get('required'):
                    field_name = field.get('name', '')
                    if field_name and not data.get(field_name):
                        errors.append(f"第{idx + 1}行：必填字段「{field.get('label', field_name)}」为空")
                        continue
            
            # 构建插入语句
            columns = ["template_id", "created_by"]
            placeholders = [":template_id", ":created_by"]
            values = {"template_id": template_id, "created_by": current_user.id}
            
            for field_name, value in data.items():
                # 安全字段名
                safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
                if safe_name[0].isdigit():
                    safe_name = 'f_' + safe_name
                columns.append(f'"{safe_name}"')
                placeholders.append(f':{safe_name}')
                values[safe_name] = value
            
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            await db.execute(text(insert_sql), values)
            imported_count += 1
        except Exception as e:
            errors.append(f"第{idx + 1}行：{str(e)}")
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"成功导入 {imported_count} 条数据",
        "imported": imported_count,
        "total": len(request.data),
        "errors": errors[:10]  # 最多返回10个错误
    }
