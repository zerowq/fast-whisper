#!/usr/bin/env python3
"""
生成缺失文件脚本
为 GitHub 克隆的仓库生成缺失的配置文件
"""

import os
import sys
from pathlib import Path

def generate_pyproject_toml():
    """生成 pyproject.toml 文件内容"""
    return """[project]
name = "faster-whisper-service"
version = "2.0.0"
description = "Optimized Faster-Whisper ASR Service with Base model (74M parameters) for balanced performance and quality"
readme = "README.md"
requires-python = ">=3.10"
authors = [
    {name = "Faster-Whisper ASR Service", email = "contact@example.com"}
]
license = {text = "MIT"}
keywords = ["whisper", "asr", "speech-recognition", "fastapi", "faster-whisper"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Multimedia :: Sound/Audio :: Speech",
]

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-multipart>=0.0.6",
    "faster-whisper>=1.0.0",
    "numpy>=1.24.0",
    "psutil>=5.9.0",
    "pynvml>=11.5.0",
    "pydantic>=2.0.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "hypothesis>=6.88.0",
    "python-dotenv>=1.0.0",
    "colorlog>=6.7.0",
]

[project.urls]
Homepage = "https://github.com/zerowq/fast-whisper"
Repository = "https://github.com/zerowq/fast-whisper"
Issues = "https://github.com/zerowq/fast-whisper/issues"
Documentation = "https://github.com/zerowq/fast-whisper#readme"

[project.scripts]
faster-whisper-service = "src.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "scripts/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
]
"""

def generate_uv_lock_placeholder():
    """生成 uv.lock 占位符说明"""
    return """# uv.lock 文件说明
# 
# 这个文件通常由 uv 自动生成，用于锁定依赖版本
# 如果您使用 uv，请运行以下命令生成此文件：
#   uv sync
#
# 如果您不使用 uv，可以使用传统的 pip 安装：
#   pip install -r requirements.txt
#
# 或者使用 pyproject.toml：
#   pip install -e .
"""

def main():
    """主函数"""
    print("🔧 生成缺失的配置文件...")
    
    current_dir = Path.cwd()
    
    # 检查是否在正确的目录
    if not (current_dir / "src").exists() or not (current_dir / "README.md").exists():
        print("❌ 错误: 请在 fast-whisper 项目根目录运行此脚本")
        print("   (应该包含 src/ 目录和 README.md 文件)")
        sys.exit(1)
    
    files_created = []
    
    # 生成 pyproject.toml
    pyproject_file = current_dir / "pyproject.toml"
    if not pyproject_file.exists():
        pyproject_file.write_text(generate_pyproject_toml())
        files_created.append("pyproject.toml")
        print("✅ 创建 pyproject.toml")
    else:
        print("ℹ️  pyproject.toml 已存在，跳过")
    
    # 生成 uv.lock 说明文件
    uv_lock_info = current_dir / "uv-lock-info.txt"
    if not uv_lock_info.exists():
        uv_lock_info.write_text(generate_uv_lock_placeholder())
        files_created.append("uv-lock-info.txt")
        print("✅ 创建 uv-lock-info.txt (uv.lock 说明)")
    
    if files_created:
        print(f"\n🎉 成功创建 {len(files_created)} 个文件:")
        for file in files_created:
            print(f"   - {file}")
        
        print("\n📋 下一步操作:")
        print("1. 如果使用 uv:")
        print("   uv sync")
        print("   uv run python scripts/download_models.py")
        print("   uv run python -m src.main")
        
        print("\n2. 如果使用 pip:")
        print("   pip install -r requirements.txt")
        print("   python scripts/download_models.py")
        print("   python -m src.main")
        
        print("\n3. 如果使用 pyproject.toml:")
        print("   pip install -e .")
        print("   python scripts/download_models.py")
        print("   python -m src.main")
    else:
        print("\n✅ 所有必要文件都已存在")
        print("\n📋 可以直接运行:")
        print("   uv sync  # 如果使用 uv")
        print("   或")
        print("   pip install -r requirements.txt  # 如果使用 pip")


if __name__ == "__main__":
    main()