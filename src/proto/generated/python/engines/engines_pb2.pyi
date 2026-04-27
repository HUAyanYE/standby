from common import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GenerateAnchorRequest(_message.Message):
    __slots__ = ("source_texts", "source_type", "topic_hints", "user_reactions")
    SOURCE_TEXTS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    TOPIC_HINTS_FIELD_NUMBER: _ClassVar[int]
    USER_REACTIONS_FIELD_NUMBER: _ClassVar[int]
    source_texts: _containers.RepeatedScalarFieldContainer[str]
    source_type: str
    topic_hints: _containers.RepeatedScalarFieldContainer[str]
    user_reactions: _containers.RepeatedCompositeFieldContainer[_common_pb2.Reaction]
    def __init__(self, source_texts: _Optional[_Iterable[str]] = ..., source_type: _Optional[str] = ..., topic_hints: _Optional[_Iterable[str]] = ..., user_reactions: _Optional[_Iterable[_Union[_common_pb2.Reaction, _Mapping]]] = ...) -> None: ...

class GenerateAnchorResponse(_message.Message):
    __slots__ = ("success", "anchor", "quality_score", "rejection_reason")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    REJECTION_REASON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    anchor: _common_pb2.Anchor
    quality_score: float
    rejection_reason: str
    def __init__(self, success: bool = ..., anchor: _Optional[_Union[_common_pb2.Anchor, _Mapping]] = ..., quality_score: _Optional[float] = ..., rejection_reason: _Optional[str] = ...) -> None: ...

class EvaluateAnchorQualityRequest(_message.Message):
    __slots__ = ("anchor",)
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    anchor: _common_pb2.Anchor
    def __init__(self, anchor: _Optional[_Union[_common_pb2.Anchor, _Mapping]] = ...) -> None: ...

class EvaluateAnchorQualityResponse(_message.Message):
    __slots__ = ("quality", "passes_threshold", "feedback")
    QUALITY_FIELD_NUMBER: _ClassVar[int]
    PASSES_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    quality: _common_pb2.AnchorQuality
    passes_threshold: bool
    feedback: str
    def __init__(self, quality: _Optional[_Union[_common_pb2.AnchorQuality, _Mapping]] = ..., passes_threshold: bool = ..., feedback: _Optional[str] = ...) -> None: ...

class GetAnchorMetadataRequest(_message.Message):
    __slots__ = ("anchor_id",)
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    def __init__(self, anchor_id: _Optional[str] = ...) -> None: ...

class GetAnchorMetadataResponse(_message.Message):
    __slots__ = ("found", "anchor_id", "topics", "anchor_type", "quality_score", "created_at")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    QUALITY_SCORE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    found: bool
    anchor_id: str
    topics: _containers.RepeatedScalarFieldContainer[str]
    anchor_type: _common_pb2.AnchorType
    quality_score: float
    created_at: int
    def __init__(self, found: bool = ..., anchor_id: _Optional[str] = ..., topics: _Optional[_Iterable[str]] = ..., anchor_type: _Optional[_Union[_common_pb2.AnchorType, str]] = ..., quality_score: _Optional[float] = ..., created_at: _Optional[int] = ...) -> None: ...

class GetAnchorVectorRequest(_message.Message):
    __slots__ = ("anchor_id",)
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    def __init__(self, anchor_id: _Optional[str] = ...) -> None: ...

class GetAnchorVectorResponse(_message.Message):
    __slots__ = ("found", "vector", "dimension")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    found: bool
    vector: bytes
    dimension: int
    def __init__(self, found: bool = ..., vector: _Optional[bytes] = ..., dimension: _Optional[int] = ...) -> None: ...

class ProcessReactionRequest(_message.Message):
    __slots__ = ("event_id", "user_id", "anchor_id", "reaction_type", "emotion_word", "opinion_text", "opinion_vector", "timestamp")
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    REACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMOTION_WORD_FIELD_NUMBER: _ClassVar[int]
    OPINION_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPINION_VECTOR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    user_id: str
    anchor_id: str
    reaction_type: _common_pb2.ReactionType
    emotion_word: _common_pb2.EmotionWord
    opinion_text: str
    opinion_vector: bytes
    timestamp: int
    def __init__(self, event_id: _Optional[str] = ..., user_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., reaction_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., emotion_word: _Optional[_Union[_common_pb2.EmotionWord, str]] = ..., opinion_text: _Optional[str] = ..., opinion_vector: _Optional[bytes] = ..., timestamp: _Optional[int] = ...) -> None: ...

class ProcessReactionResponse(_message.Message):
    __slots__ = ("success", "event_id", "resonance_value", "relationship_score", "related_user_id", "new_trust_level", "error", "processing_time_ms")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_VALUE_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    RELATED_USER_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_TRUST_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    event_id: str
    resonance_value: float
    relationship_score: float
    related_user_id: str
    new_trust_level: _common_pb2.TrustLevel
    error: str
    processing_time_ms: float
    def __init__(self, success: bool = ..., event_id: _Optional[str] = ..., resonance_value: _Optional[float] = ..., relationship_score: _Optional[float] = ..., related_user_id: _Optional[str] = ..., new_trust_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., error: _Optional[str] = ..., processing_time_ms: _Optional[float] = ...) -> None: ...

class ProcessBatchRequest(_message.Message):
    __slots__ = ("reactions", "batch_id")
    REACTIONS_FIELD_NUMBER: _ClassVar[int]
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    reactions: _containers.RepeatedCompositeFieldContainer[ProcessReactionRequest]
    batch_id: str
    def __init__(self, reactions: _Optional[_Iterable[_Union[ProcessReactionRequest, _Mapping]]] = ..., batch_id: _Optional[str] = ...) -> None: ...

class ProcessBatchResponse(_message.Message):
    __slots__ = ("success", "batch_id", "total_processed", "total_errors", "results")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_PROCESSED_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ERRORS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    batch_id: str
    total_processed: int
    total_errors: int
    results: _containers.RepeatedCompositeFieldContainer[ProcessReactionResponse]
    def __init__(self, success: bool = ..., batch_id: _Optional[str] = ..., total_processed: _Optional[int] = ..., total_errors: _Optional[int] = ..., results: _Optional[_Iterable[_Union[ProcessReactionResponse, _Mapping]]] = ...) -> None: ...

class GetRelationshipScoreRequest(_message.Message):
    __slots__ = ("user_a_id", "user_b_id")
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    user_a_id: str
    user_b_id: str
    def __init__(self, user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ...) -> None: ...

class GetRelationshipScoreResponse(_message.Message):
    __slots__ = ("found", "score_a_to_b", "score_b_to_a", "topic_diversity", "resonance_count")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    SCORE_A_TO_B_FIELD_NUMBER: _ClassVar[int]
    SCORE_B_TO_A_FIELD_NUMBER: _ClassVar[int]
    TOPIC_DIVERSITY_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    found: bool
    score_a_to_b: float
    score_b_to_a: float
    topic_diversity: int
    resonance_count: int
    def __init__(self, found: bool = ..., score_a_to_b: _Optional[float] = ..., score_b_to_a: _Optional[float] = ..., topic_diversity: _Optional[int] = ..., resonance_count: _Optional[int] = ...) -> None: ...

class GetReactionDistributionRequest(_message.Message):
    __slots__ = ("anchor_id",)
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    def __init__(self, anchor_id: _Optional[str] = ...) -> None: ...

class GetReactionDistributionResponse(_message.Message):
    __slots__ = ("found", "distribution", "anomaly_flags")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    DISTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_FLAGS_FIELD_NUMBER: _ClassVar[int]
    found: bool
    distribution: _common_pb2.ReactionSummary
    anomaly_flags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, found: bool = ..., distribution: _Optional[_Union[_common_pb2.ReactionSummary, _Mapping]] = ..., anomaly_flags: _Optional[_Iterable[str]] = ...) -> None: ...

class FindResonancePairsRequest(_message.Message):
    __slots__ = ("user_id", "anchor_id", "min_score")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    MIN_SCORE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    anchor_id: str
    min_score: float
    def __init__(self, user_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., min_score: _Optional[float] = ...) -> None: ...

class FindResonancePairsResponse(_message.Message):
    __slots__ = ("pairs",)
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    pairs: _containers.RepeatedCompositeFieldContainer[ResonancePair]
    def __init__(self, pairs: _Optional[_Iterable[_Union[ResonancePair, _Mapping]]] = ...) -> None: ...

class ResonancePair(_message.Message):
    __slots__ = ("other_user_id", "relationship_score", "shared_anchors")
    OTHER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    SHARED_ANCHORS_FIELD_NUMBER: _ClassVar[int]
    other_user_id: str
    relationship_score: float
    shared_anchors: int
    def __init__(self, other_user_id: _Optional[str] = ..., relationship_score: _Optional[float] = ..., shared_anchors: _Optional[int] = ...) -> None: ...

class EncodeTextRequest(_message.Message):
    __slots__ = ("texts", "model_preset")
    TEXTS_FIELD_NUMBER: _ClassVar[int]
    MODEL_PRESET_FIELD_NUMBER: _ClassVar[int]
    texts: _containers.RepeatedScalarFieldContainer[str]
    model_preset: str
    def __init__(self, texts: _Optional[_Iterable[str]] = ..., model_preset: _Optional[str] = ...) -> None: ...

class EncodeTextResponse(_message.Message):
    __slots__ = ("vectors", "dimension", "processing_time_ms")
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    vectors: _containers.RepeatedScalarFieldContainer[bytes]
    dimension: int
    processing_time_ms: float
    def __init__(self, vectors: _Optional[_Iterable[bytes]] = ..., dimension: _Optional[int] = ..., processing_time_ms: _Optional[float] = ...) -> None: ...

class EvaluateContentRequest(_message.Message):
    __slots__ = ("content_id", "content_type", "text", "vector", "reaction_summary", "marker_credits")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    REACTION_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    MARKER_CREDITS_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    content_type: _common_pb2.ContentSource
    text: str
    vector: bytes
    reaction_summary: _common_pb2.ReactionSummary
    marker_credits: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, content_id: _Optional[str] = ..., content_type: _Optional[_Union[_common_pb2.ContentSource, str]] = ..., text: _Optional[str] = ..., vector: _Optional[bytes] = ..., reaction_summary: _Optional[_Union[_common_pb2.ReactionSummary, _Mapping]] = ..., marker_credits: _Optional[_Iterable[float]] = ...) -> None: ...

class EvaluateContentResponse(_message.Message):
    __slots__ = ("evaluated", "decision")
    EVALUATED_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    evaluated: bool
    decision: _common_pb2.GovernanceDecision
    def __init__(self, evaluated: bool = ..., decision: _Optional[_Union[_common_pb2.GovernanceDecision, _Mapping]] = ...) -> None: ...

class CheckMarkCredibilityRequest(_message.Message):
    __slots__ = ("marker_token_hash",)
    MARKER_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    marker_token_hash: str
    def __init__(self, marker_token_hash: _Optional[str] = ...) -> None: ...

class CheckMarkCredibilityResponse(_message.Message):
    __slots__ = ("credit_score", "total_marks", "accuracy_rate", "is_suspicious")
    CREDIT_SCORE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MARKS_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_RATE_FIELD_NUMBER: _ClassVar[int]
    IS_SUSPICIOUS_FIELD_NUMBER: _ClassVar[int]
    credit_score: float
    total_marks: int
    accuracy_rate: float
    is_suspicious: bool
    def __init__(self, credit_score: _Optional[float] = ..., total_marks: _Optional[int] = ..., accuracy_rate: _Optional[float] = ..., is_suspicious: bool = ...) -> None: ...

class DetectAnomalyRequest(_message.Message):
    __slots__ = ("anchor_id", "mark_timestamps", "marker_ids", "reactions_by_type")
    class ReactionsByTypeEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    MARK_TIMESTAMPS_FIELD_NUMBER: _ClassVar[int]
    MARKER_IDS_FIELD_NUMBER: _ClassVar[int]
    REACTIONS_BY_TYPE_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    mark_timestamps: _containers.RepeatedScalarFieldContainer[float]
    marker_ids: _containers.RepeatedScalarFieldContainer[str]
    reactions_by_type: _containers.ScalarMap[str, int]
    def __init__(self, anchor_id: _Optional[str] = ..., mark_timestamps: _Optional[_Iterable[float]] = ..., marker_ids: _Optional[_Iterable[str]] = ..., reactions_by_type: _Optional[_Mapping[str, int]] = ...) -> None: ...

class DetectAnomalyResponse(_message.Message):
    __slots__ = ("anomaly_detected", "anomalies")
    ANOMALY_DETECTED_FIELD_NUMBER: _ClassVar[int]
    ANOMALIES_FIELD_NUMBER: _ClassVar[int]
    anomaly_detected: bool
    anomalies: _containers.RepeatedCompositeFieldContainer[AnomalyReport]
    def __init__(self, anomaly_detected: bool = ..., anomalies: _Optional[_Iterable[_Union[AnomalyReport, _Mapping]]] = ...) -> None: ...

class AnomalyReport(_message.Message):
    __slots__ = ("anomaly_type", "description", "severity", "actions")
    ANOMALY_TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    anomaly_type: str
    description: str
    severity: float
    actions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, anomaly_type: _Optional[str] = ..., description: _Optional[str] = ..., severity: _Optional[float] = ..., actions: _Optional[_Iterable[str]] = ...) -> None: ...

class UpdateMarkerCreditRequest(_message.Message):
    __slots__ = ("updates",)
    UPDATES_FIELD_NUMBER: _ClassVar[int]
    updates: _containers.RepeatedCompositeFieldContainer[MarkerCreditUpdate]
    def __init__(self, updates: _Optional[_Iterable[_Union[MarkerCreditUpdate, _Mapping]]] = ...) -> None: ...

class MarkerCreditUpdate(_message.Message):
    __slots__ = ("marker_token_hash", "was_accurate", "timestamp")
    MARKER_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    WAS_ACCURATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    marker_token_hash: str
    was_accurate: bool
    timestamp: int
    def __init__(self, marker_token_hash: _Optional[str] = ..., was_accurate: bool = ..., timestamp: _Optional[int] = ...) -> None: ...

class UpdateMarkerCreditResponse(_message.Message):
    __slots__ = ("success", "updated_count")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    UPDATED_COUNT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    updated_count: int
    def __init__(self, success: bool = ..., updated_count: _Optional[int] = ...) -> None: ...

class GetMarkerCreditRequest(_message.Message):
    __slots__ = ("marker_token_hash", "current_timestamp")
    MARKER_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    CURRENT_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    marker_token_hash: str
    current_timestamp: int
    def __init__(self, marker_token_hash: _Optional[str] = ..., current_timestamp: _Optional[int] = ...) -> None: ...

class GetMarkerCreditResponse(_message.Message):
    __slots__ = ("credit_score", "total_marks", "time_decayed_credit")
    CREDIT_SCORE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MARKS_FIELD_NUMBER: _ClassVar[int]
    TIME_DECAYED_CREDIT_FIELD_NUMBER: _ClassVar[int]
    credit_score: float
    total_marks: int
    time_decayed_credit: float
    def __init__(self, credit_score: _Optional[float] = ..., total_marks: _Optional[int] = ..., time_decayed_credit: _Optional[float] = ...) -> None: ...

class GetMarkerHistoryRequest(_message.Message):
    __slots__ = ("marker_token_hash", "limit")
    MARKER_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    marker_token_hash: str
    limit: int
    def __init__(self, marker_token_hash: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class GetMarkerHistoryResponse(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[MarkerHistoryEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[MarkerHistoryEntry, _Mapping]]] = ...) -> None: ...

class MarkerHistoryEntry(_message.Message):
    __slots__ = ("content_id", "mark_type", "was_accurate", "timestamp")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    MARK_TYPE_FIELD_NUMBER: _ClassVar[int]
    WAS_ACCURATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    mark_type: _common_pb2.ReactionType
    was_accurate: bool
    timestamp: int
    def __init__(self, content_id: _Optional[str] = ..., mark_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., was_accurate: bool = ..., timestamp: _Optional[int] = ...) -> None: ...

class UpdateTrustLevelRequest(_message.Message):
    __slots__ = ("user_a_id", "user_b_id", "new_score_a_to_b", "new_score_b_to_a", "topic_diversity", "current_timestamp")
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_SCORE_A_TO_B_FIELD_NUMBER: _ClassVar[int]
    NEW_SCORE_B_TO_A_FIELD_NUMBER: _ClassVar[int]
    TOPIC_DIVERSITY_FIELD_NUMBER: _ClassVar[int]
    CURRENT_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    user_a_id: str
    user_b_id: str
    new_score_a_to_b: float
    new_score_b_to_a: float
    topic_diversity: int
    current_timestamp: int
    def __init__(self, user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ..., new_score_a_to_b: _Optional[float] = ..., new_score_b_to_a: _Optional[float] = ..., topic_diversity: _Optional[int] = ..., current_timestamp: _Optional[int] = ...) -> None: ...

class UpdateTrustLevelResponse(_message.Message):
    __slots__ = ("updated", "old_level", "new_level", "confidant_eligible")
    UPDATED_FIELD_NUMBER: _ClassVar[int]
    OLD_LEVEL_FIELD_NUMBER: _ClassVar[int]
    NEW_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CONFIDANT_ELIGIBLE_FIELD_NUMBER: _ClassVar[int]
    updated: bool
    old_level: _common_pb2.TrustLevel
    new_level: _common_pb2.TrustLevel
    confidant_eligible: bool
    def __init__(self, updated: bool = ..., old_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., new_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., confidant_eligible: bool = ...) -> None: ...

class GenerateAnonymousIdentityRequest(_message.Message):
    __slots__ = ("internal_token_hash", "anchor_id")
    INTERNAL_TOKEN_HASH_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    internal_token_hash: str
    anchor_id: str
    def __init__(self, internal_token_hash: _Optional[str] = ..., anchor_id: _Optional[str] = ...) -> None: ...

class GenerateAnonymousIdentityResponse(_message.Message):
    __slots__ = ("identity",)
    IDENTITY_FIELD_NUMBER: _ClassVar[int]
    identity: _common_pb2.AnonymousIdentity
    def __init__(self, identity: _Optional[_Union[_common_pb2.AnonymousIdentity, _Mapping]] = ...) -> None: ...

class CheckConfidantEligibilityRequest(_message.Message):
    __slots__ = ("user_a_id", "user_b_id", "current_timestamp")
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    user_a_id: str
    user_b_id: str
    current_timestamp: int
    def __init__(self, user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ..., current_timestamp: _Optional[int] = ...) -> None: ...

class CheckConfidantEligibilityResponse(_message.Message):
    __slots__ = ("eligible", "score_met", "time_met", "days_since_first")
    ELIGIBLE_FIELD_NUMBER: _ClassVar[int]
    SCORE_MET_FIELD_NUMBER: _ClassVar[int]
    TIME_MET_FIELD_NUMBER: _ClassVar[int]
    DAYS_SINCE_FIRST_FIELD_NUMBER: _ClassVar[int]
    eligible: bool
    score_met: bool
    time_met: bool
    days_since_first: int
    def __init__(self, eligible: bool = ..., score_met: bool = ..., time_met: bool = ..., days_since_first: _Optional[int] = ...) -> None: ...

class ContextStateRequest(_message.Message):
    __slots__ = ("user_id", "scene_type", "mood_hint", "attention_level", "active_device", "timestamp")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCENE_TYPE_FIELD_NUMBER: _ClassVar[int]
    MOOD_HINT_FIELD_NUMBER: _ClassVar[int]
    ATTENTION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_DEVICE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    scene_type: str
    mood_hint: str
    attention_level: str
    active_device: _common_pb2.DeviceType
    timestamp: int
    def __init__(self, user_id: _Optional[str] = ..., scene_type: _Optional[str] = ..., mood_hint: _Optional[str] = ..., attention_level: _Optional[str] = ..., active_device: _Optional[_Union[_common_pb2.DeviceType, str]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class ContextStateResponse(_message.Message):
    __slots__ = ("accepted",)
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    def __init__(self, accepted: bool = ...) -> None: ...

class ContextualWeightsRequest(_message.Message):
    __slots__ = ("user_id", "candidate_topics")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CANDIDATE_TOPICS_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    candidate_topics: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, user_id: _Optional[str] = ..., candidate_topics: _Optional[_Iterable[str]] = ...) -> None: ...

class ContextualWeightsResponse(_message.Message):
    __slots__ = ("topic_weights", "recommended_scene")
    class TopicWeightsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    TOPIC_WEIGHTS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDED_SCENE_FIELD_NUMBER: _ClassVar[int]
    topic_weights: _containers.ScalarMap[str, float]
    recommended_scene: str
    def __init__(self, topic_weights: _Optional[_Mapping[str, float]] = ..., recommended_scene: _Optional[str] = ...) -> None: ...
