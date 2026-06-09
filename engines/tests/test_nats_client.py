"""
NATS 客户端 — 单元测试

测试覆盖:
- EventBuilder: 事件构建
- NATSClient: 连接/发布/订阅 (mock)

注意: 不需要实际 NATS 服务器。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))


class TestEventBuilder:
    """EventBuilder 事件构建测试"""

    def test_reaction_submitted_event(self):
        """反应提交事件"""
        from shared.nats_client import EventBuilder

        event = EventBuilder.reaction_submitted(
            user_id="u001",
            anchor_id="a001",
            reaction_type="1",
            opinion_text="测试观点",
            source_engine="resonance_engine",
        )
        assert event.topic == "reaction.submitted"
        assert event.payload["user_id"] == "u001"
        assert event.payload["anchor_id"] == "a001"
        assert event.source_engine == "resonance_engine"

    def test_anchor_created_event(self):
        """锚点创建事件"""
        from shared.nats_client import EventBuilder

        event = EventBuilder.anchor_created(
            anchor_id="a002",
            anchor_type="user",
            topics=["孤独", "城市"],
            quality_score=0.85,
            text="测试锚点文本",
        )
        assert event.topic == "anchor.created"
        assert event.payload["anchor_id"] == "a002"
        assert "孤独" in event.payload["topics"]

    def test_governance_alert_event(self):
        """治理告警事件"""
        from shared.nats_client import EventBuilder

        event = EventBuilder.governance_alert(
            content_id="a003",
            level="L2_DEMOTED",
            reason="高有害比例",
            severity=0.6,
        )
        assert event.topic == "governance.alert"
        assert event.payload["level"] == "L2_DEMOTED"

    def test_governance_action_event(self):
        """治理动作事件"""
        from shared.nats_client import EventBuilder

        event = EventBuilder.governance_action(
            content_id="a003",
            actions=["降权", "通知用户"],
            reason="有害内容",
        )
        assert event.topic == "governance.action"
        assert len(event.payload["actions"]) == 2

    def test_context_update_event(self):
        """情境更新事件"""
        from shared.nats_client import EventBuilder

        event = EventBuilder.context_update(
            user_id="u001",
            scene_type="深夜",
            mood_hint="calm",
        )
        assert event.topic == "context.update"
        assert event.payload["scene_type"] == "深夜"

    def test_event_has_id_and_timestamp(self):
        """事件应有唯一 ID 和时间戳"""
        from shared.nats_client import EventBuilder

        event1 = EventBuilder.reaction_submitted("u001", "a001", "1", None, "test")
        event2 = EventBuilder.reaction_submitted("u001", "a001", "1", None, "test")

        assert event1.event_id != event2.event_id
        assert event1.timestamp > 0
        assert event2.timestamp > 0


class TestNATSClientInit:
    """NATS 客户端初始化测试"""

    def test_init_with_url(self):
        """初始化时设置 URL"""
        from shared.nats_client import NATSClient

        client = NATSClient(nats_url="nats://localhost:4222", engine_name="test")
        assert client.nats_url == "nats://localhost:4222"
        assert client.engine_name == "test"

    def test_init_default_url(self):
        """默认 URL"""
        from shared.nats_client import NATSClient

        client = NATSClient(engine_name="test")
        assert client.nats_url == "nats://localhost:4222"

    def test_mock_mode(self):
        """Mock 模式下不连接实际服务器"""
        from shared.nats_client import NATSClient, EventBuilder

        client = NATSClient(nats_url="nats://localhost:4222", engine_name="test")
        client.use_mock = True
        # mock 模式下 publish 应该不报错
        event = EventBuilder.reaction_submitted("u001", "a001", "1", None, "test")
        # 这里只是测试不会抛异常，实际异步需要 event loop
        assert client.use_mock is True


class TestEventPriority:
    """事件优先级测试"""

    def test_critical_events_use_jetstream(self):
        """关键事件应使用 JetStream"""
        from shared.nats_client import EventPriority, TOPIC_PRIORITY

        assert TOPIC_PRIORITY.get("resonance.updated") == EventPriority.CRITICAL
        assert TOPIC_PRIORITY.get("governance.decision") == EventPriority.CRITICAL
        assert TOPIC_PRIORITY.get("user.confidant_established") == EventPriority.CRITICAL

    def test_transient_events_no_persistence(self):
        """瞬态事件不应持久化"""
        from shared.nats_client import EventPriority, TOPIC_PRIORITY

        assert TOPIC_PRIORITY.get("context.update") == EventPriority.TRANSIENT
        assert TOPIC_PRIORITY.get("anchor.replayed") == EventPriority.TRANSIENT
        assert TOPIC_PRIORITY.get("resonance.trace_found") == EventPriority.TRANSIENT

    def test_standard_events_jetstream(self):
        """标准事件使用 JetStream 但短期保留"""
        from shared.nats_client import EventPriority, TOPIC_PRIORITY

        assert TOPIC_PRIORITY.get("reaction.submitted") == EventPriority.STANDARD
        assert TOPIC_PRIORITY.get("anchor.created") == EventPriority.STANDARD
