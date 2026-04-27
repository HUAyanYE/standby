import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/app_constants.dart';
import '../models/request_status.dart';

/// Standby API 服务 — 通过 REST 与 Gateway 通信
class ApiService {
  static String? _baseUrlOverride;

  static String get _baseUrl {
    if (_baseUrlOverride != null) return _baseUrlOverride!;
    if (kIsWeb) return 'http://localhost:8080';
    return 'http://localhost:8080';
  }

  static void setBaseUrl(String url) {
    _baseUrlOverride = url;
  }

  final Dio _dio;
  final FlutterSecureStorage _storage;
  String? _accessToken;
  String? _deviceFingerprint;

  /// 获取 Dio 实例 (供 MediaService 使用)
  Dio get dio => _dio;

  ApiService()
      : _dio = Dio(BaseOptions(
          baseUrl: _baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        )),
        _storage = const FlutterSecureStorage();

  /// 是否已初始化（有有效 token）
  bool get isInitialized => _accessToken != null;

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
          options.headers['X-Device-Fingerprint'] = _deviceFingerprint;
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          final ok = await _authenticate();
          if (ok) {
            final retryResponse = await _dio.fetch(error.requestOptions);
            return handler.resolve(retryResponse);
          }
        }
        handler.next(error);
      },
    ));

    // 如果没有 token, 执行认证
    if (_accessToken == null) {
      await _authenticate();
    }
  }

  /// 设备认证
  Future<bool> _authenticate() async {
    try {
      final resp = await _dio.post('/auth/device', data: {
        'device_type': 'phone',
        'device_fingerprint': _deviceFingerprint,
        'os_version': AppConstants.osVersion,
        'app_version': AppConstants.appVersion,
      });

      final data = resp.data;
      _accessToken = data['access_token'];
      await _storage.write(key: 'access_token', value: _accessToken);

      return true;
    } catch (e) {
      print('认证失败: $e');
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

    final resp = await _dio.get('/anchors', queryParameters: params);
    return resp.data;
  }

  /// 获取锚点详情
  Future<Map<String, dynamic>> getAnchor(String anchorId) async {
    final resp = await _dio.get('/anchors/$anchorId');
    return resp.data;
  }

  /// 创建锚点 (多模态)
  Future<Map<String, dynamic>> createAnchor({
    required String modality,
    String? textContent,
    List<String>? mediaIds,
    required List<String> topics,
    String source = 'user',
  }) async {
    final data = <String, dynamic>{
      'modality': modality,
      'topics': topics,
      'source': source,
    };
    if (textContent != null) data['text_content'] = textContent;
    if (mediaIds != null && mediaIds.isNotEmpty) data['media_ids'] = mediaIds;

    final resp = await _dio.post('/anchors', data: data);
    return resp.data;
  }

  /// 创建锚点 (系统 AI)
  Future<Map<String, dynamic>> createAnchorFromSystemAi({
    required String text,
    required List<String> topics,
    required String source,
    String? mediaId,
    String? emotionHint,
  }) async {
    final data = <String, dynamic>{
      'text': text,
      'topics': topics,
      'source': source,
    };
    if (mediaId != null) data['media_id'] = mediaId;
    if (emotionHint != null) data['emotion_hint'] = emotionHint;

    final resp = await _dio.post('/anchors/from-system-ai', data: data);
    return resp.data;
  }

  /// 获取重现锚点
  Future<Map<String, dynamic>> getReplayAnchors({
    int limit = 5,
  }) async {
    final resp = await _dio.get(
      '/anchors/replay',
      queryParameters: {'limit': limit},
    );
    return resp.data;
  }

  // ============================================================
  // 反应 API
  // ============================================================

  /// 提交反应 (多模态)
  Future<Map<String, dynamic>> submitReaction({
    required String anchorId,
    required String reactionType,
    String? emotionWord,
    required String modality,
    String? textContent,
    List<String>? mediaIds,
  }) async {
    final data = <String, dynamic>{
      'anchor_id': anchorId,
      'reaction_type': reactionType,
      'modality': modality,
    };
    if (emotionWord != null) data['emotion_word'] = emotionWord;
    if (textContent != null) data['text_content'] = textContent;
    if (mediaIds != null && mediaIds.isNotEmpty) data['media_ids'] = mediaIds;

    final resp = await _dio.post('/reactions', data: data);
    return resp.data;
  }

  /// 获取锚点的反应列表
  Future<Map<String, dynamic>> listReactions(
    String anchorId, {
    int page = 1,
    int pageSize = 20,
    String? filterType,
  }) async {
    final params = <String, dynamic>{'page': page, 'page_size': pageSize};
    if (filterType != null) params['filter_type'] = filterType;
    final resp = await _dio.get('/anchors/$anchorId/reactions', queryParameters: params);
    return resp.data;
  }

  /// 获取锚点反应统计
  Future<Map<String, dynamic>> getReactionSummary(String anchorId) async {
    final resp = await _dio.get('/anchors/$anchorId/summary');
    return resp.data;
  }

  // ============================================================
  // 请求状态 API
  // ============================================================

  /// 查询异步请求状态
  Future<RequestStatus> getRequestStatus(String requestId) async {
    final resp = await _dio.get('/request/$requestId/status');
    return RequestStatus.fromJson(resp.data);
  }

  /// 轮询等待请求完成
  Future<RequestStatus> waitForRequest(
    String requestId, {
    Duration timeout = const Duration(seconds: 30),
    Duration interval = const Duration(milliseconds: 500),
  }) async {
    final deadline = DateTime.now().add(timeout);
    while (DateTime.now().isBefore(deadline)) {
      final status = await getRequestStatus(requestId);
      if (status.status != RequestStatusValue.pending) {
        return status;
      }
      await Future.delayed(interval);
    }
    return RequestStatus(
      requestId: requestId,
      status: RequestStatusValue.failed,
      error: 'Timeout',
    );
  }

  // ============================================================
  // 用户 API
  // ============================================================

  /// 获取用户档案
  Future<Map<String, dynamic>> getProfile() async {
    final resp = await _dio.get('/me');
    return resp.data;
  }

  /// 获取共鸣痕迹
  Future<Map<String, dynamic>> getResonanceTraces() async {
    final resp = await _dio.get('/traces');
    return resp.data;
  }

  /// 获取关系列表
  Future<Map<String, dynamic>> getRelationships() async {
    final resp = await _dio.get('/relationships');
    return resp.data;
  }

  // ============================================================
  // 情境 API
  // ============================================================

  /// 获取情境化提示
  Future<Map<String, dynamic>> getContextualHint() async {
    final resp = await _dio.get('/context/hint');
    return resp.data;
  }

  /// 提交情境状态
  Future<void> submitContextState({
    required String sceneType,
    required String moodHint,
    required String attentionLevel,
    required String activeDevice,
  }) async {
    await _dio.post('/context', data: {
      'scene_type': sceneType,
      'mood_hint': moodHint,
      'attention_level': attentionLevel,
      'active_device': activeDevice,
    });
  }

  /// 接收系统 AI 上下文
  Future<void> ingestContext({
    required String contextType,
    required Map<String, dynamic> rawData,
  }) async {
    await _dio.post('/context/ingest', data: {
      'context_type': contextType,
      'raw_data': rawData,
      'timestamp': DateTime.now().millisecondsSinceEpoch ~/ 1000,
    });
  }

  /// 获取锚点候选 (系统 AI 生成)
  Future<List<Map<String, dynamic>>> getContextCandidates() async {
    final resp = await _dio.get('/context/candidates');
    return (resp.data['candidates'] as List).cast<Map<String, dynamic>>();
  }

  // ============================================================
  // 治理 API
  // ============================================================

  /// 举报内容
  Future<Map<String, dynamic>> reportContent({
    required String contentId,
    required String contentType,
    required String reason,
  }) async {
    final resp = await _dio.post('/report', data: {
      'content_id': contentId,
      'content_type': contentType,
      'reason': reason,
    });
    return resp.data;
  }

  // ============================================================
  // 话题 API
  // ============================================================

  /// 获取热搜话题
  Future<List<Map<String, dynamic>>> getTrendingTopics() async {
    try {
      final resp = await _dio.get('/topics/trending');
      return (resp.data['topics'] as List).cast<Map<String, dynamic>>();
    } catch (e) {
      // 如果端点不存在，返回空列表
      return [];
    }
  }

  /// 话题自动补全
  Future<List<String>> autocompleteTopic(String query) async {
    try {
      final resp = await _dio.get('/topics/autocomplete', queryParameters: {'q': query});
      return (resp.data['suggestions'] as List).cast<String>();
    } catch (e) {
      // 如果端点不存在，返回空列表
      return [];
    }
  }
}
