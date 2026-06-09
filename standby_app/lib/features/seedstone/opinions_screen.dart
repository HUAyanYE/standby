import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../shared/services/api_service.dart';
import '../../shared/models/seedstone.dart';
import '../../app/theme.dart';

/// 感想列表页 — 显示某个心物下的所有感想
class OpinionsScreen extends ConsumerStatefulWidget {
  final Seedstone seedstone;

  const OpinionsScreen({super.key, required this.seedstone});

  @override
  ConsumerState<OpinionsScreen> createState() => _OpinionsScreenState();
}

class _OpinionsScreenState extends ConsumerState<OpinionsScreen> {
  final _api = ApiService();
  List<Map<String, dynamic>> _opinions = [];
  bool _loading = true;
  int _page = 1;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _loadOpinions();
  }

  Future<void> _loadOpinions({bool loadMore = false}) async {
    if (loadMore) {
      _page++;
    } else {
      _page = 1;
      _opinions.clear();
    }

    setState(() => _loading = true);

    try {
      final data = await _api.listReactions(
        widget.seedstone.seedstoneId,
        page: _page,
        pageSize: 20,
      );
      final list = (data['reactions'] as List?)?.cast<Map<String, dynamic>>() ?? [];
      
      setState(() {
        _opinions.addAll(list);
        _hasMore = list.length >= 20;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  String _timeAgo(int timestamp) {
    final date = DateTime.fromMillisecondsSinceEpoch(timestamp * 1000);
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return '刚刚';
    if (diff.inHours < 1) return '${diff.inMinutes}分钟前';
    if (diff.inDays < 1) return '${diff.inHours}小时前';
    if (diff.inDays < 30) return '${diff.inDays}天前';
    return '${date.month}月${date.day}日';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('感想'),
      ),
      body: _opinions.isEmpty && _loading
          ? const Center(child: CircularProgressIndicator())
          : _opinions.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('💭', style: TextStyle(fontSize: 48)),
                      const SizedBox(height: 16),
                      Text(
                        '还没有感想',
                        style: TextStyle(fontSize: 16, color: StandbyColors.text2),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '第一个写下你的感受',
                        style: TextStyle(fontSize: 14, color: StandbyColors.text3),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => _loadOpinions(),
                  child: ListView.builder(
                    padding: StandbySpacing.pagePadding,
                    itemCount: _opinions.length + (_hasMore ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == _opinions.length) {
                        if (_loading) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        _loadOpinions(loadMore: true);
                        return const SizedBox.shrink();
                      }
                      return _buildOpinionCard(_opinions[index]);
                    },
                  ),
                ),
    );
  }

  Widget _buildOpinionCard(Map<String, dynamic> opinion) {
    final textContent = opinion['text_content'] as String? ?? '';
    final anonymousName = opinion['anonymous_name'] as String? ?? '匿名用户';
    final anonymousAvatar = opinion['anonymous_avatar'] as String? ?? '🌙';
    final createdAt = opinion['created_at'] as int? ?? 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: StandbyColors.surface1,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(color: StandbyColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(anonymousAvatar, style: const TextStyle(fontSize: 20)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  anonymousName,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: StandbyColors.text,
                  ),
                ),
              ),
              Text(
                _timeAgo(createdAt),
                style: const TextStyle(fontSize: 12, color: StandbyColors.text3),
              ),
            ],
          ),
          if (textContent.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(
              textContent,
              style: StandbyTextStyles.body,
            ),
          ],
        ],
      ),
    );
  }
}
