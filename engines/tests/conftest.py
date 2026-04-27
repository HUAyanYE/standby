"""
Pytest 配置文件 - 提供共享 fixtures
"""

import sys
import os
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加引擎目录到 Python 路径
engines_dir = Path(__file__).parent.parent
sys.path.insert(0, str(engines_dir))
sys.path.insert(0, str(engines_dir / "shared"))


# ============================================================
# 基础 Fixtures
# ============================================================

@pytest.fixture
def sample_embedding():
    """示例向量 (768维)"""
    np.random.seed(42)
    return np.random.randn(768).astype(np.float32)


@pytest.fixture
def sample_embeddings(sample_embedding):
    """多个示例向量"""
    return [sample_embedding + np.random.randn(768).astype(np.float32) * 0.1 
            for _ in range(5)]


@pytest.fixture
def mock_pg():
    """Mock PostgreSQL 连接"""
    mock = MagicMock()
    mock.cursor.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_mongo():
    """Mock MongoDB 连接"""
    mock = MagicMock()
    mock.reactions = MagicMock()
    return mock


# ============================================================
# Resonance Engine Fixtures
# ============================================================

@pytest.fixture
def sample_reaction():
    """示例反应数据"""
    from resonance_engine.resonance_calculator_v2 import Reaction, ReactionType, EmotionWord
    return Reaction(
        user_id="test_user_001",
        anchor_id="test_anchor_001",
        reaction_type=ReactionType.RESONANCE,
        opinion_text="这是一个测试观点",
        emotion_word=EmotionWord.EMPATHY,
        timestamp=1700000000.0,
    )


@pytest.fixture
def sample_anchor(sample_embedding):
    """示例锚点数据"""
    from resonance_engine.resonance_calculator_v2 import Anchor
    return Anchor(
        id="test_anchor_001",
        text="中美关系的深层逻辑",
        topics=["国际关系", "中美博弈"],
        embedding=sample_embedding,
    )


@pytest.fixture
def resonance_calculator():
    """共鸣计算器模块"""
    from resonance_engine import resonance_calculator_v2 as rc
    return rc


# ============================================================
# Anchor Engine Fixtures
# ============================================================

@pytest.fixture
def anchor_calculator():
    """锚点计算器模块"""
    # 延迟导入，避免依赖问题
    try:
        from anchor_engine import anchor_calculator as ac
        return ac
    except ImportError:
        pytest.skip("anchor_engine 模块不可用")


# ============================================================
# Governance Engine Fixtures
# ============================================================

@pytest.fixture
def governance_calculator():
    """治理计算器模块"""
    try:
        from governance_engine import governance_calculator as gc
        return gc
    except ImportError:
        pytest.skip("governance_engine 模块不可用")


# ============================================================
# Mock 数据库操作
# ============================================================

@pytest.fixture
def mock_db_operations():
    """Mock 数据库操作"""
    with patch('shared.db.get_pg') as mock_pg, \
         patch('shared.db.get_mongo') as mock_mongo:
        
        # 配置 mock
        mock_pg.return_value = MagicMock()
        mock_mongo.return_value = MagicMock()
        
        yield {
            'pg': mock_pg,
            'mongo': mock_mongo,
        }
