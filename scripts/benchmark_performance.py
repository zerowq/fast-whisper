#!/usr/bin/env python3
"""
性能基准测试脚本 - 测试不同音频文件的转录性能和资源占用
"""
import os
import sys
import time
import logging
from pathlib import Path
from tabulate import tabulate

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.asr import ASRService
from core.resource_monitor import get_resource_monitor

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """性能基准测试器"""
    
    def __init__(self):
        self.asr_service = ASRService(model_size="base", model_path="./models", device="auto", compute_type="auto")
        self.resource_monitor = get_resource_monitor()
        self.results = []
    
    def get_audio_info(self, audio_path: str) -> dict:
        """获取音频文件信息"""
        import wave
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / rate
            return {
                "size_mb": file_size_mb,
                "duration_s": duration,
                "sample_rate": rate
            }
        except:
            return {
                "size_mb": file_size_mb,
                "duration_s": 0,
                "sample_rate": 0
            }
    
    def benchmark_audio(self, audio_path: str) -> dict:
        """基准测试单个音频文件"""
        print(f"\n🎵 测试: {os.path.basename(audio_path)}")
        
        audio_info = self.get_audio_info(audio_path)
        
        # 记录初始资源
        initial_metrics = self.resource_monitor.get_metrics()
        initial_cpu = initial_metrics.cpu_percent
        initial_mem = initial_metrics.memory_percent
        initial_gpu_mem = initial_metrics.gpu_memory_percent if initial_metrics.gpu_available else 0
        
        # 转录
        start_time = time.time()
        try:
            result = self.asr_service.transcribe(audio_path, beam_size=5)
            transcription_time = time.time() - start_time
            transcription_text = result.get('segments', [{}])[0].get('text', '')[:50]
        except Exception as e:
            print(f"❌ 转录失败: {e}")
            return None
        
        # 记录结束资源
        final_metrics = self.resource_monitor.get_metrics()
        final_cpu = final_metrics.cpu_percent
        final_mem = final_metrics.memory_percent
        final_gpu_mem = final_metrics.gpu_memory_percent if final_metrics.gpu_available else 0
        
        # 计算实时因子 (RTF)
        rtf = transcription_time / audio_info["duration_s"]
        
        return {
            "filename": os.path.basename(audio_path),
            "size_mb": f"{audio_info['size_mb']:.2f}",
            "duration_s": f"{audio_info['duration_s']:.2f}",
            "transcription_time_s": f"{transcription_time:.2f}",
            "rtf": f"{rtf:.2f}",
            "cpu_usage": f"{final_cpu:.1f}%",
            "memory_usage": f"{final_mem:.1f}%",
            "gpu_memory": f"{final_gpu_mem:.1f}%",
            "text_preview": transcription_text
        }
    
    def run_benchmark(self, audio_files: list):
        """运行基准测试"""
        print("🚀 开始性能基准测试...\n")
        print("=" * 100)
        
        # 加载模型
        print("📊 加载模型...")
        if not self.asr_service.load_model():
            print("❌ 模型加载失败")
            return
        print("✅ 模型已加载\n")
        
        # 测试每个音频文件
        for audio_path in audio_files:
            if not os.path.exists(audio_path):
                print(f"⚠️  文件不存在: {audio_path}")
                continue
            
            result = self.benchmark_audio(audio_path)
            if result:
                self.results.append(result)
        
        # 打印表格
        if self.results:
            print("\n" + "=" * 100)
            print("📈 性能基准测试结果\n")
            
            headers = [
                "文件名",
                "文件大小(MB)",
                "音频时长(s)",
                "转录耗时(s)",
                "实时因子(RTF)",
                "CPU占用",
                "内存占用",
                "GPU内存占用",
                "转录文本预览"
            ]
            
            print(tabulate(
                [[
                    r["filename"],
                    r["size_mb"],
                    r["duration_s"],
                    r["transcription_time_s"],
                    r["rtf"],
                    r["cpu_usage"],
                    r["memory_usage"],
                    r["gpu_memory"],
                    r["text_preview"]
                ] for r in self.results],
                headers=headers,
                tablefmt="grid"
            ))
            
            # 统计信息
            print("\n📊 统计信息:")
            total_duration = sum(float(r["duration_s"]) for r in self.results)
            total_time = sum(float(r["transcription_time_s"]) for r in self.results)
            avg_rtf = total_time / total_duration if total_duration > 0 else 0
            
            print(f"   总音频时长: {total_duration:.2f}s")
            print(f"   总转录耗时: {total_time:.2f}s")
            print(f"   平均实时因子: {avg_rtf:.2f}")
            print(f"   处理速度: {total_duration/total_time:.2f}x 实时速度")
            
        print("\n✅ 测试完成\n")

def main():
    """主函数"""
    # 测试文件列表
    test_files = [
        "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_1.wav",
        "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_2.wav",
        "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_3.wav",
    ]
    
    benchmark = PerformanceBenchmark()
    benchmark.run_benchmark(test_files)

if __name__ == "__main__":
    main()
