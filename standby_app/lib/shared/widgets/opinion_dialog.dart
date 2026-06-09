import 'package:flutter/material.dart';
import '../../app/theme.dart';

/// 感想输入对话框
///
/// 设计理念：用户只管写感想，系统自动推断反应类型
class OpinionDialog extends StatefulWidget {
  final String anchorText;

  const OpinionDialog({
    super.key,
    required this.anchorText,
  });

  /// 显示感想对话框
  static Future<String?> show({
    required BuildContext context,
    required String anchorText,
  }) {
    return showDialog<String>(
      context: context,
      builder: (_) => OpinionDialog(
        anchorText: anchorText,
      ),
    );
  }

  @override
  State<OpinionDialog> createState() => _OpinionDialogState();
}

class _OpinionDialogState extends State<OpinionDialog> {
  final TextEditingController _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text.trim();
    Navigator.pop(context, text);
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: StandbyColors.surface1,
      shape: RoundedRectangleBorder(borderRadius: StandbyRadius.cardRadius),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 标题
            const Text(
              '写下你的感想',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: StandbyColors.text,
              ),
            ),
            const SizedBox(height: 8),

            // 心物预览
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: StandbyColors.surface2,
                borderRadius: BorderRadius.circular(StandbyRadius.sm),
              ),
              child: Text(
                widget.anchorText.length > 100
                    ? '${widget.anchorText.substring(0, 100)}...'
                    : widget.anchorText,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.5,
                  color: StandbyColors.text2,
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: 16),

            // 提示文字
            Text(
              '你的感想将以匿名方式展示。',
              style: TextStyle(fontSize: 12, color: StandbyColors.text3),
            ),
            const SizedBox(height: 12),

            // 输入框
            TextField(
              controller: _controller,
              maxLines: 5,
              maxLength: 500,
              autofocus: true,
              style: const TextStyle(color: StandbyColors.text),
              decoration: InputDecoration(
                hintText: '写下你的感想...',
                hintStyle: TextStyle(color: StandbyColors.text3),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(StandbyRadius.md),
                  borderSide: const BorderSide(color: StandbyColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(StandbyRadius.md),
                  borderSide: const BorderSide(color: StandbyColors.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(StandbyRadius.md),
                  borderSide: const BorderSide(color: StandbyColors.primary),
                ),
                contentPadding: const EdgeInsets.all(16),
                filled: true,
                fillColor: StandbyColors.surface2,
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
                    onPressed: () => Navigator.pop(context, ''),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: const BorderSide(color: StandbyColors.border),
                      shape: RoundedRectangleBorder(
                        borderRadius: StandbyRadius.buttonRadius,
                      ),
                    ),
                    child: const Text('跳过', style: TextStyle(color: StandbyColors.text2)),
                  ),
                ),
                const SizedBox(width: 12),

                // 提交按钮
                Expanded(
                  child: ElevatedButton(
                    onPressed: _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: StandbyColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: StandbyRadius.buttonRadius,
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
}
