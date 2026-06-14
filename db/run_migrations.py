#!/usr/bin/env python3
"""
Standby 数据库迁移运行器

用法:
    python db/run_migrations.py                    # 运行所有待执行的迁移
    python db/run_migrations.py --status           # 查看迁移状态
    python db/run_migrations.py --seed             # 包含种子数据

环境变量:
    DATABASE_URL 或 DB_POSTGRES: PostgreSQL 连接字符串
    DEVELOPMENT_SEED: 设为 "true" 时执行种子数据迁移
"""

import os
import sys
import glob
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[migrate] %(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def get_connection():
    """获取数据库连接"""
    import psycopg2

    dsn = os.environ.get("DATABASE_URL") or os.environ.get("DB_POSTGRES", "")
    if not dsn:
        # 尝试从 engines.yaml 读取
        try:
            import yaml
            config_path = Path(__file__).parent.parent / "engines" / "config" / "engines.yaml"
            with open(config_path) as f:
                config = yaml.safe_load(f)
            db_cfg = config.get("shared", {}).get("databases", {}).get("postgresql", {})
            dsn = f"postgresql://{db_cfg.get('user', 'standby')}:{db_cfg.get('password', '')}@{db_cfg.get('host', 'localhost')}:{db_cfg.get('port', 5432)}/{db_cfg.get('database', 'standby')}"
        except Exception:
            pass

    if not dsn:
        logger.error("未找到数据库连接配置，请设置 DATABASE_URL 或 DB_POSTGRES 环境变量")
        sys.exit(1)

    if dsn.startswith("postgres://"):
        dsn = dsn.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(dsn)


def ensure_migrations_table(conn):
    """确保迁移跟踪表存在"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version     INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
    conn.commit()


def get_applied_versions(conn) -> set:
    """获取已应用的迁移版本"""
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM _migrations ORDER BY version")
        return {row[0] for row in cur.fetchall()}


def get_pending_migrations(migrations_dir: str, applied: set, include_seed: bool = False) -> list:
    """获取待执行的迁移文件"""
    pattern = os.path.join(migrations_dir, "*.sql")
    files = sorted(glob.glob(pattern))

    pending = []
    for f in files:
        name = os.path.basename(f)
        # 从文件名提取版本号: 001_extensions.sql -> 1
        try:
            version = int(name.split("_")[0])
        except ValueError:
            continue

        # 种子数据迁移默认跳过
        if "seed" in name and not include_seed:
            logger.info(f"跳过种子数据迁移: {name}")
            continue

        if version not in applied:
            pending.append((version, name, f))

    return pending


def run_migration(conn, version: int, name: str, filepath: str):
    """执行单个迁移"""
    logger.info(f"执行迁移 {version:03d}: {name}")

    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO _migrations (version, name) VALUES (%s, %s)",
            (version, name),
        )

    conn.commit()
    logger.info(f"迁移 {version:03d} 完成")


def show_status(conn, migrations_dir: str):
    """显示迁移状态"""
    applied = get_applied_versions(conn)
    pattern = os.path.join(migrations_dir, "*.sql")
    files = sorted(glob.glob(pattern))

    print("\n迁移状态:")
    print("-" * 60)

    for f in files:
        name = os.path.basename(f)
        try:
            version = int(name.split("_")[0])
        except ValueError:
            continue

        status = "✅ 已应用" if version in applied else "⏳ 待执行"
        print(f"  {version:03d} {name:<40} {status}")

    print("-" * 60)
    print(f"总计: {len(files)} 个迁移, {len(applied)} 个已应用, {len(files) - len(applied)} 个待执行\n")


def main():
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")

    if not os.path.exists(migrations_dir):
        logger.error(f"迁移目录不存在: {migrations_dir}")
        sys.exit(1)

    include_seed = "--seed" in sys.argv or os.environ.get("DEVELOPMENT_SEED", "").lower() == "true"
    status_only = "--status" in sys.argv

    conn = get_connection()
    try:
        ensure_migrations_table(conn)

        if status_only:
            show_status(conn, migrations_dir)
            return

        applied = get_applied_versions(conn)
        pending = get_pending_migrations(migrations_dir, applied, include_seed)

        if not pending:
            logger.info("没有待执行的迁移")
            return

        logger.info(f"发现 {len(pending)} 个待执行迁移")

        for version, name, filepath in pending:
            run_migration(conn, version, name, filepath)

        logger.info("所有迁移执行完成")

    except Exception as e:
        logger.error(f"迁移失败: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
