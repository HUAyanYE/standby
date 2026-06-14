"""
锚点生成引擎 — gRPC 服务实现

职责:
1. 锚点质量评估
2. 锚点元数据管理 (PostgreSQL)
3. 锚点语义向量管理 (pgvector)
4. 锚点重现调度

数据层:
- PostgreSQL: anchor_vectors (向量 + 元数据), 锚点生成日志
"""

import logging
import sys
import time
import uuid
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

from standby_common.base import (
    EngineConfig, EngineServicer, timing_decorator,
    vector_to_bytes, bytes_to_vector,
)
from standby_common.db import get_pg, put_pg
from standby_common.db.anchor import get_anchor_meta, get_anchor_meta_batch, save_anchor_meta, count_reactions_batch

# NATS 事件
from standby_common.events import NATSClient, EventBuilder

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
        models_dir = Path(__file__).parent.parent / "standby_common" / "models"
        from standby_common.encoders.text_encoder import TextEncoder
        self.encoder = TextEncoder(model_name=str(models_dir / "bge-base-zh-v1.5"))

        # 内存缓存 (从 PG 加载)
        self._anchors_cache: dict[str, dict] = {}

        # NATS 事件客户端
        import os
        nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
        self._nats = NATSClient(nats_url=nats_url, engine_name="anchor_engine")

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

            if isinstance(row[1], str):
                embedding = np.array([float(x) for x in row[1].strip('[]').split(',')], dtype=np.float32)
            elif row[1] is not None:
                embedding = np.frombuffer(bytes(row[1]), dtype=np.float32).reshape(768)
            else:
                embedding = None

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
        """保存锚点到 PostgreSQL"""
        try:
            # PG: 向量
            pg = get_pg()
            cur = pg.cursor()
            cur.execute("""
                INSERT INTO anchor_vectors (anchor_id, vector)
                VALUES (%s, %s::vector)
                ON CONFLICT (anchor_id) DO UPDATE SET vector = EXCLUDED.vector
            """, (anchor_id, str(embedding.tolist())))
            pg.commit(); put_pg(pg)

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

    def _publish_event_async(self, event):
        """非阻塞发布 NATS 事件 (使用持久化事件循环)"""
        import asyncio
        import threading

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
            future.add_done_callback(
                lambda f: logger.warning(f"NATS 发布失败: {f.exception()}")
                if f.exception() else None
            )
        except Exception as e:
            logger.warning(f"NATS 事件发布调度失败: {e}")

    def _run_nats_loop(self):
        """NATS 事件循环后台线程"""
        import asyncio
        asyncio.set_event_loop(self._nats_loop)
        self._nats_loop.run_forever()

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
                anchor_id=anchor_id,
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
            text=result.get("text", ""),
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
        """列出锚点 (分页查询 PostgreSQL)"""
        page = max(1, request.page)
        page_size = min(50, max(1, request.page_size)) if request.page_size > 0 else 20
        offset = (page - 1) * page_size

        pg = get_pg()
        cur = pg.cursor()

        # 查总数
        if request.topic_filter:
            # 批量获取元数据再过滤 (替代 N+1 逐个查询)
            cur.execute("SELECT anchor_id, created_at FROM anchor_vectors ORDER BY created_at DESC")
            all_rows = cur.fetchall()
            put_pg(pg)

            # 批量获取所有元数据
            all_ids = [row[0] for row in all_rows]
            meta_map = get_anchor_meta_batch(all_ids)

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

        # 批量获取元数据和反应数 (替代 N+1 逐个查询)
        anchor_ids = [row[0] for row in page_rows]
        meta_map = get_anchor_meta_batch(anchor_ids)

        # 批量获取反应数
        reaction_counts = count_reactions_batch(anchor_ids)

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
            
            anchors.append(common_pb2.AnchorSummary(
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

    @timing_decorator
    def evaluate_anchor_quality(self, request) -> dict:
        """评估锚点质量 (规则版)

        新增：有形事物检测 — 心物必须指向具体的事物/场景/经历
        """
        text = request.text if hasattr(request, 'text') else request.get("text", "")

        length = len(text)
        completeness = min(1.0, length / 200)

        detail_markers = ["有一次", "记得", "那天", "具体", "比如", "例如"]
        specificity = min(1.0, 0.5 + 0.1 * sum(1 for m in detail_markers if m in text))

        auth_markers = ["我", "我的", "自己", "亲身"]
        authenticity = min(1.0, 0.4 + 0.15 * sum(1 for m in auth_markers if m in text))

        thought_markers = ["？", "也许", "是否", "如果", "……", "不知道"]
        thought_space = min(1.0, 0.4 + 0.12 * sum(1 for m in thought_markers if m in text))

        # 有形事物检测 — 心物必须指向具体的事物/场景/经历
        tangible_score = self._compute_tangible_score(text)

        overall = (completeness * 0.25 + specificity * 0.25 +
                   authenticity * 0.2 + thought_space * 0.15 +
                   tangible_score * 0.15)

        quality = {
            "completeness": round(completeness, 3),
            "specificity": round(specificity, 3),
            "authenticity": round(authenticity, 3),
            "thought_space": round(thought_space, 3),
            "tangible": round(tangible_score, 3),
            "overall": round(overall, 3),
        }

        return {
            "quality": quality,
            "passes_threshold": overall >= 0.7,
            "feedback": f"综合评分 {overall:.2f}" + (" (通过)" if overall >= 0.7 else " (未达阈值 0.7)"),
        }

    def _compute_tangible_score(self, text: str) -> float:
        """计算有形事物分数

        心物（Seedstone）必须指向具体的事物/场景/经历，而非抽象概念。

        检测维度：
        1. 具体名词（物体、地点、人物）
        2. 感官描述（视觉、听觉、触觉、嗅觉、味觉）
        3. 时间/空间标记
        4. 抽象概念惩罚
        """
        if not text:
            return 0.0

        score = 0.5  # 基础分

        # 1. 具体名词
        concrete_nouns = [
            # 物体
            '地铁', '公交', '火车', '飞机', '船', '车', '自行车',
            '手机', '电脑', '书', '信', '照片', '音乐', '电影',
            '咖啡', '茶', '酒', '烟', '食物', '衣服', '鞋子',
            # 地点
            '家', '学校', '公司', '公园', '医院', '车站', '机场',
            '图书馆', '咖啡馆', '餐厅', '酒吧', '电影院', '商场',
            '海边', '山上', '河边', '湖边', '森林', '沙漠',
            # 人物
            '父亲', '母亲', '爷爷', '奶奶', '外公', '外婆',
            '老师', '朋友', '同学', '同事', '恋人', '妻子', '丈夫',
        ]
        concrete_count = sum(1 for noun in concrete_nouns if noun in text)
        score += min(0.3, concrete_count * 0.1)

        # 2. 感官描述
        sensory_words = [
            # 视觉
            '看到', '看着', '望着', '盯着', '看着', '明亮', '黑暗', '红色', '蓝色',
            # 听觉
            '听到', '听着', '声音', '音乐', '噪音', '安静', '喧闹',
            # 触觉
            '触摸', '温暖', '冰冷', '柔软', '坚硬', '湿润', '干燥',
            # 嗅觉
            '闻到', '香味', '臭味', '清新', '刺鼻',
            # 味觉
            '尝到', '甜', '苦', '酸', '辣', '咸',
        ]
        sensory_count = sum(1 for word in sensory_words if word in text)
        score += min(0.2, sensory_count * 0.05)

        # 3. 时间/空间标记
        time_space_markers = [
            '年', '月', '日', '时', '分', '早上', '中午', '下午', '晚上',
            '凌晨', '深夜', '傍晚', '黄昏', '黎明',
            '这里', '那里', '上面', '下面', '旁边', '对面', '里面', '外面',
        ]
        marker_count = sum(1 for marker in time_space_markers if marker in text)
        score += min(0.2, marker_count * 0.05)

        # 4. 抽象概念惩罚
        abstract_words = [
            '人生', '命运', '哲学', '意义', '价值', '本质', '真理',
            '自由', '平等', '正义', '道德', '伦理', '信仰', '灵魂',
        ]
        abstract_count = sum(1 for word in abstract_words if word in text)
        score -= min(0.2, abstract_count * 0.05)

        return max(0.0, min(1.0, score))

    @timing_decorator
    def get_anchor_metadata(self, request) -> dict:
        """获取锚点元数据 (从 PostgreSQL)"""
        anchor_id = request.anchor_id if hasattr(request, 'anchor_id') else request

        anchor = self._load_anchor(anchor_id)
        if not anchor:
            return {"found": False}

        return {
            "found": True,
            "anchor_id": anchor_id,
            "text": anchor.get("text", ""),
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
        """注册新锚点 (写入 PostgreSQL)"""
        embedding = self.encoder.encode_single(text)
        quality = self.evaluate_anchor_quality(type('R', (), {'text': text})())
        quality_score = quality["quality"]["overall"]

        self._save_anchor(anchor_id, text, topics, embedding, quality_score, anchor_type)

        # 发布 NATS 事件
        self._publish_event_async(
            EventBuilder.anchor_created(
                anchor_id=anchor_id,
                anchor_type=anchor_type,
                topics=topics,
                quality_score=quality_score,
                text=text,
            )
        )

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
            anchor_ids = [row[0] for row in rows]
            meta_map = get_anchor_meta_batch(anchor_ids)
            candidates = []
            for row in rows:
                aid = row[0]
                created_ts = int(row[1].timestamp()) if row[1] else 0
                meta = meta_map.get(aid)
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

    @timing_decorator
    def auto_identify_seedstone(self, text: str, topics: list[str]) -> dict:
        """自动识别心物（Seedstone）

        心物是用户表达的载体，系统自动识别用户内容是否可以成为心物。

        识别条件：
        1. 指向具体的事物/场景/经历（有形性）
        2. 包含情感表达（情感性）
        3. 有足够长度（完整性）
        4. 有话题标签（可聚合性）

        返回：
        - is_seedstone: 是否可以成为心物
        - confidence: 置信度 0-1
        - reason: 识别原因
        """
        if not text or len(text.strip()) < 10:
            return {
                "is_seedstone": False,
                "confidence": 0.0,
                "reason": "文本太短",
            }

        # 1. 有形性检测
        tangible_score = self._compute_tangible_score(text)

        # 2. 情感性检测
        emotion_words = ['感动', '触动', '感慨', '难过', '开心', '激动', '怀念', '思念',
                        '温暖', '心酸', '欣慰', '释然', '顿悟', '觉醒', '震撼', '崩溃',
                        '泪流满面', '无法呼吸', '心碎', '绝望', '狂喜', '热泪盈眶']
        has_emotion = any(word in text for word in emotion_words)

        # 3. 完整性检测
        is_complete = len(text) >= 20

        # 4. 可聚合性检测
        has_topics = len(topics) > 0

        # 计算置信度
        confidence = 0.0
        reasons = []

        if tangible_score >= 0.6:
            confidence += 0.4
            reasons.append("指向具体事物")
        elif tangible_score >= 0.4:
            confidence += 0.2
            reasons.append("有一定具体性")

        if has_emotion:
            confidence += 0.3
            reasons.append("包含情感表达")

        if is_complete:
            confidence += 0.2
            reasons.append("内容完整")

        if has_topics:
            confidence += 0.1
            reasons.append("有话题标签")

        is_seedstone = confidence >= 0.5

        return {
            "is_seedstone": is_seedstone,
            "confidence": round(confidence, 3),
            "reason": "、".join(reasons) if reasons else "不满足心物条件",
            "tangible_score": round(tangible_score, 3),
            "has_emotion": has_emotion,
        }

    @timing_decorator
    def aggregate_opinions_to_seedstone(
        self,
        anchor_id: str,
        opinions: list[dict],
        min_opinions: int = 3,
        similarity_threshold: float = 0.7,
    ) -> dict:
        """将同主题观点聚合为新心物

        当多个用户对同一锚点表达了相似的感受时，系统可以将这些观点
        聚合为一个新的心物，形成"感受链"。

        聚合条件：
        1. 至少有 min_opinions 个观点
        2. 观点之间的语义相似度 >= similarity_threshold
        3. 观点都指向同一主题

        返回：
        - can_aggregate: 是否可以聚合
        - aggregated_text: 聚合后的心物文本
        - source_opinions: 来源观点列表
        - similarity_score: 平均相似度
        """
        if len(opinions) < min_opinions:
            return {
                "can_aggregate": False,
                "reason": f"观点数量不足（需要至少 {min_opinions} 个）",
            }

        # 提取观点文本
        opinion_texts = [op.get("text", "") for op in opinions if op.get("text")]
        if len(opinion_texts) < min_opinions:
            return {
                "can_aggregate": False,
                "reason": "有效观点数量不足",
            }

        # 编码观点
        try:
            embeddings = self.encoder.encode(opinion_texts)
        except Exception as e:
            logger.error(f"编码观点失败: {e}")
            return {
                "can_aggregate": False,
                "reason": "编码失败",
            }

        # 计算观点之间的平均相似度
        n = len(embeddings)
        similarity_sum = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                sim = float(np.dot(embeddings[i], embeddings[j]))
                similarity_sum += sim
                count += 1

        avg_similarity = similarity_sum / count if count > 0 else 0.0

        if avg_similarity < similarity_threshold:
            return {
                "can_aggregate": False,
                "reason": f"观点相似度不足（{avg_similarity:.2f} < {similarity_threshold}）",
                "avg_similarity": round(avg_similarity, 3),
            }

        # 找到最具有代表性的观点（与其他观点平均相似度最高的）
        representative_idx = 0
        best_avg_sim = 0.0
        for i in range(n):
            sims = []
            for j in range(n):
                if i != j:
                    sims.append(float(np.dot(embeddings[i], embeddings[j])))
            avg_sim = sum(sims) / len(sims) if sims else 0.0
            if avg_sim > best_avg_sim:
                best_avg_sim = avg_sim
                representative_idx = i

        representative_text = opinion_texts[representative_idx]

        # 构建聚合文本
        aggregated_text = f"关于这个话题，大家的感受相似：\n\n{representative_text}"

        return {
            "can_aggregate": True,
            "aggregated_text": aggregated_text,
            "source_opinions": opinion_texts,
            "representative_opinion": representative_text,
            "similarity_score": round(avg_similarity, 3),
            "opinion_count": len(opinion_texts),
        }


    def GetGroupMemory(self, request, context):
        """获取群体记忆 (重现时展示)

        根据 docs/3 技术架构设计，返回:
        - user_opinion_text: 用户当时的感想
        - resonance_count_at_time: 当时的共鸣人数
        - emotion_words: 当时的情绪词列表
        - group_evolution: 群体对话题理解的演变摘要
        """
        anchor_id = request.anchor_id
        user_id = request.user_id

        try:
            from standby_common.db import get_pg, put_pg
            pg = get_pg()
            cur = pg.cursor()

            # 1. 获取用户的感想
            cur.execute("""
                SELECT text_content FROM reactions
                WHERE anchor_id = %s AND user_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (anchor_id, user_id))
            user_row = cur.fetchone()
            user_opinion_text = user_row[0] if user_row and user_row[0] else ""

            # 2. 统计共鸣数量
            cur.execute("""
                SELECT COUNT(*) FROM reactions
                WHERE anchor_id = %s AND reaction_type = '共鸣'
            """, (anchor_id,))
            resonance_count = cur.fetchone()[0] or 0

            # 3. 获取情绪词
            cur.execute("""
                SELECT DISTINCT emotion_word FROM reactions
                WHERE anchor_id = %s AND emotion_word IS NOT NULL AND emotion_word != ''
            """, (anchor_id,))
            emotion_words = [row[0] for row in cur.fetchall() if row[0]]

            # 4. 群体演化摘要: 查询不同时间段的反应分布
            cur.execute("""
                SELECT
                    reaction_type,
                    COUNT(*) as cnt,
                    MIN(created_at) as first_at,
                    MAX(created_at) as last_at
                FROM reactions
                WHERE anchor_id = %s
                GROUP BY reaction_type
                ORDER BY cnt DESC
            """, (anchor_id,))
            type_rows = cur.fetchall()

            put_pg(pg)

            # 构建演化摘要
            total = sum(r[1] for r in type_rows) if type_rows else 0
            if total > 0:
                parts = []
                for row in type_rows:
                    parts.append(f"{row[0]}: {row[1]}人")
                group_evolution = f"共 {total} 条反应，分布: " + "、".join(parts)
            else:
                group_evolution = "暂无群体反应数据"

            return engines_pb2.GetGroupMemoryResponse(
                user_opinion_text=user_opinion_text,
                resonance_count_at_time=resonance_count,
                emotion_words=emotion_words,
                group_evolution=group_evolution,
            )
        except Exception as e:
            logger.error(f"获取群体记忆失败: {e}")
            return engines_pb2.GetGroupMemoryResponse(
                user_opinion_text="",
                resonance_count_at_time=0,
                emotion_words=[],
                group_evolution="获取失败",
            )

    def GetFeelingChain(self, request, context):
        """获取感受链 — 返回子心物列表（每条感受是独立心物）"""
        anchor_id = request.anchor_id

        try:
            from standby_common.db_queries import get_feeling_chain_anchors
            child_anchors = get_feeling_chain_anchors(anchor_id)

            nodes = []
            for item in child_anchors:
                nodes.append(engines_pb2.FeelingChainNode(
                    reaction_id=item["anchor_id"],
                    user_id=item.get("user_id", ""),
                    display_name="",
                    avatar_seed="",
                    text_content=item.get("text_content", ""),
                    emotion_word=item.get("emotion_word", ""),
                    parent_reaction_id=anchor_id,
                    depth=0,
                    created_at=int(item.get("created_at", 0)),
                ))

            return engines_pb2.GetFeelingChainResponse(
                found=len(nodes) > 0,
                anchor_id=anchor_id,
                nodes=nodes,
            )
        except Exception as e:
            logger.error(f"获取感受链失败: {e}")
            return engines_pb2.GetFeelingChainResponse(
                found=False,
                anchor_id=anchor_id,
                nodes=[],
            )


def main():
    config = EngineConfig.from_yaml("anchor_engine")
    servicer = AnchorEngineServicer(config)

    # 初始化 NATS 连接
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(servicer._nats.connect())
        loop.close()
        logger.info("NATS 连接初始化完成")
    except Exception as e:
        logger.warning(f"NATS 连接失败，降级到 mock 模式: {e}")
        servicer._nats.use_mock = True

    servicer.run()


if __name__ == "__main__":
    main()
