/// 心物模型 — 支持多模态内容 (原 Anchor 模型)

/// 心物模态类型
enum SeedstoneModality {
  text,    // 纯文本
  image,   // 图片
  audio,   // 音频
  video,   // 视频
  mixed,   // 混合 (文本 + 媒体)
}

/// 心物来源
enum SeedstoneSource {
  user,      // 用户手动创建
  systemAi,  // 系统 AI 建议
  shared,    // 系统分享
}

/// 媒体文件引用
class MediaRef {
  final String mediaId;
  final String mediaType;      // 'image', 'audio', 'video'
  final String mimeType;       // 'image/jpeg', 'audio/mp3', 'video/mp4'
  final String storageUrl;     // MinIO URL
  final String? thumbnailUrl;  // 缩略图 URL (视频/图片)
  final int fileSizeBytes;
  final double? durationSeconds;  // 音频/视频时长
  final int? width;               // 图片/视频宽度
  final int? height;              // 图片/视频高度

  const MediaRef({
    required this.mediaId,
    required this.mediaType,
    required this.mimeType,
    required this.storageUrl,
    this.thumbnailUrl,
    required this.fileSizeBytes,
    this.durationSeconds,
    this.width,
    this.height,
  });

  factory MediaRef.fromJson(Map<String, dynamic> json) {
    return MediaRef(
      mediaId: json['media_id'] as String,
      mediaType: json['media_type'] as String,
      mimeType: json['mime_type'] as String,
      storageUrl: json['storage_url'] as String,
      thumbnailUrl: json['thumbnail_url'] as String?,
      fileSizeBytes: json['file_size_bytes'] as int? ?? 0,
      durationSeconds: (json['duration_seconds'] as num?)?.toDouble(),
      width: json['width'] as int?,
      height: json['height'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'media_id': mediaId,
      'media_type': mediaType,
      'mime_type': mimeType,
      'storage_url': storageUrl,
      if (thumbnailUrl != null) 'thumbnail_url': thumbnailUrl,
      'file_size_bytes': fileSizeBytes,
      if (durationSeconds != null) 'duration_seconds': durationSeconds,
      if (width != null) 'width': width,
      if (height != null) 'height': height,
    };
  }
}

/// 心物模型
class Seedstone {
  final String seedstoneId;
  final String creatorId;
  final SeedstoneModality modality;
  final String? textContent;
  final List<MediaRef> media;
  final List<String> topics;
  final SeedstoneSource source;
  final double qualityScore;
  final int createdAt;

  const Seedstone({
    required this.seedstoneId,
    required this.creatorId,
    required this.modality,
    this.textContent,
    required this.media,
    required this.topics,
    required this.source,
    required this.qualityScore,
    required this.createdAt,
  });

  factory Seedstone.fromJson(Map<String, dynamic> json) {
    return Seedstone(
      seedstoneId: json['anchor_id'] as String, // API 仍用 anchor_id
      creatorId: json['creator_id'] as String? ?? '',
      modality: _parseModality(json['modality'] as String? ?? 'text'),
      textContent: json['text_content'] as String?,
      media: (json['media'] as List?)
          ?.map((m) => MediaRef.fromJson(m as Map<String, dynamic>))
          .toList() ?? [],
      topics: (json['topics'] as List?)?.cast<String>() ?? [],
      source: _parseSource(json['source'] as String? ?? 'user'),
      qualityScore: (json['quality_score'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'anchor_id': seedstoneId,
      'creator_id': creatorId,
      'modality': modality.name,
      if (textContent != null) 'text_content': textContent,
      'media': media.map((m) => m.toJson()).toList(),
      'topics': topics,
      'source': source.name,
      'quality_score': qualityScore,
      'created_at': createdAt,
    };
  }

  /// 是否有媒体内容
  bool get hasMedia => media.isNotEmpty;

  /// 是否有文本内容
  bool get hasText => textContent != null && textContent!.isNotEmpty;

  /// 是否为多模态
  bool get isMultiModal => modality == SeedstoneModality.mixed;

  /// 获取主要媒体 (第一个)
  MediaRef? get primaryMedia => media.isNotEmpty ? media.first : null;

  /// 获取显示用的摘要文本
  String get displayText {
    if (textContent != null && textContent!.isNotEmpty) {
      return textContent!;
    }
    if (media.isNotEmpty) {
      final m = media.first;
      switch (m.mediaType) {
        case 'image':
          return '[图片]';
        case 'audio':
          return '[音频]';
        case 'video':
          return '[视频]';
        default:
          return '[媒体]';
      }
    }
    return '[心物]';
  }

  static SeedstoneModality _parseModality(String value) {
    return SeedstoneModality.values.firstWhere(
      (m) => m.name == value,
      orElse: () => SeedstoneModality.text,
    );
  }

  static SeedstoneSource _parseSource(String value) {
    return SeedstoneSource.values.firstWhere(
      (s) => s.name == value,
      orElse: () => SeedstoneSource.user,
    );
  }
}

/// 反应模型
class Reaction {
  final String reactionId;
  final String userId;
  final String seedstoneId;
  final String reactionType;
  final String? emotionWord;
  final String modality;
  final String? textContent;
  final List<MediaRef> media;
  final double? resonanceValue;
  final int createdAt;

  const Reaction({
    required this.reactionId,
    required this.userId,
    required this.seedstoneId,
    required this.reactionType,
    this.emotionWord,
    required this.modality,
    this.textContent,
    required this.media,
    this.resonanceValue,
    required this.createdAt,
  });

  factory Reaction.fromJson(Map<String, dynamic> json) {
    return Reaction(
      reactionId: json['reaction_id'] as String,
      userId: json['user_id'] as String? ?? '',
      seedstoneId: json['anchor_id'] as String, // API 仍用 anchor_id
      reactionType: json['reaction_type'] as String,
      emotionWord: json['emotion_word'] as String?,
      modality: json['modality'] as String? ?? 'text',
      textContent: json['text_content'] as String?,
      media: (json['media'] as List?)
          ?.map((m) => MediaRef.fromJson(m as Map<String, dynamic>))
          .toList() ?? [],
      resonanceValue: (json['resonance_value'] as num?)?.toDouble(),
      createdAt: json['created_at'] as int? ?? 0,
    );
  }
}

/// 上下文提示模型
class ContextHint {
  final String moodSuggestion;
  final String recommendedScene;
  final List<String> topicHints;

  const ContextHint({
    required this.moodSuggestion,
    required this.recommendedScene,
    required this.topicHints,
  });

  factory ContextHint.fromJson(Map<String, dynamic> json) {
    return ContextHint(
      moodSuggestion: json['mood_suggestion'] as String? ?? '',
      recommendedScene: json['recommended_scene'] as String? ?? '',
      topicHints: (json['topic_hints'] as List?)?.cast<String>() ?? [],
    );
  }
}
