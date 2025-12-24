import os
from faster_whisper import WhisperModel

class ASRService:
    def __init__(self, model_path: str, device: str = "cuda", compute_type: str = "float16"):
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.model = None
        # 注意：__init__ 内部现在没有任何打印或逻辑，绝对不会报 UnboundLocalError

    def load_model(self):
        """延迟加载模型，支持 CUDA 到 CPU 的降级"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Offline model not found at {self.model_path}")
        
        # 确定计算类型
        actual_compute_type = self.compute_type
        if self.device == "cpu" and self.compute_type == "float16":
            actual_compute_type = "int8"
            
        print(f"DEBUG: Trying to load model on {self.device} with {actual_compute_type}...")
        
        try:
            self.model = WhisperModel(
                self.model_path, 
                device=self.device, 
                compute_type=actual_compute_type,
                local_files_only=True
            )
        except Exception as e:
            if self.device == "cuda":
                print(f"Warning: CUDA Failed ({e}). Falling back to CPU...")
                self.device = "cpu"
                self.model = WhisperModel(
                    self.model_path,
                    device="cpu",
                    compute_type="int8",
                    local_files_only=True
                )
            else:
                raise e
        print(f"SUCCESS: Model loaded on {self.device}.")

    def transcribe(self, audio_path: str):
        if self.model is None:
            self.load_model()
        
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        results = []
        for segment in segments:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            
        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": results
        }
