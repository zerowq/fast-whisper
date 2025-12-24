import uvicorn
from fastapi import FastAPI
from src.api import router as api_router
from src.core.asr import ASRService
import os
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Configuration from environment or defaults
MODEL_PATH = os.getenv("MODEL_PATH", "./models")
DEVICE = os.getenv("DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "float16")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    from src.api import router
    router.asr_service = ASRService(
        model_path=MODEL_PATH,
        device=DEVICE,
        compute_type=COMPUTE_TYPE
    )
    router.asr_service.load_model()
    yield
    # Shutdown logic (optional)
    print("Shutting down ASR service...")

# Read root path from environment (for reverse proxy sub-paths)
ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(
    title="Faster-Whisper ASR Service", 
    lifespan=lifespan,
    root_path=ROOT_PATH
)
app.include_router(api_router.router, prefix="/api", tags=["ASR"])

# Mount static files
static_dir = os.path.join(os.getcwd(), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
