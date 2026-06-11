import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/services/api_service.dart';
import '../../shared/services/storage_service.dart';
import '../../shared/models/seedstone.dart';
import '../../shared/widgets/media_preview.dart';
import '../../shared/widgets/reaction_buttons.dart';
import '../../shared/widgets/opinion_dialog.dart';
import '../../app/theme.dart';

/// 遇见页 — 全屏心物浏览
class MeetScreen extends ConsumerStatefulWidget {
  const MeetScreen({super.key});

  @override
  ConsumerState<MeetScreen> createState() => _MeetScreenState();
}

class _MeetScreenState extends ConsumerState<MeetScreen> {
  final _api = ApiService();
  final _storage = StorageService();
  final PageController _pageController = PageController();
  final _random = Random();
  List<Seedstone> _seedstones = [];
  bool _loading = true;
  int _currentPage = 0;
  String? _error;
  final Map<String, bool> _reactedSeedstones = {};

  @override
  void initState() {
    super.initState();
    _loadSeedstones();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _loadSeedstones() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      int retries = 0;
      while (!_api.isInitialized && retries < 10) {
        await Future.delayed(const Duration(milliseconds: 500));
        retries++;
      }

      final data = await _api.listAnchors(page: 1, pageSize: 20);
      final list = (data['anchors'] as List?) ?? [];
      _seedstones = list.map((j) => Seedstone.fromJson(j)).toList();
      _seedstones.shuffle();

      setState(() {
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = '加载失败，请下拉刷新';
      });
    }
  }

  /// 处理写感想 — 弹出感想输入框，系统自动推断反应类型
  Future<void> _handleWriteThought(Seedstone seedstone) async {
    final opinionText = await OpinionDialog.show(
      context: context,
      anchorText: seedstone.textContent ?? "",
    );

    if (opinionText == null) return;

    await _submitReaction(
      seedstone,
      opinionText: opinionText.isEmpty ? null : opinionText,
    );
  }

  /// 提交反应到 API — 不指定 reactionType，让后端推断
  Future<void> _submitReaction(
    Seedstone seedstone, {
    String? opinionText,
  }) async {
    try {
      await _api.submitReaction(
        anchorId: seedstone.seedstoneId,
        reactionType: 1,
        opinionText: opinionText,
      );

      // 生成随机匿名身份
      final anonymousName = _generateAnonymousName();
      final anonymousAvatar = _generateAnonymousAvatar();

      await _storage.addMyReaction({
        'anchor_id': seedstone.seedstoneId,
        'anchor_text': seedstone.displayText.length > 50
            ? '${seedstone.displayText.substring(0, 50)}...'
            : seedstone.displayText,
        'reaction_type': '共鸣',
        'opinion_text': opinionText,
        'anonymous_name': anonymousName,
        'anonymous_avatar': anonymousAvatar,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });

      setState(() {
        _reactedSeedstones[seedstone.seedstoneId] = true;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('已记录你的感想')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('提交失败，请重试'),
            backgroundColor: StandbyColors.primary,
          ),
        );
      }
    }
  }

  String _generateAnonymousName() {
    final prefixes = ['夜的', '晨曦', '微风', '秋日', '冬雪', '春水', '夏雨', '远山',
                      '近海', '深林', '浅滩', '孤星', '流云', '闲鹤', '静湖', '暖阳'];
    final suffixes = ['旅人', '过客', '归人', '行者', '诗人', '歌者', '守望', '聆听',
                      '沉思', '静默', '观察', '等待', '漂流', '停泊', '游荡', '栖息'];
    return '${prefixes[_random.nextInt(prefixes.length)]}${suffixes[_random.nextInt(suffixes.length)]}';
  }

  String _generateAnonymousAvatar() {
    final avatars = ['🌙', '☀️', '🌊', '🍂', '🌸', '❄️', '🌿', '🍃', '☁️', '⭐',
                     '🌻', '🍁', '🦋', '🐱', '🦊', '🐰', '🐻', '🐼', '🐨', '🦁'];
    return avatars[_random.nextInt(avatars.length)];
  }

  void _openOpinions(Seedstone seedstone) {
    context.push('/seedstone/${seedstone.seedstoneId}');
  }

  String _getSourceIcon(SeedstoneSource source) {
    switch (source) {
      case SeedstoneSource.user:
        return '📱';
      case SeedstoneSource.systemAi:
        return '🤖';
      case SeedstoneSource.shared:
        return '🔗';
    }
  }

  String _getSourceText(SeedstoneSource source) {
    switch (source) {
      case SeedstoneSource.user:
        return '用户创建';
      case SeedstoneSource.systemAi:
        return '系统建议';
      case SeedstoneSource.shared:
        return '分享内容';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null || _seedstones.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Standby')),
        body: RefreshIndicator(
          onRefresh: _loadSeedstones,
          child: ListView(
            children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.refresh, size: 48, color: StandbyColors.text3),
                      const SizedBox(height: 16),
                      Text(
                        _error ?? '暂无心物',
                        style: TextStyle(fontSize: 16, color: StandbyColors.text2),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '下拉刷新',
                        style: TextStyle(fontSize: 14, color: StandbyColors.text3),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Standby'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadSeedstones,
          ),
        ],
      ),
      body: PageView.builder(
        controller: _pageController,
        scrollDirection: Axis.vertical,
        itemCount: _seedstones.length,
        onPageChanged: (index) {
          setState(() => _currentPage = index);
        },
        itemBuilder: (context, index) {
          return _buildSeedstonePage(_seedstones[index]);
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

          // 媒体内容
          if (seedstone.hasMedia) ...[
            MediaPreview(
              media: seedstone.primaryMedia!,
              height: 200,
            ),
            const SizedBox(height: 24),
          ],

          // 文本内容
          if (seedstone.hasText)
            Text(
              seedstone.textContent!,
              style: const TextStyle(
                fontSize: 20,
                height: 1.8,
                color: StandbyColors.text,
              ),
              textAlign: TextAlign.center,
            ),

          // 话题标签
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
                  child: Text(
                    '#$topic',
                    style: const TextStyle(
                      fontSize: 13,
                      color: StandbyColors.primary,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],

          const SizedBox(height: 16),

          // 来源标识
          Text(
            '${_getSourceIcon(seedstone.source)} ${_getSourceText(seedstone.source)}',
            style: const TextStyle(fontSize: 12, color: StandbyColors.text3),
          ),

          const SizedBox(height: 8),

          // 分隔线
          Container(height: 1, width: 60, color: StandbyColors.border),

          const Spacer(),

          // 写感想入口
          if (hasReacted)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(
                color: StandbyColors.surface2,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.check, size: 16, color: StandbyColors.text3),
                  const SizedBox(width: 8),
                  Text(
                    '已记录感想',
                    style: TextStyle(fontSize: 14, color: StandbyColors.text3),
                  ),
                ],
              ),
            )
          else
            ReactionEntry(
              onTap: () => _handleWriteThought(seedstone),
            ),
          const SizedBox(height: 16),

          // 查看感想按钮
          GestureDetector(
            onTap: () => _openOpinions(seedstone),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: StandbyColors.surface2,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.comment_outlined, size: 16, color: StandbyColors.text2),
                  const SizedBox(width: 8),
                  Text(
                    '查看感想',
                    style: TextStyle(fontSize: 14, color: StandbyColors.text2),
                  ),
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
