# -*- coding: utf-8 -*-
"""
矩阵表格导入 API - 处理二维表格（矩阵）导入
完全独立于一维表格导入流程
"""
import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.import_matrix_service import (
    parse_matrix_table,
    detect_matrix_dimensions,
    build_matrix_preview
)


# ============ 请求/响应模型 ============

class MatrixParseRequest(BaseModel):
    """解析矩阵表格请求"""
    all_rows: List[List[str]]           # 所有行数据
    max_row_candidates: int = 5        # 最大行表头候选数
    max_col_candidates: int = 5        # 最大列表头候选数


class MatrixApplyRequest(BaseModel):
    """应用矩阵表头请求"""
    all_rows: List[List[str]]
    row_header_row: int = 0            # 行表头所在行（水平维度）
    col_header_col: int = 0            # 列表头所在列（垂直维度）
    merge_type: str = "concat"         # 字段名组合方式


class MatrixPreviewRequest(BaseModel):
    """预览矩阵表格转换结果请求"""
    all_rows: List[List[str]]
    row_header_row: int = 0
    col_header_col: int = 0
    max_preview_rows: int = 5
    max_preview_cols: int = 5


# ============ 路由定义 ============

router = APIRouter(prefix="/import/matrix", tags=["矩阵表格导入"])


@router.post("/parse")
async def parse_matrix(
    body: MatrixParseRequest,
    current_user: User = Depends(get_current_user)
):
    """
    解析矩阵表格，返回行列维度候选
    
    前端在上传文件并解析后，调用此接口获取：
    - 建议的行表头行（水平维度）
    - 建议的列表头列（垂直维度）
    - 候选行列列表
    """
    try:
        all_rows = body.all_rows
        
        if not all_rows or len(all_rows) == 0:
            return JSONResponse({
                "success": False,
                "message": "数据为空"
            }, status_code=400)
        
        # 自动检测维度位置
        detection = detect_matrix_dimensions(all_rows)
        
        if "error" in detection:
            return JSONResponse({
                "success": False,
                "message": detection["error"]
            }, status_code=400)
        
        # 构建候选列表
        row_header_candidates = []
        for idx in detection.get("row_header_candidates", [0]):
            if idx < len(all_rows):
                row = all_rows[idx]
                preview = ' | '.join([str(c).strip() for c in row[:8] if c and str(c).strip()])
                row_header_candidates.append({
                    "row": idx,
                    "preview": preview if preview else f'第{idx+1}行',
                    "is_detected": idx == detection["detected_row_header_row"]
                })
        
        col_header_candidates = []
        max_cols = max(len(row) for row in all_rows) if all_rows else 0
        for idx in detection.get("col_header_candidates", [0]):
            if idx < max_cols:
                # 提取第idx列的所有值
                col_values = []
                for row in all_rows:
                    if idx < len(row):
                        col_values.append(str(row[idx]).strip())
                    if len(col_values) >= 8:
                        break
                preview = ' | '.join([v for v in col_values if v])
                col_header_candidates.append({
                    "col": idx,
                    "preview": preview if preview else f'第{idx+1}列',
                    "is_detected": idx == detection["detected_col_header_col"]
                })
        
        return JSONResponse({
            "success": True,
            "message": "矩阵解析成功",
            "data": {
                "detected_row_header_row": detection["detected_row_header_row"],
                "detected_col_header_col": detection["detected_col_header_col"],
                "confidence": detection["confidence"],
                "row_header_candidates": row_header_candidates[:body.max_row_candidates],
                "col_header_candidates": col_header_candidates[:body.max_col_candidates],
                "total_rows": len(all_rows),
                "total_cols": max_cols
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)


@router.post("/apply-header")
async def apply_matrix_header(
    body: MatrixApplyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    应用行列表头，生成字段定义
    
    前端在用户选择行列维度后，调用此接口生成：
    - 转换后的一维表格数据
    - 对应的字段定义
    - 预览数据
    """
    try:
        all_rows = body.all_rows
        row_header_row = body.row_header_row
        col_header_col = body.col_header_col
        merge_type = body.merge_type
        
        if not all_rows or len(all_rows) == 0:
            return JSONResponse({
                "success": False,
                "message": "数据为空"
            }, status_code=400)
        
        # 调用 Service 转换矩阵
        result = parse_matrix_table(
            all_rows=all_rows,
            row_header_row=row_header_row,
            col_header_col=col_header_col,
            merge_type=merge_type
        )
        
        if "error" in result:
            return JSONResponse({
                "success": False,
                "message": result["error"]
            }, status_code=400)
        
        return JSONResponse({
            "success": True,
            "message": f"已应用矩阵表头，共 {result['total_rows']} 行数据",
            "data": {
                "row_headers": result["row_headers"],
                "col_headers": result["col_headers"],
                "headers": result["headers"],
                "rows": result["rows"][:50],  # 预览前50行
                "all_rows": result["rows"],
                "total_rows": result["total_rows"],
                "total_columns": result["total_columns"],
                "fields": result["fields"],
                "matrix_preview": result["matrix_preview"]
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)


@router.post("/preview")
async def preview_matrix(
    body: MatrixPreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """
    预览矩阵表格转换结果
    
    前端在选择行列维度后，调用此接口获取预览数据
    """
    try:
        all_rows = body.all_rows
        row_header_row = body.row_header_row
        col_header_col = body.col_header_col
        
        if not all_rows or len(all_rows) == 0:
            return JSONResponse({
                "success": False,
                "message": "数据为空"
            }, status_code=400)
        
        # 构建预览
        preview = build_matrix_preview(
            all_rows=all_rows,
            row_header_row=row_header_row,
            col_header_col=col_header_col,
            max_preview_rows=body.max_preview_rows,
            max_preview_cols=body.max_preview_cols
        )
        
        return JSONResponse({
            "success": True,
            "data": preview
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)
