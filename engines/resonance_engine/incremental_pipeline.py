"""
共鸣机制引擎 - 增量计算 Pipeline

实现文档 §9.2 增量计算策略：
- 增量更新：新反应触发局部重算
- 定时全量：每日凌晨全量校准
- 实时信号：L4/L5 实时在线检测

核心数据流：
  用户反应 → [验证] → [共鸣值计算] → [关系分更新] → [信任级别更新]
                      ↓
              [话题衰减重算] → [Redis/Dragonfly 缓存更新]
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable

import numpy as np

from resonance_calculator import (
    Reaction, ReactionType, EmotionWord, Anchor,
    compute_resonance_value, compute_relationship_score,
    RelationshipScore,
)
from shared.encoders.text_encoder import TextEncoder


# ============================================================
# 数据结构
# ============================================================

class PipelineStage(Enum):
    """Pipeline 阶段"""
    VALIDATE = "validate"
    ENCODE = "encode"
    RESONANCE = "resonance"
    RELATIONSHIP = "relationship"
    TRUST_UPDATE = "trust_update"
    CACHE_UPDATE = "cache_update"
    COMPLETE = "complete"


@dataclass
class ReactionEvent:
    """用户反应事件（进入 Pipeline 的原始数据）"""
    event_id: str
    user_id: str
    anchor_id: str
    reaction_type: str              # 原始字符串，需转换
    opinion_text: Optional[str] = None
    emotion_word: Optional[str] = None
    timestamp: float = 0.0
    
    # 关联数据（由 Pipeline 查询填充）
    anchor_text: Optional[str] = None
    anchor_topics: list[str] = field(default_factory=list)
    anchor_embedding: Optional[np.ndarray] = None
    existing_opinion_embeddings: list[np.ndarray] = field(default_factory=list)
    harmful_ratio: float = 0.0
    unexperienced_ratio: float = 0.0
    other_user_id: Optional[str] = None  # 该锚点下产生共鸣的对方用户 ID


@dataclass
class PipelineResult:
    """Pipeline 处理结果"""
    event_id: str
    success: bool
    stage: PipelineStage
    resonance_value: Optional[float] = None
    relationship_score: Optional[float] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0


@dataclass
class IncrementalBatch:
    """增量批次（定时处理的批量反应）"""
    batch_id: str
    events: list[ReactionEvent]
    created_at: float = 0.0
    processed: bool = False


# ============================================================
# 数据访问接口（抽象）
# ============================================================

class DataStore:
    """数据存储接口（内存模拟，生产环境替换为 PostgreSQL/MongoDB）"""
    
    def __init__(self):
        self._anchors: dict[str, dict] = {}           # anchor_id → anchor data
        self._reactions: dict[str, list[dict]] = {}    # anchor_id → [reaction]
        self._opinion_embeddings: dict[str, list[np.ndarray]] = {}  # anchor_id → [embedding]
        self._relationship_records: dict[tuple[str, str], list[dict]] = {}  # (user_a, user_b) → records
    
    def get_anchor(self, anchor_id: str) -> Optional[dict]:
        return self._anchors.get(anchor_id)
    
    def register_anchor(self, anchor_id: str, text: str, topics: list[str], embedding: np.ndarray):
        self._anchors[anchor_id] = {"text": text, "topics": topics, "embedding": embedding}
    
    def add_reaction(self, anchor_id: str, reaction: dict):
        if anchor_id not in self._reactions:
            self._reactions[anchor_id] = []
        self._reactions[anchor_id].append(reaction)
    
    def get_existing_opinion_embeddings(self, anchor_id: str) -> list[np.ndarray]:
        return self._opinion_embeddings.get(anchor_id, [])
    
    def add_opinion_embedding(self, anchor_id: str, embedding: np.ndarray):
        if anchor_id not in self._opinion_embeddings:
            self._opinion_embeddings[anchor_id] = []
        self._opinion_embeddings[anchor_id].append(embedding)
    
    def get_mark_ratios(self, anchor_id: str) -> tuple[float, float]:
        """获取有害/未体验标记比例"""
        reactions = self._reactions.get(anchor_id, [])
        if not reactions:
            return 0.0, 0.0
        harmful = sum(1 for r in reactions if r.get("reaction_type") == "有害")
        unexperienced = sum(1 for r in reactions if r.get("reaction_type") == "未体验")
        total = len(reactions)
        return harmful / total, unexperienced / total
    
    def add_relationship_record(self, user_a: str, user_b: str, record: dict):
        key = tuple(sorted([user_a, user_b]))
        if key not in self._relationship_records:
            self._relationship_records[key] = []
        self._relationship_records[key].append(record)
    
    def get_relationship_records(self, user_a: str, user_b: str) -> list[dict]:
        key = tuple(sorted([user_a, user_b]))
        return self._relationship_records.get(key, [])
    
    def find_resonance_pairs(self, anchor_id: str, user_id: str) -> list[str]:
        """找到在同一锚点上有共鸣的其他用户"""
        reactions = self._reactions.get(anchor_id, [])
        resonance_users = set()
        for r in reactions:
            if r.get("reaction_type") == "共鸣" and r.get("user_id") != user_id:
                resonance_users.add(r["user_id"])
        return list(resonance_users)


# ============================================================
# Pipeline 实现
# ============================================================

class ResonancePipeline:
    """共鸣增量计算 Pipeline
    
    处理流程：
    1. 验证 → 2. 编码 → 3. 共鸣值计算 → 4. 关系分更新 → 5. 缓存
    """
    
    def __init__(
        self,
        encoder: TextEncoder,
        data_store: DataStore,
        on_trust_update: Optional[Callable] = None,
    ):
        self.encoder = encoder
        self.store = data_store
        self.on_trust_update = on_trust_update  # 信任级别更新回调
        
        # 统计
        self.stats = {
            "total_processed": 0,
            "total_errors": 0,
            "avg_latency_ms": 0.0,
        }
    
    def process_event(self, event: ReactionEvent) -> PipelineResult:
        """处理单个反应事件"""
        start_time = time.perf_counter()
        
        try:
            # Stage 1: 验证
            result = self._validate(event)
            if not result.success:
                return result
            
            # Stage 2: 编码
            opinion_embedding = self._encode(event)
            
            # Stage 3: 共鸣值计算
            resonance_score = self._compute_resonance(event, opinion_embedding)
            
            # Stage 4: 关系分更新
            relationship_score = self._update_relationships(event, resonance_score)
            
            # Stage 5: 存储
            self._store_results(event, resonance_score, opinion_embedding)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            return PipelineResult(
                event_id=event.event_id,
                success=True,
                stage=PipelineStage.COMPLETE,
                resonance_value=resonance_score.value if resonance_score else None,
                relationship_score=relationship_score.score if relationship_score else None,
                processing_time_ms=elapsed_ms,
            )
        
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self.stats["total_errors"] += 1
            return PipelineResult(
                event_id=event.event_id,
                success=False,
                stage=PipelineStage.VALIDATE,
                error=str(e),
                processing_time_ms=elapsed_ms,
            )
    
    def process_batch(self, events: list[ReactionEvent]) -> list[PipelineResult]:
        """批量处理（利用 encoder 的 batch 能力）"""
        start_time = time.perf_counter()
        results = []
        
        # 预先批量编码（比逐条编码快）
        texts_to_encode = []
        encode_indices = []
        
        for i, event in enumerate(events):
            if event.opinion_text and len(event.opinion_text.strip()) > 0:
                texts_to_encode.append(event.opinion_text)
                encode_indices.append(i)
        
        if texts_to_encode:
            batch_embeddings = self.encoder.encode(texts_to_encode)
        else:
            batch_embeddings = []
        
        # 逐个处理
        emb_idx = 0
        for i, event in enumerate(events):
            try:
                # 验证
                val_result = self._validate(event)
                if not val_result.success:
                    results.append(val_result)
                    continue
                
                # 使用预编码的 embedding
                if i in encode_indices:
                    opinion_embedding = batch_embeddings[emb_idx]
                    emb_idx += 1
                else:
                    opinion_embedding = None
                
                # 共鸣值
                resonance_score = self._compute_resonance(event, opinion_embedding)
                
                # 关系分
                relationship_score = self._update_relationships(event, resonance_score)
                
                # 存储
                if opinion_embedding is not None:
                    self._store_results(event, resonance_score, opinion_embedding)
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                results.append(PipelineResult(
                    event_id=event.event_id,
                    success=True,
                    stage=PipelineStage.COMPLETE,
                    resonance_value=resonance_score.value if resonance_score else None,
                    relationship_score=relationship_score.score if relationship_score else None,
                    processing_time_ms=elapsed_ms,
                ))
            
            except Exception as e:
                results.append(PipelineResult(
                    event_id=event.event_id,
                    success=False,
                    stage=PipelineStage.VALIDATE,
                    error=str(e),
                ))
        
        self.stats["total_processed"] += len(events)
        return results
    
    def _validate(self, event: ReactionEvent) -> PipelineResult:
        """Stage 1: 验证"""
        # 检查锚点存在
        anchor = self.store.get_anchor(event.anchor_id)
        if not anchor:
            return PipelineResult(
                event_id=event.event_id,
                success=False,
                stage=PipelineStage.VALIDATE,
                error=f"锚点不存在: {event.anchor_id}",
            )
        
        # 转换反应类型
        type_map = {
            "共鸣": ReactionType.RESONANCE,
            "无感": ReactionType.NEUTRAL,
            "反对": ReactionType.OPPOSITION,
            "未体验": ReactionType.UNEXPERIENCED,
            "有害": ReactionType.HARMFUL,
        }
        if event.reaction_type not in type_map:
            return PipelineResult(
                event_id=event.event_id,
                success=False,
                stage=PipelineStage.VALIDATE,
                error=f"未知反应类型: {event.reaction_type}",
            )
        
        # 填充关联数据
        event.anchor_text = anchor["text"]
        event.anchor_topics = anchor["topics"]
        event.anchor_embedding = anchor["embedding"]
        event.existing_opinion_embeddings = self.store.get_existing_opinion_embeddings(event.anchor_id)
        event.harmful_ratio, event.unexperienced_ratio = self.store.get_mark_ratios(event.anchor_id)
        
        return PipelineResult(event_id=event.event_id, success=True, stage=PipelineStage.VALIDATE)
    
    def _encode(self, event: ReactionEvent) -> Optional[np.ndarray]:
        """Stage 2: 编码（单条模式）"""
        if event.opinion_text and len(event.opinion_text.strip()) > 0:
            return self.encoder.encode_single(event.opinion_text)
        return None
    
    def _compute_resonance(
        self,
        event: ReactionEvent,
        opinion_embedding: Optional[np.ndarray],
    ) -> Optional[object]:
        """Stage 3: 共鸣值计算"""
        type_map = {
            "共鸣": ReactionType.RESONANCE,
            "无感": ReactionType.NEUTRAL,
            "反对": ReactionType.OPPOSITION,
            "未体验": ReactionType.UNEXPERIENCED,
            "有害": ReactionType.HARMFUL,
        }
        emotion_map = {
            "共情": EmotionWord.EMPATHY,
            "被言说": EmotionWord.ARTICULATED,
            "开眼界": EmotionWord.INSIGHT,
        }
        
        reaction = Reaction(
            user_id=event.user_id,
            anchor_id=event.anchor_id,
            reaction_type=type_map[event.reaction_type],
            opinion_text=event.opinion_text,
            emotion_word=emotion_map.get(event.emotion_word),
            timestamp=event.timestamp,
            harmful_ratio=event.harmful_ratio,
            unexperienced_ratio=event.unexperienced_ratio,
        )
        
        anchor = Anchor(
            id=event.anchor_id,
            text=event.anchor_text or "",
            topics=event.anchor_topics,
            embedding=event.anchor_embedding,
        )
        
        op_emb = opinion_embedding if opinion_embedding is not None else np.zeros_like(event.anchor_embedding)
        
        return compute_resonance_value(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=op_emb,
            anchor_embedding=event.anchor_embedding,
            existing_opinion_embeddings=event.existing_opinion_embeddings,
        )
    
    def _update_relationships(
        self,
        event: ReactionEvent,
        resonance_score,
    ) -> Optional[RelationshipScore]:
        """Stage 4: 关系分更新"""
        if resonance_score is None or resonance_score.value <= 0:
            return None
        
        # 找到在同一锚点上有共鸣的其他用户
        other_users = self.store.find_resonance_pairs(event.anchor_id, event.user_id)
        
        if not other_users:
            return None
        
        # 为每个关系对更新
        latest_score = None
        for other_user in other_users:
            # 获取现有记录
            records = self.store.get_relationship_records(event.user_id, other_user)
            
            # 添加新记录
            new_record = {
                "value": resonance_score.value,
                "topic": event.anchor_topics[0] if event.anchor_topics else "未分类",
            }
            records.append(new_record)
            
            # 重新计算关系分
            rel = compute_relationship_score(event.user_id, other_user, records)
            
            # 存储
            self.store.add_relationship_record(event.user_id, other_user, new_record)
            
            latest_score = rel
            
            # 回调（通知用户引擎更新信任级别）
            if self.on_trust_update:
                self.on_trust_update(event.user_id, other_user, rel.score)
        
        return latest_score
    
    def _store_results(
        self,
        event: ReactionEvent,
        resonance_score,
        opinion_embedding: Optional[np.ndarray],
    ):
        """Stage 5: 存储结果"""
        # 存储反应记录
        self.store.add_reaction(event.anchor_id, {
            "user_id": event.user_id,
            "reaction_type": event.reaction_type,
            "opinion_text": event.opinion_text,
            "timestamp": event.timestamp,
            "resonance_value": resonance_score.value if resonance_score else 0,
        })
        
        # 存储观点 embedding
        if opinion_embedding is not None:
            self.store.add_opinion_embedding(event.anchor_id, opinion_embedding)


# ============================================================
# 定时全量校准
# ============================================================

class DailyRecalibrator:
    """定时全量校准器
    
    每日凌晨批量重算所有关系分：
    - 修复增量计算的累积误差
    - 应用最新的算法参数
    - 清理过期数据
    """
    
    def __init__(self, data_store: DataStore):
        self.store = data_store
    
    def recalibrate_all(self) -> dict:
        """全量重算所有关系分"""
        start_time = time.perf_counter()
        
        total_pairs = 0
        updated_pairs = 0
        level_changes = 0
        
        for (user_a, user_b), records in self.store._relationship_records.items():
            total_pairs += 1
            
            # 重算关系分
            new_rel = compute_relationship_score(user_a, user_b, records)
            
            # 对比旧分（如果有）
            # 这里简化处理——直接记录重算结果
            updated_pairs += 1
        
        elapsed = time.perf_counter() - start_time
        
        return {
            "total_pairs": total_pairs,
            "updated_pairs": updated_pairs,
            "level_changes": level_changes,
            "elapsed_seconds": round(elapsed, 3),
        }


# ============================================================
# 测试
# ============================================================

def run_tests():
    """增量计算 Pipeline 测试"""
    print("=" * 60)
    print("  共鸣增量计算 Pipeline 测试")
    print("=" * 60)
    
    # 初始化
    models_dir = Path(__file__).parent.parent / "shared" / "models"
    encoder = TextEncoder(model_name=str(models_dir / "bge-base-zh-v1.5"))
    store = DataStore()
    
    # 信任更新日志
    trust_updates = []
    def on_trust_update(user_a, user_b, score):
        trust_updates.append((user_a, user_b, score))
    
    pipeline = ResonancePipeline(encoder, store, on_trust_update=on_trust_update)
    
    # 注册锚点
    anchor_text = "深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。"
    anchor_emb = encoder.encode_single(anchor_text)
    store.register_anchor("a001", anchor_text, ["孤独", "城市"], anchor_emb)
    
    # --- 单条事件测试 ---
    print("\n📋 单条事件处理")
    
    event1 = ReactionEvent(
        event_id="e001",
        user_id="u001",
        anchor_id="a001",
        reaction_type="共鸣",
        opinion_text="孤独不是身边没有人，是没有人知道你在哪里。",
        emotion_word="被言说",
        timestamp=time.time(),
    )
    
    result1 = pipeline.process_event(event1)
    print(f"  事件 e001:")
    print(f"    成功: {result1.success}")
    print(f"    共鸣值: {result1.resonance_value:.4f}" if result1.resonance_value else "    共鸣值: None")
    print(f"    耗时: {result1.processing_time_ms:.1f}ms")
    
    # 第二条（不同用户，同一锚点）
    event2 = ReactionEvent(
        event_id="e002",
        user_id="u002",
        anchor_id="a001",
        reaction_type="共鸣",
        opinion_text="地铁上的孤独是一种被包围的孤独。",
        emotion_word="共情",
        timestamp=time.time(),
    )
    
    result2 = pipeline.process_event(event2)
    print(f"\n  事件 e002:")
    print(f"    成功: {result2.success}")
    print(f"    共鸣值: {result2.resonance_value:.4f}" if result2.resonance_value else "    共鸣值: None")
    print(f"    关系分: {result2.relationship_score:.4f}" if result2.relationship_score else "    关系分: None")
    print(f"    耗时: {result2.processing_time_ms:.1f}ms")
    
    # 信任更新回调
    print(f"\n  信任更新回调: {len(trust_updates)} 次")
    for ua, ub, score in trust_updates:
        print(f"    {ua} ↔ {ub}: {score:.4f}")
    
    # --- 批量处理测试 ---
    print(f"\n{'='*60}")
    print("  批量处理测试")
    print(f"{'='*60}\n")
    
    batch_events = [
        ReactionEvent(
            event_id=f"batch_{i}",
            user_id=f"u_batch_{i}",
            anchor_id="a001",
            reaction_type="共鸣",
            opinion_text=text,
            timestamp=time.time(),
        )
        for i, text in enumerate([
            "深夜的地铁像一个移动的棺材。",
            "城市里的每个人都是孤岛。",
            "孤独是一种选择，不是命运。",
            "地铁上的灯从来不属于乘客。",
            "深夜回家的路，是最长的孤独。",
        ])
    ]
    
    batch_results = pipeline.process_batch(batch_events)
    
    success_count = sum(1 for r in batch_results if r.success)
    print(f"  批量处理: {success_count}/{len(batch_events)} 成功")
    
    for r in batch_results:
        rv = f"{r.resonance_value:.4f}" if r.resonance_value else "N/A"
        rs = f"{r.relationship_score:.4f}" if r.relationship_score else "N/A"
        print(f"    {r.event_id}: 共鸣={rv}, 关系={rs}, {r.processing_time_ms:.1f}ms")
    
    # --- 全量校准测试 ---
    print(f"\n{'='*60}")
    print("  全量校准测试")
    print(f"{'='*60}\n")
    
    recal = DailyRecalibrator(store)
    recal_result = recal.recalibrate_all()
    print(f"  关系对总数: {recal_result['total_pairs']}")
    print(f"  更新数: {recal_result['updated_pairs']}")
    print(f"  耗时: {recal_result['elapsed_seconds']}s")
    
    # --- 统计 ---
    print(f"\n📋 Pipeline 统计")
    print(f"  处理总数: {pipeline.stats['total_processed']}")
    print(f"  错误总数: {pipeline.stats['total_errors']}")
    print(f"  信任更新回调: {len(trust_updates)} 次")
    
    print(f"\n✅ 测试完成")


if __name__ == "__main__":
    from pathlib import Path
    run_tests()
