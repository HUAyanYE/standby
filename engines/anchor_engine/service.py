"""
锚点生成引擎 — gRPC 服务实现

职责:
1. 锚点质量评估
2. 锚点元数据管理 (PostgreSQL)
3. 锚点语义向量管理 (pgvector)
4. 锚点重现调度

数据层:
- PostgreSQL: anchor_vectors (向量 + 元数据)
- MongoDB: 锚点生成日志
"""

import logging
import sys
import time
import uuid
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from shared.engine_base import (
    EngineConfig, EngineServicer, timing_decorator,
    vector_to_bytes, bytes_to_vector,
)
from shared.db import get_pg, put_pg
from shared.pg_compat import get_anchor_meta, get_anchor_meta_batch, save_anchor_meta, count_reactions_batch

# gRPC 生成代码
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "proto" / "generated" / "python"))
from engines import engines_pb2_grpc
from engines import engines_pb2
from common import common_pb2


class AnchorEngineServicer(EngineServicer):
    """锚点生成引擎 gRPC 服务 — PostgreSQL"""

    def __init__(self, config: EngineConfig):
        super().__init__(config)

        # 加载编码器
        models_dir = Path(__file__).parent.parent / "shared" / "models"
        from shared.encoders.text_encoder import TextEncoder
        self.encoder = TextEncoder(model_name=str(models_dir / "bge-base-zh-v1.5"))

        # 内存缓存 (从 PG 加载)
        self._anchors_cache: dict[str, dict] = {}

    def _load_anchor(self, anchor_id: str) -> dict | None:
        """从 PG 加载锚点"""
        if anchor_id in self._anchors_cache:
            return self._anchors_cache[anchor_id]

        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT anchor_id, vector, created_at
                FROM anchor_vectors
                WHERE anchor_id = %s
            """, (anchor_id,))
            row = cur.fetchone()
            put_pg(pg)
            if not row:
                return None

            embedding = np.frombuffer(bytes(row[1]), dtype=np.float32).reshape(768) if row[1] else None

            # 从 PostgreSQL 获取元数据
            meta = get_anchor_meta(anchor_id)

            anchor_data = {
                "text": meta.get("text", "") if meta else "",
                "topics": meta.get("topics", []) if meta else [],
                "anchor_type": meta.get("anchor_type", "platform_initial") if meta else "platform_initial",
                "embedding": embedding,
                "quality_score": meta.get("quality_score", 0.0) if meta else 0.0,
                "created_at": int(row[2].timestamp()) if row[2] else 0,
            }
            self._anchors_cache[anchor_id] = anchor_data
            return anchor_data
        except Exception as e:
            logger.error(f"加载锚点失败: {e}")
            return None

    def _save_anchor(self, anchor_id: str, text: str, topics: list,
                     embedding: np.ndarray, quality_score: float,
                     anchor_type: str = "platform_initial"):
        """保存锚点到 PG + Mongo"""
        try:
            # PG: 向量
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                INSERT INTO anchor_vectors (anchor_id, vector)
                VALUES (%s, %s::vector)
                ON CONFLICT (anchor_id) DO UPDATE SET vector = EXCLUDED.vector
            """, (anchor_id, str(embedding.tolist())))
            put_pg(pg)

            # PostgreSQL: 元数据
            save_anchor_meta(anchor_id, text, topics, quality_score, anchor_type)

            # 更新缓存
            self._anchors_cache[anchor_id] = {
                "text": text, "topics": topics,
                "anchor_type": anchor_type,
                "embedding": embedding,
                "quality_score": quality_score,
                "created_at": int(time.time()),
            }
        except Exception as e:
            logger.error(f"保存锚点失败: {e}")

    def register_services(self, server):
        engines_pb2_grpc.add_AnchorEngineServicer_to_server(self, server)
        logger.info("AnchorEngine service 已注册")

    # --------------------------------------------------------
    # gRPC PascalCase 别名
    # --------------------------------------------------------

    def GenerateAnchor(self, request, context):
        """生成锚点 (从请求数据注册)"""
        texts = list(request.source_texts)
        topics = list(request.topic_hints) if request.topic_hints else []
        anchor_id = f"a_{uuid.uuid4().hex[:8]}"
        if texts:
            result = self.register_anchor(anchor_id, texts[0], topics)
            anchor_obj = common_pb2.Anchor(
                anchor_id=anchor_id,
                text=texts[0],
                topics=topics,
            )
            return engines_pb2.GenerateAnchorResponse(
                success=True,
                anchor=anchor_obj,
                quality_score=result.get("quality", {}).get("overall", 0),
            )
        return engines_pb2.GenerateAnchorResponse(success=False, rejection_reason="无源文本")

    def EvaluateAnchorQuality(self, request, context):
        result = self.evaluate_anchor_quality(request)
        q = result.get("quality", {})
        return engines_pb2.EvaluateAnchorQualityResponse(
            quality=common_pb2.AnchorQuality(
                completeness=q.get("completeness", 0),
                specificity=q.get("specificity", 0),
                authenticity=q.get("authenticity", 0),
                thought_space=q.get("thought_space", 0),
                overall=q.get("overall", 0),
            ),
            passes_threshold=result.get("passes_threshold", False),
            feedback=result.get("feedback", ""),
        )

    def GetAnchorMetadata(self, request, context):
        result = self.get_anchor_metadata(request)
        if not result.get("found"):
            return engines_pb2.GetAnchorMetadataResponse(found=False)
        return engines_pb2.GetAnchorMetadataResponse(
            found=True,
            anchor_id=result.get("anchor_id", ""),
            topics=result.get("topics", []),
            quality_score=result.get("quality_score", 0),
            created_at=result.get("created_at", 0),
        )

    def GetAnchorVector(self, request, context):
        result = self.get_anchor_vector(request)
        if not result.get("found"):
            return engines_pb2.GetAnchorVectorResponse(found=False)
        return engines_pb2.GetAnchorVectorResponse(
            found=True,
            vector=result.get("vector", b""),
            dimension=result.get("dimension", 0),
        )

    def ListAnchors(self, request, context):
        """列出锚点 (分页查询 PG + Mongo)"""
        page = max(1, request.page)
        page_size = min(50, max(1, request.page_size)) if request.page_size > 0 else 20
        offset = (page - 1) * page_size

        try:
            pg = get_pg()
            cur = pg.cursor()

            # 查总数
            if request.topic_filter:
                # 批量获取元数据再过滤 (替代 N+1 逐个查询)
                cur.execute("SELECT anchor_id, created_at FROM anchor_vectors ORDER BY created_at DESC")
                all_rows = cur.fetchall()
                put_pg(pg)
                mongo = get_mongo()

                # 批量获取所有元数据
                all_ids = [row[0] for row in all_rows]
                meta_list = list(mongo.anchor_metadata.find({"anchor_id": {"$in": all_ids}}))
                meta_map = {m["anchor_id"]: m for m in meta_list}

                filtered = []
                for row in all_rows:
                    aid = row[0]
                    meta = meta_map.get(aid)
                    if meta and request.topic_filter in meta.get("topics", []):
                        filtered.append((aid, row[1], meta))
                total_count = len(filtered)
                page_rows = filtered[offset:offset + page_size]
            else:
                cur.execute("SELECT COUNT(*) FROM anchor_vectors")
                total_count = cur.fetchone()[0]
                cur.execute("""
                    SELECT anchor_id, created_at FROM anchor_vectors
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (page_size, offset))
                page_rows = [(r[0], r[1], None) for r in cur.fetchall()]

            mongo = get_mongo()

            # 批量获取元数据和反应数 (替代 N+1 逐个查询)
            anchor_ids = [row[0] for row in page_rows]
            meta_list = list(mongo.anchor_metadata.find({"anchor_id": {"$in": anchor_ids}}))
            meta_map = {m["anchor_id"]: m for m in meta_list}

            # 批量获取反应数 (aggregation pipeline)
            reaction_counts = {}
            try:
                pipeline = [
                    {"$match": {"anchor_id": {"$in": anchor_ids}}},
                    {"$group": {"_id": "$anchor_id", "count": {"$sum": 1}}}
                ]
                for r in mongo.reactions.aggregate(pipeline):
                    reaction_counts[r["_id"]] = r["count"]
            except Exception:
                pass  # 如果聚合失败，reaction_count 默认为 0

            anchors = []
            for row in page_rows:
                aid = row[0]
                created_ts = int(row[1].timestamp()) if row[1] else 0
                meta = row[2] if row[2] else meta_map.get(aid)

                # 跳过没有元数据的锚点
                if meta is None:
                    logger.debug(f"锚点 {aid} 没有元数据，跳过")
                    continue
                
                # 从批量结果获取反应数
                reaction_count = reaction_counts.get(aid, 0)

                # 处理text字段
                text_content = meta.get("text", "")
                if not text_content:
                    logger.debug(f"锚点 {aid} 的text字段为空，跳过")
                    continue
                
                text = text_content[:100]
                logger.debug(f"锚点 {aid} 的text字段存在，长度: {len(text_content)}")
                
                anchors.append(engines_pb2.AnchorSummary(
                    anchor_id=aid,
                    text=text,
                    topics=meta.get("topics", []),
                    quality_score=meta.get("quality_score", 0.0),
                    reaction_count=reaction_count,
                    created_at=created_ts,
                ))

            return engines_pb2.ListAnchorsResponse(
                anchors=anchors,
                total_count=total_count,
                has_more=(offset + page_size < total_count),
            )
        except Exception as e:
            logger.error(f"列出锚点失败: {e}")
            return engines_pb2.ListAnchorsResponse(anchors=[], total_count=0, has_more=False)

    @timing_decorator
    def evaluate_anchor_quality(self, request) -> dict:
        """评估锚点质量 (规则版)"""
        text = request.text if hasattr(request, 'text') else request.get("text", "")

        length = len(text)
        completeness = min(1.0, length / 200)

        detail_markers = ["有一次", "记得", "那天", "具体", "比如", "例如"]
        specificity = min(1.0, 0.5 + 0.1 * sum(1 for m in detail_markers if m in text))

        auth_markers = ["我", "我的", "自己", "亲身"]
        authenticity = min(1.0, 0.4 + 0.15 * sum(1 for m in auth_markers if m in text))

        thought_markers = ["？", "也许", "是否", "如果", "……", "不知道"]
        thought_space = min(1.0, 0.4 + 0.12 * sum(1 for m in thought_markers if m in text))

        overall = (completeness * 0.3 + specificity * 0.25 +
                   authenticity * 0.25 + thought_space * 0.2)

        quality = {
            "completeness": round(completeness, 3),
            "specificity": round(specificity, 3),
            "authenticity": round(authenticity, 3),
            "thought_space": round(thought_space, 3),
            "overall": round(overall, 3),
        }

        return {
            "quality": quality,
            "passes_threshold": overall >= 0.7,
            "feedback": f"综合评分 {overall:.2f}" + (" (通过)" if overall >= 0.7 else " (未达阈值 0.7)"),
        }

    @timing_decorator
    def get_anchor_metadata(self, request) -> dict:
        """获取锚点元数据 (从 PG/Mongo)"""
        anchor_id = request.anchor_id if hasattr(request, 'anchor_id') else request

        anchor = self._load_anchor(anchor_id)
        if not anchor:
            return {"found": False}

        return {
            "found": True,
            "anchor_id": anchor_id,
            "topics": anchor.get("topics", []),
            "anchor_type": anchor.get("anchor_type", "platform_initial"),
            "quality_score": anchor.get("quality_score", 0.0),
            "created_at": anchor.get("created_at", 0),
        }

    @timing_decorator
    def get_anchor_vector(self, request) -> dict:
        """获取锚点语义向量 (从 PG)"""
        anchor_id = request.anchor_id if hasattr(request, 'anchor_id') else request

        anchor = self._load_anchor(anchor_id)
        if not anchor or anchor.get("embedding") is None:
            return {"found": False}

        emb = anchor["embedding"]
        return {
            "found": True,
            "vector": vector_to_bytes(emb),
            "dimension": emb.shape[0],
        }

    def register_anchor(self, anchor_id: str, text: str, topics: list,
                        anchor_type: str = "platform_initial") -> dict:
        """注册新锚点 (写入 PG + Mongo)"""
        embedding = self.encoder.encode_single(text)
        quality = self.evaluate_anchor_quality(type('R', (), {'text': text})())
        quality_score = quality["quality"]["overall"]

        self._save_anchor(anchor_id, text, topics, embedding, quality_score, anchor_type)

        logger.info(f"注册锚点: {anchor_id} (质量={quality_score:.2f})")

        return {
            "anchor_id": anchor_id,
            "quality": quality["quality"],
            "vector_dimension": embedding.shape[0],
        }

    def get_replay_anchors(self, request) -> dict:
        """获取重现锚点 (从 PG 查询)"""
        top_k = request.top_k if hasattr(request, 'top_k') else (request.get("top_k", 5) if isinstance(request, dict) else 5)
        current_ts = time.time()

        import datetime
        month = datetime.datetime.now().month

        if month in (3, 4, 5):
            season_keywords = ["春天", "花开", "新生", "希望"]
        elif month in (6, 7, 8):
            season_keywords = ["夏天", "毕业", "旅行", "海边"]
        elif month in (9, 10, 11):
            season_keywords = ["秋天", "落叶", "收获", "中秋"]
        else:
            season_keywords = ["冬天", "雪", "新年", "春节"]

        try:
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                SELECT anchor_id, created_at
                FROM anchor_vectors
                WHERE created_at < NOW() - INTERVAL '7 days'
                ORDER BY created_at DESC
                LIMIT 100
            """)
            rows = cur.fetchall()
            put_pg(pg)

            # 获取元数据
            mongo = get_mongo()
            candidates = []
            for row in rows:
                aid = row[0]
                created_ts = int(row[1].timestamp()) if row[1] else 0
                meta = mongo.anchor_metadata.find_one({"anchor_id": aid})
                if not meta:
                    continue

                topics = meta.get("topics", [])
                season_match = any(kw in " ".join(topics) for kw in season_keywords)
                days_since = (current_ts - created_ts) / 86400
                decay = 1.0 - 0.5 ** (days_since / 30.0)
                trigger_score = decay * (1.5 if season_match else 1.0)

                candidates.append({
                    "anchor_id": aid,
                    "title": meta.get("text", "")[:50],
                    "topics": topics,
                    "trigger_type": "seasonal" if season_match else "classic_cycle",
                    "trigger_score": trigger_score,
                })

            candidates.sort(key=lambda x: x["trigger_score"], reverse=True)
            return {"anchors": candidates[:top_k]}
        except Exception as e:
            logger.error(f"获取重现锚点失败: {e}")
            return {"anchors": []}


def main():
    config = EngineConfig.from_yaml("anchor_engine")
    servicer = AnchorEngineServicer(config)
    servicer.run()


if __name__ == "__main__":
    main()
