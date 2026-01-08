#!/usr/bin/env python3
"""
GPU vs CPU 性能对比测试脚本
同时测试 GPU 和 CPU 模式，生成对比报告
"""
import os
import sys
import subprocess
import time
import json
import requests
from datetime import datetime
from pathlib import Path

class GPUvsCPUComparison:
    """GPU 和 CPU 性能对比"""
    
    def __init__(self):
        self.gpu_port = 8898
        self.cpu_port = 8897
        self.gpu_url = f"http://localhost:{self.gpu_port}"
        self.cpu_url = f"http://localhost:{self.cpu_port}"
        self.test_files = [
            "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_1.wav",
            "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_2.wav",
            "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_3.wav",
        ]
    
    def check_service(self, url: str) -> bool:
        """检查服务是否在线"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_cpu_container(self) -> bool:
        """启动 CPU 模式容器"""
        print("🚀 启动 CPU 模式容器...")
        
        # 检查是否已经运行
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=faster-whisper-asr-cpu"],
            capture_output=True, text=True
        )
        
        if result.stdout.strip():
            print("⚠️  CPU 容器已在运行，跳过启动")
            return True
        
        # 启动 CPU 容器
        cmd = [
            "docker", "run", "-d",
            "--name", "faster-whisper-asr-cpu",
            "-p", f"{self.cpu_port}:8898",
            "-e", "DEVICE=cpu",
            "-e", "COMPUTE_TYPE=int8",
            "-e", "PORT=8898",
            "-v", os.path.expanduser("~/.cache/huggingface") + ":/root/.cache/huggingface",
            "-v", "/home/work/evyd/code/speech/cosyvoice-mms:/home/work/evyd/code/speech/cosyvoice-mms",
            "faster-whisper-asr:latest"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 启动 CPU 容器失败: {result.stderr}")
            return False
        
        print(f"✅ CPU 容器已启动: {result.stdout.strip()[:12]}")
        
        # 等待容器启动
        print("⏳ 等待 CPU 容器启动完成...")
        for i in range(60):
            if self.check_service(self.cpu_url):
                print("✅ CPU 容器已就绪")
                return True
            time.sleep(1)
        
        print("❌ CPU 容器启动超时")
        return False
    
    def get_resource_usage(self, container_name: str) -> dict:
        """获取容器资源使用情况"""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", container_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # 解析 docker stats 输出
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # CONTAINER ID   NAME    CPU %    MEM USAGE / LIMIT
                    parts = lines[1].split()
                    return {
                        "cpu_percent": float(parts[2].rstrip('%')),
                        "memory_usage": parts[3],
                    }
        except:
            pass
        return {"cpu_percent": 0, "memory_usage": "0B"}
    
    def get_gpu_usage(self) -> dict:
        """获取 GPU 使用情况"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(',')
                    return {
                        "gpu_utilization": float(parts[1]),
                        "gpu_memory_used_mb": float(parts[2]),
                        "gpu_memory_total_mb": float(parts[3])
                    }
        except:
            pass
        return {"gpu_utilization": 0, "gpu_memory_used_mb": 0, "gpu_memory_total_mb": 0}
    
    def test_performance(self, url: str, device: str) -> dict:
        """测试性能"""
        print(f"\n{'='*80}")
        print(f"🧪 开始 {device.upper()} 性能测试")
        print(f"{'='*80}\n")
        
        results = []
        container_name = "faster-whisper-asr" if device == "gpu" else "faster-whisper-asr-cpu"
        
        for audio_file in self.test_files:
            if not os.path.exists(audio_file):
                print(f"❌ 文件不存在: {audio_file}")
                continue
            
            filename = os.path.basename(audio_file)
            file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
            
            print(f"🎵 测试: {filename} ({file_size_mb:.2f}MB)")
            
            # 获取音频时长
            try:
                import wave
                with wave.open(audio_file, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / rate
            except:
                duration = 0
            
            # 发送转录请求
            start_time = time.time()
            resource_before = self.get_resource_usage(container_name)
            gpu_before = self.get_gpu_usage() if device == "gpu" else {}
            
            try:
                with open(audio_file, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(
                        f"{url}/transcribe",
                        files=files,
                        params={'beam_size': 5, 'task': 'transcribe'},
                        timeout=600
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    transcription_time = time.time() - start_time
                    resource_after = self.get_resource_usage(container_name)
                    gpu_after = self.get_gpu_usage() if device == "gpu" else {}
                    rtf = transcription_time / duration if duration > 0 else 0
                    
                    print(f"  ✅ 转录成功 ({transcription_time:.2f}s)")
                    print(f"     CPU占用: {resource_after['cpu_percent']:.1f}%")
                    print(f"     内存占用: {resource_after['memory_usage']}")
                    
                    if device == "gpu" and gpu_after:
                        print(f"     GPU利用率: {gpu_after['gpu_utilization']:.1f}%")
                        print(f"     GPU内存: {gpu_after['gpu_memory_used_mb']:.0f}MB / {gpu_after['gpu_memory_total_mb']:.0f}MB")
                    
                    results.append({
                        "filename": filename,
                        "file_size_mb": file_size_mb,
                        "duration_s": duration,
                        "transcription_time_s": transcription_time,
                        "rtf": rtf,
                        "speed": 1/rtf if rtf > 0 else 0,
                        "text_preview": result.get('segments', [{}])[0].get('text', '')[:100] if isinstance(result.get('segments'), list) else '',
                        "cpu_percent": resource_after['cpu_percent'],
                        "memory_usage": resource_after['memory_usage'],
                        "gpu_utilization": gpu_after.get('gpu_utilization', 0) if device == "gpu" else 0,
                        "gpu_memory_used_mb": gpu_after.get('gpu_memory_used_mb', 0) if device == "gpu" else 0,
                        "gpu_memory_total_mb": gpu_after.get('gpu_memory_total_mb', 0) if device == "gpu" else 0
                    })
                else:
                    print(f"  ❌ 转录失败: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 错误: {e}")
        
        return {
            "device": device,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_comparison_report(self, gpu_data: dict, cpu_data: dict) -> str:
        """生成对比报告"""
        report = []
        report.append("# GPU vs CPU 性能对比测试报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 提取统计数据
        gpu_results = gpu_data['results']
        cpu_results = cpu_data['results']
        
        if gpu_results and cpu_results:
            # GPU 统计
            gpu_total_duration = sum(r['duration_s'] for r in gpu_results)
            gpu_total_time = sum(r['transcription_time_s'] for r in gpu_results)
            gpu_avg_rtf = gpu_total_time / gpu_total_duration if gpu_total_duration > 0 else 0
            gpu_avg_speed = 1 / gpu_avg_rtf if gpu_avg_rtf > 0 else 0
            
            # CPU 统计
            cpu_total_duration = sum(r['duration_s'] for r in cpu_results)
            cpu_total_time = sum(r['transcription_time_s'] for r in cpu_results)
            cpu_avg_rtf = cpu_total_time / cpu_total_duration if cpu_total_duration > 0 else 0
            cpu_avg_speed = 1 / cpu_avg_rtf if cpu_avg_rtf > 0 else 0
            
            # 性能对比
            speedup = gpu_avg_speed / cpu_avg_speed if cpu_avg_speed > 0 else 0
            time_reduction = (cpu_total_time - gpu_total_time) / cpu_total_time * 100 if cpu_total_time > 0 else 0
            
            report.append("## 📊 性能对比汇总\n\n")
            report.append("| 指标 | CPU 模式 | GPU 模式 | 性能提升 |\n")
            report.append("|------|---------|---------|----------|\n")
            report.append(f"| **处理速度** | {cpu_avg_speed:.1f}x | {gpu_avg_speed:.1f}x | **{speedup:.1f}x** ⭐ |\n")
            report.append(f"| **总耗时** | {cpu_total_time:.2f}s | {gpu_total_time:.2f}s | **-{time_reduction:.1f}%** |\n")
            report.append(f"| **平均RTF** | {cpu_avg_rtf:.3f} | {gpu_avg_rtf:.3f} | **{cpu_avg_rtf/gpu_avg_rtf:.1f}x 更快** |\n")
            report.append(f"| **文件数** | {len(cpu_results)} | {len(gpu_results)} | - |\n\n")
            
            # 详细对比表
            report.append("## 📈 详细对比结果\n\n")
            report.append("### CPU 模式\n")
            report.append("| 文件名 | 大小(MB) | 时长(s) | 转录耗时(s) | 处理速度 | RTF | CPU占用 | 内存占用 |\n")
            report.append("|--------|---------|--------|-----------|---------|-----|---------|----------|\n")
            for r in cpu_results:
                cpu_pct = r.get('cpu_percent', 0)
                mem_usage = r.get('memory_usage', '0B')
                report.append(f"| {r['filename']} | {r['file_size_mb']:.2f} | {r['duration_s']:.2f} | {r['transcription_time_s']:.2f} | {r['speed']:.1f}x | {r['rtf']:.3f} | {cpu_pct:.1f}% | {mem_usage} |\n")
            
            report.append("\n### GPU 模式\n")
            report.append("| 文件名 | 大小(MB) | 时长(s) | 转录耗时(s) | 处理速度 | RTF | CPU占用 | 内存占用 | GPU利用率 | GPU显存 |\n")
            report.append("|--------|---------|--------|-----------|---------|-----|---------|----------|----------|----------|\n")
            for r in gpu_results:
                cpu_pct = r.get('cpu_percent', 0)
                mem_usage = r.get('memory_usage', '0B')
                gpu_util = r.get('gpu_utilization', 0)
                gpu_mem = r.get('gpu_memory_used_mb', 0)
                report.append(f"| {r['filename']} | {r['file_size_mb']:.2f} | {r['duration_s']:.2f} | {r['transcription_time_s']:.2f} | {r['speed']:.1f}x | {r['rtf']:.3f} | {cpu_pct:.1f}% | {mem_usage} | {gpu_util:.1f}% | {gpu_mem:.0f}MB |\n")
            
            # 性能评价
            report.append("\n## ✅ 性能评价\n\n")
            report.append("### 🚀 GPU 优势\n")
            report.append(f"- **处理速度提升**: {speedup:.1f} 倍\n")
            report.append(f"- **总体时间节省**: {time_reduction:.1f}%\n")
            
            if speedup > 4:
                report.append(f"- ⭐⭐⭐ **优秀** - GPU 加速效果显著\n")
            elif speedup > 2:
                report.append(f"- ⭐⭐ **良好** - GPU 加速效果明显\n")
            else:
                report.append(f"- ⭐ **可用** - GPU 加速有效果\n")
            
            report.append("\n### 💡 建议\n")
            if gpu_avg_speed > 30:
                report.append("- GPU 性能充分，建议用于生产环境\n")
            elif gpu_avg_speed > 10:
                report.append("- GPU 性能良好，适合中等负载\n")
            else:
                report.append("- GPU 性能可以，评估是否需要优化\n")
        
        report.append("\n---\n")
        report.append(f"*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        return "".join(report)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPU vs CPU 性能对比测试")
    parser.add_argument("--skip-cpu", action="store_true", help="跳过 CPU 测试（仅测试 GPU）")
    parser.add_argument("--output", default="gpu_cpu_comparison_report.md", help="报告输出文件")
    
    args = parser.parse_args()
    
    comparator = GPUvsCPUComparison()
    
    # 检查 GPU 服务
    print("🔍 检查 GPU 服务...")
    if not comparator.check_service(comparator.gpu_url):
        print(f"❌ GPU 服务不可用: {comparator.gpu_url}")
        print("请确保 GPU 容器正在运行:")
        print("  docker ps | grep faster-whisper-asr")
        sys.exit(1)
    print(f"✅ GPU 服务在线\n")
    
    # GPU 测试
    gpu_data = comparator.test_performance(comparator.gpu_url, "gpu")
    
    # CPU 测试
    if not args.skip_cpu:
        # 启动 CPU 容器
        if not comparator.start_cpu_container():
            print("❌ 无法启动 CPU 容器，跳过 CPU 测试")
            cpu_data = None
        else:
            # 等待 CPU 容器完全准备好
            print("⏳ 等待 CPU 容器完全准备...")
            time.sleep(5)
            cpu_data = comparator.test_performance(comparator.cpu_url, "cpu")
    else:
        print("⏭️  跳过 CPU 测试")
        cpu_data = None
    
    # 生成报告
    print("\n" + "="*80)
    print("📝 生成对比报告...")
    print("="*80 + "\n")
    
    if cpu_data:
        report = comparator.generate_comparison_report(gpu_data, cpu_data)
    else:
        # 只有 GPU 数据时生成单独报告
        report = f"# GPU 性能测试报告\n\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        if gpu_data['results']:
            gpu_total_duration = sum(r['duration_s'] for r in gpu_data['results'])
            gpu_total_time = sum(r['transcription_time_s'] for r in gpu_data['results'])
            gpu_avg_rtf = gpu_total_time / gpu_total_duration if gpu_total_duration > 0 else 0
            gpu_avg_speed = 1 / gpu_avg_rtf if gpu_avg_rtf > 0 else 0
            report += f"- **平均处理速度**: {gpu_avg_speed:.1f}x 实时速度\n"
            report += f"- **总耗时**: {gpu_total_time:.2f}s\n"
            report += f"- **总音频时长**: {gpu_total_duration:.2f}s\n"
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {args.output}\n")
    print("="*80)
    print(report)
    print("="*80)

if __name__ == "__main__":
    main()
