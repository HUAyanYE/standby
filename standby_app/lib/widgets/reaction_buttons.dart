import 'package:flutter/material.dart';

/// 反应类型
enum ReactionType {
  resonance,  // 共鸣
  neutral,    // 无感
  opposition, // 反对
  unexperienced, // 未体验
  harmful,    // 有害
}

/// 五态反应按钮组件
class ReactionButtons extends StatelessWidget {
  final ReactionType? selectedReaction;
  final Map<ReactionType, int> counts;
  final Function(ReactionType) onReaction;
  final Function()? onResonance; // 点击共鸣时的特殊处理

  const ReactionButtons({
    super.key,
    this.selectedReaction,
    required this.counts,
    required this.onReaction,
    this.onResonance,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // 共鸣按钮（最大）
        _buildResonanceButton(context),
        const SizedBox(height: 16),
        // 其他四个按钮
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildNormalButton(context, ReactionType.neutral, '😐', '无感', 56),
            const SizedBox(width: 12),
            _buildNormalButton(context, ReactionType.opposition, '👎', '反对', 56),
            const SizedBox(width: 12),
            _buildNormalButton(context, ReactionType.unexperienced, '❓', '未体验', 56),
            const SizedBox(width: 12),
            _buildHarmfulButton(context),
          ],
        ),
      ],
    );
  }

  /// 共鸣按钮（最大）
  Widget _buildResonanceButton(BuildContext context) {
    final isSelected = selectedReaction == ReactionType.resonance;
    final count = counts[ReactionType.resonance] ?? 0;

    return GestureDetector(
      onTap: () {
        if (isSelected) {
          onReaction(ReactionType.resonance); // 取消
        } else {
          onResonance?.call(); // 弹出情绪词选择
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 80,
        height: 80,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: isSelected ? Colors.red.shade100 : Colors.red.shade50,
          border: Border.all(
            color: isSelected ? Colors.red : Colors.red.shade200,
            width: isSelected ? 3 : 1,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('❤️', style: TextStyle(fontSize: 28)),
            Text(
              '共鸣',
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: Colors.red.shade700,
              ),
            ),
            if (count > 0)
              Text(
                '$count+',
                style: TextStyle(
                  fontSize: 10,
                  color: Colors.red.shade400,
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// 普通反应按钮
  Widget _buildNormalButton(
    BuildContext context,
    ReactionType type,
    String emoji,
    String label,
    double size,
  ) {
    final isSelected = selectedReaction == type;
    final count = counts[type] ?? 0;

    Color getColor() {
      switch (type) {
        case ReactionType.neutral:
          return Colors.grey;
        case ReactionType.opposition:
          return Colors.blueGrey;
        case ReactionType.unexperienced:
          return Colors.grey.shade300;
        default:
          return Colors.grey;
      }
    }

    return GestureDetector(
      onTap: () => onReaction(type),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: size,
        height: size,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          color: isSelected ? getColor().withOpacity(0.2) : getColor().withOpacity(0.05),
          border: Border.all(
            color: isSelected ? getColor() : getColor().withOpacity(0.3),
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(emoji, style: const TextStyle(fontSize: 20)),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: getColor(),
              ),
            ),
            if (count > 0)
              Text(
                '$count+',
                style: TextStyle(
                  fontSize: 8,
                  color: getColor().withOpacity(0.7),
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// 有害按钮（更小更暗，只显示图标）
  Widget _buildHarmfulButton(BuildContext context) {
    final isSelected = selectedReaction == ReactionType.harmful;

    return GestureDetector(
      onTap: () => onReaction(ReactionType.harmful),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: isSelected ? Colors.grey.shade400 : Colors.grey.shade200,
          border: Border.all(
            color: isSelected ? Colors.grey.shade600 : Colors.grey.shade300,
            width: 1,
          ),
        ),
        child: Center(
          child: Text(
            '⚠️',
            style: TextStyle(
              fontSize: 14,
              color: isSelected ? Colors.grey.shade800 : Colors.grey.shade500,
            ),
          ),
        ),
      ),
    );
  }
}
