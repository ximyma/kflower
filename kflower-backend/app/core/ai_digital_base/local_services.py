# -*- coding: utf-8 -*-
"""
本地AI服务 - OCR、文本解析、嵌入向量、本地模型
"""
import re
import io
import uuid
import json
from typing import Optional, Dict, Any, List
from PIL import Image
import numpy as np

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
        
        # 如果配置了 Tesseract 路径，设置环境变量
        if self.tesseract_path:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

    def configure(self, tesseract_path: str = None, lang: str = None):
        """配置 OCR"""
        if tesseract_path:
            self.tesseract_path = tesseract_path
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        if lang:
            self.default_lang = lang

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

    @staticmethod
    def get_supported_models() -> Dict[str, Dict[str, Any]]:
        """获取所有支持的嵌入模型列表"""
        return EmbeddingService.SUPPORTED_MODELS.copy()

    def _get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        return self.SUPPORTED_MODELS.get(model_name, {"provider": "api", "dimension": 1536, "description": model_name})

    def _get_provider(self, model_name: str = None) -> str:
        """获取指定模型的provider类型"""
        if model_name:
            info = self._get_model_info(model_name)
            return info.get("provider", "api")
        return self.embedding_provider

    def _load_local_model(self, model_name: str):
        """加载本地sentence-transformers模型"""
        if not ST_AVAILABLE:
            raise RuntimeError("sentence-transformers 未安装，请运行: pip install sentence-transformers")
        if model_name not in self._local_models:
            self._local_models[model_name] = SentenceTransformer(model_name, device=self.st_device)
        return self._local_models[model_name]

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

    async def _embed_text_local(self, text: str, model_name: str) -> Dict[str, Any]:
        """通过本地sentence-transformers获取嵌入向量"""
        if not ST_AVAILABLE:
            return {"success": False, "error": "sentence-transformers 未安装，请运行: pip install sentence-transformers"}

        try:
            model = self._load_local_model(model_name)
            embedding = model.encode(text[:8000], show_progress_bar=False).tolist()
            model_info = self._get_model_info(model_name)
            return {
                "success": True,
                "embedding": embedding,
                "model": model_name,
                "provider": "local",
                "dimension": model_info.get("dimension", len(embedding))
            }
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

    async def _embed_batch_local(self, texts: List[str], model_name: str) -> Dict[str, Any]:
        """通过本地sentence-transformers批量获取嵌入向量"""
        if not ST_AVAILABLE:
            return {"success": False, "error": "sentence-transformers 未安装，请运行: pip install sentence-transformers"}

        try:
            model = self._load_local_model(model_name)
            embeddings = model.encode([t[:4000] for t in texts], show_progress_bar=False).tolist()
            model_info = self._get_model_info(model_name)
            return {
                "success": True,
                "embeddings": embeddings,
                "model": model_name,
                "provider": "local",
                "count": len(texts),
                "dimension": model_info.get("dimension", len(embeddings[0]) if embeddings else 0)
            }
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
