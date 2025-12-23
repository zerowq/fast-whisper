import uvicorn
from fastapi import FastAPI
from src.api import router as api_router
from src.core.asr import ASRService
import os
from contextlib import asynccontextmanager

# Configuration from environment or defaults
# Updated: Default to ./models as per recent download results
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

app = FastAPI(title="Faster-Whisper ASR Service", lifespan=lifespan)
app.include_router(api_router.router, tags=["ASR"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8899)
