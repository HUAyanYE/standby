"""
锚点重现 v2 — 单元测试

测试覆盖:
- get_current_season: 季节判断
- compute_trigger_score_v2: 触发评分
- compute_time_trend: 时间趋势
"""

import sys
from pathlib import Path
import time

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "anchor_engine"))

from anchor_replay_v2 import (
    ReplayTrigger, ReplayCandidate, GroupMemoryData,
    get_current_season, compute_trigger_score_v2,
    compute_time_trend,
)


# ============================================================
# 季节判断
# ============================================================

class TestSeason:
    """季节判断测试"""

    def test_spring(self):
        assert get_current_season(3) == "spring"
        assert get_current_season(4) == "spring"
        assert get_current_season(5) == "spring"

    def test_summer(self):
        assert get_current_season(6) == "summer"
        assert get_current_season(7) == "summer"
        assert get_current_season(8) == "summer"

    def test_autumn(self):
        assert get_current_season(9) == "autumn"
        assert get_current_season(10) == "autumn"
        assert get_current_season(11) == "autumn"

    def test_winter(self):
        assert get_current_season(12) == "winter"
        assert get_current_season(1) == "winter"
        assert get_current_season(2) == "winter"


# ============================================================
# 时间趋势
# ============================================================

class TestTimeTrend:
    """时间趋势测试"""

    def test_growing_trend(self):
        """增长趋势"""
        data = {
            "2025-Q1": {"resonance": 30, "opposition": 5},
            "2025-Q2": {"resonance": 45, "opposition": 8},
            "2025-Q3": {"resonance": 60, "opposition": 3},
        }
        result = compute_time_trend(data)
        assert result["trend"] == "growing"
        assert result["growth_rate"] > 0

    def test_declining_trend(self):
        """下降趋势"""
        data = {
            "2025-Q1": {"resonance": 60, "opposition": 3},
            "2025-Q2": {"resonance": 45, "opposition": 8},
            "2025-Q3": {"resonance": 30, "opposition": 5},
        }
        result = compute_time_trend(data)
        assert result["trend"] == "declining"

    def test_insufficient_data(self):
        """数据不足"""
        data = {
            "2025-Q1": {"resonance": 30, "opposition": 5},
        }
        result = compute_time_trend(data)
        assert result["trend"] == "insufficient_data"


# ============================================================
# 触发评分
# ============================================================

class TestTriggerScore:
    """触发评分测试"""

    def _make_candidate(self, created_days_ago, topics=None):
        """创建测试候选锚点"""
        now = time.time()
        return ReplayCandidate(
            anchor_id=f"a_{created_days_ago}d",
            anchor_text=f"测试锚点 {created_days_ago} 天前",
            topics=topics or [],
            trigger_type=ReplayTrigger.CLASSIC_CYCLE,
            trigger_score=0.0,
            last_shown_ts=now - created_days_ago * 86400,
            show_count=0,
        )

    def test_score_range(self):
        """触发评分应在合理范围内"""
        candidate = self._make_candidate(30, ["孤独"])
        score = compute_trigger_score_v2(candidate, current_ts=time.time())
        assert 0.0 <= score <= 2.0

    def test_seasonal_bonus(self):
        """季节匹配应有加分"""
        import datetime
        month = datetime.datetime.now().month
        current_season = get_current_season(month)

        # 创建包含当前季节关键词的话题
        season_topics = {
            "spring": ["春天", "花开"],
            "summer": ["夏天", "海边"],
            "autumn": ["秋天", "落叶"],
            "winter": ["冬天", "雪"],
        }

        candidate = self._make_candidate(30, season_topics.get(current_season, []))
        score_seasonal = compute_trigger_score_v2(candidate, current_ts=time.time())

        candidate_no_season = self._make_candidate(30, ["无关话题"])
        score_no_season = compute_trigger_score_v2(candidate_no_season, current_ts=time.time())

        # 季节匹配应该有更高分
        assert score_seasonal >= score_no_season

    def test_score_deterministic(self):
        """相同输入 → 相同输出"""
        candidate = self._make_candidate(30, ["孤独"])
        ts = time.time()
        score1 = compute_trigger_score_v2(candidate, current_ts=ts)
        score2 = compute_trigger_score_v2(candidate, current_ts=ts)
        assert score1 == score2
