#!/usr/bin/env python3
"""
同步修复到 GitHub 仓库
将最新的端口配置和模型文件修复推送到 GitHub
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixSyncer:
    """修复同步器"""
    
    def __init__(self):
        self.source_dir = Path(".").resolve()
        self.github_copy_dir = Path("../fast-whisper-github").resolve()
        self.github_repo = "https://github.com/zerowq/fast-whisper.git"
    
    def run_command(self, command: list, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        """运行命令并返回结果"""
        if cwd is None:
            cwd = self.github_copy_dir
        
        logger.info(f"运行命令: {' '.join(command)} (在 {cwd})")
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
    
    def ensure_github_copy_exists(self) -> bool:
        """确保 GitHub 副本存在"""
        logger.info("🔍 检查 GitHub 副本目录...")
        
        if self.github_copy_dir.exists():
            logger.info(f"✅ GitHub 副本目录已存在: {self.github_copy_dir}")
            return True
        
        logger.info("📥 克隆 GitHub 仓库...")
        try:
            self.run_command([
                "git", "clone", self.github_repo, str(self.github_copy_dir)
            ], cwd=self.source_dir.parent)
            logger.info("✅ GitHub 仓库克隆完成")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 克隆失败: {e}")
            return False
    
    def copy_fixed_files(self) -> bool:
        """复制修复的文件"""
        logger.info("📋 复制修复的文件...")
        
        # 需要复制的文件列表
        files_to_copy = [
            "src/core/config.py",
            "src/main.py", 
            "scripts/download_models.py",
            "fix_issues.py",
            "test_config.py",
            "scripts/setup_env.py",
            "TROUBLESHOOTING.md"
        ]
        
        try:
            for file_path in files_to_copy:
                source_file = self.source_dir / file_path
                target_file = self.github_copy_dir / file_path
                
                if source_file.exists():
                    # 确保目标目录存在
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(source_file, target_file)
                    logger.info(f"✅ 复制: {file_path}")
                else:
                    logger.warning(f"⚠️  源文件不存在: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 复制文件失败: {e}")
            return False
    
    def commit_and_push(self) -> bool:
        """提交并推送更改"""
        logger.info("📤 提交并推送更改...")
        
        try:
            # 检查是否有更改
            result = self.run_command(["git", "status", "--porcelain"])
            if not result.stdout.strip():
                logger.info("ℹ️  没有需要提交的更改")
                return True
            
            # 添加所有更改
            self.run_command(["git", "add", "."])
            logger.info("✅ 文件添加到 Git")
            
            # 创建提交
            commit_message = "Fix: 修复端口配置和模型文件验证问题\n\n- 添加 python-dotenv 支持自动加载 .env 文件\n- 修复模型文件验证逻辑，支持 vocabulary.txt\n- 添加快速修复脚本和故障排除指南\n- 改进配置管理和错误处理"
            
            self.run_command(["git", "commit", "-m", commit_message])
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
            logger.error(f"❌ 提交推送失败: {e}")
            return False
    
    def sync_fixes(self) -> bool:
        """同步修复"""
        logger.info("🚀 开始同步修复到 GitHub...")
        
        # 1. 确保 GitHub 副本存在
        if not self.ensure_github_copy_exists():
            return False
        
        # 2. 复制修复的文件
        if not self.copy_fixed_files():
            return False
        
        # 3. 提交并推送
        if not self.commit_and_push():
            return False
        
        return True
    
    def print_success_summary(self):
        """打印成功摘要"""
        print("\n" + "🎉" * 50)
        print("  修复已成功同步到 GitHub!")
        print("🎉" * 50)
        print(f"📋 修复内容:")
        print(f"   ✅ 端口配置问题 - 添加 .env 文件支持")
        print(f"   ✅ 模型文件验证 - 支持 vocabulary.txt")
        print(f"   ✅ 快速修复脚本 - fix_issues.py")
        print(f"   ✅ 配置测试脚本 - test_config.py")
        print(f"   ✅ 故障排除指南 - TROUBLESHOOTING.md")
        print(f"\n🔗 GitHub 仓库:")
        print(f"   https://github.com/zerowq/fast-whisper")
        print(f"\n💡 现在您可以在 GPU 服务器上:")
        print(f"   git pull origin main")
        print(f"   python fix_issues.py")
        print("🎉" * 50 + "\n")


def main():
    """主函数"""
    syncer = FixSyncer()
    
    success = syncer.sync_fixes()
    
    if success:
        syncer.print_success_summary()
        return 0
    else:
        logger.error("❌ 同步失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())