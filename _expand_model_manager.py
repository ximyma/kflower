# -*- coding: utf-8 -*-
"""
Expand AI Model Manager with full parameter support
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path_mm = r'D:\kflower\kflower-backend\app\core\ai_digital_base\model_manager.py'

with open(path_mm, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace the class with expanded version
old_class = '''class AIModelManager:
    """
    AI模型管理器 - 支持动态模型列表和多模型配置
    """
    
    # 各服务商的默认基础URL
    PROVIDER_BASE_URLS = {
        "siliconflow": "https://api.siliconflow.cn/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai": "https://api.openai.com/v1",
        "moonshot": "https://api.moonshot.cn/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
        "baidu": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "minimax": "https://api.minimax.chat/v1",
    }
    
    # 预设的推荐模型（当API不可用时显示）
    DEFAULT_MODELS = {
        "siliconflow": [
            {"id": "Qwen/Qwen3-32B", "name": "Qwen3-32B", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen2.5-72B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-32B-Instruct", "name": "Qwen2.5-32B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-14B-Instruct", "name": "Qwen2.5-14B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-7B-Instruct", "name": "Qwen2.5-7B-Instruct", "type": "chat", "context": 32768},
            {"id": "deepseek-ai/DeepSeek-V3", "name": "DeepSeek-V3", "type": "chat", "context": 64000},
            {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek-R1 (推理)", "type": "chat", "context": 64000},
            {"id": "THUDM/glm-4-9b-chat", "name": "GLM-4-9B", "type": "chat", "context": 131072},
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "name": "Llama-3.3-70B", "type": "chat", "context": 131072},
        ],
        "deepseek": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "type": "chat", "context": 64000},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "type": "chat", "context": 64000},
        ],
        "qwen": [
            {"id": "qwen-max", "name": "Qwen Max", "type": "chat", "context": 32768},
            {"id": "qwen-plus", "name": "Qwen Plus", "type": "chat", "context": 131072},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "type": "chat", "context": 131072},
            {"id": "qwen-long", "name": "Qwen Long", "type": "chat", "context": 1000000},
        ],
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o", "type": "chat", "context": 128000},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "type": "chat", "context": 128000},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "type": "chat", "context": 128000},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat", "context": 16385},
        ],
        "moonshot": [
            {"id": "moonshot-v1-8k", "name": "Moonshot V1 8K", "type": "chat", "context": 8192},
            {"id": "moonshot-v1-32k", "name": "Moonshot V1 32K", "type": "chat", "context": 32768},
            {"id": "moonshot-v1-128k", "name": "Moonshot V1 128K", "type": "chat", "context": 131072},
        ],
        "zhipu": [
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "type": "chat", "context": 131072},
            {"id": "glm-4-0520", "name": "GLM-4 0520", "type": "chat", "context": 131072},
            {"id": "glm-4-air", "name": "GLM-4 Air", "type": "chat", "context": 131072},
        ],
    }'''

new_class = '''class AIModelManager:
    """
    AI模型管理器 - 支持动态模型列表、多模型配置、完整参数
    """

    # 各服务商的默认基础URL
    PROVIDER_BASE_URLS = {
        "siliconflow": "https://api.siliconflow.cn/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "openai": "https://api.openai.com/v1",
        "moonshot": "https://api.moonshot.cn/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
        "baidu": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",
        "minimax": "https://api.minimax.chat/v1",
        "ollama": "http://localhost:11434/v1",
    }

    # 默认模型参数配置
    DEFAULT_MODEL_PARAMS = {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.95,
        "top_k": 50,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "timeout": 120,
        "stream": False,
    }

    # 预设的推荐模型（当API不可用时显示）
    DEFAULT_MODELS = {
        "siliconflow": [
            {"id": "Qwen/Qwen3-32B", "name": "Qwen3-32B", "type": "chat", "context": 32768, "recommended": True},
            {"id": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen2.5-72B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-32B-Instruct", "name": "Qwen2.5-32B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-14B-Instruct", "name": "Qwen2.5-14B-Instruct", "type": "chat", "context": 32768},
            {"id": "Qwen/Qwen2.5-7B-Instruct", "name": "Qwen2.5-7B-Instruct", "type": "chat", "context": 32768},
            {"id": "deepseek-ai/DeepSeek-V3", "name": "DeepSeek-V3", "type": "chat", "context": 64000, "recommended": True},
            {"id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek-R1 (推理)", "type": "chat", "context": 64000},
            {"id": "THUDM/glm-4-9b-chat", "name": "GLM-4-9B", "type": "chat", "context": 131072},
            {"id": "meta-llama/Llama-3.3-70B-Instruct", "name": "Llama-3.3-70B", "type": "chat", "context": 131072},
        ],
        "deepseek": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "type": "chat", "context": 64000, "recommended": True},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "type": "chat", "context": 64000},
        ],
        "qwen": [
            {"id": "qwen-max", "name": "Qwen Max", "type": "chat", "context": 32768, "recommended": True},
            {"id": "qwen-plus", "name": "Qwen Plus", "type": "chat", "context": 131072},
            {"id": "qwen-turbo", "name": "Qwen Turbo", "type": "chat", "context": 131072},
            {"id": "qwen-long", "name": "Qwen Long", "type": "chat", "context": 1000000},
        ],
        "openai": [
            {"id": "gpt-4o", "name": "GPT-4o", "type": "chat", "context": 128000, "recommended": True},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "type": "chat", "context": 128000},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "type": "chat", "context": 128000},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat", "context": 16385},
        ],
        "moonshot": [
            {"id": "moonshot-v1-8k", "name": "Moonshot V1 8K", "type": "chat", "context": 8192},
            {"id": "moonshot-v1-32k", "name": "Moonshot V1 32K", "type": "chat", "context": 32768},
            {"id": "moonshot-v1-128k", "name": "Moonshot V1 128K", "type": "chat", "context": 131072},
        ],
        "zhipu": [
            {"id": "glm-4-plus", "name": "GLM-4 Plus", "type": "chat", "context": 131072, "recommended": True},
            {"id": "glm-4-0520", "name": "GLM-4 0520", "type": "chat", "context": 131072},
            {"id": "glm-4-air", "name": "GLM-4 Air", "type": "chat", "context": 131072},
        ],
        "ollama": [
            {"id": "qwen2.5:7b", "name": "Qwen2.5 7B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "qwen2.5:14b", "name": "Qwen2.5 14B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "llama3:8b", "name": "Llama3 8B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "deepseek-r1:7b", "name": "DeepSeek-R1 7B (本地)", "type": "chat", "context": 8192, "local": True},
            {"id": "glm4:9b", "name": "GLM4 9B (本地)", "type": "chat", "context": 4096, "local": True},
        ],
    }'''

if old_class in content:
    content = content.replace(old_class, new_class)
    with open(path_mm, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print("Model Manager expanded with full parameters and Ollama support")
else:
    print("Class pattern not found")
