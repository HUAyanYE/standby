/// 媒体选择器组件 — 选择/拍摄图片、视频、音频

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/media_service.dart';

/// 媒体选择结果
class MediaPickResult {
  final File file;
  final MediaType type;
  final String mimeType;

  const MediaPickResult({
    required this.file,
    required this.type,
    required this.mimeType,
  });
}

/// 媒体选择器组件
class MediaPicker extends StatelessWidget {
  final MediaService mediaService;
  final Function(MediaPickResult) onMediaPicked;
  final List<MediaType> allowedTypes;

  const MediaPicker({
    super.key,
    required this.mediaService,
    required this.onMediaPicked,
    this.allowedTypes = const [MediaType.image, MediaType.audio, MediaType.video],
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (allowedTypes.contains(MediaType.image))
          _buildButton(
            context,
            icon: Icons.image_outlined,
            label: '图片',
            onTap: () => _showImageOptions(context),
          ),
        if (allowedTypes.contains(MediaType.audio)) ...[
          const SizedBox(width: 16),
          _buildButton(
            context,
            icon: Icons.mic_outlined,
            label: '音频',
            onTap: () => _pickAudio(context),
          ),
        ],
        if (allowedTypes.contains(MediaType.video)) ...[
          const SizedBox(width: 16),
          _buildButton(
            context,
            icon: Icons.videocam_outlined,
            label: '视频',
            onTap: () => _showVideoOptions(context),
          ),
        ],
      ],
    );
  }

  Widget _buildButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 20, color: Colors.grey.shade600),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 显示图片选项 (相册/拍摄)
  void _showImageOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('从相册选择'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('拍摄照片'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
          ],
        ),
      ),
    );
  }

  /// 显示视频选项 (相册/录制)
  void _showVideoOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.video_library),
              title: const Text('从相册选择'),
              onTap: () {
                Navigator.pop(context);
                _pickVideo(ImageSource.gallery);
              },
            ),
            ListTile(
              leading: const Icon(Icons.videocam),
              title: const Text('录制视频'),
              onTap: () {
                Navigator.pop(context);
                _pickVideo(ImageSource.camera);
              },
            ),
          ],
        ),
      ),
    );
  }

  /// 选择图片
  Future<void> _pickImage(ImageSource source) async {
    final MediaFileInfo? result;
    if (source == ImageSource.gallery) {
      result = await mediaService.pickImage();
    } else {
      result = await mediaService.takePhoto();
    }

    if (result != null) {
      onMediaPicked(MediaPickResult(
        file: result.file,
        type: result.type,
        mimeType: result.mimeType,
      ));
    }
  }

  /// 选择视频
  Future<void> _pickVideo(ImageSource source) async {
    final MediaFileInfo? result;
    if (source == ImageSource.gallery) {
      result = await mediaService.pickVideo();
    } else {
      result = await mediaService.recordVideo();
    }

    if (result != null) {
      onMediaPicked(MediaPickResult(
        file: result.file,
        type: result.type,
        mimeType: result.mimeType,
      ));
    }
  }

  /// 录制音频
  Future<void> _pickAudio(BuildContext context) async {
    // TODO: 实现音频录制
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('音频录制功能开发中')),
    );
  }
}
