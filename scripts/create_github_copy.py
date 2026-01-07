#!/usr/bin/env python3
"""
创建干净的代码副本用于 GitHub 推送
排除所有内网敏感信息和 git 历史，只包含必要的源代码文件
"""

import os
import shutil
import sys
import logging
from pathlib import Path
from typing import List, Set

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubCopyCreator:
    """GitHub 代码副本创建器"""
    
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        
        # 需要包含的文件和目录
        self.include_patterns = {
            # 源代码 - 更宽泛的匹配
            "src",
            "scripts",
            "tests",
            
            # 配置文件
            "requirements.txt",
            "requirements-minimal.txt",
            "pyproject.toml",
            ".env.example",
            
            # 文档
            "README.md",
            "LICENSE",
            "CODE_OF_CONDUCT.md",
            "FAQ.md",
            
            # Docker 相关
            "Dockerfile",
            "docker_start.sh",
            "start.sh",
            "start_local.sh",
            
            # 静态文件目录结构
            "static",
        }
        
        # 需要排除的文件和目录 (安全考虑)
        self.exclude_patterns = {
            # Git 相关
            ".git/",
            ".gitmodules",
            
            # IDE 和编辑器
            ".idea/",
            ".vscode/",
            ".claude/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            
            # 系统文件
            ".DS_Store",
            "Thumbs.db",
            
            # 日志和缓存
            "logs/",
            "*.log",
            ".cache/",
            
            # 模型文件 (太大，用户需要自己下载)
            "models/",
            "*.bin",
            "*.safetensors",
            
            # 虚拟环境
            ".venv/",
            "venv/",
            ".env",  # 排除实际的环境变量文件
            
            # 构建产物
            "build/",
            "dist/",
            "*.egg-info/",
            
            # 测试和临时文件
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            "*.tmp",
            "*.temp",
            
            # 内网特定文件
            "ci/",  # 可能包含内网 CI 配置
            ".gitlab-ci.yml",  # 内网 GitLab CI
            "*.internal.*",  # 任何标记为内部的文件
            
            # 音频测试文件 (可能很大)
            "*.wav",
            "*.mp3",
            "*.flac",
            "*.m4a",
            
            # 其他大文件
            "*.zip",
            "*.tar.gz",
            "*.tar.bz2",
            
            # 锁文件 (让用户重新生成)
            "uv.lock",
            "poetry.lock",
            "Pipfile.lock",
        }
    
    def should_include_file(self, file_path: Path) -> bool:
        """判断文件是否应该包含在副本中"""
        relative_path = file_path.relative_to(self.source_dir)
        relative_str = str(relative_path)
        
        # 检查排除模式
        for exclude_pattern in self.exclude_patterns:
            if exclude_pattern.endswith("/"):
                # 目录模式
                if relative_str.startswith(exclude_pattern.rstrip("/")) or f"/{exclude_pattern}" in f"/{relative_str}":
                    return False
            elif "*" in exclude_pattern:
                # 通配符模式
                import fnmatch
                if fnmatch.fnmatch(relative_str, exclude_pattern):
                    return False
            else:
                # 精确匹配
                if relative_str == exclude_pattern or relative_str.endswith(f"/{exclude_pattern}"):
                    return False
        
        # 检查包含模式
        for include_pattern in self.include_patterns:
            if include_pattern.endswith("/"):
                # 目录模式
                pattern_clean = include_pattern.rstrip("/")
                if relative_str.startswith(pattern_clean) or relative_str == pattern_clean:
                    return True
            else:
                # 文件或目录模式
                if relative_str == include_pattern or relative_str.startswith(f"{include_pattern}/"):
                    return True
        
        # 默认排除
        return False
    
    def create_clean_copy(self) -> bool:
        """创建干净的代码副本"""
        logger.info(f"开始创建 GitHub 代码副本...")
        logger.info(f"源目录: {self.source_dir}")
        logger.info(f"目标目录: {self.target_dir}")
        
        try:
            # 清理目标目录
            if self.target_dir.exists():
                logger.info("清理现有目标目录...")
                shutil.rmtree(self.target_dir)
            
            # 创建目标目录
            self.target_dir.mkdir(parents=True, exist_ok=True)
            
            # 收集需要复制的文件
            files_to_copy = []
            for root, dirs, files in os.walk(self.source_dir):
                root_path = Path(root)
                
                # 检查目录是否应该被跳过
                relative_root = root_path.relative_to(self.source_dir)
                if not self.should_include_file(root_path):
                    continue
                
                # 检查文件
                for file in files:
                    file_path = root_path / file
                    if self.should_include_file(file_path):
                        files_to_copy.append(file_path)
            
            logger.info(f"找到 {len(files_to_copy)} 个文件需要复制")
            
            # 复制文件
            copied_count = 0
            for file_path in files_to_copy:
                relative_path = file_path.relative_to(self.source_dir)
                target_file = self.target_dir / relative_path
                
                # 创建目标目录
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                shutil.copy2(file_path, target_file)
                copied_count += 1
                
                if copied_count % 10 == 0:
                    logger.info(f"已复制 {copied_count}/{len(files_to_copy)} 个文件...")
            
            logger.info(f"✅ 成功复制 {copied_count} 个文件")
            
            # 创建必要的空目录
            self._create_empty_directories()
            
            # 创建 .gitignore 文件
            self._create_gitignore()
            
            # 创建 GitHub 特定文件
            self._create_github_files()
            
            logger.info("✅ GitHub 代码副本创建完成!")
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建代码副本失败: {e}")
            return False
    
    def _create_empty_directories(self):
        """创建必要的空目录"""
        empty_dirs = [
            "models",
            "static",
            "logs",
        ]
        
        for dir_name in empty_dirs:
            dir_path = self.target_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            
            # 创建 .gitkeep 文件
            gitkeep_file = dir_path / ".gitkeep"
            gitkeep_file.write_text("# This directory is kept in git for structure\n")
    
    def _create_gitignore(self):
        """创建 .gitignore 文件"""
        gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Model files (users need to download themselves)
models/*.bin
models/*.safetensors
models/pytorch_model.bin
models/model.bin

# Audio files
*.wav
*.mp3
*.flac
*.m4a
*.ogg

# Logs
logs/
*.log

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Lock files
uv.lock
poetry.lock
Pipfile.lock
"""
        
        gitignore_file = self.target_dir / ".gitignore"
        gitignore_file.write_text(gitignore_content)
        logger.info("✅ 创建 .gitignore 文件")
    
    def _create_github_files(self):
        """创建 GitHub 特定文件"""
        
        # 创建 LICENSE 文件 (如果不存在)
        license_file = self.target_dir / "LICENSE"
        if not license_file.exists():
            license_content = """MIT License

Copyright (c) 2024 Faster-Whisper ASR Service

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
            license_file.write_text(license_content)
            logger.info("✅ 创建 LICENSE 文件")
    
    def print_summary(self):
        """打印创建摘要"""
        if not self.target_dir.exists():
            logger.error("目标目录不存在")
            return
        
        print("\n" + "="*60)
        print("📋 GitHub 代码副本摘要")
        print("="*60)
        print(f"📁 目标目录: {self.target_dir}")
        
        # 统计文件数量
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.target_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
        
        print(f"📊 文件统计:")
        print(f"   总文件数: {total_files}")
        print(f"   总大小: {total_size / 1024 / 1024:.2f} MB")
        
        print(f"\n🚀 下一步操作:")
        print(f"   1. cd {self.target_dir}")
        print(f"   2. git init")
        print(f"   3. git add .")
        print(f"   4. git commit -m 'Initial commit: Faster-Whisper ASR Service (Optimized)'")
        print(f"   5. git remote add origin https://github.com/zerowq/fast-whisper.git")
        print(f"   6. git push -u origin main")
        print("="*60 + "\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="创建干净的 GitHub 代码副本")
    parser.add_argument(
        "--source", 
        default=".", 
        help="源代码目录 (默认: 当前目录)"
    )
    parser.add_argument(
        "--target", 
        default="../fast-whisper-github", 
        help="目标目录 (默认: ../fast-whisper-github)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="仅显示将要复制的文件，不实际复制"
    )
    
    args = parser.parse_args()
    
    # 创建副本创建器
    creator = GitHubCopyCreator(args.source, args.target)
    
    if args.dry_run:
        logger.info("🔍 干运行模式 - 仅显示将要复制的文件")
        # TODO: 实现干运行逻辑
        return
    
    # 创建副本
    success = creator.create_clean_copy()
    
    if success:
        creator.print_summary()
        sys.exit(0)
    else:
        logger.error("❌ 创建失败")
        sys.exit(1)


if __name__ == "__main__":
    main()