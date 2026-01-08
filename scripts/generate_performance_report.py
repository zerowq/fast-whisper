#!/usr/bin/env python3
"""
性能测试和报告生成脚本 - 用于领导演示
测试 Docker 容器中的 GPU 和 CPU 性能
"""
import os
import sys
import time
import requests
import subprocess
import json
from datetime import datetime
from pathlib import Path

class PerformanceReporter:
    """性能测试和报告生成器"""
    
    def __init__(self, api_url="http://localhost:8898"):
        self.api_url = api_url
        self.results = []
        self.gpu_metrics = []
        self.cpu_metrics = []
        
    def check_service_health(self) -> bool:
        """检查服务是否在线"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_gpu_status(self) -> dict:
        """获取 GPU 状态"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu", 
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines:
                    parts = [x.strip() for x in line.split(',')]
                    if len(parts) >= 5:
                        gpus.append({
                            "index": parts[0],
                            "name": parts[1],
                            "memory_used_mb": float(parts[2]),
                            "memory_total_mb": float(parts[3]),
                            "gpu_utilization": float(parts[4])
                        })
                return {"gpus": gpus, "available": True}
        except:
            pass
        return {"gpus": [], "available": False}
    
    def get_cpu_status(self) -> dict:
        """获取 CPU 状态"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=5
            )
            # 查找 Python 进程的 CPU 使用率
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / (1024*1024),
                "memory_total_mb": memory.total / (1024*1024)
            }
        except:
            return {}
    
    def test_audio_file(self, audio_path: str, device: str = "gpu") -> dict:
        """测试单个音频文件"""
        if not os.path.exists(audio_path):
            print(f"❌ 文件不存在: {audio_path}")
            return None
        
        filename = os.path.basename(audio_path)
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        
        print(f"\n🎵 测试: {filename} ({file_size_mb:.2f}MB)")
        
        # 获取音频时长
        try:
            import wave
            with wave.open(audio_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / rate
        except:
            duration = 0
        
        # 记录开始 GPU 状态
        gpu_before = self.get_gpu_status()
        cpu_before = self.get_cpu_status()
        
        # 发送转录请求
        start_time = time.time()
        try:
            with open(audio_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.api_url}/transcribe",
                    files=files,
                    params={'beam_size': 5, 'task': 'transcribe'},
                    timeout=600
                )
            
            if response.status_code == 200:
                result = response.json()
                transcription_time = time.time() - start_time
                
                # 记录结束 GPU 状态
                gpu_after = self.get_gpu_status()
                cpu_after = self.get_cpu_status()
                
                # 计算性能指标
                rtf = transcription_time / duration if duration > 0 else 0
                
                print(f"  ✅ 转录成功")
                print(f"     文件大小: {file_size_mb:.2f}MB")
                print(f"     音频时长: {duration:.2f}s")
                print(f"     转录耗时: {transcription_time:.2f}s")
                print(f"     实时因子: {rtf:.2f} (1={1/rtf:.1f}x 实时速度)")
                
                return {
                    "filename": filename,
                    "file_size_mb": file_size_mb,
                    "duration_s": duration,
                    "transcription_time_s": transcription_time,
                    "rtf": rtf,
                    "speed": f"{1/rtf:.1f}x" if rtf > 0 else "N/A",
                    "text_preview": result.get('segments', [{}])[0].get('text', '')[:100] if isinstance(result.get('segments'), list) else '',
                    "language": result.get('language', 'unknown'),
                    "gpu_memory_before": gpu_before['gpus'][0]['memory_used_mb'] if gpu_before['gpus'] else 0,
                    "gpu_memory_after": gpu_after['gpus'][0]['memory_used_mb'] if gpu_after['gpus'] else 0,
                    "gpu_util_max": max([g['gpu_utilization'] for g in gpu_after['gpus']]) if gpu_after['gpus'] else 0,
                    "cpu_percent": cpu_after.get('cpu_percent', 0),
                    "memory_percent": cpu_after.get('memory_percent', 0),
                    "device": device
                }
            else:
                print(f"  ❌ 转录失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            return None
    
    def generate_report(self, results: list) -> str:
        """生成 Markdown 格式报告"""
        report = []
        report.append("# Faster-Whisper ASR 性能测试报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**测试服务**: http://localhost:8898\n")
        report.append(f"**测试文件数**: {len(results)}\n\n")
        
        # 系统信息
        report.append("## 📊 系统信息\n")
        gpu_status = self.get_gpu_status()
        if gpu_status['available'] and gpu_status['gpus']:
            gpu = gpu_status['gpus'][0]
            report.append(f"- **GPU**: {gpu['name']}\n")
            report.append(f"- **GPU内存**: {gpu['memory_used_mb']:.0f}MB / {gpu['memory_total_mb']:.0f}MB\n")
            report.append(f"- **GPU利用率**: {gpu['gpu_utilization']:.1f}%\n")
        
        cpu_status = self.get_cpu_status()
        if cpu_status:
            report.append(f"- **CPU使用率**: {cpu_status.get('cpu_percent', 0):.1f}%\n")
            report.append(f"- **内存使用**: {cpu_status.get('memory_used_mb', 0):.0f}MB / {cpu_status.get('memory_total_mb', 0):.0f}MB\n")
        
        report.append("\n## 📈 性能测试结果\n")
        report.append("| 文件名 | 大小(MB) | 时长(s) | 转录耗时(s) | 实时因子 | 处理速度 | 语言 | GPU内存增加 | 最大GPU利用率 |\n")
        report.append("|--------|---------|--------|-----------|---------|---------|------|-----------|---------------|\n")
        
        for r in results:
            if r:
                gpu_mem_increase = r['gpu_memory_after'] - r['gpu_memory_before']
                report.append(f"| {r['filename']} | {r['file_size_mb']:.2f} | {r['duration_s']:.2f} | {r['transcription_time_s']:.2f} | {r['rtf']:.3f} | {r['speed']} | {r['language']} | {gpu_mem_increase:.0f}MB | {r['gpu_util_max']:.1f}% |\n")
        
        # 统计
        report.append("\n## 📊 统计汇总\n")
        valid_results = [r for r in results if r]
        if valid_results:
            total_duration = sum(r['duration_s'] for r in valid_results)
            total_time = sum(r['transcription_time_s'] for r in valid_results)
            avg_rtf = total_time / total_duration if total_duration > 0 else 0
            avg_speed = 1 / avg_rtf if avg_rtf > 0 else 0
            avg_gpu_util = sum(r['gpu_util_max'] for r in valid_results) / len(valid_results)
            
            report.append(f"- **总音频时长**: {total_duration:.2f}s\n")
            report.append(f"- **总转录耗时**: {total_time:.2f}s\n")
            report.append(f"- **平均实时因子(RTF)**: {avg_rtf:.3f}\n")
            report.append(f"- **平均处理速度**: {avg_speed:.1f}x 实时速度\n")
            report.append(f"- **平均GPU利用率**: {avg_gpu_util:.1f}%\n")
            report.append(f"- **文件数**: {len(valid_results)}\n")
        
        # 转录质量示例
        report.append("\n## 🎯 转录质量示例\n")
        for i, r in enumerate(valid_results[:3], 1):
            if r and r['text_preview']:
                report.append(f"\n**样本 {i}** ({r['filename']}):\n")
                report.append(f"> {r['text_preview']}...\n")
        
        # 性能评价
        report.append("\n## ✅ 性能评价\n")
        if valid_results:
            avg_speed = 1 / avg_rtf if avg_rtf > 0 else 0
            if avg_speed > 50:
                report.append("- ⭐⭐⭐ **优秀** - 处理速度超过 50x 实时速度\n")
            elif avg_speed > 10:
                report.append("- ⭐⭐ **良好** - 处理速度 10-50x 实时速度\n")
            elif avg_speed > 1:
                report.append("- ⭐ **可用** - 处理速度 1-10x 实时速度\n")
            else:
                report.append("- ⭐ **需改进** - 处理速度低于 1x 实时速度\n")
            
            if avg_gpu_util > 80:
                report.append("- GPU 充分利用，性能最优\n")
            elif avg_gpu_util > 50:
                report.append("- GPU 利用率中等，可进一步优化\n")
            else:
                report.append("- GPU 利用率较低，可调整并发参数\n")
        
        report.append("\n---\n")
        report.append(f"*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        return "".join(report)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="性能测试和报告生成")
    parser.add_argument("--api-url", default="http://localhost:8898", help="API 地址")
    parser.add_argument("--output", default="performance_report.md", help="报告输出文件")
    
    args = parser.parse_args()
    
    # 初始化报告器
    reporter = PerformanceReporter(args.api_url)
    
    # 检查服务
    print("🔍 检查服务状态...")
    if not reporter.check_service_health():
        print(f"❌ 服务不可用: {args.api_url}")
        print("请确保 Docker 容器正在运行:")
        print("  docker ps | grep faster-whisper-asr")
        sys.exit(1)
    
    print(f"✅ 服务在线: {args.api_url}\n")
    
    # 测试文件列表
    test_files = [
        "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_1.wav",
        "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_2.wav",
        "/home/work/evyd/code/speech/cosyvoice-mms/output/benchmark/kokoro_test_3.wav",
    ]
    
    print("🚀 开始性能测试...\n")
    results = []
    for audio_file in test_files:
        result = reporter.test_audio_file(audio_file, device="gpu")
        if result:
            results.append(result)
    
    # 生成报告
    print("\n\n📝 生成性能报告...")
    report = reporter.generate_report(results)
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {args.output}")
    print("\n" + "="*80)
    print(report)
    print("="*80)

if __name__ == "__main__":
    main()
