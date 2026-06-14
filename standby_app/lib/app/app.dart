import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'router.dart';
import 'theme.dart';
import 'theme_provider.dart';

/// Standby App — 根组件
class StandbyApp extends ConsumerWidget {
  const StandbyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(goRouterProvider);
    final themeMode = ref.watch(themeModeProvider);

    ThemeMode flutterMode;
    switch (themeMode) {
      case AppThemeMode.light:
        flutterMode = ThemeMode.light;
        break;
      case AppThemeMode.system:
        flutterMode = ThemeMode.system;
        break;
      case AppThemeMode.dark:
        flutterMode = ThemeMode.dark;
        break;
    }

    return MaterialApp.router(
      title: 'Standby',
      debugShowCheckedModeBanner: false,
      theme: buildStandbyLightTheme(),
      darkTheme: buildStandbyTheme(),
      themeMode: flutterMode,
      routerConfig: router,
    );
  }
}
