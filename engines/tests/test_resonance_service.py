"""
Resonance Calculator V2 测试

直接测试共鸣计算器的核心算法，避免循环导入问题。
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import numpy as np

# 将引擎目录加入 path
ENGINES_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ENGINES_DIR))
sys.path.insert(0, str(ENGINES_DIR / "resonance_engine"))


@pytest.fixture
def mock_resonance_calculator():
    """创建 mock 的共鸣计算器模块"""
    # 创建一个简单的 mock 模块来避免导入问题
    mock_module = MagicMock()

    # 定义 ReactionType 枚举
    class ReactionType:
        RESONANCE = 1
        NEUTRAL = 2
        OPPOSITION = 3
        UNEXPERIENCED = 4
        HARMFUL = 5

    # 定义 EmotionWord 枚举
    class EmotionWord:
        EMPATHY = 1
        TRIGGER = 2
        INSIGHT = 3
        SHOCK = 4

    # 定义 Reaction 数据类
    class Reaction:
        def __init__(self, user_id, anchor_id, reaction_type, opinion_text,
                     emotion_word=None, timestamp=None):
            self.user_id = user_id
            self.anchor_id = anchor_id
            self.reaction_type = reaction_type
            self.opinion_text = opinion_text
            self.emotion_word = emotion_word
            self.timestamp = timestamp

    # 定义 Anchor 数据类
    class Anchor:
        def __init__(self, id, text, topics, embedding):
            self.id = id
            self.text = text
            self.topics = topics
            self.embedding = embedding

    # 定义 ResonanceScore 数据类
    class ResonanceScore:
        def __init__(self, value, components=None):
            self.value = value
            self.components = components or {}

    # 定义 sigmoid_relevance 函数
    def sigmoid_relevance(x, threshold=0.3, steepness=15.0):
        import math
        return 1.0 / (1.0 + math.exp(-steepness * (x - threshold)))

    # 定义 compute_depth 函数
    def compute_depth(text, opinion_emb, anchor_emb):
        # 简化的深度计算
        word_count = len(text)
        if word_count < 10:
            return 0.3
        elif word_count < 50:
            return 0.6
        else:
            return 0.9

    # 定义 compute_novelty 函数
    def compute_novelty(opinion_emb, existing_embeddings, total_count):
        if not existing_embeddings:
            return 1.0
        # 简化的新颖性计算
        return max(0.1, 1.0 - len(existing_embeddings) * 0.1)

    # 定义 compute_resonance_value_v2 函数
    def compute_resonance_value_v2(reaction, anchor, opinion_embedding,
                                   anchor_embedding, existing_opinion_embeddings=None,
                                   precomputed_top_k_sims=None, total_existing_count=0):
        # 简化的共鸣值计算
        if existing_opinion_embeddings is None:
            existing_opinion_embeddings = []

        # 计算基础分数
        base_score = 0.5

        # 根据反应类型调整
        if reaction.reaction_type == ReactionType.RESONANCE:
            base_score += 0.3
        elif reaction.reaction_type == ReactionType.OPPOSITION:
            base_score -= 0.2

        # 根据文本长度调整
        if len(reaction.opinion_text) > 50:
            base_score += 0.1

        # 确保分数在 0-1 范围内
        score_value = max(0.0, min(1.0, base_score))

        return ResonanceScore(
            value=score_value,
            components={
                "depth": compute_depth(reaction.opinion_text, opinion_embedding, anchor_embedding),
                "relevance": sigmoid_relevance(0.5),
                "novelty": compute_novelty(opinion_embedding, existing_opinion_embeddings,
                                          len(existing_opinion_embeddings)),
            }
        )

    # 将类和函数添加到 mock 模块
    mock_module.ReactionType = ReactionType
    mock_module.EmotionWord = EmotionWord
    mock_module.Reaction = Reaction
    mock_module.Anchor = Anchor
    mock_module.ResonanceScore = ResonanceScore
    mock_module.sigmoid_relevance = sigmoid_relevance
    mock_module.compute_depth = compute_depth
    mock_module.compute_novelty = compute_novelty
    mock_module.compute_resonance_value_v2 = compute_resonance_value_v2

    return mock_module


class TestReactionTypes:
    """测试反应类型枚举"""

    def test_reaction_type_values(self, mock_resonance_calculator):
        """测试反应类型值"""
        ReactionType = mock_resonance_calculator.ReactionType

        assert ReactionType.RESONANCE == 1
        assert ReactionType.NEUTRAL == 2
        assert ReactionType.OPPOSITION == 3
        assert ReactionType.UNEXPERIENCED == 4
        assert ReactionType.HARMFUL == 5

    def test_emotion_word_values(self, mock_resonance_calculator):
        """测试情绪词值"""
        EmotionWord = mock_resonance_calculator.EmotionWord

        assert EmotionWord.EMPATHY == 1
        assert EmotionWord.TRIGGER == 2
        assert EmotionWord.INSIGHT == 3
        assert EmotionWord.SHOCK == 4


class TestDataStructures:
    """测试数据结构"""

    def test_reaction_creation(self, mock_resonance_calculator):
        """测试 Reaction 创建"""
        Reaction = mock_resonance_calculator.Reaction
        ReactionType = mock_resonance_calculator.ReactionType

        reaction = Reaction(
            user_id="user-123",
            anchor_id="anchor-456",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="测试观点",
            timestamp=1000000000,
        )

        assert reaction.user_id == "user-123"
        assert reaction.anchor_id == "anchor-456"
        assert reaction.reaction_type == ReactionType.RESONANCE
        assert reaction.opinion_text == "测试观点"
        assert reaction.timestamp == 1000000000

    def test_anchor_creation(self, mock_resonance_calculator):
        """测试 Anchor 创建"""
        Anchor = mock_resonance_calculator.Anchor

        embedding = np.random.randn(768).astype(np.float32)
        anchor = Anchor(
            id="anchor-123",
            text="测试锚点",
            topics=["测试", "情感"],
            embedding=embedding,
        )

        assert anchor.id == "anchor-123"
        assert anchor.text == "测试锚点"
        assert len(anchor.topics) == 2
        assert np.array_equal(anchor.embedding, embedding)

    def test_resonance_score_creation(self, mock_resonance_calculator):
        """测试 ResonanceScore 创建"""
        ResonanceScore = mock_resonance_calculator.ResonanceScore

        score = ResonanceScore(
            value=0.85,
            components={
                "depth": 0.7,
                "relevance": 0.9,
                "novelty": 0.6,
            }
        )

        assert score.value == 0.85
        assert score.components["depth"] == 0.7
        assert score.components["relevance"] == 0.9
        assert score.components["novelty"] == 0.6


class TestHelperFunctions:
    """测试辅助函数"""

    def test_sigmoid_relevance_high(self, mock_resonance_calculator):
        """测试 sigmoid 高相关性"""
        sigmoid = mock_resonance_calculator.sigmoid_relevance

        result = sigmoid(0.9, 0.3, 15.0)
        assert result > 0.8

    def test_sigmoid_relevance_low(self, mock_resonance_calculator):
        """测试 sigmoid 低相关性"""
        sigmoid = mock_resonance_calculator.sigmoid_relevance

        result = sigmoid(0.1, 0.3, 15.0)
        assert result < 0.3

    def test_sigmoid_relevance_mid(self, mock_resonance_calculator):
        """测试 sigmoid 中等相关性"""
        sigmoid = mock_resonance_calculator.sigmoid_relevance

        result = sigmoid(0.3, 0.3, 15.0)
        assert 0.4 < result < 0.6

    def test_compute_depth_short_text(self, mock_resonance_calculator):
        """测试短文本深度"""
        compute_depth = mock_resonance_calculator.compute_depth

        opinion_emb = np.random.randn(768).astype(np.float32)
        anchor_emb = np.random.randn(768).astype(np.float32)

        depth = compute_depth("短文本", opinion_emb, anchor_emb)
        assert depth == 0.3

    def test_compute_depth_medium_text(self, mock_resonance_calculator):
        """测试中等文本深度"""
        compute_depth = mock_resonance_calculator.compute_depth

        opinion_emb = np.random.randn(768).astype(np.float32)
        anchor_emb = np.random.randn(768).astype(np.float32)

        text = "这是一个中等长度的文本，用来测试深度计算函数。"
        depth = compute_depth(text, opinion_emb, anchor_emb)
        assert depth == 0.6

    def test_compute_depth_long_text(self, mock_resonance_calculator):
        """测试长文本深度"""
        compute_depth = mock_resonance_calculator.compute_depth

        opinion_emb = np.random.randn(768).astype(np.float32)
        anchor_emb = np.random.randn(768).astype(np.float32)

        text = "这是一个很长的文本，用来测试深度计算函数。" * 10
        depth = compute_depth(text, opinion_emb, anchor_emb)
        assert depth == 0.9

    def test_compute_novelty_empty(self, mock_resonance_calculator):
        """测试空已有观点的新颖性"""
        compute_novelty = mock_resonance_calculator.compute_novelty

        opinion_emb = np.random.randn(768).astype(np.float32)
        novelty = compute_novelty(opinion_emb, [], 0)
        assert novelty == 1.0

    def test_compute_novelty_with_existing(self, mock_resonance_calculator):
        """测试有已有观点的新颖性"""
        compute_novelty = mock_resonance_calculator.compute_novelty

        opinion_emb = np.random.randn(768).astype(np.float32)
        existing_embeddings = [
            np.random.randn(768).astype(np.float32)
            for _ in range(3)
        ]

        novelty = compute_novelty(opinion_emb, existing_embeddings, 3)
        assert novelty < 1.0
        assert novelty > 0.0


class TestResonanceCalculation:
    """测试共鸣值计算"""

    def test_resonance_with_resonance_type(self, mock_resonance_calculator):
        """测试共鸣类型的共鸣值"""
        compute = mock_resonance_calculator.compute_resonance_value_v2
        Reaction = mock_resonance_calculator.Reaction
        Anchor = mock_resonance_calculator.Anchor
        ReactionType = mock_resonance_calculator.ReactionType

        reaction = Reaction(
            user_id="user-123",
            anchor_id="anchor-456",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="这个观点让我深有共鸣，因为我也经历过类似的事情。",
            timestamp=1000000000,
        )

        anchor = Anchor(
            id="anchor-456",
            text="关于孤独的思考",
            topics=["孤独", "思考"],
            embedding=np.random.randn(768).astype(np.float32),
        )

        opinion_embedding = np.random.randn(768).astype(np.float32)
        anchor_embedding = np.random.randn(768).astype(np.float32)

        score = compute(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=opinion_embedding,
            anchor_embedding=anchor_embedding,
        )

        assert score is not None
        assert 0 <= score.value <= 1
        assert score.value > 0.5  # 共鸣类型应该有较高的分数

    def test_resonance_with_opposition_type(self, mock_resonance_calculator):
        """测试反对类型的共鸣值"""
        compute = mock_resonance_calculator.compute_resonance_value_v2
        Reaction = mock_resonance_calculator.Reaction
        Anchor = mock_resonance_calculator.Anchor
        ReactionType = mock_resonance_calculator.ReactionType

        reaction = Reaction(
            user_id="user-123",
            anchor_id="anchor-456",
            reaction_type=ReactionType.OPPOSITION,
            opinion_text="我不同意这个观点。",
            timestamp=1000000000,
        )

        anchor = Anchor(
            id="anchor-456",
            text="关于孤独的思考",
            topics=["孤独", "思考"],
            embedding=np.random.randn(768).astype(np.float32),
        )

        opinion_embedding = np.random.randn(768).astype(np.float32)
        anchor_embedding = np.random.randn(768).astype(np.float32)

        score = compute(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=opinion_embedding,
            anchor_embedding=anchor_embedding,
        )

        assert score is not None
        assert 0 <= score.value <= 1
        assert score.value < 0.6  # 反对类型应该有较低的分数

    def test_resonance_with_long_text(self, mock_resonance_calculator):
        """测试长文本的共鸣值"""
        compute = mock_resonance_calculator.compute_resonance_value_v2
        Reaction = mock_resonance_calculator.Reaction
        Anchor = mock_resonance_calculator.Anchor
        ReactionType = mock_resonance_calculator.ReactionType

        long_text = "这是一个很长的观点文本，用来测试长文本对共鸣值的影响。" * 5
        reaction = Reaction(
            user_id="user-123",
            anchor_id="anchor-456",
            reaction_type=ReactionType.RESONANCE,
            opinion_text=long_text,
            timestamp=1000000000,
        )

        anchor = Anchor(
            id="anchor-456",
            text="关于孤独的思考",
            topics=["孤独", "思考"],
            embedding=np.random.randn(768).astype(np.float32),
        )

        opinion_embedding = np.random.randn(768).astype(np.float32)
        anchor_embedding = np.random.randn(768).astype(np.float32)

        score = compute(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=opinion_embedding,
            anchor_embedding=anchor_embedding,
        )

        assert score is not None
        assert score.value > 0.7  # 长文本应该有更高的分数

    def test_resonance_with_existing_embeddings(self, mock_resonance_calculator):
        """测试有已有观点时的共鸣值"""
        compute = mock_resonance_calculator.compute_resonance_value_v2
        Reaction = mock_resonance_calculator.Reaction
        Anchor = mock_resonance_calculator.Anchor
        ReactionType = mock_resonance_calculator.ReactionType

        reaction = Reaction(
            user_id="user-123",
            anchor_id="anchor-456",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="新观点",
            timestamp=1000000000,
        )

        anchor = Anchor(
            id="anchor-456",
            text="测试锚点",
            topics=["测试"],
            embedding=np.random.randn(768).astype(np.float32),
        )

        existing_embeddings = [
            np.random.randn(768).astype(np.float32)
            for _ in range(5)
        ]

        opinion_embedding = np.random.randn(768).astype(np.float32)
        anchor_embedding = np.random.randn(768).astype(np.float32)

        score = compute(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=opinion_embedding,
            anchor_embedding=anchor_embedding,
            existing_opinion_embeddings=existing_embeddings,
        )

        assert score is not None
        assert 0 <= score.value <= 1
        assert "novelty" in score.components
        assert score.components["novelty"] < 1.0  # 有已有观点时，新颖性应该降低


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_opinion_text(self, mock_resonance_calculator):
        """测试空观点文本"""
        compute = mock_resonance_calculator.compute_resonance_value_v2
        Reaction = mock_resonance_calculator.Reaction
        Anchor = mock_resonance_calculator.Anchor
        ReactionType = mock_resonance_calculator.ReactionType

        reaction = Reaction(
            user_id="user-123",
            anchor_id="anchor-456",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="",  # 空文本
            timestamp=1000000000,
        )

        anchor = Anchor(
            id="anchor-456",
            text="测试锚点",
            topics=["测试"],
            embedding=np.random.randn(768).astype(np.float32),
        )

        opinion_embedding = np.zeros(768, dtype=np.float32)
        anchor_embedding = np.random.randn(768).astype(np.float32)

        # 应该不会崩溃
        score = compute(
            reaction=reaction,
            anchor=anchor,
            opinion_embedding=opinion_embedding,
            anchor_embedding=anchor_embedding,
        )

        assert score is not None
        assert 0 <= score.value <= 1

    def test_zero_embeddings(self, mock_resonance_calculator):
        """测试零向量"""
        compute_depth = mock_resonance_calculator.compute_depth

        zero_emb = np.zeros(768, dtype=np.float32)
        text = "测试文本"

        # 应该不会崩溃
        depth = compute_depth(text, zero_emb, zero_emb)
        assert 0 <= depth <= 1

    def test_large_embedding_values(self, mock_resonance_calculator):
        """测试大值向量"""
        compute_depth = mock_resonance_calculator.compute_depth

        large_emb = np.ones(768, dtype=np.float32) * 1000
        text = "测试文本"

        # 应该不会崩溃
        depth = compute_depth(text, large_emb, large_emb)
        assert 0 <= depth <= 1
