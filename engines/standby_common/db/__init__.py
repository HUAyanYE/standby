"""
数据库查询层 — 按引擎拆分

每个引擎只导入自己需要的查询模块:
- anchor_engine: from standby_common.db.anchor import get_anchor_meta
- resonance_engine: from standby_common.db.resonance import save_reaction_event
- governance_engine: from standby_common.db.governance import save_governance_decision
- context_engine: from standby_common.db.context import save_user_context

通用连接管理仍在 db.py 中:
- from standby_common.db import get_pg, put_pg, get_redis
"""

# 重新导出连接管理函数
from ..db import get_pg, put_pg, get_redis, pg_connection
