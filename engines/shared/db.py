"""
Standby 数据库连接管理

提供 PostgreSQL (连接池) 和 Redis/Dragonfly 的统一接口。
从环境变量或 engines.yaml 配置读取连接信息。

注意: 无MongoDB — 所有数据存储在PostgreSQL

使用方式:
    from shared.db import get_pg, put_pg, get_redis

    pg = get_pg()          # psycopg2 connection (从池中获取)
    redis = get_redis()    # redis client (可选)

    # 重要: 用完后归还连接到池
    put_pg(pg)
"""

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# ============================================================
# PostgreSQL (连接池)
# ============================================================

_pg_pool = None
_pg_pool_lock = threading.Lock()
_pg_last_check = 0

PG_POOL_MIN = 2
PG_POOL_MAX = 20


def _init_pg_pool():
    """初始化 PostgreSQL 连接池"""
    global _pg_pool

    import psycopg2
    from psycopg2 import pool

    dsn = os.environ.get("DB_POSTGRES", "")
    if dsn:
        if dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)
        try:
            _pg_pool = pool.ThreadedConnectionPool(
                PG_POOL_MIN, PG_POOL_MAX, dsn
            )
            logger.info(f"PG 连接池初始化成功 (min={PG_POOL_MIN}, max={PG_POOL_MAX})")
            return
        except Exception as e:
            logger.error(f"PG 连接池初始化失败 (env): {e}")
            raise

    # Fallback: 从 engines.yaml 读取
    try:
        import yaml
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "engines.yaml"
        )
        with open(config_path) as f:
            config = yaml.safe_load(f)
        db_cfg = config.get("shared", {}).get("databases", {}).get("postgresql", {})
        _pg_pool = pool.ThreadedConnectionPool(
            PG_POOL_MIN, PG_POOL_MAX,
            host=db_cfg.get("host", "localhost"),
            port=db_cfg.get("port", 5432),
            dbname=db_cfg.get("database", "standby"),
            user=db_cfg.get("user", "standby"),
            password=db_cfg.get("password", "standby_dev_password"),
        )
        logger.info(f"PG 连接池初始化成功 (from engines.yaml, min={PG_POOL_MIN}, max={PG_POOL_MAX})")
    except Exception as e:
        logger.error(f"PG 连接池初始化失败 (engines.yaml): {e}")
        raise


def get_pg():
    """从连接池获取 PostgreSQL 连接

    返回: psycopg2 connection
    重要: 用完后调用 put_pg(conn) 归还
    """
    global _pg_pool, _pg_last_check

    if _pg_pool is None:
        with _pg_pool_lock:
            if _pg_pool is None:
                _init_pg_pool()

    try:
        conn = _pg_pool.getconn()
        # 检查连接是否存活
        if conn.closed:
            _pg_pool.putconn(conn, close=True)
            conn = _pg_pool.getconn()
        return conn
    except Exception as e:
        logger.error(f"从连接池获取连接失败: {e}")
        # 尝试重新初始化
        with _pg_pool_lock:
            try:
                _pg_pool = None
                _init_pg_pool()
                return _pg_pool.getconn()
            except Exception:
                raise


def put_pg(conn, close=False):
    """归还 PostgreSQL 连接到连接池

    Args:
        conn: psycopg2 connection
        close: 如果 True，关闭连接而非归还
    """
    global _pg_pool
    if _pg_pool is not None and conn is not None:
        try:
            _pg_pool.putconn(conn, close=close)
        except Exception:
            pass


class pg_connection:
    """PostgreSQL 连接上下文管理器

    使用方式:
        with pg_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ...")
        # 连接自动归还到池
    """
    def __enter__(self):
        self.conn = get_pg()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        put_pg(self.conn, close=(exc_type is not None))
        return False


def close_pg():
    """关闭所有 PostgreSQL 连接"""
    global _pg_pool
    if _pg_pool:
        try:
            _pg_pool.closeall()
        except Exception:
            pass
        _pg_pool = None


# ============================================================
# Dragonfly / Redis (可选缓存层)
# ============================================================

_redis_client = None
_redis_lock = threading.Lock()


def get_redis():
    """获取 Redis/Dragonfly 客户端 (可选)

    返回: redis.Redis 或 None (如果未配置)
    """
    global _redis_client

    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            logger.warning("Redis 连接已断开，重新连接...")
            _redis_client = None

    with _redis_lock:
        if _redis_client is not None:
            return _redis_client

        redis_url = os.environ.get("DB_REDIS", "")
        if not redis_url:
            # 尝试从 engines.yaml 读取
            try:
                import yaml
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "config", "engines.yaml"
                )
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                redis_cfg = config.get("shared", {}).get("databases", {}).get("redis", {})
                if redis_cfg:
                    host = redis_cfg.get("host", "localhost")
                    port = redis_cfg.get("port", 6379)
                    redis_url = f"redis://{host}:{port}"
            except Exception:
                pass

        if not redis_url:
            # 默认连接 Dragonfly
            redis_url = "redis://localhost:6379"

        try:
            import redis
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
            )
            _redis_client.ping()
            logger.info(f"Redis 连接成功: {redis_url}")
            return _redis_client
        except Exception as e:
            logger.warning(f"Redis 连接失败 (缓存不可用): {e}")
            _redis_client = None
            return None


def close_redis():
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None


# ============================================================
# 统一关闭
# ============================================================

def close_all():
    """关闭所有数据库连接"""
    close_pg()
    close_redis()
