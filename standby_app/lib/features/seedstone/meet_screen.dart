import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/providers/seedstone_provider.dart';
import '../../shared/providers/core_providers.dart';
import '../../shared/models/seedstone.dart';
import '../../shared/widgets/media_preview.dart';
import '../../shared/widgets/reaction_buttons.dart';
import '../../shared/widgets/opinion_dialog.dart';
import '../../shared/widgets/standby_empty_state.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

class MeetScreen extends ConsumerStatefulWidget {
  const MeetScreen({super.key});

  @override
  ConsumerState<MeetScreen> createState() => _MeetScreenState();
}

class _MeetScreenState extends ConsumerState<MeetScreen> {
  final PageController _pageController = PageController();
  final Map<String, bool> _reactedSeedstones = {};

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _handleWriteThought(Seedstone seedstone) async {
    final opinionText = await OpinionDialog.show(
      context: context,
      anchorText: seedstone.textContent ?? "",
    );

    if (opinionText == null || opinionText.trim().isEmpty) return;

    try {
      final api = ref.read(apiServiceProvider);
      final storage = ref.read(storageServiceProvider);

      final newAnchor = await api.createAnchor(
        sourceTexts: [opinionText.trim()],
        topicHints: seedstone.topics.isNotEmpty ? seedstone.topics : null,
        modality: 'text',
      );

      final newAnchorId = newAnchor['anchor_id'] as String?;

      if (newAnchorId != null && newAnchorId.isNotEmpty) {
        await api.submitReaction(
          anchorId: newAnchorId,
          reactionType: 1,
          opinionText: opinionText.trim(),
        );
      }

      await storage.addMyReaction({
        'anchor_id': seedstone.seedstoneId,
        'feeling_anchor_id': newAnchorId ?? '',
        'anchor_text': seedstone.displayText.length > 50
            ? '${seedstone.displayText.substring(0, 50)}...'
            : seedstone.displayText,
        'reaction_type': '共鸣',
        'opinion_text': opinionText.trim(),
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });

      setState(() {
        _reactedSeedstones[seedstone.seedstoneId] = true;
      });

      ref.read(myReactionsProvider.notifier).refresh();

      HapticFeedback.lightImpact();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.check_circle_outline, color: StandbyColors.primary, size: 20),
                const SizedBox(width: 8),
                const Text('你的感受已成为新的心物'),
              ],
            ),
            backgroundColor: context.surface2,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.white, size: 20),
                const SizedBox(width: 8),
                Text('提交失败: $e'),
              ],
            ),
            backgroundColor: StandbyColors.primary,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    }
  }

  String _getSourceIcon(SeedstoneSource source) {
    switch (source) {
      case SeedstoneSource.user: return '📱';
      case SeedstoneSource.systemAi: return '🤖';
      case SeedstoneSource.shared: return '🔗';
    }
  }

  String _getSourceText(SeedstoneSource source) {
    switch (source) {
      case SeedstoneSource.user: return '用户创建';
      case SeedstoneSource.systemAi: return '系统建议';
      case SeedstoneSource.shared: return '分享内容';
    }
  }

  @override
  Widget build(BuildContext context) {
    final seedstonesAsync = ref.watch(seedstoneListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Standby'),
        actions: [
          IconButton(
            key: const Key('btn_refresh'),
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(seedstoneListProvider.notifier).refresh(),
          ),
        ],
      ),
      body: seedstonesAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => RefreshIndicator(
          onRefresh: () => ref.read(seedstoneListProvider.notifier).refresh(),
          child: ListView(
            children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.refresh, size: 48, color: context.text3Color),
                      const SizedBox(height: 16),
                      Text('加载失败，请下拉刷新', style: TextStyle(fontSize: 16, color: context.text2Color)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        data: (seedstones) {
          if (seedstones.isEmpty) {
            return const StandbyEmptyState(
              emoji: '🌙',
              title: '暂无心物',
              description: '下拉刷新',
            );
          }
          return PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: seedstones.length,
            itemBuilder: (context, index) {
              return _buildSeedstonePage(seedstones[index]);
            },
          );
        },
      ),
    );
  }

  Widget _buildSeedstonePage(Seedstone seedstone) {
    final hasReacted = _reactedSeedstones[seedstone.seedstoneId] ?? false;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        children: [
          const Spacer(),
          if (seedstone.hasMedia) ...[
            MediaPreview(media: seedstone.primaryMedia!, height: 200),
            const SizedBox(height: 24),
          ],
          if (seedstone.hasText)
            Text(
              seedstone.textContent!,
              style: TextStyle(fontSize: 20, height: 1.8, color: context.textColor),
              textAlign: TextAlign.center,
            ),
          if (seedstone.topics.isNotEmpty) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: seedstone.topics.map((topic) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: StandbyColors.primarySoft,
                    borderRadius: StandbyRadius.tagRadius,
                  ),
                  child: Text('#$topic', style: const TextStyle(fontSize: 13, color: StandbyColors.primary)),
                );
              }).toList(),
            ),
          ],
          const SizedBox(height: 16),
          Text(
            '${_getSourceIcon(seedstone.source)} ${_getSourceText(seedstone.source)}',
            style: TextStyle(fontSize: 12, color: context.text3Color),
          ),
          const SizedBox(height: 8),
          Container(height: 1, width: 60, color: context.borderColor),
          const Spacer(),
          if (hasReacted)
            Container(
              key: const Key('btn_opinion_done'),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(color: context.surface2, borderRadius: BorderRadius.circular(20)),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.check, size: 16, color: context.text3Color),
                  const SizedBox(width: 8),
                  Text('已记录感想', style: TextStyle(fontSize: 14, color: context.text3Color)),
                ],
              ),
            )
          else
            ReactionEntry(onTap: () => _handleWriteThought(seedstone)),
          const SizedBox(height: 16),
          GestureDetector(
            key: const Key('btn_view_opinions'),
            onTap: () => context.push('/seedstone/${seedstone.seedstoneId}'),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(color: context.surface2, borderRadius: BorderRadius.circular(20)),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.comment_outlined, size: 16, color: context.text2Color),
                  const SizedBox(width: 8),
                  Text('查看感想', style: TextStyle(fontSize: 14, color: context.text2Color)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}
