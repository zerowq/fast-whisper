#!/usr/bin/env python3
"""
快速修复脚本
解决端口配置和模型文件问题
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    print("🔧 Faster-Whisper 问题修复脚本")
    print("=" * 50)
    
    # 1. 安装 python-dotenv (如果需要)
    print("1. 检查 python-dotenv...")
    try:
        import dotenv
        print("✅ python-dotenv 已安装")
    except ImportError:
        print("❌ python-dotenv 未安装，正在安装...")
        os.system("pip install python-dotenv")
    
    # 2. 创建 .env 文件
    print("\n2. 创建 .env 文件...")
    env_content = """# Faster-Whisper ASR Service 环境变量配置
PORT=8898
HOST=0.0.0.0
MODEL_SIZE=base
MODEL_PATH=./models
DEVICE=auto
COMPUTE_TYPE=auto
LOG_LEVEL=INFO
ENABLE_CORS=true
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    print("✅ 已创建 .env 文件，端口设置为 8898")
    
    # 3. 修复词汇表文件
    print("\n3. 修复模型文件...")
    models_dir = "./models"
    if os.path.exists(models_dir):
        vocab_txt = os.path.join(models_dir, "vocabulary.txt")
        vocab_json = os.path.join(models_dir, "vocabulary.json")
        
        if os.path.exists(vocab_txt) and not os.path.exists(vocab_json):
            shutil.copy2(vocab_txt, vocab_json)
            print("✅ 已创建 vocabulary.json 从 vocabulary.txt")
        elif os.path.exists(vocab_json):
            print("✅ vocabulary.json 已存在")
        else:
            print("⚠️  未找到词汇表文件")
    else:
        print("⚠️  模型目录不存在")
    
    # 4. 测试配置
    print("\n4. 测试配置...")
    try:
        # 加载 .env 文件
        from dotenv import load_dotenv
        load_dotenv()
        
        port = os.getenv("PORT", "8080")
        print(f"✅ 端口配置: {port}")
        
        if os.path.exists("./models/config.json"):
            print("✅ 模型文件存在")
        else:
            print("⚠️  模型文件不存在，请运行: python scripts/download_models.py")
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
    
    print("\n✅ 修复完成!")
    print("现在可以运行: python src/main.py")
    print("服务将在端口 8898 启动")

if __name__ == "__main__":
    main()