import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/media_service.dart';
import '../services/storage_service.dart';
import 'publish_screen.dart';

/// 记录页 — 我的发布和历史线
class RecordScreen extends StatefulWidget {
  final ApiService api;
  final MediaService mediaService;
  final Function(String anchorId)? onNavigateToAnchor;

  const RecordScreen({
    super.key,
    required this.api,
    required this.mediaService,
    this.onNavigateToAnchor,
  });

  @override
  RecordScreenState createState() => RecordScreenState();
}

class RecordScreenState extends State<RecordScreen>
    with SingleTickerProviderStateMixin {
  final _storage = StorageService();
  late TabController _tabController;
  List<Map<String, dynamic>> _reactions = [];
  List<Map<String, dynamic>> _posts = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this, initialIndex: 0);
    loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void loadData() {
    setState(() {
      _reactions = _storage.myReactions;
      _posts = _storage.myPosts;
    });
  }

  void _openPublishScreen() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PublishScreen(
          api: widget.api,
          mediaService: widget.mediaService,
          onPublished: loadData,
        ),
      ),
    );
  }

  /// 导航到遇见页的对应锚点
  void _navigateToAnchor(String anchorId) {
    widget.onNavigateToAnchor?.call(anchorId);
  }

  /// 查看发布内容的反馈
  void _viewPostFeedback(Map<String, dynamic> post) async {
    final content = post['content'] as String? ?? '';
    final scene = post['scene'] as String? ?? '';
    final anchorId = post['anchor_id'] as String? ?? '';

    // 锚点 ID 为空时不允许查看反馈
    if (anchorId.isEmpty) {
      print('跳过反馈查看: anchorId 为空');
      return;
    }

    // 显示加载状态
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _FeedbackSheet(
        content: content,
        scene: scene,
        anchorId: anchorId,
        api: widget.api,
      ),
    );
  }

  String _getReactionEmoji(String type) {
    switch (type) {
      case '共鸣':
        return '❤️';
      case '无感':
        return '😐';
      case '反对':
        return '👎';
      case '未体验':
        return '❓';
      case '有害':
        return '⚠️';
      default:
        return '•';
    }
  }

  String _formatDate(int timestamp) {
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp);
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final dateOnly = DateTime(date.year, date.month, date.day);

    if (dateOnly == today) {
      return '今天';
    } else if (dateOnly == yesterday) {
      return '昨天';
    } else {
      return '${date.month}月${date.day}日';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('记录'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            const Tab(
              icon: Icon(Icons.edit_note),
              text: '我的发布',
            ),
            Tab(
              icon: const Icon(Icons.timeline),
              text: '历史线 (${_reactions.length})',
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _openPublishScreen,
        backgroundColor: Colors.indigo,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildPostsTab(),
          _buildTimelineTab(),
        ],
      ),
    );
  }

  Widget _buildPostsTab() {
    if (_posts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.edit_note,
              size: 64,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              '还没有发布内容',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '点击右下角按钮发布你的想法',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade400,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => loadData(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _posts.length,
        itemBuilder: (context, index) {
          final post = _posts[index];

          // 显示日期分隔
          Widget? header;
          if (index == 0 ||
              _formatDate(post['timestamp'] as int) !=
                  _formatDate(_posts[index - 1]['timestamp'] as int)) {
            header = Padding(
              padding: const EdgeInsets.only(bottom: 12, top: 8),
              child: Text(
                '📅 ${_formatDate(post['timestamp'] as int)}',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey.shade600,
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

  Widget _buildTimelineTab() {
    if (_reactions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.timeline,
              size: 64,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              '还没有历史记录',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '在「遇见」页表达你的共鸣',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade400,
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => loadData(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _reactions.length,
        itemBuilder: (context, index) {
          final reaction = _reactions[index];

          // 显示日期分隔
          Widget? header;
          if (index == 0 ||
              _formatDate(reaction['timestamp'] as int) !=
                  _formatDate(_reactions[index - 1]['timestamp'] as int)) {
            header = Padding(
              padding: const EdgeInsets.only(bottom: 12, top: 8),
              child: Text(
                '📅 ${_formatDate(reaction['timestamp'] as int)}',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey.shade600,
                  fontWeight: FontWeight.w500,
                ),
              ),
            );
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (header != null) header,
              _buildTimelineCard(reaction),
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

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.shade100,
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 场景描述（可点击跳转到遇见页）
          if (scene.isNotEmpty) ...[
            GestureDetector(
              onTap: () {
                if (anchorId.isNotEmpty) {
                  _navigateToAnchor(anchorId);
                }
              },
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.movie_creation_outlined,
                        size: 16, color: Colors.grey.shade500),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        scene,
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey.shade600,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],

          // 想法内容（可点击跳转到遇见页）
          GestureDetector(
            onTap: () {
              if (anchorId.isNotEmpty) {
                _navigateToAnchor(anchorId);
              }
            },
            child: Text(
              content,
              style: const TextStyle(
                fontSize: 15,
                height: 1.6,
              ),
            ),
          ),
          const SizedBox(height: 12),

          // 话题标签和反馈提示
          Row(
            children: [
              // 话题标签
              if (topics.isNotEmpty)
                Expanded(
                  child: Wrap(
                    spacing: 8,
                    children: topics.map((topic) {
                      return Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.indigo.shade50,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '#$topic',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.indigo.shade600,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),

              // 查看反馈按钮
              GestureDetector(
                onTap: () => _viewPostFeedback(post),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.chat_bubble_outline,
                        size: 14,
                        color: Colors.grey.shade600,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '查看反馈',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTimelineCard(Map<String, dynamic> reaction) {
    final anchorId = reaction['anchor_id'] as String? ?? '';
    final anchorText = reaction['anchor_text'] as String? ?? '';
    final reactionType = reaction['reaction_type'] as String? ?? '';
    final emotionWord = reaction['emotion_word'] as String?;
    final opinionText = reaction['opinion_text'] as String?;

    return GestureDetector(
      onTap: () {
        if (anchorId.isNotEmpty) {
          _navigateToAnchor(anchorId);
        }
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 左侧：锚点摘要
              Expanded(
                flex: 3,
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade50,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(12),
                      bottomLeft: Radius.circular(12),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        anchorText,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade700,
                          height: 1.5,
                        ),
                        maxLines: 4,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Icon(
                            Icons.arrow_forward_ios,
                            size: 12,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '查看原文',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey.shade500,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // 右侧：用户操作（突出显示）
              Expanded(
                flex: 2,
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: _getReactionBgColor(reactionType),
                    borderRadius: const BorderRadius.only(
                      topRight: Radius.circular(12),
                      bottomRight: Radius.circular(12),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 反应类型
                      Row(
                        children: [
                          Text(
                            _getReactionEmoji(reactionType),
                            style: const TextStyle(fontSize: 20),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            reactionType,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: _getReactionTextColor(reactionType),
                            ),
                          ),
                        ],
                      ),

                      // 情绪词
                      if (emotionWord != null && emotionWord.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: _getReactionTextColor(reactionType)
                                .withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            emotionWord,
                            style: TextStyle(
                              fontSize: 12,
                              color: _getReactionTextColor(reactionType),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],

                      // 评论
                      if (opinionText != null && opinionText.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          opinionText,
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey.shade700,
                            fontStyle: FontStyle.italic,
                          ),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getReactionBgColor(String type) {
    switch (type) {
      case '共鸣':
        return Colors.red.shade50;
      case '无感':
        return Colors.grey.shade100;
      case '反对':
        return Colors.blueGrey.shade50;
      case '未体验':
        return Colors.orange.shade50;
      case '有害':
        return Colors.grey.shade200;
      default:
        return Colors.grey.shade50;
    }
  }

  Color _getReactionTextColor(String type) {
    switch (type) {
      case '共鸣':
        return Colors.red.shade700;
      case '无感':
        return Colors.grey.shade700;
      case '反对':
        return Colors.blueGrey.shade700;
      case '未体验':
        return Colors.orange.shade700;
      case '有害':
        return Colors.grey.shade800;
      default:
        return Colors.grey.shade700;
    }
  }
}

/// 反馈面板
class _FeedbackSheet extends StatefulWidget {
  final String content;
  final String scene;
  final String anchorId;
  final ApiService api;

  const _FeedbackSheet({
    required this.content,
    required this.scene,
    required this.anchorId,
    required this.api,
  });

  @override
  State<_FeedbackSheet> createState() => _FeedbackSheetState();
}

class _FeedbackSheetState extends State<_FeedbackSheet> {
  bool _loading = true;
  List<Map<String, dynamic>> _feedbacks = [];
  Map<String, int> _stats = {};

  @override
  void initState() {
    super.initState();
    _loadFeedback();
  }

  Future<void> _loadFeedback() async {
    setState(() => _loading = true);

    try {
      if (widget.anchorId.isEmpty) {
        throw Exception('锚点ID为空');
      }
      
      // 调用真实 API 获取反应列表
      final data = await widget.api.listReactions(widget.anchorId);
      final reactions = data['reactions'] as List? ?? [];
      final pagination = data['pagination'] as Map<String, dynamic>? ?? {};
      
      // 统计各反应类型数量
      final stats = <String, int>{};
      final feedbacks = <Map<String, dynamic>>[];
      
      for (final reaction in reactions) {
        final reactionType = reaction['reaction_type']?.toString() ?? '';
        final emotionWord = reaction['emotion_word']?.toString();
        final opinionText = reaction['opinion_text'] as String?;
        final createdAt = reaction['created_at'] as int? ?? 0;
        
        // 统计反应类型
        if (reactionType.isNotEmpty) {
          stats[reactionType] = (stats[reactionType] ?? 0) + 1;
        }
        
        // 构建反馈项
        feedbacks.add({
          'anonymous_name': '匿名用户', // 后续可从用户引擎获取
          'anonymous_avatar': '👤',
          'reaction_type': reactionType,
          'emotion_word': emotionWord,
          'opinion_text': opinionText,
          'timestamp': createdAt * 1000, // 转换为毫秒
        });
      }
      
      setState(() {
        _loading = false;
        _stats = stats;
        _feedbacks = feedbacks;
      });
    } catch (e) {
      print('加载反馈失败: $e');
      setState(() {
        _loading = false;
        _stats = {};
        _feedbacks = [];
      });
    }
  }

  String _formatTimeAgo(int timestamp) {
    final diff = DateTime.now().millisecondsSinceEpoch - timestamp;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return '${diff ~/ 60000}分钟前';
    if (diff < 86400000) return '${diff ~/ 3600000}小时前';
    return '${diff ~/ 86400000}天前';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.8,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 标题
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            '收到的反馈',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),

          // 发布内容预览
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (widget.scene.isNotEmpty) ...[
                  Row(
                    children: [
                      Icon(Icons.movie_creation_outlined,
                          size: 16, color: Colors.grey.shade500),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          widget.scene,
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey.shade600,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                ],
                Text(
                  widget.content,
                  style: const TextStyle(fontSize: 15),
                  maxLines: 5,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // 反馈统计
          _loading
              ? const Center(child: CircularProgressIndicator())
              : Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildStatItem('❤️', '共鸣', _stats['共鸣'] ?? 0),
                    _buildStatItem('😐', '无感', _stats['无感'] ?? 0),
                    _buildStatItem('💡', '启发', _stats['启发'] ?? 0),
                    _buildStatItem('💬', '评论', _stats['评论'] ?? 0),
                  ],
                ),
          const SizedBox(height: 16),

          // 反馈列表
          if (!_loading && _feedbacks.isNotEmpty) ...[
            const Text(
              '最新反馈',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: _feedbacks.length,
                itemBuilder: (context, index) {
                  final feedback = _feedbacks[index];
                  return _buildFeedbackItem(feedback);
                },
              ),
            ),
          ],

          if (!_loading && _feedbacks.isEmpty)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.chat_bubble_outline,
                      size: 48,
                      color: Colors.grey.shade300,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '暂无反馈',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey.shade500,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String emoji, String label, int count) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 24)),
        const SizedBox(height: 4),
        Text(
          '$count',
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey.shade600,
          ),
        ),
      ],
    );
  }

  Widget _buildFeedbackItem(Map<String, dynamic> feedback) {
    final name = feedback['anonymous_name'] as String? ?? '匿名用户';
    final avatar = feedback['anonymous_avatar'] as String? ?? '🌙';
    final reactionType = feedback['reaction_type'] as String? ?? '';
    final emotionWord = feedback['emotion_word'] as String?;
    final opinionText = feedback['opinion_text'] as String?;
    final timestamp = feedback['timestamp'] as int? ?? 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(avatar, style: const TextStyle(fontSize: 24)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      name,
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _formatTimeAgo(timestamp),
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      reactionType,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    if (emotionWord != null) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.indigo.shade50,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          emotionWord,
                          style: TextStyle(
                            fontSize: 11,
                            color: Colors.indigo.shade600,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                if (opinionText != null && opinionText.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    opinionText,
                    style: const TextStyle(fontSize: 14),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
