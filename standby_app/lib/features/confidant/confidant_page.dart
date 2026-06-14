import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../shared/services/api_service.dart';
import '../../shared/services/storage_service.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

/// 知己页 — 匿名知己列表、共鸣引用
class ConfidantPage extends ConsumerStatefulWidget {
  const ConfidantPage({super.key});

  @override
  ConsumerState<ConfidantPage> createState() => _ConfidantPageState();
}

class _ConfidantPageState extends ConsumerState<ConfidantPage> {
  final _api = ApiService();
  final _storage = StorageService();
  List<Map<String, dynamic>> _confidants = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadConfidants();
  }

  Future<void> _loadConfidants() async {
    setState(() => _loading = true);

    try {
      final userId = _storage.deviceFingerprint ?? '';
      final data = await _api.getRelationships(userId);
      final relationships = data['relationships'] as List? ?? [];
      
      setState(() {
        _confidants = relationships.cast<Map<String, dynamic>>();
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _confidants = [];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('知己')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _confidants.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _loadConfidants,
                  child: ListView.builder(
                    padding: StandbySpacing.pagePadding,
                    itemCount: _confidants.length,
                    itemBuilder: (context, index) => _buildConfidantCard(_confidants[index]),
                  ),
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: StandbySpacing.pagePadding,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('🕯', style: TextStyle(fontSize: 64)),
            const SizedBox(height: 24),
            Text('知己', style: StandbyTextStyles.h1),
            const SizedBox(height: 16),
            Text(
              '在 Standby，知己不是主动寻找的，\n而是在共鸣中自然浮现的。',
              style: TextStyle(fontSize: 16, color: context.text2Color, height: 1.8),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Text(
              '当你与同一个人在不同心物上多次产生共鸣，\n系统会悄悄告诉你：\n「有个人总是跟你有同样的感受」',
              style: TextStyle(fontSize: 14, color: context.text3Color, height: 1.8),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(
                color: context.surface2,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '继续写感想，知己会出现的',
                style: TextStyle(fontSize: 14, color: context.text2Color),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConfidantCard(Map<String, dynamic> confidant) {
    final avatar = confidant['avatar'] as String? ?? '🌙';
    final nickname = confidant['nickname'] as String? ?? '匿名知己';
    final sharedAnchors = confidant['shared_anchors'] as int? ?? 0;
    final lastResonanceText = confidant['last_resonance_text'] as String? ?? '';
    final depth = confidant['depth'] as double? ?? 0.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: StandbySpacing.cardPadding,
      decoration: BoxDecoration(
        color: context.surface1,
        borderRadius: StandbyRadius.cardRadius,
        border: Border.all(
          color: StandbyColors.primary.withAlpha((depth * 180).toInt().clamp(20, 180)),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: StandbyColors.primary.withAlpha((depth * 60).toInt().clamp(10, 60)),
                  shape: BoxShape.circle,
                ),
                child: Center(child: Text(avatar, style: const TextStyle(fontSize: 24))),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(nickname, style: StandbyTextStyles.h3),
                    const SizedBox(height: 4),
                    Text(
                      '$sharedAnchors 个共同心物',
                      style: TextStyle(fontSize: 12, color: context.text3Color),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (lastResonanceText.isNotEmpty) ...[
            const SizedBox(height: 16),
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
                      lastResonanceText,
                      style: TextStyle(
                        fontSize: 13,
                        color: context.text2Color,
                        fontStyle: FontStyle.italic,
                        height: 1.5,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

}
