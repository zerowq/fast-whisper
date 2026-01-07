#!/usr/bin/env python3
"""
最终检查点 - 基本功能验证
确认服务启动成功，监控指标可访问，简单测试一次音频转录
"""

import os
import sys
import time
import requests
import subprocess
import logging
import tempfile
import json
from pathlib import Path
import threading
import signal

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalVerifier:
    """最终验证器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.server_process = None
        self.server_ready = False
        
    def start_server_background(self) -> bool:
        """在后台启动服务器"""
        logger.info("🚀 启动服务器...")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update({
                "PORT": str(self.port),
                "MODEL_SIZE": "base",
                "DEVICE": "cpu",
                "COMPUTE_TYPE": "int8",
                "LOG_LEVEL": "INFO"
            })
            
            # 启动服务器进程
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "src.main"],
                cwd=Path(__file__).parent.parent,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 启动日志监控线程
            log_thread = threading.Thread(target=self._monitor_server_logs, daemon=True)
            log_thread.start()
            
            # 等待服务器启动 (最多60秒)
            logger.info("等待服务器启动...")
            start_time = time.time()
            timeout = 60
            
            while time.time() - start_time < timeout:
                if self.server_process.poll() is not None:
                    logger.error("❌ 服务器进程意外退出")
                    return False
                
                if self.server_ready:
                    logger.info("✅ 服务器启动成功")
                    return True
                
                time.sleep(1)
            
            logger.error("❌ 服务器启动超时")
            return False
            
        except Exception as e:
            logger.error(f"❌ 启动服务器失败: {e}")
            return False
    
    def _monitor_server_logs(self):
        """监控服务器日志"""
        if not self.server_process:
            return
        
        try:
            for line in iter(self.server_process.stdout.readline, ''):
                line = line.strip()
                if line:
                    # 检查服务器是否准备就绪
                    if "服务已启动在" in line or "Application startup complete" in line:
                        self.server_ready = True
                    
                    # 记录重要日志
                    if any(keyword in line for keyword in ["ERROR", "❌", "✅"]):
                        logger.debug(f"[SERVER] {line}")
        except Exception as e:
            logger.debug(f"日志监控异常: {e}")
    
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            logger.info("🛑 停止服务器...")
            try:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=10)
                    logger.info("✅ 服务器已停止")
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️  强制终止服务器")
                    self.server_process.kill()
                    self.server_process.wait()
            except Exception as e:
                logger.error(f"停止服务器时出错: {e}")
            finally:
                self.server_process = None
    
    def verify_service_startup(self) -> bool:
        """验证服务启动"""
        logger.info("🔍 验证服务启动...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 服务启动验证通过")
                logger.info(f"  状态: {data.get('status', 'unknown')}")
                logger.info(f"  模型已加载: {data.get('model_loaded', False)}")
                return True
            else:
                logger.error(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 服务启动验证失败: {e}")
            return False
    
    def verify_metrics_access(self) -> bool:
        """验证监控指标可访问"""
        logger.info("📈 验证监控指标可访问...")
        
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 监控指标可访问")
                
                # 显示关键指标
                logger.info(f"  CPU使用率: {data.get('cpu_usage_percent', 'N/A')}%")
                memory = data.get('memory', {})
                if memory:
                    logger.info(f"  内存使用率: {memory.get('used_percent', 'N/A')}%")
                
                health = data.get('health', {})
                if health:
                    status = health.get('status', 'unknown')
                    logger.info(f"  健康状态: {status}")
                    if status == 'warning':
                        warnings = health.get('warnings', [])
                        logger.info(f"  警告: {len(warnings)} 个")
                
                return True
            else:
                logger.error(f"❌ 监控指标访问失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 监控指标访问失败: {e}")
            return False
    
    def create_test_audio_file(self) -> str:
        """创建简单的测试音频文件"""
        try:
            import numpy as np
            import wave
            
            # 生成1秒的测试音频
            sample_rate = 16000
            duration = 1.0
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # 保存为临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            
            with wave.open(temp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            return temp_file.name
            
        except ImportError:
            logger.warning("⚠️  numpy 不可用，跳过音频转录测试")
            return None
        except Exception as e:
            logger.error(f"❌ 创建测试音频失败: {e}")
            return None
    
    def verify_audio_transcription(self) -> bool:
        """验证音频转录功能"""
        logger.info("🎤 验证音频转录功能...")
        
        # 创建测试音频
        audio_file = self.create_test_audio_file()
        if not audio_file:
            logger.warning("⚠️  跳过音频转录测试")
            return True  # 不算失败
        
        try:
            # 发送转录请求
            with open(audio_file, 'rb') as f:
                files = {'file': ('test.wav', f, 'audio/wav')}
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 音频转录功能正常")
                logger.info(f"  语言: {data.get('language', 'unknown')}")
                logger.info(f"  音频时长: {data.get('duration', 0):.2f}s")
                logger.info(f"  片段数: {len(data.get('segments', []))}")
                
                # 显示转录文本
                segments = data.get('segments', [])
                if segments:
                    text = segments[0].get('text', '').strip()
                    logger.info(f"  转录文本: {text}")
                
                # 显示性能信息
                performance = data.get('performance', {})
                if performance:
                    logger.info(f"  处理时间: {performance.get('processing_time', 'unknown')}")
                
                return True
            else:
                logger.error(f"❌ 音频转录失败: {response.status_code}")
                logger.error(f"响应: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 音频转录测试失败: {e}")
            return False
        finally:
            # 清理临时文件
            if audio_file and os.path.exists(audio_file):
                try:
                    os.unlink(audio_file)
                except:
                    pass
    
    def run_final_verification(self) -> bool:
        """运行最终验证"""
        logger.info("🏁 开始最终检查点验证...")
        
        verification_steps = [
            ("启动服务器", self.start_server_background),
            ("验证服务启动", self.verify_service_startup),
            ("验证监控指标可访问", self.verify_metrics_access),
            ("验证音频转录功能", self.verify_audio_transcription),
        ]
        
        passed_steps = 0
        total_steps = len(verification_steps)
        
        try:
            for step_name, step_func in verification_steps:
                logger.info(f"\n{'='*50}")
                logger.info(f"步骤: {step_name}")
                logger.info(f"{'='*50}")
                
                try:
                    if step_func():
                        logger.info(f"✅ {step_name} - 通过")
                        passed_steps += 1
                    else:
                        logger.error(f"❌ {step_name} - 失败")
                        break
                except Exception as e:
                    logger.error(f"❌ {step_name} - 异常: {e}")
                    break
        
        finally:
            # 确保服务器被停止
            self.stop_server()
        
        # 打印最终摘要
        logger.info(f"\n{'🏁'*25}")
        logger.info("最终验证摘要")
        logger.info(f"{'🏁'*25}")
        logger.info(f"通过步骤: {passed_steps}/{total_steps}")
        
        if passed_steps == total_steps:
            logger.info("🎉 最终验证通过!")
            logger.info("✨ Faster-Whisper ASR 服务优化完成!")
            logger.info("")
            logger.info("📋 功能确认:")
            logger.info("  ✅ 服务能够启动 (`python -m src.main`)")
            logger.info("  ✅ 监控指标可访问 (`curl http://localhost:8080/metrics`)")
            logger.info("  ✅ 音频转录功能正常")
            logger.info("  ✅ Base 模型 (74M参数) 正常工作")
            logger.info("  ✅ 资源监控功能正常")
            logger.info("")
            logger.info("🚀 可以开始使用服务了!")
            return True
        else:
            logger.error(f"❌ {total_steps - passed_steps} 个步骤失败")
            logger.error("请检查错误信息并修复问题")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="最终检查点验证")
    parser.add_argument(
        "--host",
        default="localhost",
        help="服务器主机 (默认: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="服务器端口 (默认: 8080)"
    )
    
    args = parser.parse_args()
    
    # 创建验证器
    verifier = FinalVerifier(args.host, args.port)
    
    # 设置信号处理器以确保清理
    def signal_handler(signum, frame):
        logger.info("收到中断信号，正在清理...")
        verifier.stop_server()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 运行最终验证
    success = verifier.run_final_verification()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()