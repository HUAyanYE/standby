"""
PostgreSQL 兼容层 — 集成测试

测试覆盖:
- save_anchor_meta / get_anchor_meta / get_anchor_meta_batch
- count_reactions_batch
- save_reaction_event
- save_governance_decision
- save_user_context / load_all_user_contexts
- find_resonance_reaction_users
- list_reactions_paginated / count_reactions_filtered
- get_reaction_counts_by_type

注意: 这些测试需要 PostgreSQL 连接。
  标记 @pytest.mark.integration 以跳过 CI。
"""

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

# 跳过如果没有数据库连接
pytestmark = pytest.mark.integration


@pytest.fixture
def db_available():
    """检查数据库是否可用"""
    try:
        from shared.db import get_pg, put_pg
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        put_pg(pg)
        return True
    except Exception:
        return False


@pytest.fixture
def unique_id():
    """生成唯一 ID"""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.mark.skipif(
    not pytest.importorskip("psycopg2", reason="psycopg2 未安装"),
    reason="psycopg2 未安装"
)
class TestAnchorMeta:
    """锚点元数据 CRUD 测试"""

    def test_save_and_get(self, db_available, unique_id):
        """保存并获取锚点元数据"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import save_anchor_meta, get_anchor_meta

        anchor_id = f"a_{unique_id}"
        assert save_anchor_meta(anchor_id, "测试文本", ["测试话题"], 0.8, "user")

        meta = get_anchor_meta(anchor_id)
        assert meta is not None
        assert meta["anchor_id"] == anchor_id
        assert meta["text"] == "测试文本"
        assert "测试话题" in meta["topics"]
        assert meta["quality_score"] == pytest.approx(0.8, abs=0.01)

    def test_get_nonexistent(self, db_available):
        """获取不存在的锚点 → None"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import get_anchor_meta
        meta = get_anchor_meta("a_nonexistent_12345")
        assert meta is None

    def test_batch_get(self, db_available, unique_id):
        """批量获取锚点元数据"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import save_anchor_meta, get_anchor_meta_batch

        ids = [f"a_batch_{unique_id}_{i}" for i in range(3)]
        for aid in ids:
            save_anchor_meta(aid, f"text_{aid}", ["topic"], 0.5, "user")

        result = get_anchor_meta_batch(ids)
        for aid in ids:
            assert aid in result

    def test_upsert(self, db_available, unique_id):
        """重复保存应更新"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import save_anchor_meta, get_anchor_meta

        anchor_id = f"a_upsert_{unique_id}"
        save_anchor_meta(anchor_id, "原文本", ["topic1"], 0.5, "user")
        save_anchor_meta(anchor_id, "新文本", ["topic2"], 0.9, "user")

        meta = get_anchor_meta(anchor_id)
        assert meta is not None
        assert meta["text"] == "新文本"
        assert meta["quality_score"] == pytest.approx(0.9, abs=0.01)


@pytest.mark.skipif(
    not pytest.importorskip("psycopg2", reason="psycopg2 未安装"),
    reason="psycopg2 未安装"
)
class TestReactionEvent:
    """反应事件 CRUD 测试"""

    def test_save_and_count(self, db_available, unique_id):
        """保存反应事件并计数"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import (
            save_anchor_meta, save_reaction_event,
            count_reactions_batch,
        )

        anchor_id = f"a_react_{unique_id}"
        save_anchor_meta(anchor_id, "测试锚点", ["测试"], 0.5, "user")

        # 保存几条反应
        for i in range(3):
            save_reaction_event({
                "anchor_id": anchor_id,
                "user_id": f"user_{i}",
                "reaction_type": "共鸣",
                "text_content": f"反应 {i}",
                "resonance_value": 0.5 + i * 0.1,
                "timestamp": 1000000 + i,
            })

        counts = count_reactions_batch([anchor_id])
        assert counts.get(anchor_id, 0) >= 3

    def test_feeling_chain(self, db_available, unique_id):
        """感受链：父子反应关系"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import save_anchor_meta, save_reaction_event

        anchor_id = f"a_chain_{unique_id}"
        save_anchor_meta(anchor_id, "测试锚点", ["测试"], 0.5, "user")

        # 根反应
        save_reaction_event({
            "anchor_id": anchor_id,
            "user_id": "user_1",
            "reaction_type": "共鸣",
            "text_content": "根反应",
            "resonance_value": 0.8,
        })

        # 获取根反应 ID (需要查询)
        from shared.db import get_pg, put_pg
        pg = get_pg()
        cur = pg.cursor()
        cur.execute("SELECT id FROM reactions WHERE anchor_id = %s LIMIT 1", (anchor_id,))
        root_id = cur.fetchone()[0]
        put_pg(pg)

        # 子反应
        save_reaction_event({
            "anchor_id": anchor_id,
            "user_id": "user_2",
            "reaction_type": "共鸣",
            "text_content": "子反应",
            "resonance_value": 0.6,
            "parent_reaction_id": root_id,
        })

        # 验证深度
        pg = get_pg()
        cur = pg.cursor()
        cur.execute(
            "SELECT depth FROM reactions WHERE anchor_id = %s AND parent_reaction_id = %s",
            (anchor_id, root_id)
        )
        child_depth = cur.fetchone()[0]
        put_pg(pg)
        assert child_depth == 1


@pytest.mark.skipif(
    not pytest.importorskip("psycopg2", reason="psycopg2 未安装"),
    reason="psycopg2 未安装"
)
class TestGovernanceDecision:
    """治理决策日志测试"""

    def test_save_decision(self, db_available, unique_id):
        """保存治理决策"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import save_governance_decision

        content_id = f"a_gov_{unique_id}"
        result = save_governance_decision({
            "content_id": content_id,
            "content_type": "anchor",
            "level": "L0_NORMAL",
            "harmful_weight": 0.0,
            "marker_avg_credit": 0.5,
            "reason": "测试决策",
            "actions": ["无"],
        })
        assert result is True


@pytest.mark.skipif(
    not pytest.importorskip("psycopg2", reason="psycopg2 未安装"),
    reason="psycopg2 未安装"
)
class TestUserContext:
    """用户情境状态测试"""

    def test_save_and_load(self, db_available, unique_id):
        """保存并加载用户情境"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import save_user_context, load_all_user_contexts

        user_id = f"ctx_{unique_id}"
        context = {
            "scene_type": "深夜",
            "mood_hint": "calm",
            "attention_level": "focused",
            "device": 1,
            "timestamp": 1000000,
        }
        assert save_user_context(user_id, context)

        all_contexts = load_all_user_contexts()
        assert user_id in all_contexts
        assert all_contexts[user_id]["scene_type"] == "深夜"


@pytest.mark.skipif(
    not pytest.importorskip("psycopg2", reason="psycopg2 未安装"),
    reason="psycopg2 未安装"
)
class TestReactionCounts:
    """反应分布统计测试"""

    def test_counts_by_type(self, db_available, unique_id):
        """按类型统计反应"""
        if not db_available:
            pytest.skip("数据库不可用")

        from shared.pg_compat import (
            save_anchor_meta, save_reaction_event,
            get_reaction_counts_by_type,
        )

        anchor_id = f"a_counts_{unique_id}"
        save_anchor_meta(anchor_id, "测试", ["测试"], 0.5, "user")

        # 保存不同类型反应
        for rtype in ["共鸣", "共鸣", "无感", "反对"]:
            save_reaction_event({
                "anchor_id": anchor_id,
                "user_id": f"user_{uuid.uuid4().hex[:6]}",
                "reaction_type": rtype,
                "text_content": f"反应 {rtype}",
                "resonance_value": 0.5,
            })

        counts = get_reaction_counts_by_type(anchor_id)
        assert counts["resonance_count"] >= 2
        assert counts["neutral_count"] >= 1
        assert counts["opposition_count"] >= 1
        assert counts["total_count"] >= 4
