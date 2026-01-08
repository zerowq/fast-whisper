# Docker 部署指南

## 📋 Docker 部署方案说明

### ✅ 为什么使用 Docker？

1. **完全解决 cuDNN 问题** - Docker 镜像内置 CUDA 12.2 + cuDNN 9
2. **环境一致性** - 开发环境 = 生产环境，避免"在我机器上可以运行"问题
3. **隔离性** - 不影响系统其他应用
4. **易于扩展** - 支持多容器并行部署、负载均衡
5. **版本管理** - 易于回滚和更新

---

## 🚀 快速开始

### 前置条件

```bash
# 1. 安装 Docker
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. 安装 NVIDIA Docker Runtime（GPU 支持）
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 3. 验证 GPU 支持
docker run --rm --gpus all nvidia/cuda:12.2.2-runtime-ubuntu22.04 nvidia-smi
```

### 方式 1: 使用 docker-compose（推荐）

```bash
# 1. 启动服务
docker-compose up -d

# 2. 查看日志
docker-compose logs -f faster-whisper-asr

# 3. 检查状态
docker-compose ps

# 4. 停止服务
docker-compose down

# 5. 重启服务
docker-compose restart
```

### 方式 2: 手动构建和运行

```bash
# 1. 构建镜像
docker build -t faster-whisper-asr:latest .

# 2. 运行容器（GPU 支持）
docker run --rm \
  --gpus all \
  -p 8898:8898 \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  -v $(pwd)/models:/app/models \
  faster-whisper-asr:latest

# 3. 运行容器（CPU 模式）
docker run --rm \
  -p 8898:8898 \
  -e DEVICE=cpu \
  -e COMPUTE_TYPE=int8 \
  -v $(pwd)/models:/app/models \
  faster-whisper-asr:latest
```

---

## 📊 Docker 配置说明

### Dockerfile 关键配置

```dockerfile
# 使用 NVIDIA 官方镜像（包含 CUDA 12.2 + cuDNN 9）
FROM nvidia/cuda:12.2.2-cudnn9-runtime-ubuntu22.04

# GPU 计算环境预配置
ENV DEVICE=cuda
ENV COMPUTE_TYPE=float16  # GPU 推荐 float16（速度快）

# 端口
EXPOSE 8898

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3
```

### docker-compose.yml 关键配置

```yaml
# GPU 运行时配置
runtime: nvidia
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1  # 使用 1 块 GPU
          capabilities: [gpu]

# 环境变量
environment:
  - DEVICE=cuda
  - COMPUTE_TYPE=float16
  - PORT=8898

# 卷挂载（模型持久化）
volumes:
  - ./models:/app/models
```

---

## 🔧 常用命令

```bash
# 查看运行中的容器
docker-compose ps

# 查看容器日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100

# 进入容器 shell
docker-compose exec faster-whisper-asr bash

# 查看容器资源使用情况
docker stats faster-whisper-asr

# 重启容器
docker-compose restart

# 停止容器
docker-compose stop

# 删除容器和镜像
docker-compose down
docker rmi faster-whisper-asr:latest
```

---

## 🧪 验证部署

### 1. 容器启动检查

```bash
# 查看容器状态
docker-compose ps

# 预期输出：
# NAME                       STATUS         PORTS
# faster-whisper-asr         Up 2 minutes   0.0.0.0:8898->8898/tcp
```

### 2. 健康检查

```bash
# 方式 1：使用 docker-compose
docker-compose ps  # 查看 STATUS 是否为 "Up" 和 "healthy"

# 方式 2：直接请求 API
curl http://localhost:8898/health

# 预期输出：
# {"status":"healthy","device":"cuda","model":"base","uptime":123.45}
```

### 3. API 测试

```bash
# 查看 API 文档
curl http://localhost:8898/docs

# 测试转录 API
curl -X POST http://localhost:8898/transcribe \
  -F "file=@kokoro_test_1.wav" \
  -F "language=" \
  -F "beam_size=5" \
  -F "task=transcribe"
```

### 4. 查看 GPU 使用情况

```bash
# 方式 1：在容器内查看
docker-compose exec faster-whisper-asr nvidia-smi

# 方式 2：主机上查看
nvidia-smi  # 应该看到 python 进程使用 GPU

# 预期输出示例：
# GPU:0 (Tesla V100): 8765MiB / 32768MiB - python (PID: 123)
```

---

## 📈 性能对比（预期）

### CPU 模式（无 Docker）
- RTF: 0.13（7.43x 实时速度）
- 内存: 3.6%
- 耗时: 4.21s / 31.28s 音频

### GPU 模式（Docker + CUDA + cuDNN）
- **RTF: ~0.01-0.02（50-100x 实时速度）** ⭐
- GPU 内存: ~8-10GB
- 耗时: ~0.3-0.5s / 31.28s 音频

---

## ⚠️ 常见问题

### 问题 1: Docker 无法访问 GPU

```bash
# 检查 nvidia-docker 是否安装
nvidia-docker version

# 查看 GPU 是否可见
docker run --rm --gpus all nvidia/cuda:12.2.2-runtime-ubuntu22.04 nvidia-smi

# 如果还是不行，检查 Docker 配置
docker info | grep nvidia
```

### 问题 2: 容器启动失败

```bash
# 查看详细日志
docker-compose logs

# 常见原因：
# 1. 模型文件不存在 - 确保 models/ 目录有文件
# 2. 端口被占用 - 改变映射端口或关闭其他应用
# 3. GPU 内存不足 - 改用 CPU 模式或清理其他 GPU 进程
```

### 问题 3: GPU 内存占用过高

```bash
# 查看 GPU 内存
docker-compose exec faster-whisper-asr nvidia-smi

# 解决方案：
# 1. 改用 int8 计算类型（更省内存）
#    环境变量：COMPUTE_TYPE=int8
# 2. 使用小模型（tiny 或 small）
#    环境变量：MODEL_SIZE=tiny
```

### 问题 4: cuDNN 错误仍然出现

```bash
# 原因通常是 nvidia-docker 配置问题
# 解决：
# 1. 重新安装 nvidia-docker2
sudo apt-get install --reinstall nvidia-docker2
sudo systemctl restart docker

# 2. 测试 Docker GPU 支持
docker run --rm --gpus all nvidia/cuda:12.2.2-cudnn9-runtime-ubuntu22.04 \
  python3 -c "import torch; print(torch.cuda.is_available())"
```

---

## 🚀 生产部署建议

### 1. 使用 Docker Swarm 或 Kubernetes

```bash
# Docker Swarm 多节点部署
docker service create \
  --name faster-whisper \
  --gpus all \
  -p 8898:8898 \
  faster-whisper-asr:latest
```

### 2. 添加负载均衡

```yaml
# docker-compose.yml - 添加 Nginx 反向代理
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - faster-whisper-asr-1
      - faster-whisper-asr-2
```

### 3. 监控和日志

```bash
# 使用 ELK Stack 或 Grafana 监控
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 📝 完整工作流

```bash
# 1. 克隆项目
git clone -b gpu-deployment https://github.com/zerowq/fast-whisper.git
cd fast-whisper

# 2. 验证模型文件存在
ls -lah models/

# 3. 启动 Docker 服务
docker-compose up -d

# 4. 检查服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f

# 6. 测试 API
curl -X POST http://localhost:8898/transcribe \
  -F "file=@kokoro_test_1.wav"

# 7. 访问 API 文档
# 浏览器打开：http://localhost:8898/docs

# 8. 监控 GPU
docker-compose exec faster-whisper-asr nvidia-smi

# 9. 停止服务
docker-compose down
```

---

**优势总结：**
✅ cuDNN 问题完全解决  
✅ 环境一致性  
✅ 易于部署和扩展  
✅ 生产就绪  

**预期性能提升：**
🚀 CPU: 7.43x 实时速度  
🚀 GPU: 50-100x 实时速度 ⭐
