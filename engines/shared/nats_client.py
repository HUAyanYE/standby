"""
Standby 引擎间通信 — NATS 客户端

异步事件发布/订阅:
- 引擎完成工作后发布事件到 NATS
- 其他引擎订阅相关 topic 接收通知
- 使用 JetStream 保证关键事件不丢失

对齐 proto/nats/events.proto
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级 — 决定是否使用 JetStream"""
    CRITICAL = "critical"    # JetStream, 持久化 (治理决策、关系变更)
    STANDARD = "standard"    # JetStream, 短期保留 (锚点生成、反应处理)
    TRANSIENT = "transient"  # 纯 Pub/Sub, 不持久化 (情境状态)


# Topic → Stream 映射 (JetStream 配置)
STREAM_CONFIGS = {
    "anchor_events": {
        "subjects": ["anchor.>"],
        "retention_days": 7,
    },
    "reaction_events": {
        "subjects": ["reaction.>"],
        "retention_days": 30,
    },
    "resonance_events": {
        "subjects": ["resonance.>"],
        "retention_days": 90,
    },
    "governance_events": {
        "subjects": ["governance.>"],
        "retention_days": 180,
    },
}

# Topic → 优先级映射
TOPIC_PRIORITY = {
    "anchor.generated": EventPriority.STANDARD,
    "anchor.updated": EventPriority.STANDARD,
    "anchor.replayed": EventPriority.TRANSIENT,
    "reaction.submitted": EventPriority.STANDARD,
    "reaction.processed": EventPriority.STANDARD,
    "resonance.updated": EventPriority.CRITICAL,
    "resonance.trust_changed": EventPriority.CRITICAL,
    "resonance.trace_found": EventPriority.TRANSIENT,
    "governance.decision": EventPriority.CRITICAL,
    "governance.marked": EventPriority.STANDARD,
    "governance.anomaly": EventPriority.CRITICAL,
    "governance.credit_updated": EventPriority.STANDARD,
    "user.confidant_established": EventPriority.CRITICAL,
    "user.activity_changed": EventPriority.TRANSIENT,
    "context.state_changed": EventPriority.TRANSIENT,
    "context.anchor_hint": EventPriority.TRANSIENT,
}


@dataclass
class Event:
    """通用事件结构"""
    event_id: str
    topic: str
    payload: dict
    timestamp: float = 0.0
    source_engine: str = ""
    priority: EventPriority = EventPriority.STANDARD
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_json(self) -> bytes:
        data = asdict(self)
        data["priority"] = self.priority.value
        return json.dumps(data, ensure_ascii=False).encode("utf-8")
    
    @classmethod
    def from_json(cls, data: bytes) -> "Event":
        d = json.loads(data)
        d["priority"] = EventPriority(d.get("priority", "standard"))
        return cls(**d)


class NATSClient:
    """NATS 客户端封装
    
    支持两种模式:
    1. 生产模式: 连接真实 NATS 服务器
    2. 开发模式: 内存模拟 (无需 NATS 服务器)
    """
    
    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        engine_name: str = "unknown",
        use_mock: bool = False,
    ):
        self.nats_url = nats_url
        self.engine_name = engine_name
        self.use_mock = use_mock
        
        self._nc = None           # NATS 连接
        self._js = None           # JetStream 上下文
        self._subscriptions = {}  # topic → [callback]
        self._mock_events = []    # 开发模式: 事件日志
        
        logger.info(f"NATS 客户端初始化: {engine_name} → {nats_url} (mock={use_mock})")
    
    async def connect(self):
        """连接 NATS 服务器"""
        if self.use_mock:
            logger.info("开发模式: 跳过 NATS 连接")
            return
        
        try:
            # 使用 sys.path 过滤掉 proto 生成的 nats 目录
            import sys
            import importlib
            
            # 临时移除 proto 路径，避免 nats 模块冲突
            proto_path = None
            for p in sys.path:
                if 'proto/generated/python' in p:
                    proto_path = p
                    break
            
            if proto_path:
                sys.path.remove(proto_path)
            
            # 重新导入 nats (使用系统安装的 nats-py)
            if 'nats' in sys.modules:
                del sys.modules['nats']
            
            import nats
            self._nc = await nats.connect(self.nats_url)
            self._js = self._nc.jetstream()
            logger.info(f"已连接 NATS: {self.nats_url}")
            
            # 恢复 proto 路径
            if proto_path:
                sys.path.insert(0, proto_path)
            
            # 确保 streams 存在
            await self._ensure_streams()
        except Exception as e:
            logger.error(f"NATS 连接失败: {e}")
            logger.warning("降级到 mock 模式")
            self.use_mock = True
    
    async def _ensure_streams(self):
        """确保 JetStream streams 已创建"""
        if not self._js:
            return
        
        for stream_name, config in STREAM_CONFIGS.items():
            try:
                from nats.js.api import StreamConfig
                
                await self._js.add_stream(
                    name=stream_name,
                    subjects=config["subjects"],
                    max_age=config["retention_days"] * 86400,  # 转秒
                )
                logger.info(f"Stream 已就绪: {stream_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    pass
                else:
                    logger.warning(f"创建 stream {stream_name} 失败: {e}")
    
    async def publish(self, event: Event):
        """发布事件"""
        topic = event.topic
        data = event.to_json()
        
        if self.use_mock:
            self._mock_events.append(event)
            logger.debug(f"[mock] 发布事件: {topic} (id={event.event_id})")
            return
        
        priority = TOPIC_PRIORITY.get(topic, EventPriority.STANDARD)
        
        if priority in (EventPriority.CRITICAL, EventPriority.STANDARD):
            # JetStream 发布 (持久化)
            await self._js.publish(topic, data)
        else:
            # 普通 Pub/Sub
            await self._nc.publish(topic, data)
        
        logger.info(f"发布事件: {topic} (id={event.event_id}, priority={priority.value})")

    async def publish_batch(self, events):
        """批量发布事件 (减少网络 roundtrip)"""
        if not events:
            return

        if self.use_mock:
            for event in events:
                self._mock_events.append(event)
            logger.debug(f"[mock] 批量发布 {len(events)} 个事件")
            return

        import asyncio
        tasks = []
        for event in events:
            priority = TOPIC_PRIORITY.get(event.topic, EventPriority.STANDARD)
            if priority in (EventPriority.CRITICAL, EventPriority.STANDARD):
                tasks.append(self._js.publish(event.topic, event.to_json()))
            else:
                tasks.append(self._nc.publish(event.topic, event.to_json()))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"批量发布 {len(events)} 个事件")

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[Event], Any],
        durable_name: Optional[str] = None,
    ):
        """订阅事件
        
        Args:
            topic: 主题 (支持通配符, 如 "anchor.>")
            callback: 回调函数
            durable_name: 持久化订阅名称 (JetStream)
        """
        if self.use_mock:
            self._subscriptions.setdefault(topic, []).append(callback)
            logger.info(f"[mock] 订阅: {topic}")
            return
        
        # 查找主题优先级
        if topic in TOPIC_PRIORITY:
            priority = TOPIC_PRIORITY[topic]
        elif ">" in topic:
            # 通配符订阅：查找匹配的前缀
            prefix = topic.split(">")[0]  # 例如 "anchor."
            matching_priorities = [
                p for t, p in TOPIC_PRIORITY.items() 
                if t.startswith(prefix)
            ]
            priority = matching_priorities[0] if matching_priorities else EventPriority.STANDARD
        else:
            priority = EventPriority.STANDARD
        
        async def message_handler(msg):
            try:
                event = Event.from_json(msg.data)
                await callback(event)
                await msg.ack()
            except Exception as e:
                logger.error(f"处理事件失败: {e}")
                await msg.nak()
        
        if priority in (EventPriority.CRITICAL, EventPriority.STANDARD):
            # JetStream 订阅 (带持久化)
            sub = await self._js.subscribe(
                topic,
                cb=message_handler,
                durable=durable_name or f"{self.engine_name}_{topic.replace('.', '_')}",
            )
        else:
            # 普通订阅
            sub = await self._subscribe(topic, message_handler)
        
        logger.info(f"订阅: {topic} (engine={self.engine_name})")
    
    async def _subscribe(self, topic, handler):
        """普通 NATS 订阅"""
        return await self._nc.subscribe(topic, cb=handler)
    
    async def disconnect(self):
        """断开连接"""
        if self._nc:
            await self._nc.drain()
            logger.info("NATS 连接已断开")
    
    def get_mock_events(self) -> list:
        """获取开发模式下的事件日志"""
        return self._mock_events


# ============================================================
# 事件构建器 — 类型安全的事件创建
# ============================================================

import uuid

class EventBuilder:
    """事件构建器 — 简化事件创建"""
    
    @staticmethod
    def anchor_generated(
        anchor_id: str,
        anchor_type: str,
        topics: list,
        quality_score: float,
        source_engine: str = "anchor_engine",
    ) -> Event:
        return Event(
            event_id=str(uuid.uuid4()),
            topic="anchor.generated",
            payload={
                "anchor_id": anchor_id,
                "anchor_type": anchor_type,
                "topics": topics,
                "quality_score": quality_score,
            },
            source_engine=source_engine,
            priority=EventPriority.STANDARD,
        )
    
    @staticmethod
    def reaction_submitted(
        user_id: str,
        anchor_id: str,
        reaction_type: str,
        opinion_text: Optional[str] = None,
        source_engine: str = "gateway",
    ) -> Event:
        return Event(
            event_id=str(uuid.uuid4()),
            topic="reaction.submitted",
            payload={
                "user_id": user_id,
                "anchor_id": anchor_id,
                "reaction_type": reaction_type,
                "opinion_text": opinion_text,
            },
            source_engine=source_engine,
            priority=EventPriority.STANDARD,
        )
    
    @staticmethod
    def resonance_updated(
        user_a_id: str,
        user_b_id: str,
        anchor_id: str,
        old_score: float,
        new_score: float,
        source_engine: str = "resonance_engine",
    ) -> Event:
        return Event(
            event_id=str(uuid.uuid4()),
            topic="resonance.updated",
            payload={
                "user_a_id": user_a_id,
                "user_b_id": user_b_id,
                "anchor_id": anchor_id,
                "old_score": old_score,
                "new_score": new_score,
            },
            source_engine=source_engine,
            priority=EventPriority.CRITICAL,
        )
    
    @staticmethod
    def governance_decision(
        content_id: str,
        level: str,
        reason: str,
        actions: list,
        source_engine: str = "governance_engine",
    ) -> Event:
        return Event(
            event_id=str(uuid.uuid4()),
            topic="governance.decision",
            payload={
                "content_id": content_id,
                "level": level,
                "reason": reason,
                "actions": actions,
            },
            source_engine=source_engine,
            priority=EventPriority.CRITICAL,
        )


# ============================================================
# 测试
# ============================================================

async def run_tests():
    """NATS 客户端测试 (mock 模式)"""
    print("=" * 60)
    print("  NATS 客户端测试 (Mock 模式)")
    print("=" * 60)
    
    # 创建两个引擎的客户端
    anchor_client = NATSClient(engine_name="anchor_engine", use_mock=True)
    resonance_client = NATSClient(engine_name="resonance_engine", use_mock=True)
    
    # 共鸣引擎订阅锚点生成事件
    received_events = []
    
    async def on_anchor_generated(event: Event):
        received_events.append(event)
        print(f"  共鸣引擎收到: {event.topic} — {event.payload['anchor_id']}")
    
    await resonance_client.subscribe("anchor.generated", on_anchor_generated)
    
    # 锚点引擎发布事件
    event = EventBuilder.anchor_generated(
        anchor_id="a_001",
        anchor_type="platform_initial",
        topics=["孤独", "城市"],
        quality_score=0.85,
    )
    await anchor_client.publish(event)
    
    # 验证
    mock_events = anchor_client.get_mock_events()
    print(f"\n  发布事件数: {len(mock_events)}")
    print(f"  事件 ID: {mock_events[0].event_id}")
    print(f"  Topic: {mock_events[0].topic}")
    print(f"  Payload: {mock_events[0].payload}")
    
    # 测试反应事件
    reaction_event = EventBuilder.reaction_submitted(
        user_id="u_001",
        anchor_id="a_001",
        reaction_type="共鸣",
        opinion_text="深夜地铁确实很孤独。",
    )
    await anchor_client.publish(reaction_event)
    
    print(f"\n  总发布事件数: {len(anchor_client.get_mock_events())}")
    
    # JSON 序列化测试
    json_data = event.to_json()
    restored = Event.from_json(json_data)
    assert restored.topic == event.topic
    assert restored.payload == event.payload
    print(f"\n  JSON 序列化/反序列化: ✅")
    
    print(f"\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(run_tests())
