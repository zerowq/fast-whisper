# 故障排除指南

## 常见问题及解决方案

### 1. 端口配置问题

**问题**: 创建了 `.env` 文件设置 `PORT=8898`，但服务仍在 8080 端口启动

**原因**: 
- `python-dotenv` 未安装
- `.env` 文件未被正确加载

**解决方案**:

```bash
# 方法1: 快速修复
python fix_issues.py

# 方法2: 手动修复
pip install python-dotenv
# 创建 .env 文件，内容如下:
echo "PORT=8898" > .env

# 方法3: 直接设置环境变量
export PORT=8898
python src/main.py
```

### 2. 模型文件验证失败

**问题**: 下载的模型缺少 `vocabulary.json` 文件

**原因**: Hugging Face 模型仓库中的文件名为 `vocabulary.txt`，但代码期望 `vocabulary.json`

**解决方案**:

```bash
# 自动修复
python fix_issues.py

# 手动修复
cd models
cp vocabulary.txt vocabulary.json
```

### 3. 依赖项问题

**问题**: `ImportError: No module named 'dotenv'`

**解决方案**:

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或单独安装
pip install python-dotenv
```

### 4. 模型路径问题

**问题**: `ERROR: 模型文件未找到: ./models`

**原因**: 
- 模型文件未下载
- 工作目录不正确
- 模型文件不完整

**解决方案**:

```bash
# 1. 下载模型
python scripts/download_models.py --size base

# 2. 验证模型文件
python test_config.py

# 3. 检查工作目录
python -c "import os; print('当前目录:', os.getcwd()); print('models存在:', os.path.exists('./models'))"
```

## 完整的设置流程

### 新环境设置

```bash
# 1. 克隆代码
git clone https://github.com/zerowq/fast-whisper.git
cd fast-whisper

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载模型
python scripts/download_models.py --size base

# 4. 修复配置问题
python fix_issues.py

# 5. 测试配置
python test_config.py

# 6. 启动服务
python src/main.py
```

### GPU 服务器设置

```bash
# 1. 设置环境变量
export PORT=8898
export DEVICE=cuda
export COMPUTE_TYPE=float16

# 2. 或创建 .env 文件
cat > .env << EOF
PORT=8898
DEVICE=cuda
COMPUTE_TYPE=float16
MODEL_SIZE=base
EOF

# 3. 启动服务
python src/main.py
```

## 验证步骤

### 1. 检查配置

```bash
python test_config.py
```

### 2. 检查模型文件

```bash
ls -la models/
# 应该看到:
# - config.json
# - model.bin
# - tokenizer.json
# - vocabulary.txt
# - vocabulary.json (自动创建)
```

### 3. 检查端口

```bash
# 启动服务后检查
netstat -tlnp | grep 8898
# 或
lsof -i :8898
```

### 4. 测试 API

```bash
# 健康检查
curl http://localhost:8898/health

# API 文档
curl http://localhost:8898/docs
```

## 环境变量参考

```bash
# 服务配置
PORT=8898                         # 服务端口
HOST=0.0.0.0                     # 服务地址
LOG_LEVEL=INFO                   # 日志级别

# 模型配置
MODEL_SIZE=base                  # 模型大小: tiny, base, small, medium, large
MODEL_PATH=./models             # 模型路径
DEVICE=auto                     # 设备: auto, cuda, cpu
COMPUTE_TYPE=auto               # 计算类型: auto, float16, int8

# 性能配置
MAX_FILE_SIZE_MB=100            # 最大文件大小
REQUEST_TIMEOUT_SECONDS=300     # 请求超时
BEAM_SIZE=5                     # 束搜索大小

# 功能配置
ENABLE_CORS=true                # 启用 CORS
ENABLE_METRICS=true             # 启用监控
```

## 常用命令

```bash
# 快速修复所有问题
python fix_issues.py

# 测试配置
python test_config.py

# 重新下载模型
python scripts/download_models.py --size base --force

# 查看可用模型
python scripts/download_models.py --list

# 启动服务 (调试模式)
LOG_LEVEL=DEBUG python src/main.py

# 直接设置端口启动
PORT=8898 python src/main.py
```

## 获取帮助

如果问题仍然存在，请：

1. 运行 `python test_config.py` 获取详细错误信息
2. 检查日志输出中的错误消息
3. 确认工作目录和文件权限
4. 提供完整的错误堆栈信息