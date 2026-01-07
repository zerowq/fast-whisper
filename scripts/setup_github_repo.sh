#!/bin/bash
# 安全的 GitHub 仓库初始化和推送脚本
# 在干净的代码副本中初始化全新的 git 仓库并推送到 GitHub

set -e  # 遇到错误时退出

# 配置
GITHUB_REPO="https://github.com/zerowq/fast-whisper.git"
CLEAN_COPY_DIR="../fast-whisper-github"
COMMIT_MESSAGE="Initial commit: Faster-Whisper ASR Service (Optimized)"

echo "🚀 GitHub 仓库设置脚本"
echo "======================="

# 检查干净副本目录是否存在
if [ ! -d "$CLEAN_COPY_DIR" ]; then
    echo "❌ 错误: 干净的代码副本目录不存在: $CLEAN_COPY_DIR"
    echo "请先运行: python scripts/create_github_copy.py"
    exit 1
fi

echo "📁 切换到干净的代码副本目录: $CLEAN_COPY_DIR"
cd "$CLEAN_COPY_DIR"

# 检查是否已经是 git 仓库
if [ -d ".git" ]; then
    echo "⚠️  警告: 目录已经是 git 仓库，将重新初始化"
    rm -rf .git
fi

echo "🔧 初始化新的 Git 仓库..."
git init

echo "📝 配置 Git 用户信息 (如果需要)..."
# 检查是否已配置用户信息
if ! git config user.name > /dev/null 2>&1; then
    echo "请输入您的 Git 用户名:"
    read -r git_username
    git config user.name "$git_username"
fi

if ! git config user.email > /dev/null 2>&1; then
    echo "请输入您的 Git 邮箱:"
    read -r git_email
    git config user.email "$git_email"
fi

echo "📋 添加所有文件到 Git..."
git add .

echo "💾 创建初始提交..."
git commit -m "$COMMIT_MESSAGE"

echo "🌐 添加 GitHub 远程仓库..."
git remote add origin "$GITHUB_REPO"

echo "🔍 检查远程仓库连接..."
if ! git ls-remote origin > /dev/null 2>&1; then
    echo "❌ 错误: 无法连接到远程仓库 $GITHUB_REPO"
    echo "请检查:"
    echo "  1. 仓库 URL 是否正确"
    echo "  2. 您是否有推送权限"
    echo "  3. GitHub 认证是否配置正确"
    exit 1
fi

echo "📤 推送到 GitHub..."
echo "注意: 如果这是第一次推送，可能需要输入 GitHub 凭据"

# 尝试推送到 main 分支
if git push -u origin main; then
    echo "✅ 成功推送到 GitHub!"
else
    echo "⚠️  推送到 main 分支失败，尝试推送到 master 分支..."
    if git push -u origin master; then
        echo "✅ 成功推送到 GitHub (master 分支)!"
    else
        echo "❌ 推送失败"
        echo "请手动检查并推送:"
        echo "  git push -u origin main"
        echo "  或"
        echo "  git push -u origin master"
        exit 1
    fi
fi

echo ""
echo "🎉 GitHub 仓库设置完成!"
echo "📋 仓库信息:"
echo "   URL: $GITHUB_REPO"
echo "   本地路径: $(pwd)"
echo "   分支: $(git branch --show-current)"
echo ""
echo "🔗 访问您的仓库:"
echo "   https://github.com/zerowq/fast-whisper"
echo ""
echo "📝 后续操作:"
echo "   1. 在 GitHub 上添加仓库描述"
echo "   2. 设置仓库主题标签 (whisper, asr, speech-recognition, fastapi)"
echo "   3. 启用 Issues 和 Discussions (如果需要)"
echo "   4. 添加 README 徽章 (如果需要)"
echo ""
echo "✨ 完成!"