import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../providers/core_providers.dart';

final reactionRepositoryProvider = Provider<ReactionRepository>((ref) {
  return ReactionRepository(
    ref.read(apiServiceProvider),
    ref.read(storageServiceProvider),
  );
});

class ReactionRepository {
  final ApiService _api;
  final StorageService _storage;

  ReactionRepository(this._api, this._storage);

  Future<Map<String, dynamic>> submitReaction({
    required String anchorId,
    required int reactionType,
    String? opinionText,
    int? emotionWord,
  }) async {
    return _api.submitReaction(
      anchorId: anchorId,
      reactionType: reactionType,
      opinionText: opinionText,
      emotionWord: emotionWord,
    );
  }

  Future<Map<String, dynamic>> listReactions(
    String anchorId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    return _api.listReactions(anchorId, page: page, pageSize: pageSize);
  }

  Future<Map<String, dynamic>> getReactionDistribution(String anchorId) async {
    return _api.getReactionDistribution(anchorId);
  }

  Future<void> saveLocalReaction(Map<String, dynamic> reaction) async {
    await _storage.addMyReaction(reaction);
  }

  List<Map<String, dynamic>> getLocalReactions() {
    return _storage.myReactions;
  }
}
