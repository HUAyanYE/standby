/// 媒体服务 — 处理图片/音频/视频的选择、压缩、上传

import 'dart:io';
import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import 'api_service.dart';

/// 媒体类型
enum MediaType {
  image,
  audio,
  video,
}

/// 媒体文件信息
class MediaFileInfo {
  final File file;
  final MediaType type;
  final String mimeType;
  final int fileSizeBytes;

  const MediaFileInfo({
    required this.file,
    required this.type,
    required this.mimeType,
    required this.fileSizeBytes,
  });
}

/// 媒体服务
class MediaService {
  final ApiService _api;
  final ImagePicker _picker = ImagePicker();

  MediaService(this._api);

  /// 从相册选择图片
  Future<MediaFileInfo?> pickImage() async {
    final xFile = await _picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );
    if (xFile == null) return null;

    final file = File(xFile.path);
    final size = await file.length();
    return MediaFileInfo(
      file: file,
      type: MediaType.image,
      mimeType: 'image/jpeg',
      fileSizeBytes: size,
    );
  }

  /// 拍摄照片
  Future<MediaFileInfo?> takePhoto() async {
    final xFile = await _picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );
    if (xFile == null) return null;

    final file = File(xFile.path);
    final size = await file.length();
    return MediaFileInfo(
      file: file,
      type: MediaType.image,
      mimeType: 'image/jpeg',
      fileSizeBytes: size,
    );
  }

  /// 从相册选择视频
  Future<MediaFileInfo?> pickVideo() async {
    final xFile = await _picker.pickVideo(
      source: ImageSource.gallery,
      maxDuration: const Duration(minutes: 5),
    );
    if (xFile == null) return null;

    final file = File(xFile.path);
    final size = await file.length();
    return MediaFileInfo(
      file: file,
      type: MediaType.video,
      mimeType: 'video/mp4',
      fileSizeBytes: size,
    );
  }

  /// 录制视频
  Future<MediaFileInfo?> recordVideo() async {
    final xFile = await _picker.pickVideo(
      source: ImageSource.camera,
      maxDuration: const Duration(minutes: 5),
    );
    if (xFile == null) return null;

    final file = File(xFile.path);
    final size = await file.length();
    return MediaFileInfo(
      file: file,
      type: MediaType.video,
      mimeType: 'video/mp4',
      fileSizeBytes: size,
    );
  }

  /// 录制音频 (需要 record 插件)
  Future<MediaFileInfo?> recordAudio() async {
    // TODO: 实现音频录制
    // 需要 record 插件
    return null;
  }

  /// 上传媒体文件到服务器
  Future<Map<String, dynamic>> uploadMedia(MediaFileInfo mediaInfo) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        mediaInfo.file.path,
        filename: mediaInfo.file.path.split('/').last,
      ),
      'media_type': mediaInfo.type.name,
    });

    final resp = await _api.dio.post(
      '/media/upload',
      data: formData,
    );

    return resp.data as Map<String, dynamic>;
  }

  /// 上传多个媒体文件
  Future<List<Map<String, dynamic>>> uploadMultiple(
    List<MediaFileInfo> files,
  ) async {
    final results = <Map<String, dynamic>>[];
    for (final file in files) {
      final result = await uploadMedia(file);
      results.add(result);
    }
    return results;
  }

  /// 获取媒体文件的 MIME 类型
  static String getMimeType(String filePath) {
    final ext = filePath.split('.').last.toLowerCase();
    switch (ext) {
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      case 'gif':
        return 'image/gif';
      case 'webp':
        return 'image/webp';
      case 'mp3':
        return 'audio/mpeg';
      case 'aac':
        return 'audio/aac';
      case 'm4a':
        return 'audio/mp4';
      case 'wav':
        return 'audio/wav';
      case 'mp4':
        return 'video/mp4';
      case 'mov':
        return 'video/quicktime';
      case 'avi':
        return 'video/x-msvideo';
      default:
        return 'application/octet-stream';
    }
  }

  /// 根据 MIME 类型判断媒体类型
  static MediaType getMediaType(String mimeType) {
    if (mimeType.startsWith('image/')) return MediaType.image;
    if (mimeType.startsWith('audio/')) return MediaType.audio;
    if (mimeType.startsWith('video/')) return MediaType.video;
    return MediaType.image; // 默认
  }
}
