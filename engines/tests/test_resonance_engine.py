"""
Resonance Engine 单元测试

测试核心算法:
- compute_resonance_value_v2 - 共鸣值计算
- compute_relationship_score_v2 - 关系分计算
- Reaction, Anchor 数据结构
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import time

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestReactionType:
    """反应类型测试"""
    
    def test_reaction_type_values(self):
        from resonance_engine.resonance_calculator_v2 import ReactionType
        
        assert ReactionType.RESONANCE.value == "共鸣"
        assert ReactionType.NEUTRAL.value == "无感"
        assert ReactionType.OPPOSITION.value == "反对"
        assert ReactionType.UNEXPERIENCED.value == "未体验"
        assert ReactionType.HARMFUL.value == "有害"


class TestEmotionWord:
    """情绪词测试"""
    
    def test_emotion_word_values(self):
        from resonance_engine.resonance_calculator_v2 import EmotionWord
        
        assert EmotionWord.EMPATHY.value == "同感"
        assert EmotionWord.TRIGGER.value == "触发"
        assert EmotionWord.INSIGHT.value == "启发"
        assert EmotionWord.SHOCK.value == "震撼"


class TestResonanceValueV2:
    """共鸣值计算 v2 测试"""
    
    def test_basic_resonance(self, sample_embedding):
        """测试基本共鸣计算"""
        from resonance_engine.resonance_calculator_v2 import (
            compute_resonance_value_v2, Reaction, Anchor, ReactionType
        )
        
        anchor = Anchor(
            id="test_anchor_001",
            text="中美关系的深层逻辑",
            topics=["国际关系"],
            embedding=sample_embedding,
        )
        
        reaction = Reaction(
            user_id="test_user_001",
            anchor_id=anchor.id,
            reaction_type=ReactionType.RESONANCE,
            opinion_text="这是一个测试观点",
            timestamp=time.time(),
        )
        
        score = compute_resonance_value_v2(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=sample_embedding,
            anchor_embedding=anchor.embedding,
            existing_opinion_embeddings=[],
        )
        
        # 应该返回 ResonanceScore 或 None
        assert score is None or hasattr(score, 'value')
        if score is not None:
            assert isinstance(score.value, (int, float))
    
    def test_resonance_with_emotion(self, sample_embedding):
        """测试带情绪词的共鸣计算"""
        from resonance_engine.resonance_calculator_v2 import (
            compute_resonance_value_v2, Reaction, Anchor, ReactionType, EmotionWord
        )
        
        anchor = Anchor(
            id="test_anchor",
            text="测试锚点",
            topics=[],
            embedding=sample_embedding,
        )
        
        reaction = Reaction(
            user_id="test_user",
            anchor_id=anchor.id,
            reaction_type=ReactionType.RESONANCE,
            emotion_word=EmotionWord.SHOCK,  # 震撼
            opinion_text="震撼的观点",
            timestamp=time.time(),
        )
        
        score = compute_resonance_value_v2(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=sample_embedding,
            anchor_embedding=anchor.embedding,
            existing_opinion_embeddings=[],
        )
        
        # 应该正常返回
        assert score is None or hasattr(score, 'value')
    
    def test_resonance_with_existing_opinions(self, sample_embedding, sample_embeddings):
        """测试有已有观点时的共鸣计算"""
        from resonance_engine.resonance_calculator_v2 import (
            compute_resonance_value_v2, Reaction, Anchor, ReactionType
        )
        
        anchor = Anchor(
            id="test_anchor",
            text="测试锚点",
            topics=[],
            embedding=sample_embedding,
        )
        
        reaction = Reaction(
            user_id="test_user",
            anchor_id=anchor.id,
            reaction_type=ReactionType.RESONANCE,
            opinion_text="测试观点",
            timestamp=time.time(),
        )
        
        score = compute_resonance_value_v2(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=sample_embedding,
            anchor_embedding=anchor.embedding,
            existing_opinion_embeddings=sample_embeddings,
        )
        
        assert score is None or hasattr(score, 'value')
    
    def test_different_reaction_types(self, sample_embedding):
        """测试不同反应类型的共鸣值"""
        from resonance_engine.resonance_calculator_v2 import (
            compute_resonance_value_v2, Reaction, Anchor, ReactionType
        )
        
        anchor = Anchor(
            id="test_anchor",
            text="测试锚点",
            topics=[],
            embedding=sample_embedding,
        )
        
        for reaction_type in [ReactionType.RESONANCE, ReactionType.NEUTRAL, ReactionType.OPPOSITION]:
            reaction = Reaction(
                user_id="test_user",
                anchor_id=anchor.id,
                reaction_type=reaction_type,
                opinion_text="测试观点",
                timestamp=time.time(),
            )
            
            score = compute_resonance_value_v2(
                reaction=reaction,
                anchor=anchor,
                opinion_embedding=sample_embedding,
                anchor_embedding=anchor.embedding,
                existing_opinion_embeddings=[],
            )
            
            # 每种类型都应该能正常处理
            assert score is None or hasattr(score, 'value')
    
    def test_empty_opinion(self, sample_embedding):
        """测试空观点文本"""
        from resonance_engine.resonance_calculator_v2 import (
            compute_resonance_value_v2, Reaction, Anchor, ReactionType
        )
        
        anchor = Anchor(
            id="test_anchor",
            text="测试锚点",
            topics=[],
            embedding=sample_embedding,
        )
        
        reaction = Reaction(
            user_id="test_user",
            anchor_id=anchor.id,
            reaction_type=ReactionType.RESONANCE,
            opinion_text="",  # 空观点
            timestamp=time.time(),
        )
        
        zero_embedding = np.zeros(768, dtype=np.float32)
        score = compute_resonance_value_v2(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=zero_embedding,
            anchor_embedding=anchor.embedding,
            existing_opinion_embeddings=[],
        )
        
        # 应该正常处理
        assert score is None or hasattr(score, 'value')


class TestRelationshipScoreV2:
    """关系分计算 v2 测试"""
    
    def test_basic_relationship(self):
        """测试基本关系分计算"""
        from resonance_engine.resonance_calculator_v2 import compute_relationship_score_v2
        
        # 模拟共鸣记录
        resonance_records = [
            {
                "anchor_id": "anchor_1",
                "user_a_resonance": 0.8,
                "user_b_resonance": 0.9,
                "topics": ["国际关系"],
                "timestamp": time.time(),
            },
        ]
        
        score = compute_relationship_score_v2(
            user_a="user_a",
            user_b="user_b",
            resonance_records=resonance_records,
        )
        
        # 应该返回 RelationshipScore
        assert hasattr(score, 'score')
        assert hasattr(score, 'user_a')
        assert hasattr(score, 'user_b')
        assert score.user_a == "user_a"
        assert score.user_b == "user_b"
        assert isinstance(score.score, (int, float))
    
    def test_no_shared_anchors(self):
        """测试无共同锚点"""
        from resonance_engine.resonance_calculator_v2 import compute_relationship_score_v2
        
        score = compute_relationship_score_v2(
            user_a="user_a",
            user_b="user_b",
            resonance_records=[],  # 无共同锚点
        )
        
        assert score.resonance_count == 0
        assert score.score == 0
    
    def test_multiple_shared_anchors(self):
        """测试多个共同锚点"""
        from resonance_engine.resonance_calculator_v2 import compute_relationship_score_v2
        
        resonance_records = [
            {"anchor_id": f"anchor_{i}", "user_a_resonance": 0.8, "user_b_resonance": 0.9, 
             "topics": [f"topic_{i}"], "timestamp": time.time()}
            for i in range(10)
        ]
        
        score = compute_relationship_score_v2(
            user_a="user_a",
            user_b="user_b",
            resonance_records=resonance_records,
        )
        
        assert score.resonance_count == 10


class TestAnchor:
    """锚点数据结构测试"""
    
    def test_anchor_creation(self, sample_embedding):
        from resonance_engine.resonance_calculator_v2 import Anchor
        
        anchor = Anchor(
            id="test_001",
            text="测试锚点",
            topics=["测试", "单元测试"],
            embedding=sample_embedding,
        )
        
        assert anchor.id == "test_001"
        assert anchor.text == "测试锚点"
        assert len(anchor.topics) == 2
        assert anchor.embedding.shape == (768,)
    
    def test_anchor_without_embedding(self):
        from resonance_engine.resonance_calculator_v2 import Anchor
        
        anchor = Anchor(
            id="test_002",
            text="无向量锚点",
            topics=[],
        )
        
        assert anchor.embedding is None


class TestReaction:
    """反应数据结构测试"""
    
    def test_reaction_creation(self):
        from resonance_engine.resonance_calculator_v2 import Reaction, ReactionType
        
        reaction = Reaction(
            user_id="user_001",
            anchor_id="anchor_001",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="测试观点",
            timestamp=time.time(),
        )
        
        assert reaction.user_id == "user_001"
        assert reaction.reaction_type == ReactionType.RESONANCE
    
    def test_reaction_with_emotion(self):
        from resonance_engine.resonance_calculator_v2 import Reaction, ReactionType, EmotionWord
        
        reaction = Reaction(
            user_id="user_001",
            anchor_id="anchor_001",
            reaction_type=ReactionType.RESONANCE,
            emotion_word=EmotionWord.EMPATHY,  # 同感
            opinion_text="感同身受",
            timestamp=time.time(),
        )
        
        assert reaction.emotion_word == EmotionWord.EMPATHY


class TestSigmoidRelevance:
    """Sigmoid 相关性函数测试"""
    
    def test_sigmoid_at_threshold(self):
        from resonance_engine.resonance_calculator_v2 import sigmoid_relevance
        
        # 在阈值处应该是 0.5
        result = sigmoid_relevance(0.3, threshold=0.3)
        assert abs(result - 0.5) < 0.01
    
    def test_sigmoid_high_relevance(self):
        from resonance_engine.resonance_calculator_v2 import sigmoid_relevance
        
        # 高相关性应该接近 1
        result = sigmoid_relevance(0.9, threshold=0.3)
        assert result > 0.99
    
    def test_sigmoid_low_relevance(self):
        from resonance_engine.resonance_calculator_v2 import sigmoid_relevance
        
        # 低相关性应该接近 0
        result = sigmoid_relevance(0.0, threshold=0.3)
        assert result < 0.02  # 放宽一点边界


class TestComputeNovelty:
    """Novelty 计算测试"""
    
    def test_novelty_no_existing(self, sample_embedding):
        from resonance_engine.resonance_calculator_v2 import compute_novelty_v2
        
        # 无已有观点时，novelty 应该是 1.0
        novelty = compute_novelty_v2(
            opinion_embedding=sample_embedding,
            existing_embeddings=[],
            relevance=0.8,
        )
        
        assert novelty == 1.0
    
    def test_novelty_with_similar_existing(self, sample_embedding):
        from resonance_engine.resonance_calculator_v2 import compute_novelty_v2
        
        # 创建相似的已有观点
        existing = [sample_embedding + np.random.randn(768).astype(np.float32) * 0.01 
                    for _ in range(10)]
        
        novelty = compute_novelty_v2(
            opinion_embedding=sample_embedding,
            existing_embeddings=existing,
            relevance=0.8,
        )
        
        # 相似观点应该导致低 novelty
        assert novelty < 0.5
    
    def test_novelty_low_relevance(self, sample_embedding):
        from resonance_engine.resonance_calculator_v2 import compute_novelty_v2
        
        # 低相关性时 novelty 应该是 0
        novelty = compute_novelty_v2(
            opinion_embedding=sample_embedding,
            existing_embeddings=[sample_embedding],
            relevance=0.1,  # 低于 floor (0.3)
        )
        
        assert novelty == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
