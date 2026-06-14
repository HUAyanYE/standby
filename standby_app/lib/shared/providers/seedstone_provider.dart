import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core_providers.dart';
import '../models/seedstone.dart';

final seedstoneListProvider = AsyncNotifierProvider<SeedstoneListNotifier, List<Seedstone>>(SeedstoneListNotifier.new);

class SeedstoneListNotifier extends AsyncNotifier<List<Seedstone>> {
  @override
  Future<List<Seedstone>> build() => _fetch();

  Future<List<Seedstone>> _fetch() async {
    final api = ref.read(apiServiceProvider);
    int retries = 0;
    while (!api.isInitialized && retries < 10) {
      await Future.delayed(const Duration(milliseconds: 500));
      retries++;
    }
    final data = await api.listAnchors(page: 1, pageSize: 20);
    final list = (data['anchors'] as List?) ?? [];
    final seedstones = list.map((j) => Seedstone.fromJson(j)).toList();
    seedstones.shuffle();
    return seedstones;
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetch());
  }
}

final myReactionsProvider = NotifierProvider<MyReactionsNotifier, List<Map<String, dynamic>>>(MyReactionsNotifier.new);

class MyReactionsNotifier extends Notifier<List<Map<String, dynamic>>> {
  @override
  List<Map<String, dynamic>> build() => _load();

  List<Map<String, dynamic>> _load() {
    final storage = ref.read(storageServiceProvider);
    return storage.myReactions;
  }

  void refresh() {
    state = _load();
  }
}

final myPostsProvider = NotifierProvider<MyPostsNotifier, List<Map<String, dynamic>>>(MyPostsNotifier.new);

class MyPostsNotifier extends Notifier<List<Map<String, dynamic>>> {
  @override
  List<Map<String, dynamic>> build() => _load();

  List<Map<String, dynamic>> _load() {
    final storage = ref.read(storageServiceProvider);
    return storage.myPosts;
  }

  void refresh() {
    state = _load();
  }
}
