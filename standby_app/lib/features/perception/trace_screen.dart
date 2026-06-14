import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/services/api_service.dart';
import '../../shared/models/trace.dart';
import '../../shared/widgets/standby_empty_state.dart';
import '../../shared/providers/feature_unlock_provider.dart';
import '../../app/theme.dart';
import '../../app/theme_colors.dart';

/// 痕迹页 — 共鸣轨迹、关系脉络
class TraceScreen extends ConsumerStatefulWidget {
  const TraceScreen({super.key});

  @override
  ConsumerState<TraceScreen> createState() => _TraceScreenState();
}

class _TraceScreenState extends ConsumerState<TraceScreen> {
  final _api = ApiService();
  List<Trace> _traces = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadTraces();
  }

  Future<void> _loadTraces() async {
    setState(() => _loading = true);

    try {
      int retries = 0;
      while (!_api.isInitialized && retries < 10) {
        await Future.delayed(const Duration(milliseconds: 500));
        retries++;
      }

      final data = await _api.getResonanceTraces();
      final tracesData = data['traces'] as List? ?? [];

      setState(() {
        _traces = tracesData.map((item) => Trace.fromJson(item)).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final confidantUnlocked = ref.watch(featureUnlockProvider(FeatureType.confidantChat));

    return Scaffold(
      appBar: AppBar(title: const Text('痕迹')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: StandbySpacing.pagePadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('近期频繁共鸣', style: TextStyle(fontSize: 14, color: context.text2Color)),
                  const SizedBox(height: 16),
                  if (_traces.isEmpty)
                    const StandbyEmptyState(
                      emoji: '🌿',
                      title: '暂无痕迹',
                      description: '多写感想，共鸣自然会出现',
                    )
                  else
                    ..._traces.map((trace) => _buildTraceCard(trace)),
                  const SizedBox(height: 24),
                  _buildConfidantSection(confidantUnlocked),
                ],
              ),
            ),
    );
  }

  Widget _buildTraceCard(Trace trace) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
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
              Text(trace.avatar, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      trace.nickname,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        color: context.textColor,
                      ),
                    ),
                    Text(
                      '${trace.sharedAnchors} 个共同心物',
                      style: TextStyle(fontSize: 12, color: context.text3Color),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: trace.sharedTopics.map((topic) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: StandbyColors.primarySoft,
                borderRadius: StandbyRadius.tagRadius,
              ),
              child: Text(topic, style: const TextStyle(fontSize: 11, color: StandbyColors.primary)),
            )).toList(),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: context.surface2,
              borderRadius: BorderRadius.circular(StandbyRadius.sm),
              border: Border.all(color: context.borderColor),
            ),
            child: Row(
              children: [
                Icon(Icons.format_quote, size: 16, color: context.text3Color),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    trace.lastAnchorText,
                    style: TextStyle(
                      fontSize: 13,
                      color: context.text2Color,
                      fontStyle: FontStyle.italic,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConfidantSection(bool isUnlocked) {
    return AnimatedOpacity(
      opacity: isUnlocked ? 1.0 : 0.6,
      duration: StandbyDuration.slow,
      child: Container(
        padding: StandbySpacing.cardPadding,
        decoration: BoxDecoration(
          color: isUnlocked ? context.surface2 : context.surface1,
          borderRadius: StandbyRadius.cardRadius,
          border: Border.all(color: isUnlocked ? StandbyColors.primarySoft : context.borderColor),
        ),
        child: Column(
          children: [
            const Text('🕯', style: TextStyle(fontSize: 32)),
            const SizedBox(height: 8),
            Text(
              '知己',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: isUnlocked ? context.textColor : context.text2Color,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              isUnlocked ? '查看知己' : '在共鸣中自然浮现',
              style: TextStyle(fontSize: 14, color: context.text2Color),
            ),
            if (isUnlocked) ...[
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => context.push('/confidant'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: StandbyColors.primary,
                  foregroundColor: Colors.white,
                ),
                child: const Text('进入知己'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
