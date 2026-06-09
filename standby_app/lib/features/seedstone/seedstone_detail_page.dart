import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../shared/services/api_service.dart';
import '../../shared/models/seedstone.dart';
import '../../shared/widgets/media_preview.dart';
import '../../app/theme.dart';

/// 心物详情页 — 显示心物内容 + 感受链
class SeedstoneDetailPage extends ConsumerStatefulWidget {
  final String seedstoneId;

  const SeedstoneDetailPage({super.key, required this.seedstoneId});

  @override
  ConsumerState<SeedstoneDetailPage> createState() => _SeedstoneDetailPageState();
}

class _SeedstoneDetailPageState extends ConsumerState<SeedstoneDetailPage> {
  final _api = ApiService();
  Seedstone? _seedstone;
  List<Map<String, dynamic>> _reactions = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final anchorData = await _api.getAnchor(widget.seedstoneId);
      _seedstone = Seedstone.fromJson(anchorData);

      final reactionsData = await _api.listReactions(widget.seedstoneId, pageSize: 50);
      _reactions = (reactionsData['reactions'] as List?)?.cast<Map<String, dynamic>>() ?? [];

      setState(() => _loading = false);
    } catch (e) {
      setState(() {
        _loading = false;
        _error = '加载失败';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('心物详情'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(_error!, style: const TextStyle(color: StandbyColors.text2)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadData,
                        child: const Text('重试'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadData,
                  child: SingleChildScrollView(
                    padding: StandbySpacing.pagePadding,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSeedstoneCard(),
                        const SizedBox(height: 24),
                        _buildReactionChain(),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildSeedstoneCard() {
    final seedstone = _seedstone!;
    return Container(
      width: double.infinity,
      padding: StandbySpacing.cardPadding,
      decoration: BoxDecoration(
        color: StandbyColors.surface1,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(color: StandbyColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 媒体
          if (seedstone.hasMedia && seedstone.primaryMedia != null) ...[
            MediaPreview(media: seedstone.primaryMedia!, height: 200),
            const SizedBox(height: 16),
          ],

          // 文本内容
          if (seedstone.hasText)
            Text(
              seedstone.textContent!,
              style: StandbyTextStyles.body.copyWith(height: 1.8),
            ),

          // 话题标签
          if (seedstone.topics.isNotEmpty) ...[
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: seedstone.topics.map((topic) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: StandbyColors.primarySoft,
                    borderRadius: StandbyRadius.tagRadius,
                  ),
                  child: Text(
                    '#$topic',
                    style: const TextStyle(fontSize: 13, color: StandbyColors.primary),
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildReactionChain() {
    if (_reactions.isEmpty) {
      return Container(
        padding: StandbySpacing.cardPadding,
        decoration: BoxDecoration(
          color: StandbyColors.surface1,
          borderRadius: StandbyRadius.cardRadius,
          border: Border.all(color: StandbyColors.border),
        ),
        child: Center(
          child: Column(
            children: [
              const Text('💭', style: TextStyle(fontSize: 32)),
              const SizedBox(height: 12),
              Text(
                '还没有感受',
                style: TextStyle(fontSize: 14, color: StandbyColors.text2),
              ),
              const SizedBox(height: 4),
              Text(
                '第一个写下你的感想',
                style: TextStyle(fontSize: 12, color: StandbyColors.text3),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '感受链',
          style: StandbyTextStyles.h3,
        ),
        const SizedBox(height: 16),
        ..._reactions.map((reaction) => _buildReactionCard(reaction)),
      ],
    );
  }

  Widget _buildReactionCard(Map<String, dynamic> reaction) {
    final textContent = reaction['text_content'] as String? ?? '';
    final anonymousName = reaction['anonymous_name'] as String? ?? '匿名用户';
    final anonymousAvatar = reaction['anonymous_avatar'] as String? ?? '🌙';
    final emotionWord = reaction['emotion_word'] as String?;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: StandbyColors.surface2,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(color: StandbyColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 匿名身份
          Row(
            children: [
              Text(anonymousAvatar, style: const TextStyle(fontSize: 20)),
              const SizedBox(width: 8),
              Text(
                anonymousName,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: StandbyColors.text,
                ),
              ),
              if (emotionWord != null) ...[
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: StandbyColors.primarySoft,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    emotionWord,
                    style: const TextStyle(fontSize: 11, color: StandbyColors.primary),
                  ),
                ),
              ],
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
