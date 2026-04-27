"""
MongoDB 兼容层 — 使用 PostgreSQL 替代 MongoDB

提供一个类似 MongoDB 的接口，但底层使用 PostgreSQL。
这样引擎代码不需要大量修改。

使用方式:
    from shared.mongo_compat import get_mongo_compat
    mongo = get_mongo_compat()
    
    # 然后像使用 MongoDB 一样使用:
    mongo.reactions.insert_one({...})
    mongo.reactions.find({...})
    mongo.anchor_metadata.find_one({...})
"""

import json
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class MongoCollectionCompat:
    """模拟 MongoDB collection 的 PostgreSQL 实现"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    def _get_table_name(self) -> str:
        """根据 collection 名称映射到 PostgreSQL 表"""
        mapping = {
            'reactions': 'reactions',
            'anchor_metadata': 'anchors',
            'governance_logs': 'governance_decisions',
            'governance_decisions': 'governance_decisions',
        }
        return mapping.get(self.collection_name, self.collection_name)
    
    def insert_one(self, document: Dict[str, Any]) -> bool:
        """插入单条记录"""
        from shared.db import get_pg, put_pg
        
        table = self._get_table_name()
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            if table == 'reactions':
                cur.execute("""
                    INSERT INTO reactions (user_id, anchor_id, reaction_type, 
                                          emotion_word, modality, text_content, resonance_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    document.get('user_id'),
                    document.get('anchor_id'),
                    document.get('reaction_type'),
                    document.get('emotion_word'),
                    document.get('modality', 'text'),
                    document.get('opinion_text') or document.get('text_content'),
                    document.get('resonance_value'),
                ))
            elif table == 'anchors':
                cur.execute("""
                    INSERT INTO anchors (id, text_content, topics, quality_score, source, modality)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        topics = EXCLUDED.topics,
                        quality_score = EXCLUDED.quality_score
                """, (
                    document.get('anchor_id'),
                    document.get('text'),
                    json.dumps(document.get('topics', [])),
                    document.get('quality_score', 0.0),
                    document.get('anchor_type', 'user'),
                    'text',
                ))
            elif table == 'governance_decisions':
                cur.execute("""
                    INSERT INTO governance_decisions (content_id, content_type, level,
                                                    harmful_weight, marker_avg_credit, reason, actions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    document.get('content_id'),
                    document.get('content_type', 'anchor'),
                    document.get('level', 'L0_NORMAL'),
                    document.get('harmful_weight', 0.0),
                    document.get('marker_avg_credit', 0.5),
                    document.get('reason', ''),
                    document.get('actions', []),
                ))
            
            put_pg(pg)
            return True
        except Exception as e:
            logger.error(f"插入记录失败: {e}")
            return False
    
    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        from shared.db import get_pg, put_pg
        
        table = self._get_table_name()
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            if table == 'anchors':
                anchor_id = query.get('anchor_id')
                cur.execute("""
                    SELECT id, text_content, topics, quality_score, source, created_at
                    FROM anchors WHERE id = %s
                """, (anchor_id,))
                row = cur.fetchone()
                put_pg(pg)
                
                if not row:
                    return None
                
                return {
                    'anchor_id': row[0],
                    'text': row[1] or '',
                    'topics': json.loads(row[2]) if row[2] else [],
                    'quality_score': row[3] or 0.0,
                    'anchor_type': row[4] or 'user',
                    'created_at': row[5].timestamp() if row[5] else 0,
                }
            
            put_pg(pg)
            return None
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            return None
    
    def find(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询多条记录"""
        from shared.db import get_pg, put_pg
        
        table = self._get_table_name()
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            if table == 'reactions':
                anchor_id = query.get('anchor_id')
                user_id = query.get('user_id')
                reaction_type = query.get('reaction_type')
                
                conditions = []
                params = []
                
                if anchor_id:
                    conditions.append("anchor_id = %s")
                    params.append(anchor_id)
                if user_id:
                    if isinstance(user_id, dict) and '$ne' in user_id:
                        conditions.append("user_id != %s")
                        params.append(user_id['$ne'])
                    else:
                        conditions.append("user_id = %s")
                        params.append(user_id)
                if reaction_type:
                    conditions.append("reaction_type = %s")
                    params.append(reaction_type)
                
                where_clause = " AND ".join(conditions) if conditions else "TRUE"
                
                cur.execute(f"""
                    SELECT user_id, anchor_id, reaction_type, emotion_word, 
                           text_content, resonance_value, created_at
                    FROM reactions WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 100
                """, params)
                
                rows = cur.fetchall()
                put_pg(pg)
                
                return [{
                    'user_id': row[0],
                    'anchor_id': row[1],
                    'reaction_type': row[2],
                    'emotion_word': row[3],
                    'opinion_text': row[4],
                    'resonance_value': row[5],
                    'created_at': row[6].timestamp() if row[6] else 0,
                } for row in rows]
            
            put_pg(pg)
            return []
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            return []
    
    def aggregate(self, pipeline: List[Dict]) -> List[Dict[str, Any]]:
        """聚合查询"""
        from shared.db import get_pg, put_pg
        
        table = self._get_table_name()
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            if table == 'reactions':
                # 解析 MongoDB pipeline
                match_stage = pipeline[0].get('$match', {})
                group_stage = pipeline[1].get('$group', {})
                
                anchor_id = match_stage.get('anchor_id')
                group_by = group_stage.get('_id', '').lstrip('$')
                
                if group_by == 'reaction_type':
                    cur.execute("""
                        SELECT reaction_type, COUNT(*) as cnt
                        FROM reactions WHERE anchor_id = %s
                        GROUP BY reaction_type
                    """, (anchor_id,))
                    
                    rows = cur.fetchall()
                    put_pg(pg)
                    
                    return [{'_id': row[0], 'count': row[1]} for row in rows]
            
            put_pg(pg)
            return []
        except Exception as e:
            logger.error(f"聚合查询失败: {e}")
            return []
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """更新单条记录"""
        from shared.db import get_pg, put_pg
        
        table = self._get_table_name()
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            if table == 'anchors':
                anchor_id = query.get('anchor_id')
                set_data = update.get('$set', {})
                
                cur.execute("""
                    UPDATE anchors SET text_content = %s, topics = %s, 
                                      quality_score = %s, updated_at = NOW()
                    WHERE id = %s
                """, (
                    set_data.get('text'),
                    json.dumps(set_data.get('topics', [])),
                    set_data.get('quality_score', 0.0),
                    anchor_id,
                ))
            
            put_pg(pg)
            return True
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            return False
    
    def count_documents(self, query: Dict[str, Any]) -> int:
        """统计文档数量"""
        from shared.db import get_pg, put_pg
        
        table = self._get_table_name()
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            if table == 'reactions':
                anchor_id = query.get('anchor_id')
                cur.execute("""
                    SELECT COUNT(*) FROM reactions WHERE anchor_id = %s
                """, (anchor_id,))
                count = cur.fetchone()[0]
                put_pg(pg)
                return count
            
            put_pg(pg)
            return 0
        except Exception as e:
            logger.error(f"统计文档失败: {e}")
            return 0


class MongoDatabaseCompat:
    """模拟 MongoDB database 的 PostgreSQL 实现"""
    
    def __getattr__(self, name: str) -> MongoCollectionCompat:
        return MongoCollectionCompat(name)
    
    def command(self, cmd: str) -> bool:
        """模拟 MongoDB 命令"""
        if cmd == 'ping':
            from shared.db import get_pg, put_pg
            try:
                pg = get_pg()
                cur = pg.cursor()
                cur.execute("SELECT 1")
                put_pg(pg)
                return True
            except Exception:
                return False
        return True


def get_mongo_compat() -> MongoDatabaseCompat:
    """获取 MongoDB 兼容层实例"""
    return MongoDatabaseCompat()
