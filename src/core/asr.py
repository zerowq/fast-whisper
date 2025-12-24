import os
from faster_whisper import WhisperModel

class ASRService:
    def __init__(self, model_path: str, device: str = "cuda", compute_type: str = "float16"):
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.model = None

        print(f"Loading Faster-Whisper model from {self.model_path} on {self.device} ({actual_compute_type})...")
        try:
            self.model = WhisperModel(
                self.model_path, 
                device=self.device, 
                compute_type=actual_compute_type
            )
        except Exception as e:
            if self.device == "cuda":
                print(f"Warning: Failed to load model on CUDA: {e}. Falling back to CPU...")
                self.device = "cpu"
                actual_compute_type = "int8"
                self.model = WhisperModel(
                    self.model_path,
                    device="cpu",
                    compute_type="int8"
                )
            else:
                raise e
        print(f"Model loaded successfully on {self.device}.")

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
