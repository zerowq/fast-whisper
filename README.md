# Faster-Whisper ASR Service (Optimized)

轻量化语音识别服务，基于 Faster-Whisper 优化，默认使用 **Base 模型** (74M参数，平衡性能和质量)，支持资源监控和环境变量配置。

## ✨ 特性

- 🎯 **轻量化设计**: 默认使用 Base 模型，仅 74M 参数
- 🚀 **快速启动**: `python -m src.main` 一键启动
- 📊 **资源监控**: 实时 GPU/CPU/内存监控
- ⚙️ **灵活配置**: 支持环境变量配置
- 🔄 **自动降级**: GPU 不可用时自动切换到 CPU
- 📈 **监控指标**: 提供详细的性能指标 API

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 下载模型
```bash
# 下载默认的 base 模型 (推荐)
python scripts/download_models.py

# 或者下载其他大小的模型
python scripts/download_models.py --size tiny    # 最小模型 (39M)
python scripts/download_models.py --size small   # 小型模型 (244M)
```

### 3. 启动服务
```bash
python -m src.main
```

### 4. 访问服务
- 📖 API 文档: http://localhost:8080/docs
- ❤️ 健康检查: http://localhost:8080/health
- 📈 监控指标: http://localhost:8080/metrics

## 📊 模型选择

| 模型大小 | 参数量 | 内存占用 | 特点 |
|---------|--------|----------|------|
| tiny    | 39M    | ~40MB    | 最快速度，适合资源受限环境 |
| **base** | **74M** | **~75MB** | **推荐选择，平衡性能和质量** |
| small   | 244M   | ~245MB   | 更高准确率 |
| medium  | 769M   | ~775MB   | 高准确率 |
| large   | 1.55B  | ~1.5GB   | 最高准确率 |

## ⚙️ 配置选项

### 环境变量配置

复制 `.env.example` 为 `.env` 并根据需要修改：

```bash
# 模型配置
MODEL_SIZE=base          # 模型大小
DEVICE=auto             # 设备选择: auto, cuda, cpu
COMPUTE_TYPE=auto       # 计算类型: auto, float16, int8

# 服务配置
PORT=8080               # 服务端口
HOST=0.0.0.0           # 服务地址
LOG_LEVEL=INFO         # 日志级别
```

### 常用配置示例

```bash
# CPU 模式 (无 GPU 环境)
DEVICE=cpu
COMPUTE_TYPE=int8

# GPU 模式 (推荐)
DEVICE=cuda
COMPUTE_TYPE=float16

# 轻量模式 (资源受限)
MODEL_SIZE=tiny
DEVICE=cpu
COMPUTE_TYPE=int8
```

## 📡 API 使用

### 转录音频文件
```bash
curl -X POST "http://localhost:8080/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav"
```

### 转录远程音频
```bash
curl -X POST "http://localhost:8080/transcribe" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/audio.wav"}'
```

### 获取监控指标
```bash
curl http://localhost:8080/metrics
```

## 🔧 项目结构

```text
faster-whisper/
├── .env.example        # 环境变量模板
├── requirements.txt    # Python 依赖
├── scripts/           # 工具脚本
│   └── download_models.py  # 模型下载脚本
├── src/               # 源代码
│   ├── main.py        # 应用入口
│   ├── api/           # API 路由
│   │   └── router.py
│   └── core/          # 核心功能
│       ├── asr.py     # ASR 服务
│       ├── config.py  # 配置管理
│       └── resource_monitor.py  # 资源监控
├── models/            # 模型文件 (gitignore)
└── static/            # 静态文件
```

## 🐳 Docker 部署

### 构建镜像
```bash
docker build -t faster-whisper-optimized .
```

### 运行容器 (GPU)
```bash
docker run -d \
  --name whisper-asr \
  --gpus all \
  -e MODEL_SIZE=base \
  -e DEVICE=cuda \
  -p 8080:8080 \
  faster-whisper-optimized
```

### 运行容器 (CPU)
```bash
docker run -d \
  --name whisper-asr \
  -e MODEL_SIZE=base \
  -e DEVICE=cpu \
  -p 8080:8080 \
  faster-whisper-optimized
```

## 📈 监控和健康检查

### 健康检查
```bash
curl http://localhost:8080/health
```

### 详细监控指标
```bash
curl http://localhost:8080/metrics | jq
```

监控指标包括：
- CPU 使用率
- 内存使用情况
- GPU 状态和使用率
- 推理延迟统计
- 模型加载状态

## 🛠️ 故障排除

### 模型未找到
```bash
# 检查模型文件
ls -la models/

# 重新下载模型
python scripts/download_models.py --size base --force
```

### GPU 不可用
服务会自动降级到 CPU 模式，或手动设置：
```bash
export DEVICE=cpu
export COMPUTE_TYPE=int8
```

### 内存不足
使用更小的模型：
```bash
export MODEL_SIZE=tiny
```

## 📝 更新日志

### v2.0.0 (Optimized)
- ✨ 默认使用 Base 模型 (74M参数)
- 📊 集成资源监控功能
- ⚙️ 支持环境变量配置
- 🔄 自动 GPU/CPU 降级
- 📈 增强的监控指标 API
- 🚀 优化启动流程和错误处理

## 📄 许可证

MIT License
