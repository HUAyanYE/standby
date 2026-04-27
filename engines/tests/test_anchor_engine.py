"""
Anchor Engine 单元测试

基于实际 API:
- compute_trigger_score_v2(candidate, current_ts, ...)
- compute_user_affinity(user_id, anchor_topics, user_topic_history)
- semantic_seasonal_relevance(anchor_embedding, season_embeddings, current_season)
"""

import pytest
import sys
import numpy as np
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestReplayTrigger:
    """重现触发类型测试"""
    
    def test_trigger_types_exist(self):
        from anchor_engine.anchor_replay_v2 import ReplayTrigger
        
        expected_types = ['SEASONAL', 'ANNIVERSARY', 'SOCIAL_EVENT', 'CLASSIC_CYCLE', 'GROUP_MEMORY']
        for trigger_name in expected_types:
            assert hasattr(ReplayTrigger, trigger_name)


class TestTriggerScoreV2:
    """触发分数计算测试"""
    
    def test_basic_trigger_score(self):
        from anchor_engine.anchor_replay_v2 import (
            compute_trigger_score_v2, ReplayCandidate, ReplayTrigger
        )
        
        candidate = ReplayCandidate(
            anchor_id="test_anchor",
            anchor_text="测试锚点",
            topics=["测试"],
            trigger_type=ReplayTrigger.SEASONAL,
            trigger_score=0.8,
        )
        
        score = compute_trigger_score_v2(
            candidate=candidate,
            current_ts=time.time(),
        )
        
        assert isinstance(score, (int, float))
    
    def test_different_trigger_types(self):
        from anchor_engine.anchor_replay_v2 import (
            compute_trigger_score_v2, ReplayCandidate, ReplayTrigger
        )
        
        for trigger_type in ReplayTrigger:
            candidate = ReplayCandidate(
                anchor_id="test_anchor",
                anchor_text="测试锚点",
                topics=["测试"],
                trigger_type=trigger_type,
                trigger_score=0.5,
            )
            
            score = compute_trigger_score_v2(
                candidate=candidate,
                current_ts=time.time(),
            )
            
            assert isinstance(score, (int, float))


class TestUserAffinity:
    """用户亲和度测试"""
    
    def test_basic_affinity(self):
        from anchor_engine.anchor_replay_v2 import compute_user_affinity
        
        affinity = compute_user_affinity(
            user_id="test_user",
            anchor_topics=["科技", "AI"],
            user_topic_history={
                "科技": {"count": 10, "last_ts": time.time()},
                "AI": {"count": 5, "last_ts": time.time()},
            },
        )
        
        assert isinstance(affinity, (int, float))
        assert 0 <= affinity <= 1
    
    def test_matching_topics(self):
        from anchor_engine.anchor_replay_v2 import compute_user_affinity
        
        # 用户对科技话题有兴趣
        affinity_with_interest = compute_user_affinity(
            user_id="test_user",
            anchor_topics=["科技", "AI"],
            user_topic_history={
                "科技": {"count": 100, "last_ts": time.time()},
            },
        )
        
        # 用户对美食话题无兴趣
        affinity_without_interest = compute_user_affinity(
            user_id="test_user",
            anchor_topics=["美食"],
            user_topic_history={
                "科技": {"count": 100, "last_ts": time.time()},
            },
        )
        
        # 有兴趣的话题应该有更高的亲和度
        assert affinity_with_interest >= affinity_without_interest


class TestSemanticSeasonalRelevance:
    """语义季节相关性测试"""
    
    def test_basic_relevance(self):
        from anchor_engine.anchor_replay_v2 import semantic_seasonal_relevance
        
        # 创建测试向量
        np.random.seed(42)
        anchor_embedding = np.random.randn(768).astype(np.float32)
        
        season_embeddings = {
            "summer": [np.random.randn(768).astype(np.float32) for _ in range(3)],
            "winter": [np.random.randn(768).astype(np.float32) for _ in range(3)],
        }
        
        relevance = semantic_seasonal_relevance(
            anchor_embedding=anchor_embedding,
            season_embeddings=season_embeddings,
            current_season="summer",
        )
        
        assert isinstance(relevance, (int, float))
        assert 0 <= relevance <= 1


class TestReplayCandidate:
    """重现候选数据结构测试"""
    
    def test_candidate_creation(self):
        from anchor_engine.anchor_replay_v2 import ReplayCandidate, ReplayTrigger
        
        candidate = ReplayCandidate(
            anchor_id="test_anchor",
            anchor_text="测试锚点",
            topics=["测试"],
            trigger_type=ReplayTrigger.SEASONAL,
            trigger_score=0.8,
        )
        
        assert candidate.anchor_id == "test_anchor"
        assert candidate.trigger_type == ReplayTrigger.SEASONAL
        assert candidate.trigger_score == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
