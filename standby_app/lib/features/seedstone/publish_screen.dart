import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../../shared/services/api_service.dart';
import '../../shared/services/media_service.dart';
import '../../shared/services/storage_service.dart';
import '../../shared/widgets/media_preview.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

/// 发布页 — 创建心物/感想
class PublishScreen extends ConsumerStatefulWidget {
  const PublishScreen({super.key});

  @override
  ConsumerState<PublishScreen> createState() => _PublishScreenState();
}

class _PublishScreenState extends ConsumerState<PublishScreen> {
  final _api = ApiService();
  final _mediaService = MediaService(ApiService());
  final _storage = StorageService();
  final _anchorController = TextEditingController();
  final _feelingController = TextEditingController();
  final _topicController = TextEditingController();
  final _imagePicker = ImagePicker();
  
  List<String> _topics = [];
  List<File> _mediaFiles = [];
  bool _publishing = false;

  @override
  void dispose() {
    _anchorController.dispose();
    _feelingController.dispose();
    _topicController.dispose();
    super.dispose();
  }

  void _addTopic(String topic) {
    final trimmed = topic.trim();
    if (trimmed.isNotEmpty && !_topics.contains(trimmed) && _topics.length < 5) {
      setState(() {
        _topics.add(trimmed);
        _topicController.clear();
      });
    }
  }

  void _removeTopic(String topic) {
    setState(() => _topics.remove(topic));
  }

  Future<void> _pickImage() async {
    final XFile? image = await _imagePicker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() => _mediaFiles.add(File(image.path)));
    }
  }

  void _removeMedia(int index) {
    setState(() => _mediaFiles.removeAt(index));
  }

  Future<void> _publish() async {
    final anchorText = _anchorController.text.trim();
    final feelingText = _feelingController.text.trim();

    if (anchorText.isEmpty && _mediaFiles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请写下什么触动了你')),
      );
      return;
    }

    setState(() => _publishing = true);

    try {
      // 上传媒体文件
      List<String> mediaIds = [];
      for (final file in _mediaFiles) {
        try {
          final mediaInfo = MediaFileInfo(
            file: file,
            type: MediaType.image,
            mimeType: 'image/jpeg',
            fileSizeBytes: file.lengthSync(),
          );
          final result = await _mediaService.uploadMedia(mediaInfo);
          if (result['media_id'] != null) {
            mediaIds.add(result['media_id'] as String);
          }
        } catch (e) {
          debugPrint('媒体上传失败: $e');
        }
      }

      // 自动提取话题
      if (_topics.isEmpty && anchorText.isNotEmpty) {
        _extractTopics(anchorText);
      }

      // 创建心物
      String modality = 'text';
      if (mediaIds.isNotEmpty && anchorText.isNotEmpty) {
        modality = 'mixed';
      } else if (mediaIds.isNotEmpty) {
        modality = 'image';
      }

      final result = await _api.createAnchor(
        sourceTexts: anchorText.isNotEmpty ? [anchorText] : [' '],
        topicHints: _topics.isNotEmpty ? _topics : null,
        modality: modality,
      );

      // 如果有感想，提交反应
      if (feelingText.isNotEmpty && result['anchor_id'] != null) {
        await _api.submitReaction(
          anchorId: result['anchor_id'] as String,
          reactionType: 1,
          opinionText: feelingText,
        );
      }

      // 保存到本地
      await _storage.addMyPost({
        'anchor_id': result['anchor_id'] ?? '',
        'scene': anchorText,
        'content': feelingText,
        'topics': _topics,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('已发布')),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('发布失败: $e'), backgroundColor: StandbyColors.primary),
        );
      }
    } finally {
      setState(() => _publishing = false);
    }
  }

  void _extractTopics(String text) {
    final regex = RegExp(r'#(\S+)');
    final matches = regex.allMatches(text);
    for (final match in matches) {
      final topic = match.group(1)!;
      if (!_topics.contains(topic) && _topics.length < 5) {
        _topics.add(topic);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('发布'),
        actions: [
          TextButton(
            onPressed: _publishing ? null : _publish,
            child: _publishing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('发布', style: TextStyle(color: StandbyColors.primary)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: StandbySpacing.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('什么触动了你?', style: StandbyTextStyles.h3),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: context.surface1,
                borderRadius: StandbyRadius.cardRadius,
                border: Border.all(color: context.borderColor),
              ),
              child: TextField(
                controller: _anchorController,
                maxLines: 5,
                style: StandbyTextStyles.body,
                decoration: InputDecoration(
                  hintText: '写下触动你的事物...',
                  hintStyle: TextStyle(color: context.text3Color),
                  border: InputBorder.none,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 媒体选择
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ..._mediaFiles.asMap().entries.map((entry) {
                  return Stack(
                    children: [
                      MediaPreview(
                        media: entry.value,
                        isLocal: true,
                        height: 100,
                        width: 100,
                      ),
                      Positioned(
                        top: 0,
                        right: 0,
                        child: GestureDetector(
                          onTap: () => _removeMedia(entry.key),
                          child: Container(
                            padding: const EdgeInsets.all(4),
                            decoration: const BoxDecoration(
                              color: StandbyColors.primary,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.close, size: 14, color: Colors.white),
                          ),
                        ),
                      ),
                    ],
                  );
                }),
                GestureDetector(
                  onTap: _pickImage,
                  child: Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      color: context.surface2,
                      borderRadius: StandbyRadius.buttonRadius,
                      border: Border.all(color: context.borderColor),
                    ),
                    child: Icon(Icons.add_photo_alternate_outlined, color: context.text3Color),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // 话题标签
            Text('话题标签', style: StandbyTextStyles.h3),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ..._topics.map((topic) => Chip(
                  label: Text('#$topic'),
                  onDeleted: () => _removeTopic(topic),
                  backgroundColor: context.surface2,
                  labelStyle: const TextStyle(color: StandbyColors.primary),
                  deleteIconColor: context.text3Color,
                )),
                if (_topics.length < 5)
                  SizedBox(
                    width: 120,
                    child: TextField(
                      controller: _topicController,
                      style: TextStyle(fontSize: 14, color: context.textColor),
                      decoration: InputDecoration(
                        hintText: '添加话题',
                        hintStyle: TextStyle(color: context.text3Color, fontSize: 14),
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        border: OutlineInputBorder(
                          borderRadius: StandbyRadius.tagRadius,
                          borderSide: BorderSide(color: context.borderColor),
                        ),
                      ),
                      onSubmitted: _addTopic,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 32),

            Text('你的感受:', style: StandbyTextStyles.h3),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: context.surface2,
                borderRadius: StandbyRadius.cardRadius,
                border: Border.all(color: StandbyColors.primarySoft),
              ),
              child: TextField(
                controller: _feelingController,
                maxLines: 3,
                style: StandbyTextStyles.body,
                decoration: InputDecoration(
                  hintText: '写下你的感受（可选）...',
                  hintStyle: TextStyle(color: context.text3Color),
                  border: InputBorder.none,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
