"""
共鸣机制引擎 - 共鸣值计算

实现文档 §9.2 中定义的完整共鸣值公式：
  single_resonance_value = resonance_weight
                         × depth_weight
                         × relevance_score
                         × novelty_score
                         × harmful_penalty
                         × unexperienced_penalty

以及关系分聚合：
  relationship_score = Σ(共鸣值 × 话题衰减) × 跨话题加权
"""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.encoders.text_encoder import TextEncoder


# ============================================================
# 数据结构
# ============================================================

class ReactionType(Enum):
    RESONANCE = "共鸣"
    NEUTRAL = "无感"
    OPPOSITION = "反对"
    UNEXPERIENCED = "未体验"
    HARMFUL = "有害"


class EmotionWord(Enum):
    EMPATHY = "共情"        # "我也是这样"
    ARTICULATED = "被言说"  # "你替我说出了口"
    INSIGHT = "开眼界"      # "我从没这么想过"


@dataclass
class Reaction:
    """一条用户反应"""
    user_id: str
    anchor_id: str
    reaction_type: ReactionType
    opinion_text: Optional[str] = None       # 观点文字（可选）
    emotion_word: Optional[EmotionWord] = None  # 情绪词（可选）
    timestamp: float = 0.0
    harmful_ratio: float = 0.0               # 该锚点的有害标记比例
    unexperienced_ratio: float = 0.0         # 该锚点的未体验标记比例


@dataclass
class Anchor:
    """锚点"""
    id: str
    text: str
    topics: list[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None


@dataclass
class ResonanceScore:
    """单条反应的共鸣值"""
    value: float
    components: dict


# ============================================================
# 共鸣值计算
# ============================================================

# 反应类型权重
REACTION_WEIGHTS = {
    ReactionType.RESONANCE: 1.0,
    ReactionType.NEUTRAL: 0.0,
    ReactionType.OPPOSITION: -0.2,
    ReactionType.UNEXPERIENCED: None,  # 不计入共鸣值
    ReactionType.HARMFUL: None,        # 不计入共鸣值
}

# 情绪词加权
EMOTION_BONUSES = {
    EmotionWord.EMPATHY: 1.0,      # 同感：标准
    EmotionWord.ARTICULATED: 1.1,  # 被言说：微调
    EmotionWord.INSIGHT: 1.1,      # 开眼界：微调
}

# 字数权重
def get_depth_weight(text: Optional[str]) -> float:
    """根据观点字数计算字数权重"""
    if text is None or len(text.strip()) == 0:
        return 0.6  # 仅点击反应（含情绪词）
    length = len(text)
    if length < 50:
        return 0.9  # 简短观点
    elif length <= 200:
        return 1.0  # 深度观点
    else:
        return 1.1  # 长文


def get_resonance_weight(
    reaction_type: ReactionType,
    emotion_word: Optional[EmotionWord] = None,
) -> Optional[float]:
    """计算反应类型权重（含情绪词微调）"""
    base = REACTION_WEIGHTS.get(reaction_type)
    if base is None:
        return None  # 不计入共鸣值
    
    if emotion_word and reaction_type == ReactionType.RESONANCE:
        bonus = EMOTION_BONUSES.get(emotion_word, 1.0)
        return base * bonus
    return base


def compute_relevance(
    opinion_embedding: np.ndarray,
    anchor_embedding: np.ndarray,
) -> float:
    """计算观点与锚点的相关性（余弦相似度）"""
    # embedding 已 L2 归一化，点积 = 余弦相似度
    return float(np.dot(opinion_embedding, anchor_embedding))


def compute_novelty(
    opinion_embedding: np.ndarray,
    existing_embeddings: list[np.ndarray],
    relevance: float,
) -> float:
    """计算观点的增量性
    
    novelty = 1 - max(与锚点下已有观点的相似度)
    
    如果锚点下已有观点不足 5 条，novelty 按 1.0 处理
    （不惩罚先驱者）。
    """
    if relevance < 0.3:
        return 0.0  # 不相关，novelty 为 0
    
    if len(existing_embeddings) < 5:
        return 1.0  # 数据不足，不惩罚
    
    # 计算与所有已有观点的最大相似度
    existing_matrix = np.array(existing_embeddings)
    similarities = np.dot(existing_matrix, opinion_embedding)
    max_sim = float(np.max(similarities))
    
    novelty = max(0.1, 1 - max_sim)  # 下限 0.1
    return novelty


def compute_resonance_value(
    reaction: Reaction,
    anchor: Anchor,
    opinion_embedding: np.ndarray,
    anchor_embedding: np.ndarray,
    existing_opinion_embeddings: list[np.ndarray],
) -> Optional[ResonanceScore]:
    """计算单条反应的共鸣值
    
    返回 None 表示该反应不计入共鸣值（如"有害""未体验"）。
    """
    # 1. 反应类型权重
    resonance_weight = get_resonance_weight(reaction.reaction_type, reaction.emotion_word)
    if resonance_weight is None:
        return None
    
    # 2. 字数权重
    depth_weight = get_depth_weight(reaction.opinion_text)
    
    # 3. 有文字的观点：计算 relevance 和 novelty
    #    无文字的纯点击：跳过语义分析，relevance=novelty=1.0
    has_text = reaction.opinion_text is not None and len(reaction.opinion_text.strip()) > 0
    
    if has_text:
        relevance = compute_relevance(opinion_embedding, anchor_embedding)
        novelty = compute_novelty(opinion_embedding, existing_opinion_embeddings, relevance)
    else:
        relevance = 1.0  # 纯点击：不分析语义
        novelty = 1.0
    
    # 4. 惩罚系数
    harmful_penalty = max(0, 1.0 - reaction.harmful_ratio * 2)
    unexperienced_penalty = max(0, 1.0 - reaction.unexperienced_ratio * 1.5)
    
    # 5. 最终值
    value = (resonance_weight 
             * depth_weight 
             * relevance 
             * novelty 
             * harmful_penalty 
             * unexperienced_penalty)
    
    return ResonanceScore(
        value=round(value, 6),
        components={
            "resonance_weight": resonance_weight,
            "depth_weight": depth_weight,
            "relevance": round(relevance, 4),
            "novelty": round(novelty, 4),
            "harmful_penalty": round(harmful_penalty, 4),
            "unexperienced_penalty": round(unexperienced_penalty, 4),
        },
    )


# ============================================================
# 话题衰减与跨话题加权
# ============================================================

def topic_decay(n_topic: int, alpha: float = 0.3) -> float:
    """同一话题第 N 次共鸣的边际价值递减"""
    return 1.0 / (1 + alpha * (n_topic - 1))


def diversity_bonus(unique_topics: int, beta: float = 0.15) -> float:
    """跨话题加权"""
    return beta * np.log(unique_topics + 1)


# ============================================================
# 关系分聚合
# ============================================================

@dataclass
class RelationshipScore:
    """两人之间的关系分"""
    user_a: str
    user_b: str
    score: float
    unique_topics: int
    resonance_count: int
    breakdown: list[dict]


def compute_relationship_score(
    user_a: str,
    user_b: str,
    resonance_records: list[dict],
) -> RelationshipScore:
    """计算两个用户之间的关系分
    
    resonance_records: [
        {"value": float, "topic": str},
        ...
    ]
    """
    if not resonance_records:
        return RelationshipScore(user_a, user_b, 0.0, 0, 0, [])
    
    # 按话题统计次数
    topic_counts = {}
    breakdown = []
    
    for record in resonance_records:
        topic = record["topic"]
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        n = topic_counts[topic]
        
        decay = topic_decay(n)
        weighted_value = record["value"] * decay
        
        breakdown.append({
            "topic": topic,
            "raw_value": record["value"],
            "n_topic": n,
            "decay": round(decay, 4),
            "weighted_value": round(weighted_value, 6),
        })
    
    # 基础分 = Σ(共鸣值 × 话题衰减)
    base_score = sum(b["weighted_value"] for b in breakdown)
    
    # 跨话题加权
    unique_topics = len(topic_counts)
    bonus = diversity_bonus(unique_topics)
    
    # 最终关系分
    final_score = base_score * (1 + bonus)
    
    return RelationshipScore(
        user_a=user_a,
        user_b=user_b,
        score=round(final_score, 4),
        unique_topics=unique_topics,
        resonance_count=len(resonance_records),
        breakdown=breakdown,
    )


# ============================================================
# 测试
# ============================================================

def run_tests():
    """运行共鸣值计算的单元测试"""
    print("=" * 60)
    print("  共鸣值计算公式测试")
    print("=" * 60)
    
    # 加载编码器
    models_dir = Path(__file__).parent.parent / "shared" / "models"
    encoder = TextEncoder(model_name=str(models_dir / "bge-base-zh-v1.5"))
    
    # 测试锚点
    anchor = Anchor(
        id="a001",
        text="深夜独自坐在末班地铁上，窗外灯火通明，但没有一盏灯是为我亮的。",
        topics=["孤独", "城市"],
    )
    anchor_emb = encoder.encode_single(anchor.text)
    
    # 测试观点
    test_cases = [
        {
            "label": "复述锚点 + 共鸣 + 无情绪词",
            "reaction": Reaction(
                user_id="u001", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                opinion_text="是啊，深夜地铁确实孤独，窗外的灯不属于我。",
            ),
            "opinion": "是啊，深夜地铁确实孤独，窗外的灯不属于我。",
        },
        {
            "label": "增量感悟 + 共鸣 + 被言说",
            "reaction": Reaction(
                user_id="u002", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                emotion_word=EmotionWord.ARTICULATED,
                opinion_text="孤独不是身边没有人，是没有人知道你在哪里。"
                             "有一次在机场候机厅过夜，周围全是人但没有一个人认识我。",
            ),
            "opinion": "孤独不是身边没有人，是没有人知道你在哪里。"
                       "有一次在机场候机厅过夜，周围全是人但没有一个人认识我。",
        },
        {
            "label": "全新角度 + 共鸣 + 开眼界",
            "reaction": Reaction(
                user_id="u003", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                emotion_word=EmotionWord.INSIGHT,
                opinion_text="地铁的孤独不是因为没人，是因为你在移动中——"
                             "每一站都有人上下，但没有人是为了你停留。",
            ),
            "opinion": "地铁的孤独不是因为没人，是因为你在移动中——"
                       "每一站都有人上下，但没有人是为了你停留。",
        },
        {
            "label": "反对观点",
            "reaction": Reaction(
                user_id="u004", anchor_id="a001",
                reaction_type=ReactionType.OPPOSITION,
                opinion_text="我不觉得这是孤独，这只是大城市生活的常态。"
                             "习惯了就不会有什么感觉。",
            ),
            "opinion": "我不觉得这是孤独，这只是大城市生活的常态。"
                       "习惯了就不会有什么感觉。",
        },
        {
            "label": "仅点击共鸣 + 情绪词",
            "reaction": Reaction(
                user_id="u005", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                emotion_word=EmotionWord.EMPATHY,
            ),
            "opinion": None,
        },
        {
            "label": "有害标记（不计入）",
            "reaction": Reaction(
                user_id="u006", anchor_id="a001",
                reaction_type=ReactionType.HARMFUL,
            ),
            "opinion": None,
        },
    ]
    
    # 编码所有观点
    opinion_texts = [c["opinion"] for c in test_cases if c["opinion"]]
    opinion_embs = encoder.encode(opinion_texts) if opinion_texts else []
    
    # 逐个计算
    existing_embs = []
    emb_idx = 0
    
    print(f"\n锚点: {anchor.text}\n")
    print(f"{'标签':<25} {'权重':>5} {'字数':>5} {'相关':>6} {'增量':>6} {'惩罚':>5} {'共鸣值':>8}")
    print("-" * 75)
    
    for case in test_cases:
        if case["opinion"]:
            op_emb = opinion_embs[emb_idx]
            emb_idx += 1
        else:
            op_emb = encoder.encode_single("") if case["reaction"].reaction_type != ReactionType.HARMFUL else np.zeros(768)
        
        score = compute_resonance_value(
            reaction=case["reaction"],
            anchor=anchor,
            opinion_embedding=op_emb,
            anchor_embedding=anchor_emb,
            existing_opinion_embeddings=existing_embs,
        )
        
        if score is None:
            print(f"{case['label']:<25} {'N/A':>5} {'N/A':>5} {'N/A':>6} {'N/A':>6} {'N/A':>5} {'不计入':>8}")
        else:
            c = score.components
            print(f"{case['label']:<25} {c['resonance_weight']:>5.1f} {c['depth_weight']:>5.1f} "
                  f"{c['relevance']:>6.3f} {c['novelty']:>6.3f} "
                  f"{c['harmful_penalty'] * c['unexperienced_penalty']:>5.3f} {score.value:>8.4f}")
            
            # 加入已有观点池（用于下一个的 novelty 计算）
            if case["opinion"]:
                existing_embs.append(op_emb)
    
    # 测试关系分聚合
    print(f"\n{'='*60}")
    print(f"  关系分聚合测试")
    print(f"{'='*60}\n")
    
    records = [
        {"value": 0.8, "topic": "孤独"},
        {"value": 0.6, "topic": "孤独"},   # 同话题，衰减
        {"value": 0.7, "topic": "音乐"},
        {"value": 0.5, "topic": "城市"},
        {"value": 0.9, "topic": "阅读"},
    ]
    
    rel = compute_relationship_score("u001", "u002", records)
    
    print(f"关系分: {rel.score}")
    print(f"共鸣次数: {rel.resonance_count}")
    print(f"话题数: {rel.unique_topics}")
    print(f"跨话题加权: {diversity_bonus(rel.unique_topics):.4f}")
    print(f"\n明细:")
    for b in rel.breakdown:
        print(f"  [{b['topic']}] 第{b['n_topic']}次: {b['raw_value']:.2f} × {b['decay']:.4f} = {b['weighted_value']:.6f}")
    
    print(f"\n✅ 测试完成")


if __name__ == "__main__":
    run_tests()
