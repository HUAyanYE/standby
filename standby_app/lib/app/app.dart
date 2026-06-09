import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'router.dart';
import 'theme.dart';

/// Standby App — 根组件
class StandbyApp extends ConsumerWidget {
  const StandbyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(goRouterProvider);

    return MaterialApp.router(
      title: 'Standby',
      debugShowCheckedModeBanner: false,
      theme: buildStandbyTheme(),
      routerConfig: router,
    );
  }
}
