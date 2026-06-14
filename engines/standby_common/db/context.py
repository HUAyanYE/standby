"""
Context Engine 专用数据库查询

包含 context_engine 拥有的表的查询:
- user_contexts (读写)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def save_user_context(user_id: str, context_data: Dict[str, Any]) -> bool:
    """保存用户情境状态"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
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
        return True
    except Exception as e:
        logger.error(f"保存用户情境失败: {e}")
        try:
            pg.rollback()
        except Exception:
            pass
        return False
    finally:
        put_pg(pg)


def load_all_user_contexts() -> Dict[str, Dict[str, Any]]:
    """加载所有用户情境状态"""
    from standby_common.db import get_pg, put_pg

    pg = get_pg()
    try:
        cur = pg.cursor()
        cur.execute("""
            SELECT user_id, scene_type, mood_hint, attention_level,
                   device, context_timestamp
            FROM user_contexts
        """)
        rows = cur.fetchall()
        pg.commit()

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
        try:
            pg.rollback()
        except Exception:
            pass
        return {}
    finally:
        put_pg(pg)
