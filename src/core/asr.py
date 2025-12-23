import os
from faster_whisper import WhisperModel

class ASRService:
    def __init__(self, model_path: str, device: str = "cuda", compute_type: str = "float16"):
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Offline model not found at {self.model_path}")
        
        # CPU doesn't support float16, use int8 or float32
        actual_compute_type = self.compute_type
        if self.device == "cpu" and self.compute_type == "float16":
            actual_compute_type = "int8"
            
        print(f"Loading Faster-Whisper model from {self.model_path} on {self.device} ({actual_compute_type})...")
        self.model = WhisperModel(
            self.model_path, 
            device=self.device, 
            compute_type=actual_compute_type
        )
        print("Model loaded successfully.")

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
