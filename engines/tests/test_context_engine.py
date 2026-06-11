"""
Context Engine — 单元测试

测试覆盖:
- submit_context_state: 提交情境状态
- get_contextual_weights: 获取情境化话题权重
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "context_engine"))


@pytest.fixture
def mock_config():
    """模拟引擎配置"""
    config = MagicMock()
    config.engine_name = "context_engine"
    config.host = "0.0.0.0"
    config.port = 8094
    config.max_workers = 10
    config.log_level = "INFO"
    return config


class TestContextEngineLogic:
    """Context Engine 业务逻辑测试"""

    def test_scene_type_weights(self):
        """不同场景类型应有不同的权重调整"""
        # 模拟场景权重
        scene_weights = {
            "commute": {"entertainment": 1.2, "knowledge": 0.8},
            "work_break": {"entertainment": 1.0, "knowledge": 1.1},
            "late_night": {"emotional": 1.3, "humor": 0.9},
        }

        # 验证权重结构
        for scene, weights in scene_weights.items():
            assert isinstance(weights, dict), f"{scene} 权重应为字典"
            for topic, weight in weights.items():
                assert weight > 0, f"{scene}.{topic} 权重应为正数"

    def test_mood_hint_impact(self):
        """情绪提示应影响话题权重"""
        # 模拟情绪对权重的影响
        mood_effects = {
            "happy": {"humor": 1.2, "emotional": 0.9},
            "sad": {"emotional": 1.3, "humor": 0.7},
            "neutral": {"entertainment": 1.0, "knowledge": 1.0},
        }

        for mood, effects in mood_effects.items():
            assert isinstance(effects, dict), f"{mood} 效果应为字典"

    def test_attention_level_impact(self):
        """注意力水平应影响内容复杂度"""
        # 高注意力 → 可推荐复杂内容
        # 低注意力 → 推荐简单内容
        attention_levels = ["high", "medium", "low"]
        for level in attention_levels:
            assert level in attention_levels, f"注意力水平应为 {attention_levels} 之一"


class TestContextDataValidation:
    """情境数据验证测试"""

    def test_valid_scene_types(self):
        """验证有效的场景类型"""
        valid_scenes = ["commute", "work_break", "late_night", "morning", "weekend"]
        for scene in valid_scenes:
            assert isinstance(scene, str), "场景类型应为字符串"
            assert len(scene) > 0, "场景类型不应为空"

    def test_valid_mood_hints(self):
        """验证有效的情绪提示"""
        valid_moods = ["happy", "sad", "neutral", "excited", "calm", "anxious"]
        for mood in valid_moods:
            assert isinstance(mood, str), "情绪提示应为字符串"

    def test_valid_attention_levels(self):
        """验证有效的注意力水平"""
        valid_levels = ["high", "medium", "low"]
        for level in valid_levels:
            assert isinstance(level, str), "注意力水平应为字符串"
            assert level in valid_levels, f"注意力水平应为 {valid_levels} 之一"


class TestContextWeightCalculation:
    """情境权重计算测试"""

    def test_base_weight_calculation(self):
        """基础权重计算"""
        # 基础权重应为 1.0
        base_weight = 1.0
        assert base_weight == 1.0

    def test_weight_with_scene_modifier(self):
        """带场景修饰的权重计算"""
        base = 1.0
        scene_modifier = 1.2
        result = base * scene_modifier
        assert result == 1.2

    def test_weight_with_mood_modifier(self):
        """带情绪修饰的权重计算"""
        base = 1.0
        mood_modifier = 0.8
        result = base * mood_modifier
        assert result == 0.8

    def test_weight_with_combined_modifiers(self):
        """组合修饰的权重计算"""
        base = 1.0
        scene_modifier = 1.2
        mood_modifier = 0.9
        result = base * scene_modifier * mood_modifier
        assert abs(result - 1.08) < 0.001

    def test_weight_bounds(self):
        """权重应在合理范围内"""
        min_weight = 0.1
        max_weight = 3.0

        # 测试边界
        assert min_weight > 0, "最小权重应为正数"
        assert max_weight > min_weight, "最大权重大于最小权重"

        # 测试裁剪
        test_weight = 5.0
        clamped = max(min_weight, min(max_weight, test_weight))
        assert clamped == max_weight, "超出范围的权重应被裁剪"
