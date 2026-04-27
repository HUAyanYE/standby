import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/anchor.dart';
import '../widgets/media_preview.dart';
import '../widgets/reaction_buttons.dart';
import '../widgets/emotion_dialog.dart';
import '../widgets/opinion_dialog.dart';
import 'opinions_screen.dart';

/// 遇见页 — 全屏锚点浏览
class MeetScreen extends StatefulWidget {
  final ApiService api;
  final String? initialAnchorId;
  final VoidCallback? onReactionAdded;

  const MeetScreen({
    super.key,
    required this.api,
    this.initialAnchorId,
    this.onReactionAdded,
  });

  @override
  State<MeetScreen> createState() => _MeetScreenState();
}

class _MeetScreenState extends State<MeetScreen> {
  final _storage = StorageService();
  final PageController _pageController = PageController();
  List<Anchor> _anchors = [];
  bool _loading = true;
  int _currentPage = 0;
  String? _error;

  // 记录每个锚点的反应状态
  final Map<String, ReactionType?> _selectedReactions = {};

  @override
  void initState() {
    super.initState();
    _loadAnchors();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _loadAnchors() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // 检查 API 是否已初始化，如果没有则等待
      int retries = 0;
      while (!widget.api.isInitialized && retries < 10) {
        print('API 未初始化，等待中... (尝试 ${retries + 1}/10)');
        await Future.delayed(const Duration(milliseconds: 500));
        retries++;
      }

      if (!widget.api.isInitialized) {
        print('API 初始化超时，尝试继续...');
      }

      final data = await widget.api.listAnchors(page: 1, pageSize: 20);
      final list = (data['anchors'] as List?) ?? [];
      _anchors = list.map((j) => Anchor.fromJson(j)).toList();

      // 随机打乱顺序
      _anchors.shuffle();

      // 如果指定了初始锚点，找到它的位置
      int initialPage = 0;
      if (widget.initialAnchorId != null && _anchors.isNotEmpty) {
        final index = _anchors.indexWhere(
          (a) => a.anchorId == widget.initialAnchorId,
        );
        if (index >= 0) {
          initialPage = index;
        }
      }

      setState(() {
        _loading = false;
        _currentPage = initialPage;
      });

      // 如果指定了初始锚点，跳转到对应页面
      if (widget.initialAnchorId != null && _pageController.hasClients) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _pageController.jumpToPage(initialPage);
        });
      }
    } catch (e) {
      print('加载锚点失败: $e');
      setState(() {
        _loading = false;
        _error = '加载失败，请下拉刷新';
      });
    }
  }

  /// 处理共鸣反应（包含情绪词选择和评论）
  Future<void> _handleResonance(Anchor anchor) async {
    // 1. 弹出情绪词选择
    final emotionResult = await EmotionDialog.show(context);
    if (emotionResult == null) return;

    // 获取情绪词（可能为 null，表示用户跳过了）
    final emotionWord = emotionResult.emotionWord ?? '';

    // 2. 弹出评论输入框
    final opinionText = await OpinionDialog.show(
      context: context,
      anchorText: anchor.textContent ?? "",
      emotionWord: emotionWord.isNotEmpty ? emotionWord : '共鸣',
      reactionType: '共鸣',
    );

    // 用户取消了评论对话框
    if (opinionText == null) return;

    // 3. 提交反应
    await _submitReaction(
      anchor,
      ReactionType.resonance,
      emotionWord: emotionWord.isNotEmpty ? emotionWord : null,
      opinionText: opinionText.isEmpty ? null : opinionText,
    );
  }

  /// 处理其他反应
  Future<void> _handleReaction(Anchor anchor, ReactionType type) async {
    // 检查是否已选择该反应
    final currentReaction = _selectedReactions[anchor.anchorId];
    if (currentReaction == type) {
      // 取消反应
      setState(() => _selectedReactions.remove(anchor.anchorId));
      return;
    }

    // 获取反应类型名称
    final reactionTypeName = _getReactionTypeName(type);

    // 弹出评论输入框
    final opinionText = await OpinionDialog.show(
      context: context,
      anchorText: anchor.textContent ?? "",
      emotionWord: '',
      reactionType: reactionTypeName,
    );

    // 用户取消了评论对话框
    if (opinionText == null) return;

    // 提交反应
    await _submitReaction(
      anchor,
      type,
      opinionText: opinionText.isEmpty ? null : opinionText,
    );
  }

  /// 提交反应到 API
  Future<void> _submitReaction(
    Anchor anchor,
    ReactionType type, {
    String? emotionWord,
    String? opinionText,
  }) async {
    try {
      final reactionTypeName = _getReactionTypeName(type);

      // 生成匿名身份
      final anonymousName = _generateAnonymousName();
      final anonymousAvatar = _generateAnonymousAvatar();

      await widget.api.submitReaction(
        anchorId: anchor.anchorId,
        reactionType: reactionTypeName,
        emotionWord: emotionWord,
        modality: 'text',
        textContent: opinionText,
      );

      // 保存到本地记录
      await _storage.addMyReaction({
        'anchor_id': anchor.anchorId,
        'anchor_text': anchor.displayText.length > 50
            ? '${anchor.displayText.substring(0, 50)}...'
            : anchor.displayText,
        'reaction_type': reactionTypeName,
        'emotion_word': emotionWord,
        'opinion_text': opinionText,
        'anonymous_name': anonymousName,
        'anonymous_avatar': anonymousAvatar,
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      });

      setState(() {
        _selectedReactions[anchor.anchorId] = type;
      });

      // 通知父组件刷新数据
      widget.onReactionAdded?.call();

      if (mounted) {
        final message = emotionWord != null
            ? '已记录你的 $emotionWord 共鸣'
            : '已记录你的 $reactionTypeName';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(message)),
        );
      }
    } catch (e) {
      print('提交反应失败: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('提交失败，请重试'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// 生成匿名昵称
  String _generateAnonymousName() {
    final prefixes = ['夜的', '晨曦', '微风', '秋日', '冬雪', '春水', '夏雨', '远山'];
    final suffixes = ['旅人', '过客', '归人', '行者', '诗人', '歌者', '守望', '聆听'];
    final random = DateTime.now().millisecondsSinceEpoch;
    return '${prefixes[random % prefixes.length]}${suffixes[(random ~/ 10) % suffixes.length]}';
  }

  /// 生成匿名头像
  String _generateAnonymousAvatar() {
    final avatars = ['🌙', '☀️', '🌊', '🍂', '🌸', '❄️', '🌿', '🍃', '☁️', '⭐'];
    final random = DateTime.now().millisecondsSinceEpoch;
    return avatars[random % avatars.length];
  }

  String _getReactionTypeName(ReactionType type) {
    switch (type) {
      case ReactionType.resonance:
        return '共鸣';
      case ReactionType.neutral:
        return '无感';
      case ReactionType.opposition:
        return '反对';
      case ReactionType.unexperienced:
        return '未体验';
      case ReactionType.harmful:
        return '有害';
    }
  }

  /// 打开评论列表
  void _openOpinions(Anchor anchor) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => OpinionsScreen(api: widget.api, anchor: anchor),
      ),
    );
  }

  /// 获取来源图标
  String _getSourceIcon(AnchorSource source) {
    switch (source) {
      case AnchorSource.user:
        return '📱';
      case AnchorSource.systemAi:
        return '🤖';
      case AnchorSource.shared:
        return '🔗';
    }
  }

  /// 获取来源文本
  String _getSourceText(AnchorSource source) {
    switch (source) {
      case AnchorSource.user:
        return '用户创建';
      case AnchorSource.systemAi:
        return '系统建议';
      case AnchorSource.shared:
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

    if (_error != null || _anchors.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Standby')),
        body: RefreshIndicator(
          onRefresh: _loadAnchors,
          child: ListView(
            children: [
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.6,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.refresh,
                        size: 48,
                        color: Colors.grey.shade400,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _error ?? '暂无锚点',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey.shade500,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '下拉刷新',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade400,
                        ),
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

    // 检查滑动方向设置
    final isVertical = _storage.isVerticalSwipe;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Standby'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAnchors,
          ),
        ],
      ),
      body: PageView.builder(
        controller: _pageController,
        scrollDirection: isVertical ? Axis.vertical : Axis.horizontal,
        itemCount: _anchors.length,
        onPageChanged: (index) {
          setState(() => _currentPage = index);
        },
        itemBuilder: (context, index) {
          return _buildAnchorPage(_anchors[index]);
        },
      ),
    );
  }

  Widget _buildAnchorPage(Anchor anchor) {
    final selectedReaction = _selectedReactions[anchor.anchorId];
    final counts = _getReactionCounts(anchor);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        children: [
          const Spacer(),

          // ============================================================
          // 媒体内容 (如果有)
          // ============================================================
          if (anchor.hasMedia) ...[
            MediaPreview(
              media: anchor.primaryMedia!,
              height: 200,
            ),
            const SizedBox(height: 24),
          ],

          // ============================================================
          // 文本内容
          // ============================================================
          if (anchor.hasText)
            Text(
              anchor.textContent!,
              style: const TextStyle(
                fontSize: 20,
                height: 1.8,
                fontFamily: 'Noto Serif CJK',
              ),
              textAlign: TextAlign.center,
            ),

          // ============================================================
          // 话题标签
          // ============================================================
          if (anchor.topics.isNotEmpty) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: anchor.topics.map((topic) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.indigo.shade50,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '#$topic',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.indigo.shade400,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],

          const SizedBox(height: 16),

          // ============================================================
          // 来源标识
          // ============================================================
          Text(
            '${_getSourceIcon(anchor.source)} ${_getSourceText(anchor.source)}',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade500,
            ),
          ),

          const SizedBox(height: 8),

          // 分隔线
          Container(
            height: 1,
            width: 60,
            color: Colors.grey.shade300,
          ),

          const Spacer(),

          // ============================================================
          // 反应按钮
          // ============================================================
          ReactionButtons(
            selectedReaction: selectedReaction,
            counts: counts,
            onReaction: (type) => _handleReaction(anchor, type),
            onResonance: () => _handleResonance(anchor),
          ),
          const SizedBox(height: 16),

          // ============================================================
          // 查看观点按钮
          // ============================================================
          GestureDetector(
            onTap: () => _openOpinions(anchor),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.comment_outlined, size: 16, color: Colors.grey.shade600),
                  const SizedBox(width: 8),
                  Text(
                    '查看观点',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
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

  Map<ReactionType, int> _getReactionCounts(Anchor anchor) {
    // 模拟数据，实际应该从 API 获取
    return {
      ReactionType.resonance: 80 + (anchor.reactionCount * 2),
      ReactionType.neutral: 30 + anchor.reactionCount,
      ReactionType.opposition: 10,
      ReactionType.unexperienced: 5,
      ReactionType.harmful: 1,
    };
  }
}
