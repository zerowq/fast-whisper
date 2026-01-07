"""
资源监控模块
实现 GPU/CPU/内存监控，提供资源使用指标 API
"""

import os
import time
import psutil
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    """资源指标数据类"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    gpu_available: bool
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    gpu_memory_percent: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None
    disk_usage_percent: float = 0.0
    process_count: int = 0

class ResourceMonitor:
    """资源监控器，提供实时的系统资源监控"""
    
    def __init__(self):
        """初始化资源监控器"""
        self.gpu_available = self._check_gpu_availability()
        self.start_time = time.time()
        
        if self.gpu_available:
            logger.info("✅ GPU 监控已启用")
        else:
            logger.info("ℹ️  GPU 不可用，仅监控 CPU/内存")
    
    def _check_gpu_availability(self) -> bool:
        """检查 GPU 是否可用"""
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            return device_count > 0
        except (ImportError, Exception) as e:
            logger.debug(f"GPU 不可用: {e}")
            return False
    
    def _get_gpu_metrics(self) -> Dict[str, Optional[float]]:
        """获取 GPU 指标"""
        if not self.gpu_available:
            return {
                "gpu_memory_used_mb": None,
                "gpu_memory_total_mb": None,
                "gpu_memory_percent": None,
                "gpu_utilization_percent": None
            }
        
        try:
            import pynvml
            
            # 获取第一个 GPU 的信息
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            # 内存信息
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_used_mb = memory_info.used / (1024 * 1024)
            memory_total_mb = memory_info.total / (1024 * 1024)
            memory_percent = (memory_info.used / memory_info.total) * 100
            
            # GPU 利用率
            try:
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_utilization = utilization.gpu
            except Exception:
                gpu_utilization = None
            
            return {
                "gpu_memory_used_mb": round(memory_used_mb, 2),
                "gpu_memory_total_mb": round(memory_total_mb, 2),
                "gpu_memory_percent": round(memory_percent, 2),
                "gpu_utilization_percent": gpu_utilization
            }
            
        except Exception as e:
            logger.warning(f"获取 GPU 指标失败: {e}")
            return {
                "gpu_memory_used_mb": None,
                "gpu_memory_total_mb": None,
                "gpu_memory_percent": None,
                "gpu_utilization_percent": None
            }
    
    def _get_cpu_metrics(self) -> Dict[str, float]:
        """获取 CPU 指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return {"cpu_percent": round(cpu_percent, 2)}
        except Exception as e:
            logger.warning(f"获取 CPU 指标失败: {e}")
            return {"cpu_percent": 0.0}
    
    def _get_memory_metrics(self) -> Dict[str, float]:
        """获取内存指标"""
        try:
            memory = psutil.virtual_memory()
            return {
                "memory_percent": round(memory.percent, 2),
                "memory_used_mb": round(memory.used / (1024 * 1024), 2),
                "memory_total_mb": round(memory.total / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.warning(f"获取内存指标失败: {e}")
            return {
                "memory_percent": 0.0,
                "memory_used_mb": 0.0,
                "memory_total_mb": 0.0
            }
    
    def _get_disk_metrics(self) -> Dict[str, float]:
        """获取磁盘使用指标"""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                "disk_usage_percent": round(disk_usage.percent, 2)
            }
        except Exception as e:
            logger.warning(f"获取磁盘指标失败: {e}")
            return {"disk_usage_percent": 0.0}
    
    def _get_process_metrics(self) -> Dict[str, int]:
        """获取进程指标"""
        try:
            process_count = len(psutil.pids())
            return {"process_count": process_count}
        except Exception as e:
            logger.warning(f"获取进程指标失败: {e}")
            return {"process_count": 0}
    
    def get_metrics(self) -> ResourceMetrics:
        """
        获取当前系统资源指标
        
        Returns:
            ResourceMetrics: 包含所有资源指标的数据类
        """
        timestamp = time.time()
        
        # 收集各类指标
        cpu_metrics = self._get_cpu_metrics()
        memory_metrics = self._get_memory_metrics()
        gpu_metrics = self._get_gpu_metrics()
        disk_metrics = self._get_disk_metrics()
        process_metrics = self._get_process_metrics()
        
        # 构建资源指标对象
        metrics = ResourceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_metrics["cpu_percent"],
            memory_percent=memory_metrics["memory_percent"],
            memory_used_mb=memory_metrics["memory_used_mb"],
            memory_total_mb=memory_metrics["memory_total_mb"],
            gpu_available=self.gpu_available,
            gpu_memory_used_mb=gpu_metrics["gpu_memory_used_mb"],
            gpu_memory_total_mb=gpu_metrics["gpu_memory_total_mb"],
            gpu_memory_percent=gpu_metrics["gpu_memory_percent"],
            gpu_utilization_percent=gpu_metrics["gpu_utilization_percent"],
            disk_usage_percent=disk_metrics["disk_usage_percent"],
            process_count=process_metrics["process_count"]
        )
        
        return metrics
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        获取资源指标的字典格式
        
        Returns:
            Dict[str, Any]: 资源指标字典
        """
        metrics = self.get_metrics()
        return asdict(metrics)
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统基本信息
        
        Returns:
            Dict[str, Any]: 系统信息
        """
        try:
            uptime = time.time() - self.start_time
            
            system_info = {
                "platform": os.name,
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "uptime_seconds": round(uptime, 2),
                "gpu_available": self.gpu_available,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
            
            # 添加 GPU 信息
            if self.gpu_available:
                try:
                    import pynvml
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    system_info["gpu_name"] = gpu_name
                except Exception:
                    system_info["gpu_name"] = "Unknown"
            
            return system_info
            
        except Exception as e:
            logger.warning(f"获取系统信息失败: {e}")
            return {
                "platform": "unknown",
                "cpu_count": 0,
                "cpu_count_logical": 0,
                "uptime_seconds": 0.0,
                "gpu_available": False,
                "python_version": "unknown"
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        metrics = self.get_metrics()
        
        # 定义健康阈值
        cpu_warning_threshold = 80.0
        memory_warning_threshold = 85.0
        gpu_memory_warning_threshold = 90.0
        disk_warning_threshold = 90.0
        
        warnings = []
        status = "healthy"
        
        # 检查 CPU 使用率
        if metrics.cpu_percent > cpu_warning_threshold:
            warnings.append(f"CPU 使用率过高: {metrics.cpu_percent}%")
            status = "warning"
        
        # 检查内存使用率
        if metrics.memory_percent > memory_warning_threshold:
            warnings.append(f"内存使用率过高: {metrics.memory_percent}%")
            status = "warning"
        
        # 检查 GPU 内存使用率
        if (metrics.gpu_available and 
            metrics.gpu_memory_percent is not None and 
            metrics.gpu_memory_percent > gpu_memory_warning_threshold):
            warnings.append(f"GPU 内存使用率过高: {metrics.gpu_memory_percent}%")
            status = "warning"
        
        # 检查磁盘使用率
        if metrics.disk_usage_percent > disk_warning_threshold:
            warnings.append(f"磁盘使用率过高: {metrics.disk_usage_percent}%")
            status = "warning"
        
        return {
            "status": status,
            "timestamp": metrics.timestamp,
            "warnings": warnings,
            "metrics_summary": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "gpu_memory_percent": metrics.gpu_memory_percent,
                "disk_usage_percent": metrics.disk_usage_percent
            }
        }
    
    def log_metrics(self) -> None:
        """记录当前资源指标到日志"""
        metrics = self.get_metrics()
        
        log_message = (
            f"资源监控 - "
            f"CPU: {metrics.cpu_percent}%, "
            f"内存: {metrics.memory_percent}% ({metrics.memory_used_mb:.0f}MB/{metrics.memory_total_mb:.0f}MB)"
        )
        
        if metrics.gpu_available and metrics.gpu_memory_percent is not None:
            log_message += f", GPU内存: {metrics.gpu_memory_percent}% ({metrics.gpu_memory_used_mb:.0f}MB/{metrics.gpu_memory_total_mb:.0f}MB)"
            if metrics.gpu_utilization_percent is not None:
                log_message += f", GPU利用率: {metrics.gpu_utilization_percent}%"
        
        logger.info(log_message)


# 全局资源监控器实例
_resource_monitor = None

def get_resource_monitor() -> ResourceMonitor:
    """获取全局资源监控器实例"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor


if __name__ == "__main__":
    # 测试资源监控器
    monitor = ResourceMonitor()
    
    print("=== 系统信息 ===")
    system_info = monitor.get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")
    
    print("\n=== 当前资源指标 ===")
    metrics = monitor.get_metrics_dict()
    for key, value in metrics.items():
        if value is not None:
            print(f"{key}: {value}")
    
    print("\n=== 健康状态 ===")
    health = monitor.get_health_status()
    print(f"状态: {health['status']}")
    if health['warnings']:
        print("警告:")
        for warning in health['warnings']:
            print(f"  - {warning}")
    
    print("\n=== 日志记录 ===")
    monitor.log_metrics()