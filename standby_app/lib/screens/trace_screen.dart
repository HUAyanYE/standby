import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// 痕迹页 — 共鸣发现
class TraceScreen extends StatefulWidget {
  final ApiService api;

  const TraceScreen({super.key, required this.api});

  @override
  State<TraceScreen> createState() => _TraceScreenState();
}

class _TraceScreenState extends State<TraceScreen> {
  // 模拟数据
  final List<_TraceData> _traces = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadTraces();
  }

  Future<void> _loadTraces() async {
    setState(() => _loading = true);

    try {
      // 等待 API 初始化完成 (和遇见页一样的 retry 逻辑)
      int retries = 0;
      while (!widget.api.isInitialized && retries < 10) {
        print('API 未初始化，等待中... (尝试 ${retries + 1}/10)');
        await Future.delayed(const Duration(milliseconds: 500));
        retries++;
      }

      if (!widget.api.isInitialized) {
        print('API 初始化超时，尝试继续...');
      }

      final data = await widget.api.getResonanceTraces();
      final tracesData = data['traces'] as List? ?? [];
      
      setState(() {
        _traces.clear();
        _traces.addAll(tracesData.map((item) => _TraceData.fromJson(item)));
        _loading = false;
      });
    } catch (e) {
      print('加载痕迹失败: $e');
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('痕迹'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 标题
                  Text(
                    '近期频繁共鸣',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 痕迹列表
                  ..._traces.map((trace) => _buildTraceCard(trace)),
                  const SizedBox(height: 24),

                  // 知己区域
                  _buildConfidantSection(),
                ],
              ),
            ),
    );
  }

  Widget _buildTraceCard(_TraceData trace) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 用户信息
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
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Text(
                      '${trace.sharedAnchors} 个共同锚点',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey.shade500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // 共同话题
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: trace.topics.map((topic) => Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.indigo.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                topic,
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.indigo.shade400,
                ),
              ),
            )).toList(),
          ),
          const SizedBox(height: 12),

          // 最近共鸣
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Row(
              children: [
                Icon(Icons.format_quote, size: 16, color: Colors.grey.shade400),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    trace.lastAnchorText,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey.shade600,
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

  Widget _buildConfidantSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.amber.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.amber.shade100),
      ),
      child: Column(
        children: [
          const Text('🕯', style: TextStyle(fontSize: 32)),
          const SizedBox(height: 8),
          const Text(
            '知己',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '暂时无人',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '共鸣需要时间沉淀',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade500,
            ),
          ),
        ],
      ),
    );
  }
}

class _TraceData {
  final String avatar;
  final String nickname;
  final int sharedAnchors;
  final List<String> topics;
  final String lastAnchorText;

  _TraceData({
    required this.avatar,
    required this.nickname,
    required this.sharedAnchors,
    required this.topics,
    required this.lastAnchorText,
  });

  factory _TraceData.fromJson(Map<String, dynamic> json) {
    return _TraceData(
      avatar: json['avatar'] as String? ?? '👤',
      nickname: json['nickname'] as String? ?? '匿名用户',
      sharedAnchors: json['shared_anchors'] as int? ?? 0,
      topics: (json['topics'] as List?)?.cast<String>() ?? [],
      lastAnchorText: json['last_anchor_text'] as String? ?? '',
    );
  }
}
