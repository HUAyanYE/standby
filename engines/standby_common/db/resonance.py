"""
Resonance Engine 专用数据库查询

包含 resonance_engine 拥有的表的查询:
- resonance_vectors (读写)
- reactions (读写)
- relationships (读写)
- anchors (只读，通过 gRPC 查询)
"""

import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def get_reaction_counts_by_type(anchor_id: str) -> Dict[str, int]:
    """按反应类型统计"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            SELECT reaction_type, COUNT(*) as cnt
            FROM reactions WHERE anchor_id = %s
            GROUP BY reaction_type
        """, (anchor_id,))
        rows = cur.fetchall()
        pg.commit()

        counts = {row[0]: row[1] for row in rows}
        total = sum(counts.values())
        return {
            "resonance_count": counts.get("共鸣", 0),
            "neutral_count": counts.get("无感", 0),
            "opposition_count": counts.get("反对", 0),
            "unexperienced_count": counts.get("未体验", 0),
            "harmful_count": counts.get("有害", 0),
            "total_count": total,
        }
    except Exception as e:
        logger.error(f"按类型统计反应失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return {
            "resonance_count": 0, "neutral_count": 0,
            "opposition_count": 0, "unexperienced_count": 0,
            "harmful_count": 0, "total_count": 0,
        }
    finally:
        put_pg(pg)


def find_resonance_reaction_users(anchor_id: str, exclude_user_id: str) -> List[str]:
    """找到在同一锚点上有共鸣的其他用户"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            SELECT DISTINCT user_id FROM reactions
            WHERE anchor_id = %s AND reaction_type = '共鸣' AND user_id != %s
        """, (anchor_id, exclude_user_id))
        rows = cur.fetchall()
        pg.commit()

        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"查找共鸣用户失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return []
    finally:
        put_pg(pg)


def list_reactions_paginated(anchor_id: str, filter_type: Optional[str] = None,
                             offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """分页查询反应"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        if filter_type:
            cur.execute("""
                SELECT id, user_id, anchor_id, reaction_type, emotion_word,
                       text_content, resonance_value, created_at
                FROM reactions WHERE anchor_id = %s AND reaction_type = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (anchor_id, filter_type, limit, offset))
        else:
            cur.execute("""
                SELECT id, user_id, anchor_id, reaction_type, emotion_word,
                       text_content, resonance_value, created_at
                FROM reactions WHERE anchor_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (anchor_id, limit, offset))
        rows = cur.fetchall()
        pg.commit()

        return [{
            "id": row[0],
            "user_id": row[1],
            "anchor_id": row[2],
            "reaction_type": row[3],
            "emotion_word": row[4],
            "opinion_text": row[5],
            "resonance_value": row[6],
            "created_at": row[7].timestamp() if row[7] else 0,
        } for row in rows]
    except Exception as e:
        logger.error(f"分页查询反应失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return []
    finally:
        put_pg(pg)


def count_reactions_filtered(anchor_id: str, filter_type: Optional[str] = None) -> int:
    """统计反应数量"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        if filter_type:
            cur.execute("""
                SELECT COUNT(*) FROM reactions
                WHERE anchor_id = %s AND reaction_type = %s
            """, (anchor_id, filter_type))
        else:
            cur.execute("""
                SELECT COUNT(*) FROM reactions WHERE anchor_id = %s
            """, (anchor_id,))
        count = cur.fetchone()[0]
        pg.commit()

        return count
    except Exception as e:
        logger.error(f"统计反应数量失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return 0
    finally:
        put_pg(pg)


def save_reaction_event(reaction_data: Dict[str, Any]) -> bool:
    """保存反应事件"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()

        parent_reaction_id = reaction_data.get("parent_reaction_id")
        depth = 0
        root_reaction_id = None

        if parent_reaction_id:
            cur.execute("""
                SELECT depth, root_reaction_id FROM reactions WHERE id = %s
            """, (parent_reaction_id,))
            parent_row = cur.fetchone()
            if parent_row:
                depth = parent_row[0] + 1
                root_reaction_id = parent_row[1] or parent_reaction_id
            else:
                parent_reaction_id = None

        cur.execute("""
            INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word,
                                   modality, text_content, resonance_value,
                                   parent_reaction_id, depth, root_reaction_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            reaction_data.get("user_id"),
            reaction_data.get("anchor_id"),
            reaction_data.get("reaction_type"),
            reaction_data.get("emotion_word"),
            reaction_data.get("modality", "text"),
            reaction_data.get("text_content"),
            reaction_data.get("resonance_value"),
            parent_reaction_id,
            depth,
            root_reaction_id,
        ))

        new_id = cur.fetchone()[0]
        if not root_reaction_id:
            cur.execute("""
                UPDATE reactions SET root_reaction_id = %s WHERE id = %s
            """, (new_id, new_id))

        pg.commit()
        return True
    except Exception as e:
        logger.error(f"保存反应事件失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return False
    finally:
        put_pg(pg)
