"""
配置管理模块
实现环境变量配置支持，配置验证和优先级管理
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

# 尝试导入 python-dotenv，如果不存在则跳过
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# 配置日志
logger = logging.getLogger(__name__)

# 模型配置映射 (从 asr.py 复制以避免循环导入)
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

@dataclass
class ServiceConfig:
    """服务配置数据类"""
    # 模型配置
    model_size: str = "base"
    model_path: str = "./models"
    
    # 设备配置
    device: str = "auto"
    compute_type: str = "auto"
    
    # 服务配置
    port: int = 8080
    host: str = "0.0.0.0"
    log_level: str = "INFO"
    
    # 高级配置
    max_file_size_mb: int = 100
    request_timeout_seconds: int = 300
    enable_cors: bool = True
    
    # 性能配置
    beam_size: int = 5
    language: Optional[str] = None
    task: str = "transcribe"
    
    # 监控配置
    enable_metrics: bool = True
    metrics_interval_seconds: int = 60
    
    # 路径配置
    root_path: str = ""
    static_dir: str = "./static"
    
    # 验证状态
    _validated: bool = field(default=False, init=False)

class ConfigManager:
    """配置管理器，处理环境变量和默认值的优先级管理"""
    
    # 环境变量映射
    ENV_MAPPING = {
        # 模型配置
        "MODEL_SIZE": ("model_size", str),
        "MODEL_PATH": ("model_path", str),
        
        # 设备配置
        "DEVICE": ("device", str),
        "COMPUTE_TYPE": ("compute_type", str),
        
        # 服务配置
        "PORT": ("port", int),
        "HOST": ("host", str),
        "LOG_LEVEL": ("log_level", str),
        
        # 高级配置
        "MAX_FILE_SIZE_MB": ("max_file_size_mb", int),
        "REQUEST_TIMEOUT_SECONDS": ("request_timeout_seconds", int),
        "ENABLE_CORS": ("enable_cors", bool),
        
        # 性能配置
        "BEAM_SIZE": ("beam_size", int),
        "LANGUAGE": ("language", str),
        "TASK": ("task", str),
        
        # 监控配置
        "ENABLE_METRICS": ("enable_metrics", bool),
        "METRICS_INTERVAL_SECONDS": ("metrics_interval_seconds", int),
        
        # 路径配置
        "ROOT_PATH": ("root_path", str),
        "STATIC_DIR": ("static_dir", str),
    }
    
    # 有效值定义
    VALID_VALUES = {
        "model_size": list(MODEL_CONFIGS.keys()),
        "device": ["auto", "cuda", "cpu"],
        "compute_type": ["auto", "float16", "int8"],
        "log_level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "task": ["transcribe", "translate"],
    }
    
    def __init__(self):
        # 尝试加载 .env 文件
        self._load_dotenv()
        self.config = ServiceConfig()
        self._load_from_environment()
    
    def _load_dotenv(self) -> None:
        """加载 .env 文件"""
        if DOTENV_AVAILABLE:
            # 查找 .env 文件
            env_files = ['.env', '../.env', '../../.env']
            for env_file in env_files:
                if os.path.exists(env_file):
                    load_dotenv(env_file)
                    logger.info(f"✅ 已加载环境文件: {env_file}")
                    return
            logger.info("ℹ️  未找到 .env 文件")
        else:
            logger.info("ℹ️  python-dotenv 未安装，跳过 .env 文件加载")
    
    def _convert_value(self, value: str, target_type: type) -> Any:
        """转换环境变量值到目标类型"""
        if target_type == bool:
            return value.lower() in ("true", "1", "yes", "on")
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        else:
            return value
    
    def _load_from_environment(self) -> None:
        """从环境变量加载配置"""
        logger.info("🔧 从环境变量加载配置...")
        
        loaded_configs = []
        
        for env_var, (attr_name, target_type) in self.ENV_MAPPING.items():
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                try:
                    # 处理 None 值的特殊情况
                    if env_value.lower() in ("none", "null", ""):
                        converted_value = None
                    else:
                        converted_value = self._convert_value(env_value, target_type)
                    
                    setattr(self.config, attr_name, converted_value)
                    loaded_configs.append(f"{env_var}={env_value}")
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️  无效的环境变量值 {env_var}={env_value}: {e}")
        
        if loaded_configs:
            logger.info(f"✅ 已加载 {len(loaded_configs)} 个环境变量配置")
            for config in loaded_configs:
                logger.debug(f"   {config}")
        else:
            logger.info("ℹ️  未找到环境变量配置，使用默认值")
    
    def validate_config(self) -> bool:
        """验证配置的有效性"""
        logger.info("🔍 验证配置参数...")
        
        errors = []
        warnings = []
        
        # 验证模型大小
        if self.config.model_size not in self.VALID_VALUES["model_size"]:
            errors.append(f"无效的模型大小: {self.config.model_size}")
        
        # 验证设备配置
        if self.config.device not in self.VALID_VALUES["device"]:
            errors.append(f"无效的设备配置: {self.config.device}")
        
        # 验证计算类型
        if self.config.compute_type not in self.VALID_VALUES["compute_type"]:
            errors.append(f"无效的计算类型: {self.config.compute_type}")
        
        # 验证端口
        if not (1 <= self.config.port <= 65535):
            errors.append(f"无效的端口号: {self.config.port}")
        
        # 验证日志级别
        if self.config.log_level not in self.VALID_VALUES["log_level"]:
            errors.append(f"无效的日志级别: {self.config.log_level}")
        
        # 验证任务类型
        if self.config.task not in self.VALID_VALUES["task"]:
            errors.append(f"无效的任务类型: {self.config.task}")
        
        # 验证数值范围
        if self.config.max_file_size_mb <= 0:
            errors.append(f"文件大小限制必须大于0: {self.config.max_file_size_mb}")
        
        if self.config.request_timeout_seconds <= 0:
            errors.append(f"请求超时时间必须大于0: {self.config.request_timeout_seconds}")
        
        if self.config.beam_size <= 0:
            errors.append(f"束搜索大小必须大于0: {self.config.beam_size}")
        
        if self.config.metrics_interval_seconds <= 0:
            errors.append(f"监控间隔必须大于0: {self.config.metrics_interval_seconds}")
        
        # 验证路径
        if not os.path.isabs(self.config.model_path) and not self.config.model_path.startswith("./"):
            warnings.append(f"建议使用绝对路径或相对路径: {self.config.model_path}")
        
        # 兼容性检查
        if self.config.device == "cpu" and self.config.compute_type == "float16":
            warnings.append("CPU 不支持 float16，将自动切换到 int8")
        
        # 记录验证结果
        if errors:
            logger.error("❌ 配置验证失败:")
            for error in errors:
                logger.error(f"   - {error}")
            return False
        
        if warnings:
            logger.warning("⚠️  配置警告:")
            for warning in warnings:
                logger.warning(f"   - {warning}")
        
        logger.info("✅ 配置验证通过")
        self.config._validated = True
        return True
    
    def get_config(self) -> ServiceConfig:
        """获取配置对象"""
        if not self.config._validated:
            if not self.validate_config():
                raise ValueError("配置验证失败")
        return self.config
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        config = self.get_config()
        return {
            "model": {
                "size": config.model_size,
                "path": config.model_path,
                "device": config.device,
                "compute_type": config.compute_type,
            },
            "service": {
                "port": config.port,
                "host": config.host,
                "log_level": config.log_level,
                "root_path": config.root_path,
                "static_dir": config.static_dir,
            },
            "performance": {
                "max_file_size_mb": config.max_file_size_mb,
                "request_timeout_seconds": config.request_timeout_seconds,
                "beam_size": config.beam_size,
                "language": config.language,
                "task": config.task,
            },
            "features": {
                "enable_cors": config.enable_cors,
                "enable_metrics": config.enable_metrics,
                "metrics_interval_seconds": config.metrics_interval_seconds,
            }
        }
    
    def print_config_summary(self) -> None:
        """打印配置摘要"""
        config = self.get_config()
        model_config = MODEL_CONFIGS[config.model_size]
        
        print("\n" + "📋" * 25 + " 配置摘要 " + "📋" * 25)
        print(f"🎯 模型配置:")
        print(f"   大小: {config.model_size} ({model_config['parameters']})")
        print(f"   描述: {model_config['description']}")
        print(f"   路径: {config.model_path}")
        print(f"   设备: {config.device}")
        print(f"   计算类型: {config.compute_type}")
        
        print(f"\n🌐 服务配置:")
        print(f"   地址: {config.host}:{config.port}")
        print(f"   日志级别: {config.log_level}")
        print(f"   根路径: {config.root_path or '/'}")
        print(f"   静态目录: {config.static_dir}")
        
        print(f"\n⚡ 性能配置:")
        print(f"   最大文件大小: {config.max_file_size_mb}MB")
        print(f"   请求超时: {config.request_timeout_seconds}s")
        print(f"   束搜索大小: {config.beam_size}")
        print(f"   默认语言: {config.language or '自动检测'}")
        print(f"   默认任务: {config.task}")
        
        print(f"\n🔧 功能配置:")
        print(f"   CORS: {'启用' if config.enable_cors else '禁用'}")
        print(f"   监控: {'启用' if config.enable_metrics else '禁用'}")
        if config.enable_metrics:
            print(f"   监控间隔: {config.metrics_interval_seconds}s")
        
        print("📋" * 60 + "\n")
    
    def get_environment_template(self) -> str:
        """获取环境变量模板"""
        template = """# Faster-Whisper ASR Service 环境变量配置模板
# 复制此文件为 .env 并根据需要修改配置

# 模型配置
MODEL_SIZE=base                    # 模型大小: tiny, base, small, medium, large
MODEL_PATH=./models               # 模型文件路径
DEVICE=auto                       # 设备: auto, cuda, cpu
COMPUTE_TYPE=auto                 # 计算类型: auto, float16, int8

# 服务配置
PORT=8080                         # 服务端口
HOST=0.0.0.0                     # 服务地址
LOG_LEVEL=INFO                   # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
ROOT_PATH=                       # 根路径 (用于反向代理)
STATIC_DIR=./static              # 静态文件目录

# 性能配置
MAX_FILE_SIZE_MB=100             # 最大文件大小 (MB)
REQUEST_TIMEOUT_SECONDS=300      # 请求超时时间 (秒)
BEAM_SIZE=5                      # 束搜索大小
LANGUAGE=                        # 默认语言 (留空自动检测)
TASK=transcribe                  # 默认任务: transcribe, translate

# 功能配置
ENABLE_CORS=true                 # 启用 CORS
ENABLE_METRICS=true              # 启用监控
METRICS_INTERVAL_SECONDS=60      # 监控间隔 (秒)
"""
        return template


# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> ServiceConfig:
    """获取服务配置"""
    return get_config_manager().get_config()


if __name__ == "__main__":
    # 测试配置管理器
    config_manager = ConfigManager()
    
    print("=== 配置验证 ===")
    is_valid = config_manager.validate_config()
    print(f"配置有效: {is_valid}")
    
    if is_valid:
        print("\n=== 配置摘要 ===")
        config_manager.print_config_summary()
        
        print("\n=== 配置字典 ===")
        config_dict = config_manager.get_config_dict()
        import json
        print(json.dumps(config_dict, indent=2, ensure_ascii=False))
    
    print("\n=== 环境变量模板 ===")
    template = config_manager.get_environment_template()
    print(template)