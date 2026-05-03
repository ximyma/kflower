"""
API路由 - 本地AI服务
支持：OCR识别、文本解析、嵌入向量、附件上传
"""
import io
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.schemas import BaseResponse
from app.core.ai_digital_base.local_services import (
    ocr_service, text_parser_service, embedding_service,
    OCRService, TextParserService, EmbeddingService, ST_AVAILABLE
)

router = APIRouter(prefix="/local-ai", tags=["本地AI服务"])


# ============= OCR 服务 =============

@router.post("/ocr/text")
async def ocr_extract_text(
    file: UploadFile = File(...),
    lang: str = Form("chi_sim+eng"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    OCR 文字识别 - 从图片中提取文字

    Args:
        file: 图片文件
        lang: 语言，默认 chi_sim+eng（简体中文+英文）

    Returns:
        {"success": true, "text": "...", "confidence": 0.95}
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        contents = await file.read()
        result = ocr_service.extract_text(contents, lang)

        if result["success"]:
            return JSONResponse({
                "success": True,
                "data": result,
                "message": f"识别成功，置信度 {result['confidence']:.0%}"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": result.get("error", "OCR识别失败")
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR处理失败: {str(e)}")


@router.post("/ocr/table")
async def ocr_extract_table(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    OCR 表格识别 - 从图片中提取表格数据

    Returns:
        {"success": true, "headers": [...], "rows": [[...], ...]}
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        contents = await file.read()
        result = ocr_service.extract_table(contents)

        if result["success"]:
            return JSONResponse({
                "success": True,
                "data": result,
                "message": f"识别到 {result['row_count']} 行 × {result['col_count']} 列"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": result.get("error", "表格识别失败")
            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"表格识别失败: {str(e)}")


@router.get("/ocr/status")
async def ocr_status(
    current_user: User = Depends(get_current_user)
):
    """获取 OCR 服务状态"""
    is_available = ocr_service.is_configured()
    return JSONResponse({
        "success": True,
        "data": {
            "available": is_available,  # 返回布尔值
            "tesseract_cmd": ocr_service.tesseract_path,
            "default_lang": ocr_service.default_lang,
        }
    })


@router.put("/ocr/config")
async def ocr_configure(
    tesseract_path: str = Form(...),
    lang: str = Form("chi_sim+eng"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """配置 OCR 服务（同时保存到数据库）"""
    # 1. 更新内存中的服务
    ocr_service.configure(tesseract_path, lang)
    
    # 2. 保存到数据库
    from sqlalchemy import select
    from app.models.ai import SystemConfig
    
    # 保存 tesseract_path
    result = await db.execute(
        select(SystemConfig).where(
            SystemConfig.key == "ocr_tesseract_path",
            SystemConfig.organization_id == None
        )
    )
    config = result.scalar_one_or_none()
    if config:
        config.value = tesseract_path
    else:
        config = SystemConfig(
            key="ocr_tesseract_path",
            value=tesseract_path,
            description="Tesseract OCR 安装路径",
            organization_id=None
        )
        db.add(config)
    
    # 保存 lang
    result = await db.execute(
        select(SystemConfig).where(
            SystemConfig.key == "ocr_lang",
            SystemConfig.organization_id == None
        )
    )
    config_lang = result.scalar_one_or_none()
    if config_lang:
        config_lang.value = lang
    else:
        config_lang = SystemConfig(
            key="ocr_lang",
            value=lang,
            description="OCR 识别语言",
            organization_id=None
        )
        db.add(config_lang)
    
    await db.commit()
    
    return JSONResponse({
        "success": True,
        "message": f"OCR 已配置并保存到数据库: {tesseract_path}"
    })


# ============= 文本解析服务 =============

@router.post("/text/segment")
async def text_segment(
    text: str = Form(...),
    mode: str = Form("default"),
    current_user: User = Depends(get_current_user)
):
    """
    文本分词

    Args:
        text: 输入文本
        mode: 分词模式 default/cut/search

    Returns:
        {"success": true, "words": [...], "pos": [...]}
    """
    result = text_parser_service.segment(text, mode)
    return JSONResponse(result)


@router.post("/text/keywords")
async def text_keywords(
    text: str = Form(...),
    top_k: int = Form(10),
    method: str = Form("tfidf"),
    current_user: User = Depends(get_current_user)
):
    """
    提取关键词

    Args:
        text: 输入文本
        top_k: 返回数量
        method: tfidf/textrank
    """
    result = text_parser_service.extract_keywords(text, top_k, method)
    return JSONResponse(result)


@router.post("/text/summary")
async def text_summary(
    text: str = Form(...),
    max_length: int = Form(200),
    current_user: User = Depends(get_current_user)
):
    """
    提取文本摘要

    Args:
        text: 输入文本
        max_length: 摘要最大长度
    """
    result = text_parser_service.extract_summary(text, max_length)
    return JSONResponse(result)


@router.post("/text/parse")
async def text_parse(
    text: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    结构化文本解析 - 提取实体、关系

    Returns:
        {"success": true, "entities": {"person": [...], "org": [...], ...}}
    """
    result = text_parser_service.parse_structured_data(text)
    return JSONResponse(result)


# ============= 嵌入向量服务 =============

@router.post("/embed")
async def embed_text(
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文本嵌入向量

    Returns:
        {"success": true, "embedding": [...], "model": "..."}
    """
    result = await embedding_service.embed_text(text)
    return JSONResponse(result)


@router.post("/embed/batch")
async def embed_batch(
    texts: str = Form(...),  # JSON string: List[str]
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量获取嵌入向量"""
    try:
        text_list = json.loads(texts)
        if not isinstance(text_list, list) or len(text_list) > 100:
            raise HTTPException(status_code=400, detail="最多支持100条文本")
        result = await embedding_service.embed_batch(text_list)
        return JSONResponse(result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="texts 格式错误，应为 JSON 数组")


@router.get("/embed/status")
async def embed_status(
    current_user: User = Depends(get_current_user)
):
    """获取嵌入服务状态"""
    from app.core.ai_digital_base.local_services import ST_AVAILABLE, EmbeddingService

    supported_models = EmbeddingService.get_supported_models()
    model_info = supported_models.get(embedding_service.embedding_model, {})

    return JSONResponse({
        "success": True,
        "data": {
            "api_key_configured": bool(embedding_service.embedding_api_key),
            "model": embedding_service.embedding_model,
            "base_url": embedding_service.embedding_api_base,
            "provider": embedding_service.embedding_provider,
            "st_available": ST_AVAILABLE,
            "st_device": embedding_service.st_device,
            "current_model_info": model_info,
            "supported_models": supported_models,
        }
    })


@router.put("/embed/config")
async def embed_configure(
    api_key: str = Form(None),
    api_base: str = Form(None),
    model: str = Form(None),
    provider: str = Form(None),
    st_device: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """配置嵌入服务"""
    from app.core.ai_digital_base.local_services import ST_AVAILABLE, EmbeddingService

    # 验证模型是否支持
    if model:
        supported = EmbeddingService.get_supported_models()
        if model not in supported:
            return JSONResponse({
                "success": False,
                "message": f"不支持的模型: {model}，请从支持的模型列表中选择"
            }, status_code=400)
        # 如果是本地模型但sentence-transformers不可用
        model_info = supported[model]
        if model_info["provider"] == "local" and not ST_AVAILABLE:
            return JSONResponse({
                "success": False,
                "message": f"本地模型 {model} 需要安装 sentence-transformers: pip install sentence-transformers"
            }, status_code=400)

    embedding_service.configure(api_key, api_base or None, model, provider, st_device)
    return JSONResponse({
        "success": True,
        "message": "嵌入服务配置已更新",
        "data": {
            "model": embedding_service.embedding_model,
            "provider": embedding_service.embedding_provider,
            "st_device": embedding_service.st_device,
        }
    })


# ============ 新增：Embedding 模型管理 API ============

@router.get("/embed/models")
async def embed_list_models(
    current_user: User = Depends(get_current_user)
):
    """获取所有可用的嵌入模型（包括内置和自定义）"""
    from app.core.ai_digital_base.local_services import ST_AVAILABLE, EmbeddingService
    
    models = embedding_service.get_all_models()
    
    return JSONResponse({
        "success": True,
        "data": {
            "models": models,
            "current_model": embedding_service.embedding_model,
            "current_provider": embedding_service.embedding_provider,
            "st_available": ST_AVAILABLE,
            "custom_models_count": len(embedding_service.get_custom_models()),
        }
    })


@router.post("/embed/models")
async def embed_add_model(
    model_config: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """添加自定义嵌入模型"""
    result = embedding_service.add_custom_model(model_config)
    return JSONResponse(result)


@router.put("/embed/models/{model_id}")
async def embed_update_model(
    model_id: str,
    model_config: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """更新自定义嵌入模型"""
    result = embedding_service.update_custom_model(model_id, model_config)
    if not result.get("success"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@router.delete("/embed/models/{model_id}")
async def embed_delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除自定义嵌入模型"""
    result = embedding_service.delete_custom_model(model_id)
    if not result.get("success"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@router.put("/embed/models/{model_id}/default")
async def embed_set_default_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """设置默认嵌入模型"""
    result = embedding_service.set_default_model(model_id)
    if not result.get("success"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


@router.post("/embed/models/{model_id}/test")
async def embed_test_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """测试嵌入模型"""
    from app.core.ai_digital_base.local_services import ST_AVAILABLE, EmbeddingService
    
    # 获取模型信息
    model_info = embedding_service._get_model_info(model_id)
    provider = model_info.get("provider", "api")
    
    # 临时切换到该模型进行测试
    original_model = embedding_service.embedding_model
    original_provider = embedding_service.embedding_provider
    original_api_key = embedding_service.embedding_api_key
    original_api_base = embedding_service.embedding_api_base
    
    try:
        embedding_service.embedding_model = model_id
        embedding_service.embedding_provider = provider
        
        if provider == "api":
            embedding_service.embedding_api_key = model_info.get("api_key")
            embedding_service.embedding_api_base = model_info.get("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        # 执行测试
        result = await embedding_service.embed_text("你好，这是一条测试文本。Hello, this is a test.")
        
        return JSONResponse({
            "success": result.get("success", False),
            "message": "测试成功" if result.get("success") else result.get("error", "测试失败"),
            "data": {
                "model": model_id,
                "provider": provider,
                "dimension": result.get("dimension") or (len(result.get("embedding", [])) if result.get("embedding") else 0),
                "embedding_preview": result.get("embedding", [])[:5] if result.get("embedding") else None,
            }
        })
    finally:
        # 恢复原配置
        embedding_service.embedding_model = original_model
        embedding_service.embedding_provider = original_provider
        embedding_service.embedding_api_key = original_api_key
        embedding_service.embedding_api_base = original_api_base


# ============= 附件处理（AI对话） =============

@router.post("/process-attachment")
async def process_attachment(
    file: UploadFile = File(...),
    operations: str = Form('["ocr", "segment"]'),  # JSON array
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    处理附件 - 支持 OCR + 分词 + 摘要

    Args:
        file: 上传的文件（图片/文本/Excel）
        operations: 要执行的操作列表 ["ocr", "segment", "keywords", "summary", "embed"]

    Returns:
        处理结果，包含所有操作的输出
    """
    try:
        operations_list = json.loads(operations)
    except json.JSONDecodeError:
        operations_list = ["segment"]

    results = {}
    content_text = ""

    # 根据文件类型处理
    content_type = file.content_type or ""

    if content_type.startswith("image/"):
        # 图片文件 - OCR
        contents = await file.read()
        if "ocr" in operations_list:
            ocr_result = ocr_service.extract_text(contents)
            results["ocr"] = ocr_result
            if ocr_result.get("success"):
                content_text = ocr_result["text"]

    elif content_type in ["text/plain", "application/json"]:
        # 纯文本
        contents = await file.read()
        try:
            content_text = contents.decode("utf-8")
        except UnicodeDecodeError:
            content_text = contents.decode("gbk", errors="ignore")
        results["text_preview"] = content_text[:500]

    elif content_type.endswith(".xlsx") or content_type.endswith(".xls") or content_type.endswith(".csv"):
        # Excel 文件
        results["excel"] = {"message": "Excel文件请使用导入功能处理"}
        content_text = f"[上传了Excel文件: {file.filename}]"

    else:
        # 其他文件
        results["file"] = {"filename": file.filename, "type": content_type}
        content_text = f"[上传了文件: {file.filename}]"

    # 执行文本分析操作
    if content_text:
        if "segment" in operations_list:
            results["segment"] = text_parser_service.segment(content_text[:10000])

        if "keywords" in operations_list:
            results["keywords"] = text_parser_service.extract_keywords(content_text[:10000])

        if "summary" in operations_list:
            results["summary"] = text_parser_service.extract_summary(content_text[:10000])

        if "parse" in operations_list:
            results["parse"] = text_parser_service.parse_structured_data(content_text[:10000])

        if "embed" in operations_list and content_text:
            embed_result = await embedding_service.embed_text(content_text[:8000])
            results["embed"] = embed_result

    return JSONResponse({
        "success": True,
        "filename": file.filename,
        "content_type": content_type,
        "content_text": content_text,
        "results": results,
        "operations": operations_list
    })


# ============= 服务状态总览 =============

@router.get("/services-status")
async def services_status(
    current_user: User = Depends(get_current_user)
):
    """获取所有本地AI服务状态"""
    return JSONResponse({
        "success": True,
        "data": {
            "ocr": {
                "available": TesseractOCRServiceAvailable(),
                "tesseract_path": ocr_service.tesseract_path,
                "default_lang": ocr_service.default_lang,
            },
            "jieba": {
                "available": text_parser_service.config is not None,
            },
            "embedding": {
                "configured": bool(embedding_service.embedding_api_key),
                "model": embedding_service.embedding_model,
                "provider": embedding_service.embedding_provider,
                "st_available": ST_AVAILABLE,
            }
        }
    })


def TesseractOCRServiceAvailable():
    """检查 Tesseract 是否可用"""
    try:
        import pytesseract
        return True
    except ImportError:
        return False
