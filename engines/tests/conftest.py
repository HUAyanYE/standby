"""
Standby 引擎测试 — 公共 fixtures
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# 将引擎目录加入 path
ENGINES_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ENGINES_DIR))
sys.path.insert(0, str(ENGINES_DIR / "resonance_engine"))
sys.path.insert(0, str(ENGINES_DIR / "governance_engine"))
sys.path.insert(0, str(ENGINES_DIR / "anchor_engine"))
sys.path.insert(0, str(ENGINES_DIR / "shared"))


@pytest.fixture
def random_embedding():
    """生成随机 768 维单位向量"""
    vec = np.random.randn(768).astype(np.float32)
    return vec / np.linalg.norm(vec)


@pytest.fixture
def similar_embedding():
    """生成与 random_embedding 相似的向量 (余弦相似度 ~0.8)"""
    base = np.random.randn(768).astype(np.float32)
    base = base / np.linalg.norm(base)
    noise = np.random.randn(768).astype(np.float32) * 0.2
    vec = base + noise
    return vec / np.linalg.norm(vec)


@pytest.fixture
def dissimilar_embedding():
    """生成与 random_embedding 不相似的向量 (余弦相似度 ~0.1)"""
    vec = np.random.randn(768).astype(np.float32)
    return vec / np.linalg.norm(vec)


@pytest.fixture
def sample_texts():
    """样本文本集合"""
    return {
        "short": "今天天气不错。",
        "medium": "每天早上挤地铁的时候，我都会想起小时候在乡下坐拖拉机的日子。那时候觉得慢，现在觉得挤。",
        "long": "深夜一个人在便利店吃关东煮，看着窗外的霓虹灯，突然觉得这座城市既陌生又温暖。"
               "我想起了第一次来这个城市的时候，那时候什么都不懂，只觉得这里灯火通明。"
               "现在我在这里生活了五年，有了自己的小窝，有了几个可以深夜打电话的朋友。"
               "但有时候，还是会觉得孤独。不是那种没人陪的孤独，而是那种身处人群中的孤独。",
        "emotional": "那一刻，我泪流满面。不是因为难过，而是因为终于被理解了。",
        "abstract": "人生的意义在于不断追寻自我价值的实现。",
        "tangible": "那杯咖啡已经凉了，但我还是端起来喝了一口。苦涩的味道让我清醒了一些。",
    }
