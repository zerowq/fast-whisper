# Faster-Whisper ASR Microservice

A high-performance ASR service based on Faster-Whisper, optimized for GPU-accelerated private clouds with **full offline support**.

## Project Structure
```text
faster-whisper/
├── Dockerfile          # GPU-enabled container definition
├── requirements.txt    # Python dependencies
├── models/             # Submodule: local storage for weights (generated)
├── scripts/            # DevOps helper scripts
│   └── download_model.py
└── src/                # Source code
    ├── main.py         # App entry point
    ├── api/            # API routing layer
    │   └── router.py
    ├── core/           # Model logic layer
    │   └── asr.py
    └── utils/          # Utility functions
```

## DevOps Guide

### 1. Offline Preparation
Run the download script on a machine with internet access to prepare the models.

```bash
pip install faster-whisper
python3 scripts/download_model.py
```

### 2. Build Image
The Dockerfile will bundle the `models/` directory into the image.

```bash
docker build -t faster-whisper-asr:v1 .
```

### 3. Deployment (GPU)
```bash
docker run -d \
  --name asr-service \
  --gpus all \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  -p 8080:8080 \
  faster-whisper-asr:v1

*Tip: If running in a environment without GPU (like a preview or local machine), change `DEVICE=cpu` and `COMPUTE_TYPE=int8`.*
```

### 4. Local Testing (Mac M1/CPU)
If you are on a Mac or machine without GPU:
- **Install requirements**: `pip install -r requirements.txt`
- **Start service**: `chmod +x start_local.sh && ./start_local.sh`
- **Test API**: `python3 scripts/test_api.py path/to/audio.wav`

---

# Faster-Whisper ASR 微服务

基于 Faster-Whisper 的高性能 ASR 服务，为支持 GPU 加速的私有云环境优化，支持**全离线部署**。

## 项目结构
```text
faster-whisper/
├── Dockerfile          # 支持 GPU 的容器定义
├── requirements.txt    # Python 依赖
├── models/             # 模型本地副本 (脚本生成)
├── scripts/            # 运维脚本
│   └── download_model.py
└── src/                # 业务源代码
    ├── main.py         # 应用入口
    ├── api/            # 接口路由层
    │   └── router.py
    ├── core/           # 核心业务层 (模型推理)
    │   └── asr.py
    └── utils/          # 工具类
```

## 运维指南

### 1. 离线化准备
在可联网的机器上运行脚本，预下载模型权重。

```bash
pip install faster-whisper
python3 scripts/download_model.py
```

### 2. 构建镜像
Dockerfile 会自动将本地 `models/` 目录拷贝进容器。

```bash
docker build -t faster-whisper-asr:v1 .
```

### 3. 生产部署 (GPU)
```bash
docker run -d \
  --name asr-service \
  --gpus all \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  -p 8080:8080 \
  faster-whisper-asr:v1

*提示：如果在没有 GPU 的环境（如预览环境或本地）运行，请将 `DEVICE` 改为 `cpu`，`COMPUTE_TYPE` 改为 `int8`。*
```

### 4. 本地测试 (Mac M1/CPU)
如果你使用的是 Mac 或没有显卡的机器：
- **安装依赖**: `pip install -r requirements.txt`
- **启动服务**: `chmod +x start_local.sh && ./start_local.sh`
- **测试接口**: `python3 scripts/test_api.py 音频文件路径.wav`
