import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// 本地存储服务 — 管理用户设置和本地数据
class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  late SharedPreferences _prefs;

  // 键名常量
  static const String _keyOnboardingDone = 'onboarding_done';
  static const String _keyUserIdentity = 'user_identity';
  static const String _keySwipeDirection = 'swipe_direction'; // 'vertical' or 'horizontal'
  static const String _keyAccessToken = 'access_token';
  static const String _keyDeviceFingerprint = 'device_fingerprint';
  static const String _keyMyReactions = 'my_reactions'; // 我的反应记录
  static const String _keyMyPosts = 'my_posts'; // 我的发布记录

  /// 初始化
  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // ── Onboarding ──────────────────────────────────────────

  bool get isOnboardingDone => _prefs.getBool(_keyOnboardingDone) ?? false;

  Future<void> setOnboardingDone() async {
    await _prefs.setBool(_keyOnboardingDone, true);
  }

  // ── 用户身份 ──────────────────────────────────────────

  Map<String, dynamic>? get userIdentity {
    final jsonStr = _prefs.getString(_keyUserIdentity);
    if (jsonStr == null) return null;
    return jsonDecode(jsonStr);
  }

  Future<void> setUserIdentity(Map<String, dynamic> identity) async {
    await _prefs.setString(_keyUserIdentity, jsonEncode(identity));
  }

  bool get isRegistered => userIdentity != null;

  // ── 滑动方向设置 ──────────────────────────────────────────

  String get swipeDirection => _prefs.getString(_keySwipeDirection) ?? 'vertical';

  Future<void> setSwipeDirection(String direction) async {
    await _prefs.setString(_keySwipeDirection, direction);
  }

  bool get isVerticalSwipe => swipeDirection == 'vertical';

  // ── Token ──────────────────────────────────────────

  String? get accessToken => _prefs.getString(_keyAccessToken);

  Future<void> setAccessToken(String token) async {
    await _prefs.setString(_keyAccessToken, token);
  }

  String? get deviceFingerprint => _prefs.getString(_keyDeviceFingerprint);

  Future<void> setDeviceFingerprint(String fingerprint) async {
    await _prefs.setString(_keyDeviceFingerprint, fingerprint);
  }

  // ── 我的反应记录 ──────────────────────────────────────────

  List<Map<String, dynamic>> get myReactions {
    final jsonStr = _prefs.getString(_keyMyReactions);
    if (jsonStr == null) return [];
    final list = jsonDecode(jsonStr) as List;
    return list.cast<Map<String, dynamic>>();
  }

  Future<void> addMyReaction(Map<String, dynamic> reaction) async {
    final reactions = myReactions;
    reactions.insert(0, reaction); // 最新的在前面
    // 只保留最近 100 条
    if (reactions.length > 100) {
      reactions.removeRange(100, reactions.length);
    }
    await _prefs.setString(_keyMyReactions, jsonEncode(reactions));
  }

  Future<void> clearMyReactions() async {
    await _prefs.remove(_keyMyReactions);
  }

  // ── 我的发布记录 ──────────────────────────────────────────

  List<Map<String, dynamic>> get myPosts {
    final jsonStr = _prefs.getString(_keyMyPosts);
    if (jsonStr == null) return [];
    final list = jsonDecode(jsonStr) as List;
    return list.cast<Map<String, dynamic>>();
  }

  Future<void> addMyPost(Map<String, dynamic> post) async {
    final posts = myPosts;
    posts.insert(0, post); // 最新的在前面
    // 只保留最近 50 条
    if (posts.length > 50) {
      posts.removeRange(50, posts.length);
    }
    await _prefs.setString(_keyMyPosts, jsonEncode(posts));
  }

  Future<void> clearMyPosts() async {
    await _prefs.remove(_keyMyPosts);
  }

  // ── 清除所有数据 ──────────────────────────────────────────

  Future<void> clearAll() async {
    await _prefs.clear();
  }
}
