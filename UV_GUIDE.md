# UV 包管理器使用指南

本项目使用 [uv](https://github.com/astral-sh/uv) 作为包管理器。`uv` 是一个极快的 Python 包管理器，比 `pip` 快 10-100 倍。

## 📦 快速开始

### 1. 安装 UV

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -Command "& {Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -OutFile $env:TEMP/install.ps1; & $env:TEMP/install.ps1}"

# 或使用 Homebrew
brew install uv
```

### 2. 验证安装

```bash
uv --version
```

## 🚀 常用命令

### 创建虚拟环境

```bash
# 创建虚拟环境
uv venv

# 创建指定 Python 版本的虚拟环境
uv venv --python 3.10

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### 安装依赖

```bash
# 安装所有依赖（包括开发依赖）
uv sync

# 仅安装生产依赖
uv sync --no-dev

# 安装特定的依赖组
uv sync --only-group dev

# 安装单个包
uv pip install package_name
```

### 添加新依赖

```bash
# 添加生产依赖
uv add package_name

# 添加开发依赖
uv add --group dev package_name

# 添加特定版本
uv add "package_name>=1.0.0"
```

### 更新依赖

```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定包
uv pip install --upgrade package_name
```

### 移除依赖

```bash
# 从 pyproject.toml 中移除
uv remove package_name
```

## 📋 项目结构

```
faster-whisper-service/
├── pyproject.toml          # 项目配置和依赖定义
├── uv.lock                 # 锁定文件（自动生成）
├── .venv/                  # 虚拟环境
├── src/                    # 源代码
├── tests/                  # 测试
└── scripts/                # 脚本
```

## 🔧 pyproject.toml 配置

```toml
[project]
name = "faster-whisper-service"
version = "2.0.0"
requires-python = ">=3.10"

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    # ... 其他生产依赖
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "hypothesis>=6.88.0",
    # ... 其他开发依赖
]

[tool.uv]
python-version = "3.10"
```

## 🐳 GPU 服务器部署

### 初始设置

```bash
# 1. 克隆项目
git clone -b gpu-deployment https://github.com/zerowq/fast-whisper.git
cd fast-whisper

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
source .venv/bin/activate

# 4. 安装依赖
uv sync --no-dev

# 5. 下载模型
python scripts/download_models.py

# 6. 启动服务
python src/main.py
```

### 使用 UV 运行命令

```bash
# 运行 Python 脚本
uv run python src/main.py

# 运行测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/test_asr_model_management.py -v
```

## 📝 最佳实践

### 1. 使用 uv.lock 文件

```bash
# 提交 uv.lock 到 Git，确保环境一致性
git add uv.lock
git commit -m "Update dependencies lock"
```

### 2. 区分生产和开发依赖

```toml
# 生产依赖
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
]

# 开发依赖
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
]
```

### 3. 固定关键依赖版本

```bash
# 对于关键库（如 CUDA、torch），使用精确版本
uv add "torch==2.0.0"
```

### 4. 定期更新依赖

```bash
# 检查可用的更新
uv pip index versions package_name

# 安全地更新
uv sync --upgrade
```

## ⚡ 性能优势

UV 相比传统包管理器的优势：

| 任务 | pip | uv |
|------|-----|-----|
| 首次安装依赖 | 60s | 6s |
| 增量安装 | 30s | 0.3s |
| 创建虚拟环境 | 8s | 0.1s |
| 冻结依赖 | 45s | 2s |

## 🔍 故障排查

### 问题：虚拟环境激活失败

```bash
# 重新创建虚拟环境
uv venv --force

# 重新激活
source .venv/bin/activate
```

### 问题：依赖冲突

```bash
# 查看详细的错误信息
uv sync --verbose

# 强制同步
uv sync --force
```

### 问题：找不到特定版本

```bash
# 查看可用版本
uv pip index versions package_name

# 使用特定索引源
uv pip install package_name --index-url https://pypi.org/simple/
```

## 📚 更多信息

- [UV 官方文档](https://docs.astral.sh/uv/)
- [UV GitHub 仓库](https://github.com/astral-sh/uv)
- [Python 虚拟环境最佳实践](https://docs.python.org/3/tutorial/venv.html)

## 🎯 GPU 部署快速命令

```bash
# 完整部署流程
uv venv --python 3.10
source .venv/bin/activate
uv sync --no-dev
python scripts/download_models.py
PORT=8898 python src/main.py
```

---

**提示**: 始终在虚拟环境中工作，避免污染系统 Python！
