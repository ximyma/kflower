"""
下载 BAAI/bge-reranker-v2-m3 模型到本地
使用 HuggingFace 镜像源加速下载
"""
import os
import sys
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

def download_bge_reranker_model():
    """
    下载 BAAI/bge-reranker-v2-m3 模型到本地目录
    """
    # 模型名称
    model_name = "BAAI/bge-reranker-v2-m3"
    
    # 本地保存目录（使用相对于后端目录的路径）
    local_dir = os.path.join(os.path.dirname(__file__), "bge-reranker-v2-m3")
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"开始下载 {model_name} 模型...")
    print(f"本地保存目录: {local_dir}")
    
    try:
        # 设置 HuggingFace 镜像源（国内加速）
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        # 下载分词器
        print("正在下载分词器...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        tokenizer.save_pretrained(local_dir)
        print(f"✓ 分词器已保存到: {local_dir}")
        
        # 下载模型
        print("正在下载模型（这可能需要几分钟时间）...")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float32
        )
        model.save_pretrained(local_dir)
        print(f"✓ 模型已保存到: {local_dir}")
        
        # 验证模型文件
        print("\n验证下载的模型文件...")
        required_files = [
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "vocab.txt",
            "model.safetensors"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = os.path.join(local_dir, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  ✓ {file} ({size:,} bytes)")
            else:
                # 检查 .bin 格式（旧版本）
                if file == "model.safetensors":
                    bin_path = os.path.join(local_dir, "pytorch_model.bin")
                    if os.path.exists(bin_path):
                        size = os.path.getsize(bin_path)
                        print(f"  ✓ pytorch_model.bin ({size:,} bytes)")
                    else:
                        missing_files.append(file)
                else:
                    missing_files.append(file)
        
        if missing_files:
            print(f"\n⚠ 警告: 以下文件可能缺失: {', '.join(missing_files)}")
            print("  但这可能是正常的，因为不同版本的模型文件可能不同")
        else:
            print("\n✓ 所有关键文件已下载")
        
        print("\n" + "="*50)
        print("模型下载完成!")
        print(f"模型路径: {local_dir}")
        print("="*50)
        
        return local_dir
        
    except Exception as e:
        print(f"\n✗ 下载过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    download_bge_reranker_model()
