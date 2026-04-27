from common import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AuthError(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AUTH_ERROR_UNSPECIFIED: _ClassVar[AuthError]
    INVALID_DEVICE: _ClassVar[AuthError]
    INVALID_CREDENTIALS: _ClassVar[AuthError]
    DEVICE_LIMIT_EXCEEDED: _ClassVar[AuthError]
    RATE_LIMITED: _ClassVar[AuthError]
    PHONE_NOT_VERIFIED: _ClassVar[AuthError]
AUTH_ERROR_UNSPECIFIED: AuthError
INVALID_DEVICE: AuthError
INVALID_CREDENTIALS: AuthError
DEVICE_LIMIT_EXCEEDED: AuthError
RATE_LIMITED: AuthError
PHONE_NOT_VERIFIED: AuthError

class DeviceAuthRequest(_message.Message):
    __slots__ = ("device", "phone_number_hash", "verification_code", "existing_token")
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    PHONE_NUMBER_HASH_FIELD_NUMBER: _ClassVar[int]
    VERIFICATION_CODE_FIELD_NUMBER: _ClassVar[int]
    EXISTING_TOKEN_FIELD_NUMBER: _ClassVar[int]
    device: _common_pb2.DeviceInfo
    phone_number_hash: str
    verification_code: str
    existing_token: str
    def __init__(self, device: _Optional[_Union[_common_pb2.DeviceInfo, _Mapping]] = ..., phone_number_hash: _Optional[str] = ..., verification_code: _Optional[str] = ..., existing_token: _Optional[str] = ...) -> None: ...

class DeviceAuthResponse(_message.Message):
    __slots__ = ("success", "access_token", "refresh_token", "expires_at", "user_id", "error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    access_token: str
    refresh_token: str
    expires_at: int
    user_id: str
    error: AuthError
    def __init__(self, success: bool = ..., access_token: _Optional[str] = ..., refresh_token: _Optional[str] = ..., expires_at: _Optional[int] = ..., user_id: _Optional[str] = ..., error: _Optional[_Union[AuthError, str]] = ...) -> None: ...

class RefreshTokenRequest(_message.Message):
    __slots__ = ("refresh_token", "device")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    device: _common_pb2.DeviceInfo
    def __init__(self, refresh_token: _Optional[str] = ..., device: _Optional[_Union[_common_pb2.DeviceInfo, _Mapping]] = ...) -> None: ...

class RefreshTokenResponse(_message.Message):
    __slots__ = ("success", "access_token", "expires_at", "error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    access_token: str
    expires_at: int
    error: AuthError
    def __init__(self, success: bool = ..., access_token: _Optional[str] = ..., expires_at: _Optional[int] = ..., error: _Optional[_Union[AuthError, str]] = ...) -> None: ...

class LogoutRequest(_message.Message):
    __slots__ = ("access_token",)
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    access_token: str
    def __init__(self, access_token: _Optional[str] = ...) -> None: ...

class LogoutResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class ListAnchorsRequest(_message.Message):
    __slots__ = ("pagination", "topic_filter", "context_hint")
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    TOPIC_FILTER_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_HINT_FIELD_NUMBER: _ClassVar[int]
    pagination: _common_pb2.Pagination
    topic_filter: _containers.RepeatedScalarFieldContainer[str]
    context_hint: str
    def __init__(self, pagination: _Optional[_Union[_common_pb2.Pagination, _Mapping]] = ..., topic_filter: _Optional[_Iterable[str]] = ..., context_hint: _Optional[str] = ...) -> None: ...

class ListAnchorsResponse(_message.Message):
    __slots__ = ("anchors", "pagination")
    ANCHORS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    anchors: _containers.RepeatedCompositeFieldContainer[_common_pb2.AnchorSummary]
    pagination: _common_pb2.PaginatedResponse
    def __init__(self, anchors: _Optional[_Iterable[_Union[_common_pb2.AnchorSummary, _Mapping]]] = ..., pagination: _Optional[_Union[_common_pb2.PaginatedResponse, _Mapping]] = ...) -> None: ...

class GetAnchorRequest(_message.Message):
    __slots__ = ("anchor_id",)
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    def __init__(self, anchor_id: _Optional[str] = ...) -> None: ...

class GetAnchorResponse(_message.Message):
    __slots__ = ("found", "anchor", "my_reaction_summary")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_FIELD_NUMBER: _ClassVar[int]
    MY_REACTION_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    found: bool
    anchor: _common_pb2.Anchor
    my_reaction_summary: _common_pb2.ReactionSummary
    def __init__(self, found: bool = ..., anchor: _Optional[_Union[_common_pb2.Anchor, _Mapping]] = ..., my_reaction_summary: _Optional[_Union[_common_pb2.ReactionSummary, _Mapping]] = ...) -> None: ...

class GetReplayAnchorsRequest(_message.Message):
    __slots__ = ("top_k",)
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    top_k: int
    def __init__(self, top_k: _Optional[int] = ...) -> None: ...

class GetReplayAnchorsResponse(_message.Message):
    __slots__ = ("anchors",)
    ANCHORS_FIELD_NUMBER: _ClassVar[int]
    anchors: _containers.RepeatedCompositeFieldContainer[ReplayAnchor]
    def __init__(self, anchors: _Optional[_Iterable[_Union[ReplayAnchor, _Mapping]]] = ...) -> None: ...

class ReplayAnchor(_message.Message):
    __slots__ = ("summary", "trigger_type", "trigger_score", "group_memory")
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_TYPE_FIELD_NUMBER: _ClassVar[int]
    TRIGGER_SCORE_FIELD_NUMBER: _ClassVar[int]
    GROUP_MEMORY_FIELD_NUMBER: _ClassVar[int]
    summary: _common_pb2.AnchorSummary
    trigger_type: str
    trigger_score: float
    group_memory: _common_pb2.GroupMemory
    def __init__(self, summary: _Optional[_Union[_common_pb2.AnchorSummary, _Mapping]] = ..., trigger_type: _Optional[str] = ..., trigger_score: _Optional[float] = ..., group_memory: _Optional[_Union[_common_pb2.GroupMemory, _Mapping]] = ...) -> None: ...

class ImportAnchorRequest(_message.Message):
    __slots__ = ("content_text", "source_url", "content_image")
    CONTENT_TEXT_FIELD_NUMBER: _ClassVar[int]
    SOURCE_URL_FIELD_NUMBER: _ClassVar[int]
    CONTENT_IMAGE_FIELD_NUMBER: _ClassVar[int]
    content_text: str
    source_url: str
    content_image: bytes
    def __init__(self, content_text: _Optional[str] = ..., source_url: _Optional[str] = ..., content_image: _Optional[bytes] = ...) -> None: ...

class ImportAnchorResponse(_message.Message):
    __slots__ = ("accepted", "anchor_id", "message")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    anchor_id: str
    message: str
    def __init__(self, accepted: bool = ..., anchor_id: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class GetReactionSummaryRequest(_message.Message):
    __slots__ = ("anchor_id",)
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    def __init__(self, anchor_id: _Optional[str] = ...) -> None: ...

class GetReactionSummaryResponse(_message.Message):
    __slots__ = ("summary",)
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    summary: _common_pb2.ReactionSummary
    def __init__(self, summary: _Optional[_Union[_common_pb2.ReactionSummary, _Mapping]] = ...) -> None: ...

class SubmitReactionRequest(_message.Message):
    __slots__ = ("anchor_id", "reaction_type", "emotion_word", "opinion_text")
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    REACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMOTION_WORD_FIELD_NUMBER: _ClassVar[int]
    OPINION_TEXT_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    reaction_type: _common_pb2.ReactionType
    emotion_word: _common_pb2.EmotionWord
    opinion_text: str
    def __init__(self, anchor_id: _Optional[str] = ..., reaction_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., emotion_word: _Optional[_Union[_common_pb2.EmotionWord, str]] = ..., opinion_text: _Optional[str] = ...) -> None: ...

class SubmitReactionResponse(_message.Message):
    __slots__ = ("success", "reaction_id", "resonance_value", "anchor_summary", "notifications")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    REACTION_ID_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_VALUE_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    reaction_id: str
    resonance_value: float
    anchor_summary: _common_pb2.ReactionSummary
    notifications: _containers.RepeatedCompositeFieldContainer[ResonanceNotification]
    def __init__(self, success: bool = ..., reaction_id: _Optional[str] = ..., resonance_value: _Optional[float] = ..., anchor_summary: _Optional[_Union[_common_pb2.ReactionSummary, _Mapping]] = ..., notifications: _Optional[_Iterable[_Union[ResonanceNotification, _Mapping]]] = ...) -> None: ...

class ResonanceNotification(_message.Message):
    __slots__ = ("type", "message", "related_user_anonymous_name")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    RELATED_USER_ANONYMOUS_NAME_FIELD_NUMBER: _ClassVar[int]
    type: str
    message: str
    related_user_anonymous_name: str
    def __init__(self, type: _Optional[str] = ..., message: _Optional[str] = ..., related_user_anonymous_name: _Optional[str] = ...) -> None: ...

class ListReactionsRequest(_message.Message):
    __slots__ = ("anchor_id", "filter_type", "pagination")
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    FILTER_TYPE_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    filter_type: _common_pb2.ReactionType
    pagination: _common_pb2.Pagination
    def __init__(self, anchor_id: _Optional[str] = ..., filter_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., pagination: _Optional[_Union[_common_pb2.Pagination, _Mapping]] = ...) -> None: ...

class ListReactionsResponse(_message.Message):
    __slots__ = ("reactions", "pagination")
    REACTIONS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    reactions: _containers.RepeatedCompositeFieldContainer[ReactionView]
    pagination: _common_pb2.PaginatedResponse
    def __init__(self, reactions: _Optional[_Iterable[_Union[ReactionView, _Mapping]]] = ..., pagination: _Optional[_Union[_common_pb2.PaginatedResponse, _Mapping]] = ...) -> None: ...

class ReactionView(_message.Message):
    __slots__ = ("reaction_id", "author", "reaction_type", "emotion_word", "opinion_text", "has_resonance_trace", "trace_hint", "created_at")
    REACTION_ID_FIELD_NUMBER: _ClassVar[int]
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    REACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMOTION_WORD_FIELD_NUMBER: _ClassVar[int]
    OPINION_TEXT_FIELD_NUMBER: _ClassVar[int]
    HAS_RESONANCE_TRACE_FIELD_NUMBER: _ClassVar[int]
    TRACE_HINT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    reaction_id: str
    author: _common_pb2.AnonymousIdentity
    reaction_type: _common_pb2.ReactionType
    emotion_word: _common_pb2.EmotionWord
    opinion_text: str
    has_resonance_trace: bool
    trace_hint: str
    created_at: int
    def __init__(self, reaction_id: _Optional[str] = ..., author: _Optional[_Union[_common_pb2.AnonymousIdentity, _Mapping]] = ..., reaction_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., emotion_word: _Optional[_Union[_common_pb2.EmotionWord, str]] = ..., opinion_text: _Optional[str] = ..., has_resonance_trace: bool = ..., trace_hint: _Optional[str] = ..., created_at: _Optional[int] = ...) -> None: ...

class GetResonanceTracesRequest(_message.Message):
    __slots__ = ("pagination",)
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    pagination: _common_pb2.Pagination
    def __init__(self, pagination: _Optional[_Union[_common_pb2.Pagination, _Mapping]] = ...) -> None: ...

class GetResonanceTracesResponse(_message.Message):
    __slots__ = ("traces", "pagination")
    TRACES_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    traces: _containers.RepeatedCompositeFieldContainer[ResonanceTrace]
    pagination: _common_pb2.PaginatedResponse
    def __init__(self, traces: _Optional[_Iterable[_Union[ResonanceTrace, _Mapping]]] = ..., pagination: _Optional[_Union[_common_pb2.PaginatedResponse, _Mapping]] = ...) -> None: ...

class ResonanceTrace(_message.Message):
    __slots__ = ("trace_id", "other_user", "relationship_score", "shared_anchors", "shared_topics", "recent_anchor_titles", "trust_level")
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    OTHER_USER_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    SHARED_ANCHORS_FIELD_NUMBER: _ClassVar[int]
    SHARED_TOPICS_FIELD_NUMBER: _ClassVar[int]
    RECENT_ANCHOR_TITLES_FIELD_NUMBER: _ClassVar[int]
    TRUST_LEVEL_FIELD_NUMBER: _ClassVar[int]
    trace_id: str
    other_user: _common_pb2.AnonymousIdentity
    relationship_score: float
    shared_anchors: int
    shared_topics: int
    recent_anchor_titles: _containers.RepeatedScalarFieldContainer[str]
    trust_level: _common_pb2.TrustLevel
    def __init__(self, trace_id: _Optional[str] = ..., other_user: _Optional[_Union[_common_pb2.AnonymousIdentity, _Mapping]] = ..., relationship_score: _Optional[float] = ..., shared_anchors: _Optional[int] = ..., shared_topics: _Optional[int] = ..., recent_anchor_titles: _Optional[_Iterable[str]] = ..., trust_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ...) -> None: ...

class GetProfileRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetProfileResponse(_message.Message):
    __slots__ = ("user_id", "credit_score", "marker_credit", "total_reactions", "total_anchors_engaged", "confidant_count", "created_at")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CREDIT_SCORE_FIELD_NUMBER: _ClassVar[int]
    MARKER_CREDIT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_REACTIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ANCHORS_ENGAGED_FIELD_NUMBER: _ClassVar[int]
    CONFIDANT_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    credit_score: float
    marker_credit: float
    total_reactions: int
    total_anchors_engaged: int
    confidant_count: int
    created_at: int
    def __init__(self, user_id: _Optional[str] = ..., credit_score: _Optional[float] = ..., marker_credit: _Optional[float] = ..., total_reactions: _Optional[int] = ..., total_anchors_engaged: _Optional[int] = ..., confidant_count: _Optional[int] = ..., created_at: _Optional[int] = ...) -> None: ...

class ListRelationshipsRequest(_message.Message):
    __slots__ = ("min_level", "pagination")
    MIN_LEVEL_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    min_level: _common_pb2.TrustLevel
    pagination: _common_pb2.Pagination
    def __init__(self, min_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., pagination: _Optional[_Union[_common_pb2.Pagination, _Mapping]] = ...) -> None: ...

class ListRelationshipsResponse(_message.Message):
    __slots__ = ("relationships", "pagination")
    RELATIONSHIPS_FIELD_NUMBER: _ClassVar[int]
    PAGINATION_FIELD_NUMBER: _ClassVar[int]
    relationships: _containers.RepeatedCompositeFieldContainer[RelationshipView]
    pagination: _common_pb2.PaginatedResponse
    def __init__(self, relationships: _Optional[_Iterable[_Union[RelationshipView, _Mapping]]] = ..., pagination: _Optional[_Union[_common_pb2.PaginatedResponse, _Mapping]] = ...) -> None: ...

class RelationshipView(_message.Message):
    __slots__ = ("other_user", "relationship_score", "topic_diversity", "trust_level", "is_confidant", "last_resonance_at")
    OTHER_USER_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    TOPIC_DIVERSITY_FIELD_NUMBER: _ClassVar[int]
    TRUST_LEVEL_FIELD_NUMBER: _ClassVar[int]
    IS_CONFIDANT_FIELD_NUMBER: _ClassVar[int]
    LAST_RESONANCE_AT_FIELD_NUMBER: _ClassVar[int]
    other_user: _common_pb2.AnonymousIdentity
    relationship_score: float
    topic_diversity: int
    trust_level: _common_pb2.TrustLevel
    is_confidant: bool
    last_resonance_at: int
    def __init__(self, other_user: _Optional[_Union[_common_pb2.AnonymousIdentity, _Mapping]] = ..., relationship_score: _Optional[float] = ..., topic_diversity: _Optional[int] = ..., trust_level: _Optional[_Union[_common_pb2.TrustLevel, str]] = ..., is_confidant: bool = ..., last_resonance_at: _Optional[int] = ...) -> None: ...

class ExpressConfidantIntentRequest(_message.Message):
    __slots__ = ("target_user_internal_hash",)
    TARGET_USER_INTERNAL_HASH_FIELD_NUMBER: _ClassVar[int]
    target_user_internal_hash: str
    def __init__(self, target_user_internal_hash: _Optional[str] = ...) -> None: ...

class ExpressConfidantIntentResponse(_message.Message):
    __slots__ = ("success", "matched", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MATCHED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    matched: bool
    message: str
    def __init__(self, success: bool = ..., matched: bool = ..., message: _Optional[str] = ...) -> None: ...

class ListConfidantsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListConfidantsResponse(_message.Message):
    __slots__ = ("confidants",)
    CONFIDANTS_FIELD_NUMBER: _ClassVar[int]
    confidants: _containers.RepeatedCompositeFieldContainer[ConfidantView]
    def __init__(self, confidants: _Optional[_Iterable[_Union[ConfidantView, _Mapping]]] = ...) -> None: ...

class ConfidantView(_message.Message):
    __slots__ = ("confidant_id", "fixed_name", "fixed_avatar_url", "relationship_score", "established_at", "last_interaction_at")
    CONFIDANT_ID_FIELD_NUMBER: _ClassVar[int]
    FIXED_NAME_FIELD_NUMBER: _ClassVar[int]
    FIXED_AVATAR_URL_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIP_SCORE_FIELD_NUMBER: _ClassVar[int]
    ESTABLISHED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_INTERACTION_AT_FIELD_NUMBER: _ClassVar[int]
    confidant_id: str
    fixed_name: str
    fixed_avatar_url: str
    relationship_score: float
    established_at: int
    last_interaction_at: int
    def __init__(self, confidant_id: _Optional[str] = ..., fixed_name: _Optional[str] = ..., fixed_avatar_url: _Optional[str] = ..., relationship_score: _Optional[float] = ..., established_at: _Optional[int] = ..., last_interaction_at: _Optional[int] = ...) -> None: ...

class SubmitContextStateRequest(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: ContextState
    def __init__(self, state: _Optional[_Union[ContextState, _Mapping]] = ...) -> None: ...

class ContextState(_message.Message):
    __slots__ = ("scene_type", "mood_hint", "attention_level", "active_device", "timestamp")
    SCENE_TYPE_FIELD_NUMBER: _ClassVar[int]
    MOOD_HINT_FIELD_NUMBER: _ClassVar[int]
    ATTENTION_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_DEVICE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    scene_type: str
    mood_hint: str
    attention_level: str
    active_device: _common_pb2.DeviceType
    timestamp: int
    def __init__(self, scene_type: _Optional[str] = ..., mood_hint: _Optional[str] = ..., attention_level: _Optional[str] = ..., active_device: _Optional[_Union[_common_pb2.DeviceType, str]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class SubmitContextStateResponse(_message.Message):
    __slots__ = ("accepted",)
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    def __init__(self, accepted: bool = ...) -> None: ...

class GetContextualHintRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetContextualHintResponse(_message.Message):
    __slots__ = ("recommended_scene", "mood_suggestion", "topic_hints")
    RECOMMENDED_SCENE_FIELD_NUMBER: _ClassVar[int]
    MOOD_SUGGESTION_FIELD_NUMBER: _ClassVar[int]
    TOPIC_HINTS_FIELD_NUMBER: _ClassVar[int]
    recommended_scene: str
    mood_suggestion: str
    topic_hints: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, recommended_scene: _Optional[str] = ..., mood_suggestion: _Optional[str] = ..., topic_hints: _Optional[_Iterable[str]] = ...) -> None: ...

class ReportContentRequest(_message.Message):
    __slots__ = ("content_id", "content_type", "report_type", "reason")
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    REPORT_TYPE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    content_type: _common_pb2.ContentSource
    report_type: _common_pb2.ReactionType
    reason: str
    def __init__(self, content_id: _Optional[str] = ..., content_type: _Optional[_Union[_common_pb2.ContentSource, str]] = ..., report_type: _Optional[_Union[_common_pb2.ReactionType, str]] = ..., reason: _Optional[str] = ...) -> None: ...

class ReportContentResponse(_message.Message):
    __slots__ = ("accepted", "message")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    message: str
    def __init__(self, accepted: bool = ..., message: _Optional[str] = ...) -> None: ...

class GetContentStatusRequest(_message.Message):
    __slots__ = ("content_id",)
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    content_id: str
    def __init__(self, content_id: _Optional[str] = ...) -> None: ...

class GetContentStatusResponse(_message.Message):
    __slots__ = ("level", "status_message", "can_appeal")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    STATUS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CAN_APPEAL_FIELD_NUMBER: _ClassVar[int]
    level: _common_pb2.GovernanceLevel
    status_message: str
    can_appeal: bool
    def __init__(self, level: _Optional[_Union[_common_pb2.GovernanceLevel, str]] = ..., status_message: _Optional[str] = ..., can_appeal: bool = ...) -> None: ...

class AppealDecisionRequest(_message.Message):
    __slots__ = ("decision_id", "appeal_reason")
    DECISION_ID_FIELD_NUMBER: _ClassVar[int]
    APPEAL_REASON_FIELD_NUMBER: _ClassVar[int]
    decision_id: str
    appeal_reason: str
    def __init__(self, decision_id: _Optional[str] = ..., appeal_reason: _Optional[str] = ...) -> None: ...

class AppealDecisionResponse(_message.Message):
    __slots__ = ("accepted", "message")
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    accepted: bool
    message: str
    def __init__(self, accepted: bool = ..., message: _Optional[str] = ...) -> None: ...
