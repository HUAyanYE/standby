import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../providers/core_providers.dart';

final governanceRepositoryProvider = Provider<GovernanceRepository>((ref) {
  return GovernanceRepository(ref.read(apiServiceProvider));
});

class GovernanceRepository {
  final ApiService _api;

  GovernanceRepository(this._api);

  Future<Map<String, dynamic>> evaluateContent({
    required String contentId,
    String contentType = 'anchor',
    required Map<String, int> reactionSummary,
  }) async {
    return _api.evaluateContent(
      contentId: contentId,
      contentType: contentType,
      reactionSummary: reactionSummary,
    );
  }
}
