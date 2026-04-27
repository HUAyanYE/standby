"""
锚点重现引擎 v2 — 算法优化版

相比 v1 的核心改进：
1. 季节匹配: 从硬编码关键词 → 语义向量相似度
2. 个性化: 新增用户历史参与度加权
3. 触发评分: 多因子融合替代简单乘积
4. 群体记忆: 新增时间趋势感知
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================
# 数据结构 (复用 v1)
# ============================================================

class ReplayTrigger(Enum):
    SEASONAL = "seasonal"
    ANNIVERSARY = "anniversary"
    SOCIAL_EVENT = "social_event"
    CLASSIC_CYCLE = "classic_cycle"
    GROUP_MEMORY = "group_memory"


@dataclass
class ReplayCandidate:
    anchor_id: str
    anchor_text: str
    topics: list[str]
    trigger_type: ReplayTrigger
    trigger_score: float
    anchor_embedding: Optional[np.ndarray] = None  # v2 新增
    last_shown_ts: float = 0.0
    show_count: int = 0
    group_memory: Optional[object] = None


@dataclass
class GroupMemoryData:
    anchor_id: str
    total_reactions: int
    resonance_count: int
    opposition_count: int
    representative_opinions: list[dict]
    time_trend: Optional[dict] = None
    user_own_history: Optional[dict] = None


# ============================================================
# v2 核心算法
# ============================================================

# ---- 改进 1: 语义季节匹配 ----

# 季节锚点文本 (比关键词更丰富, 用于语义匹配)
SEASON_ANCHORS = {
    "spring": [
        "春天万物复苏", "三月花开", "新学期新开始",
        "植树节种下希望", "春风拂面", "清明时节",
    ],
    "summer": [
        "夏天蝉鸣声声", "毕业季离别", "海边旅行",
        "空调西瓜夏日", "盛夏的果实", "暑假时光",
    ],
    "autumn": [
        "秋天落叶纷飞", "中秋月圆", "金色收获季节",
        "十一国庆长假", "枫叶红了", "秋风萧瑟",
    ],
    "winter": [
        "冬天大雪纷飞", "新年新希望", "春节团圆",
        "寒冬腊月", "围巾火锅暖冬", "年末回顾",
    ],
}

def get_current_season(month: int) -> str:
    if month in (3, 4, 5): return "spring"
    elif month in (6, 7, 8): return "summer"
    elif month in (9, 10, 11): return "autumn"
    else: return "winter"


def semantic_seasonal_relevance(
    anchor_embedding: np.ndarray,
    season_embeddings: dict[str, list[np.ndarray]],
    current_season: str,
) -> float:
    """语义季节相关性 (v2)
    
    v1: 关键词匹配 — 仅匹配 topic 字符串中的关键词
    v2: 向量相似度 — 计算 anchor 与季节锚点文本的语义相似度
    
    优势:
    - "秋天来了" 能匹配 autumn, 即使 topic 标签中没有 "秋天"
    - "时间像落叶一样消逝" 能隐式匹配 autumn
    """
    if current_season not in season_embeddings:
        return 0.0
    
    season_embs = season_embeddings[current_season]
    if not season_embs:
        return 0.0
    
    # 计算与所有季节锚点的最大相似度
    similarities = [float(np.dot(anchor_embedding, se)) for se in season_embs]
    max_sim = max(similarities)
    
    # 映射到 [0, 1]: sim > 0.4 → 有季节相关性
    return max(0.0, min(1.0, (max_sim - 0.3) / 0.4))


# ---- 改进 2: 用户个性化加权 ----

def compute_user_affinity(
    user_id: str,
    anchor_topics: list[str],
    user_topic_history: dict[str, dict[str, int]],
) -> float:
    """用户对锚点话题的亲和度 (v2 新增)
    
    原理: 用户在"音乐"话题上反应越多, 相关锚点越可能引发共鸣
    
    注意: 这不制造信息茧房 — 重现不是推荐, 而是触发回忆
    - 高亲和度: 用户在这个话题上留下过深刻共鸣, 重现可能触发"群体记忆"
    - 低亲和度: 降低优先级, 但不屏蔽
    
    数据源: user_topic_history[user_id] = {"音乐": 5, "孤独": 3, ...}
    """
    if user_id not in user_topic_history:
        return 0.5  # 中性
    
    history = user_topic_history[user_id]
    total_reactions = sum(history.values())
    if total_reactions == 0:
        return 0.5
    
    # 匹配话题的反应占比
    match_count = sum(history.get(t, 0) for t in anchor_topics)
    affinity = match_count / total_reactions
    
    # 映射到 [0.5, 1.5]: 高亲和度 → 加权, 低亲和度 → 轻微降权
    return 0.5 + affinity


# ---- 改进 3: 多因子触发评分 ----

def compute_trigger_score_v2(
    candidate: ReplayCandidate,
    current_ts: float,
    user_id: Optional[str] = None,
    user_topic_history: Optional[dict] = None,
    season_embeddings: Optional[dict] = None,
) -> float:
    """触发优先级 v2: 多因子加权融合
    
    v1: score = decay × freq_penalty × trigger_weight × season_bonus
    (简单乘积, 所有因子同等重要)
    
    v2: score = w1×decay + w2×season + w3×affinity + w4×memory + w5×trigger
    (加权和, 可调各因子重要性)
    
    这样设计的原因:
    - 乘积: 任一因子为 0 → 总分为 0 (过于极端)
    - 加权和: 单因子弱时其他因子可补偿 (更灵活)
    """
    days_since = (current_ts - candidate.last_shown_ts) / 86400
    
    # 因子 1: 时间衰减 (距上次展示越久越优先)
    if days_since <= 0:
        decay = 0.0
    else:
        decay = 1.0 - 0.5 ** (days_since / 30.0)
    
    # 因子 2: 展示频率惩罚
    freq_penalty = 1.0 / (1 + 0.3 * candidate.show_count)
    
    # 因子 3: 触发类型权重
    trigger_weights = {
        ReplayTrigger.SEASONAL: 0.9,
        ReplayTrigger.ANNIVERSARY: 0.7,
        ReplayTrigger.SOCIAL_EVENT: 0.8,
        ReplayTrigger.CLASSIC_CYCLE: 0.5,
        ReplayTrigger.GROUP_MEMORY: 0.6,
    }
    trigger_base = trigger_weights.get(candidate.trigger_type, 0.5)
    
    # 因子 4: 语义季节相关性 (v2 新增, 替代关键词匹配)
    season_score = 0.5  # 默认中性
    if candidate.trigger_type == ReplayTrigger.SEASONAL and candidate.anchor_embedding is not None:
        current_month = time.localtime(current_ts).tm_mon
        current_season = get_current_season(current_month)
        if season_embeddings:
            season_score = semantic_seasonal_relevance(
                candidate.anchor_embedding, season_embeddings, current_season
            )
    
    # 因子 5: 用户亲和度 (v2 新增)
    affinity = 0.5  # 默认中性
    if user_id and user_topic_history and candidate.topics:
        affinity = compute_user_affinity(user_id, candidate.topics, user_topic_history)
    
    # 因子 6: 群体记忆信号 (如果有)
    memory_signal = 0.5
    if candidate.group_memory:
        gm = candidate.group_memory
        if gm.total_reactions > 0:
            # 共鸣比例越高, 记忆价值越大
            memory_signal = min(1.0, gm.resonance_count / max(1, gm.total_reactions) * 1.5)
    
    # 加权融合 (权重可调)
    score = (
        0.25 * decay * freq_penalty +  # 时间衰减
        0.20 * season_score +            # 季节匹配
        0.20 * affinity +                # 用户亲和度
        0.15 * memory_signal +           # 群体记忆
        0.20 * trigger_base              # 触发类型
    )
    
    return round(score, 4)


# ---- 改进 4: 群体记忆时间趋势 ----

def compute_time_trend(
    reactions_by_period: dict[str, dict],
) -> dict:
    """群体记忆时间趋势分析 (v2 新增)
    
    输入: reactions_by_period = {
        "2025-Q1": {"resonance": 30, "opposition": 5},
        "2025-Q2": {"resonance": 45, "opposition": 8},
        "2025-Q3": {"resonance": 60, "opposition": 3},
    }
    
    输出: {
        "trend": "growing",  # growing / stable / declining
        "growth_rate": 0.33, # 季度增长率
        "latest_intensity": 0.95, # 最近时段的共鸣强度
    }
    """
    if len(reactions_by_period) < 2:
        return {"trend": "insufficient_data", "growth_rate": 0, "latest_intensity": 0}
    
    periods = sorted(reactions_by_period.keys())
    counts = [reactions_by_period[p]["resonance"] for p in periods]
    
    # 简单线性趋势
    n = len(counts)
    x = np.arange(n)
    if n >= 2:
        slope = float(np.polyfit(x, counts, 1)[0])
    else:
        slope = 0.0
    
    avg_count = np.mean(counts) if counts else 1
    growth_rate = slope / avg_count if avg_count > 0 else 0
    
    if growth_rate > 0.1:
        trend = "growing"
    elif growth_rate < -0.1:
        trend = "declining"
    else:
        trend = "stable"
    
    latest_total = sum(reactions_by_period[periods[-1]].values())
    latest_intensity = min(1.0, latest_total / 50)  # 50 反应 = 满分
    
    return {
        "trend": trend,
        "growth_rate": round(growth_rate, 3),
        "latest_intensity": round(latest_intensity, 3),
    }


# ============================================================
# 测试
# ============================================================

def run_tests():
    """v2 锚点重现引擎测试"""
    print("=" * 70)
    print("  锚点重现引擎 v2 测试")
    print("=" * 70)
    
    # 时间衰减对比
    print("\n📋 时间衰减 (v1 vs v2 对比)")
    print(f"{'天数':>6} {'v1(半衰期30天)':>16} {'v2(半衰期30天)':>16}")
    print("-" * 45)
    for days in [0, 7, 14, 30, 60, 90, 180]:
        v1 = 1.0 - 0.5 ** (days / 30.0) if days > 0 else 0.0
        v2 = 1.0 - 0.5 ** (days / 30.0) if days > 0 else 0.0
        print(f"{days:>6} {v1:>16.4f} {v2:>16.4f}")
    
    # 触发评分测试
    print(f"\n{'='*70}")
    print("  多因子触发评分测试")
    print(f"{'='*70}\n")
    
    # 模拟候选
    candidates = [
        ReplayCandidate(
            anchor_id="a001",
            anchor_text="深夜独自坐在末班地铁上...",
            topics=["孤独", "城市", "地铁"],
            trigger_type=ReplayTrigger.CLASSIC_CYCLE,
            trigger_score=0,
            last_shown_ts=time.time() - 86400 * 60,  # 60 天前
            show_count=2,
        ),
        ReplayCandidate(
            anchor_id="a002",
            anchor_text="秋天来了，第一片叶子落下...",
            topics=["秋天", "落叶", "回忆"],
            trigger_type=ReplayTrigger.SEASONAL,
            trigger_score=0,
            last_shown_ts=time.time() - 86400 * 365,  # 一年前
            show_count=0,
        ),
        ReplayCandidate(
            anchor_id="a003",
            anchor_text="毕业那天，我们说好不哭...",
            topics=["毕业", "离别", "青春"],
            trigger_type=ReplayTrigger.ANNIVERSARY,
            trigger_score=0,
            last_shown_ts=time.time() - 86400 * 180,  # 半年前
            show_count=1,
        ),
    ]
    
    # v1 简单评分
    print(f"{'锚点':<25} {'v1评分':>8} {'v2评分':>8} {'decay':>6} {'season':>7} {'affinity':>9}")
    print("-" * 70)
    
    user_history = {"u_test": {"孤独": 5, "城市": 3, "音乐": 2}}
    
    for c in candidates:
        # v1
        days = (time.time() - c.last_shown_ts) / 86400
        v1_decay = 1.0 - 0.5 ** (days / 30.0) if days > 0 else 0.0
        v1_freq = 1.0 / (1 + 0.3 * c.show_count)
        v1_weights = {
            ReplayTrigger.SEASONAL: 1.5, ReplayTrigger.ANNIVERSARY: 1.3,
            ReplayTrigger.SOCIAL_EVENT: 1.4, ReplayTrigger.CLASSIC_CYCLE: 1.0,
            ReplayTrigger.GROUP_MEMORY: 1.2,
        }
        v1_score = v1_decay * v1_freq * v1_weights.get(c.trigger_type, 1.0)
        
        # v2
        v2_score = compute_trigger_score_v2(
            c, time.time(),
            user_id="u_test",
            user_topic_history=user_history,
        )
        
        # 因子拆解
        decay = 1.0 - 0.5 ** (max(0, days) / 30.0) if days > 0 else 0.0
        aff = compute_user_affinity("u_test", c.topics, user_history)
        
        print(f"{c.anchor_id + ' ' + c.topics[0]:<25} {v1_score:>8.4f} {v2_score:>8.4f} {decay:>6.3f} {c.trigger_type.value[:6]:>7} {aff:>9.3f}")
    
    # 时间趋势测试
    print(f"\n{'='*70}")
    print("  群体记忆时间趋势")
    print(f"{'='*70}\n")
    
    trend_data = {
        "2025-Q1": {"resonance": 20, "opposition": 3},
        "2025-Q2": {"resonance": 35, "opposition": 5},
        "2025-Q3": {"resonance": 48, "opposition": 4},
        "2025-Q4": {"resonance": 62, "opposition": 6},
    }
    trend = compute_time_trend(trend_data)
    print(f"  趋势: {trend['trend']}")
    print(f"  增长率: {trend['growth_rate']:.1%}")
    print(f"  最近强度: {trend['latest_intensity']:.2f}")
    
    print(f"\n✅ v2 测试完成")


if __name__ == "__main__":
    run_tests()
