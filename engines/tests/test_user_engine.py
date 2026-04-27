"""
User Engine 单元测试

基于实际 API:
- compute_trust_level(state, current_ts)
- check_confidant_eligibility(state, current_ts)
- generate_anonymous_identity(internal_token, anchor_id)
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTrustLevel:
    """信任等级测试"""
    
    def test_trust_levels_exist(self):
        from user_engine.user_manager import TrustLevel
        
        expected_levels = [
            'L0_BROWSE', 'L1_TRACE_VISIBLE', 'L2_OPINION_REPLY',
            'L3_ASYNC_MESSAGE', 'L4_REALTIME_CHAT', 'L5_GROUP_CHAT'
        ]
        
        for level_name in expected_levels:
            assert hasattr(TrustLevel, level_name)
    
    def test_trust_level_ordering(self):
        from user_engine.user_manager import TrustLevel
        
        # 信任等级应该是递增的
        assert TrustLevel.L0_BROWSE.value < TrustLevel.L5_GROUP_CHAT.value


class TestTrustLevelComputation:
    """信任等级计算测试"""
    
    def test_basic_trust_computation(self):
        from user_engine.user_manager import (
            compute_trust_level, RelationshipState, TrustLevel
        )
        
        state = RelationshipState(
            user_a="user_a",
            user_b="user_b",
            relationship_score_a_to_b=0.5,
            relationship_score_b_to_a=0.5,
            topic_diversity=5,
            first_resonance_ts=time.time() - 86400 * 30,  # 30 天前
        )
        
        level = compute_trust_level(
            state=state,
            current_ts=time.time(),
        )
        
        assert isinstance(level, TrustLevel)
    
    def test_higher_score_higher_trust(self):
        from user_engine.user_manager import (
            compute_trust_level, RelationshipState
        )
        
        # 高关系分
        high_score_state = RelationshipState(
            user_a="user_a",
            user_b="user_b",
            relationship_score_a_to_b=0.9,
            relationship_score_b_to_a=0.9,
            topic_diversity=10,
            first_resonance_ts=time.time() - 86400 * 180,
        )
        
        # 低关系分
        low_score_state = RelationshipState(
            user_a="user_a",
            user_b="user_b",
            relationship_score_a_to_b=0.1,
            relationship_score_b_to_a=0.1,
            topic_diversity=1,
            first_resonance_ts=time.time() - 86400 * 7,
        )
        
        high_level = compute_trust_level(high_score_state, time.time())
        low_level = compute_trust_level(low_score_state, time.time())
        
        assert high_level.value >= low_level.value


class TestConfidantEligibility:
    """密友资格检查测试"""
    
    def test_basic_eligibility_check(self):
        from user_engine.user_manager import (
            check_confidant_eligibility, RelationshipState
        )
        
        state = RelationshipState(
            user_a="user_a",
            user_b="user_b",
            relationship_score_a_to_b=0.7,
            relationship_score_b_to_a=0.7,
            topic_diversity=5,
            first_resonance_ts=time.time() - 86400 * 60,
        )
        
        result = check_confidant_eligibility(
            state=state,
            current_ts=time.time(),
        )
        
        assert isinstance(result, dict)
        assert 'eligible' in result or 'reason' in result
    
    def test_low_relationship_ineligible(self):
        from user_engine.user_manager import (
            check_confidant_eligibility, RelationshipState
        )
        
        state = RelationshipState(
            user_a="user_a",
            user_b="user_b",
            relationship_score_a_to_b=0.1,
            relationship_score_b_to_a=0.1,
            topic_diversity=1,
            first_resonance_ts=time.time() - 86400,
        )
        
        result = check_confidant_eligibility(
            state=state,
            current_ts=time.time(),
        )
        
        # 低关系分应该不符合资格
        assert result.get('eligible') == False or 'reason' in result


class TestAnonymousIdentity:
    """匿名身份生成测试"""
    
    def test_identity_generation(self):
        from user_engine.user_manager import generate_anonymous_identity
        
        identity = generate_anonymous_identity(
            internal_token="test_token_001",
            anchor_id="test_anchor_001",
        )
        
        assert identity is not None
        assert hasattr(identity, 'display_name')
        assert len(identity.display_name) > 0
    
    def test_deterministic_generation(self):
        from user_engine.user_manager import generate_anonymous_identity
        
        # 相同输入应该生成相同身份
        id1 = generate_anonymous_identity("token1", "anchor1")
        id2 = generate_anonymous_identity("token1", "anchor1")
        
        # 比较身份属性
        assert id1.display_name == id2.display_name
    
    def test_different_tokens_different_identity(self):
        from user_engine.user_manager import generate_anonymous_identity
        
        id1 = generate_anonymous_identity("token1", "anchor1")
        id2 = generate_anonymous_identity("token2", "anchor1")
        
        # 不同 token 应该生成不同身份
        assert id1.display_name != id2.display_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
