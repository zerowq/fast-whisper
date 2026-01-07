#!/usr/bin/env python3
"""
基本集成测试脚本
确保服务能够启动，验证 /health 和 /metrics 端点可访问
"""

import os
import sys
import time
import requests
import subprocess
import signal
import logging
from pathlib import Path
import threading
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTester:
    """集成测试器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 60):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.server_process = None
        self.server_ready = False
        
    def start_server(self) -> bool:
        """启动服务器"""
        logger.info("🚀 启动服务器...")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env.update({
                "PORT": str(self.port),
                "MODEL_SIZE": "base",
                "DEVICE": "cpu",  # 强制使用 CPU 以确保兼容性
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
            
            # 等待服务器启动
            logger.info(f"等待服务器启动 (最多 {self.timeout} 秒)...")
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
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
                    if any(keyword in line for keyword in ["ERROR", "WARNING", "✅", "❌", "🚀"]):
                        logger.info(f"[SERVER] {line}")
        except Exception as e:
            logger.debug(f"日志监控异常: {e}")
    
    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            logger.info("🛑 停止服务器...")
            try:
                # 发送 SIGTERM 信号
                self.server_process.terminate()
                
                # 等待进程结束
                try:
                    self.server_process.wait(timeout=10)
                    logger.info("✅ 服务器已停止")
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️  服务器未在10秒内停止，强制终止")
                    self.server_process.kill()
                    self.server_process.wait()
                    
            except Exception as e:
                logger.error(f"停止服务器时出错: {e}")
            finally:
                self.server_process = None
    
    def test_health_endpoint(self) -> bool:
        """测试健康检查端点"""
        logger.info("❤️  测试健康检查端点...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 健康检查端点响应正常")
                logger.info(f"  状态: {data.get('status', 'unknown')}")
                logger.info(f"  服务: {data.get('service', 'unknown')}")
                logger.info(f"  模型已加载: {data.get('model_loaded', False)}")
                
                if data.get('model_loaded'):
                    logger.info(f"  模型大小: {data.get('model_size', 'unknown')}")
                    logger.info(f"  设备: {data.get('device', 'unknown')}")
                
                return True
            else:
                logger.error(f"❌ 健康检查端点返回错误状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 健康检查端点请求失败: {e}")
            return False
    
    def test_metrics_endpoint(self) -> bool:
        """测试监控指标端点"""
        logger.info("📈 测试监控指标端点...")
        
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 监控指标端点响应正常")
                
                # 检查关键指标
                required_keys = ["cpu_usage_percent", "memory", "timestamp"]
                missing_keys = [key for key in required_keys if key not in data]
                
                if missing_keys:
                    logger.warning(f"⚠️  缺少关键指标: {missing_keys}")
                
                # 显示一些关键指标
                logger.info(f"  CPU使用率: {data.get('cpu_usage_percent', 'N/A')}%")
                
                memory = data.get('memory', {})
                if memory:
                    logger.info(f"  内存使用率: {memory.get('used_percent', 'N/A')}%")
                    logger.info(f"  内存使用: {memory.get('used_mb', 'N/A')}MB")
                
                gpu = data.get('gpu', {})
                if gpu and gpu.get('available'):
                    logger.info(f"  GPU可用: 是")
                    logger.info(f"  GPU内存使用率: {gpu.get('memory_percent', 'N/A')}%")
                else:
                    logger.info(f"  GPU可用: 否")
                
                health = data.get('health', {})
                if health:
                    logger.info(f"  健康状态: {health.get('status', 'unknown')}")
                    warnings = health.get('warnings', [])
                    if warnings:
                        logger.info(f"  警告数量: {len(warnings)}")
                
                return True
            else:
                logger.error(f"❌ 监控指标端点返回错误状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 监控指标端点请求失败: {e}")
            return False
    
    def test_api_docs_endpoint(self) -> bool:
        """测试 API 文档端点"""
        logger.info("📖 测试 API 文档端点...")
        
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ API 文档端点可访问")
                return True
            else:
                logger.error(f"❌ API 文档端点返回错误状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 文档端点请求失败: {e}")
            return False
    
    def test_model_info_endpoint(self) -> bool:
        """测试模型信息端点"""
        logger.info("🔍 测试模型信息端点...")
        
        try:
            response = requests.get(f"{self.base_url}/model/info", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 模型信息端点响应正常")
                logger.info(f"  模型大小: {data.get('model_size', 'unknown')}")
                logger.info(f"  参数量: {data.get('parameters', 'unknown')}")
                logger.info(f"  设备: {data.get('device', 'unknown')}")
                logger.info(f"  计算类型: {data.get('compute_type', 'unknown')}")
                logger.info(f"  已加载: {data.get('loaded', False)}")
                return True
            else:
                logger.error(f"❌ 模型信息端点返回错误状态码: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 模型信息端点请求失败: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """运行完整的集成测试"""
        logger.info("🧪 开始集成测试...")
        
        test_steps = [
            ("启动服务器", self.start_server),
            ("健康检查端点", self.test_health_endpoint),
            ("监控指标端点", self.test_metrics_endpoint),
            ("API文档端点", self.test_api_docs_endpoint),
            ("模型信息端点", self.test_model_info_endpoint),
        ]
        
        passed_steps = 0
        total_steps = len(test_steps)
        
        try:
            for step_name, step_func in test_steps:
                logger.info(f"\n{'='*50}")
                logger.info(f"测试步骤: {step_name}")
                logger.info(f"{'='*50}")
                
                try:
                    if step_func():
                        logger.info(f"✅ {step_name} - 通过")
                        passed_steps += 1
                    else:
                        logger.error(f"❌ {step_name} - 失败")
                        break  # 如果关键步骤失败，停止后续测试
                except Exception as e:
                    logger.error(f"❌ {step_name} - 异常: {e}")
                    break
        
        finally:
            # 确保服务器被停止
            self.stop_server()
        
        # 打印测试摘要
        logger.info(f"\n{'='*50}")
        logger.info("集成测试摘要")
        logger.info(f"{'='*50}")
        logger.info(f"通过步骤: {passed_steps}/{total_steps}")
        
        if passed_steps == total_steps:
            logger.info("🎉 所有集成测试通过!")
            return True
        else:
            logger.error(f"❌ {total_steps - passed_steps} 个步骤失败")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="基本集成测试")
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
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="启动超时时间 (默认: 60秒)"
    )
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = IntegrationTester(args.host, args.port, args.timeout)
    
    # 运行测试
    success = tester.run_integration_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()