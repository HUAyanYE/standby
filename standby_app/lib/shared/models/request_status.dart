/// 异步请求状态模型

/// 请求状态值
enum RequestStatusValue {
  pending,   // 处理中
  done,      // 完成
  failed,    // 失败
}

/// 异步请求状态
class RequestStatus {
  final String requestId;
  final RequestStatusValue status;
  final Map<String, dynamic>? result;
  final String? error;

  const RequestStatus({
    required this.requestId,
    required this.status,
    this.result,
    this.error,
  });

  factory RequestStatus.fromJson(Map<String, dynamic> json) {
    return RequestStatus(
      requestId: json['request_id'] as String,
      status: _parseStatus(json['status'] as String? ?? 'pending'),
      result: json['result'] as Map<String, dynamic>?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'request_id': requestId,
      'status': status.name,
      if (result != null) 'result': result,
      if (error != null) 'error': error,
    };
  }

  /// 是否处理中
  bool get isPending => status == RequestStatusValue.pending;

  /// 是否完成
  bool get isDone => status == RequestStatusValue.done;

  /// 是否失败
  bool get isFailed => status == RequestStatusValue.failed;

  /// 是否已结束 (完成或失败)
  bool get isCompleted => isDone || isFailed;

  /// 获取共鸣值 (如果完成)
  double? get resonanceValue {
    if (result == null) return null;
    return (result!['resonance_value'] as num?)?.toDouble();
  }

  /// 获取关系分数 (如果完成)
  double? get relationshipScore {
    if (result == null) return null;
    return (result!['relationship_score'] as num?)?.toDouble();
  }

  /// 获取关联用户 ID (如果完成)
  String? get relatedUserId {
    if (result == null) return null;
    return result!['related_user_id'] as String?;
  }

  static RequestStatusValue _parseStatus(String value) {
    return RequestStatusValue.values.firstWhere(
      (s) => s.name == value,
      orElse: () => RequestStatusValue.pending,
    );
  }
}
