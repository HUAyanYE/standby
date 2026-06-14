import 'package:flutter/material.dart';

/// Standby 暗色主题系统
/// 基于 docs/4-Flutter设计方案.md 七、设计规范

class StandbyColors {
  static const primary = Color(0xFFE74C3C);
  static const primarySoft = Color(0x26E74C3C);
  static const background = Color(0xFF0A0A0A);
  static const surface1 = Color(0xFF141414);
  static const surface2 = Color(0xFF1C1C1C);
  static const surface3 = Color(0xFF242424);
  static const text = Color(0xFFE8E8E8);
  static const text2 = Color(0xFF999999);
  static const text3 = Color(0xFF666666);
  static const border = Color(0x0FFFFFFF);

  // 亮色主题
  static const lightBackground = Color(0xFFF5F5F5);
  static const lightSurface1 = Color(0xFFFFFFFF);
  static const lightSurface2 = Color(0xFFF0F0F0);
  static const lightSurface3 = Color(0xFFE8E8E8);
  static const lightText = Color(0xFF1A1A1A);
  static const lightText2 = Color(0xFF666666);
  static const lightText3 = Color(0xFF999999);
  static const lightBorder = Color(0x1A000000);
}

class StandbyTextStyles {
  static const h1 = TextStyle(fontSize: 28, fontWeight: FontWeight.w600, letterSpacing: -0.5, color: StandbyColors.text);
  static const h2 = TextStyle(fontSize: 22, fontWeight: FontWeight.w500, color: StandbyColors.text);
  static const h3 = TextStyle(fontSize: 20, fontWeight: FontWeight.w600, letterSpacing: -0.3, color: StandbyColors.text);
  static const body = TextStyle(fontSize: 15, fontWeight: FontWeight.w400, height: 1.8, color: StandbyColors.text);
  static const label = TextStyle(fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1.5, color: StandbyColors.text2);
  static const button = TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: StandbyColors.text);
}

class StandbySpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const pagePadding = EdgeInsets.all(20);
  static const cardPadding = EdgeInsets.all(24);
  static const cardGap = 16.0;
}

class StandbyRadius {
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 20.0;
  static const xxl = 24.0;
  static final cardRadius = BorderRadius.circular(xl);
  static final buttonRadius = BorderRadius.circular(md);
  static final tagRadius = BorderRadius.circular(sm);
}

class StandbyDuration {
  static const fast = Duration(milliseconds: 200);
  static const normal = Duration(milliseconds: 300);
  static const slow = Duration(milliseconds: 500);
  static const verySlow = Duration(milliseconds: 800);
}

/// 构建 Standby 暗色 ThemeData
ThemeData buildStandbyTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: ColorScheme.dark(
      primary: StandbyColors.primary,
      surface: StandbyColors.surface1,
      onSurface: StandbyColors.text,
    ),
    scaffoldBackgroundColor: StandbyColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: StandbyColors.background,
      foregroundColor: StandbyColors.text,
      elevation: 0,
      scrolledUnderElevation: 0,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: StandbyColors.surface1,
      indicatorColor: StandbyColors.primarySoft,
      labelTextStyle: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return StandbyTextStyles.label.copyWith(color: StandbyColors.primary);
        }
        return StandbyTextStyles.label.copyWith(color: StandbyColors.text3);
      }),
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: StandbyColors.primary);
        }
        return const IconThemeData(color: StandbyColors.text3);
      }),
    ),
    cardTheme: CardThemeData(
      color: StandbyColors.surface1,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: StandbyRadius.cardRadius,
        side: const BorderSide(color: StandbyColors.border),
      ),
    ),
    textTheme: const TextTheme(
      headlineLarge: StandbyTextStyles.h1,
      headlineMedium: StandbyTextStyles.h2,
      headlineSmall: StandbyTextStyles.h3,
      bodyLarge: StandbyTextStyles.body,
      labelSmall: StandbyTextStyles.label,
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: StandbyColors.surface2,
      contentTextStyle: StandbyTextStyles.body.copyWith(color: StandbyColors.text),
      shape: RoundedRectangleBorder(borderRadius: StandbyRadius.buttonRadius),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: StandbyColors.primary,
      foregroundColor: Colors.white,
    ),
    dividerTheme: const DividerThemeData(
      color: StandbyColors.border,
      thickness: 1,
    ),
  );
}
