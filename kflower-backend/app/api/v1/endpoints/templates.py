"""
API路由 - 模板管理
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
import json
from datetime import datetime
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
from app.core.formula_engine import formula_engine, validation_engine, visibility_engine
from pydantic import BaseModel as PydanticBaseModel, BaseModel
from app.modules.my_apps.plugin_executor import plugin_executor, PluginContext
from app.modules.my_apps.models import AppPlugin

router = APIRouter(prefix="/templates", tags=["模板管理"])


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_published: Optional[bool] = None,
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
    
    if is_published is not None:
        query = query.where(Template.is_published == is_published)
    
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
    
    # ===== 公式计算 + 高级校验 =====
    subtable_data_to_save = {}  # field_name -> list of row dicts
    main_data = dict(data)  # 主表数据（去掉子表）
    
    for field in all_fields:
        if not isinstance(field, dict):
            continue
        fname = field.get('name', '')
        ftype = field.get('type', '')
        
        # 分离子表数据
        if ftype == 'subform':
            if fname in main_data:
                subtable_data_to_save[fname] = main_data.pop(fname)
            continue
        
        # 条件必填校验
        required_rule = field.get('required_when')
        if required_rule and not data.get(fname):
            try:
                if isinstance(required_rule, str):
                    needed = formula_engine.evaluate(required_rule, data)
                elif isinstance(required_rule, dict) and required_rule.get('formula'):
                    needed = formula_engine.evaluate(required_rule['formula'], data)
                else:
                    needed = False
                if needed:
                    raise HTTPException(status_code=400, detail=f"条件必填字段「{field.get('label', fname)}」不满足条件")
            except HTTPException:
                raise
            except:
                pass
        
        # 默认值公式
        if not main_data.get(fname) and field.get('default_formula'):
            try:
                default_val = formula_engine.evaluate(field['default_formula'], main_data)
                if default_val is not None:
                    main_data[fname] = default_val
            except:
                pass
        
        # 高级校验规则
        rules = field.get('validation_rules')
        if rules and main_data.get(fname) is not None:
            errors = validation_engine.validate_field(field, main_data[fname], main_data)
            if errors:
                raise HTTPException(status_code=400, detail=f"字段「{field.get('label', fname)}」校验失败: {'; '.join(errors)}")
    
    # 批量计算公式字段
    try:
        computed = formula_engine.compute_form(main_data, all_fields, subtable_data_to_save or None)
        main_data.update(computed)
    except Exception:
        pass  # 公式计算失败不阻止保存
    
    # 用计算后的 main_data 替换原始 data
    data = main_data
    
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
        # list/array 类型序列化为 JSON 字符串存入 SQLite
        values[safe_name] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
    
    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    # ===== 插件触发：before_save =====
    # 获取 app_id（从模板配置中）
    app_id = None
    template_config = template.config or {}
    if isinstance(template_config, dict):
        app_id = template_config.get('app_id')
    
    if app_id:
        try:
            # 构建上下文
            context = PluginContext(
                data=data,
                old_data=None,
                db=db,
                user_id=current_user.id,
                template_id=template_id,
                event='before_save',
                app_id=app_id
            )
            # 查询并执行 before_save 插件
            plugins_result = await db.execute(
                select(AppPlugin).where(
                    AppPlugin.app_id == app_id,
                    AppPlugin.trigger_event == 'before_save',
                    AppPlugin.is_enabled == True
                )
            )
            plugins = plugins_result.scalars().all()
            for plugin in plugins:
                if not plugin.target_template_id or plugin.target_template_id == template_id:
                    result = await plugin_executor.execute(plugin.script_code, context, timeout=5)
                    if not result['success']:
                        # 记录错误但不阻止保存
                        pass
        except Exception as e:
            # 插件执行失败不影响主流程
            pass
    
    try:
        await db.execute(text(insert_sql), values)
        await db.commit()
        
        # 获取刚插入的主记录 ID
        result = await db.execute(text("SELECT last_insert_rowid()"))
        row_id = result.scalar()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存数据失败: {str(e)}")
    
    # ===== 保存子表数据 =====
    if subtable_data_to_save and row_id:
        from app.models.workflow import SubTableData
        for field_name, rows in subtable_data_to_save.items():
            if not isinstance(rows, list):
                continue
            for row_data in rows:
                if not isinstance(row_data, dict):
                    continue
                sub_record = SubTableData(
                    parent_record_id=row_id,
                    parent_table_name=table_name,
                    parent_field_name=field_name,
                    row_data=row_data,
                    created_by=current_user.id
                )
                db.add(sub_record)
        await db.commit()
    
    # ===== 插件触发：after_save =====
    if app_id:
        try:
            context = PluginContext(
                data=data,
                old_data=None,
                db=db,
                user_id=current_user.id,
                template_id=template_id,
                event='after_save',
                app_id=app_id
            )
            plugins_result = await db.execute(
                select(AppPlugin).where(
                    AppPlugin.app_id == app_id,
                    AppPlugin.trigger_event == 'after_save',
                    AppPlugin.is_enabled == True
                )
            )
            plugins = plugins_result.scalars().all()
            for plugin in plugins:
                if not plugin.target_template_id or plugin.target_template_id == template_id:
                    await plugin_executor.execute(plugin.script_code, context, timeout=5)
        except Exception as e:
            pass
    
    # ===== RAG 自动索引（升级方案 7.1） =====
    if app_id:
        try:
            from app.core.rag_autoindexer import get_rag_autoindexer
            
            # 从 modules 中提取所有字段（兼容新旧格式）
            all_template_fields = []
            modules_list = template.modules or []
            if isinstance(modules_list, str):
                import json as _json
                modules_list = _json.loads(modules_list) if modules_list else []
            
            for mod in modules_list:
                if isinstance(mod, dict) and 'fields' in mod:
                    all_template_fields.extend(mod['fields'] or [])
            
            # 构建字段标签映射
            field_labels = {f.get("name", ""): f.get("label", f.get("name", "")) for f in all_template_fields}
            
            # 提取字段值
            field_values = {}
            for field in all_template_fields:
                field_name = field.get("name", "")
                if field_name in data:
                    field_values[field_name] = data[field_name]
            
            # 执行自动索引
            autoindexer = get_rag_autoindexer()
            index_result = await autoindexer.index_form_submission(
                app_id=app_id,
                template_id=template_id,
                template_name=template.name,
                template_code=template.code,
                data_id=data.get("id", 0),
                field_values=field_values,
                field_labels=field_labels,
                db=db,
            )
            
            if index_result.get("indexed_count", 0) > 0:
                logger.info(f"RAG 自动索引成功: {index_result}")
        except Exception as e:
            logger.warning(f"RAG 自动索引失败: {e}")
    
    # ===== 流程审批触发（升级方案 4.1） =====
    workflow_instance = None
    try:
        # 查找关联此模板的 AppMenu，检查是否配置了自动触发工作流
        from app.modules.my_apps.models import AppMenu
        from app.models.workflow import Workflow
        
        menu_result = await db.execute(
            select(AppMenu).where(AppMenu.template_id == template_id)
        )
        menu = menu_result.scalar_one_or_none()
        
        if menu and menu.workflow_id:
            # 检查触发条件：submit 或 auto_approve
            should_trigger = (
                menu.workflow_trigger == 'submit' or 
                menu.workflow_auto_approve == True
            )
            
            if should_trigger:
                # 获取工作流定义
                wf_result = await db.execute(
                    select(Workflow).where(Workflow.id == menu.workflow_id)
                )
                workflow = wf_result.scalar_one_or_none()
                
                if workflow and workflow.is_published:
                    from app.core.workflow.engine import WorkflowEngine
                    
                    # 构建流程变量
                    variables = dict(data)
                    # 应用字段映射
                    if menu.workflow_node_mapping:
                        for mapping in menu.workflow_node_mapping:
                            if isinstance(mapping, dict):
                                form_field = mapping.get('form_field')
                                workflow_var = mapping.get('workflow_var')
                                if form_field and workflow_var and form_field in data:
                                    variables[workflow_var] = data[form_field]
                    
                    # 添加元数据
                    variables['_template_id'] = template_id
                    variables['_form_data_id'] = row_id
                    variables['_app_id'] = app_id
                    variables['_applicant_id'] = current_user.id
                    variables['_applicant_name'] = getattr(current_user, 'name', current_user.username)
                    
                    # 启动工作流实例
                    engine = WorkflowEngine(db)
                    workflow_instance = await engine.start_instance(
                        workflow_id=menu.workflow_id,
                        title=f"{template.name} - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                        starter_id=current_user.id,
                        variables=variables,
                        form_data_id=row_id
                    )
    except Exception as e:
        # 工作流触发失败不影响主流程
        import logging
        logging.error(f"工作流触发失败: {e}")
    
    return TemplateDataResponse(
        id=row_id,
        template_id=template_id,
        name=f"{template.name}_数据_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        config={"data": data, "table_name": table_name, "workflow_instance_id": workflow_instance.id if workflow_instance else None},
        created_by=current_user.id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@router.get("/{template_id}/data")
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
    import json
    
    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 获取表名
    config = template.config or {}
    table_name = config.get('table_name', f'form_data_{template_id}')

    # 获取字段定义（与 export_template_data 一致）
    modules_raw = template.modules
    if isinstance(modules_raw, str):
        modules_list = json.loads(modules_raw) if modules_raw else []
    else:
        modules_list = modules_raw or []
    all_fields = []
    for mod in modules_list:
        if isinstance(mod, dict) and 'fields' in mod:
            all_fields.extend(mod['fields'])

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
        
        # 构建导出数据（键 = field.name，与数据库列名一致）
        export_rows = []
        for row in rows:
            mapping = row._mapping
            row_data = {
                "id": mapping.get("id"),
                "template_id": mapping.get("template_id"),
                "name": f"{template.name}_数据_{mapping.get('id')}",
                "created_by": mapping.get("created_by"),
                "created_at": mapping.get("created_at"),
                "updated_at": mapping.get("updated_at"),
            }
            # 动态字段：键 = field.name（与 submit/export 一致）
            for field in all_fields:
                if isinstance(field, dict):
                    field_name = field.get('name', '')
                    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
                    if safe_name and safe_name[0].isdigit():
                        safe_name = 'f_' + safe_name
                    row_data[field_name] = mapping.get(safe_name, '')
            export_rows.append(row_data)

        return export_rows
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
            "id": row_dict.get('id'),
            "created_at": _format_val(row_dict.get('created_at')),
            "updated_at": _format_val(row_dict.get('updated_at')),
        }
        # 只导出模板定义的字段，键 = field.name（与数据库列名一致）
        for field in all_fields:
            if isinstance(field, dict):
                field_name = field.get('name', '')
                # 构造实际的数据库列名（与 submit 时一致）
                safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
                if safe_name and safe_name[0].isdigit():
                    safe_name = 'f_' + safe_name
                export_row[field_name] = _format_val(row_dict.get(safe_name))
        export_data.append(export_row)

    # 返回 fields 列表供前端做表头映射
    fields_meta = [
        {"name": f.get('name', ''), "label": f.get('label', '')}
        for f in all_fields if isinstance(f, dict)
    ]

    return {
        "template_name": template.name,
        "fields": fields_meta,
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
                values[safe_name] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value

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
        
        # 加载子表数据
        subtable_data = {}
        try:
            from app.models.workflow import SubTableData
            sub_result = await db.execute(
                select(SubTableData).where(
                    SubTableData.parent_record_id == data_id,
                    SubTableData.parent_table_name == table_name
                )
            )
            sub_records = sub_result.scalars().all()
            for rec in sub_records:
                subtable_data.setdefault(rec.parent_field_name, []).append(rec.row_data)
        except:
            pass
        
        # 合并子表数据到主数据
        main_data = {k: row._mapping.get(k) for k in columns if k not in ['id', 'template_id', 'created_by', 'created_at', 'updated_at']}
        main_data.update(subtable_data)
        
        return {
            "id": row._mapping.get("id"),
            "template_id": row._mapping.get("template_id"),
            "name": f"{template.name}_数据_{row._mapping.get('id')}",
            "config": {"data": main_data, "table_name": table_name},
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
        # list/array 类型序列化为 JSON 字符串
        values[safe_name] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
    
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    
    update_sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = :id AND template_id = :template_id"
    
    # ===== 插件触发：before_update =====
    app_id = None
    template_config = template.config or {}
    if isinstance(template_config, dict):
        app_id = template_config.get('app_id')
    
    if app_id:
        try:
            context = PluginContext(
                data=data,
                old_data=None,
                db=db,
                user_id=current_user.id,
                template_id=template_id,
                event='before_update',
                app_id=app_id
            )
            plugins_result = await db.execute(
                select(AppPlugin).where(
                    AppPlugin.app_id == app_id,
                    AppPlugin.trigger_event == 'before_update',
                    AppPlugin.is_enabled == True
                )
            )
            plugins = plugins_result.scalars().all()
            for plugin in plugins:
                if not plugin.target_template_id or plugin.target_template_id == template_id:
                    result = await plugin_executor.execute(plugin.script_code, context, timeout=5)
                    if not result['success']:
                        pass
        except Exception as e:
            pass
    
    try:
        result = await db.execute(text(update_sql), values)
        await db.commit()
        
        # ===== 插件触发：after_update =====
        if app_id:
            try:
                context = PluginContext(
                    data=data,
                    old_data=None,
                    db=db,
                    user_id=current_user.id,
                    template_id=template_id,
                    event='after_save',
                    app_id=app_id
                )
                plugins_result = await db.execute(
                    select(AppPlugin).where(
                        AppPlugin.app_id == app_id,
                        AppPlugin.trigger_event == 'after_save',
                        AppPlugin.is_enabled == True
                    )
                )
                plugins = plugins_result.scalars().all()
                for plugin in plugins:
                    if not plugin.target_template_id or plugin.target_template_id == template_id:
                        await plugin_executor.execute(plugin.script_code, context, timeout=5)
            except Exception as e:
                pass
        
        # ===== RAG 自动索引（升级方案 7.1） =====
        if app_id:
            try:
                from app.core.rag_autoindexer import get_rag_autoindexer
                
                # 构建字段标签映射
                field_labels = {f.get("name", ""): f.get("label", f.get("name", "")) for f in template.fields}
                
                # 提取字段值
                field_values = {}
                for field in template.fields:
                    field_name = field.get("name", "")
                    if field_name in data:
                        field_values[field_name] = data[field_name]
                
                # 执行自动索引
                autoindexer = get_rag_autoindexer()
                index_result = await autoindexer.index_form_submission(
                    app_id=app_id,
                    template_id=template_id,
                    template_name=template.name,
                    template_code=template.code,
                    data_id=data_id,
                    field_values=field_values,
                    field_labels=field_labels,
                    db=db,
                )
                
                if index_result.get("indexed_count", 0) > 0:
                    logger.info(f"RAG 自动索引成功（更新）: {index_result}")
            except Exception as e:
                logger.warning(f"RAG 自动索引失败（更新）: {e}")
        
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
    
    # ===== 插件触发：before_delete =====
    app_id = None
    template_config = template.config or {}
    if isinstance(template_config, dict):
        app_id = template_config.get('app_id')
    
    if app_id:
        try:
            context = PluginContext(
                data={"id": data_id},
                old_data=None,
                db=db,
                user_id=current_user.id,
                template_id=template_id,
                event='before_delete',
                app_id=app_id
            )
            plugins_result = await db.execute(
                select(AppPlugin).where(
                    AppPlugin.app_id == app_id,
                    AppPlugin.trigger_event == 'before_delete',
                    AppPlugin.is_enabled == True
                )
            )
            plugins = plugins_result.scalars().all()
            for plugin in plugins:
                if not plugin.target_template_id or plugin.target_template_id == template_id:
                    result = await plugin_executor.execute(plugin.script_code, context, timeout=5)
                    if not result['success']:
                        pass
        except Exception as e:
            pass
    
    try:
        delete_sql = f"DELETE FROM {table_name} WHERE id = :id AND template_id = :template_id"
        result = await db.execute(text(delete_sql), {"id": data_id, "template_id": template_id})
        await db.commit()
        
        # ===== 插件触发：after_delete =====
        if app_id:
            try:
                context = PluginContext(
                    data={"id": data_id},
                    old_data=None,
                    db=db,
                    user_id=current_user.id,
                    template_id=template_id,
                    event='after_delete',
                    app_id=app_id
                )
                plugins_result = await db.execute(
                    select(AppPlugin).where(
                        AppPlugin.app_id == app_id,
                        AppPlugin.trigger_event == 'after_delete',
                        AppPlugin.is_enabled == True
                    )
                )
                plugins = plugins_result.scalars().all()
                for plugin in plugins:
                    if not plugin.target_template_id or plugin.target_template_id == template_id:
                        await plugin_executor.execute(plugin.script_code, context, timeout=5)
            except Exception as e:
                pass
        
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
        
        field_type = field.get('type', 'text')
        
        # subform 类型不创建主表列，子表数据存储在独立的 subtable_data 表中
        if field_type == 'subform':
            continue
        
        # is_formula 字段不创建主表列（计算结果在查询时动态生成）
        if field.get('is_formula'):
            continue
        
        # 字段名只能是字母、数字、下划线
        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in field_name)
        if safe_name[0].isdigit():
            safe_name = 'f_' + safe_name
        
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

def _format_val(v):
    """将 datetime 等对象格式化为 JSON 可序列化的字符串"""
    if v is None:
        return ''
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    return v


@router.post("/{template_id}/upload")
async def upload_file_to_template(
    template_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件到模板（存入模板 config 的 upload 字段）"""
    import os
    from app.core.config import settings

    # 验证模板存在
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.is_published:
        raise HTTPException(status_code=400, detail="模板未发布，无法上传文件")

    # 保存文件
    ext = os.path.splitext(file.filename or '')[1] or '.bin'
    file_id = f"{template_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, "template_files")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file_id)

    try:
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 返回访问路径
    file_url = f"/files/template_files/{file_id}"

    return {
        "success": True,
        "message": "文件上传成功",
        "file_id": file_id,
        "filename": file.filename,
        "url": file_url
    }
# ====== 公式引擎 API ======

class FormulaValidateRequest(BaseModel):
    formula: str
    fields: Optional[Dict[str, Any]] = {}

class FormulaEvaluateRequest(BaseModel):
    formula: str
    data: Optional[Dict[str, Any]] = {}

class FormComputeRequest(BaseModel):
    template_id: int
    data: Dict[str, Any]

class FormVisibilityRequest(BaseModel):
    template_id: int
    data: Dict[str, Any]


@router.post("/formula/validate")
async def validate_formula(request: FormulaValidateRequest, current_user: User = Depends(get_current_user)):
    """验证公式语法"""
    try:
        result = formula_engine.validate(request.formula)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/formula/evaluate")
async def evaluate_formula(request: FormulaEvaluateRequest, current_user: User = Depends(get_current_user)):
    """计算公式结果"""
    try:
        result = formula_engine.evaluate(request.formula, request.data or {})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/{template_id}/compute")
async def compute_form_formulas(request: FormComputeRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """批量计算模板公式"""
    try:
        template = (await db.execute(select(Template).where(Template.id == request.template_id))).scalar_one_or_none()
        if not template:
            return {"success": False, "error": "模板不存在"}
        config = json.loads(template.config) if template.config else {}
        field_defs = list(config.get('fields', {}).values())
        computed = formula_engine.compute_form(request.data, field_defs)
        return {"success": True, "results": computed}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/{template_id}/visibility")
async def compute_visibility(request: FormVisibilityRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """计算字段显隐"""
    results = {}
    try:
        template = (await db.execute(select(Template).where(Template.id == request.template_id))).scalar_one_or_none()
        if not template:
            return {"success": False, "error": "模板不存在"}
        config = json.loads(template.config) if template.config else {}
        for field_key, field_def in config.get("fields", {}).items():
            vis = visibility_engine.is_visible(field_def, request.data)
            results[field_key] = vis
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/formula/validate-data")
async def validate_form_data(request: FormComputeRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """验证表单数据"""
    errors = []
    try:
        template = (await db.execute(select(Template).where(Template.id == request.template_id))).scalar_one_or_none()
        if not template:
            return {"success": False, "error": "模板不存在"}
        config = json.loads(template.config) if template.config else {}
        for field_key, field_def in config.get("fields", {}).items():
            val = request.data.get(field_key)
            errs = validation_engine.validate_field(field_def, val, request.data)
            if errs:
                for e in errs:
                    errors.append({'field': field_key, 'error': e})
        return {"success": True, "errors": errors}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ====== 数据聚合 API ======

@router.get("/{template_id}/data/aggregations")
async def get_data_aggregations(
    template_id: int,
    group_by: str = Query("", description="分组字段名"),
    agg_func: str = Query("sum", description="聚合函数: sum/count/avg/min/max"),
    agg_field: str = Query("", description="聚合字段名(仅 sum/avg/min/max)"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """数据聚合统计"""
    try:
        template = (await db.execute(select(Template).where(Template.id == template_id))).scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        config = json.loads(template.config) if template.config else {}
        table_name = config.get("table_name")
        if not table_name:
            raise HTTPException(status_code=400, detail="模板未发布，无法查询")

        # 直接执行 SQL 聚合查询
        from sqlalchemy import text
        query_parts = []
        params = {}
        
        if group_by and agg_field and agg_func in ['sum', 'avg', 'min', 'max']:
            query_parts.append(f'SELECT {group_by}, {agg_func}({agg_field}) as value')
        elif agg_func == 'count':
            query_parts.append(f'SELECT {group_by}, COUNT(*) as value')
        else:
            query_parts.append(f'SELECT {agg_func}({agg_field}) as value')
        
        query_parts.append(f'FROM {table_name}')
        
        if start_date or end_date:
            date_col = config.get('created_at', 'created_at')
            conditions = []
            if start_date:
                conditions.append(f"{date_col} >= :start")
                params['start'] = start_date
            if end_date:
                conditions.append(f"{date_col} <= :end")
                params['end'] = end_date
            query_parts.append('WHERE ' + ' AND '.join(conditions))
        
        if group_by and agg_field:
            query_parts.append(f'GROUP BY {group_by}')
        
        query = text(' '.join(query_parts))
        rows = (await db.execute(query, params)).fetchall()
        
        if group_by:
            results_list = [{'group': r[0], 'value': r[1]} for r in rows]
            return {'success': True, 'results': results_list}
        else:
            value = rows[0][0] if rows else 0
            return {'success': True, 'count': len(rows), 'value': value}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


# ====== 数据 Lookup API ======

@router.get("/lookup")
async def lookup_template_data(
    target_template_id: int,
    search: str = Query("", description="搜索关键词"),
    display_field: str = Query("name", description="显示字段"),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查找目标模板数据（Lookup）- 独立路由，避免与 /{template_id} 路径参数冲突"""
    try:
        target_tpl = (await db.execute(select(Template).where(Template.id == target_template_id))).scalar_one_or_none()
        if not target_tpl:
            raise HTTPException(status_code=404, detail="目标模板不存在")
        config = target_tpl.config if isinstance(target_tpl.config, dict) else (json.loads(target_tpl.config) if target_tpl.config else {})
        table_name = config.get("table_name")
        if not table_name:
            raise HTTPException(status_code=400, detail="目标模板未发布")

        # 动态查询
        from sqlalchemy import text
        query_text = text(f"SELECT id, {display_field} FROM {table_name} WHERE CAST({display_field} AS TEXT) LIKE :kw LIMIT :lim")
        rows = (await db.execute(query_text, {"kw": f"%{search}%", "lim": limit})).fetchall()
        results = [{"id": r[0], "display": r[1]} for r in rows]
        return {"success": True, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/lookup/{target_template_id}/{data_id}")
async def get_lookup_record_detail(
    target_template_id: int,
    data_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取关联记录详情（用于自动填充）"""
    try:
        target_tpl = (await db.execute(select(Template).where(Template.id == target_template_id))).scalar_one_or_none()
        if not target_tpl:
            raise HTTPException(status_code=404, detail="目标模板不存在")
        config = target_tpl.config if isinstance(target_tpl.config, dict) else (json.loads(target_tpl.config) if target_tpl.config else {})
        table_name = config.get("table_name")
        if not table_name:
            raise HTTPException(status_code=400, detail="目标模板未发布")

        from sqlalchemy import text
        query_text = text(f"SELECT * FROM {table_name} WHERE id = :id LIMIT 1")
        result = await db.execute(query_text, {"id": data_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="记录不存在")

        # 获取字段定义
        modules_raw = target_tpl.modules
        if isinstance(modules_raw, str):
            modules_list = json.loads(modules_raw) if modules_raw else []
        else:
            modules_list = modules_raw or []
        all_fields = []
        for mod in modules_list:
            if isinstance(mod, dict) and 'fields' in mod:
                all_fields.extend(mod['fields'])

        # 构建字段名映射
        columns = result.keys()
        record = {}
        for k in columns:
            if k in ('id', 'template_id', 'created_by', 'created_at', 'updated_at'):
                continue
            record[k] = row._mapping.get(k)
        # 也用原始字段名映射
        for field in all_fields:
            if isinstance(field, dict):
                fname = field.get('name', '')
                safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in fname)
                if safe_name and safe_name[0].isdigit():
                    safe_name = 'f_' + safe_name
                if safe_name in row._mapping and fname != safe_name:
                    record[fname] = row._mapping.get(safe_name)

        return {"success": True, "data": record}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}
