from common import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AnchorGeneratedEvent(_message.Message):
    __slots__ = ("event_id", "anchor_id", "anchor_type", "topics", "quality_score", "created_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    anchor_id: str
    anchor_type: _common_pb2.AnchorType
    topics: _containers.RepeatedScalarFieldContainer[str]
    quality_score: float
    created_at: int
    def __init__(self, event_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., anchor_type: _Optional[_Union[_common_pb2.AnchorType, str]] = ..., topics: _Optional[_Iterable[str]] = ..., quality_score: _Optional[float] = ..., created_at: _Optional[int] = ...) -> None: ...

class AnchorUpdatedEvent(_message.Message):
    __slots__ = ("event_id", "anchor_id", "updated_fields", "updated_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    anchor_id: str
    updated_fields: _containers.RepeatedScalarFieldContainer[str]
    updated_at: int
    def __init__(self, event_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., updated_fields: _Optional[_Iterable[str]] = ..., updated_at: _Optional[int] = ...) -> None: ...

class AnchorReplayedEvent(_message.Message):
    __slots__ = ("event_id", "anchor_id", "user_id", "trigger_type", "replayed_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_TYPE_FIELD_NUMBER: _ClassVar[int]
    REPLAYED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    anchor_id: str
    user_id: str
    trigger_type: str
    replayed_at: int
    def __init__(self, event_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., user_id: _Optional[str] = ..., trigger_type: _Optional[str] = ..., replayed_at: _Optional[int] = ...) -> None: ...

class ReactionSubmittedEvent(_message.Message):
    __slots__ = ("event_id", "user_id", "anchor_id", "reaction_type", "emotion_word", "opinion_text", "opinion_vector", "created_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    REACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMOTION_WORD_FIELD_NUMBER: _ClassVar[int]
    OPINION_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPINION_VECTOR_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_id: str
    anchor_id: str
    reaction_type: _common_pb2.ReactionType
    emotion_word: _common_pb2.EmotionWord
    opinion_text: str
    opinion_vector: bytes
    created_at: int
    def __init__(self, event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., reaction_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., emotion_word: _Optional[_Union[_common_pb2.EmotionWord, str]] = ..., opinion_text: _Optional[str] = ..., opinion_vector: _Optional[bytes] = ..., created_at: _Optional[int] = ...) -> None: ...

class ReactionProcessedEvent(_message.Message):
    __slots__ = ("event_id", "original_event_id", "user_id", "anchor_id", "resonance_value", "relationship_score", "related_user_id", "new_trust_level", "processed_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_VALUE_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    RELATED_USER_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_TRUST_LEVEL_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    original_event_id: str
    user_id: str
    anchor_id: str
    resonance_value: float
    relationship_score: float
    related_user_id: str
    new_trust_level: _common_pb2.TrustLevel
    processed_at: int
    def __init__(self, event_id: _Optional[str] = ..., original_event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., resonance_value: _Optional[float] = ..., relationship_score: _Optional[float] = ..., related_user_id: _Optional[str] = ..., new_trust_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., processed_at: _Optional[int] = ...) -> None: ...

class ResonanceUpdatedEvent(_message.Message):
    __slots__ = ("event_id", "user_a_id", "user_b_id", "anchor_id", "old_score_a_to_b", "new_score_a_to_b", "old_score_b_to_a", "new_score_b_to_a", "topics", "updated_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    OLD_SCORE_A_TO_B_FIELD_NUMBER: _ClassVar[int]
    NEW_SCORE_A_TO_B_FIELD_NUMBER: _ClassVar[int]
    OLD_SCORE_B_TO_A_FIELD_NUMBER: _ClassVar[int]
    NEW_SCORE_B_TO_A_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_a_id: str
    user_b_id: str
    anchor_id: str
    old_score_a_to_b: float
    new_score_a_to_b: float
    old_score_b_to_a: float
    new_score_b_to_a: float
    topics: _containers.RepeatedScalarFieldContainer[str]
    updated_at: int
    def __init__(self, event_id: _Optional[str] = ..., user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., old_score_a_to_b: _Optional[float] = ..., new_score_a_to_b: _Optional[float] = ..., old_score_b_to_a: _Optional[float] = ..., new_score_b_to_a: _Optional[float] = ..., topics: _Optional[_Iterable[str]] = ..., updated_at: _Optional[int] = ...) -> None: ...

class TrustLevelChangedEvent(_message.Message):
    __slots__ = ("event_id", "user_a_id", "user_b_id", "old_level", "new_level", "confidant_eligible", "changed_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    OLD_LEVEL_FIELD_NUMBER: _ClassVar[int]
    NEW_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CONFIDANT_ELIGIBLE_FIELD_NUMBER: _ClassVar[int]
    CHANGED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_a_id: str
    user_b_id: str
    old_level: _common_pb2.TrustLevel
    new_level: _common_pb2.TrustLevel
    confidant_eligible: bool
    changed_at: int
    def __init__(self, event_id: _Optional[str] = ..., user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ..., old_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., new_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., confidant_eligible: bool = ..., changed_at: _Optional[int] = ...) -> None: ...

class TraceFoundEvent(_message.Message):
    __slots__ = ("event_id", "observer_user_id", "traced_user_hash", "anchor_id", "relationship_score", "found_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    OBSERVER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    TRACED_USER_HASH_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    FOUND_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    observer_user_id: str
    traced_user_hash: str
    anchor_id: str
    relationship_score: float
    found_at: int
    def __init__(self, event_id: _Optional[str] = ..., observer_user_id: _Optional[str] = ..., traced_user_hash: _Optional[str] = ..., anchor_id: _Optional[str] = ..., relationship_score: _Optional[float] = ..., found_at: _Optional[int] = ...) -> None: ...

class GovernanceDecisionEvent(_message.Message):
    __slots__ = ("event_id", "decision", "decided_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    DECIDED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    decision: _common_pb2.GovernanceDecision
    decided_at: int
    def __init__(self, event_id: _Optional[str] = ..., decision: _Optional[_Union[_common_pb2.GovernanceDecision, _Mapping]] = ..., decided_at: _Optional[int] = ...) -> None: ...

class ContentMarkedEvent(_message.Message):
    __slots__ = ("event_id", "content_id", "content_type", "marker_token_hash", "mark_type", "reason", "marked_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    MARKER_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    MARK_TYPE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    MARKED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    content_id: str
    content_type: _common_pb2.ContentSource
    marker_token_hash: str
    mark_type: _common_pb2.ReactionType
    reason: str
    marked_at: int
    def __init__(self, event_id: _Optional[str] = ..., content_id: _Optional[str] = ..., content_type: _Optional[_Union[_common_pb2.ContentSource, str]] = ..., marker_token_hash: _Optional[str] = ..., mark_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., reason: _Optional[str] = ..., marked_at: _Optional[int] = ...) -> None: ...

class AnomalyDetectedEvent(_message.Message):
    __slots__ = ("event_id", "anchor_id", "anomaly_type", "description", "severity", "recommended_actions", "detected_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_ACTIONS_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    anchor_id: str
    anomaly_type: str
    description: str
    severity: float
    recommended_actions: _containers.RepeatedScalarFieldContainer[str]
    detected_at: int
    def __init__(self, event_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., anomaly_type: _Optional[str] = ..., description: _Optional[str] = ..., severity: _Optional[float] = ..., recommended_actions: _Optional[_Iterable[str]] = ..., detected_at: _Optional[int] = ...) -> None: ...

class MarkerCreditUpdatedEvent(_message.Message):
    __slots__ = ("event_id", "marker_token_hash", "old_credit", "new_credit", "was_accurate", "updated_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    MARKER_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    OLD_CREDIT_FIELD_NUMBER: _ClassVar[int]
    NEW_CREDIT_FIELD_NUMBER: _ClassVar[int]
    WAS_ACCURATE_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    marker_token_hash: str
    old_credit: float
    new_credit: float
    was_accurate: bool
    updated_at: int
    def __init__(self, event_id: _Optional[str] = ..., marker_token_hash: _Optional[str] = ..., old_credit: _Optional[float] = ..., new_credit: _Optional[float] = ..., was_accurate: bool = ..., updated_at: _Optional[int] = ...) -> None: ...

class ConfidantEstablishedEvent(_message.Message):
    __slots__ = ("event_id", "user_a_id", "user_b_id", "established_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    ESTABLISHED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_a_id: str
    user_b_id: str
    established_at: int
    def __init__(self, event_id: _Optional[str] = ..., user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ..., established_at: _Optional[int] = ...) -> None: ...

class UserActivityChangedEvent(_message.Message):
    __slots__ = ("event_id", "user_id", "is_active", "last_device", "changed_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    LAST_DEVICE_FIELD_NUMBER: _ClassVar[int]
    CHANGED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_id: str
    is_active: bool
    last_device: _common_pb2.DeviceType
    changed_at: int
    def __init__(self, event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., is_active: bool = ..., last_device: _Optional[_Union[_common_pb2.DeviceType, str]] = ..., changed_at: _Optional[int] = ...) -> None: ...

class ContextStateChangedEvent(_message.Message):
    __slots__ = ("event_id", "user_id", "scene_type", "mood_hint", "attention_level", "active_device", "timestamp")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCENE_TYPE_FIELD_NUMBER: _ClassVar[int]
    MOOD_HINT_FIELD_NUMBER: _ClassVar[int]
    ATTENTION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_DEVICE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_id: str
    scene_type: str
    mood_hint: str
    attention_level: str
    active_device: _common_pb2.DeviceType
    timestamp: int
    def __init__(self, event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., scene_type: _Optional[str] = ..., mood_hint: _Optional[str] = ..., attention_level: _Optional[str] = ..., active_device: _Optional[_Union[_common_pb2.DeviceType, str]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class ContextualAnchorHintEvent(_message.Message):
    __slots__ = ("event_id", "user_id", "recommended_scene", "topic_hints", "generated_at")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_SCENE_FIELD_NUMBER: _ClassVar[int]
    TOPIC_HINTS_FIELD_NUMBER: _ClassVar[int]
    GENERATED_AT_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_id: str
    recommended_scene: str
    topic_hints: _containers.RepeatedScalarFieldContainer[str]
    generated_at: int
    def __init__(self, event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., recommended_scene: _Optional[str] = ..., topic_hints: _Optional[_Iterable[str]] = ..., generated_at: _Optional[int] = ...) -> None: ...
