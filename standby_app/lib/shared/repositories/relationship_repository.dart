import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../providers/core_providers.dart';

final relationshipRepositoryProvider = Provider<RelationshipRepository>((ref) {
  return RelationshipRepository(ref.read(apiServiceProvider));
});

class RelationshipRepository {
  final ApiService _api;

  RelationshipRepository(this._api);

  Future<Map<String, dynamic>> getRelationships(String userId) async {
    return _api.getRelationships(userId);
  }

  Future<Map<String, dynamic>> getRelationshipScore(String userA, String userB) async {
    return _api.getRelationshipScore(userA, userB);
  }

  Future<Map<String, dynamic>> findResonancePairs(String userId) async {
    return _api.findResonancePairs(userId);
  }

  Future<Map<String, dynamic>> getResonanceTraces({int page = 1, int pageSize = 20}) async {
    return _api.getResonanceTraces(page: page, pageSize: pageSize);
  }
}
