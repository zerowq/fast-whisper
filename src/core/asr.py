import os
import logging
from typing import Optional, Dict, Any
from faster_whisper import WhisperModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模型配置映射
MODEL_CONFIGS = {
    "tiny": {
        "repo_id": "Systran/faster-whisper-tiny",
        "size_mb": 40,
        "parameters": "39M",
        "description": "最小模型，速度最快但准确率较低"
    },
    "base": {
        "repo_id": "Systran/faster-whisper-base", 
        "size_mb": 75,
        "parameters": "74M",
        "description": "平衡模型，推荐选择，性能和质量的最佳平衡"
    },
    "small": {
        "repo_id": "Systran/faster-whisper-small",
        "size_mb": 245,
        "parameters": "244M", 
        "description": "小型模型，较好的准确率"
    },
    "medium": {
        "repo_id": "Systran/faster-whisper-medium",
        "size_mb": 775,
        "parameters": "769M",
        "description": "中型模型，高准确率"
    },
    "large": {
        "repo_id": "Systran/faster-whisper-large-v3",
        "size_mb": 1500,
        "parameters": "1.55B",
        "description": "大型模型，最高准确率但速度较慢"
    }
}

class ASRService:
    """优化的 ASR 服务，支持轻量化配置和动态模型切换"""
    
    def __init__(self, 
                 model_size: str = "base",
                 model_path: str = "./models", 
                 device: str = "auto", 
                 compute_type: str = "auto"):
        """
        初始化 ASR 服务
        
        Args:
            model_size: 模型大小 (默认: "base" - 74M参数，平衡性能和质量)
            model_path: 模型文件路径
            device: 设备选择 ("auto", "cuda", "cpu")
            compute_type: 计算类型 ("auto", "float16", "int8")
        """
        self.model_size = model_size
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self.current_device = None
        self.current_compute_type = None
        
        # 验证模型大小
        if model_size not in MODEL_CONFIGS:
            raise ValueError(f"不支持的模型大小: {model_size}. 支持的大小: {list(MODEL_CONFIGS.keys())}")
        
        logger.info(f"初始化 ASR 服务 - 模型: {model_size} ({MODEL_CONFIGS[model_size]['parameters']})")
    
    def _determine_optimal_config(self) -> tuple[str, str]:
        """确定最优的设备和计算类型配置"""
        device = self.device
        compute_type = self.compute_type
        
        # 自动设备选择
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    logger.info("检测到 CUDA，使用 GPU 加速")
                else:
                    device = "cpu"
                    logger.info("未检测到 CUDA，使用 CPU")
            except ImportError:
                device = "cpu"
                logger.info("PyTorch 未安装，使用 CPU")
        
        # 自动计算类型选择
        if compute_type == "auto":
            if device == "cuda":
                compute_type = "float16"  # GPU 使用 float16
            else:
                compute_type = "int8"     # CPU 使用 int8
        
        # CPU 不支持 float16，强制使用 int8
        if device == "cpu" and compute_type == "float16":
            compute_type = "int8"
            logger.info("CPU 不支持 float16，自动切换到 int8")
        
        return device, compute_type
    
    def _check_model_exists(self) -> bool:
        """检查模型文件是否存在"""
        if not os.path.exists(self.model_path):
            return False
        
        # 检查必要的模型文件
        required_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
        for file in required_files:
            file_path = os.path.join(self.model_path, file)
            if not os.path.exists(file_path):
                return False
        
        return True
    
    def _provide_download_guidance(self) -> None:
        """提供模型下载指引"""
        logger.error(f"模型文件未找到: {self.model_path}")
        print("\n" + "="*60)
        print("🚨 模型文件未找到！请先下载模型:")
        print(f"   python scripts/download_models.py --size {self.model_size}")
        print("\n或者下载默认的 base 模型:")
        print("   python scripts/download_models.py")
        print("\n查看所有可用模型:")
        print("   python scripts/download_models.py --list")
        print("="*60)
    
    def load_model(self) -> bool:
        """
        加载模型，支持自动降级
        
        Returns:
            bool: 加载是否成功
        """
        # 检查模型文件是否存在
        if not self._check_model_exists():
            self._provide_download_guidance()
            raise FileNotFoundError(f"模型文件未找到: {self.model_path}")
        
        # 确定最优配置
        device, compute_type = self._determine_optimal_config()
        
        logger.info(f"尝试加载模型 - 设备: {device}, 计算类型: {compute_type}")
        
        try:
            # 尝试加载模型
            self.model = WhisperModel(
                self.model_size, 
                device=device, 
                compute_type=compute_type,
                local_files_only=True
            )
            
            self.current_device = device
            self.current_compute_type = compute_type
            
            logger.info(f"✅ 模型加载成功 - {self.model_size} 模型在 {device} 设备上运行")
            return True
            
        except Exception as e:
            logger.warning(f"模型加载失败 ({device}/{compute_type}): {e}")
            
            # 自动降级策略
            if device == "cuda":
                logger.info("尝试降级到 CPU...")
                try:
                    self.model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                        local_files_only=True
                    )
                    
                    self.current_device = "cpu"
                    self.current_compute_type = "int8"
                    
                    logger.info("✅ 模型加载成功 - 已降级到 CPU")
                    return True
                    
                except Exception as cpu_error:
                    logger.error(f"CPU 降级也失败: {cpu_error}")
                    raise cpu_error
            else:
                raise e
    
    def switch_model_size(self, new_size: str) -> bool:
        """
        动态切换模型大小
        
        Args:
            new_size: 新的模型大小
            
        Returns:
            bool: 切换是否成功
        """
        if new_size not in MODEL_CONFIGS:
            logger.error(f"不支持的模型大小: {new_size}")
            return False
        
        if new_size == self.model_size:
            logger.info(f"模型大小已经是 {new_size}，无需切换")
            return True
        
        old_size = self.model_size
        old_model_path = self.model_path
        
        # 更新模型配置
        self.model_size = new_size
        # 假设不同大小的模型在不同目录，实际可能需要调整
        # 这里保持同一目录，实际使用时可能需要根据模型大小调整路径
        
        logger.info(f"尝试从 {old_size} 切换到 {new_size} 模型...")
        
        try:
            # 卸载当前模型
            if self.model is not None:
                del self.model
                self.model = None
            
            # 加载新模型
            success = self.load_model()
            if success:
                logger.info(f"✅ 模型切换成功: {old_size} → {new_size}")
                return True
            else:
                # 回滚
                self.model_size = old_size
                self.model_path = old_model_path
                logger.error(f"模型切换失败，回滚到 {old_size}")
                return False
                
        except Exception as e:
            # 回滚
            self.model_size = old_size
            self.model_path = old_model_path
            logger.error(f"模型切换失败: {e}，回滚到 {old_size}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        config = MODEL_CONFIGS[self.model_size]
        return {
            "model_size": self.model_size,
            "parameters": config["parameters"],
            "size_mb": config["size_mb"],
            "description": config["description"],
            "device": self.current_device,
            "compute_type": self.current_compute_type,
            "loaded": self.model is not None
        }
    
    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            **kwargs: 其他转录参数
            
        Returns:
            转录结果
        """
        # 确保模型已加载
        if self.model is None:
            logger.info("模型未加载，正在加载...")
            if not self.load_model():
                raise RuntimeError("模型加载失败")
        
        # 设置默认参数
        transcribe_params = {
            "beam_size": kwargs.get("beam_size", 5),
            "language": kwargs.get("language", None),  # 自动检测语言
            "task": kwargs.get("task", "transcribe"),   # transcribe 或 translate
        }
        
        logger.info(f"开始转录音频: {audio_path}")
        
        try:
            segments, info = self.model.transcribe(audio_path, **transcribe_params)
            
            results = []
            for segment in segments:
                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
            
            result = {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": results,
                "model_info": {
                    "size": self.model_size,
                    "device": self.current_device,
                    "compute_type": self.current_compute_type
                }
            }
            
            logger.info(f"转录完成 - 语言: {info.language}, 片段数: {len(results)}")
            return result
            
        except Exception as e:
            logger.error(f"转录失败: {e}")
            raise e
