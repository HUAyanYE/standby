/// ============================================================
/// Standby Flutter 客户端 — 网关接口定义
/// ============================================================
///
/// 对齐 proto/gateway/gateway.proto
/// 通过 flutter_rust_bridge 调用 Rust gRPC 客户端
/// Dart 层只定义接口和数据模型, 不直接处理网络通信
/// ============================================================

// ============================================================
// 数据模型 (对齐 proto/common/common.proto)
// ============================================================

/// 五态反应类型
enum ReactionType {
  resonance,      // 共鸣
  neutral,        // 无感
  opposition,     // 反对
  unexperienced,  // 未体验
  harmful,        // 有害
}

/// 共鸣情绪词 (可选)
enum EmotionWord {
  none,       // 未选择
  empathy,    // 同感
  trigger,    // 触发
  insight,    // 启发
  shock,      // 震撼
}

/// 信任级别
enum TrustLevel {
  l0Browse,           // 浏览
  l1TraceVisible,     // 痕迹可见
  l2OpinionReply,     // 观点回应
  l3AsyncMessage,     // 异步私信
  l4RealtimeChat,     // 实时对话
  l5GroupChat,        // 群体对话
}

/// 锚点类型
enum AnchorType {
  platformInitial,    // 平台初始
  userContent,        // 用户内容
  aiAggregated,       // AI 聚合
}

/// 设备类型
enum DeviceType {
  phone,
  tablet,
  pc,
  vehicle,
}

// ============================================================
// 数据模型类
// ============================================================

/// 锚点摘要 (列表展示)
class AnchorSummary {
  final String anchorId;
  final String title;
  final AnchorType anchorType;
  final List<String> topics;
  final int totalReactions;
  final DateTime createdAt;

  const AnchorSummary({
    required this.anchorId,
    required this.title,
    required this.anchorType,
    required this.topics,
    required this.totalReactions,
    required this.createdAt,
  });
}

/// 完整锚点
class Anchor {
  final String anchorId;
  final String text;
  final AnchorType anchorType;
  final List<String> topics;
  final String sourceAttribution;
  final AnchorQuality quality;
  final DateTime createdAt;

  const Anchor({
    required this.anchorId,
    required this.text,
    required this.anchorType,
    required this.topics,
    required this.sourceAttribution,
    required this.quality,
    required this.createdAt,
  });
}

/// 锚点质量评分
class AnchorQuality {
  final double completeness;  // 完整性
  final double specificity;   // 具体性
  final double authenticity;  // 真实性
  final double thoughtSpace;  // 引发思考的空间
  final double overall;       // 综合评分

  const AnchorQuality({
    required this.completeness,
    required this.specificity,
    required this.authenticity,
    required this.thoughtSpace,
    required this.overall,
  });
}

/// 匿名身份
class AnonymousIdentity {
  final String identityId;
  final String displayName;   // 随机昵称 (如 "夜的旅人")
  final String avatarSeed;    // 头像种子
  final String anchorId;
  final bool isFixed;         // 是否已固定 (知己)

  const AnonymousIdentity({
    required this.identityId,
    required this.displayName,
    required this.avatarSeed,
    required this.anchorId,
    required this.isFixed,
  });
}

/// 反应统计 (群体共鸣预感)
class ReactionSummary {
  final String anchorId;
  final int resonanceCount;
  final int neutralCount;
  final int oppositionCount;
  final int unexperiencedCount;
  final int harmfulCount;
  final int totalCount;

  const ReactionSummary({
    required this.anchorId,
    required this.resonanceCount,
    required this.neutralCount,
    required this.oppositionCount,
    required this.unexperiencedCount,
    required this.harmfulCount,
    required this.totalCount,
  });
}

/// 重现锚点
class ReplayAnchor {
  final AnchorSummary summary;
  final String triggerType;   // "seasonal" / "anniversary" / ...
  final double triggerScore;
  final GroupMemory? groupMemory;

  const ReplayAnchor({
    required this.summary,
    required this.triggerType,
    required this.triggerScore,
    this.groupMemory,
  });
}

/// 群体记忆数据
class GroupMemory {
  final String anchorId;
  final int totalReactions;
  final int resonanceCount;
  final int oppositionCount;
  final List<RepresentativeOpinion> opinions;
  final UserOwnHistory? userOwn;

  const GroupMemory({
    required this.anchorId,
    required this.totalReactions,
    required this.resonanceCount,
    required this.oppositionCount,
    required this.opinions,
    this.userOwn,
  });
}

/// 代表性观点
class RepresentativeOpinion {
  final String text;          // 截断展示
  final int resonanceCount;
  final DateTime createdAt;

  const RepresentativeOpinion({
    required this.text,
    required this.resonanceCount,
    required this.createdAt,
  });
}

/// 用户自己的历史
class UserOwnHistory {
  final int reactionCount;
  final String lastReactionType;
  final bool hasOpinion;

  const UserOwnHistory({
    required this.reactionCount,
    required this.lastReactionType,
    required this.hasOpinion,
  });
}

/// 反应视图 (锚点下展示)
class ReactionView {
  final String reactionId;
  final AnonymousIdentity author;
  final ReactionType reactionType;
  final EmotionWord emotionWord;
  final String? opinionText;
  final bool hasResonanceTrace;
  final String? traceHint;    // "你在此人的其他观点上也有过共鸣"
  final DateTime createdAt;

  const ReactionView({
    required this.reactionId,
    required this.author,
    required this.reactionType,
    required this.emotionWord,
    this.opinionText,
    required this.hasResonanceTrace,
    this.traceHint,
    required this.createdAt,
  });
}

/// 共鸣痕迹
class ResonanceTrace {
  final String traceId;
  final AnonymousIdentity otherUser;
  final double relationshipScore;
  final int sharedAnchors;
  final int sharedTopics;
  final List<String> recentAnchorTitles;
  final TrustLevel trustLevel;

  const ResonanceTrace({
    required this.traceId,
    required this.otherUser,
    required this.relationshipScore,
    required this.sharedAnchors,
    required this.sharedTopics,
    required this.recentAnchorTitles,
    required this.trustLevel,
  });
}

/// 用户档案
class UserProfile {
  final String userId;
  final double creditScore;
  final double markerCredit;
  final int totalReactions;
  final int totalAnchorsEngaged;
  final int confidantCount;
  final DateTime createdAt;

  const UserProfile({
    required this.userId,
    required this.creditScore,
    required this.markerCredit,
    required this.totalReactions,
    required this.totalAnchorsEngaged,
    required this.confidantCount,
    required this.createdAt,
  });
}

/// 知己视图
class ConfidantView {
  final String confidantId;
  final String fixedName;
  final String fixedAvatarUrl;
  final double relationshipScore;
  final DateTime establishedAt;
  final DateTime lastInteractionAt;

  const ConfidantView({
    required this.confidantId,
    required this.fixedName,
    required this.fixedAvatarUrl,
    required this.relationshipScore,
    required this.establishedAt,
    required this.lastInteractionAt,
  });
}

/// 提交反应的结果
class SubmitReactionResult {
  final bool success;
  final String reactionId;
  final double resonanceValue;
  final ReactionSummary anchorSummary;
  final List<ResonanceNotification> notifications;

  const SubmitReactionResult({
    required this.success,
    required this.reactionId,
    required this.resonanceValue,
    required this.anchorSummary,
    required this.notifications,
  });
}

/// 共鸣通知
class ResonanceNotification {
  final String type;          // "new_trace" / "trust_level_up" / "confidant_eligible"
  final String message;
  final String? relatedUserAnonymousName;

  const ResonanceNotification({
    required this.type,
    required this.message,
    this.relatedUserAnonymousName,
  });
}

// ============================================================
// 服务接口 (对齐 proto/gateway/gateway.proto)
// ============================================================
//
// 这些接口由 Rust gRPC 客户端实现
// Dart 层通过 flutter_rust_bridge 调用

/// 认证服务
abstract class AuthService {
  /// 设备认证 → 获取 JWT
  Future<AuthResult> deviceAuth(DeviceInfo device);
  
  /// 刷新令牌
  Future<AuthResult> refreshToken(String refreshToken);
  
  /// 登出
  Future<void> logout();
}

class AuthResult {
  final bool success;
  final String? accessToken;
  final String? refreshToken;
  final DateTime? expiresAt;
  final String? error;

  const AuthResult({
    required this.success,
    this.accessToken,
    this.refreshToken,
    this.expiresAt,
    this.error,
  });
}

class DeviceInfo {
  final DeviceType deviceType;
  final String fingerprint;
  final String osVersion;
  final String appVersion;

  const DeviceInfo({
    required this.deviceType,
    required this.fingerprint,
    required this.osVersion,
    required this.appVersion,
  });
}

/// 锚点服务
abstract class AnchorService {
  /// 获取锚点列表 (Feed)
  Future<List<AnchorSummary>> listAnchors({
    int page = 1,
    int pageSize = 20,
    List<String>? topicFilter,
  });
  
  /// 获取单个锚点详情
  Future<Anchor?> getAnchor(String anchorId);
  
  /// 获取重现锚点 (含群体记忆)
  Future<List<ReplayAnchor>> getReplayAnchors({int topK = 5});
  
  /// 导入外部内容为锚点素材
  Future<ImportResult> importAnchor({
    required String contentText,
    String? sourceUrl,
  });
  
  /// 获取锚点下的反应统计
  Future<ReactionSummary?> getReactionSummary(String anchorId);
}

class ImportResult {
  final bool accepted;
  final String? anchorId;
  final String message;

  const ImportResult({
    required this.accepted,
    this.anchorId,
    required this.message,
  });
}

/// 反应服务
abstract class ReactionService {
  /// 提交反应 (五态 + 可选观点)
  Future<SubmitReactionResult> submitReaction({
    required String anchorId,
    required ReactionType reactionType,
    EmotionWord emotionWord = EmotionWord.none,
    String? opinionText,
  });
  
  /// 获取锚点下的反应列表
  Future<List<ReactionView>> listReactions({
    required String anchorId,
    ReactionType? filterType,
    int page = 1,
    int pageSize = 20,
  });
  
  /// 获取共鸣痕迹
  Future<List<ResonanceTrace>> getResonanceTraces({
    int page = 1,
    int pageSize = 20,
  });
}

/// 用户服务
abstract class UserService {
  /// 获取用户档案
  Future<UserProfile> getProfile();
  
  /// 获取关系列表
  Future<List<RelationshipView>> listRelationships({
    TrustLevel minLevel = TrustLevel.l1TraceVisible,
  });
  
  /// 表达知己意向
  Future<ConfidantIntentResult> expressConfidantIntent(String targetHash);
  
  /// 获取知己列表
  Future<List<ConfidantView>> listConfidants();
}

class RelationshipView {
  final AnonymousIdentity otherUser;
  final double relationshipScore;
  final int topicDiversity;
  final TrustLevel trustLevel;
  final bool isConfidant;
  final DateTime lastResonanceAt;

  const RelationshipView({
    required this.otherUser,
    required this.relationshipScore,
    required this.topicDiversity,
    required this.trustLevel,
    required this.isConfidant,
    required this.lastResonanceAt,
  });
}

class ConfidantIntentResult {
  final bool success;
  final bool matched;     // 是否已双向匹配
  final String message;

  const ConfidantIntentResult({
    required this.success,
    required this.matched,
    required this.message,
  });
}

/// 情境服务
abstract class ContextService {
  /// 提交情境状态
  Future<void> submitContextState(ContextState state);
  
  /// 获取情境化推荐提示
  Future<ContextualHint> getContextualHint();
}

class ContextState {
  final String sceneType;
  final String moodHint;
  final String attentionLevel;
  final DeviceType activeDevice;

  const ContextState({
    required this.sceneType,
    required this.moodHint,
    required this.attentionLevel,
    required this.activeDevice,
  });
}

class ContextualHint {
  final String recommendedScene;
  final String moodSuggestion;
  final List<String> topicHints;

  const ContextualHint({
    required this.recommendedScene,
    required this.moodSuggestion,
    required this.topicHints,
  });
}

/// 治理服务 (用户侧)
abstract class GovernanceService {
  /// 举报内容
  Future<ReportResult> reportContent({
    required String contentId,
    required ReactionType reportType,  // harmful / unexperienced
    required String reason,            // 必须填写理由
  });
  
  /// 获取内容状态 (作者查看)
  Future<ContentStatus> getContentStatus(String contentId);
  
  /// 申诉
  Future<AppealResult> appealDecision({
    required String decisionId,
    required String appealReason,
  });
}

class ReportResult {
  final bool accepted;
  final String message;

  const ReportResult({required this.accepted, required this.message});
}

class ContentStatus {
  final String level;
  final String statusMessage;
  final bool canAppeal;

  const ContentStatus({
    required this.level,
    required this.statusMessage,
    required this.canAppeal,
  });
}

class AppealResult {
  final bool accepted;
  final String message;

  const AppealResult({required this.accepted, required this.message});
}
