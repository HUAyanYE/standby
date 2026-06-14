"""
Governance Engine 专用数据库查询

包含 governance_engine 拥有的表的查询:
- governance_decisions (读写)
- users.marker_credit (读写)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def save_governance_decision(decision_data: Dict[str, Any]) -> bool:
    """保存治理决策"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO governance_decisions (content_id, content_type, level,
                                              harmful_weight, marker_avg_credit, reason, actions)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            decision_data.get("content_id"),
            decision_data.get("content_type", "anchor"),
            decision_data.get("level", "L0_NORMAL"),
            decision_data.get("harmful_weight", 0.0),
            decision_data.get("marker_avg_credit", 0.5),
            decision_data.get("reason", ""),
            decision_data.get("actions", []),
        ))
        pg.commit()
        return True
    except Exception as e:
        logger.error(f"保存治理决策失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return False
    finally:
        put_pg(pg)
