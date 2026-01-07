#!/usr/bin/env python3
"""
基本模型功能验证脚本
确认 Base 模型能正常加载和转录，简单测试一个音频文件的转录功能
"""

import os
import sys
import logging
import tempfile
import time
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.asr import ASRService, MODEL_CONFIGS
from core.resource_monitor import get_resource_monitor
from core.config import get_config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelVerifier:
    """模型功能验证器"""
    
    def __init__(self, model_size: str = "base", model_path: str = "./models"):
        self.model_size = model_size
        self.model_path = model_path
        self.asr_service = None
        self.resource_monitor = get_resource_monitor()
    
    def verify_model_files(self) -> bool:
        """验证模型文件是否存在"""
        logger.info("🔍 验证模型文件...")
        
        if not os.path.exists(self.model_path):
            logger.error(f"❌ 模型目录不存在: {self.model_path}")
            return False
        
        # Faster-Whisper 使用 HuggingFace 格式，关键文件包括
        # config.json, tokenizer.json, model.bin (或 .safetensors)
        required_files = ["config.json", "tokenizer.json"]
        optional_files = ["model.bin", "model.safetensors", "vocabulary.json"]
        missing_required = []
        has_model = False
        
        for file in required_files:
            file_path = os.path.join(self.model_path, file)
            if not os.path.exists(file_path):
                missing_required.append(file)
        
        for file in optional_files:
            file_path = os.path.join(self.model_path, file)
            if os.path.exists(file_path):
                has_model = True
                break
        
        if missing_required or not has_model:
            if missing_required:
                logger.error(f"❌ 缺少必需的模型文件: {missing_required}")
            if not has_model:
                logger.error(f"❌ 缺少模型权重文件 (model.bin 或 model.safetensors)")
            logger.info("请运行: uv run python scripts/download_models.py --model-size base")
            logger.info("或: python scripts/download_models.py --model-size base")
            return False
        
        logger.info("✅ 模型文件验证通过")
        return True
    
    def verify_model_loading(self) -> bool:
        """验证模型加载"""
        logger.info("🔧 验证模型加载...")
        
        try:
            # 创建 ASR 服务实例
            self.asr_service = ASRService(
                model_size=self.model_size,
                model_path=self.model_path,
                device="auto",
                compute_type="auto"
            )
            
            # 记录初始资源状态
            initial_metrics = self.resource_monitor.get_metrics()
            logger.info(f"初始内存使用: {initial_metrics.memory_percent:.1f}%")
            if initial_metrics.gpu_available:
                logger.info(f"初始GPU内存使用: {initial_metrics.gpu_memory_percent:.1f}%")
            
            # 加载模型
            start_time = time.time()
            success = self.asr_service.load_model()
            load_time = time.time() - start_time
            
            if not success:
                logger.error("❌ 模型加载失败")
                return False
            
            # 记录加载后资源状态
            loaded_metrics = self.resource_monitor.get_metrics()
            memory_increase = loaded_metrics.memory_percent - initial_metrics.memory_percent
            
            logger.info(f"✅ 模型加载成功 (耗时: {load_time:.2f}s)")
            logger.info(f"内存增加: {memory_increase:.1f}%")
            
            if loaded_metrics.gpu_available and initial_metrics.gpu_memory_percent is not None:
                gpu_memory_increase = loaded_metrics.gpu_memory_percent - initial_metrics.gpu_memory_percent
                logger.info(f"GPU内存增加: {gpu_memory_increase:.1f}%")
            
            # 获取模型信息
            model_info = self.asr_service.get_model_info()
            logger.info(f"模型信息:")
            logger.info(f"  大小: {model_info['model_size']} ({model_info['parameters']})")
            logger.info(f"  设备: {model_info['device']}")
            logger.info(f"  计算类型: {model_info['compute_type']}")
            logger.info(f"  状态: {'已加载' if model_info['loaded'] else '未加载'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型加载验证失败: {e}")
            return False
    
    def create_test_audio(self) -> str:
        """创建测试音频文件 (使用合成音频)"""
        logger.info("🎵 创建测试音频文件...")
        
        try:
            import numpy as np
            import wave
            
            # 生成简单的测试音频 (1秒，16kHz，单声道)
            sample_rate = 16000
            duration = 1.0
            frequency = 440  # A4 音符
            
            # 生成正弦波
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t)
            
            # 添加一些变化使其更像语音
            audio_data = audio_data * np.exp(-t * 2)  # 衰减
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # 保存为临时 WAV 文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            
            with wave.open(temp_file.name, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            logger.info(f"✅ 测试音频文件创建: {temp_file.name}")
            return temp_file.name
            
        except ImportError:
            logger.warning("⚠️  numpy 不可用，跳过音频生成测试")
            return None
        except Exception as e:
            logger.error(f"❌ 创建测试音频失败: {e}")
            return None
    
    def verify_transcription(self, audio_file: str = None) -> bool:
        """验证转录功能"""
        logger.info("🎤 验证转录功能...")
        
        if not self.asr_service:
            logger.error("❌ ASR 服务未初始化")
            return False
        
        # 如果没有提供音频文件，创建测试音频
        if not audio_file:
            audio_file = self.create_test_audio()
            if not audio_file:
                logger.warning("⚠️  无法创建测试音频，跳过转录测试")
                return True  # 不算失败，只是跳过
        
        try:
            # 记录转录前资源状态
            pre_metrics = self.resource_monitor.get_metrics()
            
            # 执行转录
            logger.info(f"开始转录音频文件: {audio_file}")
            start_time = time.time()
            
            result = self.asr_service.transcribe(
                audio_file,
                language=None,  # 自动检测
                beam_size=5,
                task="transcribe"
            )
            
            transcription_time = time.time() - start_time
            
            # 记录转录后资源状态
            post_metrics = self.resource_monitor.get_metrics()
            
            logger.info(f"✅ 转录完成 (耗时: {transcription_time:.2f}s)")
            logger.info(f"转录结果:")
            logger.info(f"  语言: {result.get('language', 'unknown')}")
            logger.info(f"  语言置信度: {result.get('language_probability', 0):.2f}")
            logger.info(f"  音频时长: {result.get('duration', 0):.2f}s")
            logger.info(f"  片段数: {len(result.get('segments', []))}")
            
            # 显示转录文本
            segments = result.get('segments', [])
            if segments:
                logger.info("  转录文本:")
                for i, segment in enumerate(segments[:3]):  # 只显示前3个片段
                    text = segment.get('text', '').strip()
                    start = segment.get('start', 0)
                    end = segment.get('end', 0)
                    logger.info(f"    [{start:.1f}s-{end:.1f}s]: {text}")
                if len(segments) > 3:
                    logger.info(f"    ... (还有 {len(segments) - 3} 个片段)")
            
            # 显示性能信息
            if 'performance' in result:
                perf = result['performance']
                logger.info(f"  处理时间: {perf.get('processing_time', 'unknown')}")
            
            # 清理临时文件
            if audio_file and audio_file.startswith(tempfile.gettempdir()):
                try:
                    os.unlink(audio_file)
                    logger.debug(f"清理临时文件: {audio_file}")
                except:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 转录验证失败: {e}")
            return False
    
    def verify_resource_monitoring(self) -> bool:
        """验证资源监控功能"""
        logger.info("📊 验证资源监控功能...")
        
        try:
            # 获取系统信息
            system_info = self.resource_monitor.get_system_info()
            logger.info("系统信息:")
            logger.info(f"  平台: {system_info['platform']}")
            logger.info(f"  CPU核心: {system_info['cpu_count']}")
            logger.info(f"  逻辑CPU: {system_info['cpu_count_logical']}")
            logger.info(f"  运行时间: {system_info['uptime_seconds']:.1f}s")
            logger.info(f"  GPU可用: {system_info['gpu_available']}")
            
            if system_info['gpu_available']:
                logger.info(f"  GPU名称: {system_info.get('gpu_name', 'Unknown')}")
            
            # 获取当前指标
            metrics = self.resource_monitor.get_metrics()
            logger.info("当前资源指标:")
            logger.info(f"  CPU使用率: {metrics.cpu_percent}%")
            logger.info(f"  内存使用率: {metrics.memory_percent}%")
            logger.info(f"  内存使用: {metrics.memory_used_mb:.0f}MB / {metrics.memory_total_mb:.0f}MB")
            
            if metrics.gpu_available:
                logger.info(f"  GPU内存使用率: {metrics.gpu_memory_percent}%")
                logger.info(f"  GPU内存使用: {metrics.gpu_memory_used_mb:.0f}MB / {metrics.gpu_memory_total_mb:.0f}MB")
                if metrics.gpu_utilization_percent is not None:
                    logger.info(f"  GPU利用率: {metrics.gpu_utilization_percent}%")
            
            # 获取健康状态
            health = self.resource_monitor.get_health_status()
            logger.info(f"健康状态: {health['status']}")
            if health['warnings']:
                logger.warning("健康警告:")
                for warning in health['warnings']:
                    logger.warning(f"  - {warning}")
            
            logger.info("✅ 资源监控功能验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 资源监控验证失败: {e}")
            return False
    
    def run_verification(self, audio_file: str = None) -> bool:
        """运行完整的验证流程"""
        logger.info("🚀 开始基本模型功能验证...")
        
        verification_steps = [
            ("模型文件验证", self.verify_model_files),
            ("模型加载验证", self.verify_model_loading),
            ("资源监控验证", self.verify_resource_monitoring),
            ("转录功能验证", lambda: self.verify_transcription(audio_file)),
        ]
        
        passed_steps = 0
        total_steps = len(verification_steps)
        
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
            except Exception as e:
                logger.error(f"❌ {step_name} - 异常: {e}")
        
        # 打印验证摘要
        logger.info(f"\n{'='*50}")
        logger.info("验证摘要")
        logger.info(f"{'='*50}")
        logger.info(f"通过步骤: {passed_steps}/{total_steps}")
        
        if passed_steps == total_steps:
            logger.info("🎉 所有验证步骤通过!")
            return True
        else:
            logger.error(f"❌ {total_steps - passed_steps} 个步骤失败")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="基本模型功能验证")
    parser.add_argument(
        "--model-size",
        default="base",
        choices=list(MODEL_CONFIGS.keys()),
        help="模型大小 (默认: base)"
    )
    parser.add_argument(
        "--model-path",
        default="./models",
        help="模型文件路径 (默认: ./models)"
    )
    parser.add_argument(
        "--audio-file",
        help="测试音频文件路径 (可选，不提供则生成测试音频)"
    )
    
    args = parser.parse_args()
    
    # 创建验证器
    verifier = ModelVerifier(args.model_size, args.model_path)
    
    # 运行验证
    success = verifier.run_verification(args.audio_file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()