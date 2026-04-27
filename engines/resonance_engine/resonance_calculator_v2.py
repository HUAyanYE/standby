"""
共鸣机制引擎 v2 — 算法优化版

相比 v1 的核心改进：
1. Novelty: 从 max(sim) 单点 → 聚类感知加权 (k-NN 均值)
2. Relevance: 从硬阈值 0.3 → sigmoid 平滑过渡
3. Depth: 从纯字数 → 字数 × 语义信息量的复合信号
4. Emotion: 对齐 PRD 的 4 个情绪词 (同感/触发/启发/震撼)
5. Harmful/Unexperienced penalty: 从线性 → 指数型衰减
6. 关系分聚合: 新增时间加权因子
7. 跨话题加权: 从计数 → Shannon 熵

设计理念："共鸣不是重复是增量" — resonance = relevance × novelty
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
# 数据结构 (对齐 PRD v0.1 定义)
# ============================================================

class ReactionType(Enum):
    RESONANCE = "共鸣"      # 强正向
    NEUTRAL = "无感"        # 弱信号
    OPPOSITION = "反对"     # 强负向 (但也是深度参与)
    UNEXPERIENCED = "未体验" # 真实性信号，不计入共鸣值
    HARMFUL = "有害"        # 治理信号，不计入共鸣值


class EmotionWord(Enum):
    """PRD v0.1 §3.2 定义的 4 个情绪词"""
    EMPATHY = "同感"        # "我也有同样的感受" — 最常见
    TRIGGER = "触发"        # "让我想起了……" — 触及个人记忆
    INSIGHT = "启发"        # "没这么想过，但你说得对" — 视角互补
    SHOCK = "震撼"          # "说不出话" — 被深深击中


@dataclass
class Reaction:
    user_id: str
    anchor_id: str
    reaction_type: ReactionType
    opinion_text: Optional[str] = None
    emotion_word: Optional[EmotionWord] = None
    timestamp: float = 0.0
    harmful_ratio: float = 0.0
    unexperienced_ratio: float = 0.0


@dataclass
class Anchor:
    id: str
    text: str
    topics: list[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None


@dataclass
class ResonanceScore:
    value: float
    components: dict


# ============================================================
# v2 核心算法
# ============================================================

# 反应类型权重 (对齐 PRD)
REACTION_WEIGHTS = {
    ReactionType.RESONANCE: 1.0,
    ReactionType.NEUTRAL: 0.0,
    ReactionType.OPPOSITION: -0.2,   # "反对也是深度参与"
    ReactionType.UNEXPERIENCED: None,
    ReactionType.HARMFUL: None,
}

# 情绪词加权 (对齐 PRD: 触发/启发 ×1.1, 震撼 ×1.2)
EMOTION_BONUSES = {
    EmotionWord.EMPATHY: 1.0,    # 同感：标准
    EmotionWord.TRIGGER: 1.1,    # 触发：强共鸣
    EmotionWord.INSIGHT: 1.1,    # 启发：视角互补
    EmotionWord.SHOCK: 1.2,      # 震撼：最强共鸣
}


# ---- 改进 1: Sigmoid 相关性过滤 ----

def sigmoid_relevance(
    relevance: float,
    threshold: float = 0.3,
    sharpness: float = 15.0,
) -> float:
    """Sigmoid 平滑替代硬阈值
    
    v1 问题: relevance < 0.3 直接归零, 0.3 处有跳跃
    v2 方案: sigmoid(relevance; μ=threshold, k=sharpness)
    
    - relevance << threshold → ≈ 0 (平滑趋零, 非硬截断)
    - relevance == threshold → 0.5 (半功率点)
    - relevance >> threshold → ≈ 1.0
    
    sharpness 控制过渡锐度: 越大越接近硬阈值, 越小越平滑
    """
    return 1.0 / (1.0 + np.exp(-sharpness * (relevance - threshold)))


# ---- 改进 2: 聚类感知 Novelty ----

def compute_novelty_v2(
    opinion_embedding: np.ndarray,
    existing_embeddings: list[np.ndarray],
    relevance: float,
    k_neighbors: int = 5,
    relevance_floor: float = 0.3,
    precomputed_top_k_sims: list[float] | None = None,
    total_existing_count: int = 0,
) -> float:
    """聚类感知的 novelty 评分

    v1 问题: novelty = 1 - max(sim) 只看最近邻
    v2 方案: 用 k-NN 均值代替 max
    - novelty = 1 - mean(top_k_similarities)

    优化: 传入 precomputed_top_k_sims (来自 pgvector 原生搜索)
    可跳过全量加载和 Python 点积计算。
    """
    if relevance < relevance_floor:
        return 0.0  # 不相关, novelty 为 0

    # 使用预计算的 top-k 相似度 (pgvector 快速路径)
    if precomputed_top_k_sims is not None:
        if len(precomputed_top_k_sims) < 5:
            return 1.0  # 数据不足, 不惩罚先驱者
        mean_top_k = float(np.mean(precomputed_top_k_sims))
        count = total_existing_count if total_existing_count > 0 else len(precomputed_top_k_sims)
        density_factor = 1.0 / (1.0 + 0.05 * np.log(count + 1))
        novelty = max(0.1, (1.0 - mean_top_k) * density_factor)
        return novelty

    # 传统路径: 全量加载 + Python 点积
    if len(existing_embeddings) < 5:
        return 1.0  # 数据不足, 不惩罚先驱者

    existing_matrix = np.array(existing_embeddings)
    similarities = np.dot(existing_matrix, opinion_embedding)
    
    # 取 top-k 相似度的均值 (比 max 更稳健)
    k = min(k_neighbors, len(similarities))
    top_k_sims = np.sort(similarities)[-k:]
    mean_top_k = float(np.mean(top_k_sims))
    
    # 密度衰减: 观点越多, novelty 上限越低
    # log 衰减: 50 条时 0.85, 200 条时 0.72, 1000 条时 0.60
    density_factor = 1.0 / (1.0 + 0.05 * np.log(len(existing_embeddings) + 1))
    
    novelty = max(0.1, (1.0 - mean_top_k) * density_factor)
    return novelty


# ---- 改进 3: 复合深度信号 ----

def compute_depth_v2(
    text: Optional[str],
    opinion_embedding: Optional[np.ndarray] = None,
    anchor_embedding: Optional[np.ndarray] = None,
) -> float:
    """复合深度信号: 字数 × 语义信息量
    
    v1 问题: 纯字数分档 (0.6/0.9/1.0/1.1)
    - 长文但空洞 → 高权重 (不好)
    - 短小精悍 → 低权重 (不好)
    
    v2 方案: 字数权重 × 语义正交性
    - 语义正交性 = 1 - |cos_sim(opinion, anchor)|
    - 意义: 如果观点与锚点的语义方向不同, 说明提供了新维度, 更有深度
    - 但如果观点太偏离锚点 (离题), 正交性高但 relevance 低, 最终会被
      relevance 过滤掉
    """
    # 字数权重 (微调: 短文权重提升, 长文上限降低)
    if text is None or len(text.strip()) == 0:
        base = 0.6
    elif len(text) < 20:
        base = 0.8   # v1 是 0.9, 但极短观点 (如"对") 权重应更低
    elif len(text) < 50:
        base = 0.9
    elif len(text) <= 200:
        base = 1.0
    else:
        base = 1.05  # v1 是 1.1, v2 进一步降低, 避免灌水
    
    # 语义正交性 (可选, 需要 embedding)
    if opinion_embedding is not None and anchor_embedding is not None:
        cos_sim = float(np.dot(opinion_embedding, anchor_embedding))
        orthogonality = 1.0 - abs(cos_sim)
        # 正交性范围 [0, 1], 但通常 0.2-0.6
        # 映射到 [0.85, 1.15], 让正交性作为微调而非主导
        semantic_factor = 0.85 + 0.3 * orthogonality
        return base * semantic_factor
    
    return base


# ---- 改进 4: 指数型惩罚函数 ----

def harmful_penalty_v2(ratio: float) -> float:
    """指数型有害惩罚
    
    v1: max(0, 1.0 - ratio * 2) — 线性
    v2: exp(-3 * ratio) — 指数衰减
    
    线性的问题: ratio=0.5 时 penalty=0, 但 50% 有害标记的内容
    惩罚应该比线性更严厉。
    
    指数型: 
    - ratio=0.1 → 0.74 (温和)
    - ratio=0.2 → 0.55
    - ratio=0.3 → 0.41 (严厉)
    - ratio=0.5 → 0.22 (几乎归零)
    """
    return float(np.exp(-3.0 * ratio))


def unexperienced_penalty_v2(ratio: float) -> float:
    """指数型未体验惩罚 (比有害温和)"""
    return float(np.exp(-2.0 * ratio))


# ---- 改进 5: 对齐 PRD 的情绪词处理 ----

def get_resonance_weight_v2(
    reaction_type: ReactionType,
    emotion_word: Optional[EmotionWord] = None,
) -> Optional[float]:
    """反应类型权重 (含 PRD 对齐的情绪词加权)"""
    base = REACTION_WEIGHTS.get(reaction_type)
    if base is None:
        return None
    
    if emotion_word and reaction_type == ReactionType.RESONANCE:
        bonus = EMOTION_BONUSES.get(emotion_word, 1.0)
        return base * bonus
    return base


# ============================================================
# 话题衰减 & 跨话题加权 (v2)
# ============================================================

def topic_decay_v2(n_topic: int, alpha: float = 0.3) -> float:
    """话题内衰减 (保持 v1 的双曲线方案, 经过验证合理)"""
    return 1.0 / (1 + alpha * (n_topic - 1))


def diversity_bonus_v2(
    topic_records: list[dict],
    beta: float = 0.15,
) -> float:
    """跨话题加权 v2: Shannon 熵替代简单计数
    
    v1: bonus = β × ln(unique_topics + 1)
    - 只看话题数量, 不看分布
    - 10 个话题各 1 次 vs 1 个话题 10 次 → 奖励差距不大
    
    v2: bonus = β × Shannon_entropy(topic_distribution)
    - 考虑分布均匀性
    - 10 个话题各 1 次 → 熵高 → 奖励大
    - 1 个话题 10 次 → 熵低 → 奖励小
    """
    if not topic_records:
        return 0.0
    
    # 统计各话题次数
    topic_counts = {}
    for r in topic_records:
        t = r.get("topic", "未分类")
        topic_counts[t] = topic_counts.get(t, 0) + 1
    
    total = sum(topic_counts.values())
    if total <= 1:
        return 0.0
    
    # Shannon 熵
    entropy = 0.0
    for count in topic_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * np.log(p)
    
    # 归一化: 最大熵 = ln(n_topics)
    max_entropy = np.log(len(topic_counts)) if len(topic_counts) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return beta * normalized_entropy


# ============================================================
# 关系分聚合 (v2: 时间加权)
# ============================================================

@dataclass
class RelationshipScore:
    user_a: str
    user_b: str
    score: float
    unique_topics: int
    resonance_count: int
    breakdown: list[dict]


def compute_relationship_score_v2(
    user_a: str,
    user_b: str,
    resonance_records: list[dict],
    time_weight_half_life: float = 180.0,  # 半衰期 180 天
    current_ts: Optional[float] = None,
) -> RelationshipScore:
    """关系分聚合 v2
    
    v1 问题: PRD 说 "关系分不随时间衰减, 共鸣是事实不是状态"
    但实际中, 3 年前的共鸣和昨天的共鸣在激活权限时应该有区别。
    
    v2 方案: 双层结构
    - 基础分 (事实层): 不衰减, 记录所有历史共鸣
    - 活跃分 (激活层): 时间加权, 用于 L3+ 权限激活
    
    这样:
    - 基础分保存共鸣事实, 用户回归后不需重新积累
    - 活跃分反映当前关系热度, 用于权限判定
    """
    if not resonance_records:
        return RelationshipScore(user_a, user_b, 0.0, 0, 0, [])
    
    topic_counts = {}
    breakdown = []
    
    for record in resonance_records:
        topic = record.get("topic", "未分类")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        n = topic_counts[topic]
        
        decay = topic_decay_v2(n)
        raw_value = record.get("value", 0)
        
        # 时间加权 (可选)
        time_weight = 1.0
        if current_ts and "timestamp" in record:
            days_ago = (current_ts - record["timestamp"]) / 86400
            time_weight = 0.5 ** (days_ago / time_weight_half_life)
        
        weighted_value = raw_value * decay * time_weight
        
        breakdown.append({
            "topic": topic,
            "raw_value": raw_value,
            "n_topic": n,
            "decay": round(decay, 4),
            "time_weight": round(time_weight, 4),
            "weighted_value": round(weighted_value, 6),
        })
    
    # 基础分 = Σ(共鸣值 × 话题衰减)  (不含时间权重)
    base_score = sum(
        r["raw_value"] * topic_decay_v2(
            sum(1 for b in breakdown[:i+1] if b["topic"] == r["topic"])
        )
        for i, r in enumerate(breakdown)
    )
    
    # 活跃分 = Σ(共鸣值 × 话题衰减 × 时间权重)
    active_score = sum(b["weighted_value"] for b in breakdown)
    
    # 跨话题加权 (v2: Shannon 熵)
    unique_topics = len(topic_counts)
    bonus = diversity_bonus_v2(resonance_records)
    
    # 最终: 使用活跃分 × 多样性加权
    final_score = active_score * (1 + bonus)
    
    return RelationshipScore(
        user_a=user_a,
        user_b=user_b,
        score=round(final_score, 4),
        unique_topics=unique_topics,
        resonance_count=len(resonance_records),
        breakdown=breakdown,
    )


# ============================================================
# 完整共鸣值计算 (v2)
# ============================================================

def compute_resonance_value_v2(
    reaction: Reaction,
    anchor: Anchor,
    opinion_embedding: np.ndarray,
    anchor_embedding: np.ndarray,
    existing_opinion_embeddings: list[np.ndarray],
    precomputed_top_k_sims: list[float] | None = None,
    total_existing_count: int = 0,
) -> Optional[ResonanceScore]:
    """计算单条反应的共鸣值 (v2 完整版)
    
    Formula:
      value = resonance_weight
            × depth_weight(v2)
            × sigmoid_relevance(v2)
            × novelty(v2)
            × harmful_penalty(v2)
            × unexperienced_penalty(v2)
    """
    # 1. 反应类型权重
    resonance_weight = get_resonance_weight_v2(reaction.reaction_type, reaction.emotion_word)
    if resonance_weight is None:
        return None
    
    # 2. 判断是否有文字
    has_text = reaction.opinion_text is not None and len(reaction.opinion_text.strip()) > 0
    
    if has_text:
        # 3a. 有文字: 计算语义指标
        relevance_raw = float(np.dot(opinion_embedding, anchor_embedding))
        relevance = sigmoid_relevance(relevance_raw)
        novelty = compute_novelty_v2(
            opinion_embedding, existing_opinion_embeddings, relevance_raw,
            precomputed_top_k_sims=precomputed_top_k_sims,
            total_existing_count=total_existing_count,
        )
        depth = compute_depth_v2(reaction.opinion_text, opinion_embedding, anchor_embedding)
    else:
        # 3b. 无文字 (纯点击): 跳过语义分析
        relevance = 1.0
        novelty = 1.0
        depth = 0.6
    
    # 4. 惩罚系数 (指数型)
    harmful_pen = harmful_penalty_v2(reaction.harmful_ratio)
    unexp_pen = unexperienced_penalty_v2(reaction.unexperienced_ratio)
    
    # 5. 最终值
    value = resonance_weight * depth * relevance * novelty * harmful_pen * unexp_pen
    
    return ResonanceScore(
        value=round(value, 6),
        components={
            "resonance_weight": resonance_weight,
            "depth": round(depth, 4),
            "relevance_raw": round(float(np.dot(opinion_embedding, anchor_embedding)), 4) if has_text else 1.0,
            "relevance_sigmoid": round(relevance, 4),
            "novelty": round(novelty, 4),
            "harmful_penalty": round(harmful_pen, 4),
            "unexperienced_penalty": round(unexp_pen, 4),
            "formula_version": "v2",
        },
    )


# ============================================================
# 测试
# ============================================================

def run_tests():
    """v2 共鸣值计算测试 + 与 v1 对比"""
    print("=" * 70)
    print("  共鸣值计算 v2 测试")
    print("=" * 70)
    
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
            "label": "复述锚点",
            "reaction": Reaction(
                user_id="u001", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                opinion_text="是啊，深夜地铁确实孤独，窗外的灯不属于我。",
            ),
            "opinion": "是啊，深夜地铁确实孤独，窗外的灯不属于我。",
        },
        {
            "label": "增量感悟+触发",
            "reaction": Reaction(
                user_id="u002", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                emotion_word=EmotionWord.TRIGGER,
                opinion_text="孤独不是身边没有人，是没有人知道你在哪里。"
                             "有一次在机场候机厅过夜，周围全是人但没有一个人认识我。",
            ),
            "opinion": "孤独不是身边没有人，是没有人知道你在哪里。"
                       "有一次在机场候机厅过夜，周围全是人但没有一个人认识我。",
        },
        {
            "label": "全新角度+震撼",
            "reaction": Reaction(
                user_id="u003", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                emotion_word=EmotionWord.SHOCK,
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
            "label": "仅点击+同感",
            "reaction": Reaction(
                user_id="u005", anchor_id="a001",
                reaction_type=ReactionType.RESONANCE,
                emotion_word=EmotionWord.EMPATHY,
            ),
            "opinion": None,
        },
        {
            "label": "有害标记",
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
    print(f"{'标签':<20} {'权重':>5} {'深度':>5} {'相关':>6} {'增量':>6} {'惩罚':>5} {'共鸣值':>8}")
    print("-" * 70)
    
    for case in test_cases:
        if case["opinion"]:
            op_emb = opinion_embs[emb_idx]
            emb_idx += 1
        else:
            op_emb = encoder.encode_single("") if case["reaction"].reaction_type != ReactionType.HARMFUL else np.zeros(768)
        
        score = compute_resonance_value_v2(
            reaction=case["reaction"],
            anchor=anchor,
            opinion_embedding=op_emb,
            anchor_embedding=anchor_emb,
            existing_opinion_embeddings=existing_embs,
        )
        
        if score is None:
            print(f"{case['label']:<20} {'N/A':>5} {'N/A':>5} {'N/A':>6} {'N/A':>6} {'N/A':>5} {'不计入':>8}")
        else:
            c = score.components
            pen = c['harmful_penalty'] * c['unexperienced_penalty']
            print(f"{case['label']:<20} {c['resonance_weight']:>5.1f} {c['depth']:>5.2f} "
                  f"{c['relevance_sigmoid']:>6.3f} {c['novelty']:>6.3f} "
                  f"{pen:>5.3f} {score.value:>8.4f}")
            
            if case["opinion"]:
                existing_embs.append(op_emb)
    
    # ---- Sigmoid 对比测试 ----
    print(f"\n{'='*70}")
    print(f"  Sigmoid vs 硬阈值 对比")
    print(f"{'='*70}\n")
    
    test_rels = [0.1, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.7, 0.9]
    print(f"{'relevance':>10} {'硬阈值(v1)':>12} {'sigmoid(v2)':>12} {'差异':>8}")
    print("-" * 50)
    for r in test_rels:
        hard = 1.0 if r >= 0.3 else 0.0
        sig = sigmoid_relevance(r)
        diff = sig - hard
        print(f"{r:>10.2f} {hard:>12.1f} {sig:>12.4f} {diff:>+8.4f}")
    
    # ---- 惩罚函数对比 ----
    print(f"\n{'='*70}")
    print(f"  惩罚函数对比 (线性 vs 指数)")
    print(f"{'='*70}\n")
    
    print(f"{'ratio':>8} {'线性(v1)':>10} {'指数(v2)':>10}")
    print("-" * 35)
    for ratio in [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]:
        linear = max(0, 1.0 - ratio * 2)
        exp = harmful_penalty_v2(ratio)
        print(f"{ratio:>8.2f} {linear:>10.4f} {exp:>10.4f}")
    
    # ---- 跨话题加权对比 ----
    print(f"\n{'='*70}")
    print(f"  跨话题加权对比 (计数 vs Shannon 熵)")
    print(f"{'='*70}\n")
    
    test_scenarios = [
        {"label": "1话题×5次", "records": [{"topic":"孤独"}]*5},
        {"label": "2话题×(3+2)", "records": [{"topic":"孤独"}]*3 + [{"topic":"音乐"}]*2},
        {"label": "3话题各1次", "records": [{"topic":"孤独"},{"topic":"音乐"},{"topic":"阅读"}]},
        {"label": "5话题各2次", "records": [{"topic":f"t{i}"} for i in range(5) for _ in range(2)]},
        {"label": "10话题各1次", "records": [{"topic":f"t{i}"} for i in range(10)]},
    ]
    
    print(f"{'场景':<20} {'v1(计数)':>10} {'v2(熵)':>10} {'差异':>8}")
    print("-" * 55)
    for s in test_scenarios:
        records = s["records"]
        unique = len(set(r["topic"] for r in records))
        v1_bonus = 0.15 * np.log(unique + 1)
        v2_bonus = diversity_bonus_v2(records)
        print(f"{s['label']:<20} {v1_bonus:>10.4f} {v2_bonus:>10.4f} {v2_bonus-v1_bonus:>+8.4f}")
    
    print(f"\n✅ v2 测试完成")


if __name__ == "__main__":
    run_tests()
