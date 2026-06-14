import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../providers/core_providers.dart';
import '../models/seedstone.dart';

final seedstoneRepositoryProvider = Provider<SeedstoneRepository>((ref) {
  return SeedstoneRepository(ref.read(apiServiceProvider));
});

class SeedstoneRepository {
  final ApiService _api;

  SeedstoneRepository(this._api);

  Future<List<Seedstone>> listSeedstones({int page = 1, int pageSize = 20}) async {
    int retries = 0;
    while (!_api.isInitialized && retries < 10) {
      await Future.delayed(const Duration(milliseconds: 500));
      retries++;
    }
    final data = await _api.listAnchors(page: page, pageSize: pageSize);
    final list = (data['anchors'] as List?) ?? [];
    return list.map((j) => Seedstone.fromJson(j)).toList();
  }

  Future<Seedstone> getSeedstone(String id) async {
    final data = await _api.getAnchor(id);
    return Seedstone.fromJson(data);
  }

  Future<Map<String, dynamic>> createSeedstone({
    required List<String> sourceTexts,
    List<String>? topicHints,
    String source = 'user',
    String modality = 'text',
  }) async {
    return _api.createAnchor(
      sourceTexts: sourceTexts,
      topicHints: topicHints,
      source: source,
      modality: modality,
    );
  }

  Future<Map<String, dynamic>> getFeelingChain(String anchorId, {int maxDepth = 3}) async {
    return _api.getFeelingChain(anchorId, maxDepth: maxDepth);
  }

  Future<Map<String, dynamic>> getGroupMemory(String anchorId) async {
    return _api.getGroupMemory(anchorId);
  }
}
