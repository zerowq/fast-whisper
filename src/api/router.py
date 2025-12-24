from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import shutil
import os
import urllib.request
import uuid
import time
from src.core.asr import ASRService
import psutil
from collections import deque
from typing import Optional

# --- Metrics & Health ---
try:
    import pynvml
    pynvml.nvmlInit()
    is_gpu_available = True
except (ImportError, pynvml.NVMLError):
    is_gpu_available = False

# Store the last 10 inference latencies
inference_latencies = deque(maxlen=10)


router = APIRouter()

# Global ASR instance, initialized in main.py
asr_service: Optional[ASRService] = None

@router.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Health Check Endpoint
    
    Returns:
        dict: A dictionary indicating the service status.
    """
    return {"status": "ok"}

@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Metrics Endpoint
    
    Provides GPU/Memory/Inference Latency metrics.
    """
    metrics = {
        "cpu_usage_percent": psutil.cpu_percent(),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "used_percent": psutil.virtual_memory().percent,
        },
        "gpu": [],
        "inference_latency_ms": {
            "last_10_avg": round(sum(inference_latencies) / len(inference_latencies) * 1000, 2) if inference_latencies else 0,
            "last_10_samples": [round(l * 1000, 2) for l in inference_latencies]
        }
    }
    
    if is_gpu_available:
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics["gpu"].append({
                    "device_id": i,
                    "name": pynvml.nvmlDeviceGetName(handle),
                    "memory": {
                        "total_gb": round(mem_info.total / (1024**3), 2),
                        "used_gb": round(mem_info.used / (1024**3), 2),
                        "free_gb": round(mem_info.free / (1024**3), 2),
                    },
                    "utilization_percent": {
                        "gpu": utilization.gpu,
                        "memory": utilization.memory,
                    }
                })
        except pynvml.NVMLError as e:
            metrics["gpu"].append({"error": f"Could not retrieve GPU metrics: {e}"})

    return metrics

def download_remote_file(url: str):
    temp_file = f"remote_{uuid.uuid4()}.tmp"
    try:
        print(f"DEBUG: Downloading remote file from {url}...")
        # Use urllib.request instead of requests
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(temp_file, 'wb') as f:
                # Read in chunks
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        print(f"DEBUG: Remote file downloaded to {temp_file}")
        return temp_file
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise HTTPException(status_code=400, detail=f"Failed to download remote file via urllib: {str(e)}")

@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(None),
    url: str = Query(None, description="The URL of the remote audio file")
):
    print(f"\n[HTTP] Received transcription request at {time.strftime('%H:%M:%S')}")
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file or url must be provided")
    
    temp_file = None
    try:
        if file:
            temp_file = f"temp_{uuid.uuid4()}_{file.filename}"
            print(f"DEBUG: Saving uploaded file to {temp_file}...")
            with open(temp_file, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            temp_file = download_remote_file(url)
        
        print(f"DEBUG: Starting Faster-Whisper inference (this may take time on CPU)...")
        start_time = time.time()
        result = asr_service.transcribe(temp_file)
        end_time = time.time()
        
        latency = end_time - start_time
        inference_latencies.append(latency)
        
        print(f"DEBUG: Inference completed in {latency:.2f} seconds.")
        return result
    except Exception as e:
        print(f"ERROR: Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file and os.path.exists(temp_file):
            print(f"DEBUG: Cleaning up temp file {temp_file}")
            os.remove(temp_file)
