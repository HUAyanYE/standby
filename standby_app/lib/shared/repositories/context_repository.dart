import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../providers/core_providers.dart';

final contextRepositoryProvider = Provider<ContextRepository>((ref) {
  return ContextRepository(ref.read(apiServiceProvider));
});

class ContextRepository {
  final ApiService _api;

  ContextRepository(this._api);

  Future<void> submitContextState({
    required String sceneType,
    String? moodHint,
    String? attentionLevel,
    int? activeDevice,
  }) async {
    await _api.submitContextState(
      sceneType: sceneType,
      moodHint: moodHint,
      attentionLevel: attentionLevel,
      activeDevice: activeDevice,
    );
  }

  Future<Map<String, dynamic>> getContextualWeights(List<String> topics) async {
    return _api.getContextualWeights(topics);
  }
}
