"""
Anchor Engine 专用数据库查询

包含 anchor_engine 拥有的表的查询:
- anchors (读写)
- anchor_vectors (读写)
- reactions (只读，通过 gRPC 查询)
"""

import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def get_anchor_meta(anchor_id: str) -> Optional[Dict[str, Any]]:
    """获取锚点元数据"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            SELECT text_content, topics, quality_score, source, created_at
            FROM anchors WHERE id = %s
        """, (anchor_id,))
        row = cur.fetchone()
        pg.commit()

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
        try:
            pg.rollback()
        except Exception:
            pass
        return None
    finally:
        put_pg(pg)


def get_anchor_meta_batch(anchor_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """批量获取锚点元数据"""
    from standby_common.db import get_pg, put_pg

    if not anchor_ids:
        return {}

    pg = get_pg()
    try:
        cur = pg.cursor()
        placeholders = ",".join(["%s"] * len(anchor_ids))
        cur.execute(f"""
            SELECT id, text_content, topics, quality_score, source, created_at
            FROM anchors WHERE id IN ({placeholders})
        """, anchor_ids)
        rows = cur.fetchall()
        pg.commit()

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
        try:
            pg.rollback()
        except Exception:
            pass
        return {}
    finally:
        put_pg(pg)


def save_anchor_meta(anchor_id: str, text: str, topics: List[str],
                     quality_score: float = 0.0, anchor_type: str = "user",
                     parent_anchor_id: Optional[str] = None) -> bool:
    """保存锚点元数据"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO anchors (id, text_content, topics, source, quality_score, modality, parent_anchor_id)
            VALUES (%s, %s, %s, %s, %s, 'text', %s)
            ON CONFLICT (id) DO UPDATE SET
                text_content = EXCLUDED.text_content,
                topics = EXCLUDED.topics,
                quality_score = EXCLUDED.quality_score,
                parent_anchor_id = EXCLUDED.parent_anchor_id
        """, (anchor_id, text, json.dumps(topics), anchor_type, quality_score, parent_anchor_id))
        pg.commit()
        return True
    except Exception as e:
        logger.error(f"保存锚点元数据失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return False
    finally:
        put_pg(pg)


def get_feeling_chain_anchors(parent_anchor_id: str) -> List[Dict[str, Any]]:
    """获取感受链条目（子心物列表）"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            SELECT a.id, a.text_content, a.topics, a.quality_score, a.created_at,
                   r.user_id, r.reaction_type, r.emotion_word, r.resonance_value
            FROM anchors a
            JOIN reactions r ON r.anchor_id = a.id
            WHERE a.parent_anchor_id = %s
            ORDER BY a.created_at DESC
        """, (parent_anchor_id,))
        rows = cur.fetchall()
        pg.commit()

        results = []
        for row in rows:
            results.append({
                "anchor_id": row[0],
                "text_content": row[1] or "",
                "topics": json.loads(row[2]) if row[2] else [],
                "quality_score": row[3] or 0.0,
                "created_at": row[4].timestamp() if row[4] else 0,
                "user_id": row[5] or "",
                "reaction_type": row[6] or "",
                "emotion_word": row[7] or "",
                "resonance_value": row[8] or 0.0,
            })
        return results
    except Exception as e:
        logger.error(f"获取感受链失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return []
    finally:
        put_pg(pg)


def count_reactions_batch(anchor_ids: List[str]) -> Dict[str, int]:
    """批量统计反应数"""
    from standby_common.db import get_pg, put_pg

    if not anchor_ids:
        return {}

    pg = get_pg()
    try:
        cur = pg.cursor()
        placeholders = ",".join(["%s"] * len(anchor_ids))
        cur.execute(f"""
            SELECT anchor_id, COUNT(*) as cnt
            FROM reactions WHERE anchor_id IN ({placeholders})
            GROUP BY anchor_id
        """, anchor_ids)
        rows = cur.fetchall()
        pg.commit()

        return {row[0]: row[1] for row in rows}
    except Exception as e:
        logger.error(f"统计反应数失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return {}
    finally:
        put_pg(pg)
