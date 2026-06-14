import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../shared/services/storage_service.dart';
import 'theme.dart';

enum AppThemeMode { dark, light, system }

final themeModeProvider = StateNotifierProvider<ThemeModeNotifier, AppThemeMode>((ref) {
  return ThemeModeNotifier();
});

class ThemeModeNotifier extends StateNotifier<AppThemeMode> {
  ThemeModeNotifier() : super(AppThemeMode.dark) {
    _load();
  }

  void _load() {
    final saved = StorageService().themeMode;
    switch (saved) {
      case 'light':
        state = AppThemeMode.light;
        break;
      case 'system':
        state = AppThemeMode.system;
        break;
      default:
        state = AppThemeMode.dark;
    }
  }

  Future<void> setMode(AppThemeMode mode) async {
    state = mode;
    await StorageService().setThemeMode(mode.name);
  }

  ThemeMode get flutterThemeMode {
    switch (state) {
      case AppThemeMode.light:
        return ThemeMode.light;
      case AppThemeMode.system:
        return ThemeMode.system;
      case AppThemeMode.dark:
        return ThemeMode.dark;
    }
  }
}

ThemeData buildStandbyLightTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.light(
      primary: StandbyColors.primary,
      surface: StandbyColors.lightSurface1,
      onSurface: StandbyColors.lightText,
    ),
    scaffoldBackgroundColor: StandbyColors.lightBackground,
    appBarTheme: AppBarTheme(
      backgroundColor: StandbyColors.lightBackground,
      foregroundColor: StandbyColors.lightText,
      elevation: 0,
      scrolledUnderElevation: 0,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: StandbyColors.lightSurface1,
      indicatorColor: StandbyColors.primarySoft,
      labelTextStyle: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return StandbyTextStyles.label.copyWith(color: StandbyColors.primary);
        }
        return StandbyTextStyles.label.copyWith(color: StandbyColors.lightText3);
      }),
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: StandbyColors.primary);
        }
        return IconThemeData(color: StandbyColors.lightText3);
      }),
    ),
    cardTheme: CardThemeData(
      color: StandbyColors.lightSurface1,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: StandbyRadius.cardRadius,
        side: BorderSide(color: StandbyColors.lightBorder),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: StandbyColors.lightSurface2,
      contentTextStyle: StandbyTextStyles.body.copyWith(color: StandbyColors.lightText),
      shape: RoundedRectangleBorder(borderRadius: StandbyRadius.buttonRadius),
    ),
    dividerTheme: DividerThemeData(
      color: StandbyColors.lightBorder,
      thickness: 1,
    ),
  );
}
