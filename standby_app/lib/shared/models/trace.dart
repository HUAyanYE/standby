/// 共鸣痕迹模型 — 表示与我共鸣的人
class Trace {
  final String userId; // 对方的匿名 ID
  final String nickname; // 对方的昵称
  final String avatar; // 对方的头像
  final int sharedAnchors; // 共同锚点数量
  final List<String> sharedTopics; // 共同话题
  final String lastAnchorText; // 最近共鸣的锚点文本
  final DateTime lastResonanceAt; // 最近共鸣时间

  Trace({
    required this.userId,
    required this.nickname,
    required this.avatar,
    required this.sharedAnchors,
    required this.sharedTopics,
    required this.lastAnchorText,
    required this.lastResonanceAt,
  });

  /// 从 JSON 创建
  factory Trace.fromJson(Map<String, dynamic> json) {
    return Trace(
      userId: json['user_id'] as String,
      nickname: json['nickname'] as String,
      avatar: json['avatar'] as String,
      sharedAnchors: json['shared_anchors'] as int,
      sharedTopics: (json['shared_topics'] as List).cast<String>(),
      lastAnchorText: json['last_anchor_text'] as String,
      lastResonanceAt: DateTime.fromMillisecondsSinceEpoch(json['last_resonance_at'] as int),
    );
  }

  /// 显示名称
  String get displayName => '$avatar $nickname';
}
