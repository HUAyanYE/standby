/// 媒体预览组件 — 显示图片、音频、视频预览

import 'dart:io';
import 'package:flutter/material.dart';
import '../models/anchor.dart';

/// 媒体预览组件
class MediaPreview extends StatelessWidget {
  final dynamic media; // MediaRef 或 File
  final bool isLocal; // 是否本地文件
  final VoidCallback? onDelete;
  final double? width;
  final double? height;

  const MediaPreview({
    super.key,
    required this.media,
    this.isLocal = false,
    this.onDelete,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    if (isLocal && media is File) {
      return _buildLocalPreview(context, media as File);
    } else if (media is MediaRef) {
      return _buildRemotePreview(context, media as MediaRef);
    }
    return const SizedBox.shrink();
  }

  /// 本地文件预览
  Widget _buildLocalPreview(BuildContext context, File file) {
    final path = file.path.toLowerCase();
    if (path.endsWith('.jpg') || path.endsWith('.jpeg') || path.endsWith('.png') || path.endsWith('.webp')) {
      return _buildImagePreview(context, file: file);
    } else if (path.endsWith('.mp3') || path.endsWith('.aac') || path.endsWith('.m4a') || path.endsWith('.wav')) {
      return _buildAudioPreview(context);
    } else if (path.endsWith('.mp4') || path.endsWith('.mov')) {
      return _buildVideoPreview(context);
    }
    return _buildGenericPreview(context, '文件');
  }

  /// 远程媒体预览
  Widget _buildRemotePreview(BuildContext context, MediaRef mediaRef) {
    switch (mediaRef.mediaType) {
      case 'image':
        return _buildImagePreview(context, mediaRef: mediaRef);
      case 'audio':
        return _buildAudioPreview(context, mediaRef: mediaRef);
      case 'video':
        return _buildVideoPreview(context, mediaRef: mediaRef);
      default:
        return _buildGenericPreview(context, '媒体');
    }
  }

  /// 图片预览
  Widget _buildImagePreview(
    BuildContext context, {
    File? file,
    MediaRef? mediaRef,
  }) {
    return Stack(
      children: [
        Container(
          width: width ?? double.infinity,
          height: height ?? 200,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: Colors.grey.shade200,
          ),
          clipBehavior: Clip.antiAlias,
          child: file != null
              ? Image.file(
                  file,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) =>
                      _buildErrorWidget('图片加载失败'),
                )
              : Image.network(
                  mediaRef?.storageUrl ?? '',
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) =>
                      _buildErrorWidget('图片加载失败'),
                ),
        ),
        if (onDelete != null)
          Positioned(
            top: 8,
            right: 8,
            child: _buildDeleteButton(),
          ),
      ],
    );
  }

  /// 音频预览
  Widget _buildAudioPreview(BuildContext context, {MediaRef? mediaRef}) {
    return Container(
      width: width ?? double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.indigo.shade50,
        border: Border.all(color: Colors.indigo.shade200),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.indigo.shade100,
            ),
            child: Icon(
              Icons.music_note,
              color: Colors.indigo.shade400,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '音频',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: Colors.indigo.shade700,
                  ),
                ),
                if (mediaRef?.durationSeconds != null)
                  Text(
                    _formatDuration(mediaRef!.durationSeconds!),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.indigo.shade400,
                    ),
                  ),
              ],
            ),
          ),
          Icon(
            Icons.play_circle_outline,
            color: Colors.indigo.shade400,
            size: 32,
          ),
          if (onDelete != null) ...[
            const SizedBox(width: 8),
            _buildDeleteButton(),
          ],
        ],
      ),
    );
  }

  /// 视频预览
  Widget _buildVideoPreview(BuildContext context, {MediaRef? mediaRef}) {
    return Stack(
      children: [
        Container(
          width: width ?? double.infinity,
          height: height ?? 200,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: Colors.grey.shade900,
          ),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.play_circle_fill,
                  size: 48,
                  color: Colors.white.withOpacity(0.8),
                ),
                const SizedBox(height: 8),
                Text(
                  '视频',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.white.withOpacity(0.8),
                  ),
                ),
                if (mediaRef?.durationSeconds != null)
                  Text(
                    _formatDuration(mediaRef!.durationSeconds!),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.white.withOpacity(0.6),
                    ),
                  ),
              ],
            ),
          ),
        ),
        if (onDelete != null)
          Positioned(
            top: 8,
            right: 8,
            child: _buildDeleteButton(),
          ),
      ],
    );
  }

  /// 通用预览
  Widget _buildGenericPreview(BuildContext context, String label) {
    return Container(
      width: width ?? double.infinity,
      height: height ?? 100,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.grey.shade100,
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.attach_file, color: Colors.grey.shade400),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }

  /// 错误组件
  Widget _buildErrorWidget(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.broken_image, color: Colors.grey.shade400, size: 32),
          const SizedBox(height: 4),
          Text(
            message,
            style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
          ),
        ],
      ),
    );
  }

  /// 删除按钮
  Widget _buildDeleteButton() {
    return GestureDetector(
      onTap: onDelete,
      child: Container(
        width: 24,
        height: 24,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.black.withOpacity(0.5),
        ),
        child: const Icon(
          Icons.close,
          size: 16,
          color: Colors.white,
        ),
      ),
    );
  }

  /// 格式化时长
  String _formatDuration(double seconds) {
    final duration = Duration(milliseconds: (seconds * 1000).round());
    final minutes = duration.inMinutes;
    final secs = duration.inSeconds % 60;
    return '$minutes:${secs.toString().padLeft(2, '0')}';
  }
}
