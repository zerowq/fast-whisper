import requests
import sys
import os

def test_transcribe(input_val):
    url = "http://127.0.0.1:8899/transcribe"
    
    # Check if input is a URL or a file path
    if input_val.startswith("http://") or input_val.startswith("https://"):
        print(f"Testing with remote URL: {input_val}")
        try:
            response = requests.post(url, params={"url": input_val})
            handle_response(response)
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        # Local file path
        if not os.path.exists(input_val):
            print(f"Error: File {input_val} not found.")
            return
        print(f"Testing with local file: {input_val}")
        try:
            with open(input_val, "rb") as f:
                files = {"file": f}
                print("Waiting for server response (this could take a while for large-v3 on CPU)...")
                response = requests.post(url, files=files)
            handle_response(response)
        except Exception as e:
            print(f"An error occurred: {e}")

def handle_response(response):
    if response.status_code == 200:
        print("Success!")
        import json
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Failed with status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/test_api.py <file_path_or_url>")
        sys.exit(1)
    
    test_transcribe(sys.argv[1])
