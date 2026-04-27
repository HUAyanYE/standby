/// 用户匿名身份模型
class UserIdentity {
  final String nickname; // 昵称，如 "夜的旅人"
  final String avatar; // 头像，如 "🌙"
  final DateTime createdAt;

  UserIdentity({
    required this.nickname,
    required this.avatar,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// 从 JSON 创建
  factory UserIdentity.fromJson(Map<String, dynamic> json) {
    return UserIdentity(
      nickname: json['nickname'] as String,
      avatar: json['avatar'] as String,
      createdAt: DateTime.fromMillisecondsSinceEpoch(json['created_at'] as int),
    );
  }

  /// 转换为 JSON
  Map<String, dynamic> toJson() {
    return {
      'nickname': nickname,
      'avatar': avatar,
      'created_at': createdAt.millisecondsSinceEpoch,
    };
  }

  /// 显示名称（头像 + 昵称）
  String get displayName => '$avatar $nickname';
}
