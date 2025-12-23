#!/bin/bash

# Configuration for Mac M1 Local Testing
export DEVICE="cpu"
export COMPUTE_TYPE="int8"
export MODEL_PATH="./models"
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Stop on error
set -e

echo "Starting Faster-Whisper ASR Service in CPU mode..."

# Use uv if available
if command -v uv &> /dev/null; then
    RUN_CMD="uv run"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    RUN_CMD="python3"
else
    RUN_CMD="python3"
fi

# 检查模型核心文件是否完整 (判断 model.bin 是否存在且大于 1GB)
# 注意：Mac 的 stat 命令与 Linux 不同，这里用简单的大小判断
MOD_BIN="./models/model.bin"
NEED_DOWNLOAD=false

if [ ! -f "$MOD_BIN" ]; then
    NEED_DOWNLOAD=true
else
    FILESIZE=$(du -k "$MOD_BIN" | cut -f1)
    if [ $FILESIZE -lt 1000000 ]; then # 小于约 1GB
        echo "Detected incomplete model file ($FILESIZE KB). Re-downloading..."
        NEED_DOWNLOAD=true
    fi
fi

if [ "$NEED_DOWNLOAD" = true ]; then
    echo "Model files missing or incomplete. Running robust download script..."
    $RUN_CMD scripts/download_model.py
fi

echo "Model check passed. Starting FastAPI service..."
$RUN_CMD src/main.py
