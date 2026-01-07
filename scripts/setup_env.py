#!/usr/bin/env python3
"""
环境设置脚本
帮助用户快速设置 .env 文件和验证配置
"""

import os
import sys
import shutil
from pathlib import Path

def create_env_file():
    """创建 .env 文件"""
    env_template = """# Faster-Whisper ASR Service 环境变量配置
# 根据需要修改以下配置

# 模型配置
MODEL_SIZE=base                    # 模型大小: tiny, base, small, medium, large
MODEL_PATH=./models               # 模型文件路径
DEVICE=auto                       # 设备: auto, cuda, cpu
COMPUTE_TYPE=auto                 # 计算类型: auto, float16, int8

# 服务配置
PORT=8898                         # 服务端口
HOST=0.0.0.0                     # 服务地址
LOG_LEVEL=INFO                   # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
ROOT_PATH=                       # 根路径 (用于反向代理)
STATIC_DIR=./static              # 静态文件目录

# 性能配置
MAX_FILE_SIZE_MB=100             # 最大文件大小 (MB)
REQUEST_TIMEOUT_SECONDS=300      # 请求超时时间 (秒)
BEAM_SIZE=5                      # 束搜索大小
LANGUAGE=                        # 默认语言 (留空自动检测)
TASK=transcribe                  # 默认任务: transcribe, translate

# 功能配置
ENABLE_CORS=true                 # 启用 CORS
ENABLE_METRICS=true              # 启用监控
METRICS_INTERVAL_SECONDS=60      # 监控间隔 (秒)
"""
    
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"⚠️  .env 文件已存在: {env_file}")
        response = input("是否覆盖现有文件? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ 取消创建 .env 文件")
            return False
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_template)
        print(f"✅ 已创建 .env 文件: {env_file}")
        return True
    except Exception as e:
        print(f"❌ 创建 .env 文件失败: {e}")
        return False

def fix_vocabulary_file():
    """修复词汇表文件问题"""
    models_dir = "./models"
    
    if not os.path.exists(models_dir):
        print(f"⚠️  模型目录不存在: {models_dir}")
        return False
    
    vocab_txt = os.path.join(models_dir, "vocabulary.txt")
    vocab_json = os.path.join(models_dir, "vocabulary.json")
    
    if os.path.exists(vocab_txt) and not os.path.exists(vocab_json):
        try:
            shutil.copy2(vocab_txt, vocab_json)
            print(f"✅ 已创建 vocabulary.json 从 vocabulary.txt")
            return True
        except Exception as e:
            print(f"❌ 创建 vocabulary.json 失败: {e}")
            return False
    elif os.path.exists(vocab_json):
        print("✅ vocabulary.json 已存在")
        return True
    else:
        print("⚠️  未找到 vocabulary.txt 或 vocabulary.json")
        return False

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    missing_deps = []
    
    try:
        import dotenv
        print("✅ python-dotenv 已安装")
    except ImportError:
        missing_deps.append("python-dotenv")
    
    try:
        import faster_whisper
        print("✅ faster-whisper 已安装")
    except ImportError:
        missing_deps.append("faster-whisper")
    
    try:
        import fastapi
        print("✅ fastapi 已安装")
    except ImportError:
        missing_deps.append("fastapi")
    
    if missing_deps:
        print(f"❌ 缺少依赖项: {missing_deps}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖项已安装")
    return True

def test_config_loading():
    """测试配置加载"""
    print("🔍 测试配置加载...")
    
    try:
        # 添加当前目录到 Python 路径
        sys.path.insert(0, os.getcwd())
        
        from src.core.config import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        print(f"✅ 配置加载成功")
        print(f"   端口: {config.port}")
        print(f"   模型: {config.model_size}")
        print(f"   设备: {config.device}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Faster-Whisper 环境设置脚本")
    print("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        return 1
    
    # 创建 .env 文件
    print("\n📝 设置环境变量文件...")
    create_env_file()
    
    # 修复词汇表文件
    print("\n🔧 修复模型文件...")
    fix_vocabulary_file()
    
    # 测试配置加载
    print("\n🧪 测试配置...")
    if test_config_loading():
        print("\n✅ 环境设置完成!")
        print("现在可以运行: python src/main.py")
    else:
        print("\n❌ 环境设置失败，请检查错误信息")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())