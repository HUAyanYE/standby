import 'dart:io';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/seedstone.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

class MediaPreview extends StatelessWidget {
  final dynamic media;
  final bool isLocal;
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

  Widget _buildImagePreview(BuildContext context, {File? file, MediaRef? mediaRef}) {
    return Stack(
      children: [
        Container(
          width: width ?? double.infinity,
          height: height ?? 200,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(StandbyRadius.xl),
            color: context.surface2,
          ),
          clipBehavior: Clip.antiAlias,
          child: file != null
              ? Image.file(
                  file,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) =>
                      _buildErrorWidget(context, '图片加载失败'),
                )
              : CachedNetworkImage(
                  imageUrl: mediaRef?.storageUrl ?? '',
                  fit: BoxFit.cover,
                  placeholder: (context, url) => Center(
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: context.text3Color,
                    ),
                  ),
                  errorWidget: (context, url, error) =>
                      _buildErrorWidget(context, '图片加载失败'),
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

  Widget _buildAudioPreview(BuildContext context, {MediaRef? mediaRef}) {
    return Container(
      width: width ?? double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(StandbyRadius.xl),
        color: StandbyColors.primarySoft,
        border: Border.all(color: StandbyColors.primary.withAlpha(40)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: StandbyColors.primarySoft,
            ),
            child: const Icon(
              Icons.music_note,
              color: StandbyColors.primary,
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
                    color: context.textColor,
                  ),
                ),
                if (mediaRef?.durationSeconds != null)
                  Text(
                    _formatDuration(mediaRef!.durationSeconds!),
                    style: TextStyle(
                      fontSize: 12,
                      color: context.text3Color,
                    ),
                  ),
              ],
            ),
          ),
          const Icon(
            Icons.play_circle_outline,
            color: StandbyColors.primary,
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

  Widget _buildVideoPreview(BuildContext context, {MediaRef? mediaRef}) {
    return Stack(
      children: [
        Container(
          width: width ?? double.infinity,
          height: height ?? 200,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(StandbyRadius.xl),
            color: context.surface2,
          ),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.play_circle_fill,
                  size: 48,
                  color: context.text2Color,
                ),
                const SizedBox(height: 8),
                Text(
                  '视频',
                  style: TextStyle(
                    fontSize: 14,
                    color: context.text2Color,
                  ),
                ),
                if (mediaRef?.durationSeconds != null)
                  Text(
                    _formatDuration(mediaRef!.durationSeconds!),
                    style: TextStyle(
                      fontSize: 12,
                      color: context.text3Color,
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

  Widget _buildGenericPreview(BuildContext context, String label) {
    return Container(
      width: width ?? double.infinity,
      height: height ?? 100,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(StandbyRadius.xl),
        color: context.surface2,
        border: Border.all(color: context.borderColor),
      ),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.attach_file, color: context.text3Color),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(color: context.text2Color),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorWidget(BuildContext context, String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.broken_image, color: context.text3Color, size: 32),
          const SizedBox(height: 4),
          Text(
            message,
            style: TextStyle(fontSize: 12, color: context.text3Color),
          ),
        ],
      ),
    );
  }

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

  String _formatDuration(double seconds) {
    final duration = Duration(milliseconds: (seconds * 1000).round());
    final minutes = duration.inMinutes;
    final secs = duration.inSeconds % 60;
    return '$minutes:${secs.toString().padLeft(2, '0')}';
  }
}
