import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/media_service.dart';
import '../services/storage_service.dart';
import '../widgets/media_picker.dart';
import '../widgets/media_preview.dart';

/// 发布页面 — 统一入口 (用户创建 + 系统分享)
///
/// 设计哲学:
/// - 锚点先行: "什么触动了你？"
/// - 私密表达: "你的感受:"
/// - 话题自然: 文字中 # 自动识别
/// - 按钮文案: "记录这一刻"
class PublishScreen extends StatefulWidget {
  final ApiService api;
  final MediaService mediaService;
  final VoidCallback? onPublished;

  /// 系统分享传入的预填充数据
  final String? initialText;
  final File? initialMedia;
  final String? initialMediaUrl;
  final String? initialSource;

  const PublishScreen({
    super.key,
    required this.api,
    required this.mediaService,
    this.onPublished,
    this.initialText,
    this.initialMedia,
    this.initialMediaUrl,
    this.initialSource,
  });

  @override
  State<PublishScreen> createState() => _PublishScreenState();
}

class _PublishScreenState extends State<PublishScreen> {
  final TextEditingController _anchorController = TextEditingController();
  final TextEditingController _feelingController = TextEditingController();
  final _storage = StorageService();
  bool _publishing = false;

  // 媒体文件
  File? _mediaFile;
  String? _mediaType;
  String? _mimeType;

  // 从文本中提取的话题
  List<String> get _extractedTopics {
    final text = _feelingController.text;
    final topics = <String>[];
    final regex = RegExp(r'#([^\s#]+)');
    for (final match in regex.allMatches(text)) {
      topics.add(match.group(1)!);
    }
    return topics;
  }

  @override
  void initState() {
    super.initState();
    // 预填充系统分享的数据
    if (widget.initialText != null) {
      _anchorController.text = widget.initialText!;
    }
    if (widget.initialMedia != null) {
      _mediaFile = widget.initialMedia!;
      _mediaType = 'image'; // 默认
      _mimeType = 'image/jpeg';
    }
  }

  @override
  void dispose() {
    _anchorController.dispose();
    _feelingController.dispose();
    super.dispose();
  }

  /// 选择媒体
  void _onMediaPicked(MediaPickResult result) {
    setState(() {
      _mediaFile = result.file;
      _mediaType = result.type.name;
      _mimeType = result.mimeType;
    });
  }

  /// 删除媒体
  void _deleteMedia() {
    setState(() {
      _mediaFile = null;
      _mediaType = null;
      _mimeType = null;
    });
  }

  /// 记录这一刻
  Future<void> _publish() async {
    final anchorText = _anchorController.text.trim();
    final feelingText = _feelingController.text.trim();

    // 验证: 至少有锚点内容或感受
    if (anchorText.isEmpty && _mediaFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('请描述什么触动了你'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() => _publishing = true);

    try {
      String? mediaId;

      // 上传媒体文件
      if (_mediaFile != null) {
        final mediaInfo = MediaFileInfo(
          file: _mediaFile!,
          type: _mediaType == 'video' ? MediaType.video : MediaType.image,
          mimeType: _mimeType ?? 'image/jpeg',
          fileSizeBytes: await _mediaFile!.length(),
        );
        final uploadResult = await widget.mediaService.uploadMedia(mediaInfo);
        mediaId = uploadResult['media_id'] as String?;
      }

      // 确定模态类型
      String modality = 'text';
      if (mediaId != null && anchorText.isNotEmpty) {
        modality = 'mixed';
      } else if (mediaId != null) {
        modality = _mediaType ?? 'image';
      }

      // 创建锚点
      final result = await widget.api.createAnchor(
        modality: modality,
        textContent: anchorText.isNotEmpty ? anchorText : null,
        mediaIds: mediaId != null ? [mediaId] : null,
        topics: _extractedTopics,
        source: widget.initialSource ?? 'user',
      );

      final anchorId = result['anchor_id'] as String? ?? '';

      // 保存到本地记录
      await _storage.addMyPost({
        'anchor_text': anchorText,
        'feeling': feelingText,
        'topics': _extractedTopics,
        'anchor_id': anchorId,
        'has_media': mediaId != null,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('已记录'),
            backgroundColor: Colors.green,
          ),
        );

        widget.onPublished?.call();
        Navigator.pop(context);
      }
    } catch (e) {
      print('记录失败: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('记录失败: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _publishing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('记录'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ============================================================
            // 锚点区域: "什么触动了你？"
            // ============================================================
            _buildSectionTitle('什么触动了你？', Icons.touch_app_outlined),
            const SizedBox(height: 12),

            // 媒体选择
            if (_mediaFile == null)
              MediaPicker(
                mediaService: widget.mediaService,
                onMediaPicked: _onMediaPicked,
              )
            else
              MediaPreview(
                media: _mediaFile!,
                isLocal: true,
                onDelete: _deleteMedia,
                height: 200,
              ),

            const SizedBox(height: 16),

            // 锚点文本输入
            TextField(
              controller: _anchorController,
              maxLines: 4,
              decoration: InputDecoration(
                hintText: '描述你看到/听到/感受到的东西...\n例如: 公园里的一对老夫妻在长椅上打盹',
                hintStyle: TextStyle(color: Colors.grey.shade400),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                contentPadding: const EdgeInsets.all(16),
                filled: true,
                fillColor: Colors.grey.shade50,
              ),
            ),

            const SizedBox(height: 24),
            Divider(color: Colors.grey.shade300),
            const SizedBox(height: 24),

            // ============================================================
            // 感受区域: "你的感受:"
            // ============================================================
            _buildSectionTitle('你的感受:', Icons.edit_outlined),
            const SizedBox(height: 12),

            TextField(
              controller: _feelingController,
              maxLines: 6,
              decoration: InputDecoration(
                hintText: '写下你的感受...\n\n输入 # 添加话题，例如: #夕阳 #爱情',
                hintStyle: TextStyle(color: Colors.grey.shade400),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                contentPadding: const EdgeInsets.all(16),
              ),
              onChanged: (_) => setState(() {}), // 触发话题提取
            ),

            // 显示提取的话题
            if (_extractedTopics.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _extractedTopics.map((topic) {
                  return Chip(
                    label: Text('#$topic'),
                    backgroundColor: Colors.indigo.shade50,
                    labelStyle: TextStyle(color: Colors.indigo.shade700),
                  );
                }).toList(),
              ),
            ],

            const SizedBox(height: 32),

            // ============================================================
            // 记录按钮
            // ============================================================
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _publishing ? null : _publish,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.indigo,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _publishing
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        '✨ 记录这一刻',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
            ),

            const SizedBox(height: 16),

            // 私密提示
            Center(
              child: Text(
                '这是私密的表达，等待与你共鸣的人。',
                style: TextStyle(
                  fontSize: 13,
                  color: Colors.grey.shade500,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 18, color: Colors.indigo),
        const SizedBox(width: 8),
        Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
