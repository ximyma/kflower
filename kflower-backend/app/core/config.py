"""
核心配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, List
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "Kflower 企业智能管理低代码平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8878
    
    # 数据库配置 - 使用绝对路径
    DATABASE_URL: str = f"sqlite+aiosqlite:///{PROJECT_ROOT}/kflower-data/kflower.db"
    DB_ECHO: bool = False
    
    # JWT配置
    JWT_SECRET_KEY: str = "kflower-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # AI大模型配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    
    QWEN_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-max"
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 默认AI提供商
    AI_PROVIDER: str = "siliconflow"  # deepseek, qwen, siliconflow, ollama
    SILICONFLOW_API_KEY: Optional[str] = None
    SILICONFLOW_API_BASE: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "Qwen/Qwen3-8B"
    
    # 可用模型列表
    AVAILABLE_MODELS: Dict[str, List[str]] = {
        "siliconflow": [
            "Qwen/Qwen3-8B",
            "Qwen/Qwen3.5-4B",
            "BAAI/bge-m3",
            "BAAI/bge-reranker-v2-m3"
        ],
        "ollama": [
            "qwen3:8b",
            "llama3:8b",
            "gemma:7b"
        ],
        "deepseek": ["deepseek-chat"],
        "qwen": ["qwen-max"]
    }
    
    # Embedding配置
    EMBEDDING_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    EMBEDDING_MODEL: str = "text-embedding-v2"
    EMBEDDING_PROVIDER: str = "api"  # api/local  api用远程API，local用sentence-transformers
    SENTENCE_TRANSFORMERS_MODEL: str = f"{PROJECT_ROOT}/models/BAAI/bge-reranker-v2-m3"
    SENTENCE_TRANSFORMERS_DEVICE: str = "cpu"  # cpu/cuda
    
    # 向量数据库
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_ENABLED: bool = False
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]
    
    # 文件上传 - 使用绝对路径
    UPLOAD_DIR: str = f"{PROJECT_ROOT}/kflower-data/uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # OCR 配置
    TESSERACT_PATH: Optional[str] = None
    OCR_DEFAULT_LANG: str = "chi_sim+eng"
    
    # Ollama 配置
    OLLAMA_API_BASE: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_API_KEY: str = "ollama"  # Ollama 不需要实际API密钥
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 确保数据目录和上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)