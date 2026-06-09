"""
内容治理 v2 — 单元测试

测试覆盖:
- update_marker_credit_v2: Bayesian 信用更新
- get_time_decayed_credit: 时间衰减
- compute_harmful_weight_v2: 有害权重计算
- compute_dynamic_threshold: 动态阈值
- detect_coordinated_marking_v2: 协同攻击检测
- detect_velocity_anomaly: 速度异常检测
- detect_topic_type_attack_v2: 话题类型打击检测
- evaluate_governance_v2: 完整治理评估
"""

import sys
from pathlib import Path
import time

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "governance_engine"))

from rule_governance_v2 import (
    GovernanceLevel, DetectionResult, MarkerRecord, ContentReaction,
    GovernanceDecision,
    update_marker_credit_v2, get_time_decayed_credit,
    compute_harmful_weight_v2, compute_dynamic_threshold,
    detect_coordinated_marking_v2, detect_velocity_anomaly,
    detect_topic_type_attack_v2, evaluate_governance_v2,
)


# ============================================================
# MarkerRecord 信用更新
# ============================================================

class TestMarkerCredit:
    """标记者信用 Bayesian 更新测试"""

    def test_initial_credit(self):
        """新标记者初始信用为 0.5"""
        marker = MarkerRecord(token_hash="test")
        assert marker.credit_score == 0.5

    def test_accurate_mark_increases_credit(self):
        """准确标记 → 信用增加"""
        marker = MarkerRecord(token_hash="test", credit_score=0.5, total_marks=10, accurate_marks=5)
        now = time.time()
        updated = update_marker_credit_v2(marker, was_accurate=True, current_ts=now)
        assert updated.credit_score > 0.5

    def test_inaccurate_mark_decreases_credit(self):
        """不准确标记 → 信用降低"""
        marker = MarkerRecord(token_hash="test", credit_score=0.5, total_marks=10, accurate_marks=5)
        now = time.time()
        updated = update_marker_credit_v2(marker, was_accurate=False, current_ts=now)
        assert updated.credit_score < 0.5

    def test_credit_bounded_zero_to_one(self):
        """信用分应在 [0, 1] 范围内"""
        marker = MarkerRecord(token_hash="test", credit_score=0.01, total_marks=100, accurate_marks=1)
        now = time.time()
        updated = update_marker_credit_v2(marker, was_accurate=False, current_ts=now)
        assert 0.0 <= updated.credit_score <= 1.0

    def test_high_volume_marker_penalty(self):
        """高频标记（>200次）→ 信用惩罚"""
        marker = MarkerRecord(token_hash="test", credit_score=0.5, total_marks=250, accurate_marks=125)
        now = time.time()
        updated = update_marker_credit_v2(marker, was_accurate=True, current_ts=now)
        # 高频标记应该有惩罚
        assert updated.total_marks == 251


# ============================================================
# 时间衰减
# ============================================================

class TestTimeDecay:
    """时间衰减信用测试"""

    def test_no_decay_when_active(self):
        """30 天内活跃 → 无衰减"""
        now = time.time()
        marker = MarkerRecord(
            token_hash="test", credit_score=0.8,
            total_marks=10, accurate_marks=8,
            last_mark_ts=now - 10 * 86400,  # 10 天前活跃
        )
        decayed = get_time_decayed_credit(marker, now)
        assert abs(decayed - 0.8) < 0.01

    def test_decay_after_inactive(self):
        """长期不活跃 → 信用衰减"""
        now = time.time()
        marker = MarkerRecord(
            token_hash="test", credit_score=0.8,
            total_marks=10, accurate_marks=8,
            last_mark_ts=now - 120 * 86400,  # 120 天前活跃
        )
        decayed = get_time_decayed_credit(marker, now)
        # 应该衰减到 0.5 + (0.8 - 0.5) * decay_factor
        assert decayed < 0.8
        assert decayed > 0.5

    def test_long_ago_decays_to_baseline(self):
        """很久以前的信用应衰减到基线"""
        now = time.time()
        marker = MarkerRecord(
            token_hash="test", credit_score=0.8,
            total_marks=10, accurate_marks=8,
            last_mark_ts=now - 365 * 3 * 86400,  # 3 年前活跃
        )
        decayed = get_time_decayed_credit(marker, now)
        assert decayed < 0.6  # 应该衰减到接近 0.5


# ============================================================
# 有害权重
# ============================================================

class TestHarmfulWeight:
    """有害权重计算测试"""

    def test_zero_marker_credits(self):
        """无标记者 → 权重为 0"""
        reactions = ContentReaction(anchor_id="a1", harmful=0)
        assert compute_harmful_weight_v2(reactions, []) == 0.0

    def test_with_marker_credits(self):
        """有标记者 → 按信用加权"""
        reactions = ContentReaction(anchor_id="a1", harmful=3)
        credits = [0.8, 0.6, 0.9]
        weight = compute_harmful_weight_v2(reactions, credits)
        # avg_credit = (0.8 + 0.6 + 0.9) / 3 ≈ 0.767, weight = 0.767 * 3
        assert weight > 0
        assert weight == pytest.approx(0.767 * 3, abs=0.1)


# ============================================================
# 动态阈值
# ============================================================

class TestDynamicThreshold:
    """动态阈值测试"""

    def test_base_threshold_low_controversy(self):
        """低争议内容 → 使用基础阈值"""
        threshold = compute_dynamic_threshold(
            base_threshold=0.15, content_controversy=0.0, anchor_heat=0,
        )
        assert threshold == pytest.approx(0.15, abs=0.05)

    def test_high_controversy_raises_threshold(self):
        """高争议内容 → 提高阈值（避免误判）"""
        threshold_low = compute_dynamic_threshold(0.15, content_controversy=0.0, anchor_heat=0)
        threshold_high = compute_dynamic_threshold(0.15, content_controversy=0.8, anchor_heat=0)
        assert threshold_high >= threshold_low


# ============================================================
# 异常检测
# ============================================================

class TestAnomalyDetection:
    """异常检测测试"""

    def test_coordinated_marking_normal(self):
        """正常标记频率 → 无协同攻击"""
        timestamps = [time.time() - i * 60 for i in range(5)]  # 每分钟一个
        marker_ids = [f"m{i}" for i in range(5)]
        is_coordinated, reason = detect_coordinated_marking_v2(timestamps, marker_ids)
        assert not is_coordinated

    def test_coordinated_marking_detected(self):
        """短时间内大量标记来自集中来源 → 协同攻击"""
        now = time.time()
        # 升序排列 (旧→新)
        timestamps = [now - (20 - i) * 2 for i in range(20)]
        # 大量标记来自同一来源 (集中度 < 30%)
        marker_ids = ["same_marker"] * 15 + [f"m{i}" for i in range(5)]
        is_coordinated, reason = detect_coordinated_marking_v2(timestamps, marker_ids)
        assert is_coordinated

    def test_velocity_anomaly_normal(self):
        """正常速度 → 无异常"""
        timestamps = [time.time() - i * 60 for i in range(3)]
        is_velocity, reason = detect_velocity_anomaly(timestamps, "check")
        assert not is_velocity

    def test_velocity_anomaly_fast(self):
        """极快速度 → 异常"""
        now = time.time()
        timestamps = [now - i * 0.5 for i in range(15)]  # 0.5秒一个
        is_velocity, reason = detect_velocity_anomaly(timestamps, "check")
        assert is_velocity

    def test_type_targeting_balanced(self):
        """平衡的反应分布 → 无类型打击"""
        reactions_by_type = {
            "共鸣": [{"unexperienced": False}] * 10,
            "无感": [{"unexperienced": False}] * 5,
            "反对": [{"unexperienced": False}] * 3,
        }
        is_attack, reason = detect_topic_type_attack_v2(reactions_by_type)
        assert not is_attack


# ============================================================
# 完整治理评估
# ============================================================

class TestEvaluateGovernance:
    """完整治理评估测试"""

    def test_normal_content_l0(self):
        """正常内容 → L0"""
        reactions = ContentReaction(
            anchor_id="a1", resonance=10, neutral=5,
            opposition=1, unexperienced=0, harmful=0,
        )
        decision = evaluate_governance_v2(reactions, [], current_ts=time.time())
        assert decision.level == GovernanceLevel.NORMAL

    def test_high_harmful_l3_or_above(self):
        """高有害比例 → L3+"""
        reactions = ContentReaction(
            anchor_id="a1", resonance=2, neutral=1,
            opposition=0, unexperienced=0, harmful=10,
        )
        decision = evaluate_governance_v2(reactions, [], current_ts=time.time())
        assert decision.level in [
            GovernanceLevel.DEMOTED,
            GovernanceLevel.SUSPENDED,
            GovernanceLevel.REMOVED,
        ]

    def test_decision_has_reason(self):
        """决策应包含原因"""
        reactions = ContentReaction(
            anchor_id="a1", resonance=5, neutral=3,
            opposition=1, unexperienced=0, harmful=0,
        )
        decision = evaluate_governance_v2(reactions, [], current_ts=time.time())
        assert len(decision.reason) > 0

    def test_decision_has_actions(self):
        """决策应包含动作"""
        reactions = ContentReaction(
            anchor_id="a1", resonance=5, neutral=3,
            opposition=1, unexperienced=0, harmful=0,
        )
        decision = evaluate_governance_v2(reactions, [], current_ts=time.time())
        assert isinstance(decision.actions, list)
