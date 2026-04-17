"""
API路由 - 智能导入（Excel/CSV/图片OCR）
"""
import re
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Template
from app.schemas.schemas import BaseResponse
from app.services.import_service import (
    parse_excel, extract_table_from_image,
    generate_fields_from_data, build_preview_table,
    enhance_with_jieba, export_template_json
)

router = APIRouter(prefix="/import", tags=["智能导入"])


@router.post("/parse")
async def parse_file(
    file: UploadFile = File(...),
    header_row: int = Form(0),
    sheet_name: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解析上传的文件（Excel/CSV/图片），返回表头和预览数据
    - header_row: 指定哪一行作为表头（0=第一行，默认0）
    - sheet_name: 指定工作表名（仅Excel有效，默认第一个工作表）
    """
    try:
        contents = await file.read()
        filename = file.filename or 'unknown'

        if filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            # 解析 Excel/CSV
            result = parse_excel(
                contents, filename,
                header_row=header_row,
                sheet_name=sheet_name if sheet_name else None
            )
            headers = result['headers']
            rows = result['rows']
            all_rows = result.get('all_rows', [])
            sheet_names = result.get('sheet_names', [])
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
            # OCR 解析图片
            headers, rows = extract_table_from_image(contents)
            if not headers:
                return JSONResponse({
                    "success": False,
                    "message": "未能从图片中识别到表格，请确保图片清晰、包含表格线或清晰的行列数据"
                })
            all_rows = [headers] + rows
            sheet_names = []
        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式，支持: .xlsx, .xls, .csv, .png, .jpg, .jpeg, .bmp"
            )

        if not headers:
            raise HTTPException(status_code=400, detail="未能解析到有效的表头数据")

        # 生成字段定义
        fields = generate_fields_from_data(headers, rows[:50])

        # 构建预览数据
        preview = build_preview_table(headers, rows, fields)

        return JSONResponse({
            "success": True,
            "message": f"成功解析 {len(rows)} 行数据",
            "data": {
                "headers": headers,
                "rows": rows[:20],  # 限制预览行数
                "all_rows": all_rows[:30],  # 所有行（含表头行），供前端选择表头行
                "total_rows": len(rows),
                "total_columns": len(headers),
                "fields": fields,
                "preview": preview,
                "filename": filename,
                "analysis": enhance_with_jieba(headers, rows[:10]),
                "sheet_names": sheet_names,
                "current_sheet": sheet_name if sheet_name else (sheet_names[0] if sheet_names else 'Sheet1'),
                "header_row": header_row
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/preview")
async def preview_import(
    fields: List[dict],
    headers: List[str],
    rows: List[List[str]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预览导入效果（根据调整后的字段定义重新生成预览）
    """
    try:
        preview = build_preview_table(headers, rows, fields)
        return JSONResponse({
            "success": True,
            "data": preview
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-template")
async def create_template_from_import(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("general"),
    fields: str = Form(...),  # JSON string
    filename: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    从导入数据直接创建模板
    """
    try:
        # 解析字段定义
        fields_list = json.loads(fields)

        if not fields_list:
            raise HTTPException(status_code=400, detail="字段列表不能为空")

        # 生成唯一编码
        code = f"imp_{uuid.uuid4().hex[:8]}"

        # 构建 modules 配置（与现有模板格式一致）
        modules = [
            {
                "name": "main",
                "label": "主表单",
                "fields": fields_list
            }
        ]

        # 创建模板
        template = Template(
            name=name,
            code=code,
            description=description or f"从 {filename} 导入生成",
            category=category,
            modules=modules,
            ai_generated=False,
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            is_published=True
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        return JSONResponse({
            "success": True,
            "message": "模板创建成功",
            "data": {
                "id": template.id,
                "name": template.name,
                "code": template.code,
                "category": template.category,
                "fields_count": len(fields_list),
                "created_at": template.created_at.isoformat() if template.created_at else None
            }
        })

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="字段数据格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.post("/import-data")
async def import_data_to_template(
    template_id: int,
    rows: str,  # JSON string: List[List[str]]
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    将数据行批量导入到指定模板（创建实例记录）
    """
    from app.models.workflow import TemplateInstance

    try:
        # 查询模板
        result = await db.execute(
            select(Template).where(Template.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 解析数据行
        data_rows = json.loads(rows)
        if not data_rows:
            raise HTTPException(status_code=400, detail="没有数据行")

        # 获取字段定义
        modules = template.modules or []
        all_fields = []
        for m in modules:
            if isinstance(m, dict) and 'fields' in m:
                all_fields.extend(m['fields'])

        if not all_fields:
            raise HTTPException(status_code=400, detail="模板中没有字段定义")

        # 创建实例
        created_count = 0
        for row in data_rows:
            row_data = {}
            for i, field in enumerate(all_fields):
                if i < len(row):
                    row_data[field['name']] = row[i]
                else:
                    row_data[field['name']] = ''

            instance_code = f"ins_{uuid.uuid4().hex[:8]}"
            instance = TemplateInstance(
                name=f"{template.name}_数据{created_count + 1}",
                code=instance_code,
                template_id=template_id,
                config={"data": row_data},
                organization_id=current_user.organization_id,
                created_by=current_user.id
            )
            db.add(instance)
            created_count += 1

        await db.commit()

        return JSONResponse({
            "success": True,
            "message": f"成功导入 {created_count} 条数据",
            "data": {
                "template_id": template_id,
                "template_name": template.name,
                "imported_count": created_count
            }
        })

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="数据格式错误")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/field-types")
async def get_field_types(
    current_user: User = Depends(get_current_user)
):
    """
    获取支持的字段类型列表（供前端使用）
    """
    return JSONResponse({
        "success": True,
        "data": [
            {"type": "text", "label": "单行文本", "icon": "Edit", "category": "基础"},
            {"type": "textarea", "label": "多行文本", "icon": "Document", "category": "基础"},
            {"type": "number", "label": "数字", "icon": "Minus", "category": "基础"},
            {"type": "money", "label": "金额", "icon": "Ticket", "category": "基础"},
            {"type": "password", "label": "密码", "icon": "Lock", "category": "基础"},
            {"type": "email", "label": "邮箱", "icon": "Message", "category": "基础"},
            {"type": "phone", "label": "电话", "icon": "Phone", "category": "基础"},
            {"type": "url", "label": "网址", "icon": "Link", "category": "基础"},
            {"type": "date", "label": "日期", "icon": "Calendar", "category": "日期"},
            {"type": "datetime", "label": "日期时间", "icon": "Timer", "category": "日期"},
            {"type": "time", "label": "时间", "icon": "Alarm", "category": "日期"},
            {"type": "daterange", "label": "日期范围", "icon": "DateRange", "category": "日期"},
            {"type": "select", "label": "下拉选择", "icon": "ArrowDown", "category": "选择"},
            {"type": "cascader", "label": "级联选择", "icon": "Share", "category": "选择"},
            {"type": "radio", "label": "单选", "icon": "Pointer", "category": "选择"},
            {"type": "checkbox", "label": "多选", "icon": "Finished", "category": "选择"},
            {"type": "switch", "label": "开关", "icon": "Open", "category": "选择"},
            {"type": "slider", "label": "滑块", "icon": "Operation", "category": "选择"},
            {"type": "rate", "label": "评分", "icon": "Star", "category": "选择"},
            {"type": "richtext", "label": "富文本", "icon": "Notebook", "category": "高级"},
            {"type": "upload", "label": "文件上传", "icon": "Upload", "category": "高级"},
            {"type": "image", "label": "图片上传", "icon": "Picture", "category": "高级"},
            {"type": "signature", "label": "签名", "icon": "EditPen", "category": "高级"},
            {"type": "divider", "label": "分隔线", "icon": "Minus", "category": "布局"},
            {"type": "heading", "label": "标题", "icon": "Title", "category": "布局"},
            {"type": "subform", "label": "子表单", "icon": "List", "category": "数据"},
            {"type": "relation", "label": "关联数据", "icon": "Connection", "category": "数据"},
            {"type": "autonum", "label": "自动编号", "icon": "Ticket", "category": "数据"},
            {"type": "location", "label": "地图位置", "icon": "Location", "category": "特殊"},
            {"type": "color", "label": "颜色选择", "icon": "Brush", "category": "特殊"},
            {"type": "user", "label": "人员选择", "icon": "User", "category": "特殊"},
            {"type": "org", "label": "部门选择", "icon": "OfficeBuilding", "category": "特殊"},
        ]
    })
