"""
内容治理引擎 v2 — 算法优化版

相比 v1 的核心改进：
1. 标记者信用: 新增时间衰减 + Bayesian 平滑
2. 异常检测: 实现了 detect_topic_type_attack (v1 未实现)
3. 新增: 速度异常检测 (velocity-based)
4. 分级响应: 动态阈值替代固定阈值
5. 冲突仲裁: 更精细的信用分析
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math
import time

import numpy as np


# ============================================================
# 数据结构 (复用 v1)
# ============================================================

class GovernanceLevel(Enum):
    NORMAL = "L0_正常"
    OBSERVING = "L1_观察"
    DEMOTED = "L2_降权"
    SUSPENDED = "L3_暂停"
    REMOVED = "L4_移除"
    CONFLICT = "争议"


class DetectionResult(Enum):
    CLEAN = "安全"
    SUSPECT = "可疑"
    HARMFUL = "有害"
    CONFLICT = "争议"


@dataclass
class MarkerRecord:
    token_hash: str
    credit_score: float = 0.5
    total_marks: int = 0
    accurate_marks: int = 0
    last_mark_ts: float = 0.0  # v2 新增: 最近标记时间


@dataclass
class ContentReaction:
    anchor_id: str
    resonance: int = 0
    neutral: int = 0
    opposition: int = 0
    unexperienced: int = 0
    harmful: int = 0
    
    @property
    def total(self) -> int:
        return self.resonance + self.neutral + self.opposition + self.unexperienced + self.harmful
    
    @property
    def harmful_ratio(self) -> float:
        return self.harmful / max(1, self.total)
    
    @property
    def unexperienced_ratio(self) -> float:
        return self.unexperienced / max(1, self.total)
    
    @property
    def resonance_ratio(self) -> float:
        return self.resonance / max(1, self.total)


@dataclass
class GovernanceDecision:
    level: GovernanceLevel
    detection: DetectionResult
    harmful_weight: float
    marker_avg_credit: float
    reason: str
    actions: list[str] = field(default_factory=list)


# ============================================================
# v2 核心算法
# ============================================================

# ---- 改进 1: Bayesian 平滑的标记者信用 ----

def update_marker_credit_v2(
    marker: MarkerRecord,
    was_accurate: bool,
    prior_alpha: float = 2.0,
    prior_beta: float = 2.0,
    current_ts: Optional[float] = None,
) -> MarkerRecord:
    """标记者信用 v2: Bayesian Beta 分布
    
    v1 问题: credit = accuracy × volume_weight
    - 新用户 1 次标记 → credit = 0 或 1.0 (极端)
    - 没有"初始不确定性"的概念
    
    v2 方案: Bayesian Beta(α, β) 后验分布
    - 先验: Beta(prior_alpha, prior_beta) = Beta(2, 2) → 中性偏保守
    - 每次准确: α += 1
    - 每次误判: β += 1
    - 后验均值 = α / (α + β)
    
    好处:
    - 新用户: credit = 2/(2+2) = 0.5 (合理中性)
    - 1 次准确: credit = 3/(3+2) = 0.6 (温和提升)
    - 5 次全准确: credit = 7/(7+2) = 0.78 (逐步建立)
    - 比 v1 的 0→1.0 跳变更平滑
    """
    marker.total_marks += 1
    if was_accurate:
        marker.accurate_marks += 1
    
    # Bayesian 后验
    alpha = prior_alpha + marker.accurate_marks
    beta = prior_beta + (marker.total_marks - marker.accurate_marks)
    posterior_mean = alpha / (alpha + beta)
    
    # 标记量异常惩罚 (>200 次标记 → 可疑)
    if marker.total_marks > 200:
        volume_penalty = 0.7
    elif marker.total_marks < 5:
        volume_penalty = 0.8  # 样本不足, 略微降低
    else:
        volume_penalty = 1.0
    
    marker.credit_score = round(min(1.0, max(0.0, posterior_mean * volume_penalty)), 4)
    
    if current_ts:
        marker.last_mark_ts = current_ts
    
    return marker


def get_time_decayed_credit(
    marker: MarkerRecord,
    current_ts: float,
    decay_half_life_days: float = 90.0,
) -> float:
    """时间衰减信用 (v2 新增)
    
    v1 问题: 信用分是静态的, 不随时间衰减
    - 用户 6 个月前标记准确, 之后不再标记
    - 信用分不变 → 过时的高信用可能被滥用
    
    v2 方案: 信用随"无标记活动"的时间衰减
    - 最近有标记 → 信用不变
    - 久未标记 → 信用缓慢衰减至先验值 0.5
    """
    if marker.last_mark_ts <= 0:
        return marker.credit_score  # 无时间信息, 不衰减
    
    days_inactive = (current_ts - marker.last_mark_ts) / 86400
    
    if days_inactive <= 30:
        return marker.credit_score  # 30 天内活跃, 不衰减
    
    # 衰减向 0.5 (先验值) 收敛
    decay_factor = 0.5 ** ((days_inactive - 30) / decay_half_life_days)
    decayed = 0.5 + (marker.credit_score - 0.5) * decay_factor
    return round(max(0.5, min(1.0, decayed)), 4)  # 不低于先验值


def compute_harmful_weight_v2(
    reactions: ContentReaction,
    marker_credits: list[float],
) -> float:
    """有害加权总分 v2"""
    if not marker_credits:
        return 0.0
    # 使用信用加权平均 × 有害标记数
    avg_credit = sum(marker_credits) / len(marker_credits)
    return avg_credit * reactions.harmful


# ---- 改进 2: 动态阈值 ----

def compute_dynamic_threshold(
    base_threshold: float,
    content_controversy: float = 0.0,
    anchor_heat: int = 0,
) -> float:
    """动态阈值 (v2 新增)
    
    v1: 固定阈值 0.15 / 0.25
    v2: 根据内容争议度和锚点热度动态调整
    
    - 争议性话题: 有害阈值自动提高 (避免正常讨论被误判)
    - 热门内容: 阈值适当提高 (高流量下恶意标记也更多)
    """
    # 争议度: 共鸣/反对比例越接近 → 争议度越高
    controversy_factor = 1.0 + 0.5 * content_controversy  # [1.0, 1.5]
    
    # 热度: 反应越多, 阈值越高 (但有上限)
    heat_factor = 1.0 + 0.3 * min(1.0, anchor_heat / 200)  # [1.0, 1.3]
    
    return base_threshold * controversy_factor * heat_factor


# ---- 改进 3: 话题类型打击检测 (v1 未实现) ----

def detect_topic_type_attack_v2(
    reactions_by_type: dict[str, list[dict]],
    unexperienced_threshold: float = 0.4,
    min_samples: int = 10,
) -> tuple[bool, str]:
    """检测观点类型打击: 某类反应被系统性标记为未体验
    
    场景: 攻击者针对"反对"类型的观点批量标记"未体验"
    试图压制异见, 制造"一致性假象"
    
    检测方法:
    1. 按反应类型统计各类型的未体验标记率
    2. 如果某类型的未体验率显著高于整体平均 → 异常
    3. 卡方检验: 观察值 vs 期望值的偏离程度
    """
    total_reactions = sum(len(v) for v in reactions_by_type.values())
    if total_reactions < min_samples:
        return False, "样本不足"
    
    # 整体未体验率
    total_unexp = sum(
        1 for reactions in reactions_by_type.values()
        for r in reactions
        if r.get("unexperienced", False)
    )
    overall_rate = total_unexp / total_reactions if total_reactions > 0 else 0
    
    # 检查各类型的未体验率
    anomalies = []
    for rtype, reactions in reactions_by_type.items():
        type_total = len(reactions)
        if type_total < 5:
            continue
        type_unexp = sum(1 for r in reactions if r.get("unexperienced", False))
        type_rate = type_unexp / type_total
        
        # 如果某类型的未体验率 > 整体的 2 倍 且超过阈值
        if type_rate > unexperienced_threshold and type_rate > overall_rate * 2:
            anomalies.append(f"{rtype}: {type_rate:.0%} (整体{overall_rate:.0%})")
    
    if anomalies:
        return True, f"类型打击检测: {'; '.join(anomalies)}"
    return False, "正常"


# ---- 改进 4: 速度异常检测 (v2 新增) ----

def detect_velocity_anomaly(
    reaction_timestamps: list[float],
    user_id: str,
    window_seconds: float = 60,
    max_reactions: int = 10,
) -> tuple[bool, str]:
    """速度异常检测: 短时间内大量反应
    
    场景: 机器人/脚本在 1 分钟内对大量锚点做出反应
    检测: 滑动窗口内反应数超过阈值
    """
    if len(reaction_timestamps) < max_reactions:
        return False, "正常"
    
    sorted_ts = sorted(reaction_timestamps)
    
    # 滑动窗口
    for i in range(len(sorted_ts) - max_reactions + 1):
        window_start = sorted_ts[i]
        window_end = sorted_ts[i + max_reactions - 1]
        if window_end - window_start <= window_seconds:
            return True, f"速度异常: {max_reactions}次/{window_seconds}秒内"
    
    return False, "正常"


def detect_coordinated_marking_v2(
    mark_timestamps: list[float],
    marker_ids: list[str],
    time_window_seconds: float = 300,
    threshold: int = 10,
) -> tuple[bool, str]:
    """协同攻击检测 v2: 考虑标记者来源聚集度
    
    v1: 只看时间窗口内的标记数量
    v2: 同时检测标记者来源是否异常集中
    
    如果短时间内大量标记来自同一来源 → 更可能是协同攻击
    """
    if len(mark_timestamps) < threshold:
        return False, "正常"
    
    sorted_pairs = sorted(zip(mark_timestamps, marker_ids))
    
    for i in range(len(sorted_pairs) - threshold + 1):
        window = sorted_pairs[i:i + threshold]
        time_span = window[-1][0] - window[0][0]
        
        if time_span <= time_window_seconds:
            # 检查来源聚集度
            markers_in_window = [p[1] for p in window]
            unique_markers = len(set(markers_in_window))
            
            # 如果来源过于集中 (< 30% 独立来源)
            concentration = unique_markers / threshold
            if concentration < 0.3:
                return True, f"协同攻击: {threshold}次/{time_span:.0f}秒, 仅{unique_markers}个独立来源"
            else:
                # 时间集中但来源分散, 可能是正常热门内容
                return False, f"密集标记但来源分散({unique_markers}独立来源), 可能是热门内容"
    
    return False, "正常"


# ---- 改进 5: 分级响应 v2 ----

def evaluate_governance_v2(
    reactions: ContentReaction,
    marker_credits: list[float],
    base_threshold: float = 0.15,
    min_samples: int = 10,
    current_ts: Optional[float] = None,
) -> GovernanceDecision:
    """评估内容治理级别 v2
    
    v2 改进:
    - 动态阈值 (考虑争议度和热度)
    - 更精细的冲突仲裁
    - 考虑标记的时间分布
    """
    total = reactions.total
    harmful_weight = compute_harmful_weight_v2(reactions, marker_credits)
    
    # 时间衰减信用 (v2)
    if current_ts:
        decayed_credits = [
            get_time_decayed_credit(
                MarkerRecord(token_hash="", credit_score=c, last_mark_ts=current_ts - 86400 * 60),
                current_ts
            )
            for c in marker_credits
        ] if marker_credits else []
        avg_credit = sum(decayed_credits) / len(decayed_credits) if decayed_credits else 0.5
    else:
        avg_credit = sum(marker_credits) / max(1, len(marker_credits))
    
    # 样本不足
    if total < min_samples:
        return GovernanceDecision(
            level=GovernanceLevel.NORMAL,
            detection=DetectionResult.CLEAN,
            harmful_weight=harmful_weight,
            marker_avg_credit=avg_credit,
            reason=f"样本不足 ({total} < {min_samples})",
        )
    
    harmful_r = reactions.harmful_ratio
    resonance_r = reactions.resonance_ratio
    
    # 动态阈值 (v2)
    controversy = 1.0 - abs(resonance_r - 0.5) * 2  # 共鸣率越接近 0.5, 争议度越高
    dynamic_threshold = compute_dynamic_threshold(
        base_threshold, controversy, total
    )
    
    # 共鸣/有害冲突检测
    if harmful_r > base_threshold and resonance_r > 0.3:
        # 更精细的冲突仲裁
        if avg_credit < 0.3:
            # 标记者信用低 → 大概率恶意刷标
            return GovernanceDecision(
                level=GovernanceLevel.OBSERVING,
                detection=DetectionResult.CLEAN,
                harmful_weight=harmful_weight,
                marker_avg_credit=avg_credit,
                reason=f"有害标记者信用低({avg_credit:.2f}), 可能是恶意刷标",
                actions=["记录观察", "降低该批标记权重"],
            )
        else:
            return GovernanceDecision(
                level=GovernanceLevel.CONFLICT,
                detection=DetectionResult.CONFLICT,
                harmful_weight=harmful_weight,
                marker_avg_credit=avg_credit,
                reason=f"共鸣/有害冲突 (有害{harmful_r:.0%}, 共鸣{resonance_r:.0%})",
                actions=["标记为争议", "共鸣权重×0.5", "展示正反双方观点"],
            )
    
    # 分级响应 (使用动态阈值)
    if harmful_r >= dynamic_threshold * 2.5 and avg_credit > 0.4:
        return GovernanceDecision(
            level=GovernanceLevel.REMOVED,
            detection=DetectionResult.HARMFUL,
            harmful_weight=harmful_weight,
            marker_avg_credit=avg_credit,
            reason=f"有害标记严重 ({harmful_r:.0%}, 阈值{dynamic_threshold:.0%})",
            actions=["停止展示", "通知作者", "提供申诉入口"],
        )
    elif harmful_r >= dynamic_threshold * 1.5 and avg_credit > 0.4:
        return GovernanceDecision(
            level=GovernanceLevel.SUSPENDED,
            detection=DetectionResult.HARMFUL,
            harmful_weight=harmful_weight,
            marker_avg_credit=avg_credit,
            reason=f"有害标记显著 ({harmful_r:.0%})",
            actions=["暂停展示", "进入复核队列"],
        )
    elif harmful_r >= dynamic_threshold and avg_credit > 0.4:
        return GovernanceDecision(
            level=GovernanceLevel.DEMOTED,
            detection=DetectionResult.SUSPECT,
            harmful_weight=harmful_weight,
            marker_avg_credit=avg_credit,
            reason=f"有害标记达到阈值 ({harmful_r:.0%})",
            actions=["降低展示优先级"],
        )
    elif harmful_r > 0:
        return GovernanceDecision(
            level=GovernanceLevel.OBSERVING,
            detection=DetectionResult.CLEAN,
            harmful_weight=harmful_weight,
            marker_avg_credit=avg_credit,
            reason=f"少量有害标记 ({harmful_r:.0%}), 记录观察",
        )
    else:
        return GovernanceDecision(
            level=GovernanceLevel.NORMAL,
            detection=DetectionResult.CLEAN,
            harmful_weight=harmful_weight,
            marker_avg_credit=avg_credit,
            reason="无异常信号",
        )


# ============================================================
# 测试
# ============================================================

def run_tests():
    """v2 治理引擎测试"""
    print("=" * 70)
    print("  内容治理引擎 v2 测试")
    print("=" * 70)
    
    # Bayesian 信用测试
    print("\n--- Bayesian 信用 v2 测试 ---")
    m = MarkerRecord(token_hash="test")
    print(f"  初始信用: {m.credit_score}")
    
    for was_acc in [True, True, True, False, True, False, True]:
        m = update_marker_credit_v2(m, was_acc)
    
    print(f"  7次标记(5准2误): {m.credit_score}")
    print(f"  对比 v1 (5/7 × volume): {round((5/7) * 1.0, 4)}")
    
    # 时间衰减测试
    print("\n--- 时间衰减信用测试 ---")
    now = time.time()
    m_active = MarkerRecord(token_hash="a", credit_score=0.8, last_mark_ts=now - 86400 * 10)
    m_idle = MarkerRecord(token_hash="b", credit_score=0.8, last_mark_ts=now - 86400 * 180)
    
    print(f"  活跃用户(10天前): {get_time_decayed_credit(m_active, now):.4f}")
    print(f"  闲置用户(180天前): {get_time_decayed_credit(m_idle, now):.4f}")
    
    # 动态阈值测试
    print("\n--- 动态阈值测试 ---")
    print(f"  {'场景':<20} {'基础阈值':>10} {'动态阈值':>10}")
    print(f"  {'-'*45}")
    scenarios = [
        ("普通内容", 0.15, 0.0, 10),
        ("争议话题", 0.15, 0.8, 10),
        ("热门内容", 0.15, 0.0, 500),
        ("争议+热门", 0.15, 0.9, 300),
    ]
    for name, base, controv, heat in scenarios:
        dynamic = compute_dynamic_threshold(base, controv, heat)
        print(f"  {name:<20} {base:>10.2f} {dynamic:>10.2f}")
    
    # 话题类型打击检测
    print("\n--- 话题类型打击检测 ---")
    normal_data = {
        "共鸣": [{"unexperienced": False}] * 40 + [{"unexperienced": True}] * 2,
        "反对": [{"unexperienced": False}] * 15 + [{"unexperienced": True}] * 1,
    }
    attack_data = {
        "共鸣": [{"unexperienced": False}] * 40 + [{"unexperienced": True}] * 1,
        "反对": [{"unexperienced": False}] * 5 + [{"unexperienced": True}] * 12,
    }
    
    is_anomaly, reason = detect_topic_type_attack_v2(normal_data)
    print(f"  正常数据: {'异常' if is_anomaly else '正常'} — {reason}")
    
    is_anomaly, reason = detect_topic_type_attack_v2(attack_data)
    print(f"  攻击数据: {'异常' if is_anomaly else '正常'} — {reason}")
    
    # 速度异常检测
    print("\n--- 速度异常检测 ---")
    normal_ts = [1000 + i * 3600 for i in range(15)]
    bot_ts = [1000 + i * 3 for i in range(15)]
    
    is_anomaly, reason = detect_velocity_anomaly(normal_ts, "u1")
    print(f"  正常节奏(15次/天): {'异常' if is_anomaly else '正常'}")
    
    is_anomaly, reason = detect_velocity_anomaly(bot_ts, "u2")
    print(f"  机器人(15次/5秒): {'异常' if is_anomaly else '正常'} — {reason}")
    
    # 分级响应 v2
    print("\n--- 分级响应 v2 ---")
    test_cases = [
        {"name": "正常内容", "reactions": ContentReaction("a1", resonance=50, neutral=20, harmful=1)},
        {"name": "争议内容", "reactions": ContentReaction("a6", resonance=40, neutral=10, harmful=20)},
        {"name": "高有害", "reactions": ContentReaction("a5", resonance=10, neutral=5, harmful=50)},
    ]
    
    for tc in test_cases:
        r = tc["reactions"]
        credits = [0.5] * r.harmful
        decision = evaluate_governance_v2(r, credits)
        print(f"  {tc['name']:10} (有害{r.harmful_ratio:.0%}) → {decision.level.value} | {decision.reason[:40]}")
    
    print(f"\n✅ v2 测试完成")


if __name__ == "__main__":
    run_tests()
