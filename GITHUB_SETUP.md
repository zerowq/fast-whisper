# GitHub 仓库设置指南

如果您从 GitHub 克隆了代码并遇到 `uv sync` 错误，这是因为缺少 `pyproject.toml` 文件。

## 快速解决方案

### 方法 1: 创建 pyproject.toml 文件

在项目根目录创建 `pyproject.toml` 文件，内容如下：

```toml
[project]
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
```

### 方法 2: 使用自动生成脚本

运行以下命令自动生成缺失的文件：

```bash
python scripts/generate_missing_files.py
```

### 方法 3: 不使用 uv，直接使用 pip

如果您不想使用 uv，可以直接使用 pip：

```bash
# 安装依赖
pip install -r requirements.txt

# 下载模型
python scripts/download_models.py

# 启动服务
python -m src.main
```

## 完整设置流程

1. **克隆仓库**:
   ```bash
   git clone https://github.com/zerowq/fast-whisper.git
   cd fast-whisper
   ```

2. **创建 pyproject.toml** (使用上面的内容)

3. **安装依赖**:
   ```bash
   # 使用 uv (推荐)
   uv sync
   
   # 或使用 pip
   pip install -r requirements.txt
   ```

4. **下载模型**:
   ```bash
   # 使用 uv
   uv run python scripts/download_models.py
   
   # 或使用 python
   python scripts/download_models.py
   ```

5. **启动服务**:
   ```bash
   # 使用 uv
   uv run python -m src.main
   
   # 或使用 python
   python -m src.main
   ```

6. **访问服务**:
   - API 文档: http://localhost:8080/docs
   - 健康检查: http://localhost:8080/health
   - 监控指标: http://localhost:8080/metrics

## 故障排除

### 问题: `No pyproject.toml found`
**解决**: 按照上面的方法 1 创建 `pyproject.toml` 文件

### 问题: `ModuleNotFoundError`
**解决**: 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### 问题: 模型未找到
**解决**: 运行模型下载脚本：
```bash
python scripts/download_models.py --size base
```

### 问题: GPU 不可用
**解决**: 服务会自动降级到 CPU 模式，这是正常的。如果需要强制 CPU 模式：
```bash
export DEVICE=cpu
export COMPUTE_TYPE=int8
python -m src.main
```

## 环境变量配置

您可以通过环境变量自定义配置：

```bash
# 模型配置
export MODEL_SIZE=base          # tiny, base, small, medium, large
export DEVICE=auto             # auto, cuda, cpu
export COMPUTE_TYPE=auto       # auto, float16, int8

# 服务配置
export PORT=8080               # 服务端口
export LOG_LEVEL=INFO          # 日志级别

# 启动服务
python -m src.main
```

或者创建 `.env` 文件（参考 `.env.example`）。