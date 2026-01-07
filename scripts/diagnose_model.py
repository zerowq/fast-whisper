#!/usr/bin/env python3
"""
模型诊断脚本 - 快速检查模型配置问题
"""
import os
import sys
import subprocess

print("🔍 开始诊断模型问题...\n")

# 1. 检查 faster-whisper 版本
print("1️⃣ 检查 faster-whisper 版本:")
result = subprocess.run([sys.executable, "-m", "pip", "show", "faster-whisper"], 
                       capture_output=True, text=True)
if result.returncode == 0:
    for line in result.stdout.split('\n'):
        if 'Version' in line or 'Location' in line:
            print(f"   {line}")
else:
    print("   ❌ faster-whisper 未安装")

# 2. 检查模型文件
print("\n2️⃣ 检查模型文件:")
model_path = "./models"
if os.path.exists(model_path):
    files = os.listdir(model_path)
    print(f"   模型目录: {model_path}")
    print(f"   文件数: {len(files)}")
    for f in sorted(files):
        fsize = os.path.getsize(os.path.join(model_path, f)) / (1024*1024)
        print(f"   - {f} ({fsize:.1f}MB)")
else:
    print(f"   ❌ 模型目录不存在: {model_path}")

# 3. 测试模型加载
print("\n3️⃣ 测试模型加载:")
try:
    from faster_whisper import WhisperModel
    print("   ✅ faster_whisper 导入成功")
    
    # 尝试加载模型
    print("   正在加载 base 模型...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("   ✅ 模型加载成功")
    
    # 检查模型的 mel 配置
    if hasattr(model, 'model'):
        m = model.model
        print(f"   模型类型: {type(m).__name__}")
        if hasattr(m, 'encoder'):
            encoder = m.encoder
            print(f"   Encoder: {type(encoder).__name__}")
    
except Exception as e:
    print(f"   ❌ 模型加载失败: {e}")

# 4. 测试音频处理
print("\n4️⃣ 测试音频处理:")
audio_path = "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_1.wav"
if os.path.exists(audio_path):
    print(f"   找到测试音频: {audio_path}")
    try:
        import librosa
        audio, sr = librosa.load(audio_path, sr=None)
        print(f"   ✅ 音频加载成功")
        print(f"      采样率: {sr} Hz")
        print(f"      时长: {len(audio)/sr:.2f}s")
        
        # 检查 mel 谱
        print(f"\n   检查 mel 频谱:")
        mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80)
        print(f"   ✅ n_mels=80: shape={mel.shape}")
        
        mel_128 = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128)
        print(f"   ✅ n_mels=128: shape={mel_128.shape}")
        
    except ImportError:
        print("   ⚠️  librosa 未安装，跳过音频分析")
    except Exception as e:
        print(f"   ❌ 音频处理失败: {e}")
else:
    print(f"   ❌ 测试音频不存在: {audio_path}")

# 5. 建议
print("\n💡 解决方案:")
print("   如果遇到 mel 维度错误 (期望 80，得到 128):")
print("   ")
print("   方案 1: 重新下载模型")
print("   $ python scripts/download_models.py --model-size base --force")
print("   ")
print("   方案 2: 跳过转录测试验证其他功能")
print("   $ python scripts/verify_model.py --skip-transcription")
print("   ")
print("   方案 3: 升级 faster-whisper")
print("   $ uv add --upgrade faster-whisper")
print("   ")
print("✅ 诊断完成\n")
