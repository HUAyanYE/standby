"""
内容治理引擎 - 规则层

实现不需要 ML 模型的治理规则：
1. 关键词/哈希黑名单匹配
2. 标记者信用计算
3. 分级响应判定
4. 共鸣/有害冲突仲裁
5. 异常模式检测（基础版）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
# 数据结构
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
    """标记者记录"""
    token_hash: str
    credit_score: float = 0.5
    total_marks: int = 0
    accurate_marks: int = 0


@dataclass
class ContentReaction:
    """内容的反应统计"""
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
    """治理决策"""
    level: GovernanceLevel
    detection: DetectionResult
    harmful_weight: float
    marker_avg_credit: float
    reason: str
    actions: list[str] = field(default_factory=list)


# ============================================================
# 关键词黑名单（示例，实际需要维护完整列表）
# ============================================================

BLACKLIST_KEYWORDS = {
    "违法": ["赌博", "毒品", "枪支", "炸药"],
    "色情": [],  # 实际需要更完整的列表
    "垃圾营销": ["加微信", "扫码领", "免费领取", "点击链接"],
    "人身攻击": ["傻逼", "废物", "滚出去"],
}

BLACKLIST_HASHES: set[str] = set()  # 已知有害内容的哈希


# ============================================================
# 标记者信用评估
# ============================================================

def update_marker_credit(
    marker: MarkerRecord,
    was_accurate: bool,
) -> MarkerRecord:
    """更新标记者信用"""
    marker.total_marks += 1
    if was_accurate:
        marker.accurate_marks += 1
    
    # 准确率
    accuracy = marker.accurate_marks / marker.total_marks
    
    # 标记量加权
    if marker.total_marks < 5:
        volume_weight = 0.5  # 样本不足
    elif marker.total_marks <= 200:
        volume_weight = 1.0
    else:
        volume_weight = 0.7  # 过多标记，可疑
    
    marker.credit_score = round(min(1.0, max(0.0, accuracy * volume_weight)), 4)
    return marker


def compute_harmful_weight(
    reactions: ContentReaction,
    marker_credits: list[float],
) -> float:
    """计算有害标记的加权总分
    
    高信用用户的标记权重更大。
    """
    if not marker_credits:
        return 0.0
    return sum(marker_credits) / len(marker_credits) * reactions.harmful


# ============================================================
# 分级响应判定
# ============================================================

def evaluate_governance(
    reactions: ContentReaction,
    marker_credits: list[float],
    base_threshold: float = 0.15,
    min_samples: int = 10,
) -> GovernanceDecision:
    """评估内容的治理级别"""
    
    total = reactions.total
    harmful_weight = compute_harmful_weight(reactions, marker_credits)
    marker_avg_credit = sum(marker_credits) / max(1, len(marker_credits))
    
    # 样本不足
    if total < min_samples:
        return GovernanceDecision(
            level=GovernanceLevel.NORMAL,
            detection=DetectionResult.CLEAN,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason=f"样本不足 ({total} < {min_samples})",
        )
    
    harmful_r = reactions.harmful_ratio
    resonance_r = reactions.resonance_ratio
    
    # 共鸣/有害冲突检测
    if harmful_r > base_threshold and resonance_r > 0.3:
        return GovernanceDecision(
            level=GovernanceLevel.CONFLICT,
            detection=DetectionResult.CONFLICT,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason=f"共鸣/有害冲突 (有害{harmful_r:.0%}, 共鸣{resonance_r:.0%})",
            actions=["标记为争议", "共鸣权重×0.5", "展示正反双方观点"],
        )
    
    # 分级响应
    if harmful_r >= 0.4 and marker_avg_credit > 0.4:
        return GovernanceDecision(
            level=GovernanceLevel.REMOVED,
            detection=DetectionResult.HARMFUL,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason=f"有害标记严重 ({harmful_r:.0%})，标记者信用正常",
            actions=["停止展示", "通知作者", "提供申诉入口"],
        )
    elif harmful_r >= 0.25 and marker_avg_credit > 0.4:
        return GovernanceDecision(
            level=GovernanceLevel.SUSPENDED,
            detection=DetectionResult.HARMFUL,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason=f"有害标记显著 ({harmful_r:.0%})",
            actions=["暂停展示", "进入复核队列"],
        )
    elif harmful_r >= base_threshold and marker_avg_credit > 0.4:
        return GovernanceDecision(
            level=GovernanceLevel.DEMOTED,
            detection=DetectionResult.SUSPECT,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason=f"有害标记达到阈值 ({harmful_r:.0%})",
            actions=["降低展示优先级"],
        )
    elif harmful_r > 0:
        return GovernanceDecision(
            level=GovernanceLevel.OBSERVING,
            detection=DetectionResult.CLEAN,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason=f"少量有害标记 ({harmful_r:.0%})，记录观察",
        )
    else:
        return GovernanceDecision(
            level=GovernanceLevel.NORMAL,
            detection=DetectionResult.CLEAN,
            harmful_weight=harmful_weight,
            marker_avg_credit=marker_avg_credit,
            reason="无异常信号",
        )


# ============================================================
# 关键词检测
# ============================================================

def check_keywords(text: str) -> list[str]:
    """检查文本是否命中黑名单关键词"""
    hits = []
    for category, keywords in BLACKLIST_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                hits.append(f"{category}:{kw}")
    return hits


# ============================================================
# 异常模式检测（基础版）
# ============================================================

def detect_coordinated_marking(
    mark_timestamps: list[float],
    time_window_seconds: float = 300,
    threshold: int = 10,
) -> bool:
    """检测协同攻击：短时间内大量标记"""
    if len(mark_timestamps) < threshold:
        return False
    
    sorted_ts = sorted(mark_timestamps)
    for i in range(len(sorted_ts) - threshold + 1):
        if sorted_ts[i + threshold - 1] - sorted_ts[i] <= time_window_seconds:
            return True
    return False


def detect_topic_type_attack(
    reactions_by_type: dict[str, int],
    target_type: str = "opposition",
    unexperienced_threshold: float = 0.5,
) -> bool:
    """检测观点类型打击：某类反应被系统性标记为未体验"""
    total = sum(reactions_by_type.values())
    if total < 10:
        return False
    
    target_count = reactions_by_type.get(target_type, 0)
    if target_count == 0:
        return False
    
    # 检查是否该类型的观点被不成比例地标记为未体验
    # 这需要更详细的数据，这里简化为检测标记集中度
    return False  # 需要更详细的数据才能判断


# ============================================================
# 测试
# ============================================================

def run_tests():
    """运行治理规则测试"""
    print("=" * 60)
    print("  内容治理引擎 - 规则层测试")
    print("=" * 60)
    
    # 测试标记者信用
    print("\n--- 标记者信用测试 ---")
    m = MarkerRecord(token_hash="test")
    print(f"  初始信用: {m.credit_score}")
    
    m = update_marker_credit(m, was_accurate=True)
    print(f"  标记1次(准确): {m.credit_score}")
    
    for _ in range(4):
        m = update_marker_credit(m, was_accurate=True)
    print(f"  标记5次(全准确): {m.credit_score}")
    
    for _ in range(5):
        m = update_marker_credit(m, was_accurate=False)
    print(f"  标记10次(5准确+5误判): {m.credit_score}")
    
    # 测试分级响应
    print("\n--- 分级响应测试 ---")
    
    test_cases = [
        {"name": "正常内容", "reactions": ContentReaction("a1", resonance=50, neutral=20, harmful=1)},
        {"name": "观察", "reactions": ContentReaction("a2", resonance=40, neutral=20, harmful=8)},
        {"name": "降权", "reactions": ContentReaction("a3", resonance=30, neutral=20, harmful=20)},
        {"name": "暂停", "reactions": ContentReaction("a4", resonance=20, neutral=10, harmful=30)},
        {"name": "移除", "reactions": ContentReaction("a5", resonance=10, neutral=5, harmful=50)},
        {"name": "争议", "reactions": ContentReaction("a6", resonance=40, neutral=10, harmful=20)},
    ]
    
    for tc in test_cases:
        r = tc["reactions"]
        credits = [0.5] * r.harmful  # 假设标记者信用都是 0.5
        decision = evaluate_governance(r, credits)
        print(f"  {tc['name']:10} (总计{r.total}, 有害{r.harmful_ratio:.0%}, 共鸣{r.resonance_ratio:.0%})"
              f" → {decision.level.value} | {decision.reason}")
    
    # 测试协同攻击检测
    print("\n--- 协同攻击检测 ---")
    
    # 正常标记（分散在一天内）
    normal_marks = [1000 + i * 3600 for i in range(15)]
    print(f"  分散标记(15次/天): {'检测到攻击' if detect_coordinated_marking(normal_marks) else '正常'}")
    
    # 协同攻击（5分钟内集中）
    attack_marks = [1000 + i * 10 for i in range(15)]
    print(f"  集中标记(15次/5分钟): {'检测到攻击' if detect_coordinated_marking(attack_marks) else '正常'}")
    
    print(f"\n✅ 测试完成")


if __name__ == "__main__":
    run_tests()
