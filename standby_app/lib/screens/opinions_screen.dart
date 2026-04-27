import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/anchor.dart';

/// 观点列表页 — 查看锚点的反应和评论
class OpinionsScreen extends StatefulWidget {
  final ApiService api;
  final Anchor anchor;

  const OpinionsScreen({
    super.key,
    required this.api,
    required this.anchor,
  });

  @override
  State<OpinionsScreen> createState() => _OpinionsScreenState();
}

class _OpinionsScreenState extends State<OpinionsScreen> {
  List<Map<String, dynamic>> _opinions = [];
  bool _loading = true;
  String _filterType = 'all';
  int _page = 1;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _loadOpinions();
  }

  Future<void> _loadOpinions({bool refresh = false}) async {
    if (refresh) {
      setState(() {
        _page = 1;
        _hasMore = true;
        _loading = true;
      });
    }

    try {
      final data = await widget.api.listReactions(
        widget.anchor.anchorId,
        page: _page,
        pageSize: 20,
        filterType: _filterType == 'all' ? null : _filterType,
      );

      print('API 返回数据: $data');

      // 安全地获取 reactions 列表
      final dynamic reactionsData = data['reactions'];
      List<Map<String, dynamic>> newOpinions = [];
      
      if (reactionsData is List) {
        for (var item in reactionsData) {
          if (item is Map<String, dynamic>) {
            newOpinions.add(item);
          } else if (item is Map) {
            // 转换 Map<dynamic, dynamic> 为 Map<String, dynamic>
            newOpinions.add(Map<String, dynamic>.from(item));
          }
        }
      }

      setState(() {
        if (refresh) {
          _opinions = newOpinions;
        } else {
          _opinions.addAll(newOpinions);
        }
        _hasMore = newOpinions.length >= 20;
        _loading = false;
      });
    } catch (e, stackTrace) {
      print('加载观点失败: $e');
      print('堆栈跟踪: $stackTrace');
      setState(() => _loading = false);
    }
  }

  void _loadMore() {
    if (!_loading && _hasMore) {
      setState(() => _page++);
      _loadOpinions();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('观点'),
        actions: [
          // 筛选按钮
          PopupMenuButton<String>(
            initialValue: _filterType,
            onSelected: (value) {
              setState(() => _filterType = value);
              _loadOpinions(refresh: true);
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'all', child: Text('全部')),
              const PopupMenuItem(value: '共鸣', child: Text('❤️ 共鸣')),
              const PopupMenuItem(value: '无感', child: Text('😐 无感')),
              const PopupMenuItem(value: '反对', child: Text('👎 反对')),
              const PopupMenuItem(value: '未体验', child: Text('❓ 未体验')),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          // 锚点预览
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.grey.shade50,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.anchor.displayText,
                  style: const TextStyle(
                    fontSize: 16,
                    height: 1.6,
                  ),
                  maxLines: 4,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 8),
                Text(
                  '📖 编辑精选',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade500,
                  ),
                ),
              ],
            ),
          ),

          // 统计信息
          _buildStats(),

          // 观点列表
          Expanded(
            child: _loading && _opinions.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _opinions.isEmpty
                    ? Center(
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
                              '暂无观点',
                              style: TextStyle(color: Colors.grey.shade500),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: () => _loadOpinions(refresh: true),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _opinions.length + (_hasMore ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (index == _opinions.length) {
                              WidgetsBinding.instance.addPostFrameCallback((_) {
                                _loadMore();
                              });
                              return const Center(
                                child: Padding(
                                  padding: EdgeInsets.all(16),
                                  child: CircularProgressIndicator(),
                                ),
                              );
                            }
                            return _buildOpinionCard(_opinions[index]);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildStats() {
    // 统计各反应数量
    final counts = <String, int>{};
    for (final opinion in _opinions) {
      final type = opinion['reaction_type']?.toString() ?? '未知';
      counts[type] = (counts[type] ?? 0) + 1;
    }

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem('❤️', '共鸣', counts['共鸣'] ?? 0),
          _buildStatItem('😐', '无感', counts['无感'] ?? 0),
          _buildStatItem('👎', '反对', counts['反对'] ?? 0),
          _buildStatItem('❓', '未体验', counts['未体验'] ?? 0),
        ],
      ),
    );
  }

  Widget _buildStatItem(String emoji, String label, int count) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 20)),
        const SizedBox(height: 4),
        Text(
          '$count',
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  Widget _buildOpinionCard(Map<String, dynamic> opinion) {
    final reactionType = opinion['reaction_type']?.toString() ?? '';
    final emotionWord = opinion['emotion_word']?.toString();
    final opinionText = opinion['opinion_text'] as String?;
    final anonymousName = opinion['anonymous_name'] as String? ?? '匿名用户';
    final anonymousAvatar = opinion['anonymous_avatar'] as String? ?? '🌙';
    
    // 处理 timestamp 类型（可能是 int 或 String）
    int? timestamp;
    final rawTimestamp = opinion['timestamp'];
    if (rawTimestamp is int) {
      timestamp = rawTimestamp;
    } else if (rawTimestamp is String) {
      timestamp = int.tryParse(rawTimestamp);
    }

    // 计算时间差
    String timeAgo = '';
    if (timestamp != null) {
      final diff = DateTime.now().millisecondsSinceEpoch - timestamp;
      if (diff < 60000) {
        timeAgo = '刚刚';
      } else if (diff < 3600000) {
        timeAgo = '${diff ~/ 60000}分钟前';
      } else if (diff < 86400000) {
        timeAgo = '${diff ~/ 3600000}小时前';
      } else {
        timeAgo = '${diff ~/ 86400000}天前';
      }
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 用户信息
            Row(
              children: [
                Text(anonymousAvatar, style: const TextStyle(fontSize: 24)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        anonymousName,
                        style: const TextStyle(
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (timeAgo.isNotEmpty)
                        Text(
                          timeAgo,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade500,
                          ),
                        ),
                    ],
                  ),
                ),
                // 反应标签
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: _getReactionColor(reactionType).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_getReactionEmoji(reactionType)),
                      const SizedBox(width: 4),
                      Text(
                        emotionWord ?? reactionType,
                        style: TextStyle(
                          fontSize: 12,
                          color: _getReactionColor(reactionType),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            // 评论内容
            if (opinionText != null && opinionText.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                opinionText,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.6,
                ),
              ),
            ],
          ],
        ),
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
        return '💭';
    }
  }

  Color _getReactionColor(String type) {
    switch (type) {
      case '共鸣':
        return Colors.red;
      case '无感':
        return Colors.grey;
      case '反对':
        return Colors.blueGrey;
      case '未体验':
        return Colors.orange;
      case '有害':
        return Colors.grey.shade700;
      default:
        return Colors.grey;
    }
  }
}
