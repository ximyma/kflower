"""
文档转换 API 端点
提供文档格式转换、Excel→JSON 提取等功能
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import BaseResponse
from app.core.doc_converter import (
    convert_document,
    excel_to_json,
    auto_convert_for_upload,
    get_converter_status,
    SUPPORTED_INPUT_EXTS,
    SUPPORTED_OUTPUT_EXTS,
    CONVERSION_MAP,
)

router = APIRouter(prefix="/doc-converter", tags=["文档转换"])


@router.get("/status")
async def get_status(
    current_user: User = Depends(get_current_user),
):
    """获取文档转换服务状态"""
    status = get_converter_status()
    return BaseResponse(data=status)


@router.get("/supported-formats")
async def get_supported_formats(
    current_user: User = Depends(get_current_user),
):
    """获取支持的转换格式列表"""
    conversions = [
        {"from": src, "to": dst, "lo_format": lo_fmt}
        for (src, dst), lo_fmt in CONVERSION_MAP.items()
    ]
    # 加上 JSON 提取
    conversions.append({"from": "xlsx/xls/csv", "to": "json", "lo_format": "python"})

    return BaseResponse(data={
        "input_formats": sorted(SUPPORTED_INPUT_EXTS),
        "output_formats": sorted(SUPPORTED_OUTPUT_EXTS),
        "conversions": conversions,
    })


@router.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """
    上传文件并转换格式。
    支持：doc→docx、xls→xlsx、ppt→pptx、任意→pdf、xlsx/csv→json 等
    转换完成后返回文件下载。
    """
    src_ext = Path(file.filename or "").suffix.lstrip(".").lower()
    target_format = target_format.lower().lstrip(".")

    if src_ext not in SUPPORTED_INPUT_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的源格式: .{src_ext}，支持: {', '.join(sorted(SUPPORTED_INPUT_EXTS))}"
        )
    if target_format not in SUPPORTED_OUTPUT_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的目标格式: .{target_format}，支持: {', '.join(sorted(SUPPORTED_OUTPUT_EXTS))}"
        )

    # 保存上传文件到临时目录
    work_dir = tempfile.mkdtemp(prefix="kflower_upload_")
    try:
        input_path = os.path.join(work_dir, file.filename or f"input.{src_ext}")
        with open(input_path, "wb") as f_out:
            content = await file.read()
            f_out.write(content)

        # 执行转换
        result = convert_document(input_path, target_format, work_dir)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "转换失败"))

        output_path = result["output_path"]
        output_filename = Path(output_path).name

        # 返回文件（FileResponse 会在发送后删除 background task）
        # 这里使用 background 清理：先复制到另一个临时文件
        final_tmp = tempfile.mktemp(
            suffix=Path(output_path).suffix,
            prefix="kflower_out_"
        )
        shutil.copy2(output_path, final_tmp)

        return FileResponse(
            path=final_tmp,
            filename=output_filename,
            media_type="application/octet-stream",
            background=_cleanup_task(work_dir, final_tmp),
        )

    except HTTPException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-json")
async def extract_json(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    header_row: int = Form(0),
    max_rows: int = Form(2000),
    current_user: User = Depends(get_current_user),
):
    """
    将 Excel/CSV 提取为 JSON 数据（用于模板导入、数据预览）。
    返回字段列表和行数据。
    """
    src_ext = Path(file.filename or "").suffix.lstrip(".").lower()
    if src_ext not in ("xlsx", "xls", "ods", "csv"):
        raise HTTPException(
            status_code=400,
            detail=f"仅支持 Excel/CSV 格式（xlsx/xls/ods/csv），收到 .{src_ext}"
        )

    work_dir = tempfile.mkdtemp(prefix="kflower_json_")
    try:
        input_path = os.path.join(work_dir, file.filename or f"data.{src_ext}")
        with open(input_path, "wb") as f_out:
            f_out.write(await file.read())

        result = excel_to_json(
            input_path,
            sheet_name=sheet_name,
            header_row=header_row,
            max_rows=max_rows,
        )
        return BaseResponse(data=result)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


@router.post("/auto-convert")
async def auto_convert(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    自动转换：上传 doc/xls/ppt 等旧格式，自动转换为 docx/xlsx/pptx。
    用于知识库和模板上传时的前置处理。
    返回转换后文件的下载。
    """
    src_ext = Path(file.filename or "").suffix.lstrip(".").lower()

    work_dir = tempfile.mkdtemp(prefix="kflower_auto_")
    try:
        input_path = os.path.join(work_dir, file.filename or f"input.{src_ext}")
        with open(input_path, "wb") as f_out:
            f_out.write(await file.read())

        result = auto_convert_for_upload(input_path, work_dir)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "转换失败"))

        output_path = result["output_path"]
        converted = result.get("converted", False)
        output_filename = Path(output_path).name

        if not converted:
            # 无需转换，直接返回原文件
            final_tmp = tempfile.mktemp(
                suffix=Path(output_path).suffix,
                prefix="kflower_orig_"
            )
            shutil.copy2(output_path, final_tmp)
        else:
            final_tmp = tempfile.mktemp(
                suffix=Path(output_path).suffix,
                prefix="kflower_conv_"
            )
            shutil.copy2(output_path, final_tmp)

        return FileResponse(
            path=final_tmp,
            filename=output_filename,
            media_type="application/octet-stream",
            background=_cleanup_task(work_dir, final_tmp),
            headers={
                "X-Converted": str(converted).lower(),
                "X-Original-Name": file.filename or "",
                "X-Output-Name": output_filename,
            },
        )

    except HTTPException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-convert")
async def batch_convert(
    files: list[UploadFile] = File(...),
    target_format: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """
    批量转换多个文件（最多 20 个）。
    所有结果打包为 zip 压缩包返回。
    """
    import zipfile

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="单次最多转换 20 个文件")

    target_format = target_format.lower().lstrip(".")
    work_dir = tempfile.mkdtemp(prefix="kflower_batch_")
    results = []

    try:
        for f in files:
            src_ext = Path(f.filename or "").suffix.lstrip(".").lower()
            input_path = os.path.join(work_dir, f.filename or f"input.{src_ext}")
            with open(input_path, "wb") as fp:
                fp.write(await f.read())

            conv = convert_document(input_path, target_format, work_dir)
            results.append({
                "filename": f.filename,
                "success": conv.get("success", False),
                "output": Path(conv.get("output_path", "")).name if conv.get("success") else None,
                "error": conv.get("error"),
            })

        # 打包
        zip_path = os.path.join(work_dir, "converted.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                if r["success"] and r["output"]:
                    out_file = os.path.join(work_dir, r["output"])
                    if os.path.isfile(out_file):
                        zf.write(out_file, r["output"])

        final_zip = tempfile.mktemp(suffix=".zip", prefix="kflower_batch_")
        shutil.copy2(zip_path, final_zip)

        return FileResponse(
            path=final_zip,
            filename="converted.zip",
            media_type="application/zip",
            background=_cleanup_task(work_dir, final_zip),
        )

    except HTTPException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 辅助：后台清理任务
# ─────────────────────────────────────────────
class _cleanup_task:
    """FileResponse background 参数，发送完成后清理临时文件"""
    def __init__(self, *paths: str):
        self.paths = paths

    async def __call__(self) -> None:
        for p in self.paths:
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                elif os.path.isfile(p):
                    os.remove(p)
            except Exception:
                pass
