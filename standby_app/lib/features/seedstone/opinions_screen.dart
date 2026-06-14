import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../shared/services/api_service.dart';
import '../../shared/models/seedstone.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

/// 感想列表页 — 显示某个心物下的所有感受
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

  static const _prefixes = [
    '夜的', '晨曦', '微风', '秋日', '冬雪', '春水', '夏雨', '远山',
    '近海', '深林', '浅滩', '孤星', '流云', '闲鹤', '静湖', '暖阳',
  ];
  static const _suffixes = [
    '旅人', '过客', '归人', '行者', '诗人', '歌者', '守望', '聆听',
    '沉思', '静默', '观察', '等待', '漂流', '停泊', '游荡', '栖息',
  ];
  static const _avatars = [
    '🌙', '☀️', '🌊', '🍂', '🌸', '❄️', '🌿', '🍃', '☁️', '⭐',
    '🌻', '🍁', '🦋', '🐱', '🦊', '🐰', '🐻', '🐼', '🐨', '🦁',
  ];

  String _anonName(String userId) {
    final hash = userId.hashCode.abs();
    return '${_prefixes[hash % _prefixes.length]}${_suffixes[(hash ~/ _prefixes.length) % _suffixes.length]}';
  }

  String _anonAvatar(String userId) {
    return _avatars[userId.hashCode.abs() % _avatars.length];
  }

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

  String _formatTime(dynamic timestamp) {
    final ts = (timestamp as num?)?.toInt() ?? 0;
    final ms = ts > 1e12 ? ts : ts * 1000;
    final date = DateTime.fromMillisecondsSinceEpoch(ms);
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 1) return '刚刚';
    if (diff.inHours < 1) return '${diff.inMinutes}分钟前';
    if (diff.inDays < 1) return '${diff.inHours}小时前';
    if (diff.inDays < 30) return '${diff.inDays}天前';
    return '${date.month}月${date.day}日';
  }

  String? _emotionWordToString(dynamic value) {
    if (value == null) return null;
    final v = value is int ? value : int.tryParse(value.toString());
    switch (v) {
      case 1: return '同感';
      case 2: return '触发';
      case 3: return '启发';
      case 4: return '震撼';
      default: return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('感受'),
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
                        '还没有感受',
                        style: TextStyle(fontSize: 16, color: context.text2Color),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '第一个写下你的感受',
                        style: TextStyle(fontSize: 14, color: context.text3Color),
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
    final userId = (opinion['user_id'] as String?) ?? '';
    final textContent = (opinion['text_content'] as String?) ?? (opinion['opinion_text'] as String?) ?? '';
    final createdAt = (opinion['created_at'] as num?)?.toInt() ?? 0;
    final emotionStr = _emotionWordToString(opinion['emotion_word']);

    final name = userId.isNotEmpty ? _anonName(userId) : '无名者';
    final avatar = userId.isNotEmpty ? _anonAvatar(userId) : '🌙';

    return Container(
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
          Row(
            children: [
              Text(avatar, style: const TextStyle(fontSize: 22)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: context.textColor,
                      ),
                    ),
                    Text(
                      _formatTime(createdAt),
                      style: TextStyle(fontSize: 11, color: context.text3Color),
                    ),
                  ],
                ),
              ),
              if (emotionStr != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: StandbyColors.primarySoft,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    emotionStr,
                    style: const TextStyle(fontSize: 11, color: StandbyColors.primary, fontWeight: FontWeight.w500),
                  ),
                ),
            ],
          ),
          if (textContent.isNotEmpty) ...[
            const SizedBox(height: 14),
            Text(
              textContent,
              style: StandbyTextStyles.body.copyWith(height: 1.7),
            ),
          ],
        ],
      ),
    );
  }
}
