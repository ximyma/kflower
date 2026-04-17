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
    """获取模板列表 - 显示所有模板（自己创建的 + 已发布的）"""
    # 显示所有模板：自己创建的 + 组织内已发布的
    query = select(Template).where(
        (Template.created_by == current_user.id) | 
        (Template.is_published == True)
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
            created_at=t.created_at
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
        created_at=template.created_at
    )


@router.post("/", response_model=TemplateResponse)
async def create_template(
    request: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模板"""
    # 生成编码
    code = request.code or f"tpl_{uuid.uuid4().hex[:8]}"
    
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
        is_published=True,  # 默认发布，这样创建后就能看到
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    db.add(template)
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
        created_at=template.created_at
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
        created_at=template.created_at
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
    """提交模板数据 - 基于模板的字段定义验证并保存"""
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取字段定义用于验证
    all_fields = []
    for mod in (template.modules or []):
        if isinstance(mod, dict) and 'fields' in mod:
            all_fields.extend(mod['fields'])
    
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
    
    # 创建实例
    instance_code = f"ins_{uuid.uuid4().hex[:8]}"
    instance = TemplateInstance(
        name=f"{template.name}_数据_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        code=instance_code,
        template_id=template_id,
        config={"data": data},
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    
    return TemplateDataResponse(
        id=instance.id,
        template_id=instance.template_id,
        name=instance.name,
        config=instance.config or {},
        created_by=instance.created_by,
        created_at=instance.created_at,
        updated_at=instance.updated_at
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
    """查询模板提交的数据列表（分页、搜索）"""
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    query = select(TemplateInstance).where(TemplateInstance.template_id == template_id)
    
    # 搜索：在 config.data 的值中搜索
    if search:
        # SQLite JSON 搜索兼容
        query = query.where(TemplateInstance.config.cast(String).contains(search))
    
    query = query.order_by(TemplateInstance.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    instances = result.scalars().all()
    
    return [
        TemplateDataResponse(
            id=inst.id,
            template_id=inst.template_id,
            name=inst.name,
            config=inst.config or {},
            created_by=inst.created_by,
            created_at=inst.created_at,
            updated_at=inst.updated_at
        )
        for inst in instances
    ]


@router.get("/{template_id}/data/count")
async def get_template_data_count(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板数据总数"""
    result = await db.execute(
        select(func.count(TemplateInstance.id)).where(TemplateInstance.template_id == template_id)
    )
    count = result.scalar()
    return {"total": count}


@router.get("/{template_id}/data/{data_id}", response_model=TemplateDataResponse)
async def get_template_data_detail(
    template_id: int,
    data_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单条数据详情"""
    result = await db.execute(
        select(TemplateInstance).where(
            TemplateInstance.id == data_id,
            TemplateInstance.template_id == template_id
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="数据不存在")
    
    return TemplateDataResponse(
        id=instance.id,
        template_id=instance.template_id,
        name=instance.name,
        config=instance.config or {},
        created_by=instance.created_by,
        created_at=instance.created_at,
        updated_at=instance.updated_at
    )


@router.put("/{template_id}/data/{data_id}", response_model=TemplateDataResponse)
async def update_template_data(
    template_id: int,
    data_id: int,
    request: TemplateDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据"""
    result = await db.execute(
        select(TemplateInstance).where(
            TemplateInstance.id == data_id,
            TemplateInstance.template_id == template_id
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="数据不存在")
    
    # 合并更新数据
    existing_config = instance.config or {}
    existing_data = existing_config.get("data", {})
    existing_data.update(request.data)
    instance.config = {"data": existing_data}
    instance.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(instance)
    
    return TemplateDataResponse(
        id=instance.id,
        template_id=instance.template_id,
        name=instance.name,
        config=instance.config or {},
        created_by=instance.created_by,
        created_at=instance.created_at,
        updated_at=instance.updated_at
    )


@router.delete("/{template_id}/data/{data_id}")
async def delete_template_data(
    template_id: int,
    data_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据"""
    result = await db.execute(
        select(TemplateInstance).where(
            TemplateInstance.id == data_id,
            TemplateInstance.template_id == template_id
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="数据不存在")
    
    await db.delete(instance)
    await db.commit()
    
    return BaseResponse(message="数据已删除")


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
    """发布模板 - 使模板可供组织内其他用户使用"""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查权限：只有创建者可以发布
    if template.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只有模板创建者可以发布")
    
    # 设置为已发布
    template.is_published = True
    template.organization_id = current_user.organization_id
    
    await db.commit()
    await db.refresh(template)
    
    return BaseResponse(
        success=True,
        message="模板已发布",
        data={"template_id": template.id, "is_published": True}
    )


# ============ 导入导出功能 ============

@router.get("/{template_id}/data/export")
async def export_template_data(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出模板数据为JSON格式（供前端Excel转换）"""
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取所有数据
    query = select(TemplateInstance).where(TemplateInstance.template_id == template_id)
    query = query.order_by(TemplateInstance.created_at.desc())
    result = await db.execute(query)
    instances = result.scalars().all()
    
    # 获取字段定义
    all_fields = []
    for mod in (template.modules or []):
        if isinstance(mod, dict) and 'fields' in mod:
            all_fields.extend(mod['fields'])
    
    # 构建导出数据
    export_data = []
    for inst in instances:
        row = {
            "_id": inst.id,
            "_created_at": inst.created_at.isoformat() if inst.created_at else None,
            "_updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
        }
        data = inst.config.get("data", {}) if inst.config else {}
        for field in all_fields:
            if isinstance(field, dict):
                field_name = field.get('name', '')
                row[field.get('label', field_name)] = data.get(field_name, '')
        export_data.append(row)
    
    return {
        "template_name": template.name,
        "fields": [{"name": f.get('name'), "label": f.get('label')} for f in all_fields if isinstance(f, dict)],
        "data": export_data,
        "total": len(export_data)
    }


class ImportDataRequest(PydanticBaseModel):
    data: List[Dict[str, Any]]


@router.post("/{template_id}/data/import")
async def import_template_data(
    template_id: int,
    request: ImportDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量导入模板数据"""
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取字段定义
    all_fields = []
    field_map = {}  # label -> name 映射
    for mod in (template.modules or []):
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
            
            # 创建实例
            instance_code = f"ins_{uuid.uuid4().hex[:8]}"
            instance = TemplateInstance(
                name=f"{template.name}_导入_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}",
                code=instance_code,
                template_id=template_id,
                config={"data": data, "imported": True},
                organization_id=current_user.organization_id,
                created_by=current_user.id
            )
            db.add(instance)
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
