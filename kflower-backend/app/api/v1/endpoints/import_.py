# -*- coding: utf-8 -*-
"""
智能导入 API - 统一入口
支持 Excel/CSV/Word/图片/JSON 文件解析，智能表头检测和用户自选
"""
import json
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Template
from app.services.import_service import (
    parse_file, generate_fields, build_preview,
    get_dependencies_status, apply_header_row
)


class ApplyHeaderRequest(BaseModel):
    all_rows: List[List[str]]
    header_row: int = 0

router = APIRouter(prefix="/import", tags=["智能导入"])


@router.get("/status")
async def get_import_status(current_user: User = Depends(get_current_user)):
    """
    获取智能导入功能的依赖组件状态
    """
    status = get_dependencies_status()
    return JSONResponse({
        "success": True,
        "data": status
    })


@router.post("/parse")
async def parse_upload_file(
    file: UploadFile = File(...),
    header_row: int = Form(0),
    sheet_name: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    解析文件并返回候选表头行列表
    
    返回数据包含：
    - all_rows: 所有原始行数据
    - potential_headers: 候选表头行列表（带置信度）
    - detected_header_row: 智能检测的最佳表头行
    - source: 数据来源类型
    
    前端需要：
    1. 显示候选表头行让用户选择
    2. 用户选择后调用 /import/apply-header 确认
    """
    try:
        contents = await file.read()
        filename = file.filename or 'unknown'
        
        # 解析文件，获取原始数据和候选表头
        result = parse_file(
            file_bytes=contents,
            filename=filename,
            header_row=header_row,
            sheet_name=sheet_name if sheet_name else None
        )
        
        # 获取基本信息
        source = result.get('source', 'unknown')
        file_type = result.get('file_type', 'unknown')
        all_rows = result.get('all_rows', [])
        
        if not all_rows:
            return JSONResponse({
                "success": False,
                "message": "未能解析到有效数据"
            })
        
        # 获取候选表头行列表
        potential_headers = result.get('potential_headers', [])
        detected_row = result.get('detected_header_row', 0)
        
        # 如果没有候选表头，构建默认列表
        if not potential_headers:
            potential_headers = []
            for idx, row in enumerate(all_rows[:10]):
                preview = ' | '.join([c.strip() for c in row[:5] if c.strip()])
                if not preview:
                    preview = '(空行)'
                potential_headers.append({
                    'row': idx,
                    'cells': row,
                    'preview': preview if preview else f'第{idx + 1}行',
                    'is_potential': idx == detected_row,
                    'confidence': 1.0 if idx == detected_row else 0.3
                })
        
        # 获取文件名
        template_name = filename.rsplit('.', 1)[0] if filename else '未命名'
        
        return JSONResponse({
            "success": True,
            "message": f"成功解析 {source} 文件，共 {len(all_rows)} 行数据",
            "data": {
                "all_rows": all_rows[:50],  # 限制返回行数
                "potential_headers": potential_headers,
                "detected_header_row": detected_row,
                "filename": filename,
                "template_name": template_name,
                "source": source,
                "file_type": file_type,
                "sheet_names": result.get('sheet_names', []),
                "current_sheet": result.get('current_sheet', ''),
                "extracted_text": result.get('extracted_text', '')
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        return JSONResponse({
            "success": False,
            "message": error_msg,
            "detail": error_msg
        }, status_code=400)


@router.post("/apply-header")
async def apply_selected_header(
    body: ApplyHeaderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    用户选择表头行后，应用表头并生成字段定义
    
    前端以 JSON body 调用此接口，确认表头行后生成表单字段
    """
    try:
        all_rows = body.all_rows
        header_row = body.header_row

        if not all_rows:
            return JSONResponse({
                "success": False,
                "message": "数据不能为空"
            }, status_code=400)

        # 将所有元素统一转为字符串（前端数据可能包含数字等类型）
        all_rows = [[str(cell) if cell is not None else '' for cell in row] for row in all_rows]
        
        # 确保索引有效
        header_row = max(0, min(header_row, len(all_rows) - 1))
        
        # 获取表头和数据
        headers = all_rows[header_row]
        rows = all_rows[header_row + 1:]
        
        if not headers:
            return JSONResponse({
                "success": False,
                "message": "选定的表头行为空"
            }, status_code=400)
        
        # 生成字段定义
        fields = generate_fields(headers, rows[:50])
        
        # 构建预览
        preview = build_preview(headers, rows, fields)
        
        return JSONResponse({
            "success": True,
            "message": f"已应用表头，共 {len(headers)} 个字段，{len(rows)} 行数据",
            "data": {
                "headers": headers,
                "rows": rows[:20],
                "all_rows": all_rows,
                "total_rows": len(rows),
                "total_columns": len(headers),
                "fields": fields,
                "preview": preview,
                "header_row": header_row
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)


@router.post("/preview")
async def preview_import(
    fields: List[dict],
    headers: List[str],
    rows: List[List[str]],
    current_user: User = Depends(get_current_user)
):
    """
    预览导入效果
    """
    try:
        preview = build_preview(headers, rows, fields)
        return JSONResponse({
            "success": True,
            "data": preview
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)


@router.post("/create-template")
async def create_template_from_import(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("general"),
    fields: str = Form(...),  # JSON string
    filename: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    从导入数据创建模板
    """
    try:
        fields_list = json.loads(fields)
        
        if not fields_list:
            return JSONResponse({
                "success": False,
                "message": "字段列表不能为空"
            }, status_code=400)
        
        code = f"imp_{uuid.uuid4().hex[:8]}"
        
        modules = [
            {
                "name": "main",
                "label": "主表单",
                "fields": fields_list
            }
        ]
        
        template = Template(
            name=name,
            code=code,
            description=description or f"从 {filename} 导入生成",
            category=category,
            modules=modules,
            ai_generated=False,
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            is_published=False,  # 默认草稿状态
            is_public=False
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
        return JSONResponse({
            "success": False,
            "message": "字段数据格式错误"
        }, status_code=400)
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"创建模板失败: {str(e)}"
        }, status_code=500)


@router.get("/field-types")
async def get_field_types(current_user: User = Depends(get_current_user)):
    """
    获取支持的字段类型列表
    """
    return JSONResponse({
        "success": True,
        "data": [
            {"type": "text", "label": "单行文本", "category": "基础"},
            {"type": "textarea", "label": "多行文本", "category": "基础"},
            {"type": "number", "label": "数字", "category": "基础"},
            {"type": "money", "label": "金额", "category": "基础"},
            {"type": "email", "label": "邮箱", "category": "基础"},
            {"type": "phone", "label": "电话", "category": "基础"},
            {"type": "url", "label": "网址", "category": "基础"},
            {"type": "date", "label": "日期", "category": "日期"},
            {"type": "datetime", "label": "日期时间", "category": "日期"},
            {"type": "time", "label": "时间", "category": "日期"},
            {"type": "select", "label": "下拉选择", "category": "选择"},
            {"type": "radio", "label": "单选", "category": "选择"},
            {"type": "checkbox", "label": "多选", "category": "选择"},
            {"type": "switch", "label": "开关", "category": "选择"},
            {"type": "rate", "label": "评分", "category": "选择"},
            {"type": "slider", "label": "滑块", "category": "选择"},
            {"type": "upload", "label": "文件上传", "category": "高级"},
            {"type": "image", "label": "图片上传", "category": "高级"},
            {"type": "divider", "label": "分隔线", "category": "布局"},
            {"type": "heading", "label": "标题", "category": "布局"},
        ]
    })
