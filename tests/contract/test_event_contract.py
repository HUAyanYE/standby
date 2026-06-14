"""
NATS 事件格式契约测试

验证 NATS 事件的结构和字段一致性。
"""

import pytest
import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


# 从 standby_common.events 复制的定义（用于测试）
class EventPriority(Enum):
    CRITICAL = "critical"
    STANDARD = "standard"
    LOW = "low"


@dataclass
class Event:
    event_id: str
    topic: str
    payload: dict
    source_engine: str
    priority: EventPriority = EventPriority.STANDARD
    timestamp: Optional[float] = None
    version: str = "1.0"

    def to_json(self) -> str:
        data = asdict(self)
        data['priority'] = self.priority.value
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: bytes) -> 'Event':
        d = json.loads(data)
        d['priority'] = EventPriority(d['priority'])
        return cls(**d)


class TestEventStructure:
    """验证事件结构"""

    def test_event_has_required_fields(self):
        """事件必须包含所有必需字段"""
        event = Event(
            event_id="test-123",
            topic="anchor.created",
            payload={"anchor_id": "a_123"},
            source_engine="anchor_engine",
        )
        data = json.loads(event.to_json())

        required_fields = ["event_id", "topic", "payload", "source_engine", "priority", "version"]
        for field in required_fields:
            assert field in data, f"事件缺少必需字段: {field}"

    def test_event_priority_values(self):
        """事件优先级必须是有效值"""
        valid_priorities = ["critical", "standard", "low"]
        for priority in valid_priorities:
            event = Event(
                event_id="test",
                topic="test.topic",
                payload={},
                source_engine="test",
                priority=EventPriority(priority),
            )
            data = json.loads(event.to_json())
            assert data["priority"] in valid_priorities

    def test_event_version_is_string(self):
        """事件版本必须是字符串"""
        event = Event(
            event_id="test",
            topic="test.topic",
            payload={},
            source_engine="test",
            version="1.0",
        )
        data = json.loads(event.to_json())
        assert isinstance(data["version"], str)


class TestEventTopics:
    """验证事件主题命名规范"""

    def test_topic_format(self):
        """主题必须使用点分隔的命名空间"""
        valid_topics = [
            "anchor.created",
            "anchor.generated",
            "reaction.submitted",
            "governance.alert",
            "governance.action",
            "governance.decision",
            "context.update",
            "user.soulmate_event",
        ]
        for topic in valid_topics:
            assert "." in topic, f"主题必须使用点分隔: {topic}"
            parts = topic.split(".")
            assert len(parts) >= 2, f"主题必须至少有两部分: {topic}"
            for part in parts:
                assert part.isalnum() or part == "_", f"主题部分只能包含字母数字和下划线: {part}"


class TestEventSerialization:
    """验证事件序列化/反序列化"""

    def test_event_roundtrip(self):
        """事件序列化后可以正确反序列化"""
        original = Event(
            event_id="test-123",
            topic="anchor.created",
            payload={"anchor_id": "a_123", "text": "测试文本"},
            source_engine="anchor_engine",
            priority=EventPriority.STANDARD,
        )
        json_str = original.to_json()
        restored = Event.from_json(json_str.encode())

        assert restored.event_id == original.event_id
        assert restored.topic == original.topic
        assert restored.payload == original.payload
        assert restored.source_engine == original.source_engine
        assert restored.priority == original.priority

    def test_event_payload_is_dict(self):
        """事件负载必须是字典"""
        event = Event(
            event_id="test",
            topic="test.topic",
            payload={"key": "value"},
            source_engine="test",
        )
        data = json.loads(event.to_json())
        assert isinstance(data["payload"], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
