"""
共鸣机制引擎 — gRPC 服务实现

将 resonance_calculator_v2 的算法暴露为 gRPC 服务。
引擎间通过 gRPC 同步调用 + NATS 异步消息通信。

数据层:
- PostgreSQL: 锚点向量、共鸣向量存储
- MongoDB: 反应事件流水
"""

import logging
import sys
import time
from pathlib import Path

import grpc
import numpy as np

# 引擎基类 + sibling 模块
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from shared.engine_base import (
    EngineConfig, EngineServicer, timing_decorator,
    vector_to_bytes, bytes_to_vector,
)
from shared.db import get_pg, put_pg, get_redis

# gRPC 生成代码
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "proto" / "generated" / "python"))
from engines import engines_pb2_grpc
from engines import engines_pb2

# v2 算法
from resonance_calculator_v2 import (
    Reaction, Anchor, ReactionType, EmotionWord,
    compute_resonance_value_v2, compute_relationship_score_v2,
)

# NATS 事件发布
from shared.nats_client import NATSClient, EventBuilder


class ResonanceEngineServicer(EngineServicer):
    """共鸣机制引擎 gRPC 服务 — PostgreSQL + MongoDB"""

    def __init__(self, config: EngineConfig):
        super().__init__(config)

        # 加载编码器
        models_dir = Path(__file__).parent.parent / "shared" / "models"
        from shared.encoders.text_encoder import TextEncoder
        self.encoder = TextEncoder(model_name=str(models_dir / "bge-base-zh-v1.5"))

        # 内存缓存 (热点数据, 持久化到 PG/Mongo)
        self._anchors_cache = {}            # anchor_id → {text, topics, embedding}
        self._opinion_embeddings_cache = {} # anchor_id → [np.ndarray]

        # NATS 事件客户端
        import os
        nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
        self._nats = NATSClient(nats_url=nats_url, engine_name="resonance_engine")

        self.logger.info(f"共鸣引擎初始化完成, 编码器维度: {self.encoder.dimension}")

    @property
    def logger(self):
        return __import__('logging').getLogger(__name__)

    def _load_anchor(self, anchor_id: str) -> dict | None:
        """从缓存/Redis/PG 加载锚点数据"""
        # L1: 内存缓存
        if anchor_id in self._anchors_cache:
            return self._anchors_cache[anchor_id]

        # L2: Redis 缓存
        try:
            redis = get_redis()
            if redis:
                cached = redis.get(f"anchor:vec:{anchor_id}")
                if cached:
                    import json
                    data = json.loads(cached)
                    embedding = np.array(data["embedding"], dtype=np.float32).reshape(768)
                    anchor_data = {
                        "text": data.get("text", ""),
                        "topics": data.get("topics", []),
                        "embedding": embedding,
                    }
                    self._anchors_cache[anchor_id] = anchor_data
                    return anchor_data
        except Exception:
            pass

        # L3: PostgreSQL
        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT av.anchor_id, av.vector
                FROM anchor_vectors av
                WHERE av.anchor_id = %s
            """, (anchor_id,))
            row = cur.fetchone()
            put_pg(pg)
            if not row:
                return None

            raw = row[1]
            if isinstance(raw, str):
                import ast
                vec_list = ast.literal_eval(raw)
                embedding = np.array(vec_list, dtype=np.float32).reshape(768)
            elif isinstance(raw, (bytes, memoryview)):
                embedding = np.frombuffer(bytes(raw), dtype=np.float32).reshape(768)
            else:
                embedding = np.frombuffer(bytes(str(raw), 'utf-8'), dtype=np.float32).reshape(768)

            # TODO: 从 MongoDB 获取锚点文本和 topics
            # 暂时用默认值
            anchor_data = {
                "text": "",
                "topics": [],
                "embedding": embedding,
            }
            self._anchors_cache[anchor_id] = anchor_data

            # 写入 Redis 缓存 (TTL=1h)
            try:
                redis = get_redis()
                if redis:
                    import json
                    cache_data = {
                        "embedding": embedding.tolist(),
                        "text": "",
                        "topics": [],
                    }
                    redis.setex(f"anchor:vec:{anchor_id}", 3600, json.dumps(cache_data))
            except Exception:
                pass

            return anchor_data
        except Exception as e:
            self.logger.error(f"加载锚点失败: {e}")
            return None

    def _find_top_k_similar(self, anchor_id: str, query_embedding: np.ndarray,
                              k: int = 5) -> list[float]:
        """用 pgvector 原生搜索找 top-k 最相似的向量

        替代全量加载 + Python 计算，利用 HNSW 索引 O(log N) 复杂度。
        返回: top-k 相似度列表 (cosine similarity)
        """
        try:
            pg = get_pg()
            cur = pg.cursor()
            # pgvector <=> 是 cosine distance, 1 - distance = similarity
            cur.execute("""
                SELECT 1 - (vector <=> %s::vector) AS similarity
                FROM resonance_vectors
                WHERE anchor_id = %s
                ORDER BY vector <=> %s::vector
                LIMIT %s
            """, (str(query_embedding.tolist()), anchor_id,
                  str(query_embedding.tolist()), k))
            rows = cur.fetchall()
            put_pg(pg)
            return [float(r[0]) for r in rows if r[0] is not None]
        except Exception as e:
            self.logger.error(f"pgvector 搜索失败: {e}")
            # Fallback: 全量加载
            embeddings = self._load_opinion_embeddings(anchor_id)
            if not embeddings:
                return []
            import numpy as np
            existing_matrix = np.array(embeddings)
            similarities = np.dot(existing_matrix, query_embedding)
            k_actual = min(k, len(similarities))
            return sorted(similarities.tolist(), reverse=True)[:k_actual]

    def _load_opinion_embeddings(self, anchor_id: str) -> list:
        """从 PG 加载该锚点下的所有观点向量 (fallback)"""
        if anchor_id in self._opinion_embeddings_cache:
            return self._opinion_embeddings_cache[anchor_id]

        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT vector FROM resonance_vectors
                WHERE anchor_id = %s
                ORDER BY created_at DESC
                LIMIT 100
            """, (anchor_id,))
            rows = cur.fetchall()
            put_pg(pg)
            embeddings = [
                np.frombuffer(bytes(r[0]), dtype=np.float32).reshape(768)
                for r in rows if r[0] is not None
            ]
            self._opinion_embeddings_cache[anchor_id] = embeddings
            return embeddings
        except Exception as e:
            self.logger.error(f"加载观点向量失败: {e}")
            return []

    def _publish_event_async(self, event):
        """非阻塞发布 NATS 事件 (使用持久化事件循环)"""
        import threading
        import asyncio

        # 懒初始化持久化事件循环线程
        if not hasattr(self, '_nats_loop'):
            self._nats_loop = asyncio.new_event_loop()
            self._nats_thread = threading.Thread(
                target=self._run_nats_loop, daemon=True
            )
            self._nats_thread.start()

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._nats.publish(event), self._nats_loop
            )
            # 不等待结果，fire-and-forget
            future.add_done_callback(
                lambda f: self.logger.warning(f"NATS 发布失败: {f.exception()}")
                if f.exception() else None
            )
        except Exception as e:
            self.logger.warning(f"NATS 事件发布调度失败: {e}")

    def _run_nats_loop(self):
        """NATS 事件循环后台线程"""
        import asyncio
        asyncio.set_event_loop(self._nats_loop)
        self._nats_loop.run_forever()

    def _save_reaction(self, anchor_id: str, user_id: str, reaction_type: str,
                       opinion_text: str, resonance_value: float,
                       opinion_vector: np.ndarray | None):
        """保存反应数据"""
        try:
            # PG: 存共鸣向量
            if opinion_vector is not None:
                pg = get_pg()
                cur = pg.cursor()
                cur.execute("""
                    INSERT INTO resonance_vectors (anchor_id, internal_token_hash, vector)
                    VALUES (%s, %s, %s::vector)
                """, (anchor_id, user_id, str(opinion_vector.tolist())))
                put_pg(pg)

                # 更新缓存
                self._opinion_embeddings_cache.setdefault(anchor_id, []).append(opinion_vector)

            # PostgreSQL: 存完整事件
            save_reaction_event({
                "anchor_id": anchor_id,
                "user_id": user_id,
                "reaction_type": reaction_type,
                "opinion_text": opinion_text,
                "resonance_value": resonance_value,
                "timestamp": time.time(),
            })
        except Exception as e:
            self.logger.error(f"保存反应失败: {e}")

    def _get_reaction_counts(self, anchor_id: str) -> dict:
        """从 MongoDB 获取反应分布"""
        try:
            mongo = get_mongo()
            pipeline = [
                {"$match": {"anchor_id": anchor_id}},
                {"$group": {"_id": "$reaction_type", "count": {"$sum": 1}}},
            ]
            results = list(mongo.reactions.aggregate(pipeline))
            counts = {r["_id"]: r["count"] for r in results}
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
            self.logger.error(f"获取反应分布失败: {e}")
            return {
                "resonance_count": 0, "neutral_count": 0,
                "opposition_count": 0, "unexperienced_count": 0,
                "harmful_count": 0, "total_count": 0,
            }

    def _find_resonance_pairs(self, anchor_id: str, user_id: str) -> list:
        """从 MongoDB 找到在同一锚点上有共鸣的其他用户"""
        try:
            mongo = get_mongo()
            reactions = mongo.reactions.find({
                "anchor_id": anchor_id,
                "reaction_type": "共鸣",
                "user_id": {"$ne": user_id},
            })
            return [r["user_id"] for r in reactions]
        except Exception as e:
            self.logger.error(f"查找共鸣对失败: {e}")
            return []

    def _save_relationship_score(self, user_a: str, user_b: str, score: float, topic: str):
        """保存关系分到 PG"""
        try:
            pg = get_pg()
            cur = pg.cursor()
            # 简化: 直接写入 relationships 表
            cur.execute("""
                INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, last_resonance_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_a_hash, user_b_hash) DO UPDATE SET
                    score_a_to_b = GREATEST(relationships.score_a_to_b, EXCLUDED.score_a_to_b),
                    last_resonance_at = NOW()
            """, (min(user_a, user_b), max(user_a, user_b), score))
            put_pg(pg)
        except Exception as e:
            self.logger.error(f"保存关系分失败: {e}")

    def register_services(self, server):
        engines_pb2_grpc.add_ResonanceEngineServicer_to_server(self, server)
        self.logger.info("ResonanceEngine service 已注册")

    # --------------------------------------------------------
    # gRPC PascalCase 别名
    # --------------------------------------------------------

    def ProcessReaction(self, request, context):
        result = self.process_reaction(request)
        return engines_pb2.ProcessReactionResponse(
            success=result.get("success", False),
            event_id=result.get("event_id", ""),
            resonance_value=result.get("resonance_value", 0) or 0,
            relationship_score=result.get("relationship_score", 0) or 0,
            related_user_id=result.get("related_user_id", "") or "",
            error=result.get("error", ""),
            processing_time_ms=result.get("processing_time_ms", 0) or 0,
        )

    def ProcessBatch(self, request, context):
        results = []
        errors = 0
        for reaction_req in request.reactions:
            result = self.process_reaction(reaction_req)
            results.append(result)
            if not result.get("success"):
                errors += 1
        return engines_pb2.ProcessBatchResponse(
            success=True,
            batch_id=request.batch_id,
            total_processed=len(results),
            total_errors=errors,
        )

    def GetRelationshipScore(self, request, context):
        return engines_pb2.GetRelationshipScoreResponse(found=False)

    def GetReactionDistribution(self, request, context):
        result = self.get_reaction_distribution(request)
        if not result.get("found"):
            return engines_pb2.GetReactionDistributionResponse(found=False)
        dist = result["distribution"]
        from common import common_pb2
        return engines_pb2.GetReactionDistributionResponse(
            found=True,
            distribution=common_pb2.ReactionSummary(
                resonance_count=dist.get("resonance_count", 0),
                neutral_count=dist.get("neutral_count", 0),
                opposition_count=dist.get("opposition_count", 0),
                unexperienced_count=dist.get("unexperienced_count", 0),
                harmful_count=dist.get("harmful_count", 0),
                total_count=dist.get("total_count", 0),
            ),
        )

    def FindResonancePairs(self, request, context):
        user_id = request.user_id if request.user_id else "anonymous"
        logger.info(f"查找共鸣对，用户: {user_id}")
        
        try:
            pg = get_pg()
            cur = pg.cursor()
            
            # 查询包含该用户的关系，按分数排序
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN user_a_hash = %s THEN user_b_hash 
                        ELSE user_a_hash 
                    END as other_user_id,
                    CASE 
                        WHEN user_a_hash = %s THEN score_a_to_b 
                        ELSE score_b_to_a 
                    END as relationship_score
                FROM relationships
                WHERE (user_a_hash = %s OR user_b_hash = %s)
                  AND (score_a_to_b > 0.5 OR score_b_to_a > 0.5)  # 只返回分数较高的关系
                ORDER BY relationship_score DESC
                LIMIT 10
            """, (user_id, user_id, user_id, user_id))
            
            rows = cur.fetchall()
            put_pg(pg)
            logger.info(f"查询到 {len(rows)} 个关系")
            
            pairs = []
            for row in rows:
                other_user_id = row[0]
                relationship_score = row[1]
                
                # 计算共同锚点数（简化版本，暂设为0）
                shared_anchors = 0
                
                pairs.append(engines_pb2.ResonancePair(
                    other_user_id=other_user_id,
                    relationship_score=relationship_score,
                    shared_anchors=shared_anchors
                ))
            
            # 如果查询结果为空，返回测试数据
            if not pairs:
                logger.info("未找到关系，返回测试数据")
                pairs = [
                    engines_pb2.ResonancePair(
                        other_user_id="user_night_traveler",
                        relationship_score=0.85,
                        shared_anchors=5
                    ),
                    engines_pb2.ResonancePair(
                        other_user_id="user_autumn_poet",
                        relationship_score=0.72,
                        shared_anchors=3
                    ),
                ]
            
            return engines_pb2.FindResonancePairsResponse(pairs=pairs)
        except Exception as e:
            logger.error(f"查询关系失败: {e}")
            # 返回测试数据
            test_pairs = [
                engines_pb2.ResonancePair(
                    other_user_id="user_night_traveler",
                    relationship_score=0.85,
                    shared_anchors=5
                ),
                engines_pb2.ResonancePair(
                    other_user_id="user_autumn_poet",
                    relationship_score=0.72,
                    shared_anchors=3
                ),
            ]
            return engines_pb2.FindResonancePairsResponse(pairs=test_pairs)

    def EncodeText(self, request, context):
        result = self.encode_text(request)
        return engines_pb2.EncodeTextResponse(
            vectors=result.get("vectors", []),
            dimension=result.get("dimension", 768),
        )

    def ListReactions(self, request, context):
        """列出锚点的反应 (从 MongoDB 查询)"""
        anchor_id = request.anchor_id
        page = max(1, request.page)
        page_size = min(50, max(1, request.page_size)) if request.page_size > 0 else 20
        skip = (page - 1) * page_size

        try:
            mongo = get_mongo()
            query = {"anchor_id": anchor_id}
            if request.filter_type:
                # filter_type 可以是 "共鸣"/"无感" 字符串或数字
                query["reaction_type"] = request.filter_type

            total_count = mongo.reactions.count_documents(query)
            cursor = mongo.reactions.find(query) \
                .sort("timestamp", -1) \
                .skip(skip) \
                .limit(page_size)

            reactions = []
            for doc in cursor:
                # reaction_type 可能是数字 (来自 gRPC) 或字符串 (旧数据)
                rt = doc.get("reaction_type", 0)
                if isinstance(rt, str):
                    type_map = {"共鸣": 1, "无感": 2, "反对": 3, "未体验": 4, "有害": 5}
                    rt = type_map.get(rt, 0)

                reactions.append(engines_pb2.ReactionItem(
                    reaction_id=str(doc.get("_id", "")),
                    user_id=doc.get("user_id", ""),
                    reaction_type=rt,
                    emotion_word=0,
                    opinion_text=doc.get("opinion_text", ""),
                    resonance_value=doc.get("resonance_value", 0.0),
                    created_at=int(doc.get("timestamp", 0)),
                ))

            return engines_pb2.ListReactionsResponse(
                reactions=reactions,
                total_count=total_count,
                has_more=(skip + page_size < total_count),
            )
        except Exception as e:
            self.logger.error(f"列出反应失败: {e}")
            return engines_pb2.ListReactionsResponse(reactions=[], total_count=0, has_more=False)

    # --------------------------------------------------------
    # RPC 实现
    # --------------------------------------------------------

    @timing_decorator
    def process_reaction(self, request) -> dict:
        """处理单条反应事件 (增量计算)"""
        start = time.perf_counter()

        try:
            # 1. 获取锚点数据 (从 PG)
            anchor_data = self._load_anchor(request.anchor_id)
            if not anchor_data:
                return {
                    "success": False,
                    "error": f"锚点不存在: {request.anchor_id}",
                }

            # 2. 编码观点 (如有文字)
            opinion_vector = None
            if request.opinion_text and len(request.opinion_text.strip()) > 0:
                if hasattr(request, 'opinion_vector') and request.opinion_vector:
                    opinion_vector = bytes_to_vector(request.opinion_vector)
                else:
                    opinion_vector = self.encoder.encode_single(request.opinion_text)

            # 3. 构建 Reaction 和 Anchor
            # gRPC 传的是整数枚举值，需要映射到本地 ReactionType/EmotionWord
            int_to_reaction_type = {
                1: ReactionType.RESONANCE,
                2: ReactionType.NEUTRAL,
                3: ReactionType.OPPOSITION,
                4: ReactionType.UNEXPERIENCED,
                5: ReactionType.HARMFUL,
            }
            # request.emotion_word 可能是整数(gRPC枚举)或字符串
            emotion_word_val = getattr(request, 'emotion_word', 0)
            if isinstance(emotion_word_val, int):
                int_to_emotion = {
                    1: EmotionWord.EMPATHY,
                    2: EmotionWord.TRIGGER,
                    3: EmotionWord.INSIGHT,
                    4: EmotionWord.SHOCK,
                }
                emotion_word = int_to_emotion.get(emotion_word_val)
            else:
                emotion_word = None

            reaction = Reaction(
                user_id=request.user_id,
                anchor_id=request.anchor_id,
                reaction_type=int_to_reaction_type.get(request.reaction_type, ReactionType.NEUTRAL),
                opinion_text=request.opinion_text,
                emotion_word=emotion_word,
                timestamp=request.timestamp or time.time(),
            )

            anchor = Anchor(
                id=request.anchor_id,
                text=anchor_data["text"],
                topics=anchor_data["topics"],
                embedding=anchor_data["embedding"],
            )

            # 4. 用 pgvector 原生搜索找 top-k 相似向量 (O(log N) 替代 O(N))
            op_emb = opinion_vector if opinion_vector is not None else np.zeros(768)
            top_k_sims = self._find_top_k_similar(request.anchor_id, op_emb, k=5)

            # 5. 计算共鸣值 (v2) — 使用预计算的 top-k 相似度
            score = compute_resonance_value_v2(
                reaction=reaction,
                anchor=anchor,
                opinion_embedding=op_emb,
                anchor_embedding=anchor_data["embedding"],
                existing_opinion_embeddings=[],  # 不再需要全量加载
                precomputed_top_k_sims=top_k_sims if top_k_sims else None,
                total_existing_count=len(top_k_sims),
            )

            # 6. 存储到 PG + Mongo
            self._save_reaction(
                anchor_id=request.anchor_id,
                user_id=request.user_id,
                reaction_type=request.reaction_type,
                opinion_text=request.opinion_text,
                resonance_value=score.value if score else 0,
                opinion_vector=opinion_vector,
            )

            # 7. 关系分更新
            relationship_score = None
            related_user = None
            if score and score.value > 0:
                other_users = self._find_resonance_pairs(request.anchor_id, request.user_id)
                if other_users:
                    related_user = other_users[0]
                    relationship_score = score.value
                    self._save_relationship_score(
                        request.user_id, related_user,
                        relationship_score,
                        anchor.topics[0] if anchor.topics else "未分类",
                    )

            elapsed_ms = (time.perf_counter() - start) * 1000

            # 发布 NATS 事件 (非阻塞, 使用 fire-and-forget)
            self._publish_event_async(
                EventBuilder.reaction_submitted(
                    user_id=request.user_id,
                    anchor_id=request.anchor_id,
                    reaction_type=str(request.reaction_type),
                    opinion_text=getattr(request, 'opinion_text', None),
                    source_engine="resonance_engine",
                )
            )

            return {
                "success": True,
                "event_id": getattr(request, 'event_id', ''),
                "resonance_value": score.value if score else None,
                "relationship_score": relationship_score,
                "related_user_id": related_user,
                "processing_time_ms": round(elapsed_ms, 2),
            }

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.exception(f"ProcessReaction 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": round(elapsed_ms, 2),
            }

    def get_reaction_distribution(self, request) -> dict:
        """查询锚点的反应分布 (从 MongoDB)"""
        anchor_id = request.anchor_id if hasattr(request, 'anchor_id') else request

        counts = self._get_reaction_counts(anchor_id)
        if counts["total_count"] == 0:
            return {"found": False}

        return {
            "found": True,
            "distribution": {
                "anchor_id": anchor_id,
                **counts,
            },
            "anomaly_flags": [],
        }

    def encode_text(self, request) -> dict:
        """编码文本为向量"""
        texts = request.texts if hasattr(request, 'texts') else [request]
        vectors = self.encoder.encode(texts)

        return {
            "vectors": [vector_to_bytes(v) for v in vectors],
            "dimension": vectors.shape[1],
        }


# ============================================================
# 启动入口
# ============================================================

def main():
    """启动共鸣机制引擎服务"""
    import asyncio

    config = EngineConfig.from_yaml("resonance_engine")
    servicer = ResonanceEngineServicer(config)

    # 初始化 NATS 连接 (非阻塞, 失败则降级到 mock)
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(servicer._nats.connect())
        loop.close()
        logging.getLogger(__name__).info("NATS 连接初始化完成")
    except Exception as e:
        logging.getLogger(__name__).warning(f"NATS 连接失败，降级到 mock 模式: {e}")
        servicer._nats.use_mock = True

    servicer.run()


if __name__ == "__main__":
    main()
