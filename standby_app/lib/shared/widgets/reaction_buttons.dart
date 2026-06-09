import 'package:flutter/material.dart';
import '../../app/theme.dart';

/// 写感想入口组件 — 替代五态反应按钮
///
/// 设计理念：用户只管表达，系统自动推断反应类型
/// 单一入口，降低决策负担，鼓励真实表达
class ReactionEntry extends StatelessWidget {
  final VoidCallback onTap;

  const ReactionEntry({
    super.key,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        decoration: BoxDecoration(
          color: StandbyColors.primarySoft,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: StandbyColors.primary.withAlpha(80)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.edit_outlined,
              size: 20,
              color: StandbyColors.primary,
            ),
            const SizedBox(width: 8),
            Text(
              '写感想',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
                color: StandbyColors.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
