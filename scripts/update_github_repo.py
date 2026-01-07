#!/usr/bin/env python3
"""
更新 GitHub 仓库脚本
推送更新到现有的 GitHub 仓库
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubRepoUpdater:
    """GitHub 仓库更新器"""
    
    def __init__(self, clean_copy_dir: str, github_repo: str):
        self.clean_copy_dir = Path(clean_copy_dir).resolve()
        self.github_repo = github_repo
        self.commit_message = "Update: Add pyproject.toml and improve project configuration"
    
    def run_command(self, command: list, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        """运行命令并返回结果"""
        if cwd is None:
            cwd = self.clean_copy_dir
        
        logger.info(f"运行命令: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                logger.debug(f"输出: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"命令失败: {e}")
            if e.stderr:
                logger.error(f"错误输出: {e.stderr.strip()}")
            raise
    
    def update_repo(self) -> bool:
        """更新仓库"""
        logger.info("🔄 更新 GitHub 仓库...")
        
        try:
            # 检查是否是 git 仓库
            if not (self.clean_copy_dir / ".git").exists():
                logger.error("❌ 目录不是 git 仓库")
                return False
            
            # 检查状态
            result = self.run_command(["git", "status", "--porcelain"])
            if not result.stdout.strip():
                logger.info("ℹ️  没有需要提交的更改")
                return True
            
            # 添加所有更改
            self.run_command(["git", "add", "."])
            logger.info("✅ 文件添加到 Git")
            
            # 创建提交
            self.run_command(["git", "commit", "-m", self.commit_message])
            logger.info("✅ 提交创建完成")
            
            # 推送到 GitHub
            logger.info("📤 推送到 GitHub...")
            result = self.run_command(["git", "push", "origin", "main"], check=False)
            if result.returncode == 0:
                logger.info("✅ 成功推送到 GitHub!")
                return True
            else:
                logger.error("❌ 推送失败")
                logger.error(f"错误: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 更新仓库失败: {e}")
            return False
    
    def print_success_summary(self):
        """打印成功摘要"""
        print("\n" + "🎉" * 30)
        print("  GitHub 仓库更新完成!")
        print("🎉" * 30)
        print(f"📋 仓库信息:")
        print(f"   URL: {self.github_repo}")
        print(f"   本地路径: {self.clean_copy_dir}")
        print(f"\n🔗 访问您的仓库:")
        print(f"   https://github.com/zerowq/fast-whisper")
        print("🎉" * 30 + "\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="更新 GitHub 仓库")
    parser.add_argument(
        "--clean-copy-dir",
        default="../fast-whisper-github",
        help="干净代码副本目录 (默认: ../fast-whisper-github)"
    )
    parser.add_argument(
        "--github-repo",
        default="https://github.com/zerowq/fast-whisper.git",
        help="GitHub 仓库 URL"
    )
    
    args = parser.parse_args()
    
    # 创建更新器
    updater = GitHubRepoUpdater(args.clean_copy_dir, args.github_repo)
    
    # 执行更新
    success = updater.update_repo()
    
    if success:
        updater.print_success_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()