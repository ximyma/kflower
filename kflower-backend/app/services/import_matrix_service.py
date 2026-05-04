# -*- coding: utf-8 -*-
"""
矩阵表格导入服务 - 处理二维表格（矩阵）的转换
将矩阵表格转换为标准一维表格
"""
import re
from typing import List, Dict, Any, Tuple, Optional
import re


def parse_matrix_table(
    all_rows: List[List[str]],
    row_header_row: int = 0,  # 行表头所在行（水平维度）
    col_header_col: int = 0,  # 列表头所在列（垂直维度）
    merge_type: str = "concat"  # 字段组合方式：concat/underline/none
) -> Dict[str, Any]:
    """
    解析矩阵表格，将其转换为一维表格结构
    
    参数：
    - all_rows: 所有行数据
    - row_header_row: 行表头行索引（包含列维度的行，如 "Q1", "Q2", "Q3"）
    - col_header_col: 列表头列索引（包含行维度的列，如 "产品A", "产品B"）
    - merge_type: 字段名组合方式
        - "concat": 行表头_列表头（如 "产品A_Q1"）
        - "underline": 行表头_列表头（下划线连接）
        - "none": 只用列表头（如 "Q1"）
    
    返回：
    {
        "row_headers": List[str],  # 行维度值（如 ["产品A", "产品B", "总计"]）
        "col_headers": List[str],  # 列维度值（如 ["Q1", "Q2", "Q3"]）
        "headers": List[str],      # 最终表头（用于创建模板）
        "rows": List[List[str]],   # 转换后的一维数据行
        "fields": List[dict],     # 生成的字段定义
        "matrix_preview": dict    # 矩阵预览（用于前端展示）
    }
    """
    if not all_rows or len(all_rows) == 0:
        return {"error": "数据为空"}
    
    # 1. 提取行表头（水平维度）
    row_header_row_data = all_rows[row_header_row] if row_header_row < len(all_rows) else all_rows[0]
    # 跳过列表头列，获取真正的列维度值
    col_headers = []
    for i, cell in enumerate(row_header_row_data):
        if i <= col_header_col:
            continue  # 跳过行维度列
        cell_value = _get_cell_value(cell)
        
        if cell_value:
            col_headers.append(cell_value)
        else:
            # 尝试从其他行获取表头（处理合并单元格或空单元格）
            header_val = _infer_header_from_context(all_rows, i, row_header_row)
            if header_val:
                col_headers.append(header_val)
            else:
                col_headers.append(f"列{i+1}")
    
    # 2. 提取列表头（垂直维度）
    row_headers = []
    for i, row in enumerate(all_rows):
        if i == row_header_row:
            continue  # 跳过行表头行
        if len(row) > col_header_col:
            cell = row[col_header_col]
            if cell and str(cell).strip():
                row_headers.append(str(cell).strip())
            else:
                row_headers.append(f"行{i+1}")
        else:
            row_headers.append(f"行{i+1}")
    
    # 3. 提取数据区域（除去行表头行和列表头列）
    data_rows = []
    for i, row in enumerate(all_rows):
        if i == row_header_row:
            continue  # 跳过行表头行
        data_row = []
        for j, cell in enumerate(row):
            if j <= col_header_col:
                continue  # 跳过列表头列
            data_row.append(str(cell).strip() if cell else "")
        data_rows.append(data_row)
    
    # 4. 推断数值字段类型（获取一个样本值）
    sample_value = ""
    for data_row in data_rows:
        if data_row and len(data_row) > 0:
            # 找到第一个非空值
            for cell in data_row:
                if cell and str(cell).strip():
                    sample_value = str(cell).strip()
                    break
            if sample_value:
                break
    
    # 5. 生成字段定义（矩阵表格转换为一维表格后只有3个字段）
    fields = []
    headers = []
    
    # 行维度字段（如"产品"）- 也使用 select 类型，options 为行表头值
    fields.append({
        "name": "row_dimension",
        "label": "行维度",
        "type": "select",
        "options": row_headers,
        "required": True,
        "width": "50%"
    })
    headers.append("行维度")
    
    # 列维度字段（如"季度"）
    fields.append({
        "name": "col_dimension",
        "label": "列维度",
        "type": "select",
        "options": col_headers,
        "required": True,
        "width": "50%"
    })
    headers.append("列维度")
    
    # 数值字段（如"销售额"）- 自动推断类型
    field_type = _infer_cell_type(sample_value)
    if field_type not in ["number", "money"]:
        field_type = "number"  # 矩阵表格的数值字段默认用 number
    
    fields.append({
        "name": "value",
        "label": "数值",
        "type": field_type,
        "required": False,
        "width": "50%"
    })
    headers.append("数值")
    
    # 6. 构建一维数据行
    rows = []
    for i, row_h in enumerate(row_headers):
        if i < len(data_rows):
            data_row = data_rows[i]
            for j, col_h in enumerate(col_headers):
                if j < len(data_row):
                    cell_value = data_row[j]
                else:
                    cell_value = ""
                
                row_data = [row_h, col_h, cell_value]
                rows.append(row_data)
    
    # 6. 矩阵预览（用于前端展示）
    matrix_preview = {
        "row_headers": row_headers,
        "col_headers": col_headers,
        "data_region": data_rows,
        "preview_rows": min(5, len(row_headers)),
        "preview_cols": min(5, len(col_headers))
    }
    
    return {
        "row_headers": row_headers,
        "col_headers": col_headers,
        "headers": headers,
        "rows": rows,
        "fields": fields,
        "total_rows": len(rows),
        "total_columns": len(headers),
        "matrix_preview": matrix_preview
    }


def detect_matrix_dimensions(all_rows: List[List[str]]) -> Dict[str, Any]:
    """
    自动检测矩阵表格的行列维度位置
    
    返回：
    {
        "detected_row_header_row": int,  # 建议的行表头行
        "detected_col_header_col": int,  # 建议的列表头列
        "confidence": float,              # 置信度 0-1
        "row_header_candidates": List[int],  # 候选行表头行
        "col_header_candidates": List[int]   # 候选列表头列
    }
    """
    if not all_rows or len(all_rows) == 0:
        return {"error": "数据为空"}
    
    num_rows = len(all_rows)
    num_cols = max(len(row) for row in all_rows) if all_rows else 0
    
    # 候选行表头行：第一行通常是列维度
    row_header_candidates = [0]  # 默认第一行
    for i in range(min(5, num_rows)):
        row = all_rows[i]
        # 判断是否为表头行：非空单元格较多，且包含文本而非数字
        non_empty = sum(1 for c in row if c and str(c).strip())
        if non_empty >= num_cols * 0.5:  # 至少一半列有值
            row_header_candidates.append(i)
    
    # 候选列表头列：第一列通常是行维度
    col_header_candidates = [0]  # 默认第一列
    for j in range(min(5, num_cols)):
        # 判断是否为表头列：非空单元格较多
        non_empty = sum(1 for row in all_rows if j < len(row) and row[j] and str(row[j]).strip())
        if non_empty >= num_rows * 0.5:
            col_header_candidates.append(j)
    
    return {
        "detected_row_header_row": 0,
        "detected_col_header_col": 0,
        "confidence": 0.8,
        "row_header_candidates": row_header_candidates[:5],
        "col_header_candidates": col_header_candidates[:5]
    }


def _infer_cell_type(value: str) -> str:
    """推断单元格的数据类型"""
    if not value or not str(value).strip():
        return "text"
    
    value_str = str(value).strip()
    
    # 检查是否为数字
    try:
        float(value_str)
        if '.' in value_str:
            return "number"
        return "number"
    except ValueError:
        pass
    
    # 检查是否为日期
    date_patterns = [
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
        r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
        r'\d{4}年\d{1,2}月\d{1,2}日'
    ]
    for pattern in date_patterns:
        if re.search(pattern, value_str):
            return "date"
    
    # 检查是否为邮箱
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value_str):
        return "email"
    
    # 检查是否为电话
    if re.match(r'^[\d\-\+\(\)\s]{7,20}$', value_str):
        return "phone"
    
    return "text"


def build_matrix_preview(
    all_rows: List[List[str]],
    row_header_row: int,
    col_header_col: int,
    max_preview_rows: int = 5,
    max_preview_cols: int = 5
) -> Dict[str, Any]:
    """
    构建矩阵表格的预览数据（用于前端展示）
    """
    if not all_rows or len(all_rows) == 0:
        return {}
    
    # 提取行表头
    row_headers = []
    for i, row in enumerate(all_rows):
        if i == row_header_row:
            continue
        if len(row) > col_header_col:
            row_headers.append(str(row[col_header_col]).strip() or f"行{i+1}")
        if len(row_headers) >= max_preview_rows:
            break
    
    # 提取列表头
    col_headers = []
    if row_header_row < len(all_rows):
        row = all_rows[row_header_row]
        for j, cell in enumerate(row):
            if j <= col_header_col:
                continue
            col_headers.append(str(cell).strip() or f"列{j+1}")
            if len(col_headers) >= max_preview_cols:
                break
    
    # 提取数据区域预览
    preview_data = []
    for i, row in enumerate(all_rows):
        if i == row_header_row:
            continue
        if len(preview_data) >= max_preview_rows:
            break
        data_row = []
        for j, cell in enumerate(row):
            if j <= col_header_col:
                continue
            if len(data_row) >= max_preview_cols:
                break
            data_row.append(str(cell).strip() if cell else "")
        preview_data.append(data_row)
    
    return {
        "row_headers": row_headers,
        "col_headers": col_headers,
        "preview_data": preview_data,
        "total_rows": len(all_rows) - 1,  # 减去表头行
        "total_cols": max(len(row) for row in all_rows) - 1 if all_rows else 0  # 减去表头列
    }

def _get_cell_value(cell: any) -> str:
    """安全获取单元格值"""
    if cell is None:
        return ""
    return str(cell).strip()

def _infer_header_from_context(all_rows: List[List[str]], col_idx: int, header_row_idx: int) -> str:
    """
    从上下文推断表头（处理合并单元格或空单元格）
    尝试从相邻行或列获取表头值
    改进：迭代搜索左边单元格，正确处理多列合并
    """
    if not all_rows or header_row_idx >= len(all_rows):
        return ""
    
    # 尝试从同一行的左边单元格获取（水平合并）
    # 迭代搜索，而不仅仅是直接左边的单元格
    for j in range(col_idx - 1, -1, -1):  # 从当前列向左搜索
        if j < len(all_rows[header_row_idx]):
            val = _get_cell_value(all_rows[header_row_idx][j])
            if val:
                return val  # 找到非空值，直接返回（处理水平合并）
    
    # 尝试从上方行获取（垂直合并）
    for i in range(header_row_idx - 1, -1, -1):  # 从当前行向上搜索
        if i < len(all_rows) and col_idx < len(all_rows[i]):
            val = _get_cell_value(all_rows[i][col_idx])
            if val:
                return val  # 找到非空值，直接返回（处理垂直合并）
    
    # 尝试从下方行获取（垂直合并，反向）
    for i in range(header_row_idx + 1, len(all_rows)):  # 从当前行向下搜索
        if i < len(all_rows) and col_idx < len(all_rows[i]):
            val = _get_cell_value(all_rows[i][col_idx])
            if val:
                return val  # 找到非空值，直接返回（处理垂直合并，反向）
    
    return ""
