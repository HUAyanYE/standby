import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/seedstone.dart';

/// 心物列表状态
final seedstoneListProvider = StateNotifierProvider<SeedstoneListNotifier, AsyncValue<List<Seedstone>>>((ref) {
  return SeedstoneListNotifier(ref);
});

class SeedstoneListNotifier extends StateNotifier<AsyncValue<List<Seedstone>>> {
  final Ref _ref;
  
  SeedstoneListNotifier(this._ref) : super(const AsyncValue.loading()) {
    load();
  }

  Future<void> load() async {
    state = const AsyncValue.loading();
    try {
      final api = ApiService();
      // 等待 API 初始化
      int retries = 0;
      while (!api.isInitialized && retries < 10) {
        await Future.delayed(const Duration(milliseconds: 500));
        retries++;
      }

      final data = await api.listAnchors(page: 1, pageSize: 20);
      final list = (data['anchors'] as List?) ?? [];
      final seedstones = list.map((j) => Seedstone.fromJson(j)).toList();
      seedstones.shuffle();
      state = AsyncValue.data(seedstones);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> refresh() => load();
}

/// 用户反应记录 Provider
final myReactionsProvider = StateNotifierProvider<MyReactionsNotifier, List<Map<String, dynamic>>>((ref) {
  return MyReactionsNotifier();
});

class MyReactionsNotifier extends StateNotifier<List<Map<String, dynamic>>> {
  MyReactionsNotifier() : super([]) {
    _load();
  }

  void _load() {
    final storage = StorageService();
    state = storage.myReactions;
  }

  void refresh() => _load();
}

/// 用户发布记录 Provider
final myPostsProvider = StateNotifierProvider<MyPostsNotifier, List<Map<String, dynamic>>>((ref) {
  return MyPostsNotifier();
});

class MyPostsNotifier extends StateNotifier<List<Map<String, dynamic>>> {
  MyPostsNotifier() : super([]) {
    _load();
  }

  void _load() {
    final storage = StorageService();
    state = storage.myPosts;
  }

  void refresh() => _load();
}
