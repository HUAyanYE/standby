/// 用户身份模型
///
/// 设计理念（与 PRD 对齐）：
/// - 注册时：手机号验证 + 设备绑定（硬件身份），平台存档，永不对外暴露
/// - 展示时：系统分配随机昵称 + 随机头像（完全匿名）
/// - 知己关系中：可见用户设定的昵称 + 设定头像（非真名，非真实照片）
/// - 真名永不暴露：真名可被搜索、可跨平台追踪，一旦暴露无法收回
class UserIdentity {
  final String deviceId; // 硬件指纹（SHA-256, 64 字符 hex），注册时绑定
  final String? phoneHash; // 手机号哈希（注册时存档，永不对外暴露）
  final String setNickname; // 用户设定昵称（知己关系中可见）
  final String setAvatar; // 用户设定头像（知己关系中可见，非真实照片）
  final DateTime createdAt;

  UserIdentity({
    required this.deviceId,
    this.phoneHash,
    required this.setNickname,
    required this.setAvatar,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  /// 从 JSON 创建
  factory UserIdentity.fromJson(Map<String, dynamic> json) {
    return UserIdentity(
      deviceId: json['device_id'] as String,
      phoneHash: json['phone_hash'] as String?,
      setNickname: json['set_nickname'] as String,
      setAvatar: json['set_avatar'] as String,
      createdAt: DateTime.fromMillisecondsSinceEpoch(json['created_at'] as int),
    );
  }

  /// 转换为 JSON
  Map<String, dynamic> toJson() {
    return {
      'device_id': deviceId,
      'phone_hash': phoneHash,
      'set_nickname': setNickname,
      'set_avatar': setAvatar,
      'created_at': createdAt.millisecondsSinceEpoch,
    };
  }

  /// 便捷访问器
  String get nickname => setNickname;
  String get avatar => setAvatar;

  /// 显示名称（设定头像 + 设定昵称）
  /// 仅在知己关系中使用，普通展示使用系统随机生成的匿名身份
  String get displayName => '$setAvatar $setNickname';
}
