"""
共鸣值计算 v2 — 单元测试

测试覆盖:
- sigmoid_relevance: 平滑阈值
- compute_novelty_v2: k-NN 聚类感知
- compute_depth_v2: 复合深度信号
- harmful_penalty_v2 / unexperienced_penalty_v2: 指数型惩罚
- get_resonance_weight_v2: 反应类型权重
- compute_resonance_value_v2: 完整公式
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "resonance_engine"))

from resonance_calculator_v2 import (
    ReactionType, EmotionWord, Reaction, Anchor, ResonanceScore,
    sigmoid_relevance, compute_novelty_v2, compute_depth_v2,
    compute_emotion_intensity, compute_experience_detail,
    harmful_penalty_v2, unexperienced_penalty_v2,
    get_resonance_weight_v2, compute_resonance_value_v2,
)


# ============================================================
# sigmoid_relevance
# ============================================================

class TestSigmoidRelevance:
    """Sigmoid 相关性过滤测试"""

    def test_threshold_is_half_power(self):
        """relevance == threshold 时，输出应为 0.5"""
        result = sigmoid_relevance(0.3, threshold=0.3, sharpness=15.0)
        assert abs(result - 0.5) < 1e-6

    def test_high_relevance_near_one(self):
        """relevance >> threshold 时，输出应接近 1.0"""
        result = sigmoid_relevance(0.8, threshold=0.3, sharpness=15.0)
        assert result > 0.99

    def test_low_relevance_near_zero(self):
        """relevance << threshold 时，输出应接近 0.0"""
        result = sigmoid_relevance(0.0, threshold=0.3, sharpness=15.0)
        assert result < 0.02

    def test_smooth_transition(self):
        """阈值附近应平滑过渡，不是硬截断"""
        below = sigmoid_relevance(0.25, threshold=0.3, sharpness=15.0)
        at = sigmoid_relevance(0.30, threshold=0.3, sharpness=15.0)
        above = sigmoid_relevance(0.35, threshold=0.3, sharpness=15.0)
        assert below < at < above
        # v1 硬阈值会在 0.3 处跳跃，v2 应该平滑
        assert at - below < 0.3  # 过渡应该平缓

    def test_sharpness_controls_steepness(self):
        """sharpness 越大，过渡越陡峭"""
        low_sharp = sigmoid_relevance(0.32, threshold=0.3, sharpness=5.0)
        high_sharp = sigmoid_relevance(0.32, threshold=0.3, sharpness=30.0)
        assert high_sharp > low_sharp

    def test_monotonic(self):
        """输出应单调递增"""
        values = [sigmoid_relevance(r / 100, threshold=0.3, sharpness=15.0) for r in range(101)]
        for i in range(len(values) - 1):
            assert values[i] <= values[i + 1]


# ============================================================
# compute_novelty_v2
# ============================================================

class TestNovelty:
    """聚类感知 Novelty 测试"""

    def test_below_relevance_floor_returns_zero(self):
        """relevance < floor 时，novelty 为 0"""
        emb = np.random.randn(768).astype(np.float32)
        result = compute_novelty_v2(emb, [], 0.1, relevance_floor=0.3)
        assert result == 0.0

    def test_few_existing_returns_one(self):
        """已有观点 < 5 时，不惩罚先驱者"""
        emb = np.random.randn(768).astype(np.float32)
        existing = [np.random.randn(768).astype(np.float32) for _ in range(3)]
        result = compute_novelty_v2(emb, existing, 0.5)
        assert result == 1.0

    def test_similar_opinions_low_novelty(self):
        """与已有观点高度相似 → novelty 低"""
        base = np.random.randn(768).astype(np.float32)
        base = base / np.linalg.norm(base)
        # 10 个相似观点
        existing = [(base + np.random.randn(768).astype(np.float32) * 0.05) for _ in range(10)]
        existing = [e / np.linalg.norm(e) for e in existing]
        result = compute_novelty_v2(base, existing, 0.8)
        assert result < 0.5  # 高度相似 → novelty 低

    def test_dissimilar_opinions_high_novelty(self):
        """与已有观点不相似 → novelty 高"""
        opinion = np.random.randn(768).astype(np.float32)
        opinion = opinion / np.linalg.norm(opinion)
        # 10 个不相关观点
        existing = [np.random.randn(768).astype(np.float32) for _ in range(10)]
        existing = [e / np.linalg.norm(e) for e in existing]
        result = compute_novelty_v2(opinion, existing, 0.5)
        assert result > 0.5  # 不相似 → novelty 高

    def test_precomputed_top_k_sims(self):
        """预计算的 top-k 相似度路径应正常工作"""
        emb = np.random.randn(768).astype(np.float32)
        # 5 个高相似度
        top_k_sims = [0.9, 0.85, 0.8, 0.75, 0.7]
        result = compute_novelty_v2(
            emb, [], 0.5,
            precomputed_top_k_sims=top_k_sims,
            total_existing_count=100,
        )
        assert 0.0 < result < 0.5  # 高相似度 → novelty 低

    def test_density_decay(self):
        """观点越多，novelty 上限越低"""
        emb = np.random.randn(768).astype(np.float32)
        emb = emb / np.linalg.norm(emb)
        # 10 个不相关观点
        existing_10 = [np.random.randn(768).astype(np.float32) for _ in range(10)]
        # 100 个不相关观点
        existing_100 = [np.random.randn(768).astype(np.float32) for _ in range(100)]
        novelty_10 = compute_novelty_v2(emb, existing_10, 0.5)
        novelty_100 = compute_novelty_v2(emb, existing_100, 0.5)
        # 密度衰减：100 条时 novelty 上限更低
        assert novelty_100 <= novelty_10


# ============================================================
# compute_emotion_intensity
# ============================================================

class TestEmotionIntensity:
    """情感强度检测测试"""

    def test_empty_text_returns_zero(self, sample_texts):
        assert compute_emotion_intensity("") == 0.0
        assert compute_emotion_intensity(None) == 0.0

    def test_high_emotion_detected(self, sample_texts):
        """高情感文本应有高分数"""
        score = compute_emotion_intensity(sample_texts["emotional"])
        assert score > 0.3

    def test_low_emotion_detected(self, sample_texts):
        """低情感文本应有低分数"""
        score = compute_emotion_intensity(sample_texts["short"])
        assert score < 0.3

    def test_range_zero_to_one(self, sample_texts):
        """所有输出应在 [0, 1] 范围内"""
        for text in sample_texts.values():
            score = compute_emotion_intensity(text)
            assert 0.0 <= score <= 1.0


# ============================================================
# compute_experience_detail
# ============================================================

class TestExperienceDetail:
    """经历细节检测测试"""

    def test_empty_text_returns_zero(self):
        assert compute_experience_detail("") == 0.0
        assert compute_experience_detail(None) == 0.0

    def test_personal_narrative_high_score(self, sample_texts):
        """个人叙述应有高分数"""
        score = compute_experience_detail(sample_texts["long"])
        assert score > 0.3

    def test_abstract_text_low_score(self, sample_texts):
        """抽象文本应有低分数"""
        score = compute_experience_detail(sample_texts["abstract"])
        assert score < 0.3


# ============================================================
# 惩罚函数
# ============================================================

class TestPenaltyFunctions:
    """惩罚函数测试"""

    def test_zero_harmful_ratio_no_penalty(self):
        """无有害标记 → 无惩罚"""
        assert harmful_penalty_v2(0.0) == 1.0

    def test_high_harmful_ratio_strong_penalty(self):
        """高有害比例 → 强惩罚"""
        assert harmful_penalty_v2(0.5) < 0.5

    def test_zero_unexperienced_ratio_no_penalty(self):
        """无未体验标记 → 无惩罚"""
        assert unexperienced_penalty_v2(0.0) == 1.0

    def test_high_unexperienced_ratio_penalty(self):
        """高未体验比例 → 惩罚"""
        assert unexperienced_penalty_v2(0.5) < 1.0

    def test_penalty_monotonic_decreasing(self):
        """惩罚应单调递减"""
        ratios = [0.0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0]
        penalties = [harmful_penalty_v2(r) for r in ratios]
        for i in range(len(penalties) - 1):
            assert penalties[i] >= penalties[i + 1]


# ============================================================
# get_resonance_weight_v2
# ============================================================

class TestResonanceWeight:
    """反应类型权重测试"""

    def test_resonance_weight_is_one(self):
        """共鸣 → 1.0"""
        w = get_resonance_weight_v2(ReactionType.RESONANCE, None)
        assert w == 1.0

    def test_neutral_weight_is_zero(self):
        """无感 → 0.0"""
        w = get_resonance_weight_v2(ReactionType.NEUTRAL, None)
        assert w == 0.0

    def test_opposition_weight_negative(self):
        """反对 → 负值"""
        w = get_resonance_weight_v2(ReactionType.OPPOSITION, None)
        assert w == -0.2

    def test_unexperienced_returns_none(self):
        """未体验 → None (不计入)"""
        w = get_resonance_weight_v2(ReactionType.UNEXPERIENCED, None)
        assert w is None

    def test_harmful_returns_none(self):
        """有害 → None (不计入)"""
        w = get_resonance_weight_v2(ReactionType.HARMFUL, None)
        assert w is None

    def test_emotion_word_bonus(self):
        """情绪词加权测试"""
        base = get_resonance_weight_v2(ReactionType.RESONANCE, None)
        empathy = get_resonance_weight_v2(ReactionType.RESONANCE, EmotionWord.EMPATHY)
        trigger = get_resonance_weight_v2(ReactionType.RESONANCE, EmotionWord.TRIGGER)
        insight = get_resonance_weight_v2(ReactionType.RESONANCE, EmotionWord.INSIGHT)
        shock = get_resonance_weight_v2(ReactionType.RESONANCE, EmotionWord.SHOCK)

        assert empathy == base * 1.0
        assert trigger == base * 1.1
        assert insight == base * 1.1
        assert shock == base * 1.2


# ============================================================
# compute_resonance_value_v2 (完整公式)
# ============================================================

class TestResonanceValueV2:
    """完整共鸣值计算测试"""

    def test_unexperienced_returns_none(self):
        """未体验 → None"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.UNEXPERIENCED,
        )
        anchor = Anchor(id="a1", text="test")
        result = compute_resonance_value_v2(
            reaction, anchor,
            np.zeros(768), np.zeros(768), [],
        )
        assert result is None

    def test_harmful_returns_none(self):
        """有害 → None"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.HARMFUL,
        )
        anchor = Anchor(id="a1", text="test")
        result = compute_resonance_value_v2(
            reaction, anchor,
            np.zeros(768), np.zeros(768), [],
        )
        assert result is None

    def test_neutral_resonance_is_zero(self):
        """无感 → 共鸣值为 0"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.NEUTRAL,
        )
        anchor = Anchor(id="a1", text="test")
        result = compute_resonance_value_v2(
            reaction, anchor,
            np.zeros(768), np.zeros(768), [],
        )
        assert result is not None
        assert result.value == 0.0

    def test_no_text_uses_defaults(self):
        """纯点击（无文字）→ 使用默认值"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.RESONANCE,
            opinion_text=None,
        )
        anchor = Anchor(id="a1", text="test")
        result = compute_resonance_value_v2(
            reaction, anchor,
            np.zeros(768), np.zeros(768), [],
        )
        assert result is not None
        assert result.value > 0
        # 无文字时 relevance=1.0, novelty=1.0, depth=0.6
        assert result.components["relevance_sigmoid"] == 1.0
        assert result.components["novelty"] == 1.0

    def test_score_range(self, random_embedding):
        """共鸣值应在合理范围内"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="这是一段测试文本",
        )
        anchor = Anchor(id="a1", text="锚点文本")
        result = compute_resonance_value_v2(
            reaction, anchor,
            random_embedding, random_embedding, [],
        )
        assert result is not None
        # 共鸣值应在合理范围内 (考虑所有系数)
        assert -1.0 <= result.value <= 2.0

    def test_resonance_positive_for_resonance_type(self, random_embedding):
        """共鸣类型的值应为正"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="我也有同样的感受",
        )
        anchor = Anchor(id="a1", text="锚点文本")
        result = compute_resonance_value_v2(
            reaction, anchor,
            random_embedding, random_embedding, [],
        )
        assert result is not None
        assert result.value > 0

    def test_components_complete(self, random_embedding):
        """返回值应包含所有分量"""
        reaction = Reaction(
            user_id="u1", anchor_id="a1",
            reaction_type=ReactionType.RESONANCE,
            opinion_text="测试文本",
        )
        anchor = Anchor(id="a1", text="锚点文本")
        result = compute_resonance_value_v2(
            reaction, anchor,
            random_embedding, random_embedding, [],
        )
        assert result is not None
        expected_keys = [
            "resonance_weight", "depth", "relevance_raw",
            "relevance_sigmoid", "novelty",
            "harmful_penalty", "unexperienced_penalty",
        ]
        for key in expected_keys:
            assert key in result.components, f"缺少分量: {key}"
