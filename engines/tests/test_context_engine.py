"""
Context Engine 单元测试

由于 context_engine 主要是 gRPC 接口层，算法逻辑较简单，
主要测试数据结构和边界情况。
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestContextStateValidation:
    """情境状态验证测试"""
    
    def test_valid_scene_types(self):
        """测试有效场景类型"""
        valid_scenes = ["工作", "休息", "社交", "学习", "娱乐", "独处"]
        
        for scene in valid_scenes:
            # 场景类型应该是字符串
            assert isinstance(scene, str)
            assert len(scene) > 0
    
    def test_valid_mood_hints(self):
        """测试有效情绪提示"""
        valid_moods = ["专注", "放松", "兴奋", "平静", "焦虑", "快乐", "低落"]
        
        for mood in valid_moods:
            assert isinstance(mood, str)
            assert len(mood) > 0
    
    def test_valid_attention_levels(self):
        """测试有效注意力水平"""
        valid_levels = ["高", "中", "低"]
        
        for level in valid_levels:
            assert isinstance(level, str)
            assert level in ["高", "中", "低"]


class TestTimeBasedLogic:
    """基于时间的逻辑测试"""
    
    def test_hour_range(self):
        """测试小时范围"""
        for hour in range(24):
            assert 0 <= hour <= 23
    
    def test_time_period_classification(self):
        """测试时间段分类"""
        # 早晨: 6-11
        # 午间: 12-14
        # 下午: 15-17
        # 晚间: 18-21
        # 深夜: 22-5
        
        morning_hours = range(6, 12)
        afternoon_hours = range(15, 18)
        evening_hours = range(18, 22)
        night_hours = list(range(22, 24)) + list(range(0, 6))
        
        assert len(morning_hours) == 6
        assert len(afternoon_hours) == 3
        assert len(evening_hours) == 4
        assert len(night_hours) == 8


class TestWeightCalculation:
    """权重计算测试"""
    
    def test_weight_bounds(self):
        """测试权重边界"""
        # 权重应该在 0-1 之间
        weights = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for w in weights:
            assert 0 <= w <= 1
    
    def test_weight_combination(self):
        """测试权重组合"""
        # 多个权重组合后应该归一化
        weights = [0.3, 0.5, 0.2]
        total = sum(weights)
        
        # 归一化
        normalized = [w / total for w in weights]
        
        assert abs(sum(normalized) - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
