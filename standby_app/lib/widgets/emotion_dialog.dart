import 'package:flutter/material.dart';

/// 情绪词选择结果
class EmotionResult {
  final String? emotionWord; // 同感/触发/启发/震撼，或 null（跳过）

  EmotionResult({this.emotionWord});
}

/// 情绪词弹窗
class EmotionDialog extends StatelessWidget {
  const EmotionDialog({super.key});

  /// 显示情绪词选择弹窗
  static Future<EmotionResult?> show(BuildContext context) {
    return showModalBottomSheet<EmotionResult>(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => const EmotionDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 标题
          Text(
            '你的共鸣是……',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),

          // 情绪词网格
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 2.5,
            children: [
              _buildEmotionButton(context, '同感', '🤝', '我也这么想'),
              _buildEmotionButton(context, '触发', '⚡', '被说中了'),
              _buildEmotionButton(context, '启发', '💡', '有了新想法'),
              _buildEmotionButton(context, '震撼', '💫', '直击心灵'),
            ],
          ),
          const SizedBox(height: 16),

          // 跳过按钮
          TextButton(
            onPressed: () => Navigator.pop(context, EmotionResult()),
            child: Text(
              '跳过',
              style: TextStyle(color: Colors.grey.shade600),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  Widget _buildEmotionButton(
    BuildContext context,
    String emotion,
    String emoji,
    String subtitle,
  ) {
    return InkWell(
      onTap: () => Navigator.pop(context, EmotionResult(emotionWord: emotion)),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          color: Colors.indigo.shade50,
          border: Border.all(color: Colors.indigo.shade100),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('$emoji $emotion', style: const TextStyle(fontSize: 16)),
            Text(
              subtitle,
              style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
            ),
          ],
        ),
      ),
    );
  }
}
