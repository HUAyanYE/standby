"""
Governance Engine 单元测试

基于实际 API:
- evaluate_governance_v2(reactions, marker_credits, ...)
- detect_coordinated_marking_v2(mark_timestamps, marker_ids, ...)
- update_marker_credit_v2(marker, was_accurate, ...)
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestContentReaction:
    """内容反应数据结构测试"""
    
    def test_reaction_creation(self):
        from governance_engine.rule_governance_v2 import ContentReaction
        
        reaction = ContentReaction(
            anchor_id="test_anchor",
            resonance=10,
            neutral=5,
            opposition=2,
            harmful=1,
        )
        
        assert reaction.anchor_id == "test_anchor"
        assert reaction.total == 18
    
    def test_ratios(self):
        from governance_engine.rule_governance_v2 import ContentReaction
        
        reaction = ContentReaction(
            anchor_id="test_anchor",
            resonance=50,
            neutral=30,
            opposition=10,
            harmful=10,
        )
        
        assert abs(reaction.resonance_ratio - 0.5) < 0.01
        assert abs(reaction.harmful_ratio - 0.1) < 0.01
        assert reaction.total == 100


class TestGovernanceEvaluation:
    """治理评估测试"""
    
    def test_normal_content_evaluation(self):
        from governance_engine.rule_governance_v2 import (
            evaluate_governance_v2, ContentReaction, GovernanceLevel
        )
        
        reactions = ContentReaction(
            anchor_id="test_anchor",
            resonance=50,
            neutral=30,
            opposition=10,
            harmful=0,
        )
        
        decision = evaluate_governance_v2(
            reactions=reactions,
            marker_credits=[0.5] * 10,
        )
        
        # 无害内容应为正常级别
        assert decision.level == GovernanceLevel.NORMAL
        # 返回的决策对象应包含正确的元数据
        assert decision.harmful_weight == 0.0
        assert decision.marker_avg_credit == 0.5
    
    def test_harmful_content_detection(self):
        from governance_engine.rule_governance_v2 import (
            evaluate_governance_v2, ContentReaction, GovernanceLevel
        )
        
        # 大量有害标记
        reactions = ContentReaction(
            anchor_id="test_anchor",
            resonance=5,
            neutral=5,
            opposition=5,
            harmful=85,  # 85% 有害
        )
        
        decision = evaluate_governance_v2(
            reactions=reactions,
            marker_credits=[0.8] * 20,  # 高信用标记者
        )
        
        # 有害内容应该被限制或移除（使用枚举比较）
        assert decision.level in [
            GovernanceLevel.DEMOTED,
            GovernanceLevel.SUSPENDED,
            GovernanceLevel.REMOVED,
        ]


class TestCoordinatedMarkingDetection:
    """协调标记检测测试"""
    
    def test_normal_marking_pattern(self):
        from governance_engine.rule_governance_v2 import detect_coordinated_marking_v2
        
        # 正常标记模式：不同用户、分散时间
        marker_ids = [f"user_{i}" for i in range(10)]
        timestamps = [time.time() - i * 3600 for i in range(10)]  # 每小时一个
        
        is_coordinated, reason = detect_coordinated_marking_v2(
            mark_timestamps=timestamps,
            marker_ids=marker_ids,
        )
        
        assert is_coordinated == False
    
    def test_coordinated_attack_detection(self):
        from governance_engine.rule_governance_v2 import detect_coordinated_marking_v2
        
        # 协调攻击：相同用户、短时间大量标记
        marker_ids = ["attacker"] * 50
        timestamps = [time.time() - i * 0.1 for i in range(50)]  # 5 秒内 50 个
        
        is_coordinated, reason = detect_coordinated_marking_v2(
            mark_timestamps=timestamps,
            marker_ids=marker_ids,
            time_window_seconds=10,
            threshold=10,
        )
        
        assert is_coordinated == True


class TestMarkerCreditUpdate:
    """标记者信用更新测试"""
    
    def test_positive_credit_update(self):
        from governance_engine.rule_governance_v2 import (
            update_marker_credit_v2, MarkerRecord
        )
        
        marker = MarkerRecord(
            token_hash="test_marker",
            credit_score=0.5,
            total_marks=10,
            accurate_marks=5,
        )
        
        updated = update_marker_credit_v2(
            marker=marker,
            was_accurate=True,
        )
        
        # 准确标记应该增加信用
        assert updated.credit_score >= marker.credit_score
    
    def test_negative_credit_update(self):
        from governance_engine.rule_governance_v2 import (
            update_marker_credit_v2, MarkerRecord
        )
        
        marker = MarkerRecord(
            token_hash="test_marker",
            credit_score=0.5,
            total_marks=10,
            accurate_marks=5,
        )
        
        updated = update_marker_credit_v2(
            marker=marker,
            was_accurate=False,
        )
        
        # 不准确标记应该减少信用
        assert updated.credit_score <= marker.credit_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
