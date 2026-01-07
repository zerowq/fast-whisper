import os
import sys
import shutil
from huggingface_hub import snapshot_download

def main():
    repo_id = "Systran/faster-whisper-large-v3"
    output_dir = os.path.join(os.getcwd(), "models")
    
    # Force use mirror for stability
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Starting robust download of {repo_id}...")
    print(f"To directory: {output_dir}")
    print(f"Using endpoint: {os.environ['HF_ENDPOINT']}")
    
    try:
        # Removed unsupported arguments 'max_retries' and 'resume_download'
        download_path = snapshot_download(
            repo_id=repo_id,
            local_dir=output_dir,
            local_dir_use_symlinks=False, 
            etag_timeout=60 # Increased timeout
        )
        print(f"\nDownload Finished! Model files are in: {download_path}")
        
        # Verify model.bin size
        model_bin = os.path.join(output_dir, "model.bin")
        if os.path.exists(model_bin):
            size_gb = os.path.getsize(model_bin) / (1024**3)
            print(f"Verified model.bin size: {size_gb:.2f} GB")
            if size_gb < 1.0:
                 print("Warning: model.bin seems too small. The download might be incomplete.")
                 sys.exit(1)
        
    except Exception as e:
        print(f"\nDownload encountered an error: {e}")
        print("\nIf terminal download keeps failing, you can manually download files from:")
        print(f"https://hf-mirror.com/{repo_id}/tree/main")
        print("And place them directly into the './models' folder.")
        sys.exit(1)

if __name__ == "__main__":
    main()
