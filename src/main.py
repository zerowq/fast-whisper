import uvicorn
from fastapi import FastAPI
from src.api import router as api_router
from src.core.asr import ASRService
import os
import logging
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment or defaults
MODEL_SIZE = os.getenv("MODEL_SIZE", "base")  # 默认使用 base 模型
MODEL_PATH = os.getenv("MODEL_PATH", "./models")
DEVICE = os.getenv("DEVICE", "auto")  # auto, cuda, cpu
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "auto")  # auto, float16, int8
PORT = int(os.getenv("PORT", 8080))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("🚀 启动 Faster-Whisper ASR 服务...")
    logger.info(f"配置 - 模型: {MODEL_SIZE}, 设备: {DEVICE}, 计算类型: {COMPUTE_TYPE}")
    
    from src.api import router
    
    try:
        # 创建 ASR 服务实例
        router.asr_service = ASRService(
            model_size=MODEL_SIZE,
            model_path=MODEL_PATH,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        
        # 预加载模型
        logger.info("正在加载模型...")
        success = router.asr_service.load_model()
        
        if success:
            model_info = router.asr_service.get_model_info()
            logger.info(f"✅ 服务启动成功!")
            logger.info(f"   模型: {model_info['model_size']} ({model_info['parameters']})")
            logger.info(f"   设备: {model_info['device']}")
            logger.info(f"   计算类型: {model_info['compute_type']}")
            logger.info(f"   端口: {PORT}")
        else:
            logger.error("❌ 模型加载失败，服务可能无法正常工作")
            
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        logger.info("提示: 请确保已下载模型文件")
        logger.info(f"运行: python scripts/download_models.py --size {MODEL_SIZE}")
        # 不抛出异常，让服务继续启动，但会在请求时报错
    
    yield
    
    # Shutdown logic
    logger.info("🛑 关闭 ASR 服务...")

# Read root path from environment (for reverse proxy sub-paths)
ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Faster-Whisper ASR Service (Optimized)", 
    description=f"轻量化语音识别服务 - 默认使用 {MODEL_SIZE} 模型",
    version="2.0.0",
    lifespan=lifespan,
    root_path=ROOT_PATH
)

app.include_router(api_router.router, tags=["ASR"])

# Mount static files
static_dir = os.path.join(os.getcwd(), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    logger.info(f"🌟 启动 Faster-Whisper ASR 服务在端口 {PORT}")
    logger.info("访问 http://localhost:8080/docs 查看 API 文档")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
