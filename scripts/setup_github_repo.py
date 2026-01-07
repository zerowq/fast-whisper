#!/usr/bin/env python3
"""
安全的 GitHub 仓库初始化和推送脚本
在干净的代码副本中初始化全新的 git 仓库并推送到 GitHub
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubRepoSetup:
    """GitHub 仓库设置器"""
    
    def __init__(self, clean_copy_dir: str, github_repo: str):
        self.clean_copy_dir = Path(clean_copy_dir).resolve()
        self.github_repo = github_repo
        self.commit_message = "Initial commit: Faster-Whisper ASR Service (Optimized)"
    
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
    
    def check_prerequisites(self) -> bool:
        """检查前置条件"""
        logger.info("🔍 检查前置条件...")
        
        # 检查干净副本目录是否存在
        if not self.clean_copy_dir.exists():
            logger.error(f"❌ 干净的代码副本目录不存在: {self.clean_copy_dir}")
            logger.info("请先运行: python scripts/create_github_copy.py")
            return False
        
        # 检查 git 是否可用
        try:
            self.run_command(["git", "--version"], cwd=Path.cwd())
            logger.info("✅ Git 可用")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Git 不可用，请安装 Git")
            return False
        
        return True
    
    def setup_git_repo(self) -> bool:
        """设置 Git 仓库"""
        logger.info("🔧 设置 Git 仓库...")
        
        try:
            # 检查是否已经是 git 仓库
            git_dir = self.clean_copy_dir / ".git"
            if git_dir.exists():
                logger.warning("⚠️  目录已经是 git 仓库，将重新初始化")
                import shutil
                shutil.rmtree(git_dir)
            
            # 初始化 git 仓库
            self.run_command(["git", "init"])
            logger.info("✅ Git 仓库初始化完成")
            
            # 检查 git 用户配置
            self._check_git_config()
            
            # 添加所有文件
            self.run_command(["git", "add", "."])
            logger.info("✅ 文件添加到 Git")
            
            # 创建初始提交
            self.run_command(["git", "commit", "-m", self.commit_message])
            logger.info("✅ 初始提交创建完成")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git 仓库设置失败: {e}")
            return False
    
    def _check_git_config(self):
        """检查 Git 配置"""
        try:
            # 检查用户名
            result = self.run_command(["git", "config", "user.name"], check=False)
            if result.returncode != 0:
                logger.warning("⚠️  Git 用户名未配置")
                logger.info("请手动配置: git config user.name 'Your Name'")
            
            # 检查邮箱
            result = self.run_command(["git", "config", "user.email"], check=False)
            if result.returncode != 0:
                logger.warning("⚠️  Git 邮箱未配置")
                logger.info("请手动配置: git config user.email 'your.email@example.com'")
                
        except Exception as e:
            logger.warning(f"检查 Git 配置时出错: {e}")
    
    def setup_remote_and_push(self) -> bool:
        """设置远程仓库并推送"""
        logger.info("🌐 设置远程仓库...")
        
        try:
            # 添加远程仓库
            self.run_command(["git", "remote", "add", "origin", self.github_repo])
            logger.info(f"✅ 远程仓库添加完成: {self.github_repo}")
            
            # 检查远程仓库连接
            logger.info("🔍 检查远程仓库连接...")
            result = self.run_command(["git", "ls-remote", "origin"], check=False)
            if result.returncode != 0:
                logger.error("❌ 无法连接到远程仓库")
                logger.error("请检查:")
                logger.error("  1. 仓库 URL 是否正确")
                logger.error("  2. 您是否有推送权限")
                logger.error("  3. GitHub 认证是否配置正确")
                return False
            
            logger.info("✅ 远程仓库连接正常")
            
            # 推送到 GitHub
            logger.info("📤 推送到 GitHub...")
            logger.info("注意: 如果这是第一次推送，可能需要输入 GitHub 凭据")
            
            # 尝试推送到 main 分支
            result = self.run_command(["git", "push", "-u", "origin", "main"], check=False)
            if result.returncode == 0:
                logger.info("✅ 成功推送到 GitHub (main 分支)!")
                return True
            else:
                logger.warning("⚠️  推送到 main 分支失败，尝试推送到 master 分支...")
                result = self.run_command(["git", "push", "-u", "origin", "master"], check=False)
                if result.returncode == 0:
                    logger.info("✅ 成功推送到 GitHub (master 分支)!")
                    return True
                else:
                    logger.error("❌ 推送失败")
                    logger.error("请手动检查并推送:")
                    logger.error("  git push -u origin main")
                    logger.error("  或")
                    logger.error("  git push -u origin master")
                    return False
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 远程仓库设置失败: {e}")
            return False
    
    def print_success_summary(self):
        """打印成功摘要"""
        try:
            # 获取当前分支
            result = self.run_command(["git", "branch", "--show-current"])
            current_branch = result.stdout.strip()
        except:
            current_branch = "unknown"
        
        print("\n" + "🎉" * 30)
        print("  GitHub 仓库设置完成!")
        print("🎉" * 30)
        print(f"📋 仓库信息:")
        print(f"   URL: {self.github_repo}")
        print(f"   本地路径: {self.clean_copy_dir}")
        print(f"   分支: {current_branch}")
        print(f"\n🔗 访问您的仓库:")
        print(f"   https://github.com/zerowq/fast-whisper")
        print(f"\n📝 后续操作:")
        print(f"   1. 在 GitHub 上添加仓库描述")
        print(f"   2. 设置仓库主题标签 (whisper, asr, speech-recognition, fastapi)")
        print(f"   3. 启用 Issues 和 Discussions (如果需要)")
        print(f"   4. 添加 README 徽章 (如果需要)")
        print("🎉" * 30 + "\n")
    
    def setup(self) -> bool:
        """执行完整的设置流程"""
        logger.info("🚀 开始 GitHub 仓库设置...")
        
        # 检查前置条件
        if not self.check_prerequisites():
            return False
        
        # 设置 Git 仓库
        if not self.setup_git_repo():
            return False
        
        # 设置远程仓库并推送
        if not self.setup_remote_and_push():
            return False
        
        # 打印成功摘要
        self.print_success_summary()
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="设置 GitHub 仓库")
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅检查前置条件，不执行实际操作"
    )
    
    args = parser.parse_args()
    
    # 创建设置器
    setup = GitHubRepoSetup(args.clean_copy_dir, args.github_repo)
    
    if args.dry_run:
        logger.info("🔍 干运行模式 - 仅检查前置条件")
        success = setup.check_prerequisites()
        if success:
            logger.info("✅ 前置条件检查通过")
        else:
            logger.error("❌ 前置条件检查失败")
        sys.exit(0 if success else 1)
    
    # 执行设置
    success = setup.setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()