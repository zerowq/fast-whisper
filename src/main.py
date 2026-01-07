import uvicorn
from fastapi import FastAPI
from src.api import router as api_router
from src.core.asr import ASRService, MODEL_CONFIGS
from src.core.resource_monitor import get_resource_monitor
from src.core.config import get_config_manager, get_config
import os
import sys
import logging
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# 初始化配置管理器
config_manager = get_config_manager()
config = get_config()

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_configuration():
    """验证配置参数的有效性"""
    logger.info("🔍 验证配置参数...")
    
    try:
        # 配置管理器已经在初始化时进行了验证
        config_manager.validate_config()
        logger.info("✅ 配置参数验证通过")
        return True
    except ValueError as e:
        logger.error(f"❌ 配置验证失败: {e}")
        return False

def check_model_availability():
    """检查模型文件是否可用"""
    logger.info("🔍 检查模型文件...")
    
    if not os.path.exists(config.model_path):
        logger.warning(f"⚠️  模型目录不存在: {config.model_path}")
        return False
    
    # 检查必要的模型文件
    required_files = ["config.json", "model.bin", "tokenizer.json"]
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(config.model_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    # 检查词汇表文件 (可能是 vocabulary.json 或 vocabulary.txt)
    vocab_json = os.path.join(config.model_path, "vocabulary.json")
    vocab_txt = os.path.join(config.model_path, "vocabulary.txt")
    
    if not os.path.exists(vocab_json) and not os.path.exists(vocab_txt):
        missing_files.append("vocabulary.json 或 vocabulary.txt")
    elif os.path.exists(vocab_txt) and not os.path.exists(vocab_json):
        # 如果只有 vocabulary.txt，创建 vocabulary.json 的符号链接
        try:
            import shutil
            shutil.copy2(vocab_txt, vocab_json)
            logger.info("✅ 已创建 vocabulary.json 从 vocabulary.txt")
        except Exception as e:
            logger.warning(f"⚠️  无法创建 vocabulary.json: {e}")
    
    if missing_files:
        logger.warning(f"⚠️  缺少模型文件: {missing_files}")
        return False
    
    logger.info("✅ 模型文件检查通过")
    return True

def print_model_download_guidance():
    """打印模型下载指引"""
    model_config = MODEL_CONFIGS[config.model_size]
    
    print("\n" + "="*70)
    print("🚨 模型文件未找到！")
    print(f"   当前配置的模型: {config.model_size} ({model_config['parameters']}, {model_config['size_mb']}MB)")
    print(f"   模型目录: {config.model_path}")
    print("\n📥 请先下载模型:")
    print(f"   python scripts/download_models.py --size {config.model_size}")
    print("\n或者下载默认的 base 模型:")
    print("   python scripts/download_models.py")
    print("\n查看所有可用模型:")
    print("   python scripts/download_models.py --list")
    print("\n💡 提示:")
    print(f"   - base 模型 (74M参数) 是推荐的平衡选择")
    print(f"   - tiny 模型 (39M参数) 适合资源受限环境")
    print(f"   - 可通过环境变量 MODEL_SIZE 切换模型大小")
    print("="*70)

def print_startup_info():
    """打印启动信息"""
    print("\n" + "🌟" * 35)
    print("  Faster-Whisper ASR Service (Optimized)")
    print("🌟" * 35)
    
    # 使用配置管理器打印详细配置
    config_manager.print_config_summary()

def initialize_resource_monitor():
    """初始化资源监控器"""
    try:
        logger.info("🔧 初始化资源监控器...")
        resource_monitor = get_resource_monitor()
        
        # 获取系统信息
        system_info = resource_monitor.get_system_info()
        logger.info(f"💻 系统信息: {system_info['platform']}, CPU: {system_info['cpu_count']}核")
        
        if system_info['gpu_available']:
            logger.info(f"🎮 GPU 可用: {system_info.get('gpu_name', 'Unknown')}")
        else:
            logger.info("💻 仅 CPU 模式")
        
        # 记录初始资源状态
        resource_monitor.log_metrics()
        
        return True
    except Exception as e:
        logger.warning(f"⚠️  资源监控器初始化失败: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("🚀 启动 Faster-Whisper ASR 服务...")
    
    # 打印启动信息
    print_startup_info()
    
    # 验证配置
    if not validate_configuration():
        logger.error("❌ 配置验证失败，服务无法启动")
        sys.exit(1)
    
    # 初始化资源监控器
    initialize_resource_monitor()
    
    # 检查模型可用性
    model_available = check_model_availability()
    
    from src.api import router
    
    try:
        # 创建 ASR 服务实例
        logger.info("🔧 初始化 ASR 服务...")
        router.asr_service = ASRService(
            model_size=config.model_size,
            model_path=config.model_path,
            device=config.device,
            compute_type=config.compute_type
        )
        
        # 尝试预加载模型
        if model_available:
            logger.info("📥 正在加载模型...")
            success = router.asr_service.load_model()
            
            if success:
                model_info = router.asr_service.get_model_info()
                logger.info("✅ 服务启动成功!")
                logger.info(f"   模型: {model_info['model_size']} ({model_info['parameters']})")
                logger.info(f"   设备: {model_info['device']}")
                logger.info(f"   计算类型: {model_info['compute_type']}")
                logger.info(f"   状态: {'已加载' if model_info['loaded'] else '未加载'}")
            else:
                logger.error("❌ 模型加载失败")
                print_model_download_guidance()
        else:
            logger.warning("⚠️  模型文件不可用，服务将在首次请求时尝试加载")
            print_model_download_guidance()
            
    except FileNotFoundError as e:
        logger.error(f"❌ 模型文件未找到: {e}")
        print_model_download_guidance()
        logger.info("💡 服务将继续启动，但转录功能不可用直到模型下载完成")
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        logger.info("💡 服务将继续启动，但可能无法正常工作")
    
    # 最终启动确认
    logger.info(f"🌐 服务已启动在 http://{config.host}:{config.port}")
    logger.info("📖 访问 /docs 查看 API 文档")
    logger.info("❤️  访问 /health 检查服务状态")
    logger.info("📈 访问 /metrics 查看监控指标")
    
    yield
    
    # Shutdown logic
    logger.info("🛑 正在关闭 ASR 服务...")
    
    # 清理资源
    if hasattr(router, 'asr_service') and router.asr_service:
        try:
            if router.asr_service.model:
                del router.asr_service.model
                logger.info("🧹 模型资源已清理")
        except Exception as e:
            logger.warning(f"清理模型资源时出错: {e}")
    
    logger.info("✅ 服务已安全关闭")

# Read root path from environment (for reverse proxy sub-paths)
ROOT_PATH = config.root_path

app = FastAPI(
    title="Faster-Whisper ASR Service (Optimized)", 
    description=f"轻量化语音识别服务 - 默认使用 {config.model_size} 模型 (74M参数，平衡性能和质量)",
    version="2.0.0",
    lifespan=lifespan,
    root_path=ROOT_PATH
)

app.include_router(api_router.router, tags=["ASR"])

# Mount static files
static_dir = config.static_dir
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    print("\n🚀 启动 Faster-Whisper ASR 服务...")
    print(f"🌐 服务将在端口 {config.port} 启动")
    print(f"📖 API 文档: http://localhost:{config.port}/docs")
    print(f"❤️  健康检查: http://localhost:{config.port}/health")
    print(f"📈 监控指标: http://localhost:{config.port}/metrics")
    print("⏳ 正在初始化服务...\n")
    
    try:
        uvicorn.run(
            app, 
            host=config.host, 
            port=config.port,
            log_level=config.log_level.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("\n👋 收到中断信号，正在优雅关闭服务...")
    except Exception as e:
        logger.error(f"❌ 服务运行时出错: {e}")
        sys.exit(1)
