import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/services/api_service.dart';
import '../../shared/models/seedstone.dart';
import '../../shared/widgets/media_preview.dart';
import '../../shared/widgets/standby_empty_state.dart';
import '../../shared/utils/anonymity.dart';
import '../../shared/utils/formatters.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

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

      // 加载感受链（子心物列表）
      final chainData = await _api.getFeelingChain(widget.seedstoneId);
      final nodes = chainData['nodes'];
      final List<dynamic> rawList = nodes is List ? nodes : [];
      _reactions = rawList.map((e) {
        if (e is Map<String, dynamic>) return e;
        return Map<String, dynamic>.from(e as Map);
      }).toList();

      setState(() => _loading = false);
    } catch (e) {
      setState(() {
        _loading = false;
        _error = '加载失败';
      });
    }
  }

  // ── 匿名身份：使用共享工具类 ──

  // ── 情绪词映射：使用共享工具类 ──

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
                      Text(_error!, style: TextStyle(color: context.text2Color)),
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
                        const SizedBox(height: 32),
                        _buildFeelingChain(),
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
        color: context.surface1,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(color: context.borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (seedstone.hasMedia && seedstone.primaryMedia != null) ...[
            MediaPreview(media: seedstone.primaryMedia!, height: 200),
            const SizedBox(height: 16),
          ],
          if (seedstone.hasText)
            Text(
              seedstone.textContent!,
              style: StandbyTextStyles.body.copyWith(height: 1.8, fontSize: 16),
            ),
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

  Widget _buildFeelingChain() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text('感受链', style: StandbyTextStyles.h3),
            const SizedBox(width: 8),
            Text(
              '${_reactions.length}',
              style: TextStyle(fontSize: 14, color: context.text3Color),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          '每个人对这个心物的独立感受',
          style: TextStyle(fontSize: 12, color: context.text3Color),
        ),
        const SizedBox(height: 16),
        if (_reactions.isEmpty)
          const StandbyEmptyState(
            emoji: '💭',
            title: '还没有人留下感受',
            description: '第一个写下你的感受吧',
          )
        else
          ...List.generate(_reactions.length, (i) {
            return Padding(
              padding: EdgeInsets.only(bottom: i < _reactions.length - 1 ? 12 : 0),
              child: _buildFeelingCard(_reactions[i]),
            );
          }),
      ],
    );
  }

  Widget _buildFeelingCard(Map<String, dynamic> reaction) {
    final userId = (reaction['user_id'] as String?) ?? '';
    final textContent = (reaction['text_content'] as String?) ?? (reaction['opinion_text'] as String?) ?? '';
    final emotionStr = Formatters.emotionWordLabel(reaction['emotion_word']);
    final createdAt = (reaction['created_at'] as num?)?.toInt() ?? 0;

    final name = userId.isNotEmpty ? Anonymity.nameFromId(userId) : '无名者';
    final avatar = userId.isNotEmpty ? Anonymity.avatarFromId(userId) : '🌙';

    final feelingAnchorId = (reaction['anchor_id'] as String?) ?? (reaction['reaction_id'] as String?) ?? '';

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: StandbyRadius.cardRadius,
        splashColor: StandbyColors.primarySoft,
        highlightColor: StandbyColors.primarySoft,
        onTap: () {
          if (feelingAnchorId.isNotEmpty) {
            context.push('/seedstone/$feelingAnchorId');
          }
        },
        child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: context.surface1,
          borderRadius: StandbyRadius.cardRadius,
          border: Border.all(color: context.borderColor),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 匿名身份行
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
                      if (createdAt > 0)
                        Text(
                          Formatters.formatTime(createdAt),
                          style: TextStyle(fontSize: 11, color: context.text3Color),
                        ),
                    ],
                  ),
                ),
                // 情绪标签
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

            // 感受内容
            if (textContent.isNotEmpty) ...[
              const SizedBox(height: 14),
              Text(
                textContent,
                style: TextStyle(fontSize: 16, height: 1.8, color: context.textColor),
              ),
            ],

            // 底部：独立心物入口
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.favorite_outline, size: 14, color: context.text3Color),
                const SizedBox(width: 4),
                Text(
                  '我也有所感',
                  style: TextStyle(fontSize: 12, color: context.text3Color),
                ),
                const Spacer(),
                Text(
                  '查看 →',
                  style: TextStyle(fontSize: 12, color: StandbyColors.primary.withAlpha(180)),
                ),
              ],
            ),
          ],
        ),
      ),
      ),
    );
  }

}
