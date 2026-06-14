"""
standby-common — Standby 共享 Python 模块

提供引擎通用的基础设施:
- EngineServicer: gRPC 服务基类
- db: PostgreSQL 连接池 + Redis 客户端
- db_queries: 通用 SQL 查询层
- nats_client: NATS 事件发布/订阅
- rust_engine_client: Rust 高性能计算服务客户端
- encoders: 文本编码器

使用方式:
    from standby_common.base import EngineConfig, EngineServicer
    from standby_common.db import get_pg, put_pg
    from standby_common.db_queries import get_anchor_meta
    from standby_common.events import NATSClient, EventBuilder
    from standby_common.rust_client import call_resonance_compute
"""

__version__ = "0.1.0"

from .base import EngineConfig, EngineServicer, timing_decorator
from .db import get_pg, put_pg, get_redis, pg_connection
