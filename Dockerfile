# Use NVIDIA CUDA base image (runtime version is smaller and safer)
FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app \
    MODEL_PATH=/app/models

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
RUN pip3 install --no-cache-dir -r requirements.txt

# IMPORTANT: Copy the pre-downloaded models into the image
# This ensures total offline capability in the GPU environment
COPY models /app/models

# Copy the application source code
COPY src /app/src

# Expose the API port
EXPOSE 8080

# Start the service using the modular entry point
CMD ["python3", "-m", "src.main"]
