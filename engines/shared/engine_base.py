"""
Standby AI 引擎 — gRPC 服务基类

提供引擎服务的通用框架:
- gRPC server 启动/关闭
- 健康检查
- 请求日志
- 错误处理
- 配置加载

各引擎继承此基类, 实现具体的 RPC 方法。
"""

import logging
import signal
import sys
import time
from concurrent import futures
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import grpc

logger = logging.getLogger(__name__)


@dataclass
class EngineConfig:
    """引擎配置 (从 engines.yaml 加载)"""
    engine_name: str
    host: str = "0.0.0.0"
    port: int = 8090
    max_workers: int = 10
    log_level: str = "INFO"
    
    @classmethod
    def from_yaml(cls, engine_name: str, yaml_path: Optional[str] = None) -> "EngineConfig":
        """从 YAML 配置文件加载"""
        import yaml
        
        if yaml_path is None:
            yaml_path = str(Path(__file__).parent.parent / "config" / "engines.yaml")
        
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        
        engine_config = config.get(engine_name, {})
        
        return cls(
            engine_name=engine_name,
            host=engine_config.get("host", "0.0.0.0"),
            port=engine_config.get("port", cls._default_port(engine_name)),
            max_workers=engine_config.get("max_workers", 10),
            log_level=engine_config.get("log_level", "INFO"),
        )
    
    @staticmethod
    def _default_port(engine_name: str) -> int:
        ports = {
            "anchor_engine": 8090,
            "resonance_engine": 8091,
            "governance_engine": 8092,
            "user_engine": 8093,
            "context_engine": 8094,
        }
        return ports.get(engine_name, 8090)


class EngineServicer:
    """引擎服务基类
    
    使用方式:
        class MyEngineServicer(EngineServicer):
            def __init__(self, config):
                super().__init__(config)
                # 初始化引擎特有组件
            
            def register_services(self, server):
                # 注册 gRPC 服务
                add_MyServiceServicer_to_server(self, server)
    """
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format=f"[{config.engine_name}] %(asctime)s %(levelname)s %(message)s",
        )
        
        logger.info(f"初始化 {config.engine_name} 引擎")
    
    def register_services(self, server: grpc.Server):
        """注册 gRPC 服务到 server (子类实现)"""
        raise NotImplementedError
    
    def health_check(self) -> dict:
        """健康检查"""
        return {
            "engine": self.config.engine_name,
            "status": "healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._request_count),
        }
    
    def _log_request(self, method: str, duration_ms: float, success: bool = True):
        """记录请求日志"""
        self._request_count += 1
        if not success:
            self._error_count += 1
        
        level = logging.INFO if success else logging.WARNING
        status = "OK" if success else "ERROR"
        logger.log(level, f"{method} {status} {duration_ms:.1f}ms")
    
    def run(self):
        """启动 gRPC 服务"""
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self.config.max_workers),
            options=[
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ],
        )
        
        self.register_services(server)
        
        address = f"{self.config.host}:{self.config.port}"
        server.add_insecure_port(address)
        server.start()
        
        logger.info(f"{self.config.engine_name} 启动在 {address}")
        
        # 优雅关闭
        def shutdown(signum, frame):
            logger.info(f"收到信号 {signum}, 正在关闭...")
            server.stop(grace=5)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)
        
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(grace=5)


# ============================================================
# 工具函数
# ============================================================

def timing_decorator(func):
    """请求计时装饰器 — 同时支持 gRPC 和本地调用"""
    def wrapper(self, request, context=None):
        start = time.perf_counter()
        try:
            if context is not None:
                result = func(self, request, context)
            else:
                result = func(self, request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            if hasattr(self, '_log_request'):
                self._log_request(func.__name__, elapsed_ms, success=True)
            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if hasattr(self, '_log_request'):
                self._log_request(func.__name__, elapsed_ms, success=False)
            logger.exception(f"{func.__name__} 失败: {e}")
            if context is not None:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
            raise
    return wrapper


def vector_to_bytes(vector) -> bytes:
    """numpy 向量转 bytes (float32)"""
    import numpy as np
    return vector.astype(np.float32).tobytes()


def bytes_to_vector(data: bytes, dimension: int = 768):
    """bytes 转 numpy 向量"""
    import numpy as np
    return np.frombuffer(data, dtype=np.float32).reshape(dimension)
