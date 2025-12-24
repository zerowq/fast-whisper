# Faster-Whisper ASR Service Deployment Manual / 部署手册

## 1. Service Overview / 服务概述

- **Service Name (服务名称)**: `faster-whisper-asr`
- **Purpose (用途)**: Provides high-performance, offline Automatic Speech Recognition (ASR). Supports 99+ languages with industry-leading accuracy. / 提供高性能、离线的自动语音识别服务。支持 99 种以上的语言，具有行业领先的准确率。
- **Model Version (模型版本)**: `Whisper Large-V3` (Quantized via CTranslate2).
- **Resource Requirements (资源要求)**: 
  - **Hardware (硬件)**: NVIDIA GPU (8GB+ VRAM recommended). / NVIDIA GPU（建议 8GB 以上显存）。
  - **Storage (存储)**: Model weights ~3GB. / 模型权重约 3GB。
- **Port (端口)**: `8080` (HTTP).
- **Offline Mode (离线模式)**: 100% Air-gapped compatible. / 100% 物理隔离兼容。

---

## 2. Deployment Steps / 部署步骤

### 2.1 Prepare Models (Internet Access Required Once) / 准备模型（需联网一次）
Run this on a machine with internet to fetch weights into the `models/` directory. / 在联网机器上运行，将权重下载到 `models/` 目录。
```bash
python3 scripts/download_model.py
```

### 2.2 Build Image / 构建镜像
```bash
docker build -t faster-whisper-asr:latest .
```

### 2.3 Start Container (GPU Mode) / 启动容器 (GPU 模式)
```bash
docker run -d \
  --name asr-service \
  --restart always \
  --gpus all \
  -p 8080:8080 \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  faster-whisper-asr:latest
```

---

## 3. Verification / 验证部署

### 3.1 Check Startup Logs / 检查启动日志
```bash
docker logs asr-service | grep "Model loaded successfully"
```

### 3.2 Health Check & Test / 健康检查与测试
```bash
# Using the provided test script / 使用提供的测试脚本
python3 scripts/test_api.py path/to/audio_sample.wav
```

### 3.3 Access Test Page / 访问测试页面
Access the built-in GUI via browser. / 通过浏览器访问内置测试页面。
- **URL**: `http://<SERVER_IP>:8080/`

---

## 4. Domain & Network / 域名配置

- **Suggested Domain (建议域名)**: `asr-service.evyd.io`
- **Backend Service (后端服务)**: `<GPU_MACHINE_IP>:8080`
- **Timeout Note**: Long audio files may take time to process. Ensure Nginx `proxy_read_timeout` is set to at least `300s`. / 长音频处理时间较长，请确保 Nginx 超时设置不少于 300秒。
