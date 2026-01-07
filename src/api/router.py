from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import shutil
import os
import urllib.request
import uuid
import time
import logging
from src.core.asr import ASRService
import psutil
from collections import deque
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)

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
    status = {"status": "ok", "service": "Faster-Whisper ASR"}
    
    # 检查 ASR 服务状态
    if asr_service is not None:
        model_info = asr_service.get_model_info()
        status.update({
            "model_loaded": model_info["loaded"],
            "model_size": model_info["model_size"],
            "device": model_info["device"]
        })
    else:
        status["model_loaded"] = False
        
    return status

@router.get("/model/info", tags=["Model Management"])
async def get_model_info():
    """
    获取当前模型信息
    
    Returns:
        dict: 模型详细信息
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    return asr_service.get_model_info()

@router.post("/model/switch", tags=["Model Management"])
async def switch_model(model_size: str = Query(..., description="新的模型大小 (tiny, base, small, medium, large)")):
    """
    动态切换模型大小
    
    Args:
        model_size: 新的模型大小
        
    Returns:
        dict: 切换结果
    """
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR service not initialized")
    
    logger.info(f"收到模型切换请求: {model_size}")
    
    try:
        success = asr_service.switch_model_size(model_size)
        if success:
            model_info = asr_service.get_model_info()
            return {
                "success": True,
                "message": f"模型已切换到 {model_size}",
                "model_info": model_info
            }
        else:
            return {
                "success": False,
                "message": f"模型切换失败: {model_size}"
            }
    except Exception as e:
        logger.error(f"模型切换错误: {e}")
        raise HTTPException(status_code=500, detail=f"模型切换失败: {str(e)}")

@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Metrics Endpoint
    
    Provides GPU/Memory/Inference Latency metrics and model information.
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
    
    # 添加模型信息
    if asr_service is not None:
        metrics["model"] = asr_service.get_model_info()
    
    # GPU 信息
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
    """下载远程文件"""
    temp_file = f"remote_{uuid.uuid4()}.tmp"
    try:
        logger.info(f"下载远程文件: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        logger.info(f"远程文件下载完成: {temp_file}")
        return temp_file
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise HTTPException(status_code=400, detail=f"远程文件下载失败: {str(e)}")

@router.post("/transcribe", tags=["ASR"])
async def transcribe(
    file: UploadFile = File(None),
    url: str = Query(None, description="远程音频文件的 URL"),
    language: str = Query(None, description="指定语言代码 (如: zh, en, ja)，留空自动检测"),
    beam_size: int = Query(5, description="束搜索大小，影响准确率和速度"),
    task: str = Query("transcribe", description="任务类型: transcribe (转录) 或 translate (翻译为英文)")
):
    """
    音频转录接口
    
    支持上传文件或提供远程 URL，自动检测语言或指定语言
    """
    logger.info(f"收到转录请求 - 时间: {time.strftime('%H:%M:%S')}")
    
    if not file and not url:
        raise HTTPException(status_code=400, detail="必须提供文件或 URL")
    
    if asr_service is None:
        raise HTTPException(status_code=503, detail="ASR 服务未初始化")
    
    temp_file = None
    try:
        # 处理文件输入
        if file:
            temp_file = f"temp_{uuid.uuid4()}_{file.filename}"
            logger.info(f"保存上传文件: {temp_file}")
            with open(temp_file, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            temp_file = download_remote_file(url)
        
        # 转录参数
        transcribe_params = {
            "language": language,
            "beam_size": beam_size,
            "task": task
        }
        
        logger.info(f"开始转录 - 参数: {transcribe_params}")
        start_time = time.time()
        
        result = asr_service.transcribe(temp_file, **transcribe_params)
        
        end_time = time.time()
        latency = end_time - start_time
        inference_latencies.append(latency)
        
        # 添加性能信息
        result["performance"] = {
            "latency_seconds": round(latency, 2),
            "processing_time": f"{latency:.2f}s"
        }
        
        logger.info(f"转录完成 - 耗时: {latency:.2f}s, 语言: {result.get('language', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"转录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"转录失败: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            logger.debug(f"清理临时文件: {temp_file}")
            os.remove(temp_file)
