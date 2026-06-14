import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/constants/app_constants.dart';

/// Standby API 服务 — 通过 REST 与 Gateway 通信
///
/// 网关端点前缀: /api/v1
/// 认证: JWT Bearer token + 设备指纹签名
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  static String? _baseUrlOverride;

  static String get _baseUrl {
    if (_baseUrlOverride != null) return _baseUrlOverride!;
    if (kIsWeb) return 'http://localhost:8080';
    return AppConstants.apiBaseUrl;
  }

  static void setBaseUrl(String url) {
    _baseUrlOverride = url;
  }

  final Dio _dio;
  final FlutterSecureStorage _storage;
  String? _accessToken;
  String? _deviceFingerprint;
  bool _authenticating = false;

  Dio get dio => _dio;

  ApiService._internal()
      : _dio = Dio(BaseOptions(
          baseUrl: _baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        )),
        _storage = const FlutterSecureStorage();

  /// 是否已初始化（有有效 token）
  bool get isInitialized => _accessToken != null;

  /// 解包网关响应 {success, data} → data
  static dynamic _unwrap(dynamic respData) {
    if (respData is Map<String, dynamic> && respData.containsKey('data')) {
      return respData['data'];
    }
    return respData;
  }

  /// 初始化: 加载或生成设备指纹 + 自动认证
  Future<void> init(String deviceFingerprint) async {
    _deviceFingerprint = deviceFingerprint;

    // 尝试从安全存储加载 token
    _accessToken = await _storage.read(key: 'access_token');

    // 设置拦截器: 自动附加认证头
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_accessToken != null) {
          options.headers['Authorization'] = 'Bearer $_accessToken';
        }
        if (_deviceFingerprint != null) {
          options.headers['X-Device-Id'] = _deviceFingerprint;
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && !_authenticating && _deviceFingerprint != null) {
          _authenticating = true;
          try {
            final ok = await _authenticate();
            if (ok) {
              try {
                final retryResponse = await _dio.fetch(error.requestOptions);
                return handler.resolve(retryResponse);
              } catch (_) {
                // 重试也失败，返回原始错误
              }
            }
          } catch (_) {
            // 认证失败，返回原始错误
          } finally {
            _authenticating = false;
          }
        }
        handler.next(error);
      },
    ));

    // 如果没有 token, 执行认证
    if (_accessToken == null) {
      try {
        await _authenticate();
      } catch (_) {
        // 认证失败不影响应用启动
      }
    }
  }

  /// 设备认证 (注册/登录)
  Future<bool> _authenticate() async {
    try {
      // 先尝试登录
      try {
        final loginResp = await _dio.post('/api/v1/auth/login', data: {
          'device_fingerprint': _deviceFingerprint,
        });
        final data = loginResp.data;
        _accessToken = data['data']['token'];
        await _storage.write(key: 'access_token', value: _accessToken);
        return true;
      } on DioException catch (e) {
        if (e.response?.statusCode == 401) {
          // 未注册，执行注册
          final regResp = await _dio.post('/api/v1/auth/register', data: {
            'device_fingerprint': _deviceFingerprint,
          });
          final data = regResp.data;
          _accessToken = data['data']['token'];
          await _storage.write(key: 'access_token', value: _accessToken);
          return true;
        }
        rethrow;
      }
    } catch (e) {
      debugPrint('认证失败: $e');
      return false;
    }
  }

  // ============================================================
  // 锚点 API
  // ============================================================

  /// 获取锚点列表
  Future<Map<String, dynamic>> listAnchors({
    int page = 1,
    int pageSize = 20,
    String? topicFilter,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
    };
    if (topicFilter != null) params['topic_filter'] = topicFilter;

    final resp = await _dio.get('/api/v1/anchors', queryParameters: params);
    return _unwrap(resp.data);
  }

  /// 获取锚点详情
  Future<Map<String, dynamic>> getAnchor(String anchorId) async {
    final resp = await _dio.get('/api/v1/anchors/$anchorId');
    return _unwrap(resp.data);
  }

  /// 创建锚点
  Future<Map<String, dynamic>> createAnchor({
    required List<String> sourceTexts,
    List<String>? topicHints,
    String source = 'user',
    String modality = 'text',
  }) async {
    final data = <String, dynamic>{
      'source_texts': sourceTexts,
      'source': source,
      'modality': modality,
    };
    if (topicHints != null) data['topic_hints'] = topicHints;

    final resp = await _dio.post('/api/v1/anchors', data: data);
    return _unwrap(resp.data);
  }

  /// 获取锚点的群体记忆
  Future<Map<String, dynamic>> getGroupMemory(String anchorId) async {
    final resp = await _dio.get('/api/v1/anchors/$anchorId/memory');
    return _unwrap(resp.data);
  }

  /// 获取感受链
  Future<Map<String, dynamic>> getFeelingChain(
    String anchorId, {
    int maxDepth = 3,
  }) async {
    final resp = await _dio.get(
      '/api/v1/anchors/$anchorId/chain',
      queryParameters: {'max_depth': maxDepth},
    );
    return _unwrap(resp.data);
  }

  // ============================================================
  // 反应 API
  // ============================================================

  /// 提交反应
  Future<Map<String, dynamic>> submitReaction({
    required String anchorId,
    required int reactionType,
    String? opinionText,
    int? emotionWord,
    String? parentReactionId,
  }) async {
    final data = <String, dynamic>{
      'anchor_id': anchorId,
      'reaction_type': reactionType,
    };
    if (opinionText != null) data['opinion_text'] = opinionText;
    if (emotionWord != null) data['emotion_word'] = emotionWord;
    if (parentReactionId != null) data['parent_reaction_id'] = parentReactionId;

    final resp = await _dio.post('/api/v1/reactions', data: data);
    return _unwrap(resp.data);
  }

  /// 获取锚点的反应列表
  Future<Map<String, dynamic>> listReactions(
    String anchorId, {
    int page = 1,
    int pageSize = 20,
    String? filterType,
  }) async {
    final params = <String, dynamic>{
      'anchor_id': anchorId,
      'page': page,
      'page_size': pageSize,
    };
    if (filterType != null) params['filter_type'] = filterType;
    final resp = await _dio.get('/api/v1/reactions', queryParameters: params);
    return _unwrap(resp.data);
  }

  /// 获取锚点反应分布
  Future<Map<String, dynamic>> getReactionDistribution(String anchorId) async {
    final resp = await _dio.get('/api/v1/reactions/distribution/$anchorId');
    return _unwrap(resp.data);
  }

  /// 获取共鸣踪迹 (我与他人的共鸣关系)
  Future<Map<String, dynamic>> getResonanceTraces({
    int page = 1,
    int pageSize = 20,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
    };
    final resp = await _dio.get('/api/v1/relationships/traces', queryParameters: params);
    return _unwrap(resp.data);
  }

  // ============================================================
  // 关系 API
  // ============================================================

  /// 查找共鸣对
  Future<Map<String, dynamic>> findResonancePairs(String userId) async {
    final resp = await _dio.get('/api/v1/relationships/$userId');
    return _unwrap(resp.data);
  }

  /// 获取关系列表
  Future<Map<String, dynamic>> getRelationships(String userId) async {
    final resp = await _dio.get('/api/v1/relationships/$userId');
    return _unwrap(resp.data);
  }

  /// 获取关系分
  Future<Map<String, dynamic>> getRelationshipScore(
    String userA,
    String userB,
  ) async {
    final resp = await _dio.get(
      '/api/v1/relationships/score',
      queryParameters: {'user_a': userA, 'user_b': userB},
    );
    return _unwrap(resp.data);
  }

  // ============================================================
  // 治理 API
  // ============================================================

  /// 评估内容治理
  Future<Map<String, dynamic>> evaluateContent({
    required String contentId,
    String contentType = 'anchor',
    required Map<String, int> reactionSummary,
  }) async {
    final data = <String, dynamic>{
      'content_id': contentId,
      'content_type': contentType,
      ...reactionSummary,
    };
    final resp = await _dio.post('/api/v1/governance/evaluate', data: data);
    return _unwrap(resp.data);
  }

  // ============================================================
  // 情境 API
  // ============================================================

  /// 提交情境状态
  Future<void> submitContextState({
    required String sceneType,
    String? moodHint,
    String? attentionLevel,
    int? activeDevice,
  }) async {
    await _dio.post('/api/v1/context', data: {
      'scene_type': sceneType,
      if (moodHint != null) 'mood_hint': moodHint,
      if (attentionLevel != null) 'attention_level': attentionLevel,
      if (activeDevice != null) 'active_device': activeDevice,
    });
  }

  /// 获取情境化话题权重
  Future<Map<String, dynamic>> getContextualWeights(List<String> topics) async {
    final resp = await _dio.get(
      '/api/v1/context/weights',
      queryParameters: {'topics': topics.join(',')},
    );
    return _unwrap(resp.data);
  }

  // ============================================================
  // 编码 API
  // ============================================================

  /// 文本编码为向量
  Future<Map<String, dynamic>> encodeText(List<String> texts) async {
    final resp = await _dio.post('/api/v1/encode', data: {
      'texts': texts,
    });
    return _unwrap(resp.data);
  }
}
