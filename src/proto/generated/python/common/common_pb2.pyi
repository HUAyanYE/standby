from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ReactionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    REACTION_TYPE_UNSPECIFIED: _ClassVar[ReactionType]
    RESONANCE: _ClassVar[ReactionType]
    NEUTRAL: _ClassVar[ReactionType]
    OPPOSITION: _ClassVar[ReactionType]
    UNEXPERIENCED: _ClassVar[ReactionType]
    HARMFUL: _ClassVar[ReactionType]

class EmotionWord(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EMOTION_WORD_UNSPECIFIED: _ClassVar[EmotionWord]
    EMPATHY: _ClassVar[EmotionWord]
    TRIGGER: _ClassVar[EmotionWord]
    INSIGHT: _ClassVar[EmotionWord]
    SHOCK: _ClassVar[EmotionWord]

class TrustLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TRUST_LEVEL_UNSPECIFIED: _ClassVar[TrustLevel]
    L0_BROWSE: _ClassVar[TrustLevel]
    L1_TRACE_VISIBLE: _ClassVar[TrustLevel]
    L2_OPINION_REPLY: _ClassVar[TrustLevel]
    L3_ASYNC_MESSAGE: _ClassVar[TrustLevel]
    L4_REALTIME_CHAT: _ClassVar[TrustLevel]
    L5_GROUP_CHAT: _ClassVar[TrustLevel]

class GovernanceLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    GOVERNANCE_LEVEL_UNSPECIFIED: _ClassVar[GovernanceLevel]
    GOV_NORMAL: _ClassVar[GovernanceLevel]
    GOV_OBSERVING: _ClassVar[GovernanceLevel]
    GOV_DEMOTED: _ClassVar[GovernanceLevel]
    GOV_SUSPENDED: _ClassVar[GovernanceLevel]
    GOV_REMOVED: _ClassVar[GovernanceLevel]
    GOV_CONFLICT: _ClassVar[GovernanceLevel]

class AnchorType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ANCHOR_TYPE_UNSPECIFIED: _ClassVar[AnchorType]
    PLATFORM_INITIAL: _ClassVar[AnchorType]
    USER_CONTENT: _ClassVar[AnchorType]
    AI_AGGREGATED: _ClassVar[AnchorType]

class DeviceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_TYPE_UNSPECIFIED: _ClassVar[DeviceType]
    PHONE: _ClassVar[DeviceType]
    TABLET: _ClassVar[DeviceType]
    PC: _ClassVar[DeviceType]
    VEHICLE: _ClassVar[DeviceType]

class ContentSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTENT_SOURCE_UNSPECIFIED: _ClassVar[ContentSource]
    ANCHOR: _ClassVar[ContentSource]
    OPINION: _ClassVar[ContentSource]
    REPLAY: _ClassVar[ContentSource]
REACTION_TYPE_UNSPECIFIED: ReactionType
RESONANCE: ReactionType
NEUTRAL: ReactionType
OPPOSITION: ReactionType
UNEXPERIENCED: ReactionType
HARMFUL: ReactionType
EMOTION_WORD_UNSPECIFIED: EmotionWord
EMPATHY: EmotionWord
TRIGGER: EmotionWord
INSIGHT: EmotionWord
SHOCK: EmotionWord
TRUST_LEVEL_UNSPECIFIED: TrustLevel
L0_BROWSE: TrustLevel
L1_TRACE_VISIBLE: TrustLevel
L2_OPINION_REPLY: TrustLevel
L3_ASYNC_MESSAGE: TrustLevel
L4_REALTIME_CHAT: TrustLevel
L5_GROUP_CHAT: TrustLevel
GOVERNANCE_LEVEL_UNSPECIFIED: GovernanceLevel
GOV_NORMAL: GovernanceLevel
GOV_OBSERVING: GovernanceLevel
GOV_DEMOTED: GovernanceLevel
GOV_SUSPENDED: GovernanceLevel
GOV_REMOVED: GovernanceLevel
GOV_CONFLICT: GovernanceLevel
ANCHOR_TYPE_UNSPECIFIED: AnchorType
PLATFORM_INITIAL: AnchorType
USER_CONTENT: AnchorType
AI_AGGREGATED: AnchorType
DEVICE_TYPE_UNSPECIFIED: DeviceType
PHONE: DeviceType
TABLET: DeviceType
PC: DeviceType
VEHICLE: DeviceType
CONTENT_SOURCE_UNSPECIFIED: ContentSource
ANCHOR: ContentSource
OPINION: ContentSource
REPLAY: ContentSource

class Pagination(_message.Message):
    __slots__ = ("page", "page_size", "cursor")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    page: int
    page_size: int
    cursor: str
    def __init__(self, page: _Optional[int] = ..., page_size: _Optional[int] = ..., cursor: _Optional[str] = ...) -> None: ...

class PaginatedResponse(_message.Message):
    __slots__ = ("total_count", "next_cursor", "has_more")
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    total_count: int
    next_cursor: str
    has_more: bool
    def __init__(self, total_count: _Optional[int] = ..., next_cursor: _Optional[str] = ..., has_more: bool = ...) -> None: ...

class TimeRange(_message.Message):
    __slots__ = ("start_ts", "end_ts")
    START_TS_FIELD_NUMBER: _ClassVar[int]
    END_TS_FIELD_NUMBER: _ClassVar[int]
    start_ts: int
    end_ts: int
    def __init__(self, start_ts: _Optional[int] = ..., end_ts: _Optional[int] = ...) -> None: ...

class AnchorSummary(_message.Message):
    __slots__ = ("anchor_id", "title", "anchor_type", "topics", "total_reactions", "created_at")
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    TITLE_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_REACTIONS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    title: str
    anchor_type: AnchorType
    topics: _containers.RepeatedScalarFieldContainer[str]
    total_reactions: int
    created_at: int
    def __init__(self, anchor_id: _Optional[str] = ..., title: _Optional[str] = ..., anchor_type: _Optional[_Union[AnchorType, str]] = ..., topics: _Optional[_Iterable[str]] = ..., total_reactions: _Optional[int] = ..., created_at: _Optional[int] = ...) -> None: ...

class Anchor(_message.Message):
    __slots__ = ("anchor_id", "text", "anchor_type", "topics", "source_attribution", "anchor_vector", "vector_dimension", "quality", "created_at", "updated_at")
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    TOPICS_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ATTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_VECTOR_FIELD_NUMBER: _ClassVar[int]
    VECTOR_DIMENSION_FIELD_NUMBER: _ClassVar[int]
    QUALITY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    text: str
    anchor_type: AnchorType
    topics: _containers.RepeatedScalarFieldContainer[str]
    source_attribution: str
    anchor_vector: bytes
    vector_dimension: int
    quality: AnchorQuality
    created_at: int
    updated_at: int
    def __init__(self, anchor_id: _Optional[str] = ..., text: _Optional[str] = ..., anchor_type: _Optional[_Union[AnchorType, str]] = ..., topics: _Optional[_Iterable[str]] = ..., source_attribution: _Optional[str] = ..., anchor_vector: _Optional[bytes] = ..., vector_dimension: _Optional[int] = ..., quality: _Optional[_Union[AnchorQuality, _Mapping]] = ..., created_at: _Optional[int] = ..., updated_at: _Optional[int] = ...) -> None: ...

class AnchorQuality(_message.Message):
    __slots__ = ("completeness", "specificity", "authenticity", "thought_space", "overall")
    COMPLETENESS_FIELD_NUMBER: _ClassVar[int]
    SPECIFICITY_FIELD_NUMBER: _ClassVar[int]
    AUTHENTICITY_FIELD_NUMBER: _ClassVar[int]
    THOUGHT_SPACE_FIELD_NUMBER: _ClassVar[int]
    OVERALL_FIELD_NUMBER: _ClassVar[int]
    completeness: float
    specificity: float
    authenticity: float
    thought_space: float
    overall: float
    def __init__(self, completeness: _Optional[float] = ..., specificity: _Optional[float] = ..., authenticity: _Optional[float] = ..., thought_space: _Optional[float] = ..., overall: _Optional[float] = ...) -> None: ...

class Reaction(_message.Message):
    __slots__ = ("reaction_id", "user_id", "anchor_id", "reaction_type", "emotion_word", "opinion_text", "opinion_vector", "resonance_value", "created_at")
    REACTION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    REACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    EMOTION_WORD_FIELD_NUMBER: _ClassVar[int]
    OPINION_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPINION_VECTOR_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_VALUE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    reaction_id: str
    user_id: str
    anchor_id: str
    reaction_type: ReactionType
    emotion_word: EmotionWord
    opinion_text: str
    opinion_vector: bytes
    resonance_value: float
    created_at: int
    def __init__(self, reaction_id: _Optional[str] = ..., user_id: _Optional[str] = ..., anchor_id: _Optional[str] = ..., reaction_type: _Optional[_Union[ReactionType, str]] = ..., emotion_word: _Optional[_Union[EmotionWord, str]] = ..., opinion_text: _Optional[str] = ..., opinion_vector: _Optional[bytes] = ..., resonance_value: _Optional[float] = ..., created_at: _Optional[int] = ...) -> None: ...

class ReactionSummary(_message.Message):
    __slots__ = ("anchor_id", "resonance_count", "neutral_count", "opposition_count", "unexperienced_count", "harmful_count", "total_count", "updated_at")
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    NEUTRAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    OPPOSITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    UNEXPERIENCED_COUNT_FIELD_NUMBER: _ClassVar[int]
    HARMFUL_COUNT_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    resonance_count: int
    neutral_count: int
    opposition_count: int
    unexperienced_count: int
    harmful_count: int
    total_count: int
    updated_at: int
    def __init__(self, anchor_id: _Optional[str] = ..., resonance_count: _Optional[int] = ..., neutral_count: _Optional[int] = ..., opposition_count: _Optional[int] = ..., unexperienced_count: _Optional[int] = ..., harmful_count: _Optional[int] = ..., total_count: _Optional[int] = ..., updated_at: _Optional[int] = ...) -> None: ...

class AnonymousIdentity(_message.Message):
    __slots__ = ("identity_id", "display_name", "avatar_seed", "anchor_id", "is_fixed", "fixed_name", "fixed_avatar_url")
    IDENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    AVATAR_SEED_FIELD_NUMBER: _ClassVar[int]
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    IS_FIXED_FIELD_NUMBER: _ClassVar[int]
    FIXED_NAME_FIELD_NUMBER: _ClassVar[int]
    FIXED_AVATAR_URL_FIELD_NUMBER: _ClassVar[int]
    identity_id: str
    display_name: str
    avatar_seed: str
    anchor_id: str
    is_fixed: bool
    fixed_name: str
    fixed_avatar_url: str
    def __init__(self, identity_id: _Optional[str] = ..., display_name: _Optional[str] = ..., avatar_seed: _Optional[str] = ..., anchor_id: _Optional[str] = ..., is_fixed: bool = ..., fixed_name: _Optional[str] = ..., fixed_avatar_url: _Optional[str] = ...) -> None: ...

class RelationshipState(_message.Message):
    __slots__ = ("user_a_id", "user_b_id", "score_a_to_b", "score_b_to_a", "topic_diversity", "trust_level", "is_confidant", "first_resonance_at", "last_resonance_at")
    USER_A_ID_FIELD_NUMBER: _ClassVar[int]
    USER_B_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_A_TO_B_FIELD_NUMBER: _ClassVar[int]
    SCORE_B_TO_A_FIELD_NUMBER: _ClassVar[int]
    TOPIC_DIVERSITY_FIELD_NUMBER: _ClassVar[int]
    TRUST_LEVEL_FIELD_NUMBER: _ClassVar[int]
    IS_CONFIDANT_FIELD_NUMBER: _ClassVar[int]
    FIRST_RESONANCE_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_RESONANCE_AT_FIELD_NUMBER: _ClassVar[int]
    user_a_id: str
    user_b_id: str
    score_a_to_b: float
    score_b_to_a: float
    topic_diversity: int
    trust_level: TrustLevel
    is_confidant: bool
    first_resonance_at: int
    last_resonance_at: int
    def __init__(self, user_a_id: _Optional[str] = ..., user_b_id: _Optional[str] = ..., score_a_to_b: _Optional[float] = ..., score_b_to_a: _Optional[float] = ..., topic_diversity: _Optional[int] = ..., trust_level: _Optional[_Union[TrustLevel, str]] = ..., is_confidant: bool = ..., first_resonance_at: _Optional[int] = ..., last_resonance_at: _Optional[int] = ...) -> None: ...

class GroupMemory(_message.Message):
    __slots__ = ("anchor_id", "total_reactions", "resonance_count", "opposition_count", "opinions", "time_trend", "user_own")
    ANCHOR_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_REACTIONS_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    OPPOSITION_COUNT_FIELD_NUMBER: _ClassVar[int]
    OPINIONS_FIELD_NUMBER: _ClassVar[int]
    TIME_TREND_FIELD_NUMBER: _ClassVar[int]
    USER_OWN_FIELD_NUMBER: _ClassVar[int]
    anchor_id: str
    total_reactions: int
    resonance_count: int
    opposition_count: int
    opinions: _containers.RepeatedCompositeFieldContainer[RepresentativeOpinion]
    time_trend: TimeTrend
    user_own: UserOwnHistory
    def __init__(self, anchor_id: _Optional[str] = ..., total_reactions: _Optional[int] = ..., resonance_count: _Optional[int] = ..., opposition_count: _Optional[int] = ..., opinions: _Optional[_Iterable[_Union[RepresentativeOpinion, _Mapping]]] = ..., time_trend: _Optional[_Union[TimeTrend, _Mapping]] = ..., user_own: _Optional[_Union[UserOwnHistory, _Mapping]] = ...) -> None: ...

class RepresentativeOpinion(_message.Message):
    __slots__ = ("text", "resonance_count", "created_at")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    RESONANCE_COUNT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    text: str
    resonance_count: int
    created_at: int
    def __init__(self, text: _Optional[str] = ..., resonance_count: _Optional[int] = ..., created_at: _Optional[int] = ...) -> None: ...

class TimeTrend(_message.Message):
    __slots__ = ("trend", "growth_rate", "latest_intensity")
    TREND_FIELD_NUMBER: _ClassVar[int]
    GROWTH_RATE_FIELD_NUMBER: _ClassVar[int]
    LATEST_INTENSITY_FIELD_NUMBER: _ClassVar[int]
    trend: str
    growth_rate: float
    latest_intensity: float
    def __init__(self, trend: _Optional[str] = ..., growth_rate: _Optional[float] = ..., latest_intensity: _Optional[float] = ...) -> None: ...

class UserOwnHistory(_message.Message):
    __slots__ = ("reaction_count", "last_reaction_type", "has_opinion")
    REACTION_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_REACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    HAS_OPINION_FIELD_NUMBER: _ClassVar[int]
    reaction_count: int
    last_reaction_type: str
    has_opinion: bool
    def __init__(self, reaction_count: _Optional[int] = ..., last_reaction_type: _Optional[str] = ..., has_opinion: bool = ...) -> None: ...

class GovernanceDecision(_message.Message):
    __slots__ = ("decision_id", "content_id", "content_type", "level", "harmful_weight", "marker_avg_credit", "reason", "actions", "decided_at")
    DECISION_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    HARMFUL_WEIGHT_FIELD_NUMBER: _ClassVar[int]
    MARKER_AVG_CREDIT_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    DECIDED_AT_FIELD_NUMBER: _ClassVar[int]
    decision_id: str
    content_id: str
    content_type: ContentSource
    level: GovernanceLevel
    harmful_weight: float
    marker_avg_credit: float
    reason: str
    actions: _containers.RepeatedScalarFieldContainer[str]
    decided_at: int
    def __init__(self, decision_id: _Optional[str] = ..., content_id: _Optional[str] = ..., content_type: _Optional[_Union[ContentSource, str]] = ..., level: _Optional[_Union[GovernanceLevel, str]] = ..., harmful_weight: _Optional[float] = ..., marker_avg_credit: _Optional[float] = ..., reason: _Optional[str] = ..., actions: _Optional[_Iterable[str]] = ..., decided_at: _Optional[int] = ...) -> None: ...

class DeviceInfo(_message.Message):
    __slots__ = ("device_type", "device_fingerprint", "os_version", "app_version")
    DEVICE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    OS_VERSION_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    device_type: DeviceType
    device_fingerprint: str
    os_version: str
    app_version: str
    def __init__(self, device_type: _Optional[_Union[DeviceType, str]] = ..., device_fingerprint: _Optional[str] = ..., os_version: _Optional[str] = ..., app_version: _Optional[str] = ...) -> None: ...
