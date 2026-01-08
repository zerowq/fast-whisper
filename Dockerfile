# Use NVIDIA CUDA 12.2 base image with cuDNN 9 (runtime version is smaller and safer)
FROM nvidia/cuda:12.2.2-cudnn9-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app \
    MODEL_PATH=/app/models \
    PORT=8898 \
    HOST=0.0.0.0 \
    DEVICE=cuda \
    COMPUTE_TYPE=float16 \
    ROOT_PATH=""

# Install system dependencies (ffmpeg is essential for whisper)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# IMPORTANT: Copy the pre-downloaded models into the image
# This ensures total offline capability in the GPU environment
COPY models /app/models

# Copy the application source code
COPY src /app/src
COPY static /app/static

# Expose the API port
EXPOSE 8898

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8898/health', timeout=5)" || exit 1

# Start the service using the modular entry point
CMD ["python3", "-m", "src.main"]
