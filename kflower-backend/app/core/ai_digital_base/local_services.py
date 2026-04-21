# -*- coding: utf-8 -*-
"""
本地AI服务 - OCR、文本解析、嵌入向量、本地模型
"""
import re
import io
import uuid
import json
import os
import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Tesseract OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# 图像处理
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# jieba 分词
try:
    import jieba
    import jieba.analyse
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

# 向量嵌入
try:
    import httpx
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

# sentence-transformers 本地模型
try:
    # 禁止自动从 HuggingFace 下载模型
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


class OCRService:
    """OCR 文字识别服务"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # 从配置文件读取 Tesseract 路径
        from app.core.config import settings
        self.tesseract_path = self.config.get("tesseract_path", settings.TESSERACT_PATH)
        self.default_lang = self.config.get("lang", settings.OCR_DEFAULT_LANG)
        
        # 尝试从数据库读取配置
        self._load_from_db()
        
        # 如果配置了 Tesseract 路径，设置环境变量
        if self.tesseract_path:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            except Exception:
                pass

    def _load_from_db(self):
        """从数据库加载配置"""
        try:
            from app.core.config import settings
            db_path = settings.DATABASE_URL
            
            if 'sqlite' in db_path:
                if ':///' in db_path:
                    db_file = db_path.split(':///')[-1]
                else:
                    db_file = db_path.split('://')[1]
                
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 读取 OCR 配置
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'ocr_tesseract_path' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    self.tesseract_path = row[0]
                
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'ocr_lang' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    self.default_lang = row[0]
                
                conn.close()
        except Exception:
            pass

    def configure(self, tesseract_path: str = None, lang: str = None):
        """配置 OCR"""
        if tesseract_path:
            self.tesseract_path = tesseract_path
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            except Exception:
                pass
        if lang:
            self.default_lang = lang

    def is_configured(self) -> bool:
        """检查 OCR 是否已正确配置"""
        if not TESSERACT_AVAILABLE:
            return False
        if not self.tesseract_path:
            return False
        try:
            import pytesseract
            version = pytesseract.get_tesseract_version()
            return version is not None
        except Exception:
            return False

    def extract_text(self, image_data: bytes, lang: str = None) -> Dict[str, Any]:
        """
        从图片中提取文字

        Args:
            image_data: 图片二进制数据
            lang: 语言代码，默认 chi_sim+eng

        Returns:
            {"success": True, "text": "...", "confidence": 0.95}
        """
        if not TESSERACT_AVAILABLE:
            return {"success": False, "error": "Tesseract OCR 未安装"}

        lang = lang or self.default_lang

        try:
            # 打开并预处理图片
            pil_img = Image.open(io.BytesIO(image_data))
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            # 图像预处理
            processed_img = self._preprocess(pil_img)

            # OCR 识别
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(
                processed_img,
                lang=lang,
                config=custom_config
            )

            # 估算置信度
            data = pytesseract.image_to_data(
                processed_img,
                lang=lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5

            return {
                "success": True,
                "text": text.strip(),
                "confidence": round(avg_confidence, 2),
                "lang": lang
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_table(self, image_data: bytes) -> Dict[str, Any]:
        """
        从图片中提取表格数据

        Returns:
            {"success": True, "headers": [...], "rows": [[...], ...]}
        """
        if not TESSERACT_AVAILABLE:
            return {"success": False, "error": "Tesseract OCR 未安装"}

        try:
            pil_img = Image.open(io.BytesIO(image_data))
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")

            # 预处理
            processed = self._preprocess(pil_img)

            # 表格识别
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(
                processed,
                lang=self.default_lang,
                config=custom_config
            )

            # 解析表格结构
            headers, rows = self._parse_table_text(text)

            return {
                "success": True,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "col_count": len(headers)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _preprocess(self, pil_img: Image.Image) -> Image.Image:
        """图像预处理"""
        if CV2_AVAILABLE:
            img_array = np.array(pil_img)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            # 自适应二值化
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )
            # 降噪
            denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
            return Image.fromarray(denoised)
        else:
            return pil_img

    def _parse_table_text(self, text: str) -> tuple:
        """解析 OCR 表格文本"""
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if not lines:
            return [], []

        # 尝试用分隔符分割列
        headers = []
        rows = []

        for i, line in enumerate(lines):
            # 尝试多种分隔符
            cells = None
            for sep in ["\t", " │ ", " │ ", "    ", "  "]:
                if sep in line:
                    cells = [c.strip() for c in line.split(sep) if c.strip()]
                    break

            if cells is None:
                # 用正则分割（连续的空格或制表符）
                cells = re.split(r"\s{2,}", line)

            cells = [c.strip() for c in cells if c.strip()]

            if len(cells) >= 2:
                if i == 0:
                    headers = cells
                else:
                    rows.append(cells)

        if not headers and rows:
            headers = [f"列{i+1}" for i in range(len(rows[0]))]

        return headers, rows


class TextParserService:
    """文本解析服务 - jieba 分词"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        if JIEBA_AVAILABLE:
            # 初始化 jieba
            jieba.initialize()

    def segment(self, text: str, mode: str = "default") -> Dict[str, Any]:
        """
        文本分词

        Args:
            text: 输入文本
            mode: 分词模式 default/cut/search

        Returns:
            {"success": True, "words": [...], "pos": [...]}
        """
        if not JIEBA_AVAILABLE:
            return {"success": False, "error": "jieba 未安装"}

        try:
            if mode == "cut":
                words = list(jieba.cut(text))
            elif mode == "search":
                words = list(jieba.cut_for_search(text))
            else:
                words = list(jieba.cut(text))

            # 词性标注
            pos_seg = list(jieba.posseg.cut(text))
            pos = [{"word": w, "flag": p.flag} for w, p in pos_seg]

            return {
                "success": True,
                "words": words,
                "pos": pos,
                "word_count": len(words)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_keywords(self, text: str, top_k: int = 10, method: str = "tfidf") -> Dict[str, Any]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回数量
            method: tfidf/textrank

        Returns:
            {"success": True, "keywords": [{"word": "...", "weight": 0.5}, ...]}
        """
        if not JIEBA_AVAILABLE:
            return {"success": False, "error": "jieba 未安装"}

        try:
            if method == "textrank":
                keywords = jieba.analyse.textrank(text, topK=top_k, withWeight=True)
            else:
                keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)

            return {
                "success": True,
                "keywords": [{"word": w, "weight": round(score, 4)} for w, score in keywords],
                "method": method
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_summary(self, text: str, max_length: int = 200) -> Dict[str, Any]:
        """提取文本摘要"""
        if not JIEBA_AVAILABLE:
            return {"success": False, "error": "jieba 未安装"}

        try:
            summary = jieba.analyse.extract_tags(
                text,
                topK=20,
                withWeight=True
            )
            summary_text = "，".join([w for w, _ in summary])
            if len(summary_text) > max_length:
                summary_text = summary_text[:max_length] + "..."

            return {
                "success": True,
                "summary": summary_text,
                "keywords": [w for w, _ in summary[:5]]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def parse_structured_data(self, text: str) -> Dict[str, Any]:
        """
        解析结构化数据（从文本中提取实体和关系）

        Returns:
            {"success": True, "entities": {...}, "structured": {...}}
        """
        if not JIEBA_AVAILABLE:
            return {"success": False, "error": "jieba 未安装"}

        try:
            words = list(jieba.cut(text))
            pos = list(jieba.posseg.cut(text))

            entities = {
                "person": [],   # 人名
                "org": [],      # 组织名
                "location": [], # 地名
                "time": [],     # 时间
                "number": []    # 数字
            }

            for word, flag in pos:
                if flag == "nr" and word not in entities["person"]:
                    entities["person"].append(word)
                elif flag == "ns" and word not in entities["location"]:
                    entities["location"].append(word)
                elif flag == "nt" and word not in entities["org"]:
                    entities["org"].append(word)
                elif flag == "t":
                    entities["time"].append(word)

            # 清理空分类
            entities = {k: v for k, v in entities.items() if v}

            return {
                "success": True,
                "entities": entities,
                "word_count": len(words),
                "pos_tags": [{"word": w, "flag": p.flag} for w, p in pos]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


class EmbeddingService:
    """嵌入向量服务 - 支持API和本地sentence-transformers"""

    # 支持的嵌入模型列表
    SUPPORTED_MODELS = {
        # API模型
        "text-embedding-v2": {"provider": "api", "dimension": 1536, "description": "DashScope text-embedding-v2"},
        "text-embedding-v3": {"provider": "api", "dimension": 1024, "description": "DashScope text-embedding-v3"},
        "text-embedding-3-small": {"provider": "api", "dimension": 1536, "description": "OpenAI small"},
        "text-embedding-3-large": {"provider": "api", "dimension": 3072, "description": "OpenAI large"},
        # sentence-transformers 本地模型
        "all-MiniLM-L6-v2": {"provider": "local", "dimension": 384, "description": "轻量级英文模型(80MB)"},
        "paraphrase-multilingual-MiniLM-L12-v2": {"provider": "local", "dimension": 384, "description": "多语言模型(420MB)"},
        "paraphrase-multilingual-mpnet-base-v2": {"provider": "local", "dimension": 768, "description": "多语言高质量(970MB)"},
        "shibing624/text2vec-base-chinese": {"provider": "local", "dimension": 768, "description": "中文文本向量化(400MB)"},
        "DMetaSoul/sbert-chinese-qmc-domain-v1": {"provider": "local", "dimension": 768, "description": "中文领域模型"},
        "moka-ai/m3e-small": {"provider": "local", "dimension": 512, "description": "M3E小型中文模型"},
        "moka-ai/m3e-base": {"provider": "local", "dimension": 768, "description": "M3E基础中文模型"},
        "moka-ai/m3e-large": {"provider": "local", "dimension": 1024, "description": "M3E大型中文模型"},
        "BAAI/bge-small-zh-v1.5": {"provider": "local", "dimension": 512, "description": "BGE小型中文模型"},
        "BAAI/bge-base-zh-v1.5": {"provider": "local", "dimension": 768, "description": "BGE基础中文模型"},
        "BAAI/bge-large-zh-v1.5": {"provider": "local", "dimension": 1024, "description": "BGE大型中文模型"},
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.embedding_api_key = self.config.get("embedding_api_key")
        self.embedding_api_base = self.config.get("embedding_api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.embedding_model = self.config.get("embedding_model", "text-embedding-v2")
        self.embedding_provider = self.config.get("embedding_provider", "api")  # api/local
        self.st_device = self.config.get("st_device", "cpu")
        self._local_models: Dict[str, Any] = {}  # 缓存已加载的本地模型
        
        # ============ 新增：多模型配置支持 ============
        # 用户配置的模型列表
        self._custom_models: Dict[str, Dict[str, Any]] = {}
        # 当前使用的模型配置
        self._current_model_config: Dict[str, Any] = {}
        
        # 优先从数据库加载配置
        if not self._load_from_db():
            # 如果数据库没有，加载本地配置
            self._load_custom_models()

    def _load_from_db(self) -> bool:
        """从数据库加载嵌入模型配置"""
        try:
            from app.core.config import settings
            db_path = settings.DATABASE_URL
            
            if 'sqlite' in db_path:
                if ':///' in db_path:
                    db_file = db_path.split(':///')[-1]
                else:
                    db_file = db_path.split('://')[1]
                
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 读取嵌入模型配置
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'embedding_model' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    self.embedding_model = row[0]
                
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'embedding_api_key' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    self.embedding_api_key = row[0]
                
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'embedding_api_base' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    self.embedding_api_base = row[0]
                
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'embedding_provider' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    self.embedding_provider = row[0]
                
                cursor.execute("SELECT value FROM system_configs WHERE `key` = 'embedding_custom_models' AND organization_id IS NULL")
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        import json
                        custom_models = json.loads(row[0])
                        if isinstance(custom_models, dict):
                            self._custom_models = custom_models
                    except:
                        pass
                
                conn.close()
                return True
        except Exception:
            pass
        return False

    def _save_to_db(self) -> bool:
        """保存嵌入模型配置到数据库"""
        try:
            from app.core.config import settings
            db_path = settings.DATABASE_URL
            
            if 'sqlite' in db_path:
                if ':///' in db_path:
                    db_file = db_path.split(':///')[-1]
                else:
                    db_file = db_path.split('://')[1]
                
                import sqlite3
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                configs = [
                    ('embedding_model', self.embedding_model),
                    ('embedding_api_key', self.embedding_api_key or ''),
                    ('embedding_api_base', self.embedding_api_base),
                    ('embedding_provider', self.embedding_provider),
                ]
                
                for key, value in configs:
                    cursor.execute(
                        "INSERT OR REPLACE INTO system_configs (`key`, value, organization_id) VALUES (?, ?, NULL)",
                        (key, value)
                    )
                
                # 保存自定义模型列表
                import json
                cursor.execute(
                    "INSERT OR REPLACE INTO system_configs (`key`, value, organization_id, value_type) VALUES (?, ?, NULL, 'json')",
                    ('embedding_custom_models', json.dumps(self._custom_models, ensure_ascii=False))
                )
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            pass
        return False
    
    def _load_custom_models(self):
        """从配置文件加载自定义模型列表"""
        import os
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_file = os.path.join(config_dir, "embedding_models.json")
        try:
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._custom_models = data.get("models", {})
                    # 设置当前模型
                    default_model = data.get("default_model")
                    if default_model and default_model in self._custom_models:
                        self._current_model_config = self._custom_models[default_model]
                        self.embedding_model = default_model
                        self.embedding_api_key = self._current_model_config.get("api_key")
                        self.embedding_api_base = self._current_model_config.get("api_base", self.embedding_api_base)
                        self.embedding_provider = self._current_model_config.get("provider", "api")
                        self.st_device = self._current_model_config.get("device", "cpu")
        except Exception as e:
            print(f"加载 embedding 模型配置失败: {e}")
    
    def _save_custom_models(self):
        """保存自定义模型列表到配置文件和数据库"""
        import os
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_file = os.path.join(config_dir, "embedding_models.json")
        try:
            default_model = self.embedding_model if self.embedding_model in self._custom_models else None
            data = {
                "models": self._custom_models,
                "default_model": default_model
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 同时保存到数据库
            self._save_to_db()
            return True
        except Exception as e:
            print(f"保存 embedding 模型配置失败: {e}")
            return False

    @staticmethod
    def get_supported_models() -> Dict[str, Dict[str, Any]]:
        """获取所有支持的嵌入模型列表"""
        return EmbeddingService.SUPPORTED_MODELS.copy()
    
    def get_custom_models(self) -> Dict[str, Dict[str, Any]]:
        """获取用户自定义的模型列表"""
        return self._custom_models.copy()
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """获取所有可用的模型（包括内置和自定义）"""
        all_models = []
        
        # 内置模型
        for name, info in self.SUPPORTED_MODELS.items():
            model_item = {
                "id": name,
                "name": name,
                "model": name,
                "provider": info.get("provider", "api"),
                "dimension": info.get("dimension", 1536),
                "description": info.get("description", ""),
                "is_builtin": True,
                "available": True,
                "is_default": name == self.embedding_model
            }
            all_models.append(model_item)
        
        # 自定义模型
        for model_id, cfg in self._custom_models.items():
            # 避免重复
            if model_id not in self.SUPPORTED_MODELS:
                all_models.append({
                    "id": model_id,
                    "name": cfg.get("name", model_id),
                    "model": cfg.get("model", model_id),
                    "provider": cfg.get("provider", "api"),
                    "dimension": cfg.get("dimension", 1536),
                    "description": cfg.get("description", ""),
                    "api_key": cfg.get("api_key"),
                    "api_base": cfg.get("api_base", ""),
                    "model_path": cfg.get("model_path", ""),
                    "device": cfg.get("device", "cpu"),
                    "is_builtin": False,
                    "available": True,
                    "is_default": model_id == self.embedding_model
                })
        
        return all_models
    
    def add_custom_model(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """添加自定义模型"""
        model_id = model_config.get("model") or model_config.get("model_id")
        if not model_id:
            return {"success": False, "error": "模型ID不能为空"}
        
        # 保存到自定义模型列表
        self._custom_models[model_id] = {
            "name": model_config.get("name", model_id),
            "model": model_id,
            "provider": model_config.get("provider", "api"),
            "dimension": model_config.get("dimension", 1536),
            "description": model_config.get("description", ""),
            "api_key": model_config.get("api_key", ""),
            "api_base": model_config.get("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            "model_path": model_config.get("model_path", ""),
            "device": model_config.get("device", "cpu"),
            "batch_size": model_config.get("batch_size", 32),
            "enabled": model_config.get("enabled", True)
        }
        
        self._save_custom_models()
        return {"success": True, "message": f"模型 {model_id} 已添加", "model_id": model_id}
    
    def update_custom_model(self, model_id: str, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新自定义模型"""
        if model_id not in self._custom_models:
            return {"success": False, "error": f"模型 {model_id} 不存在"}
        
        # 更新配置
        self._custom_models[model_id].update({
            "name": model_config.get("name", self._custom_models[model_id].get("name")),
            "model": model_id,
            "provider": model_config.get("provider", self._custom_models[model_id].get("provider")),
            "dimension": model_config.get("dimension", self._custom_models[model_id].get("dimension")),
            "description": model_config.get("description", self._custom_models[model_id].get("description", "")),
            "api_key": model_config.get("api_key", self._custom_models[model_id].get("api_key", "")),
            "api_base": model_config.get("api_base", self._custom_models[model_id].get("api_base", "")),
            "model_path": model_config.get("model_path", self._custom_models[model_id].get("model_path", "")),
            "device": model_config.get("device", self._custom_models[model_id].get("device", "cpu")),
            "batch_size": model_config.get("batch_size", self._custom_models[model_id].get("batch_size", 32)),
            "enabled": model_config.get("enabled", self._custom_models[model_id].get("enabled", True))
        })
        
        self._save_custom_models()
        return {"success": True, "message": f"模型 {model_id} 已更新"}
    
    def delete_custom_model(self, model_id: str) -> Dict[str, Any]:
        """删除自定义模型"""
        if model_id not in self._custom_models:
            return {"success": False, "error": f"模型 {model_id} 不存在"}
        
        del self._custom_models[model_id]
        
        # 如果删除的是当前模型，重置为默认
        if self.embedding_model == model_id:
            self.embedding_model = "text-embedding-v2"
            self.embedding_provider = "api"
            self.embedding_api_key = None
            self.embedding_api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        self._save_custom_models()
        return {"success": True, "message": f"模型 {model_id} 已删除"}
    
    def set_default_model(self, model_id: str) -> Dict[str, Any]:
        """设置默认模型"""
        # 检查是否是内置模型
        if model_id in self.SUPPORTED_MODELS:
            info = self.SUPPORTED_MODELS[model_id]
            self.embedding_model = model_id
            self.embedding_provider = info.get("provider", "api")
            self._current_model_config = {}
            self._save_custom_models()
            return {"success": True, "message": f"默认模型已设置为 {model_id}"}
        
        # 检查是否是自定义模型
        if model_id in self._custom_models:
            cfg = self._custom_models[model_id]
            self.embedding_model = model_id
            self.embedding_api_key = cfg.get("api_key")
            self.embedding_api_base = cfg.get("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            self.embedding_provider = cfg.get("provider", "api")
            self.st_device = cfg.get("device", "cpu")
            self._current_model_config = cfg
            self._save_custom_models()
            return {"success": True, "message": f"默认模型已设置为 {model_id}"}
        
        return {"success": False, "error": f"模型 {model_id} 不存在"}

    def set_kb_embedding_config(
        self,
        embedding_model: str,
        embedding_model_type: str = "api",
        embedding_model_path: str = None,
        embedding_api_key: str = None,
        embedding_api_base: str = None,
    ) -> Dict[str, Any]:
        """
        根据知识库配置设置当前使用的 embedding 模型
        用于向量化时切换到 KB 指定的模型
        
        Args:
            embedding_model: 模型名称（如 all-MiniLM-L6-v2）
            embedding_model_type: 模型类型 api | local
            embedding_model_path: 本地模型路径（如 E:\\models\\all-MiniLM-L6-v2）
            embedding_api_key: API密钥（可选）
            embedding_api_base: API地址（可选）
        
        Returns:
            {"success": True, "model": "...", "provider": "local/api", "model_path": "..."}
        """
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_model_type
        
        if embedding_model_type == "local":
            # 本地模型：优先用用户配置的路径，其次用模型名（SentenceTransformer自动从缓存加载）
            if embedding_model_path:
                resolved_path = embedding_model_path
            else:
                # 模型名作为路径：如果本地存在则直接加载，否则报错提示
                resolved_path = embedding_model

            if resolved_path and not os.path.exists(resolved_path):
                logger.warning(
                    f"本地 embedding 模型路径不存在: {resolved_path}，"
                    f"嵌入时将报错，请确保路径正确。"
                )
            
            self.st_device = "cpu"
            self._current_model_config = {
                "model": embedding_model,
                "model_path": resolved_path,
                "provider": "local",
                "dimension": self._get_model_info(embedding_model).get("dimension", 384),
            }
            logger.info(f"设置知识库 embedding 为本地模型: {embedding_model}, 路径: {resolved_path}")
            return {
                "success": True,
                "model": embedding_model,
                "provider": "local",
                "model_path": resolved_path,
            }
        else:
            # API 模型
            self.embedding_api_key = embedding_api_key or self.embedding_api_key
            self.embedding_api_base = embedding_api_base or self.embedding_api_base
            self._current_model_config = {
                "model": embedding_model,
                "provider": "api",
                "api_key": self.embedding_api_key,
                "api_base": self.embedding_api_base,
            }
            logger.info(f"设置知识库 embedding 为 API 模型: {embedding_model}")
            return {
                "success": True,
                "model": embedding_model,
                "provider": "api",
            }

    def _get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        # 先检查自定义模型
        if model_name in self._custom_models:
            return self._custom_models[model_name]
        # 检查是否是本地路径（自动识别本地模型）
        if model_name and (os.path.isdir(model_name) or 
                          model_name.startswith(("E:\\", "C:\\", "/")) or
                          model_name in ["all-mpnet-base-v2", "all-MiniLM-L6-v2", "bge-m3", "bge-reranker-v2-m3"]):
            return {"provider": "local", "dimension": 768, "description": f"本地模型: {model_name}"}
        # 再检查内置模型
        return self.SUPPORTED_MODELS.get(model_name, {"provider": "api", "dimension": 1536, "description": model_name})

    def _get_provider(self, model_name: str = None) -> str:
        """获取指定模型的provider类型"""
        if model_name:
            info = self._get_model_info(model_name)
            return info.get("provider", "api")
        return self.embedding_provider

    def _load_local_model(self, model_name: str, model_path: str = None):
        """
        加载本地sentence-transformers模型（禁止自动下载，必须本地存在）

        Args:
            model_name: 模型名称（如 all-MiniLM-L6-v2）
            model_path: 本地模型路径（优先使用，如 E:\\models\\all-MiniLM-L6-v2）
        """
        if not ST_AVAILABLE:
            raise RuntimeError("sentence-transformers 未安装，请运行: pip install sentence-transformers")

        # 确定加载路径：必须使用 model_path，且路径必须存在
        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"本地 embedding 模型路径不存在: {model_path}\n"
                    f"请先下载模型到该路径，或修改配置使用 API 嵌入服务。"
                )
            load_path = model_path
        else:
            raise FileNotFoundError(
                f"未配置本地 embedding 模型路径 (model_path)。\n"
                f"请在知识库设置中配置本地模型路径，或切换为 API 嵌入服务。"
            )

        cache_key = load_path

        if cache_key not in self._local_models:
            logger.info(f"加载本地 embedding 模型: {load_path}")
            self._local_models[cache_key] = SentenceTransformer(load_path, device=self.st_device)
        return self._local_models[cache_key]

    def configure(self, api_key: str = None, api_base: str = None, model: str = None, provider: str = None, st_device: str = None):
        """配置嵌入服务"""
        if api_key:
            self.embedding_api_key = api_key
        if api_base:
            self.embedding_api_base = api_base
        if model:
            self.embedding_model = model
        if provider:
            self.embedding_provider = provider
        if st_device:
            self.st_device = st_device

    async def embed_text(self, text: str) -> Dict[str, Any]:
        """
        获取文本的嵌入向量 - 支持API和本地模型

        Returns:
            {"success": True, "embedding": [...], "model": "..."}
        """
        model_name = self.embedding_model
        provider = self._get_provider(model_name)

        if provider == "local":
            return await self._embed_text_local(text, model_name)
        else:
            return await self._embed_text_api(text, model_name)

    async def _embed_text_api(self, text: str, model_name: str) -> Dict[str, Any]:
        """通过API获取嵌入向量"""
        if not self.embedding_api_key:
            return {"success": False, "error": "未配置嵌入 API Key"}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.embedding_api_base}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.embedding_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "input": text[:8000]  # 限制长度
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "embedding": data["data"][0]["embedding"],
                        "model": model_name,
                        "provider": "api",
                        "tokens": data.get("usage", {}).get("total_tokens", 0)
                    }
                else:
                    return {"success": False, "error": f"API错误: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _embed_text_local(self, text: str, model_name: str, model_path: str = None) -> Dict[str, Any]:
        """通过本地sentence-transformers获取嵌入向量（禁止下载，必须本地存在）"""
        if not ST_AVAILABLE:
            return {"success": False, "error": "sentence-transformers 未安装，请运行: pip install sentence-transformers"}

        try:
            model = self._load_local_model(model_name, model_path)
            embedding = model.encode(text[:8000], show_progress_bar=False).tolist()
            model_info = self._get_model_info(model_name)
            # 如果传了 model_path，用它作为显示名称
            display_name = model_path if model_path else model_name
            return {
                "success": True,
                "embedding": embedding,
                "model": display_name,
                "provider": "local",
                "dimension": model_info.get("dimension", len(embedding))
            }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def embed_batch(self, texts: List[str]) -> Dict[str, Any]:
        """批量嵌入 - 支持API和本地模型"""
        model_name = self.embedding_model
        provider = self._get_provider(model_name)

        if provider == "local":
            return await self._embed_batch_local(texts, model_name)
        else:
            return await self._embed_batch_api(texts, model_name)

    async def _embed_batch_api(self, texts: List[str], model_name: str) -> Dict[str, Any]:
        """通过API批量获取嵌入向量"""
        if not self.embedding_api_key:
            return {"success": False, "error": "未配置嵌入 API Key"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.embedding_api_base}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.embedding_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "input": [t[:4000] for t in texts]
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "embeddings": [item["embedding"] for item in data["data"]],
                        "model": model_name,
                        "provider": "api",
                        "count": len(texts)
                    }
                else:
                    return {"success": False, "error": f"API错误: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _embed_batch_local(self, texts: List[str], model_name: str, model_path: str = None) -> Dict[str, Any]:
        """通过本地sentence-transformers批量获取嵌入向量（禁止下载，必须本地存在）"""
        if not ST_AVAILABLE:
            return {"success": False, "error": "sentence-transformers 未安装，请运行: pip install sentence-transformers"}

        try:
            model = self._load_local_model(model_name, model_path)
            embeddings = model.encode([t[:4000] for t in texts], show_progress_bar=False).tolist()
            model_info = self._get_model_info(model_name)
            display_name = model_path if model_path else model_name
            return {
                "success": True,
                "embeddings": embeddings,
                "model": display_name,
                "provider": "local",
                "count": len(texts),
                "dimension": model_info.get("dimension", len(embeddings[0]) if embeddings else 0)
            }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局服务实例
ocr_service = OCRService()
text_parser_service = TextParserService()
# 懒加载，避免启动时初始化失败的模型
_embedding_service = None

def get_embedding_service():
    """获取嵌入服务实例（懒加载）"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

# 保持向后兼容
embedding_service = type('LazyEmbeddingService', (), {
    '__getattr__': lambda self, name: getattr(get_embedding_service(), name)
})()
