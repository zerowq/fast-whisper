from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import shutil
import os
import urllib.request
import uuid
import time
from src.core.asr import ASRService

router = APIRouter()

# Global ASR instance, initialized in main.py
asr_service = None

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
        
        print(f"DEBUG: Inference completed in {end_time - start_time:.2f} seconds.")
        return result
    except Exception as e:
        print(f"ERROR: Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file and os.path.exists(temp_file):
            print(f"DEBUG: Cleaning up temp file {temp_file}")
            os.remove(temp_file)
