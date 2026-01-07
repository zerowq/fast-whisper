#!/usr/bin/env python3
"""
配置测试脚本
验证环境变量和模型文件配置是否正确
"""

import os
import sys

def test_dotenv_loading():
    """测试 .env 文件加载"""
    print("🔍 测试 .env 文件加载...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        port = os.getenv("PORT")
        if port:
            print(f"✅ 从 .env 读取到端口: {port}")
            return True
        else:
            print("❌ 未能从 .env 读取端口配置")
            return False
    except ImportError:
        print("❌ python-dotenv 未安装")
        return False
    except Exception as e:
        print(f"❌ .env 加载失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    print("🔍 测试配置管理器...")
    
    try:
        # 确保能导入配置模块
        sys.path.insert(0, os.getcwd())
        from src.core.config import get_config_manager
        
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        print(f"✅ 配置管理器工作正常")
        print(f"   端口: {config.port}")
        print(f"   模型: {config.model_size}")
        print(f"   路径: {config.model_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False

def test_model_files():
    """测试模型文件"""
    print("🔍 测试模型文件...")
    
    models_dir = "./models"
    if not os.path.exists(models_dir):
        print(f"❌ 模型目录不存在: {models_dir}")
        return False
    
    required_files = ["config.json", "model.bin", "tokenizer.json"]
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(models_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
        else:
            print(f"✅ 找到文件: {file}")
    
    # 检查词汇表文件
    vocab_json = os.path.join(models_dir, "vocabulary.json")
    vocab_txt = os.path.join(models_dir, "vocabulary.txt")
    
    if os.path.exists(vocab_json):
        print(f"✅ 找到文件: vocabulary.json")
    elif os.path.exists(vocab_txt):
        print(f"✅ 找到文件: vocabulary.txt")
    else:
        missing_files.append("vocabulary.json/vocabulary.txt")
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    print("✅ 所有模型文件存在")
    return True

def main():
    """主测试函数"""
    print("🧪 Faster-Whisper 配置测试")
    print("=" * 40)
    
    all_passed = True
    
    # 测试 .env 加载
    if not test_dotenv_loading():
        all_passed = False
    
    print()
    
    # 测试配置管理器
    if not test_config_manager():
        all_passed = False
    
    print()
    
    # 测试模型文件
    if not test_model_files():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✅ 所有测试通过!")
        print("可以运行: python src/main.py")
    else:
        print("❌ 部分测试失败")
        print("请运行: python fix_issues.py")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())