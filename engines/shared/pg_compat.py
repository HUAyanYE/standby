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
        
        # 感受链：获取父反应信息并计算深度
        parent_reaction_id = reaction_data.get("parent_reaction_id")
        depth = 0
        root_reaction_id = None
        
        if parent_reaction_id:
            # 查询父反应的深度和根节点
            cur.execute("""
                SELECT depth, root_reaction_id FROM reactions WHERE id = %s
            """, (parent_reaction_id,))
            parent_row = cur.fetchone()
            if parent_row:
                depth = parent_row[0] + 1
                root_reaction_id = parent_row[1] or parent_reaction_id
            else:
                # 父反应不存在，当作根反应处理
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
        
        # 如果是根反应，更新 root_reaction_id 为自己的 id
        new_id = cur.fetchone()[0]
        if not root_reaction_id:
            cur.execute("""
                UPDATE reactions SET root_reaction_id = %s WHERE id = %s
            """, (new_id, new_id))
        
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


def get_reaction_counts_by_type(anchor_id: str) -> Dict[str, int]:
    """按反应类型统计 (替代 mongo.reactions.aggregate by reaction_type)

    Returns: dict with keys: resonance_count, neutral_count, opposition_count,
             unexperienced_count, harmful_count, total_count
    """
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            SELECT reaction_type, COUNT(*) as cnt
            FROM reactions WHERE anchor_id = %s
            GROUP BY reaction_type
        """, (anchor_id,))
        rows = cur.fetchall()
        pg.commit(); put_pg(pg)

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
        return {
            "resonance_count": 0, "neutral_count": 0,
            "opposition_count": 0, "unexperienced_count": 0,
            "harmful_count": 0, "total_count": 0,
        }


def save_user_context(user_id: str, context_data: Dict[str, Any]) -> bool:
    """保存用户情境状态 (PostgreSQL 持久化)

    Args:
        user_id: 用户 ID
        context_data: 包含 scene_type, mood_hint, attention_level, device, timestamp
    """
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO user_contexts (user_id, scene_type, mood_hint, attention_level,
                                       device, context_timestamp, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                scene_type = EXCLUDED.scene_type,
                mood_hint = EXCLUDED.mood_hint,
                attention_level = EXCLUDED.attention_level,
                device = EXCLUDED.device,
                context_timestamp = EXCLUDED.context_timestamp,
                updated_at = NOW()
        """, (
            user_id,
            context_data.get("scene_type", ""),
            context_data.get("mood_hint", ""),
            context_data.get("attention_level", ""),
            context_data.get("device", 0),
            context_data.get("timestamp", 0),
        ))
        pg.commit()
        put_pg(pg)
        return True
    except Exception as e:
        logger.error(f"保存用户情境失败: {e}")
        return False


def load_all_user_contexts() -> Dict[str, Dict[str, Any]]:
    """加载所有用户情境状态 (启动时恢复)

    Returns: dict mapping user_id → context data
    """
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            SELECT user_id, scene_type, mood_hint, attention_level,
                   device, context_timestamp
            FROM user_contexts
        """)
        rows = cur.fetchall()
        pg.commit()
        put_pg(pg)

        result = {}
        for row in rows:
            result[row[0]] = {
                "scene_type": row[1] or "",
                "mood_hint": row[2] or "",
                "attention_level": row[3] or "",
                "device": row[4] or 0,
                "timestamp": row[5] or 0,
            }
        return result
    except Exception as e:
        logger.error(f"加载用户情境失败: {e}")
        return {}


def find_resonance_reaction_users(anchor_id: str, exclude_user_id: str) -> List[str]:
    """找到在同一锚点上有共鸣的其他用户 (替代 mongo.reactions.find)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("""
            SELECT DISTINCT user_id FROM reactions
            WHERE anchor_id = %s AND reaction_type = '共鸣' AND user_id != %s
        """, (anchor_id, exclude_user_id))
        rows = cur.fetchall()
        pg.commit(); put_pg(pg)
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"查找共鸣用户失败: {e}")
        return []


def list_reactions_paginated(anchor_id: str, filter_type: str = None,
                             offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """分页查询反应 (替代 mongo.reactions.find with sort/skip/limit)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
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
        pg.commit(); put_pg(pg)

        return [{
            "_id": row[0],
            "user_id": row[1],
            "anchor_id": row[2],
            "reaction_type": row[3],
            "emotion_word": row[4],
            "opinion_text": row[5],
            "resonance_value": row[6],
            "timestamp": row[7].timestamp() if row[7] else 0,
        } for row in rows]
    except Exception as e:
        logger.error(f"分页查询反应失败: {e}")
        return []


def count_reactions_filtered(anchor_id: str, filter_type: str = None) -> int:
    """统计反应数量 (替代 mongo.reactions.count_documents)"""
    from shared.db import get_pg, put_pg

    try:
        pg = get_pg()
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
        pg.commit(); put_pg(pg)
        return count
    except Exception as e:
        logger.error(f"统计反应数量失败: {e}")
        return 0
