import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/providers/seedstone_provider.dart';
import '../../shared/widgets/standby_empty_state.dart';
import '../../shared/utils/formatters.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

/// 记录页 — 我的发布和感受日记
class RecordScreen extends ConsumerStatefulWidget {
  const RecordScreen({super.key});

  @override
  ConsumerState<RecordScreen> createState() => RecordScreenState();
}

class RecordScreenState extends ConsumerState<RecordScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this, initialIndex: 0);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void loadData() {
    ref.read(myReactionsProvider.notifier).refresh();
    ref.read(myPostsProvider.notifier).refresh();
  }

  @override
  Widget build(BuildContext context) {
    final reactions = ref.watch(myReactionsProvider);
    final posts = ref.watch(myPostsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('记录'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.edit_note), text: '我的发布'),
            Tab(icon: Icon(Icons.book_outlined), text: '感受日记'),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/publish'),
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildPostsTab(posts),
          _buildDiaryTab(reactions),
        ],
      ),
    );
  }

  Widget _buildPostsTab(List<Map<String, dynamic>> posts) {
    if (posts.isEmpty) {
      return const Center(
        child: StandbyEmptyState(
          emoji: '📝',
          title: '还没有发布内容',
          description: '点击右下角按钮发布你的想法',
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => loadData(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: posts.length,
        itemBuilder: (context, index) {
          final post = posts[index];

          Widget? header;
          if (index == 0 ||
              Formatters.formatDate(post['timestamp'] as int) !=
                  Formatters.formatDate(posts[index - 1]['timestamp'] as int)) {
            header = Padding(
              padding: const EdgeInsets.only(bottom: 12, top: 8),
              child: Text(
                '📅 ${Formatters.formatDate(post['timestamp'] as int)}',
                style: TextStyle(
                  fontSize: 14,
                  color: context.text2Color,
                  fontWeight: FontWeight.w500,
                ),
              ),
            );
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (header != null) header,
              _buildPostCard(post),
            ],
          );
        },
      ),
    );
  }

  Widget _buildDiaryTab(List<Map<String, dynamic>> reactions) {
    if (reactions.isEmpty) {
      return const Center(
        child: StandbyEmptyState(
          emoji: '💭',
          title: '还没有感受记录',
          description: '在「遇见」页写下你的感想',
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => loadData(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: reactions.length,
        itemBuilder: (context, index) {
          final reaction = reactions[index];

          Widget? header;
          if (index == 0 ||
              Formatters.formatDate(reaction['timestamp'] as int) !=
                  Formatters.formatDate(reactions[index - 1]['timestamp'] as int)) {
            header = Padding(
              padding: const EdgeInsets.only(bottom: 12, top: 8),
              child: Text(
                '📅 ${Formatters.formatDate(reaction['timestamp'] as int)}',
                style: TextStyle(
                  fontSize: 14,
                  color: context.text2Color,
                  fontWeight: FontWeight.w500,
                ),
              ),
            );
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (header != null) header,
              _buildDiaryCard(reaction),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPostCard(Map<String, dynamic> post) {
    final scene = post['scene'] as String? ?? '';
    final content = post['content'] as String? ?? '';
    final topics = (post['topics'] as List?)?.cast<String>() ?? [];
    final anchorId = post['anchor_id'] as String? ?? '';

    return GestureDetector(
      onTap: () {
        if (anchorId.isNotEmpty) {
          context.push('/seedstone/$anchorId');
        }
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: context.surface1,
          borderRadius: StandbyRadius.cardRadius,
          border: Border.all(color: context.borderColor),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (scene.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: context.surface2,
                  borderRadius: BorderRadius.circular(StandbyRadius.sm),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.movie_creation_outlined, size: 16, color: context.text3Color),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        scene,
                        style: TextStyle(
                          fontSize: 13,
                          color: context.text2Color,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],
            Text(content, style: StandbyTextStyles.body),
            const SizedBox(height: 12),
            if (topics.isNotEmpty)
              Wrap(
                spacing: 8,
                children: topics.map((topic) {
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: StandbyColors.primarySoft,
                      borderRadius: StandbyRadius.tagRadius,
                    ),
                    child: Text(
                      '#$topic',
                      style: const TextStyle(fontSize: 12, color: StandbyColors.primary),
                    ),
                  );
                }).toList(),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDiaryCard(Map<String, dynamic> reaction) {
    final anchorId = reaction['anchor_id'] as String? ?? '';
    final anchorText = reaction['anchor_text'] as String? ?? '';
    final opinionText = reaction['opinion_text'] as String?;

    return GestureDetector(
      onTap: () {
        if (anchorId.isNotEmpty) {
          context.push('/seedstone/$anchorId');
        }
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: context.surface1,
          borderRadius: StandbyRadius.cardRadius,
          border: Border.all(color: context.borderColor),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: context.surface2,
                borderRadius: BorderRadius.circular(StandbyRadius.sm),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.format_quote, size: 16, color: context.text3Color),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      anchorText,
                      style: TextStyle(
                        fontSize: 14,
                        color: context.text2Color,
                        height: 1.5,
                      ),
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
            if (opinionText != null && opinionText.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                opinionText,
                style: StandbyTextStyles.body.copyWith(fontStyle: FontStyle.italic),
                maxLines: 5,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.arrow_forward_ios, size: 12, color: context.text3Color),
                const SizedBox(width: 4),
                Text('查看原文', style: TextStyle(fontSize: 12, color: context.text3Color)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
