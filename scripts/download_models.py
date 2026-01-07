#!/usr/bin/env python3
"""
Faster-Whisper Model Download Script
支持多种模型大小选择，默认下载 base 模型，实现断点续传和错误重试机制
"""

import os
import sys
import argparse
import time
from typing import Dict, Optional
from huggingface_hub import snapshot_download, HfApi
from huggingface_hub.utils import HfHubHTTPError

# 模型配置映射
MODEL_CONFIGS = {
    "tiny": {
        "repo_id": "Systran/faster-whisper-tiny",
        "size_mb": 40,
        "parameters": "39M",
        "description": "最小模型，速度最快但准确率较低"
    },
    "base": {
        "repo_id": "Systran/faster-whisper-base", 
        "size_mb": 75,
        "parameters": "74M",
        "description": "平衡模型，推荐选择，性能和质量的最佳平衡"
    },
    "small": {
        "repo_id": "Systran/faster-whisper-small",
        "size_mb": 245,
        "parameters": "244M", 
        "description": "小型模型，较好的准确率"
    },
    "medium": {
        "repo_id": "Systran/faster-whisper-medium",
        "size_mb": 775,
        "parameters": "769M",
        "description": "中型模型，高准确率"
    },
    "large": {
        "repo_id": "Systran/faster-whisper-large-v3",
        "size_mb": 1500,
        "parameters": "1.55B",
        "description": "大型模型，最高准确率但速度较慢"
    }
}

class ModelDownloader:
    """模型下载器，支持断点续传和错误重试"""
    
    def __init__(self, output_dir: str = "./models", max_retries: int = 3, retry_delay: int = 5):
        self.output_dir = os.path.abspath(output_dir)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 设置镜像源以提高下载稳定性
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def list_available_models(self) -> None:
        """列出所有可用的模型"""
        print("可用的模型大小:")
        print("-" * 60)
        for size, config in MODEL_CONFIGS.items():
            print(f"{size:8} | {config['parameters']:8} | {config['size_mb']:4}MB | {config['description']}")
        print("-" * 60)
        print("推荐使用 'base' 模型，它提供了性能和质量的最佳平衡")
    
    def validate_model_size(self, model_size: str) -> bool:
        """验证模型大小是否有效"""
        return model_size in MODEL_CONFIGS
    
    def check_existing_model(self, model_size: str) -> bool:
        """检查模型是否已经存在"""
        config = MODEL_CONFIGS[model_size]
        model_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
        
        for file in model_files:
            file_path = os.path.join(self.output_dir, file)
            if not os.path.exists(file_path):
                return False
        
        # 检查 model.bin 文件大小是否合理
        model_bin_path = os.path.join(self.output_dir, "model.bin")
        if os.path.exists(model_bin_path):
            size_mb = os.path.getsize(model_bin_path) / (1024 * 1024)
            expected_size = config["size_mb"]
            # 允许 ±20% 的大小差异
            if size_mb < expected_size * 0.8:
                print(f"警告: model.bin 文件大小 ({size_mb:.1f}MB) 小于预期 ({expected_size}MB)")
                return False
        
        return True
    
    def download_with_retry(self, model_size: str, force: bool = False) -> bool:
        """带重试机制的模型下载"""
        config = MODEL_CONFIGS[model_size]
        repo_id = config["repo_id"]
        
        print(f"准备下载模型: {model_size}")
        print(f"仓库ID: {repo_id}")
        print(f"参数量: {config['parameters']}")
        print(f"预期大小: {config['size_mb']}MB")
        print(f"输出目录: {self.output_dir}")
        print(f"使用镜像: {os.environ.get('HF_ENDPOINT', 'default')}")
        
        # 检查是否已存在
        if not force and self.check_existing_model(model_size):
            print(f"模型 '{model_size}' 已存在且完整，跳过下载")
            print("如需重新下载，请使用 --force 参数")
            return True
        
        # 重试下载
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"\n开始下载 (尝试 {attempt}/{self.max_retries})...")
                
                download_path = snapshot_download(
                    repo_id=repo_id,
                    local_dir=self.output_dir,
                    local_dir_use_symlinks=False,
                    resume_download=True,  # 启用断点续传
                    etag_timeout=120,      # 增加超时时间
                    token=None             # 不使用认证token
                )
                
                print(f"\n✅ 下载成功! 模型文件位于: {download_path}")
                
                # 验证下载完整性
                if self.verify_download(model_size):
                    print("✅ 模型文件验证通过")
                    return True
                else:
                    print("❌ 模型文件验证失败")
                    if attempt < self.max_retries:
                        print(f"将在 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                        continue
                    return False
                    
            except HfHubHTTPError as e:
                print(f"❌ HTTP错误 (尝试 {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    print(f"将在 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("❌ 达到最大重试次数，下载失败")
                    self._print_manual_download_instructions(repo_id)
                    return False
                    
            except Exception as e:
                print(f"❌ 下载错误 (尝试 {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    print(f"将在 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("❌ 达到最大重试次数，下载失败")
                    self._print_manual_download_instructions(repo_id)
                    return False
        
        return False
    
    def verify_download(self, model_size: str) -> bool:
        """验证下载的模型文件完整性"""
        config = MODEL_CONFIGS[model_size]
        required_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
        
        print("验证模型文件...")
        for file in required_files:
            file_path = os.path.join(self.output_dir, file)
            if not os.path.exists(file_path):
                print(f"❌ 缺少文件: {file}")
                return False
            print(f"✅ 找到文件: {file}")
        
        # 验证 model.bin 大小
        model_bin_path = os.path.join(self.output_dir, "model.bin")
        if os.path.exists(model_bin_path):
            size_mb = os.path.getsize(model_bin_path) / (1024 * 1024)
            expected_size = config["size_mb"]
            print(f"model.bin 大小: {size_mb:.1f}MB (预期: {expected_size}MB)")
            
            if size_mb < expected_size * 0.8:
                print(f"❌ model.bin 文件大小异常，可能下载不完整")
                return False
        
        return True
    
    def _print_manual_download_instructions(self, repo_id: str) -> None:
        """打印手动下载说明"""
        print("\n" + "="*60)
        print("自动下载失败，您可以尝试手动下载:")
        print(f"1. 访问: https://hf-mirror.com/{repo_id}/tree/main")
        print(f"2. 下载所有文件到目录: {self.output_dir}")
        print("3. 确保下载以下文件:")
        print("   - config.json")
        print("   - model.bin")
        print("   - tokenizer.json") 
        print("   - vocabulary.json")
        print("   - preprocessor_config.json (如果存在)")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Faster-Whisper 模型下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python download_models.py                    # 下载默认的 base 模型
  python download_models.py --size tiny        # 下载 tiny 模型
  python download_models.py --size large       # 下载 large 模型
  python download_models.py --list             # 列出所有可用模型
  python download_models.py --force            # 强制重新下载
        """
    )
    
    parser.add_argument(
        "--size", 
        choices=list(MODEL_CONFIGS.keys()),
        default="base",
        help="模型大小 (默认: base，推荐的平衡选择)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="./models",
        help="模型输出目录 (默认: ./models)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的模型大小"
    )
    
    parser.add_argument(
        "--force",
        action="store_true", 
        help="强制重新下载，即使模型已存在"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="最大重试次数 (默认: 3)"
    )
    
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        help="重试间隔秒数 (默认: 5)"
    )
    
    args = parser.parse_args()
    
    # 创建下载器
    downloader = ModelDownloader(
        output_dir=args.output_dir,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )
    
    # 列出模型
    if args.list:
        downloader.list_available_models()
        return
    
    # 验证模型大小
    if not downloader.validate_model_size(args.size):
        print(f"❌ 无效的模型大小: {args.size}")
        downloader.list_available_models()
        sys.exit(1)
    
    # 下载模型
    print(f"🚀 开始下载 Faster-Whisper {args.size} 模型...")
    success = downloader.download_with_retry(args.size, args.force)
    
    if success:
        print(f"\n🎉 模型 '{args.size}' 下载完成!")
        print(f"📁 模型位置: {downloader.output_dir}")
        print("\n现在您可以启动服务:")
        print("python -m src.main")
        sys.exit(0)
    else:
        print(f"\n❌ 模型 '{args.size}' 下载失败")
        sys.exit(1)


if __name__ == "__main__":
    main()