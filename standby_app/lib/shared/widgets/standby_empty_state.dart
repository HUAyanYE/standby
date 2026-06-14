import 'package:flutter/material.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

class StandbyEmptyState extends StatelessWidget {
  final String emoji;
  final String title;
  final String description;
  final String? actionLabel;
  final VoidCallback? onAction;

  const StandbyEmptyState({
    super.key,
    required this.emoji,
    required this.title,
    required this.description,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 24),
      decoration: BoxDecoration(
        color: context.surface1,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(color: context.borderColor),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 48)),
          const SizedBox(height: 16),
          Text(
            title,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: context.text2Color,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: TextStyle(
              fontSize: 14,
              color: context.text3Color,
              height: 1.8,
            ),
            textAlign: TextAlign.center,
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 24),
            GestureDetector(
              onTap: onAction,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                decoration: BoxDecoration(
                  color: context.surface2,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  actionLabel!,
                  style: TextStyle(fontSize: 14, color: context.text2Color),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
