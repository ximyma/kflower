"""
魔塔社区 (ModelScope) 模型下载工具
用于替代 HuggingFace 下载，解决国内访问问题
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 模型映射：HuggingFace模型名 -> 魔塔社区模型名
MODELSCOPE_MODEL_MAP: Dict[str, str] = {
    # Embedding 模型
    "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "paraphrase-multilingual-mpnet-base-v2": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "shibing624/text2vec-base-chinese": "iic/text2vec-base-chinese",
    "BAAI/bge-small-zh-v1.5": "BAAI/bge-small-zh-v1.5",
    "BAAI/bge-base-zh-v1.5": "BAAI/bge-base-zh-v1.5",
    "BAAI/bge-large-zh-v1.5": "BAAI/bge-large-zh-v1.5",
    "BAAI/bge-m3": "BAAI/bge-m3",
    "moka-ai/m3e-small": "iic/m3e-small",
    "moka-ai/m3e-base": "iic/m3e-base",
    "moka-ai/m3e-large": "iic/m3e-large",
    "DMetaSoul/sbert-chinese-qmc-domain-v1": "damo/nlp_sbert-chinese-qmc-domain-v1",
    
    # Rerank 模型
    "BAAI/bge-reranker-v2-m3": "BAAI/bge-reranker-v2-m3",
    "BAAI/bge-reranker-base": "BAAI/bge-reranker-base",
    "BAAI/bge-reranker-large": "BAAI/bge-reranker-large",
    
    # OCR 模型 (如果有需要)
    "paddleocr": "iic/paddleocr",
}


def get_modelscope_model_id(hf_model_id: str) -> str:
    """获取魔塔社区的模型ID"""
    # 直接匹配
    if hf_model_id in MODELSCOPE_MODEL_MAP:
        return MODELSCOPE_MODEL_MAP[hf_model_id]
    
    # 尝试前缀匹配
    for hf_prefix, ms_prefix in [
        ("sentence-transformers/", "sentence-transformers/"),
        ("BAAI/", "BAAI/"),
        ("shibing624/", "iic/"),
        ("moka-ai/", "iic/"),
    ]:
        if hf_model_id.startswith(hf_prefix):
            return hf_model_id.replace(hf_prefix, ms_prefix, 1)
    
    # 默认返回原名称，让 ModelScope 尝试解析
    return hf_model_id


def download_model_from_modelscope(
    model_id: str,
    cache_dir: Optional[str] = None,
    local_dir: Optional[str] = None,
    revision: Optional[str] = None,
) -> Optional[str]:
    """
    从魔塔社区下载模型
    
    Args:
        model_id: HuggingFace 模型ID 或魔塔社区模型ID
        cache_dir: 缓存目录（可选）
        local_dir: 本地保存目录（可选，优先使用）
        revision: 模型版本（可选）
        
    Returns:
        模型本地路径，下载失败返回 None
    """
    try:
        # 尝试导入 modelscope
        try:
            from modelscope import snapshot_download
        except ImportError:
            logger.warning("modelscope 未安装，尝试安装...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "modelscope"])
            from modelscope import snapshot_download
        
        # 获取魔塔社区模型ID
        ms_model_id = get_modelscope_model_id(model_id)
        logger.info(f"从魔塔社区下载模型: {model_id} -> {ms_model_id}")
        
        # 设置缓存目录
        if cache_dir is None:
            from app.core.config import settings
            cache_dir = os.path.join(settings.PROJECT_ROOT, "models", "cache")
        
        os.makedirs(cache_dir, exist_ok=True)
        
        # 下载模型
        download_kwargs = {
            "model_id": ms_model_id,
            "cache_dir": cache_dir,
        }
        if revision:
            download_kwargs["revision"] = revision
        if local_dir:
            download_kwargs["local_dir"] = local_dir
            download_kwargs["local_dir_use_symlinks"] = False
        
        model_path = snapshot_download(**download_kwargs)
        logger.info(f"模型下载完成: {model_path}")
        return model_path
        
    except Exception as e:
        logger.error(f"从魔塔社区下载模型失败: {e}")
        return None


def ensure_model_downloaded(
    model_id: str,
    local_path: Optional[str] = None,
    cache_dir: Optional[str] = None,
) -> Optional[str]:
    """
    确保模型已下载，如果本地不存在则从魔塔社区下载
    
    Args:
        model_id: 模型ID
        local_path: 指定的本地路径（如果存在则直接使用）
        cache_dir: 缓存目录
        
    Returns:
        模型本地路径
    """
    # 如果指定了本地路径且存在，直接使用
    if local_path and os.path.exists(local_path):
        logger.info(f"使用本地模型: {local_path}")
        return local_path
    
    # 检查缓存中是否已存在
    if cache_dir:
        # 尝试从缓存目录查找
        model_name = model_id.replace("/", "--")
        possible_paths = [
            os.path.join(cache_dir, model_id),
            os.path.join(cache_dir, model_name),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"从缓存加载模型: {path}")
                return path
    
    # 从魔塔社区下载
    return download_model_from_modelscope(model_id, cache_dir=cache_dir)


# 兼容性：设置环境变量让 transformers 优先使用本地模型
def setup_modelscope_environment():
    """设置魔塔社区环境配置"""
    # 设置模型缓存目录
    from app.core.config import settings
    cache_dir = os.path.join(settings.PROJECT_ROOT, "models", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # 设置 transformers 缓存目录
    os.environ["TRANSFORMERS_CACHE"] = cache_dir
    os.environ["HF_HOME"] = cache_dir
    
    # 允许从魔塔社区下载（取消离线模式）
    # 注意：这需要在调用前设置，下载完成后可以重新设置离线模式
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    
    return cache_dir
