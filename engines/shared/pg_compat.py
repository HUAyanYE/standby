"""
PostgreSQL 兼容层 — 替代 MongoDB 操作

提供类似 MongoDB 的接口，但底层使用 PostgreSQL。
用于渐进式迁移，减少引擎代码改动。

使用方式:
    from shared.pg_compat import get_anchor_meta, save_anchor_meta, count_reactions

    # 查询锚点元数据
    meta = get_anchor_meta(anchor_id)

    # 保存锚点元数据
    save_anchor_meta(anchor_id, text, topics, quality_score)

    # 统计反应数
    counts = count_reactions_batch(anchor_ids)
"""

import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def get_anchor_meta(anchor_id: str) -> Optional[Dict[str, Any]]:
    """获取锚点元数据 (替代 mongo.anchor_metadata.find_one)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            SELECT text_content, topics, quality_score, source, created_at
            FROM anchors WHERE id = %s
        """, (anchor_id,))
        row = cur.fetchone()
        pg.commit(); put_pg(pg)

        if not row:
            return None

        return {
            "anchor_id": anchor_id,
            "text": row[0] or "",
            "topics": json.loads(row[1]) if row[1] else [],
            "quality_score": row[2] or 0.0,
            "anchor_type": row[3] or "user",
            "created_at": row[4].timestamp() if row[4] else 0,
        }
    except Exception as e:
        logger.error(f"获取锚点元数据失败: {e}")
        return None


def get_anchor_meta_batch(anchor_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """批量获取锚点元数据 (替代 mongo.anchor_metadata.find)"""
    from shared.db import get_pg, put_pg

    if not anchor_ids:
        return {}

    try:
        pg = get_pg()
        cur = pg.cursor()
        placeholders = ",".join(["%s"] * len(anchor_ids))
        cur.execute(f"""
            SELECT id, text_content, topics, quality_score, source, created_at
            FROM anchors WHERE id IN ({placeholders})
        """, anchor_ids)
        rows = cur.fetchall()
        pg.commit(); put_pg(pg)

        result = {}
        for row in rows:
            result[row[0]] = {
                "anchor_id": row[0],
                "text": row[1] or "",
                "topics": json.loads(row[2]) if row[2] else [],
                "quality_score": row[3] or 0.0,
                "anchor_type": row[4] or "user",
                "created_at": row[5].timestamp() if row[5] else 0,
            }
        return result
    except Exception as e:
        logger.error(f"批量获取锚点元数据失败: {e}")
        return {}


def save_anchor_meta(anchor_id: str, text: str, topics: List[str],
                     quality_score: float = 0.0, anchor_type: str = "user") -> bool:
    """保存锚点元数据 (替代 mongo.anchor_metadata.update_one)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO anchors (id, text_content, topics, source, quality_score, modality)
            VALUES (%s, %s, %s, %s, %s, 'text')
            ON CONFLICT (id) DO UPDATE SET
                text_content = EXCLUDED.text_content,
                topics = EXCLUDED.topics,
                quality_score = EXCLUDED.quality_score
        """, (anchor_id, text, json.dumps(topics), anchor_type, quality_score))
        pg.commit(); put_pg(pg)
        return True
    except Exception as e:
        logger.error(f"保存锚点元数据失败: {e}")
        return False


def count_reactions_batch(anchor_ids: List[str]) -> Dict[str, int]:
    """批量统计反应数 (替代 mongo.reactions.aggregate)"""
    from shared.db import get_pg, put_pg

    if not anchor_ids:
        return {}

    try:
        pg = get_pg()
        cur = pg.cursor()
        placeholders = ",".join(["%s"] * len(anchor_ids))
        cur.execute(f"""
            SELECT anchor_id, COUNT(*) as cnt
            FROM reactions WHERE anchor_id IN ({placeholders})
            GROUP BY anchor_id
        """, anchor_ids)
        rows = cur.fetchall()
        pg.commit(); put_pg(pg)

        return {row[0]: row[1] for row in rows}
    except Exception as e:
        logger.error(f"统计反应数失败: {e}")
        return {}


def save_reaction_event(reaction_data: Dict[str, Any]) -> bool:
    """保存反应事件 (替代 mongo.reactions.insert_one)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word,
                                   modality, text_content, resonance_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            reaction_data.get("user_id"),
            reaction_data.get("anchor_id"),
            reaction_data.get("reaction_type"),
            reaction_data.get("emotion_word"),
            reaction_data.get("modality", "text"),
            reaction_data.get("text_content"),
            reaction_data.get("resonance_value"),
        ))
        pg.commit(); put_pg(pg)
        return True
    except Exception as e:
        logger.error(f"保存反应事件失败: {e}")
        return False


def save_governance_decision(decision_data: Dict[str, Any]) -> bool:
    """保存治理决策 (替代 mongo.governance_logs.insert_one)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
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
        pg.commit(); put_pg(pg)
        return True
    except Exception as e:
        logger.error(f"保存治理决策失败: {e}")
        return False
