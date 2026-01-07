import requests
import sys
import os
import time

def check_server_health(url: str, max_retries: int = 3, timeout: int = 5) -> bool:
    """检查服务器是否在线"""
    base_url = url.rsplit('/', 1)[0]  # 移除 /transcribe
    health_url = f"{base_url}/health"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(health_url, timeout=timeout)
            if response.status_code == 200:
                print(f"✅ 服务器在线 ({health_url})")
                return True
        except requests.exceptions.ConnectionError:
            print(f"⏳ 服务器未响应 (尝试 {attempt + 1}/{max_retries})...")
            if attempt < max_retries - 1:
                time.sleep(1)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ 检查服务器健康状态失败: {e}")
    
    return False

def test_transcribe(input_val):
    # 从环境变量获取端口，默认 8898
    port = os.getenv("PORT", "8898")
    url = f"http://127.0.0.1:{port}/transcribe"
    
    # 先检查服务器是否在线
    if not check_server_health(url):
        print(f"❌ 无法连接到服务器 ({url})")
        print(f"   请确保服务已启动: python src/main.py")
        sys.exit(1)
    
    # Check if input is a URL or a file path
    if input_val.startswith("http://") or input_val.startswith("https://"):
        print(f"🌐 使用远程 URL: {input_val}")
        try:
            response = requests.post(url, params={"url": input_val}, timeout=300)
            handle_response(response)
        except Exception as e:
            print(f"❌ 错误: {e}")
            sys.exit(1)
    else:
        # Local file path
        if not os.path.exists(input_val):
            print(f"❌ 文件不存在: {input_val}")
            sys.exit(1)
        
        print(f"📁 使用本地文件: {input_val}")
        print(f"⏳ 等待服务器响应 (大型模型在 CPU 上可能需要较长时间)...")
        try:
            with open(input_val, "rb") as f:
                files = {"file": f}
                response = requests.post(url, files=files, timeout=600)
            handle_response(response)
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时，服务器处理时间过长")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 错误: {e}")
            sys.exit(1)

def handle_response(response):
    if response.status_code == 200:
        print("✅ 转录成功!")
        import json
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"❌ 失败 (状态码: {response.status_code})")
        print(f"响应: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/test_api.py <文件路径或URL>")
        print()
        print("示例:")
        print("  # 测试本地文件")
        print("  python scripts/test_api.py test_audio.wav")
        print()
        print("  # 测试远程 URL")
        print("  python scripts/test_api.py https://example.com/audio.wav")
        sys.exit(1)
    
    test_transcribe(sys.argv[1])
