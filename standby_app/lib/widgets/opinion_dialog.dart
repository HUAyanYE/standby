import 'package:flutter/material.dart';

/// 评论输入对话框
class OpinionDialog extends StatefulWidget {
  final String anchorText;
  final String emotionWord;
  final String reactionType;

  const OpinionDialog({
    super.key,
    required this.anchorText,
    required this.emotionWord,
    required this.reactionType,
  });

  /// 显示评论对话框
  static Future<String?> show({
    required BuildContext context,
    required String anchorText,
    required String emotionWord,
    required String reactionType,
  }) {
    return showDialog<String>(
      context: context,
      builder: (_) => OpinionDialog(
        anchorText: anchorText,
        emotionWord: emotionWord,
        reactionType: reactionType,
      ),
    );
  }

  @override
  State<OpinionDialog> createState() => _OpinionDialogState();
}

class _OpinionDialogState extends State<OpinionDialog> {
  final TextEditingController _controller = TextEditingController();
  bool _skipComment = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    if (_skipComment) {
      Navigator.pop(context, ''); // 返回空字符串表示跳过评论
    } else {
      final text = _controller.text.trim();
      Navigator.pop(context, text.isEmpty ? '' : text);
    }
  }

  /// 根据反应类型获取标题
  String _getTitle() {
    switch (widget.reactionType) {
      case '未体验':
      case '有害':
        return '为什么这么觉得？';
      default:
        return '写下你的感想（可选）';
    }
  }

  /// 根据反应类型获取提示文字
  String _getHint() {
    switch (widget.reactionType) {
      case '未体验':
        return '说说为什么你没有相关的体验...';
      case '有害':
        return '说说为什么你觉得这个内容有害...';
      default:
        return '写下你的感想...';
    }
  }

  /// 根据反应类型获取说明文字
  String _getDescription() {
    switch (widget.reactionType) {
      case '未体验':
        return '你的反馈将帮助其他人理解不同的视角。';
      case '有害':
        return '你的反馈将帮助我们改进内容质量。';
      default:
        return '你的感想将以匿名方式展示，帮助其他人理解这种共鸣。';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 反应信息
            Row(
              children: [
                _getReactionEmoji(),
                const SizedBox(width: 8),
                Text(
                  widget.emotionWord.isNotEmpty
                      ? '${widget.reactionType} · ${widget.emotionWord}'
                      : widget.reactionType,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey.shade600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // 锚点预览
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                widget.anchorText.length > 100
                    ? '${widget.anchorText.substring(0, 100)}...'
                    : widget.anchorText,
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.5,
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: 16),

            // 标题（根据反应类型变化）
            Text(
              _getTitle(),
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),

            // 提示文字
            Text(
              _getDescription(),
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade500,
              ),
            ),
            const SizedBox(height: 16),

            // 输入框
            TextField(
              controller: _controller,
              maxLines: 4,
              maxLength: 500,
              decoration: InputDecoration(
                hintText: _getHint(),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                contentPadding: const EdgeInsets.all(16),
              ),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 16),

            // 按钮组
            Row(
              children: [
                // 跳过按钮
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      setState(() => _skipComment = true);
                      _submit();
                    },
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text('跳过'),
                  ),
                ),
                const SizedBox(width: 12),

                // 提交按钮
                Expanded(
                  child: ElevatedButton(
                    onPressed: _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.indigo,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      '提交',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _getReactionEmoji() {
    switch (widget.reactionType) {
      case '共鸣':
        return const Text('❤️', style: TextStyle(fontSize: 20));
      case '无感':
        return const Text('😐', style: TextStyle(fontSize: 20));
      case '反对':
        return const Text('👎', style: TextStyle(fontSize: 20));
      case '未体验':
        return const Text('❓', style: TextStyle(fontSize: 20));
      case '有害':
        return const Text('⚠️', style: TextStyle(fontSize: 20));
      default:
        return const Text('💭', style: TextStyle(fontSize: 20));
    }
  }
}
